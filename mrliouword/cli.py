"""
mrliouword.cli — Mrliouword 命令列介面入口

CLI 是 Mrliouword 系統的正式命令列服務入口（pyproject.toml 中宣告為 mrliouword = "mrliouword.cli:main"）。

用法::

    mrliouword health            # 執行健康檢查
    mrliouword version           # 顯示版本資訊
    mrliouword config get <key>  # 讀取設定值
    mrliouword config set <key> <value>  # 寫入設定值
    mrliouword trace emit <event_type> [--payload '{"key": "value"}']
    mrliouword memory store <content_json>
    mrliouword api serve [--host 0.0.0.0] [--port 7771]  # 啟動 API server

所有輸出均為 JSON 格式，方便與其他系統整合。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional


def _print_json(obj: Any, pretty: bool = True) -> None:
    indent = 2 if pretty else None
    print(json.dumps(obj, ensure_ascii=False, indent=indent))


# ── 子命令處理器 ───────────────────────────────────────────────────────────────

def cmd_version(_args: argparse.Namespace) -> int:
    from mrliouword import __version__, __product__, __origin_signature__
    _print_json({
        "product": __product__,
        "version": __version__,
        "origin_signature": __origin_signature__,
        "python_package": "mrliouword",
        "cli": "mrliouword",
    })
    return 0


def cmd_health(_args: argparse.Namespace) -> int:
    from mrliouword.api import HealthProbe
    probe = HealthProbe()
    status = probe.check()
    _print_json(status.to_dict())
    return 0 if status.ok else 1


def cmd_config_get(args: argparse.Namespace) -> int:
    from mrliouword.config import MrliouwordConfig
    cfg = MrliouwordConfig()
    val = cfg.get(args.key)
    _print_json({"key": args.key, "value": val})
    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    from mrliouword.config import MrliouwordConfig
    cfg = MrliouwordConfig()
    try:
        value: Any = json.loads(args.value)
    except (json.JSONDecodeError, ValueError):
        value = args.value
    cfg.set(args.key, value)
    cfg.save()
    _print_json({"key": args.key, "value": value, "status": "saved"})
    return 0


def cmd_config_show(_args: argparse.Namespace) -> int:
    from mrliouword.config import MrliouwordConfig
    cfg = MrliouwordConfig()
    _print_json(cfg.dump(mask_secrets=True))
    return 0


def cmd_trace_emit(args: argparse.Namespace) -> int:
    import tempfile, pathlib
    from mrliouword.trace import Tracer
    from mrliouword.schemas import TraceEvent
    try:
        payload: Dict[str, Any] = json.loads(args.payload) if args.payload else {}
    except json.JSONDecodeError as exc:
        _print_json({"error": f"invalid payload JSON: {exc}"})
        return 1

    # 在 CI / test 環境中使用 tempdir 避免寫入生產路徑
    import os
    data_dir: Optional[pathlib.Path] = None
    if os.environ.get("MRL_RUNTIME_MODE") == "test":
        data_dir = pathlib.Path(tempfile.mkdtemp()) / "trace"

    tracer = Tracer(data_dir=data_dir)
    event = TraceEvent(event_type=args.event_type, payload=payload)
    result = tracer.emit(event)
    _print_json(result)
    return 0


def cmd_memory_store(args: argparse.Namespace) -> int:
    import tempfile, pathlib
    from mrliouword.memory import MemoryStore
    try:
        content: Dict[str, Any] = json.loads(args.content)
    except json.JSONDecodeError as exc:
        _print_json({"error": f"invalid content JSON: {exc}"})
        return 1

    import os
    data_dir: Optional[pathlib.Path] = None
    if os.environ.get("MRL_RUNTIME_MODE") == "test":
        data_dir = pathlib.Path(tempfile.mkdtemp()) / "memory"

    store = MemoryStore(data_dir=data_dir)
    entry_id = store.store(content)
    _print_json({"entry_id": entry_id, "status": "stored"})
    return 0


def cmd_api_serve(args: argparse.Namespace) -> int:
    """啟動 API server（委派給 09_workflow/api_gateway.py）。"""
    import pathlib, sys
    workflow_dir = pathlib.Path(__file__).resolve().parent.parent / "09_workflow"
    sys.path.insert(0, str(workflow_dir))
    try:
        import api_gateway
        api_gateway.serve(host=args.host, port=args.port)
    except AttributeError:
        # api_gateway.py 使用 argparse 啟動，改用 subprocess
        import subprocess
        cmd = [
            sys.executable,
            str(workflow_dir / "api_gateway.py"),
            "serve",
            "--host", args.host,
            "--port", str(args.port),
        ]
        proc = subprocess.run(cmd)
        return proc.returncode
    return 0


# ── 主入口 ─────────────────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mrliouword",
        description="Mrliouword — 唯一權威母體系統 CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # version
    sub.add_parser("version", help="顯示版本資訊")

    # health
    sub.add_parser("health", help="執行健康檢查")

    # config
    cfg_parser = sub.add_parser("config", help="設定管理")
    cfg_sub = cfg_parser.add_subparsers(dest="config_cmd", required=True)
    cfg_get = cfg_sub.add_parser("get", help="讀取設定值")
    cfg_get.add_argument("key", help="設定鍵（如 llm.default_model）")
    cfg_set = cfg_sub.add_parser("set", help="寫入設定值")
    cfg_set.add_argument("key", help="設定鍵")
    cfg_set.add_argument("value", help="設定值（支援 JSON 字串）")
    cfg_sub.add_parser("show", help="顯示完整設定")

    # trace
    trace_parser = sub.add_parser("trace", help="追蹤操作")
    trace_sub = trace_parser.add_subparsers(dest="trace_cmd", required=True)
    trace_emit = trace_sub.add_parser("emit", help="發送追蹤事件")
    trace_emit.add_argument("event_type", help="事件類型")
    trace_emit.add_argument("--payload", default=None, help="JSON payload 字串")

    # memory
    mem_parser = sub.add_parser("memory", help="記憶操作")
    mem_sub = mem_parser.add_subparsers(dest="memory_cmd", required=True)
    mem_store = mem_sub.add_parser("store", help="儲存記憶條目")
    mem_store.add_argument("content", help="JSON 內容字串")

    # api
    api_parser = sub.add_parser("api", help="API server 操作")
    api_sub = api_parser.add_subparsers(dest="api_cmd", required=True)
    api_serve = api_sub.add_parser("serve", help="啟動 API server")
    api_serve.add_argument("--host", default="127.0.0.1", help="綁定位址")
    api_serve.add_argument("--port", type=int, default=7771, help="綁定埠號")

    args = parser.parse_args(argv)

    dispatch: Dict[str, Any] = {
        "version": cmd_version,
        "health": cmd_health,
    }

    if args.command in dispatch:
        return dispatch[args.command](args)

    if args.command == "config":
        cfg_dispatch = {
            "get": cmd_config_get,
            "set": cmd_config_set,
            "show": cmd_config_show,
        }
        return cfg_dispatch[args.config_cmd](args)

    if args.command == "trace":
        if args.trace_cmd == "emit":
            return cmd_trace_emit(args)

    if args.command == "memory":
        if args.memory_cmd == "store":
            return cmd_memory_store(args)

    if args.command == "api":
        if args.api_cmd == "serve":
            return cmd_api_serve(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
