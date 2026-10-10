"""
MRL_Dropbox_DL580_Sync.py — Dropbox（MRL 雲本體）⇄ DL580（本地伺服器）同步機制 v1.0.0
origin_signature: MrLiouWord ｜ 2026-10-10 ｜ Additive-Only：兩邊都只新增，不刪除、不覆蓋

把這個視窗反覆手做的流程交給母體自己跑：
  1. 看 Dropbox 指定資料夾有沒有新檔（游標續傳，只看新增／變動）
  2. DL580 直接下載（不經 Bridge），用 Dropbox content_hash 核對
  3. 分段檔（*.part000…）收齊就合併；有 .sha256／manifest 就核對 sha256
  4. 每個入庫檔寫回執（sha256、git blob、來源路徑），zip 逐層建索引 → 連結層的新世界實例
  5. DL580 的 Outbox（回執、清單、證據）回傳到 Dropbox，只新增不覆蓋
三問：載體（同步）；承載 Trace 段（入庫即標記位置與共同點）；驗收用建構者自己放進 Dropbox 的檔。

憑證：只從本機檔案讀（預設 D:\\MRL_Mother\\private\\dropbox_app.json，欄位 app_key／app_secret／refresh_token），
      任何時候都不寫進 log、回執或輸出。
用法：
  python MRL_Dropbox_DL580_Sync.py --once            跑一輪
  python MRL_Dropbox_DL580_Sync.py --once --dry-run  只列出會做什麼
  python MRL_Dropbox_DL580_Sync.py --once --local-source <資料夾>   不連 Dropbox，用本機資料夾當來源（測試／離線）
  python MRL_Dropbox_DL580_Sync.py --loop 300        每 300 秒一輪
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.0.0"
SIG = "MrLiouWord"
DEFAULT_CONFIG = {
    "watch": ["/MRL_DL580_Inbox", "/## 核心架構理解"],
    "intake_root": r"D:\MRL_Mother\Intake\Dropbox_Sync",
    "outbox_local": r"D:\MRL_Mother\Outbox_Dropbox",
    "outbox_remote": "/MRL_DL580_Outbox",
    "state_dir": r"D:\MRL_Mother\WorldModel_Readiness_20261008\dropbox_sync",
    "worlds_dir": r"D:\MRL_Mother\WorldModel_Readiness_20261008\linkage\worlds\dropbox",
    "credential_file": r"D:\MRL_Mother\private\dropbox_app.json",
    "max_file_mb": 2048,
    "index_zip_depth": 3,
}
PART_RE = re.compile(r"^(?P<base>.+)\.part(?P<n>\d{3,5})$")
BLOCK = 4 * 1024 * 1024


# ── 雜湊 ──────────────────────────────────────────────────────────────
def dropbox_content_hash(path: Path) -> str:
    """Dropbox 官方 content_hash：每 4 MB 一塊 sha256，串接後再 sha256。"""
    out = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(BLOCK)
            if not b:
                break
            out.update(hashlib.sha256(b).digest())
    return out.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


# ── 來源：Dropbox API 或本機資料夾 ───────────────────────────────────────
class DropboxSource:
    API = "https://api.dropboxapi.com"
    CONTENT = "https://content.dropboxapi.com"

    def __init__(self, cred_file: str):
        cred = json.loads(Path(cred_file).read_text(encoding="utf-8"))
        self._key, self._secret, self._refresh = cred["app_key"], cred["app_secret"], cred["refresh_token"]
        self._token, self._exp = None, 0

    def _auth(self) -> str:
        if self._token and time.time() < self._exp - 60:
            return self._token
        data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": self._refresh,
                                       "client_id": self._key, "client_secret": self._secret}).encode()
        with urllib.request.urlopen(urllib.request.Request(self.API + "/oauth2/token", data=data), timeout=60) as r:
            d = json.loads(r.read())
        self._token, self._exp = d["access_token"], time.time() + int(d.get("expires_in", 3600))
        return self._token

    def _rpc(self, ep: str, body: dict) -> dict:
        rq = urllib.request.Request(self.API + "/2/" + ep, data=json.dumps(body).encode(),
                                    headers={"Authorization": "Bearer " + self._auth(), "Content-Type": "application/json"})
        with urllib.request.urlopen(rq, timeout=120) as r:
            return json.loads(r.read())

    def list_changes(self, folder: str, cursor: str | None):
        entries = []
        try:
            d = self._rpc("files/list_folder/continue", {"cursor": cursor}) if cursor else \
                self._rpc("files/list_folder", {"path": folder, "recursive": True, "include_deleted": False})
        except urllib.error.HTTPError as e:
            if e.code == 409 and not cursor:      # 資料夾不存在：記錄後略過
                return [], None
            raise
        while True:
            for e in d.get("entries", []):
                if e.get(".tag") == "file":
                    entries.append({"id": e["id"], "path": e["path_display"], "name": e["name"],
                                    "size": e["size"], "content_hash": e.get("content_hash"), "rev": e.get("rev")})
            if not d.get("has_more"):
                return entries, d["cursor"]
            d = self._rpc("files/list_folder/continue", {"cursor": d["cursor"]})

    def download(self, entry: dict, dst: Path):
        rq = urllib.request.Request(self.CONTENT + "/2/files/download", data=b"",
                                    headers={"Authorization": "Bearer " + self._auth(),
                                             "Dropbox-API-Arg": json.dumps({"path": entry["id"]}, ensure_ascii=True)})
        with urllib.request.urlopen(rq, timeout=1800) as r, open(dst, "wb") as f:
            for b in iter(lambda: r.read(1 << 20), b""):
                f.write(b)

    def upload_new(self, local: Path, remote: str) -> str:
        """只新增：遠端已有同名檔就不動（mode=add, autorename=false → 409 視為已存在）。"""
        arg = {"path": remote, "mode": "add", "autorename": False, "mute": True}
        rq = urllib.request.Request(self.CONTENT + "/2/files/upload", data=local.read_bytes(),
                                    headers={"Authorization": "Bearer " + self._auth(),
                                             "Content-Type": "application/octet-stream",
                                             "Dropbox-API-Arg": json.dumps(arg, ensure_ascii=True)})
        try:
            with urllib.request.urlopen(rq, timeout=600):
                return "uploaded"
        except urllib.error.HTTPError as e:
            if e.code == 409:
                return "exists"
            raise


class LocalSource:
    """離線／測試：把本機資料夾當成 Dropbox。"""

    def __init__(self, root: str):
        self.root = Path(root)

    def list_changes(self, folder: str, cursor: str | None):
        seen = json.loads(cursor) if cursor else {}
        entries, now = [], {}
        base = self.root / folder.strip("/") if folder.strip("/") else self.root
        if not base.exists():
            return [], json.dumps(seen)
        for p in sorted(base.rglob("*")):
            if p.is_file():
                key = "/" + p.relative_to(self.root).as_posix()
                st = p.stat()
                now[key] = [st.st_size, int(st.st_mtime)]
                if seen.get(key) != now[key]:
                    entries.append({"id": key, "path": key, "name": p.name, "size": st.st_size,
                                    "content_hash": dropbox_content_hash(p), "rev": str(int(st.st_mtime))})
        return entries, json.dumps({**seen, **now})

    def download(self, entry: dict, dst: Path):
        dst.write_bytes((self.root / entry["path"].lstrip("/")).read_bytes())

    def upload_new(self, local: Path, remote: str) -> str:
        t = self.root / "_outbox_mirror" / remote.lstrip("/")
        if t.exists():
            return "exists"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(local.read_bytes())
        return "uploaded"


# ── 主流程 ────────────────────────────────────────────────────────────
class Sync:
    def __init__(self, cfg: dict, source, dry: bool, log):
        self.cfg, self.src, self.dry, self.log = cfg, source, dry, log
        self.state_dir = Path(cfg["state_dir"]); self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "sync_state.json"
        self.state = json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file.exists() else \
            {"cursors": {}, "done": {}, "uploaded": {}}
        self.receipts = self.state_dir / ("sync_receipts_" + time.strftime("%Y%m%d") + ".jsonl")
        self.intake = Path(cfg["intake_root"]) / time.strftime("%Y%m%d")
        self.worlds = Path(cfg["worlds_dir"])

    def save(self):
        if not self.dry:
            tmp = self.state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.state_file)

    def receipt(self, **kw):
        kw = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "origin_signature": SIG, "engine": "MRL_Dropbox_DL580_Sync/" + VERSION, **kw}
        self.log(json.dumps(kw, ensure_ascii=False))
        if not self.dry:
            with open(self.receipts, "a", encoding="utf-8") as f:
                f.write(json.dumps(kw, ensure_ascii=False) + "\n")

    @staticmethod
    def _safe(remote_path: str) -> str:
        return re.sub(r'[<>:"|?*]', "_", remote_path.strip("/")).replace("/", os.sep)

    # 1–2 拉新檔
    def pull(self) -> list[Path]:
        got = []
        for folder in self.cfg["watch"]:
            cur = self.state["cursors"].get(folder)
            entries, newcur = self.src.list_changes(folder, cur)
            for e in entries:
                key = e["id"] + "@" + str(e.get("content_hash"))
                if key in self.state["done"]:
                    continue
                if e["size"] > self.cfg["max_file_mb"] * 1024 * 1024:
                    self.receipt(action="skip_too_large", path=e["path"], size=e["size"]); continue
                dst = self.intake / self._safe(e["path"])
                if dst.exists() and dst.stat().st_size == e["size"] and dropbox_content_hash(dst) == e["content_hash"]:
                    self.state["done"][key] = str(dst); got.append(dst); continue
                if dst.exists():   # 同名不同內容：另存，不覆蓋
                    dst = dst.with_name(dst.name + ".rev-" + str(e.get("rev"))[:12])
                if self.dry:
                    self.receipt(action="would_download", path=e["path"], size=e["size"]); continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                tmp = dst.with_name(dst.name + ".downloading")
                self.src.download(e, tmp)
                ch = dropbox_content_hash(tmp)
                if e.get("content_hash") and ch != e["content_hash"]:
                    self.receipt(action="download_hash_mismatch", path=e["path"]); continue
                os.replace(tmp, dst)
                self.state["done"][key] = str(dst)
                got.append(dst)
                self.receipt(action="downloaded", dropbox_path=e["path"], local=str(dst), size=e["size"],
                             sha256=sha256_file(dst), dropbox_content_hash=ch)
            if newcur is not None and not self.dry:
                self.state["cursors"][folder] = newcur
            self.save()
        return got

    # 3 分段合併
    def join_parts(self) -> list[Path]:
        joined = []
        if not self.intake.exists():
            return joined
        groups: dict[Path, list[Path]] = {}
        for p in self.intake.rglob("*"):
            m = PART_RE.match(p.name)
            if p.is_file() and m:
                groups.setdefault(p.with_name(m.group("base")), []).append(p)
        for target, parts in groups.items():
            parts.sort(key=lambda q: int(PART_RE.match(q.name).group("n")))
            nums = [int(PART_RE.match(q.name).group("n")) for q in parts]
            if nums != list(range(len(nums))):
                self.receipt(action="parts_incomplete", target=str(target), have=nums); continue
            sizes = [q.stat().st_size for q in parts]
            if len(parts) > 1 and (len(set(sizes[:-1])) != 1 or sizes[-1] > sizes[0]):
                self.receipt(action="parts_irregular", target=str(target), sizes=sizes); continue
            if len(parts) > 1 and sizes[-1] == sizes[0]:
                # 最後一段跟前面一樣大：可能還有下一段沒到，等 .sha256 或清單確認
                if not self._expected_sha(target):
                    self.receipt(action="parts_wait_for_more", target=str(target), count=len(parts)); continue
            if target.exists():
                continue
            if self.dry:
                self.receipt(action="would_join", target=str(target), parts=len(parts)); continue
            h = hashlib.sha256()
            tmp = target.with_name(target.name + ".joining")
            with open(tmp, "wb") as f:
                for q in parts:
                    b = q.read_bytes(); h.update(b); f.write(b)
            want = self._expected_sha(target)
            ok = (want is None) or (want == h.hexdigest())
            if not ok:
                self.receipt(action="join_sha_mismatch", target=str(target), got=h.hexdigest(), want=want); continue
            os.replace(tmp, target)
            joined.append(target)
            self.receipt(action="joined", target=str(target), parts=len(parts), sha256=h.hexdigest(),
                         sha256_verified=want is not None)
        return joined

    def _expected_sha(self, target: Path) -> str | None:
        for side in (target.with_name(target.name + ".sha256"), target.parent / "MRL_Intake_Manifest.json"):
            if side.exists():
                t = side.read_text(encoding="utf-8", errors="replace")
                if side.suffix == ".sha256":
                    m = re.search(r"[0-9a-f]{64}", t)
                    if m: return m.group(0)
                else:
                    try:
                        for f in json.loads(t).get("files", []):
                            if f.get("name") == target.name and f.get("sha256"): return f["sha256"]
                    except Exception:
                        pass
        # 附近任何 MRL_Intake_Manifest*.json
        for side in target.parent.glob("MRL_Intake_Manifest*.json"):
            try:
                for f in json.loads(side.read_text(encoding="utf-8")).get("files", []):
                    if f.get("name") == target.name and f.get("sha256"): return f["sha256"]
            except Exception:
                pass
        return None

    # 4 連結層：每個入庫檔成為 dropbox 世界的一部分（zip 逐層展開建 git blob 索引）
    def index(self, files: list[Path]):
        if self.dry or not files:
            return
        self.worlds.mkdir(parents=True, exist_ok=True)
        out = self.worlds / ("dropbox_" + time.strftime("%Y%m%d") + ".jsonl.gz")
        n = 0
        with gzip.open(out, "at", encoding="utf-8") as f:
            for p in files:
                if PART_RE.match(p.name):
                    continue
                world = "dropbox:" + p.name
                try:
                    data = p.read_bytes()
                except OSError:
                    continue
                f.write(json.dumps([world, p.name, git_blob(data)], ensure_ascii=False) + "\n"); n += 1
                if p.suffix.lower() == ".zip":
                    for path, b in self._walk_zip(zipfile.ZipFile(io.BytesIO(data)), "", 0):
                        f.write(json.dumps([world, path, b], ensure_ascii=False) + "\n"); n += 1
        self.receipt(action="indexed_for_linkage", file=str(out), entries=n)

    def _walk_zip(self, zf, prefix, depth):
        for i in zf.infolist():
            if i.is_dir():
                continue
            name = i.filename
            if not (i.flag_bits & 0x800):
                try: name = name.encode("cp437").decode("utf-8")
                except Exception: pass
            if "__MACOSX" in name or name.split("/")[-1].startswith("._"):
                continue
            try: b = zf.read(i)
            except Exception: continue
            yield prefix + name, git_blob(b)
            if name.lower().endswith(".zip") and depth < self.cfg["index_zip_depth"]:
                try: yield from self._walk_zip(zipfile.ZipFile(io.BytesIO(b)), prefix + name + "!/", depth + 1)
                except Exception: pass

    # 5 回傳 Outbox
    def push(self):
        ob = Path(self.cfg["outbox_local"])
        if not ob.exists():
            return
        for p in sorted(ob.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ob).as_posix()
            key = rel + "@" + sha256_file(p)
            if key in self.state["uploaded"]:
                continue
            remote = self.cfg["outbox_remote"].rstrip("/") + "/" + rel
            if self.dry:
                self.receipt(action="would_upload", local=str(p), remote=remote); continue
            st = self.src.upload_new(p, remote)
            self.state["uploaded"][key] = st
            self.receipt(action="outbox_" + st, local=str(p), remote=remote)
            self.save()

    def run_once(self):
        t0 = time.time()
        got = self.pull()
        joined = self.join_parts()
        self.index(got + joined)
        self.push()
        self.save()
        self.receipt(action="cycle_done", downloaded=len(got), joined=len(joined), secs=round(time.time() - t0, 1))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows 主控台預設 cp950
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--local-source")
    a = ap.parse_args()
    cfg = dict(DEFAULT_CONFIG)
    if a.config:
        cfg.update(json.loads(Path(a.config).read_text(encoding="utf-8")))
    log = lambda s: print(s, flush=True)
    if a.local_source:
        src = LocalSource(a.local_source)
    else:
        if not Path(cfg["credential_file"]).exists():
            log(json.dumps({"engine": "MRL_Dropbox_DL580_Sync/" + VERSION, "status": "waiting_for_credential",
                            "credential_file": cfg["credential_file"],
                            "note": "請建構者在 DL580 本機放入 Dropbox App 憑證（app_key／app_secret／refresh_token）；不經對話傳遞"},
                           ensure_ascii=False))
            sys.exit(5)
        src = DropboxSource(cfg["credential_file"])
    s = Sync(cfg, src, a.dry_run, log)
    if a.loop:
        while True:
            try:
                s.run_once()
            except Exception as e:
                s.receipt(action="cycle_error", error=str(e)[:300])
            time.sleep(a.loop)
    else:
        s.run_once()


if __name__ == "__main__":
    main()
