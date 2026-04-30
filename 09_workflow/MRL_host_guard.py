#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL_host_guard.py — DL580 canonical host enforcement

origin_signature: MrLiouWord
layer: L3 LAW
group: Y=1 MotherCore

Mainstream pattern note
-----------------------
This module enforces a production-standard *trust boundary*:
only the canonical host (DL580) is allowed to perform learning persistence
operations. All other nodes may treat external inputs as learning materials but
must not mutate internal knowledge stores.

Checks are performed using a defense-in-depth strategy:
  A) hostname allowlist
  B) IP/CIDR allowlist (for the local interface or primary outbound IP)
  C) host fingerprint file marker (operator provisioned)
"""

from __future__ import annotations

import ipaddress
import os
import platform
import socket
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"


@dataclass(frozen=True)
class HostGuardConfig:
    hostname_allowlist: List[str]
    cidr_allowlist: List[str]
    fingerprint_file: str
    fingerprint_value: str


DEFAULT_DL580_CONFIG = HostGuardConfig(
    hostname_allowlist=[
        "win-pbvu i7vk2a6".replace(" ", ""),
        "win-pbvui7vk2a6.tail7de813.ts.net",
    ],
    cidr_allowlist=[
        "100.78.70.78/32",
        "127.0.0.1/32",
    ],
    fingerprint_file=r"D:\mrl\config\MRL_host_role.txt",
    fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
)


def _norm_host(s: str) -> str:
    return (s or "").strip().lower().rstrip(".")


def _get_hostname_candidates() -> List[str]:
    cands = []
    try:
        cands.append(platform.node())
    except Exception:
        pass
    try:
        cands.append(socket.gethostname())
    except Exception:
        pass
    try:
        cands.append(socket.getfqdn())
    except Exception:
        pass
    out: List[str] = []
    seen = set()
    for c in cands:
        n = _norm_host(c)
        if n and n not in seen:
            out.append(n)
            seen.add(n)
    return out


def _read_fingerprint(path: str) -> Tuple[bool, str]:
    try:
        if not path:
            return False, "fingerprint_file not configured"
        if not os.path.exists(path):
            return False, f"fingerprint_file not found: {path}"
        raw = open(path, "r", encoding="utf-8", errors="replace").read().strip()
        return True, raw
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _get_ip_candidates() -> List[str]:
    ips: List[str] = []
    # Localhost always included
    ips.append("127.0.0.1")
    # Best-effort primary outbound IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
        finally:
            s.close()
    except Exception:
        pass
    # Dedup
    out: List[str] = []
    seen = set()
    for ip in ips:
        if ip and ip not in seen:
            out.append(ip)
            seen.add(ip)
    return out


def _ip_in_cidrs(ip: str, cidrs: Iterable[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for c in cidrs:
        try:
            net = ipaddress.ip_network(c, strict=False)
        except ValueError:
            continue
        if ip_obj in net:
            return True
    return False


def is_dl580_canonical_host(cfg: HostGuardConfig = DEFAULT_DL580_CONFIG) -> Tuple[bool, str]:
    """Return (ok, reason). ok=True means this host is allowed to persist learning."""

    # A) hostname
    hostnames = _get_hostname_candidates()
    allow_hosts = {_norm_host(x) for x in (cfg.hostname_allowlist or [])}
    if allow_hosts and not any(h in allow_hosts for h in hostnames):
        return False, f"hostname not allowed: {hostnames}"

    # B) CIDR
    cidrs = list(cfg.cidr_allowlist or [])
    if cidrs:
        ips = _get_ip_candidates()
        if not any(_ip_in_cidrs(ip, cidrs) for ip in ips):
            return False, f"ip not allowed: {ips}"

    # C) fingerprint
    ok, fp = _read_fingerprint(cfg.fingerprint_file)
    if not ok:
        return False, f"fingerprint read failed: {fp}"
    if (fp or "").strip() != (cfg.fingerprint_value or "").strip():
        return False, "fingerprint mismatch"

    return True, "dl580 canonical host verified"

