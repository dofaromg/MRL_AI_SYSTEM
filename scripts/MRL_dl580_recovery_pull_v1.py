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
#          5 另一個 pull 正在進行（鎖檔存在）｜6 磁碟剩餘空間不足
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ORIGIN_SIGNATURE = "MrLiouWord"
SYNCED_MARKERS = ("dropbox", "onedrive", "google drive", "googledrive", "icloud")
DEFAULT_TIMEOUT_SEC = 6 * 3600
DEFAULT_MIN_FREE_GB = 1.0
LOCK_NAME = ".pull.lock"
PARTIAL_PREFIX = ".partial-"   # git 暫存目錄（clone 完成並 checkout 成功後才改名為正式修訂目錄）
RCLONE_RETRY_ARGS = ["--retries", "3", "--low-level-retries", "10"]
GIT_ENV = {"GIT_TERMINAL_PROMPT": "0"}  # 需要憑證時直接失敗，不在無人值守時卡在提示上
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
            *RCLONE_RETRY_ARGS, *source.get("extra_args", [])]


def _fail(r) -> str:
    return (r.stderr or r.stdout or "")[-500:] or f"exit {r.returncode}"


def _git_env() -> dict:
    return {**os.environ, **GIT_ENV}


def pull_git(source: dict, dst: pathlib.Path, runner, timeout) -> tuple[bool, str]:
    """每個遠端 HEAD 修訂存成獨立目錄 <dst>/<sha前12碼>；已有的修訂不動，新修訂不會覆蓋舊的。
    先在 .partial-<sha前12碼> 完成 clone＋checkout，成功後才改名：中途失敗不會留下
    『看起來完整、其實缺檔』的修訂目錄（下次執行會把它當作已完成而跳過）。"""
    kw = dict(capture_output=True, text=True, timeout=timeout, env=_git_env())
    r = runner(["git", "ls-remote", source["url"], "HEAD"], **kw)
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
    partial = dst / f"{PARTIAL_PREFIX}{sha[:12]}"
    if partial.exists():  # 前次中斷留下的本程式暫存目錄（不是已回收資料）；清掉重來
        shutil.rmtree(partial, ignore_errors=True)
    for cmd in (["git", "clone", source["url"], str(partial)],
                ["git", "-C", str(partial), "checkout", "--detach", sha]):
        r = runner(cmd, **kw)
        if r.returncode != 0:
            shutil.rmtree(partial, ignore_errors=True)
            return False, _fail(r)
    os.rename(partial, target)
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
            for repo in sorted(g.parent for g in src_dir.glob("*/.git")
                               if not g.parent.name.startswith(PARTIAL_PREFIX)):
                rows.append({"source": src_dir.name, "path": f"{repo.name}/.git(HEAD)",
                             "git_head": git_head(repo, runner)})
        for f in sorted(src_dir.rglob("*")):
            rel = f.relative_to(src_dir)
            if not f.is_file() or (is_git and ".git" in rel.parts):
                continue
            if is_git and rel.parts[0].startswith(PARTIAL_PREFIX):
                continue  # 未完成的暫存目錄不屬於回收資料
            size = f.stat().st_size
            rows.append({
                "source": src_dir.name, "path": rel.as_posix(), "size": size,
                "sha256": sha256_file(f),
                "zero_byte": size == 0 and not is_git,  # git 倉庫內的空檔（.keep、__init__.py）屬正常
            })
    return rows


def _fsync_dir(path: pathlib.Path) -> None:
    try:  # Windows 不支援對目錄 fsync；略過即可
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def write_manifest(out: pathlib.Path, rows: list[dict]) -> pathlib.Path:
    """先把清單完整寫進暫存檔並 fsync，再把雜湊追加進 SHA256SUMS（fsync），最後以排他方式
    連結成正式檔名。中途斷電只可能留下『有雜湊記錄但無清單』（verify 會忽略孤立記錄），
    不會出現『有清單但沒有雜湊記錄』的半成品。"""
    tmp = out / f".MANIFEST_tmp.{os.getpid()}"
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    digest = sha256_file(tmp)
    stem, n = f"MANIFEST_{utc_now()}", 0
    try:
        while True:  # 排他建立，不覆蓋既有清單
            name = f"{stem}.jsonl" if n == 0 else f"{stem}_{n}.jsonl"
            if (out / name).exists():
                n += 1
                continue
            with (out / "SHA256SUMS").open("a", encoding="utf-8") as f:
                f.write(f"{digest}  {name}\n")
                f.flush()
                os.fsync(f.fileno())
            try:
                try:
                    os.link(tmp, out / name)  # 目標已存在會丟 FileExistsError，不會覆蓋
                except FileExistsError:
                    raise
                except OSError:  # 檔案系統不支援硬連結（exFAT、部分網路磁碟）：改用排他建立＋複製
                    with (out / name).open("xb") as dst_fh, tmp.open("rb") as src_fh:
                        shutil.copyfileobj(src_fh, dst_fh)
                        dst_fh.flush()
                        os.fsync(dst_fh.fileno())
                break
            except FileExistsError:
                n += 1
    finally:
        tmp.unlink(missing_ok=True)
    _fsync_dir(out)
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


