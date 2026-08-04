from __future__ import annotations

import unittest

from MRL_URL_v1 import (
    MRLURLError,
    build_asi_field,
    build_asi_frame,
    build_asi_po,
    build_projection_resource,
    build_source_object,
    build_trace_event,
    build_world_node,
    canonicalize_mrl_url,
    parse_mrl_url,
)


DIGEST = "a" * 64


class TestMRLURLV1(unittest.TestCase):
    def test_asi_po_round_trip_is_tokenless_and_explicit(self) -> None:
        url = build_asi_po(
            "earth-lab",
            "frame-0001",
            "po-0001",
            source_hash=DIGEST,
            mode="measured",
        )
        self.assertEqual(
            url,
            "mrl://asi/field/earth-lab/frame/frame-0001/po/po-0001"
            f"?v=1&src={DIGEST}&mode=measured",
        )
        parsed = parse_mrl_url(url)
        self.assertEqual(parsed.layer, "asi")
        self.assertTrue(parsed.is_tokenless_asi)
        self.assertEqual(parsed.field_mode, "measured")
        self.assertFalse(parsed.as_dict()["grants_authority"])

    def test_all_asi_route_depths_are_supported(self) -> None:
        field = build_asi_field("earth-lab", source_hash=DIGEST, mode="inferred")
        frame = build_asi_frame(
            "earth-lab", "frame-0001", source_hash=DIGEST, mode="simulated"
        )
        self.assertEqual(parse_mrl_url(field).segments[-1], "earth-lab")
        self.assertEqual(parse_mrl_url(frame).segments[-1], "frame-0001")

    def test_non_asi_layers_are_structurally_distinct(self) -> None:
        urls = {
            "world": build_world_node("mother", "flowseed", source_hash=DIGEST),
            "projection": build_projection_resource(
                "web", "public-index", source_hash=DIGEST
            ),
            "source": build_source_object("origin-0001", source_hash=DIGEST),
            "trace": build_trace_event("event-0001", source_hash=DIGEST),
        }
        for layer, url in urls.items():
            with self.subTest(layer=layer):
                parsed = parse_mrl_url(url)
                self.assertEqual(parsed.layer, layer)
                self.assertFalse(parsed.is_tokenless_asi)
                self.assertIsNone(parsed.field_mode)

    def test_token_account_session_and_credentials_are_rejected(self) -> None:
        base = build_asi_field("earth-lab", source_hash=DIGEST, mode="measured")
        for key in ("token", "access_token", "account", "session", "password"):
            with self.subTest(key=key):
                with self.assertRaises(MRLURLError) as denied:
                    parse_mrl_url(base + f"&{key}=value")
                self.assertEqual(denied.exception.code, "CREDENTIAL_IN_URL")

    def test_userinfo_port_and_fragment_are_rejected(self) -> None:
        samples = {
            "userinfo": (
                f"mrl://user@asi/field/earth-lab?v=1&src={DIGEST}&mode=measured",
                "USERINFO_FORBIDDEN",
            ),
            "port": (
                f"mrl://asi:443/field/earth-lab?v=1&src={DIGEST}&mode=measured",
                "PORT_FORBIDDEN",
            ),
            "fragment": (
                f"mrl://asi/field/earth-lab?v=1&src={DIGEST}&mode=measured#hidden",
                "FRAGMENT_FORBIDDEN",
            ),
        }
        for name, (url, code) in samples.items():
            with self.subTest(name=name):
                with self.assertRaises(MRLURLError) as denied:
                    parse_mrl_url(url)
                self.assertEqual(denied.exception.code, code)

    def test_raw_environment_values_do_not_belong_in_url(self) -> None:
        url = (
            f"mrl://asi/field/earth-lab?v=1&src={DIGEST}"
            "&mode=measured&frequency_hz=60"
        )
        with self.assertRaises(MRLURLError) as denied:
            parse_mrl_url(url)
        self.assertEqual(denied.exception.code, "QUERY_KEY_FORBIDDEN")

    def test_asi_mode_is_required_and_non_asi_mode_is_forbidden(self) -> None:
        with self.assertRaises(MRLURLError) as missing:
            parse_mrl_url(f"mrl://asi/field/earth-lab?v=1&src={DIGEST}")
        self.assertEqual(missing.exception.code, "FIELD_MODE_REQUIRED")

        world = build_world_node("mother", "flowseed", source_hash=DIGEST)
        with self.assertRaises(MRLURLError) as forbidden:
            parse_mrl_url(world + "&mode=measured")
        self.assertEqual(forbidden.exception.code, "QUERY_KEY_FORBIDDEN")

    def test_noncanonical_query_order_can_be_normalized_but_not_silently_accepted(self) -> None:
        value = (
            f"mrl://asi/field/earth-lab?mode=measured&src={DIGEST}&v=1"
        )
        with self.assertRaises(MRLURLError) as denied:
            parse_mrl_url(value)
        self.assertEqual(denied.exception.code, "URL_NON_CANONICAL")
        self.assertEqual(
            canonicalize_mrl_url(value),
            f"mrl://asi/field/earth-lab?v=1&src={DIGEST}&mode=measured",
        )

    def test_duplicate_unknown_and_malformed_hash_fail_closed(self) -> None:
        invalid = {
            "duplicate": (
                f"mrl://trace/event/e1?v=1&v=1&src={DIGEST}",
                "QUERY_DUPLICATE",
            ),
            "unknown": (
                f"mrl://trace/event/e1?v=1&src={DIGEST}&private=false",
                "QUERY_KEY_FORBIDDEN",
            ),
            "hash": (
                "mrl://trace/event/e1?v=1&src=abcd",
                "SOURCE_HASH_INVALID",
            ),
        }
        for name, (url, code) in invalid.items():
            with self.subTest(name=name):
                with self.assertRaises(MRLURLError) as denied:
                    parse_mrl_url(url)
                self.assertEqual(denied.exception.code, code)

    def test_similar_name_and_path_confusion_are_rejected(self) -> None:
        urls = [
            f"mrl://ASI/field/earth-lab?v=1&src={DIGEST}&mode=measured",
            f"mrl://asi/field/Earth-Lab?v=1&src={DIGEST}&mode=measured",
            f"mrl://asi/field/%2e%2e?v=1&src={DIGEST}&mode=measured",
            f"https://asi/field/earth-lab?v=1&src={DIGEST}&mode=measured",
        ]
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaises(MRLURLError):
                    parse_mrl_url(url)


if __name__ == "__main__":
    unittest.main()
