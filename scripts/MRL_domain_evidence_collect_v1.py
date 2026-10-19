#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MRL_domain_evidence_collect_v1 — 網域權位事件（Issue #146）唯讀蒐證腳本
# origin_signature: MrLiouWord
#
# 用途：對指定網域做「只讀」快照（DNS over HTTPS / RDAP / HTTP 不跟隨轉址），
#       輸出 JSON + SHA256SUMS 到「本地」目錄，供修正前後對照與封存。
# 約束：
#   - 零外部依賴（標準庫）。不寫入任何 DNS / 帳號 / 平台；不送出任何憑證。
#   - 資料只落在 --out 指定的本地路徑（DL580 本機）；不上傳平台。
#   - 每個旗標都只是「觀測」，不是「結論」。看不到 ≠ 不存在（局部視角規則）。
#   - 觀測位置由 --observer 標記；沙盒、DL580、外部網路得到的結果不可混為一談。
# 用法：
#   python3 scripts/MRL_domain_evidence_collect_v1.py --domain mrliouhan.ai \
#       --observer DL580 --out D:\mrl\evidence\mrliouhan_before
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ORIGIN_SIGNATURE = "MrLiouWord"
DOH_ENDPOINT = "https://cloudflare-dns.com/dns-query"
RDAP_ENDPOINTS = ("https://rdap.org/domain/", "https://rdap.identitydigital.services/rdap/domain/")
USER_AGENT = "MRL-domain-evidence/1 (read-only; origin_signature=MrLiouWord)"
RECORD_TYPES = ("A", "AAAA", "NS", "SOA", "MX", "TXT", "CAA", "CNAME", "DS")
# 子網域探測：只看公開 DNS，不代表全部子網域（無法列舉 zone）
PROBE_LABELS = ("www", "bridge", "_acme-challenge", "_cf-custom-hostname", "_dmarc")
HTTP_PATHS = ("/", "/robots.txt", "/manus-oauth/callback")
HTTP_HOSTS_PREFIX = ("", "www.")
PLATFORM_HOST_SUFFIXES = ("manus.im", "manus.space", "manus.computer")

