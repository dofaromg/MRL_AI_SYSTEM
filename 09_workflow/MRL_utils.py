#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_utils.py — 母體共用工具函數（去重蒸餾回母體）
origin_signature: MrLiouWord
layer: L0 ROOT
group: Y=0 RootGate

Purpose
-------
Single canonical home for utilities used across multiple MRL workflow modules.
Consumers import directly instead of maintaining local copies.

  from MRL_utils import _try_import

Exported
--------
  _try_import(module, attr) -> Any | None
      Gracefully import a named attribute from any module.
      Returns None on any import or attribute error (zero external deps).

  ORIGIN_SIGNATURE : str
      Canonical MRL origin signature constant.
"""

from __future__ import annotations

import importlib
from typing import Any

ORIGIN_SIGNATURE: str = "MrLiouWord"


def _try_import(module: str, attr: str) -> Any:
    """Attempt to import *attr* from *module*; return ``None`` on any failure."""
    try:
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None
