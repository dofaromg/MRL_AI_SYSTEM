#!/usr/bin/env python3
"""MrLiouWord: read-only source gate for the R02 operations supplement.

Run from a checked-out repository. This validates source, not a DL580 runtime.
PowerShell payload is parsed by pwsh and is never executed by this program.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys

ORIGIN = "MrLiouWord"
OPS = "MRL_Recovery_Operations/20261010_R02"
MANIFEST = OPS + "/OPERATIONS_MANIFEST.json"
VERIFIER = OPS + "/verify_operations_manifest.py"
WATCHDOG = OPS + "/MRL_active_runtime_watchdog_v3.py"
WORKFLOW = ".github/workflows/MRL_recovery_operations.yml"
MAX_BYTES = 16 * 1024 * 1024
MAX_FILES = 256
SCHEMA = "MRL_recovery_operations_source_gate_v1"


class GateError(Exception):
    def __init__(self, code: str, path: str | None = None):
        super().__init__(code)
        self.code, self.path = code, path


def require(condition: bool, code: str, path: str | None = None) -> None:
    if not condition:
        raise GateError(code, path)


def json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def parse_json(data):
    try:
        return json.loads(data, object_pairs_hook=json_object)
    except GateError:
        raise
    except (ValueError, UnicodeError, TypeError):
        raise GateError("INVALID_JSON") from None


def checked_path(value, allow_manifest=False):
    require(isinstance(value, str) and 0 < len(value) <= 1024, "INVALID_PATH")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), "INVALID_PATH")
    require(not any(c in value for c in '\\:<>"|?*'), "INVALID_PATH")
    parts = value.split("/")
    require(all(p and p not in (".", "..") and not p.endswith((" ", "."))
                for p in parts), "INVALID_PATH")
    require(str(PurePosixPath(value)) == value, "INVALID_PATH")
    require(value == WORKFLOW or value.startswith(OPS + "/"), "OUT_OF_SCOPE_PATH")
    require(allow_manifest or value != MANIFEST, "SELF_HASH_FORBIDDEN")
    require(not any(p.casefold() == "__pycache__" for p in parts)
            and not value.casefold().endswith((".pyc", ".pyo")), "BYTECODE_FORBIDDEN")
    return value


def manifest_entries(raw):
    require(len(raw) <= MAX_BYTES, "MANIFEST_TOO_LARGE")
    document = parse_json(raw)
    require(isinstance(document, dict), "INVALID_MANIFEST")
    require(document.get("origin_signature") == ORIGIN, "ORIGIN_MISMATCH")
    rows = document.get("files")
    expected = document.get("expected_file_list")
    require(isinstance(rows, list) and 1 <= len(rows) <= MAX_FILES, "INVALID_FILES")
    require(isinstance(expected, list), "INVALID_EXPECTED_LIST")
    entries, folded = {}, set()
    for row in rows:
        require(isinstance(row, dict), "INVALID_FILE_ENTRY")
        require({"path", "bytes", "sha256", "git_blob_sha"} <= row.keys(),
                "MISSING_FILE_FIELDS")
        path = checked_path(row["path"])
        require(path.casefold() not in folded, "DUPLICATE_PAYLOAD_PATH", path)
        require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_BYTES,
                "INVALID_BYTE_COUNT", path)
        require(isinstance(row["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
                "INVALID_SHA256", path)
        require(isinstance(row["git_blob_sha"], str)
                and re.fullmatch(r"[0-9a-f]{40}", row["git_blob_sha"]) is not None,
                "INVALID_GIT_BLOB_SHA", path)
        entries[path] = row
        folded.add(path.casefold())
    require({VERIFIER, WATCHDOG, WORKFLOW} <= entries.keys(), "MISSING_REQUIRED_PAYLOAD")
    expected_set, expected_folded = set(), set()
    for item in expected:
        path = checked_path(item, allow_manifest=True)
        require(path.casefold() not in expected_folded, "DUPLICATE_EXPECTED_PATH", path)
        expected_set.add(path)
        expected_folded.add(path.casefold())
    require(expected_set == set(entries) | {MANIFEST}, "EXPECTED_SET_MISMATCH")
    return entries, expected_set


def plain(st, directory=False):
    require(not stat.S_ISLNK(st.st_mode)
            and not (getattr(st, "st_file_attributes", 0) & 0x400),
            "SYMLINK_OR_REPARSE_POINT")
    require(stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode),
            "NOT_A_PLAIN_DIRECTORY" if directory else "NOT_A_REGULAR_FILE")


def path_stat(repo, relative, directory=False):
    plain(repo.lstat(), directory=True)
    current = repo
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        st = current.lstat()
        plain(st, directory=index < len(parts) - 1 or directory)
    return current, st


def fingerprint(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def read_regular(repo, relative):
    path, before = path_stat(repo, relative)
    require(before.st_size <= MAX_BYTES, "PAYLOAD_TOO_LARGE", relative)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        plain(opened)
        require(fingerprint(opened) == fingerprint(before), "FILE_CHANGED", relative)
        chunks, length = [], 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, MAX_BYTES + 1 - length))
            if not chunk:
                break
            length += len(chunk)
            require(length <= MAX_BYTES, "PAYLOAD_TOO_LARGE", relative)
            chunks.append(chunk)
        require(fingerprint(os.fstat(fd)) == fingerprint(opened), "FILE_CHANGED", relative)
        _, after = path_stat(repo, relative)
        require(fingerprint(after) == fingerprint(opened), "FILE_CHANGED", relative)
        data = b"".join(chunks)
        require(len(data) == before.st_size, "FILE_CHANGED", relative)
        return data
    finally:
        os.close(fd)


def inventory(repo):
    base, _ = path_stat(repo, OPS, directory=True)
    found = set()

    def visit(directory):
        with os.scandir(directory) as scan:
            children = sorted(scan, key=lambda item: item.name)
        for item in children:
            path = Path(item.path)
            relative = path.relative_to(repo).as_posix()
            checked_path(relative, allow_manifest=True)
            st = item.stat(follow_symlinks=False)
            if stat.S_ISDIR(st.st_mode):
                plain(st, directory=True)
                visit(path)
            else:
                plain(st)
                require(relative not in found, "DUPLICATE_DISK_PATH", relative)
                found.add(relative)

    visit(base)
    return found


def content_hashes(data):
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha256(data).hexdigest(), hashlib.sha1(header + data).hexdigest()


def verify_content(path, data, row):
    require(len(data) == row["bytes"], "BYTE_COUNT_MISMATCH", path)
    sha256, blob = content_hashes(data)
    require(sha256 == row["sha256"], "SHA256_MISMATCH", path)
    require(blob == row["git_blob_sha"], "GIT_BLOB_SHA_MISMATCH", path)


PS_PARSE = r"""
$ErrorActionPreference = 'Stop'
try {
    $Items = ConvertFrom-Json -InputObject ([Console]::In.ReadToEnd())
    $Rows = @(foreach ($Item in $Items) {
        $Tokens = $null
        $ParseErrors = $null
        [void][System.Management.Automation.Language.Parser]::ParseInput(
            [string]$Item.source, [ref]$Tokens, [ref]$ParseErrors)
        $Count = 0
        if ($null -ne $ParseErrors) { $Count = @($ParseErrors).Count }
        [pscustomobject]@{path = [string]$Item.path; errors = [int]$Count}
    })
    $Result = @{version = $PSVersionTable.PSVersion.ToString(); results = $Rows}
    [Console]::Out.Write((ConvertTo-Json -InputObject $Result -Depth 4 -Compress))
    exit 0
} catch {
    [Console]::Out.Write('{"parser_failed":true}')
    exit 1
}
"""


def powershell_syntax(documents):
    if not documents:
        return {"files": 0, "parser": "NOT_NEEDED"}
    try:
        result = subprocess.run(
            ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", PS_PARSE],
            input=json.dumps(documents, ensure_ascii=True), text=True,
            encoding="utf-8", capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise GateError("POWERSHELL_PARSER_UNAVAILABLE") from None
    require(result.returncode == 0 and len(result.stdout) <= 65536,
            "POWERSHELL_PARSER_FAILED")
    parsed = parse_json(result.stdout)
    require(isinstance(parsed, dict) and isinstance(parsed.get("version"), str)
            and re.fullmatch(r"[0-9]+(?:\.[0-9A-Za-z+-]+)+", parsed["version"])
            is not None, "POWERSHELL_RESULT_INVALID")
    rows = parsed.get("results")
    require(isinstance(rows, list) and len(rows) == len(documents),
            "POWERSHELL_RESULT_INVALID")
    expected = {doc["path"] for doc in documents}
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str)
                and row["path"] in expected and row["path"] not in seen
                and type(row.get("errors")) is int and row["errors"] >= 0,
                "POWERSHELL_RESULT_INVALID")
        require(row["errors"] == 0, "POWERSHELL_SYNTAX_ERROR", row["path"])
        seen.add(row["path"])
    require(seen == expected, "POWERSHELL_RESULT_INVALID")
    return {"files": len(documents), "parser": "pwsh_static_parser",
            "version": parsed["version"]}


def verify(repo):
    raw = read_regular(repo, MANIFEST)
    entries, expected = manifest_entries(raw)
    actual = inventory(repo)
    require(actual == {p for p in expected if p.startswith(OPS + "/")},
            "OPERATIONS_INVENTORY_MISMATCH")
    documents, python_count = [], 0
    for path, row in sorted(entries.items()):
        data = read_regular(repo, path)
        verify_content(path, data, row)
        suffix = PurePosixPath(path).suffix.casefold()
        if suffix == ".py":
            try:
                tree = ast.parse(data, filename=path)
                compile(tree, path, "exec", dont_inherit=True)
            except (SyntaxError, ValueError, TypeError):
                raise GateError("PYTHON_SYNTAX_ERROR", path) from None
            python_count += 1
        elif suffix == ".ps1":
            try:
                source = data.decode("utf-8-sig")
            except UnicodeError:
                raise GateError("POWERSHELL_ENCODING_INVALID", path) from None
            documents.append({"path": path, "source": source})
    ps_result = powershell_syntax(documents)
    require(read_regular(repo, MANIFEST) == raw, "MANIFEST_CHANGED")
    require(inventory(repo) == actual, "INVENTORY_CHANGED")
    # Close the parser interval with a second complete content check.
    for path, row in sorted(entries.items()):
        verify_content(path, read_regular(repo, path), row)
    return {"schema": SCHEMA, "origin_signature": ORIGIN, "status": "PASS",
            "execution_scope": "SOURCE_VALIDATION_ONLY", "host_platform": sys.platform,
            "manifest": MANIFEST, "payload_files": len(entries),
            "expected_files": len(expected), "operations_regular_files": len(actual),
            "sha256_verified": len(entries), "git_blob_sha_verified": len(entries),
            "python_ast_compile_files": python_count, "powershell_syntax": ps_result,
            "manifest_self_hash": "EXCLUDED",
            "live_runtime_execution": False, "dl580_runtime": "NOT_ASSERTED"}


def main():
    try:
        require(len(sys.argv) == 1, "UNEXPECTED_ARGUMENTS")
        repo = Path(__file__).absolute().parents[2]
        result = verify(repo)
    except GateError as exc:
        result = {"schema": SCHEMA, "origin_signature": ORIGIN, "status": "FAIL",
                  "execution_scope": "SOURCE_VALIDATION_ONLY", "error": exc.code,
                  "live_runtime_execution": False, "dl580_runtime": "NOT_ASSERTED"}
        if exc.path is not None:
            result["path"] = exc.path
    except (OSError, ValueError, RuntimeError):
        result = {"schema": SCHEMA, "origin_signature": ORIGIN, "status": "FAIL",
                  "execution_scope": "SOURCE_VALIDATION_ONLY", "error": "SOURCE_READ_FAILED",
                  "live_runtime_execution": False, "dl580_runtime": "NOT_ASSERTED"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
