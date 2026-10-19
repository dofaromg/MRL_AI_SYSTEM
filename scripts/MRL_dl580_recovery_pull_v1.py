#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MRL_dl580_recovery_pull_v1 — 把散在雲端的 MRL 資料拉回 DL580「本機」並建立雜湊清單（Issue #146 資料回收）
# origin_signature: MrLiouWord
#
# 設計約束（對應建構者指示：資料不放平台、Additive-Only）：
#   - 只在 DL580 本機執行；輸出目錄不得位於雲端同步資料夾（Dropbox/OneDrive/Google Drive），除非明確 --allow-synced。
#   - 只新增、不刪除、不覆蓋：rclone 只用 `copy --immutable`（絕不用 sync/move/delete）；
#     git 來源每個遠端 HEAD 修訂各自存成 <來源名>/<sha前12碼>/ 目錄，已有的修訂不動。
#   - 不讀取、不保存任何憑證：雲端授權由 DL580 上已設定好的 rclone 提供。
#   - 每次拉取後建立 MANIFEST_<UTC>.jsonl（排他建立）＋ SHA256SUMS（追加）；verify 會先核對清單本身的雜湊。
#   - 空結果與 0 位元組檔案不當成成功備份（需明確 --allow-empty / --accept-zero-byte）。
#
# 用法（DL580，PowerShell 或 bash）：
#   python scripts/MRL_dl580_recovery_pull_v1.py pull   --plan D:\mrl\recovery\plan.json --out D:\mrl\recovery\store
#   python scripts/MRL_dl580_recovery_pull_v1.py verify --out D:\mrl\recovery\store
# plan.json 格式見 scripts/MRL_dl580_recovery_plan.example.json（複製後在本機填入，勿提交含私人 ID 的版本）。
# 結束碼：0 成功｜1 verify 失敗｜2 輸出路徑在同步資料夾｜3 有來源拉取失敗或結果為空｜4 有 0 位元組檔案未被接受
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ORIGIN_SIGNATURE = "MrLiouWord"
SYNCED_MARKERS = ("dropbox", "onedrive", "google drive", "googledrive", "icloud")
DEFAULT_TIMEOUT_SEC = 6 * 3600
_SHA_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")


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
def rclone_command(source: dict, dst: pathlib.Path) -> list[str]:
    src = source["remote"] + source.get("path", "")
    return ["rclone", "copy", src, str(dst), "--immutable", "--create-empty-src-dirs",
            *source.get("extra_args", [])]


def _fail(r) -> str:
    return (r.stderr or r.stdout or "")[-500:] or f"exit {r.returncode}"


