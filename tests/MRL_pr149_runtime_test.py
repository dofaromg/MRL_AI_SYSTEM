import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import time
import tempfile
import unittest
import urllib.request
import urllib.error
ROOT = Path(__file__).resolve().parents[1]
class RuntimeTests(unittest.TestCase):
    def test_chat(self):
        spec = importlib.util.spec_from_file_location("platform_server", ROOT / "MRL_Platform_Server.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class Mother:
            def chat(self, msg): return self.result
        mother = Mother()
        module._MA = mother
        for result, expected in [({"error": "missing model"}, False), ("reply", True), ({"reply": "hello"}, True)]:
            mother.result = result
            self.assertEqual(module.api_chat({"message": "hello"})["ok"], expected)
    def test_gateway(self):
        for auth, opt, token, expected in [(False, False, None, 403), (False, True, None, 200), (True, True, None, 401), (True, False, "Bearer secret-test-token", 200),
            (True, False, "bearer secret-test-token", 200),
            (True, False, "bEaReR   secret-test-token", 200),
            (True, False, "Bearer Secret-test-token", 401),
            (True, False, "Basic secret-test-token", 401),
            (True, False, "Bearersecret-test-token", 401),
            (True, False, "Bearer secret-test-token extra", 401),
            (True, False, "Bearer", 401)]:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
            env = dict(os.environ, MRL_PORT=str(port), MRL_AUTH_REQUIRED=str(auth).lower(), MRL_ALLOW_UNAUTHENTICATED_WRITES=str(opt).lower(), MRL_API_TOKEN="secret-test-token")
            proc = subprocess.Popen(["node", "MRL_RuntimeServer.js"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL)
            try:
                url = f"http://127.0.0.1:{port}"
                for _ in range(100):
                    try:
                        self.assertEqual(urllib.request.urlopen(url + "/health").status, 200); break
                    except OSError: time.sleep(.05)
                else: self.fail("server did not start")
                headers = {"Content-Type": "application/json"}
                if token: headers["Authorization"] = token
                req = urllib.request.Request(url + "/mrl/perceive", data=b'{}', headers=headers)
                try: status = urllib.request.urlopen(req).status
                except urllib.error.HTTPError as exc: status = exc.code
                self.assertEqual(status, expected)
            finally:
                proc.terminate(); proc.wait(timeout=10)
    def test_launcher_port(self):
        for configured, override, expected in [(None, None, "8790"), ("8800", None, "8800"), ("8800", "8900", "8900"), (None, "8900", "8900"), ("8800", "", "8800")]:
            with self.subTest(configured=configured, override=override), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                (home / "scripts").mkdir()
                (home / "node_modules").mkdir()
                binaries = home / "bin"
                binaries.mkdir()
                (home / "scripts/MRL_dl580_deploy_check.sh").write_text('printf "check=%s\\n" "$MRL_PORT"\n')
                for name in ["npm", "node"]:
                    executable = binaries / name
                    executable.write_text('#!/usr/bin/env bash\nprintf "' + name + '=%s\\n" "$MRL_PORT"\n')
                    executable.chmod(0o755)
                env = dict(os.environ, MRL_HOME=str(home), PATH=str(binaries) + os.pathsep + os.environ["PATH"])
                for key, value in [("MRL_PORT", configured), ("MRL_RUNTIME_PORT", override)]:
                    env.pop(key, None)
                    if value is not None: env[key] = value
                result = subprocess.run(["bash", str(ROOT / "deploy/dl580/MRL_dl580_start.sh")], env=env, capture_output=True, text=True, check=True)
                for line in [f"MRL_PORT={expected}", f"check={expected}", f"npm={expected}", f"node={expected}"]:
                    self.assertIn(line, result.stdout.splitlines())
                self.assertLess(result.stdout.index(f"MRL_PORT={expected}"), result.stdout.index(f"check={expected}"))
if __name__ == "__main__": unittest.main()
