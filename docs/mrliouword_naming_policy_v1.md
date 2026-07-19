# Mrliouword 命名規範與相容遷移政策

**文件版本**：v1.0  
**日期**：2026-07-18  
**狀態**：正式（已實作驗證）

---

## 一、權威命名規範

以下為 Mrliouword 系統的唯一正式命名規範，所有新元件一律遵守：

| 識別類型 | 規範值 | 範例 |
|---------|--------|------|
| **產品名稱** | `Mrliouword` | 文件標題、README、版本宣告 |
| **Python 套件／命名空間** | `mrliouword` | `from mrliouword import MemoryStore` |
| **CLI 命令** | `mrliouword` | `mrliouword health` |
| **環境變數前綴（新）** | `MRLIOUWORD_` | `MRLIOUWORD_LLM_DEFAULT_MODEL=gpt-4o` |
| **環境變數前綴（舊，向後相容）** | `MRL_` | `MRL_LLM_DEFAULT_MODEL=gpt-4o` |
| **API base path** | `/api/v1` | `GET /api/v1/health` |
| **容器／服務名稱** | `mrliouword-*` | `mrliouword-api`, `mrliouword-runtime` |
| **Kubernetes label** | `app.kubernetes.io/part-of: mrliouword` | K8s manifest |
| **協定名稱** | `Mrliouword Particle Protocol` | 文件、schema 宣告 |
| **origin_signature** | `MrLiouWord` | JSON 簽章欄位（歷史格式，維持相容） |

---

## 二、舊名稱使用規則

下列名稱**僅可**作為歷史相容別名、子領域名稱或 migration 說明，**不得**成為新元件的產品正名：

| 舊名稱 | 允許用途 | 禁止用途 |
|--------|---------|---------|
| `MRL` | 現有模組前綴（`MRL_AgentHarness_*`）、子系統標籤 | 新服務／套件的產品名稱 |
| `FlowAgent` | 子系統名稱（如 `FlowAgent runtime` 子模組）| 獨立產品或頂層服務名稱 |
| `ParticleRuntime` | 技術描述詞（如「Mrliouword Particle Runtime」）| 容器名稱、CLI 命令 |
| `MRL_AGI` | 現有設定鍵（`system.name = MRL_AGI`）| 對外 API 回應中的 product 欄位 |

---

## 三、遷移路徑

### 3.1 Python imports

**舊用法（仍可用，但標記為 deprecated）**：
```python
from MRL_utils import ORIGIN_SIGNATURE, embed_signature
```

**新用法（建議）**：
```python
from mrliouword.schemas import ORIGIN_SIGNATURE, embed_signature
```

兩者位元相容（已由整合測試 `test_embed_signature_compat_with_mrl_utils` 驗證）。

---

### 3.2 環境變數

**舊用法（仍可用）**：
```bash
export MRL_LLM_DEFAULT_MODEL=gpt-4o
export MRL_RUNTIME_MODE=test
```

**新用法（建議）**：
```bash
export MRLIOUWORD_LLM_DEFAULT_MODEL=gpt-4o
export MRLIOUWORD_RUNTIME_MODE=test
```

優先序：`MRLIOUWORD_` > `MRL_` > JSON config > 預設值。

已在 `09_workflow/config_manager.py` 及 `mrliouword/config.py` 同時實作。

---

### 3.3 API 路徑

**現有端點**（09_workflow/api_gateway.py，向後相容保留）：
```
GET  /health
POST /chat
GET  /sessions
...
```

**新端點（Mrliouword 規範）**：
```
GET  /api/v1/health
POST /api/v1/chat
GET  /api/v1/sessions
```

遷移策略：在 api_gateway.py 新增 `/api/v1` 前綴路由，舊路由保留至下一個 major 版本。

---

### 3.4 容器 / 服務名稱

| 舊名稱 | 新名稱 |
|--------|--------|
| `mrl-api-server` | `mrliouword-api` |
| `mrl-runtime` | `mrliouword-runtime` |
| `mrl-worker` | `mrliouword-worker` |
| `flow-tasks-server` | `mrliouword-tasks`（待 flow-tasks 存取恢復後遷移） |

---

## 四、命名審計工具

現有 `09_workflow/MRL_Naming_Sovereignty_Auditor_v1.py` 提供命名合規性稽核。

建議擴展審計規則以涵蓋 Mrliouword 正名：
1. 新服務名稱以 `mrliouword-` 開頭
2. 新 Python 套件以 `mrliouword` 命名空間為準
3. 新 CLI 命令以 `mrliouword` 開頭
4. 環境變數建議使用 `MRLIOUWORD_` 前綴

---

## 五、版本管理

- **Semantic Versioning**：MAJOR.MINOR.PATCH
- 當前版本：`1.0.0`（pyproject.toml）
- MAJOR 版本更新時，舊相容別名可移除（需提供完整 migration guide）
- schema_version 欄位在所有資料模型中強制存在（已由整合測試驗證）

---

## 六、machine-readable 元件清單

```json
{
  "product": "Mrliouword",
  "version": "1.0.0",
  "python_package": "mrliouword",
  "cli": "mrliouword",
  "env_prefix_canonical": "MRLIOUWORD_",
  "env_prefix_compat": "MRL_",
  "api_base_path": "/api/v1",
  "origin_signature": "MrLiouWord",
  "container_prefix": "mrliouword-",
  "k8s_label": "app.kubernetes.io/part-of=mrliouword",
  "protocol": "Mrliouword Particle Protocol",
  "legacy_aliases": ["MRL", "FlowAgent", "ParticleRuntime"]
}
```

此清單存放於 `data/mrliouword_manifest.json`，防止未來產生多個權威來源。