def pull_git(source: dict, dst: pathlib.Path, runner, timeout) -> tuple[bool, str]:
    """每個遠端 HEAD 修訂存成獨立目錄 <dst>/<sha前12碼>；已有的修訂不動，新修訂不會覆蓋舊的。"""
    r = runner(["git", "ls-remote", source["url"], "HEAD"], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return False, _fail(r)
    parts = (r.stdout or "").split()
    sha = parts[0] if parts else ""
    if not _SHA_RE.match(sha):
        return False, "無法取得遠端 HEAD 修訂"
    target = dst / sha[:12]
    if (target / ".git").exists():
        return True, ""
    dst.mkdir(parents=True, exist_ok=True)
    for cmd in (["git", "clone", source["url"], str(target)],
                ["git", "-C", str(target), "checkout", "--detach", sha]):
        r = runner(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            return False, _fail(r)
    return True, ""


def pull(sources: list[dict], out: pathlib.Path, runner=None, timeout=DEFAULT_TIMEOUT_SEC) -> dict:
    real = runner is None  # 實機執行才檢查工具是否安裝；測試注入假 runner 時略過
    runner = runner or subprocess.run
    results: dict[str, dict] = {}
    for s in sources:
        tool = "rclone" if s["kind"] == "rclone" else "git"
        if real and shutil.which(tool) is None:
            results[s["name"]] = {"ok": False, "error": f"找不到 {tool}，請先在 DL580 安裝並設定"}
            continue
        dst = out / s["name"]
        try:
            if s["kind"] == "rclone":
                dst.parent.mkdir(parents=True, exist_ok=True)
                r = runner(rclone_command(s, dst), capture_output=True, text=True, timeout=timeout)
                ok, err = r.returncode == 0, ("" if r.returncode == 0 else _fail(r))
            else:
                ok, err = pull_git(s, dst, runner, timeout)
        except subprocess.TimeoutExpired:
            ok, err = False, f"逾時（>{timeout}s），已中止此來源"
        results[s["name"]] = {"ok": ok, **({"error": err} if err else {})}
    return results


# ── 清單與驗證 ──────────────────────────────────────────────────────────────
def git_head(repo: pathlib.Path, runner=None) -> str | None:
    runner = runner or subprocess.run
    try:
        r = runner(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def build_manifest(out: pathlib.Path, git_sources=frozenset(), runner=None) -> list[dict]:
    """git_sources：由 git 取得的來源名稱。只有這些來源的 .git 內容不逐檔雜湊（改記 HEAD 修訂）；
    rclone 來源裡若有 .git 目錄，視為資料一併雜湊。"""
    rows: list[dict] = []
    for src_dir in sorted(p for p in out.iterdir() if p.is_dir()):
        is_git = src_dir.name in git_sources
        if is_git:
            for repo in sorted(g.parent for g in src_dir.glob("*/.git")):
                rows.append({"source": src_dir.name, "path": f"{repo.name}/.git(HEAD)",
                             "git_head": git_head(repo, runner)})
        for f in sorted(src_dir.rglob("*")):
            rel = f.relative_to(src_dir)
            if not f.is_file() or (is_git and ".git" in rel.parts):
                continue
            size = f.stat().st_size
            rows.append({
                "source": src_dir.name, "path": rel.as_posix(), "size": size,
                "sha256": sha256_file(f),
                "zero_byte": size == 0 and not is_git,  # git 倉庫內的空檔（.keep、__init__.py）屬正常
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


def _read_sums(out: pathlib.Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    p = out / "SHA256SUMS"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "  " in line:
                digest, name = line.split("  ", 1)
                sums.setdefault(name, digest)
    return sums


def verify(out: pathlib.Path) -> dict:
    manifests = sorted(out.glob("MANIFEST_*.jsonl"))
    if not manifests:
        return {"ok": False, "error": "沒有 MANIFEST 可驗證"}
    sums = _read_sums(out)
    for m in manifests:  # 先確認清單本身沒被動過，再信任其中的列
        if sums.get(m.name) is None:
            return {"ok": False, "error": f"SHA256SUMS 缺少清單記錄: {m.name}"}
        if sha256_file(m) != sums[m.name]:
            return {"ok": False, "error": f"清單雜湊不符（可能被修改或損毀）: {m.name}"}
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
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help="每個來源的逾時秒數（0 表示不限）")
    p.add_argument("--allow-synced", action="store_true", help="允許輸出到雲端同步資料夾（不建議）")
    p.add_argument("--allow-empty", action="store_true", help="接受來源本來就沒有檔案")
    p.add_argument("--accept-zero-byte", action="store_true", help="接受 0 位元組檔案（已確認它們就是預期資料）")
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
    sources = load_plan(pathlib.Path(args.plan))
    results = pull(sources, out, timeout=args.timeout or None)
    rows = build_manifest(out, git_sources={s["name"] for s in sources if s["kind"] == "git"})
    manifest = write_manifest(out, rows)
    counts: dict[str, int] = {}
    for r in rows:
        if "sha256" in r:
            counts[r["source"]] = counts.get(r["source"], 0) + 1
    if not args.allow_empty:  # 回報成功但沒有任何檔案，不能當成備份完成
        for name, r in results.items():
            if r["ok"] and counts.get(name, 0) == 0:
                results[name] = {"ok": False, "error": "來源沒有產生任何檔案（若本來就是空的，請加 --allow-empty）"}
    zero = [f"{r['source']}/{r['path']}" for r in rows if r.get("zero_byte")]
    print(f"manifest: {manifest}  files={sum(counts.values())}")
    for name, r in results.items():
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {name} files={counts.get(name, 0)} {r.get('error', '')}")
    if zero:
        print(f"WARNING: {len(zero)} 個 0 位元組檔案（可能是空殼，不可當成有效備份）：")
        for z in zero[:20]:
            print(f"  - {z}")
    if not all(r["ok"] for r in results.values()):
        return 3
    if zero and not args.accept_zero_byte:
        print("有 0 位元組檔案；確認它們就是預期資料後，加 --accept-zero-byte 重新執行以取得成功結束碼。",
              file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
