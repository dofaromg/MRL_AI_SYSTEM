#!/usr/bin/env python3
"""Create a preserved-source Watchdog syntax candidate; never execute or activate it."""
import argparse
import ast
import copy
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import sys
import warnings
from datetime import datetime, timezone

SOURCE = r"D:\mrl\MRL_Watchdog.py"
CANDIDATE = r"D:\mrl\MRL_Watchdog_SyntaxCandidate_20261010_R01.py"
RECEIPT_NAME = "MRL_Watchdog_SyntaxCandidate_20261010_R01.receipt.json"
SPEC = {
    "original_size": 1787,
    "original_sha256": "2c327ed594594425a7a58d2082abc624a22531f7011d446dd2bd999172eff846",
    "candidate_size": 1788,
    "candidate_sha256": "52b4d3053f592f703f5ed4deadefc15b41a5a842e7763566b9c5206481c199f8",
    "insert_offset": 1605,
    "line": 41,
    "constant_column": 47,
    "lf_count": 47,
    "crlf_count": 0,
}

class GateFailure(Exception):
    pass

def require(condition, code):
    if not condition:
        raise GateFailure(code)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def syntax_metadata(exc):
    result = {"class": type(exc).__name__}
    for key in ("lineno", "offset", "end_lineno", "end_offset"):
        value = getattr(exc, key, None)
        result[key] = value if isinstance(value, int) else None
    return result

def parse_compile(data):
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        tree = ast.parse(data, filename="<watchdog-syntax-validation>", mode="exec")
        compile(tree, "<watchdog-syntax-validation>", "exec",
                dont_inherit=True, optimize=0)
    return tree, len(recorded)

def neutralize_source_line(data, line_number):
    lines = data.splitlines(keepends=True)
    require(1 <= line_number <= len(lines), "BASELINE_LINE_MISSING")
    line = lines[line_number - 1]
    require(line.endswith(b"\n") and not line.endswith(b"\r\n"),
            "BASELINE_LINE_ENDING_UNSUPPORTED")
    body = line[:-1]
    indentation = body[:len(body) - len(body.lstrip(b" \t"))]
    lines[line_number - 1] = indentation + b"pass\n"
    return b"".join(lines)

def neutralize_ast_statement(tree, line_number):
    result = copy.deepcopy(tree)
    matching = [node for node in ast.walk(result)
                if isinstance(node, ast.stmt)
                and getattr(node, "lineno", None) == line_number]
    require(len(matching) == 1, "BASELINE_STATEMENT_NOT_UNIQUE")
    target = matching[0]
    require(getattr(target, "end_lineno", None) == line_number,
            "BASELINE_STATEMENT_CROSSES_LINE")
    replacements = 0
    for parent in ast.walk(result):
        for field, value in ast.iter_fields(parent):
            if isinstance(value, list):
                for index, item in enumerate(value):
                    if item is target:
                        value[index] = ast.copy_location(ast.Pass(), target)
                        replacements += 1
            elif value is target:
                setattr(parent, field, ast.copy_location(ast.Pass(), target))
                replacements += 1
    require(replacements == 1, "BASELINE_STATEMENT_REPLACEMENT_FAILED")
    ast.fix_missing_locations(result)
    compile(result, "<watchdog-neutralized-validation>", "exec",
            dont_inherit=True, optimize=0)
    return result

