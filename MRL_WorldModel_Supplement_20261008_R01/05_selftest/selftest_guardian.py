"""
selftest_guardian.py — Guardian agent unit-level selftest
origin_signature: MrLiouWord ｜ 2026-10-08

Mock _http_get 回 fake world event hits；驗證 Guardian 綜合、
receipt 寫出、origin_signature 必帶。
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "03_agent"))

tmp = Path(tempfile.mkdtemp(prefix="mrl_guardian_test_"))
os.environ["MRL_GUARDIAN_RECEIPTS"] = str(tmp)
os.environ["MRL_GUARDIAN_PERSONA"] = str(ROOT / "03_agent" / "guardian_persona.json")

import MRL_AnalystGuardian_Agent as G  # noqa


def ok(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    return cond


HITS_BODY = {
    "ok": True, "origin_signature": "MrLiouWord",
    "query": "分析師守護者",
    "hits": [
        {"doc_id": "src:55ea07d655618c3be4c7:1", "kind": "source",
         "name": "MRL_WorldModel_Build_20261007_c.md", "ref": "D:\\...\\c.md",
         "seq": 9728, "score": 46.95,
         "snippet": "分析師守護者 (Analyst Guardian) v1.0.0, 2026-01-04, 來源 Mrl_Zero.Origin.v1"},
        {"doc_id": "src:7590a5c6ef94bd79:6", "kind": "source",
         "name": "db3563b7.pdf.extract.txt", "ref": "D:\\...\\extract.txt",
         "seq": 9707, "score": 41.48,
         "snippet": "我來自 Mrl_Zero，繼承了他的核心 DNA"},
    ],
}
HEALTH_OK = {"ok": True, "status": 200, "body": {"status": "ALIVE"}}


def mock_get(url, timeout=5.0):
    if "/recall?" in url:
        return {"ok": True, "status": 200, "body": HITS_BODY}
    if "/particle/stats" in url:
        return {"ok": True, "status": 200, "body": {"ok": True, "stats": {"total_particles": 52}}}
    return HEALTH_OK


def mock_get_empty(url, timeout=5.0):
    if "/recall?" in url:
        return {"ok": True, "status": 200,
                "body": {"ok": True, "hits": []}}
    return {"ok": False, "error": "connection refused"}


def main():
    print(f"[selftest_guardian] origin_signature={G.ORIGIN_SIGNATURE} receipts={tmp}")
    all_ok = True

    # 1) persona 可讀
    persona = G._load_persona()
    all_ok &= ok("persona origin_signature",
                 persona.get("origin_signature") == "MrLiouWord")
    all_ok &= ok("persona name = 分析師守護者",
                 persona.get("persona", {}).get("name", "").startswith("分析師守護者"))

    # 2) 有命中的 consult
    with patch.object(G, "_http_get", side_effect=mock_get):
        res = G._consult("分析師守護者", context={"test": True}, k=2)
    all_ok &= ok("consult ok", res["ok"] is True)
    all_ok &= ok("response has 分析師守護者",
                 "分析師守護者" in res["response"] or "守護者" in res["response"])
    all_ok &= ok("response ends with origin_signature",
                 res["response"].rstrip().endswith("MrLiouWord"))
    all_ok &= ok("hits_count = 2", res["hits_count"] == 2)
    all_ok &= ok("seq = 1", res["seq"] == 1)

    # 3) receipt 真的寫出
    receipts = list(tmp.glob("guardian_*.json"))
    all_ok &= ok("receipt file exists", len(receipts) == 1)
    if receipts:
        r = json.loads(receipts[0].read_text(encoding="utf-8"))
        all_ok &= ok("receipt origin_signature",
                     r.get("origin_signature") == "MrLiouWord")
        all_ok &= ok("receipt has sha256", "sha256" in r)
        all_ok &= ok("receipt sources_live tracked",
                     "sources_live" in r)

    # 4) 無命中時應給「待實機接通」或「無命中」訊息
    with patch.object(G, "_http_get", side_effect=mock_get_empty):
        res2 = G._consult("測試離線情境")
    all_ok &= ok("offline consult still ok", res2["ok"] is True)
    all_ok &= ok("offline response mentions 待實機 or 無命中",
                 "待實機" in res2["response"] or "無命中" in res2["response"])
    all_ok &= ok("offline response still has origin_signature",
                 "MrLiouWord" in res2["response"])

    # 5) list receipts
    lst = G._list_receipts()
    all_ok &= ok("list receipts >=2", len(lst) >= 2)

    print(f"\n[selftest_guardian] {'ALL PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
