"""
test_MRL_domain_evidence_collect_v1.py — Issue #146 蒐證腳本離線測試（不連網）
origin_signature: MrLiouWord
"""
from __future__ import annotations

import importlib.util
import urllib.request
import pathlib
import tempfile
import unittest

_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "MRL_domain_evidence_collect_v1.py"
_spec = importlib.util.spec_from_file_location("MRL_domain_evidence_collect_v1", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _rec(*answers):
    return {"answers": list(answers)}


def _snapshot():
    return {
        "domain": "example.test",
        "dns": {
            "A": _rec("104.18.26.246", "100.78.70.78"),
            "NS": _rec("ns1.registrar.example.", "ns2.registrar.example."),
            "probe": {"_acme-challenge": {
                "CNAME": _rec("example.test.abc.dcv.cloudflare.com."), "TXT": _rec(), "A": _rec()}},
        },
        "http": [{"url": "https://example.test/", "status": 302,
                  "headers": {"location": "https://manus.im/app-auth?x=1"}}],
        "rdap": {"registrar": {"name": "R", "iana_id": "1"}, "status": ["client transfer prohibited"],
                 "events": {}, "secureDNS": {"delegationSigned": False}, "registrant_privacy": True},
    }


class ClassifyTests(unittest.TestCase):
    def test_flags_are_observations(self):
        codes = {f["flag"] for f in mod.classify(_snapshot())}
        self.assertEqual(codes, {
            "A_RECORD_CGNAT_IN_PUBLIC_DNS", "A_RECORD_IN_CLOUDFLARE_RANGE", "NS_NOT_CLOUDFLARE",
            "CLOUDFLARE_FOR_SAAS_DCV_DELEGATION", "HTTP_REDIRECT_TO_MANUS_HOST",
            "RDAP_REGISTRAR", "RDAP_REGISTRANT_PRIVACY"})

    def test_no_flag_claims_ownership(self):
        text = " ".join(f["flag"] + f["detail"] for f in mod.classify(_snapshot()))
        for banned in ("owned by", "擁有者為", "已轉移"):
            self.assertNotIn(banned, text)

    def test_clean_snapshot_has_no_manus_flag(self):
        snap = _snapshot()
        snap["http"] = [{"url": "https://example.test/", "status": 200, "headers": {}}]
        self.assertNotIn("HTTP_REDIRECT_TO_MANUS_HOST", {f["flag"] for f in mod.classify(snap)})

    def test_lookalike_host_not_flagged(self):
        snap = _snapshot()
        snap["http"] = [{"url": "https://example.test/", "status": 302,
                         "headers": {"location": "https://notmanus.im/x"}}]
        self.assertNotIn("HTTP_REDIRECT_TO_MANUS_HOST", {f["flag"] for f in mod.classify(snap)})


class RdapReduceTests(unittest.TestCase):
    def test_drops_contact_details(self):
        raw = {
            "ldhName": "example.test", "handle": "H", "status": ["ok"],
            "events": [{"eventAction": "registration", "eventDate": "2026-05-16T00:00:00Z"}],
            "nameservers": [{"ldhName": "ns2.x"}, {"ldhName": "ns1.x"}],
            "entities": [
                {"roles": ["registrant"], "vcardArray": ["vcard", [["fn", {}, "text", "Privacy Service"],
                                                                    ["tel", {}, "uri", "tel:+1.0000000000"]]]},
                {"roles": ["registrar"], "publicIds": [{"identifier": "3956"}],
                 "vcardArray": ["vcard", [["fn", {}, "text", "Registrar LLC"]]]}],
        }
        raw["events"].append({"eventAction": "registration", "eventDate": "2026-06-01T00:00:00Z"})
        out = mod.reduce_rdap(raw, "abc")
        self.assertEqual(out["events"]["registration"],
                         ["2026-05-16T00:00:00Z", "2026-06-01T00:00:00Z"])
        self.assertEqual(out["registrar"], {"name": "Registrar LLC", "iana_id": "3956"})
        self.assertEqual(out["nameservers"], ["ns1.x", "ns2.x"])
        self.assertTrue(out["registrant_privacy"])
        self.assertNotIn("tel:", str(out))


class RobustnessTests(unittest.TestCase):
    def test_malformed_registrar_vcard_keeps_registration_data(self):
        for bad in (None, [], ["vcard"], ["vcard", None], ["vcard", [["fn"]]], ["vcard", ["x"]]):
            raw = {"ldhName": "example.test", "status": ["ok"],
                   "entities": [{"roles": ["registrar"], "vcardArray": bad}]}
            out = mod.reduce_rdap(raw, "abc")
            self.assertEqual(out["status"], ["ok"])
            self.assertEqual(out["registrar"]["name"], "")

    def test_doh_does_not_follow_redirects(self):
        import urllib.error
        from unittest import mock
        err = urllib.error.HTTPError("u", 302, "Found", {}, None)
        with mock.patch.object(urllib.request.OpenerDirector, "open", side_effect=err):
            out = mod.doh_query("example.test", "A")
        self.assertIn("HTTPError", out["error"])

    def test_malformed_location_is_recorded_not_raised(self):
        snap = _snapshot()
        snap["http"] = [{"url": "https://example.test/", "status": 302, "headers": {"location": "http://["}}]
        flags = {f["flag"] for f in mod.classify(snap)}
        self.assertIn("HTTP_REDIRECT_LOCATION_UNPARSEABLE", flags)

    def test_body_evidence_extracts_attribution_metadata(self):
        html = (b'<html><head><title>T</title><meta name="canonical-authority" content="Mr.liou">'
                b'<meta property="og:site_name" content="Mrlious"><link rel="canonical" href="https://x/">'
                b'<link rel="icon" href="/f.ico"></head><body>canonical_authority: Mr.liou</body></html>')
        ev = mod.body_evidence(html, False)
        self.assertEqual(ev["meta"]["og:site_name"], "Mrlious")
        self.assertEqual(ev["title"], "T")
        self.assertEqual(len(ev["links"]), 2)
        self.assertTrue(ev["attribution_markers_present"]["canonical_authority"])
        self.assertFalse(ev["attribution_markers_present"]["origin_signature"])
        self.assertEqual(ev["body_sha256"], mod.sha256_bytes(html))

    def test_manus_label_is_probed(self):
        self.assertIn("manus", mod.PROBE_LABELS)

    def test_all_failed_is_not_usable_evidence(self):
        snap = {"dns": {"A": {"error": "x"}, "probe": {}}, "http": [{"url": "u", "error": "x"}],
                "rdap": {"error": "x"}}
        self.assertFalse(mod.has_usable_evidence(snap))
        snap["http"] = [{"url": "u", "status": 302}]
        self.assertTrue(mod.has_usable_evidence(snap))


class BundleTests(unittest.TestCase):
    def test_same_second_collision_does_not_overwrite(self):
        snap = {"domain": "example.test", "collected_at": "2026-10-19T00:00:00Z", "flags": []}
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            first = mod.write_bundle(snap, out)
            first_bytes = first.read_bytes()
            second = mod.write_bundle(dict(snap, flags=["different"]), out)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), first_bytes)
            for line in (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest, name = line.split("  ")
                self.assertEqual(digest, mod.sha256_bytes((out / name).read_bytes()))

    def test_sha256sums_is_append_only_and_verifiable(self):
        snap = {"domain": "example.test", "collected_at": "2026-10-19T00:00:00Z", "flags": []}
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            first = mod.write_bundle(snap, out)
            snap2 = dict(snap, collected_at="2026-10-19T00:00:01Z")
            mod.write_bundle(snap2, out)
            lines = (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            digest, name = lines[0].split("  ")
            self.assertEqual(name, first.name)
            self.assertEqual(digest, mod.sha256_bytes(first.read_bytes()))


if __name__ == "__main__":
    unittest.main()
