"""
mrliouword.config — 統一設定載入、環境分層與安全預設

封裝 09_workflow/config_manager.py，提供 Mrliouword 正式命名介面。

環境變數優先序（高 → 低）：
  1. MRLIOUWORD_<KEY>   （新正名前綴）
  2. MRL_<KEY>          （舊前綴，保持向後相容）
  3. JSON config 檔案
  4. 內建預設值

敏感鍵（api_key, token, secret, password, credential）在 dump() 中自動遮罩。
"""

from __future__ import annotations

import os
import pathlib
import sys
from typing import Any, Optional

# 將 09_workflow/ 加入 sys.path（若尚未存在）
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _REPO_ROOT / "09_workflow"
if str(_WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW_DIR))

from config_manager import ConfigManager as _ConfigManager  # noqa: E402

_MRLIOUWORD_PREFIX = "MRLIOUWORD_"
_MRL_PREFIX = "MRL_"


class MrliouwordConfig:
    """
    Mrliouword 統一設定管理器。

    支援 MRLIOUWORD_ 與 MRL_ 兩種環境變數前綴（MRLIOUWORD_ 優先），
    並將底層設定委派給 09_workflow/config_manager.py 的 ConfigManager。

    範例::

        cfg = MrliouwordConfig()
        model = cfg.get("llm.default_model", default="mock")
        cfg.set("llm.default_model", "gpt-4o")
        print(cfg.dump(mask_secrets=True))
    """

    def __init__(
        self,
        config_path: Optional[pathlib.Path] = None,
    ) -> None:
        kwargs: dict = {}
        if config_path is not None:
            kwargs["config_path"] = config_path
        self._inner = _ConfigManager(**kwargs)

    # ── MRLIOUWORD_ 環境變數前綴支援 ───────────────────────────────────────────

    def _resolve_env(self, key: str) -> Optional[str]:
        """
        按優先序解析環境變數：
          1. MRLIOUWORD_<KEY_UPPER>
          2. MRL_<KEY_UPPER>
        """
        env_key = key.upper().replace(".", "_")
        mrliouword_val = os.environ.get(_MRLIOUWORD_PREFIX + env_key)
        if mrliouword_val is not None:
            return mrliouword_val
        return os.environ.get(_MRL_PREFIX + env_key)

    # ── 公開介面 ───────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """
        讀取設定值。MRLIOUWORD_/MRL_ 環境變數優先於 JSON 檔案，
        JSON 檔案優先於內建預設值。
        """
        env_val = self._resolve_env(key)
        if env_val is not None:
            # 型別轉換委派給內層（已有現有值時使用同型別轉換）
            existing = self._inner.get(key)
            if existing is not None:
                try:
                    return type(existing)(env_val)
                except (ValueError, TypeError):
                    pass
            # bool 字串特殊處理
            if env_val.lower() in ("true", "1", "yes"):
                return True
            if env_val.lower() in ("false", "0", "no"):
                return False
            return env_val
        return self._inner.get(key, default=default)

    def set(self, key: str, value: Any) -> None:
        """寫入設定值（至 JSON config）。"""
        self._inner.set(key, value)

    def save(self) -> None:
        """將當前設定持久化至 JSON config 檔案。"""
        self._inner.save()

    def dump(self, mask_secrets: bool = True) -> dict:
        """回傳完整設定（敏感欄位可遮罩）。"""
        return self._inner.dump(mask_secrets=mask_secrets)

    def reset(self) -> None:
        """重設為預設值。"""
        self._inner.reset()

    @property
    def origin_signature(self) -> str:
        """系統原點簽章。"""
        return self.get("system.origin_signature", default="MrLiouWord")

    @property
    def product_name(self) -> str:
        """權威產品名稱。"""
        return "Mrliouword"

    @property
    def version(self) -> str:
        """系統版本。"""
        return self.get("system.version", default="1.0")