def _load_manifest_rows(m: pathlib.Path) -> list[dict]:
    rows = []
    for i, line in enumerate(m.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{m.name} 第 {i} 行不是合法 JSON: {e}") from e
        if not isinstance(r, dict):
            raise ValueError(f"{m.name} 第 {i} 行不是物件")
        rows.append(r)
    return rows


def verify(out: pathlib.Path) -> dict:
    """ok 只在：每份清單的雜湊都對得上 SHA256SUMS、清單內每個檔案都存在且雜湊一致時為 True。
    unlisted（磁碟上有、但任何清單都沒記的檔案）與 orphan_sums（有記錄但清單不存在）只是提示，
    不影響 ok——它們代表『尚未被清單涵蓋』，不代表已回收資料受損。"""
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
    try:
        for m in manifests:  # 以最早記錄為準：之後同一路徑雜湊改變即視為異動
            for r in _load_manifest_rows(m):
                if "sha256" in r:
                    expected.setdefault((r["source"], r["path"]), r["sha256"])
    except (ValueError, KeyError, UnicodeDecodeError) as e:
        return {"ok": False, "error": f"清單內容無法解析: {e}"}
    missing, changed = [], []
    for (src, rel), digest in expected.items():
        f = out / src / rel
        try:
            if not f.is_file():
                missing.append(f"{src}/{rel}")
            elif sha256_file(f) != digest:
                changed.append(f"{src}/{rel}")
        except OSError as e:  # 權限或 I/O 錯誤：無法確認就不能算通過
            changed.append(f"{src}/{rel} (無法讀取: {e})")
    orphan_sums = sorted(n for n in sums if n.startswith("MANIFEST_") and not (out / n).is_file())
    listed = {(a, b) for a, b in expected}
    unlisted = []
    for src_dir in sorted(p for p in out.iterdir() if p.is_dir()):
        for f in sorted(src_dir.rglob("*")):
            rel = f.relative_to(src_dir)
            if not f.is_file() or rel.parts[0].startswith(PARTIAL_PREFIX):
                continue
            if (src_dir.name, rel.as_posix()) not in listed and ".git" not in rel.parts:
                unlisted.append(f"{src_dir.name}/{rel.as_posix()}")
    return {"ok": not missing and not changed, "checked": len(expected), "missing": missing,
            "changed": changed, "orphan_sums": orphan_sums, "unlisted": unlisted}


# ── 執行保護：鎖檔與磁碟空間 ────────────────────────────────────────────────
class PullLockHeld(RuntimeError):
    pass


class pull_lock:
    """同一個輸出目錄同時只允許一個 pull（兩個程序交錯寫入會讓清單與實際檔案對不上）。
    鎖檔記錄 pid 與開始時間。程序被強制終止後鎖檔會殘留：確認沒有 pull 在跑後，手動刪除即可。"""

    def __init__(self, out: pathlib.Path):
        self.path = out / LOCK_NAME

    def __enter__(self):
        try:
            with self.path.open("x", encoding="utf-8") as f:
                f.write(json.dumps({"pid": os.getpid(), "started": utc_now()}))
        except FileExistsError:
            try:
                info = self.path.read_text(encoding="utf-8")
            except OSError:
                info = "?"
            raise PullLockHeld(f"{self.path} 已存在（{info}）；若確定沒有其他 pull 在執行，請手動刪除後重試。")
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def free_gb(path: pathlib.Path) -> float:
    return shutil.disk_usage(path).free / 1024 ** 3


# ── CLI ────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MRL 資料回收：DL580 本機拉取＋雜湊清單（Issue #146）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help="每個來源的逾時秒數（0 表示不限）")
    p.add_argument("--min-free-gb", type=float, default=DEFAULT_MIN_FREE_GB,
                   help="輸出磁碟剩餘空間低於此值（GB）就拒絕開始；0 表示不檢查")
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
        if res.get("unlisted"):
            print(f"NOTE: {len(res['unlisted'])} 個檔案不在任何清單內（尚未被涵蓋，不影響 ok）。", file=sys.stderr)
        return 0 if res["ok"] else 1

    if is_synced_path(out) and not args.allow_synced:
        print(f"拒絕：{out} 位於雲端同步資料夾；資料不放平台。請改用本機路徑（例如 D:\\mrl\\recovery\\store）。",
              file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    sources = load_plan(pathlib.Path(args.plan))
    if args.min_free_gb and free_gb(out) < args.min_free_gb:
        print(f"拒絕：{out} 剩餘 {free_gb(out):.2f} GB，低於 --min-free-gb {args.min_free_gb}。", file=sys.stderr)
        return 6
    try:
        with pull_lock(out):
            results = pull(sources, out, timeout=args.timeout or None)
            rows = build_manifest(out, git_sources={s["name"] for s in sources if s["kind"] == "git"})
            manifest = write_manifest(out, rows)
    except PullLockHeld as e:
        print(f"拒絕：{e}", file=sys.stderr)
        return 5
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