def verify_bytes(original, spec=None):
    spec = SPEC if spec is None else spec
    require(type(original) is bytes, "SOURCE_TYPE_INVALID")
    require(len(original) == spec["original_size"], "SOURCE_SIZE_MISMATCH")
    require(digest(original) == spec["original_sha256"], "SOURCE_HASH_MISMATCH")
    offset = spec["insert_offset"]
    require(original[offset - 1:offset + 2] == bytes((39, 92, 39)),
            "PATCH_CONTEXT_MISMATCH")
    candidate = original[:offset] + bytes((92,)) + original[offset:]
    require(len(candidate) == spec["candidate_size"], "CANDIDATE_SIZE_MISMATCH")
    require(digest(candidate) == spec["candidate_sha256"], "CANDIDATE_HASH_MISMATCH")
    require(candidate[:offset] + candidate[offset + 1:] == original,
            "INVERSE_PATCH_MISMATCH")
    require(original.count(b"\n") == candidate.count(b"\n") == spec["lf_count"],
            "LINE_COUNT_MISMATCH")
    require(original.count(b"\r\n") == candidate.count(b"\r\n") == spec["crlf_count"],
            "LINE_ENDING_MISMATCH")
    try:
        parse_compile(original)
    except SyntaxError as exc:
        original_error = syntax_metadata(exc)
        require(exc.lineno == spec["line"], "ORIGINAL_ERROR_LINE_MISMATCH")
    else:
        raise GateFailure("ORIGINAL_UNEXPECTEDLY_PARSEABLE")
    tree, warning_count = parse_compile(candidate)
    parents = {child: parent for parent in ast.walk(tree)
               for child in ast.iter_child_nodes(parent)}
    separators = [node for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and node.value == "\\"
                  and getattr(node, "lineno", None) == spec["line"]
                  and getattr(node, "col_offset", None) == spec["constant_column"]]
    require(len(separators) == 1, "SEPARATOR_CONSTANT_NOT_UNIQUE")
    parent = parents.get(separators[0])
    require(isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Attribute)
            and parent.func.attr in {"replace", "split", "rsplit"}
            and any(item is separators[0] for item in parent.args),
            "SEPARATOR_CONTEXT_NOT_PATH_OPERATION")
    baseline, baseline_warnings = parse_compile(
        neutralize_source_line(original, spec["line"]))
    neutralized = neutralize_ast_statement(tree, spec["line"])
    require(ast.dump(baseline, include_attributes=False)
            == ast.dump(neutralized, include_attributes=False),
            "AST_OUTSIDE_LINE_CHANGED")
    counts = {
        "top_level_statements": len(tree.body),
        "imports": sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree)),
        "functions": sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)),
        "while_statements": sum(isinstance(n, ast.While) for n in ast.walk(tree)),
        "for_statements": sum(isinstance(n, ast.For) for n in ast.walk(tree)),
        "try_statements": sum(isinstance(n, ast.Try) for n in ast.walk(tree)),
        "if_statements": sum(isinstance(n, ast.If) for n in ast.walk(tree)),
        "calls": sum(isinstance(n, ast.Call) for n in ast.walk(tree)),
        "bare_except_handlers": sum(isinstance(n, ast.ExceptHandler) and n.type is None
                                   for n in ast.walk(tree)),
    }
    metadata = {
        "status": "SYNTAX_REPAIRED_CANDIDATE",
        "original_size": len(original),
        "original_sha256": digest(original),
        "candidate_size": len(candidate),
        "candidate_sha256": digest(candidate),
        "patch": {"original_byte_offset": offset, "deleted_bytes": 0,
                  "inserted_bytes": 1, "inserted_hex": "5c"},
        "all_other_bytes_identical": True,
        "inverse_patch_restores_original": True,
        "physical_lf_count": candidate.count(b"\n"),
        "original_syntax_error": original_error,
        "ast_parse": "PASS",
        "compile": "PASS",
        "separator_context": "PATH_SEPARATOR_OPERATION",
        "ast_outside_replaced_statement": "IDENTICAL",
        "candidate_warning_count": warning_count,
        "baseline_warning_count": baseline_warnings,
        "ast_counts": counts,
        "deployment": "BLOCKED",
        "activation_blocked_reason": "STATIC_TARGET_MISMATCH",
        "previously_verified_configured_ports": [7600, 7800],
        "previously_verified_active_inference_port": 7500,
        "previously_verified_asi_port": 7700,
        "runtime": "NOT_EXECUTED",
        "semantic_equivalence": "NOT_ASSERTED",
        "task_mutation_calls": 0,
        "candidate_execution_calls": 0,
        "service_start_stop_calls": 0,
    }
    return candidate, metadata

