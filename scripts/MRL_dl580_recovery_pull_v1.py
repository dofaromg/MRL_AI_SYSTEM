#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MRL_dl580_recovery_pull_v1 — 把散在雲端的 MRL 資料拉回 DL580「本機」並建立雜湊清單（Issue #146 資料回收）
# origin_signature: MrLiouWord
#
# 設計約束（對應建構者指示：資料不放平台、Additive-Only）：
#   - 只在 DL580 本機執行；輸出目錄不得位於雲端同步資料夾（Dropbox/OneDrive/Google Drive），除非明確 --allow-synced。
#   - 只新增、不刪除、不覆蓋：rclone 只用 `copy --immutable`（絕不用 sync/move/delete）；git 只 clone/fetch。
#   - 不讀取、不保存任何憑證：雲端授權由 DL580 上已設定好的 rclone 提供。
#   - 每次拉取後建立 MANIFEST_<UTC>.jsonl（排他建立）＋ SHA256SUMS（追加），可用 verify 重驗。
#   - 0 位元組檔案會被標記（Drive 上 Manus 代存的檔案曾是空殼），不當成成功備份。
#
# 用法（DL580，PowerShell 或 bash）：
#   python scripts/MRL_dl580_recovery_pull_v1.py pull   --plan D:\mrl\recovery\plan.json --out D:\mrl\recovery\store
#   python scripts/MRL_dl580_recovery_pull_v1.py verify --out D:\mrl\recovery\store
# plan.json 格式見 scripts/MRL_dl580_recovery_plan.example.json（複製後在本機填入，勿提交含私人 ID 的版本）。
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ORIGIN_SIGNATURE = "MrLiouWord"
SYNCED_MARKERS = ("dropbox", "onedrive", "google drive", "googledrive", "icloud")
SKIP_DIRS = {".git"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ── 安全檢查與計畫驗證 ──────────────────────────────────────────────────────
def is_synced_path(path: pathlib.Path) -> bool:
    low = str(path.resolve()).lower()
    return any(m in low for m in SYNCED_MARKERS)


def load_plan(path: pathlib.Path) -> list[dict]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    sources = plan.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("plan.sources 必須是非空陣列")
    seen = set()
    for s in sources:
        name = s.get("name", "")
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            raise ValueError(f"來源名稱不合法: {name!r}")
        if name in seen:
            raise ValueError(f"來源名稱重複: {name}")
        seen.add(name)
        kind = s.get("kind")
        if kind == "rclone":
            if not s.get("remote", "").endswith(":"):
                raise ValueError(f"{name}: remote 需為 'name:' 形式")
        elif kind == "git":
            if not s.get("url", "").startswith("https://"):
                raise ValueError(f"{name}: git url 必須是 https://")
        else:
            raise ValueError(f"{name}: kind 只能是 rclone 或 git")
    return sources


# ── 拉取（只新增）──────────────────────────────────────────────────────────
def build_commands(source: dict, dst: pathlib.Path) -> list[list[str]]:
    if source["kind"] == "rclone":
        src = source["remote"] + source.get("path", "")
        return [["rclone", "copy", src, str(dst), "--immutable", "--create-empty-src-dirs",
                 *source.get("extra_args", [])]]
    if (dst / ".git").exists():
        return [["git", "-C", str(dst), "fetch", "--all", "--tags"]]
    return [["git", "clone", source["url"], str(dst)]]


def pull(sources: list[dict], out: pathlib.Path, runner=subprocess.run) -> dict:
    results: dict[str, dict] = {}
    for s in sources:
        tool = "rclone" if s["kind"] == "rclone" else "git"
        if runner is subprocess.run and shutil.which(tool) is None:
            results[s["name"]] = {"ok": False, "error": f"找不到 {tool}，請先在 DL580 安裝並設定"}
            continue
        dst = out / s["name"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        ok, err = True, ""
        for cmd in build_commands(s, dst):
            r = runner(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                ok, err = False, (r.stderr or r.stdout or "")[-500:]
                break
        results[s["name"]] = {"ok": ok, **({"error": err} if err else {})}
    return results


# ── 清單與驗證 ──────────────────────────────────────────────────────────────
def git_head(repo: pathlib.Path, runner=subprocess.run) -> str | None:
    try:
        r = runner(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def build_manifest(out: pathlib.Path, runner=subprocess.run) -> list[dict]:
    rows: list[dict] = []
    for src_dir in sorted(p for p in out.iterdir() if p.is_dir()):
        is_git = (src_dir / ".git").exists()  # git 倉庫內的空檔（.keep、__init__.py）是正常的，不當空殼警告
        if is_git:
            rows.append({"source": src_dir.name, "path": ".git(HEAD)", "git_head": git_head(src_dir, runner)})
        for f in sorted(src_dir.rglob("*")):
            if not f.is_file() or SKIP_DIRS & set(f.relative_to(src_dir).parts):
                continue
            size = f.stat().st_size
            rows.append({
                "source": src_dir.name, "path": f.relative_to(src_dir).as_posix(), "size": size,
                "sha256": sha256_file(f), "zero_byte": size == 0 and not is_git,
            })
    return rows


def write_manifest(out: pathlib.Path, rows: list[dict]) -> pathlib.Path:
    stem, n = f"MANIFEST_{utc_now()}", 0
    while True:  # 排他建立，不覆蓋既有清單
        name = f"{stem}.jsonl" if n == 0 else f"{stem}_{n}.jsonl"
        try:
            with (out / name).open("x", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            break
        except FileExistsError:
            n += 1
    digest = sha256_file(out / name)
    with (out / "SHA256SUMS").open("a", encoding="utf-8") as f:
        f.write(f"{digest}  {name}\n")
    return out / name


def verify(out: pathlib.Path) -> dict:
    manifests = sorted(out.glob("MANIFEST_*.jsonl"))
    if not manifests:
        return {"ok": False, "error": "沒有 MANIFEST 可驗證"}
    expected: dict[tuple, str] = {}
    for m in manifests:  # 以最早記錄為準：之後同一路徑雜湊改變即視為異動
        for line in m.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "sha256" in r:
                expected.setdefault((r["source"], r["path"]), r["sha256"])
    missing, changed = [], []
    for (src, rel), digest in expected.items():
        f = out / src / rel
        if not f.is_file():
            missing.append(f"{src}/{rel}")
        elif sha256_file(f) != digest:
            changed.append(f"{src}/{rel}")
    return {"ok": not missing and not changed, "checked": len(expected), "missing": missing, "changed": changed}


# ── CLI ────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MRL 資料回收：DL580 本機拉取＋雜湊清單（Issue #146）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--allow-synced", action="store_true", help="允許輸出到雲端同步資料夾（不建議）")
    v = sub.add_parser("verify")
    v.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)

    if args.cmd == "verify":
        res = verify(out)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1

    if is_synced_path(out) and not args.allow_synced:
        print(f"拒絕：{out} 位於雲端同步資料夾；資料不放平台。請改用本機路徑（例如 D:\\mrl\\recovery\\store）。",
              file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    results = pull(load_plan(pathlib.Path(args.plan)), out)
    rows = build_manifest(out)
    manifest = write_manifest(out, rows)
    zero = [f"{r['source']}/{r['path']}" for r in rows if r.get("zero_byte")]
    print(f"manifest: {manifest}  files={sum(1 for r in rows if 'sha256' in r)}")
    for name, r in results.items():
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {name} {r.get('error', '')}")
    if zero:
        print(f"WARNING: {len(zero)} 個 0 位元組檔案（可能是空殼，不可當成有效備份）：")
        for z in zero[:20]:
            print(f"  - {z}")
    return 0 if all(r["ok"] for r in results.values()) else 3


if __name__ == "__main__":
    sys.exit(main())
