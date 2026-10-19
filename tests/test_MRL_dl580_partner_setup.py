"""DL580 partner setup orchestration tests; no host services or network touched."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "deploy" / "tailscale" / "MRL_dl580_partner_setup"


class PartnerSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "calls"
        self.env = dict(
            os.environ,
            HOME=str(self.directory),
            PATH=f"{self.bin}:/usr/bin:/bin",
            CALL_LOG=str(self.log),
            TEST_ROOT=str(ROOT),
        )

    def linux(self, **changes: str) -> subprocess.CompletedProcess[str]:
        dispatcher = self.bin / "dispatcher"
        dispatcher.write_text(
            """#!/bin/bash
printf '%s %s\\n' "${0##*/}" "$*" >> "$CALL_LOG"
case "${0##*/}" in
  uname) echo "${TEST_OS:-Linux}" ;;
  id) if [ "$1" = "-u" ]; then echo "${TEST_UID:-1000}"; else echo partner; fi ;;
  git)
    case "$*" in
      *--show-toplevel*) echo "$TEST_ROOT" ;;
      *--porcelain*) [ "${DIRTY:-0}" = 0 ] || echo " M local.txt" ;;
      *--verify*) exit "${NO_UPSTREAM:-0}" ;;
      *pull*) exit "${PULL_FAIL:-0}" ;;
    esac ;;
  systemctl)
    case "$1" in
      show) echo "${SSH_LOAD:-loaded}" ;;
      is-active|is-enabled) exit "${SSH_STOPPED:-0}" ;;
    esac ;;
  sudo) exit "${SUDO_FAIL:-0}" ;;
  tailscale) [ "${NO_TS:-0}" = 0 ] && echo 100.64.0.10 ;;
  claude) echo "Claude test CLI"; exit "${CLAUDE_FAIL:-0}" ;;
  python3) exit "${SMOKE_FAIL:-0}" ;;
  curl)
    if [ "${DOWNLOAD_FAIL:-0}" = 1 ]; then exit 22; fi
    printf '#!/bin/bash\\nmkdir -p "$HOME/.local/bin"\\nprintf "#!/bin/bash\\\\necho installed-cli\\\\n" > "$HOME/.local/bin/claude"\\nchmod +x "$HOME/.local/bin/claude"\\n' > "${@: -1}" ;;
esac
exit 0
""",
            encoding="utf-8",
        )
        dispatcher.chmod(0o755)
        for name in (
            "uname", "id", "git", "systemctl", "sudo",
            "tailscale", "claude", "python3", "curl",
        ):
            (self.bin / name).symlink_to(dispatcher)
        if changes.pop("MISSING_CLAUDE", ""):
            (self.bin / "claude").unlink()
        return subprocess.run(
            ["/bin/bash", str(ENTRY.with_suffix(".sh"))],
            env=dict(self.env, **changes),
            capture_output=True, text=True, check=False,
        )

    def test_linux_ready_and_repeat_preserve_settings(self) -> None:
        result = self.linux()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Host: 100.64.0.10", result.stdout)
        self.assertIn("User: partner", result.stdout)
        calls = self.log.read_text()
        self.assertIn("pull --ff-only", calls)
        self.assertIn("MRL_mother_assembly.py status", calls)
        self.assertNotIn("sudo ", calls)
        self.assertNotIn("curl ", calls)
        self.assertNotIn("tailscale up", calls)
        repeated = subprocess.run(
            ["/bin/bash", str(ENTRY.with_suffix(".sh"))],
            env=self.env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(repeated.returncode, 0)
        self.assertNotIn("curl ", self.log.read_text())

    def test_linux_partial_conditions(self) -> None:
        for condition in (
            "DIRTY", "NO_UPSTREAM", "PULL_FAIL", "NO_TS",
            "SMOKE_FAIL", "CLAUDE_FAIL",
        ):
            with self.subTest(condition=condition):
                self.log.unlink(missing_ok=True)
                result = self.linux(**{condition: "1"})
                self.assertEqual(result.returncode, 1)
                self.assertIn("PARTIAL", result.stdout)
                if condition in ("DIRTY", "NO_UPSTREAM"):
                    self.assertNotIn("pull ", self.log.read_text())
                for name in self.bin.iterdir():
                    name.unlink()

    def test_linux_rejects_other_os_and_root_before_changes(self) -> None:
        for changes in ({"TEST_OS": "Darwin"}, {"TEST_UID": "0"}):
            with self.subTest(changes=changes):
                result = self.linux(**changes)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("git ", self.log.read_text())
                for name in self.bin.iterdir():
                    name.unlink()

    def test_linux_missing_ssh_is_partial(self) -> None:
        result = self.linux(SSH_LOAD="not-found")
        self.assertEqual(result.returncode, 1)
        self.assertIn("OpenSSH", result.stdout)
        self.assertNotIn("sudo ", self.log.read_text())

    def test_linux_failed_ssh_enable_is_partial(self) -> None:
        result = self.linux(SSH_STOPPED="1", SUDO_FAIL="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sudo systemctl enable --now ssh.service", self.log.read_text())

    def test_linux_recognizes_existing_cli_outside_path(self) -> None:
        local = self.directory / ".local" / "bin" / "claude"
        local.parent.mkdir(parents=True)
        local.write_text("#!/bin/bash\necho existing-cli\n", encoding="utf-8")
        local.chmod(0o755)
        result = self.linux(MISSING_CLAUDE="1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("curl ", self.log.read_text())

    def test_linux_failed_download_is_partial_and_cleaned(self) -> None:
        self.env["TMPDIR"] = str(self.directory)
        result = self.linux(MISSING_CLAUDE="1", DOWNLOAD_FAIL="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("PARTIAL", result.stdout)
        self.assertFalse(list(self.directory.glob("tmp.*")))

    def test_linux_installs_cli_and_cleans_installer(self) -> None:
        self.env["TMPDIR"] = str(self.directory)
        result = self.linux(MISSING_CLAUDE="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("installed-cli", result.stdout)
        self.assertIn("https://claude.ai/install.sh", self.log.read_text())
        self.assertFalse(list(self.directory.glob("tmp.*")))

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell runtime unavailable")
    def test_windows_orchestration_with_mocked_host_commands(self) -> None:
        harness = self.directory / "host.ps1"
        harness.write_text(
            """