# Cloudflare 公布的 IPv4 範圍（以官方清單為準；此處僅供旗標標示，需另行核對）
CLOUDFLARE_V4 = tuple(ipaddress.ip_network(n) for n in (
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"))
CGNAT_V4 = ipaddress.ip_network("100.64.0.0/10")

NOT_INFERABLE = [
    "不可由此推定 Manus 擁有或曾取得網域所有權（RDAP 只反映註冊商／註冊局層）。",
    "不可由此推定誰操作了 Cloudflare / Manus 端設定（需帳號 Audit Log）。",
    "不可由此推定任何人的意圖（INTENT_NOT_PROVEN）。",
    "不可由此推定法律上的創作所有權轉移（OWNERSHIP_TRANSFER_NOT_PROVEN）。",
    "單一觀測位置的結果不是全局事實；請於 DL580 與另一網路各跑一次對照。",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── 網路探測（皆唯讀）──────────────────────────────────────────────────────
def doh_query(name: str, rtype: str, timeout: float = 10.0) -> dict:
    url = f"{DOH_ENDPOINT}?name={urllib.parse.quote(name)}&type={rtype}"
    req = urllib.request.Request(url, headers={"accept": "application/dns-json", "user-agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        d = json.loads(raw)
        return {
            "name": name, "type": rtype, "rcode": d.get("Status"),
            "answers": [a.get("data") for a in d.get("Answer", [])],
            "authority": [a.get("data") for a in d.get("Authority", [])],
            "ttl": [a.get("TTL") for a in d.get("Answer", [])],
            "ad": d.get("AD"), "raw_sha256": sha256_bytes(raw),
        }
    except Exception as e:  # noqa: BLE001 — 蒐證腳本：失敗也要記錄，不可中斷
        return {"name": name, "type": rtype, "error": f"{type(e).__name__}: {e}"}


def rdap_lookup(domain: str, timeout: float = 20.0) -> dict:
    """RDAP 取回後只保留註冊層欄位；ToS notices 與隱私服務聯絡電話／地址不保存。"""
    errors = []
    for base in RDAP_ENDPOINTS:  # 單一端點被限流／拒絕時換下一個；全部失敗才回報錯誤
        req = urllib.request.Request(base + domain, headers={
            "accept": "application/rdap+json", "user-agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return reduce_rdap(json.loads(raw), sha256_bytes(raw)) | {"endpoint": base}
        except Exception as e:  # noqa: BLE001
            errors.append(f"{base}: {type(e).__name__}: {e}")
    return {"error": "; ".join(errors)}


def reduce_rdap(d: dict, raw_sha256: str = "") -> dict:
    registrar = None
    for ent in d.get("entities", []):
        if "registrar" in ent.get("roles", []):
            ids = ent.get("publicIds", [])
            name = ""
            for item in ent.get("vcardArray", [None, []])[1]:
                if item and item[0] == "fn":
                    name = item[3]
            registrar = {"name": name, "iana_id": ids[0]["identifier"] if ids else None}
    return {
        "ldhName": d.get("ldhName"),
        "handle": d.get("handle"),
        "status": d.get("status", []),
        "events": {e.get("eventAction"): e.get("eventDate") for e in d.get("events", [])},
        "nameservers": sorted(n.get("ldhName", "") for n in d.get("nameservers", [])),
        "secureDNS": d.get("secureDNS"),
        "registrar": registrar,
        "registrant_privacy": any(
            "registrant" in e.get("roles", []) and "privacy" in json.dumps(e).lower()
            for e in d.get("entities", [])),
        "raw_sha256": raw_sha256,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401 — 不跟隨，直接回報 3xx
        return None


def http_probe(url: str, timeout: float = 10.0) -> dict:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    try:
        resp = opener.open(req, timeout=timeout)
        status, headers = resp.status, resp.headers
    except urllib.error.HTTPError as e:
        status, headers = e.code, e.headers
    except Exception as e:  # noqa: BLE001
        return {"url": url, "error": f"{type(e).__name__}: {e}"}
    hdr = {k.lower(): v for k, v in headers.items()}
    cookie_names = [c.split("=", 1)[0] for c in headers.get_all("set-cookie") or []]
    hdr.pop("set-cookie", None)  # 值不保存，只留名稱
    return {"url": url, "status": status, "headers": hdr, "set_cookie_names": cookie_names}


# ── 旗標：只描述觀測 ────────────────────────────────────────────────────────
def _ip(value: str):
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def classify(snapshot: dict) -> list[dict]:
    flags: list[dict] = []

    def add(code: str, detail: str) -> None:
        flags.append({"flag": code, "detail": detail})

    dns = snapshot.get("dns", {})
    apex_a = dns.get("A", {}).get("answers", [])
    for v in apex_a:
        ip = _ip(v)
        if ip is None or ip.version != 4:
            continue
        if ip in CGNAT_V4:
            add("A_RECORD_CGNAT_IN_PUBLIC_DNS",
                f"{v} 屬 100.64.0.0/10（CGNAT／Tailscale 常用段）卻出現在公開 A 記錄；"
                "疑似殘留或洩漏內網位址，需對照 DL580 Tailscale 位址與註冊商 zone。")
        elif any(ip in n for n in CLOUDFLARE_V4):
            add("A_RECORD_IN_CLOUDFLARE_RANGE",
                f"{v} 位於 Cloudflare 公布範圍；只表示前端是 Cloudflare 邊緣，"
                "不表示帳號歸屬（自有 zone 或 Cloudflare for SaaS 皆會如此）。")
    ns = [n.rstrip(".").lower() for n in dns.get("NS", {}).get("answers", [])]
    if ns and not all(n.endswith(".ns.cloudflare.com") for n in ns):
        add("NS_NOT_CLOUDFLARE", f"權威 NS = {ns}；DNS 權威不在 Cloudflare，"
            "Cloudflare 邊緣回應可能來自自訂主機名（SaaS）而非本網域自有 zone。")
    for label, rec in dns.get("probe", {}).items():
        dcv = [v for t in ("CNAME", "TXT", "A") for v in rec.get(t, {}).get("answers", [])
               if ".dcv.cloudflare.com" in str(v)]
        if dcv:
            add("CLOUDFLARE_FOR_SAAS_DCV_DELEGATION",
                f"{label}.{snapshot['domain']} → {dcv[0]}；此為 Cloudflare for SaaS 自訂主機名"
                "憑證驗證委派形態。該 SaaS 租戶的 Cloudflare 帳號未知（待 Audit Log）。")
    for p in snapshot.get("http", []):
        loc = (p.get("headers") or {}).get("location", "")
        host = urllib.parse.urlparse(loc).hostname or ""
        if any(host == s or host.endswith("." + s) for s in PLATFORM_HOST_SUFFIXES):
            add("HTTP_REDIRECT_TO_MANUS_HOST",
                f"{p['url']} → {p['status']} Location 主機 {host}；"
                "表示該網域對外請求被導向 Manus 平台（OAuth 入口）。")
    rd = snapshot.get("rdap", {})
    if rd and "error" not in rd:
        add("RDAP_REGISTRAR", f"registrar={rd.get('registrar')}; status={rd.get('status')}; "
            f"events={rd.get('events')}; DNSSEC={rd.get('secureDNS')}")
        if rd.get("registrant_privacy"):
            add("RDAP_REGISTRANT_PRIVACY", "註冊人受隱私服務保護；所有人身分須由註冊商帳號證明。")
    return flags


# ── 快照與封存 ──────────────────────────────────────────────────────────────
def collect(domain: str, observer: str, delay: float = 0.3) -> dict:
    snap: dict = {
        "schema": "MRL_domain_evidence_v1", "origin_signature": ORIGIN_SIGNATURE,
        "domain": domain, "observer": observer, "collected_at": utc_now(),
        "dns": {}, "http": [], "rdap": {},
    }
    for t in RECORD_TYPES:
        snap["dns"][t] = doh_query(domain, t)
        time.sleep(delay)
    snap["dns"]["probe"] = {}
    for label in PROBE_LABELS:
        name = f"{label}.{domain}"
        snap["dns"]["probe"][label] = {t: doh_query(name, t) for t in ("A", "CNAME", "TXT")}
        time.sleep(delay)
    for prefix in HTTP_HOSTS_PREFIX:
        for path in HTTP_PATHS:
            if prefix and path != "/":
                continue
            snap["http"].append(http_probe(f"https://{prefix}{domain}{path}"))
            time.sleep(delay)
    snap["rdap"] = rdap_lookup(domain)
    snap["flags"] = classify(snap)
    snap["not_inferable"] = NOT_INFERABLE
    return snap


def write_bundle(snapshot: dict, out_dir: pathlib.Path) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    name = f"{snapshot['domain']}_{snapshot['collected_at'].replace(':', '')}.json"
    (out_dir / name).write_bytes(body)
    sums = out_dir / "SHA256SUMS"
    with sums.open("a", encoding="utf-8") as f:  # Additive-Only：只追加
        f.write(f"{sha256_bytes(body)}  {name}\n")
    return out_dir / name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MRL 網域權位事件唯讀蒐證（Issue #146）")
    ap.add_argument("--domain", default="mrliouhan.ai")
    ap.add_argument("--observer", required=True, help="觀測位置標記，例如 DL580 / sandbox / mobile")
    ap.add_argument("--out", required=True, help="本地輸出目錄（不要指向雲端同步資料夾）")
    args = ap.parse_args(argv)
    snap = collect(args.domain, args.observer)
    path = write_bundle(snap, pathlib.Path(args.out))
    print(f"snapshot: {path}")
    for f in snap["flags"]:
        print(f"[{f['flag']}] {f['detail']}")
    print("NOT_INFERABLE:")
    for n in snap["not_inferable"]:
        print(f"  - {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