def validate_existing_directory(raw_path):
    require(os.name == "nt", "WINDOWS_REQUIRED")
    require(isinstance(raw_path, str) and raw_path, "DIRECTORY_REQUIRED")
    require(ntpath.isabs(raw_path)
            and ntpath.splitdrive(raw_path)[0].upper() == "D:",
            "D_ABSOLUTE_PATH_REQUIRED")
    require(".." not in raw_path.replace("/", "\\").split("\\"),
            "PARENT_TRAVERSAL_REJECTED")
    require(":" not in ntpath.splitdrive(raw_path)[1], "ADS_PATH_REJECTED")
    path = Path(raw_path)
    require(path.is_dir(), "EXISTING_DIRECTORY_REQUIRED")
    for item in (path, *path.parents):
        info = os.lstat(item)
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0) & 0x400),
                "REPARSE_DIRECTORY_REJECTED")
    final = path.resolve(strict=True)
    require(ntpath.splitdrive(str(final))[0].upper() == "D:", "FINAL_VOLUME_NOT_D")
    return path

def assert_plain_file(path):
    info = os.lstat(path)
    require(stat.S_ISREG(info.st_mode)
            and not (getattr(info, "st_file_attributes", 0) & 0x400),
            "SOURCE_NOT_REGULAR_FILE")

def exclusive_write(path, payload):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(str(path), flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "WRITE_NO_PROGRESS")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    assert_plain_file(path)
    require(path.read_bytes() == payload, "EXCLUSIVE_WRITE_READBACK_MISMATCH")

def run(receipt_dir, write=False):
    source = Path(SOURCE)
    candidate_path = Path(CANDIDATE)
    validate_existing_directory(str(source.parent))
    receipt_parent = validate_existing_directory(receipt_dir)
    assert_plain_file(source)
    original = source.read_bytes()
    candidate, receipt = verify_bytes(original)
    receipt.update({
        "schema": "MRL_Watchdog_SyntaxCandidate_Receipt/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source),
        "candidate_path": str(candidate_path),
        "receipt_path": str(receipt_parent / RECEIPT_NAME),
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "write_requested": bool(write),
        "candidate_created": False,
        "receipt_created": False,
        "original_preserved": True,
    })
    receipt_path = receipt_parent / RECEIPT_NAME
    require(source.read_bytes() == original, "SOURCE_CHANGED_DURING_VALIDATION")
    if not write:
        receipt["operation"] = "DRY_RUN"
        return receipt
    require(not os.path.lexists(candidate_path), "CANDIDATE_ALREADY_EXISTS")
    require(not os.path.lexists(receipt_path), "RECEIPT_ALREADY_EXISTS")
    # Each create uses O_EXCL. A partial failure is reported and never activates anything.
    exclusive_write(candidate_path, candidate)
    receipt["candidate_created"] = True
    require(source.read_bytes() == original, "SOURCE_CHANGED_AFTER_CANDIDATE_CREATE")
    receipt["receipt_created"] = True
    receipt["operation"] = "EXCLUSIVE_CANDIDATE_AND_RECEIPT_CREATED"
    payload = (json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2)
               + "\n").encode("utf-8")
    exclusive_write(receipt_path, payload)
    require(source.read_bytes() == original, "SOURCE_CHANGED_AFTER_RECEIPT_CREATE")
    receipt["receipt_sha256"] = digest(payload)
    return receipt

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a fixed single-byte Watchdog syntax repair; never activate it.")
    parser.add_argument("--receipt-dir", required=True,
                        help="Existing approved D: directory under opsR02.")
    parser.add_argument("--write", action="store_true",
                        help="Exclusively create the fixed sibling candidate and receipt.")
    args = parser.parse_args(argv)
    try:
        result = run(args.receipt_dir, args.write)
    except BaseException as exc:
        result = {
            "status": "FAIL",
            "error_code": str(exc) if isinstance(exc, GateFailure) else type(exc).__name__,
            "deployment": "BLOCKED",
            "runtime": "NOT_EXECUTED",
            "task_mutation_calls": 0,
            "candidate_execution_calls": 0,
            "service_start_stop_calls": 0,
            "partial_artifacts_possible": bool(args.write),
        }
        if isinstance(exc, SyntaxError):
            result["syntax_error"] = syntax_metadata(exc)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