$env:OS = 'Windows_NT'
$PSNativeCommandUseErrorActionPreference = $true
function git {
    Add-Content $env:CALL_LOG "git $args"
    $global:LASTEXITCODE = 0
    if ($args -contains '--show-toplevel') { return $env:TEST_ROOT }
    if ($args -contains '--porcelain' -and $env:DIRTY -eq '1') { return ' M local.txt' }
    if ($args -contains '--verify' -and $env:NO_UPSTREAM -eq '1') { $global:LASTEXITCODE = 1 }
    if ($args -contains '--verify' -and $env:NO_UPSTREAM_NATIVE -eq '1') {
        & $env:TEST_GIT -C $env:TEST_ROOT rev-parse --verify refs/heads/mrl-test-nonexistent 2>$null
        $global:LASTEXITCODE = $LASTEXITCODE
    }
    if ($args -contains 'pull' -and $env:PULL_FAIL -eq '1') { $global:LASTEXITCODE = 1 }
}
function Get-Service {
    if ($env:NO_SSH -eq '1') { return $null }
    if ($env:START_SSH -eq '1' -and -not $script:SshStarted) {
        return [pscustomobject]@{StartType='Manual'; Status='Stopped'}
    }
    return [pscustomobject]@{StartType='Automatic'; Status='Running'}
}
function Set-Service {
    Add-Content $env:CALL_LOG "Set-Service $args"
    if ($env:DENY_SSH -eq '1') { throw 'access denied' }
}
function Start-Service {
    Add-Content $env:CALL_LOG "Start-Service $args"
    $script:SshStarted = $true
}
function tailscale {
    $global:LASTEXITCODE = 0
    if ($env:NO_TS -ne '1') { '100.64.0.10' }
}
function claude { $global:LASTEXITCODE = 0; 'Claude test CLI' }
function python {
    Add-Content $env:CALL_LOG "python $args"
    $global:LASTEXITCODE = 0
    if ($env:SMOKE_FAIL -eq '1') { $global:LASTEXITCODE = 1 }
}
function curl.exe {
    Add-Content $env:CALL_LOG "curl.exe $args"
    $global:LASTEXITCODE = 0
    if ($env:DOWNLOAD_FAIL -eq '1') { $global:LASTEXITCODE = 22; return }
    Set-Content -LiteralPath $args[-1] -Value "function global:claude { `$global:LASTEXITCODE = 0; 'installed-cli' }"
}
function whoami { 'dl580\\partner' }
if ($env:INSTALL_CLAUDE -eq '1') { Remove-Item Function:claude }
& $env:TEST_ENTRY
exit $LASTEXITCODE
""",
            encoding="utf-8",
        )
        for condition in (
            "", "DIRTY", "NO_UPSTREAM", "PULL_FAIL", "NO_SSH", "NO_TS",
            "SMOKE_FAIL", "START_SSH", "DENY_SSH", "INSTALL_CLAUDE", "DOWNLOAD_FAIL",
            "NO_UPSTREAM_NATIVE",
        ):
            with self.subTest(condition=condition):
                self.log.unlink(missing_ok=True)
                extra = {condition: "1"} if condition else {}
                if condition == "DENY_SSH":
                    extra["START_SSH"] = "1"
                if condition == "DOWNLOAD_FAIL":
                    extra["INSTALL_CLAUDE"] = "1"
                result = subprocess.run(
                    ["pwsh", "-NoProfile", "-File", str(harness)],
                    env=dict(
                        self.env, TEST_ENTRY=str(ENTRY.with_suffix(".ps1")),
                        TEST_GIT=shutil.which("git") or "/usr/bin/git", **extra,
                    ),
                    capture_output=True, text=True, check=False,
                )
                partial = condition not in ("", "START_SSH", "INSTALL_CLAUDE")
                self.assertEqual(result.returncode, int(partial), result.stdout + result.stderr)
                self.assertIn("MRL_mother_assembly.py", self.log.read_text())
                self.assertIn("PARTIAL" if partial else "Host: 100.64.0.10", result.stdout)
                if condition in ("DIRTY", "NO_UPSTREAM", "NO_UPSTREAM_NATIVE"):
                    self.assertNotIn("pull ", self.log.read_text())
                if condition == "INSTALL_CLAUDE":
                    self.assertIn("installed-cli", result.stdout)
                if condition == "START_SSH":
                    self.assertIn("Start-Service", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
