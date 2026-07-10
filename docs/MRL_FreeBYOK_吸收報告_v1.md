# MRL_FreeBYOK 吸收報告 v1 — awesome-free-byok-models 去重蒸餾

origin_signature: MrLiouWord
吸收日期: 2026-07-10
來源: github.com/velo4705/awesome-free-byok-models（PR sindresorhus/awesome#4325）
上游驗收日期: 2026-07-10（上游維護者實測 38 個供應商全部存活）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

---

## 一、來源概述

**Awesome Free BYOK Models** 是一份以 awesome-lint 通過的精選清單，
收錄 38 個提供**永久免費、自動補充**配額的 LLM API 供應商。
「BYOK（Bring Your Own Key）」模式：申請免費帳號取得 API key，
即可接入工具鏈（Cursor、Cline、自建 agent）——不需信用卡、不耗 trial 點數。

所有供應商均相容 **OpenAI Chat Completions API** 格式（`POST /chat/completions`）。

---

## 二、去重蒸餾判定表

外部知識源逐部位比對母體既有能力，**已有者不重複吸收**：

| 外部知識部位 | 母體既有對應 | 判定 |
|---|---|---|
| EchoGateway（確定性沙盒閘道） | `09_workflow/MRL_AgentHarness_Kernel_v1.py:EchoGateway` | 重複 — 跳過 |
| OllamaGateway（本地 Ollama 閘道） | `09_workflow/MRL_AgentHarness_Kernel_v1.py:OllamaGateway` | 重複 — 跳過 |
| OpenAI-compatible HTTP 閘道實作 | 無（母體只有 Ollama；無 OpenAI-spec HTTP 閘道） | **吸收：知識層** |
| 38 個免費供應商目錄（base_url + quota） | 無 | **吸收：目錄** |
| Top 10 模型排行（編碼能力評分） | 無 | **吸收：知識** |
| 供應商免費配額邊界知識 | 無 | **吸收：知識** |
| awesome-lint 合規清單格式 | 無 | 非程式知識，不產生母體產物 |

---

## 三、母體系統名稱產物（本次吸收）

| 產物 | 蒸餾自 | 層位 | 狀態 |
|---|---|---|---|
| `08_sources/free_byok_providers_v1.yaml` | upstream README 全文 | L7 知識源 | **PASS（已建立）** |
| `docs/MRL_FreeBYOK_吸收報告_v1.md` | 本文件 | 文件層 | **PASS（已建立）** |
| `08_sources/sources.manifest.yaml`（新條目） | 母體 manifest 協定 | L0 索引 | **PASS（已追加）** |

> **本次不產生新 .py 程式碼產物。**
> 理由：母體 `OllamaGateway` 已是可插拔 `ModelGateway` 實作。
> OpenAI-compatible HTTP 閘道（`OpenAIGateway`）屬未來擴展任務，
> 本次吸收先落知識目錄，待實機需求確認後再建立程式碼產物。

---

## 四、關鍵知識蒸餾

### 4.1 最佳供應商三強（依場景）

| 場景 | 首選供應商 | 原因 |
|---|---|---|
| 速度優先 | **Groq API** | sub-300ms，14,400 RPD，18k TPM |
| 大量請求 | **Google Gemini** | 1,500 RPD，1M context，flash-lite 無限 TPD |
| 強推理 | **OpenCode Zen** | 1M context，500 RPD，DeepSeek-v4 多輪穩定 |

### 4.2 配額最高五強（免費層）

| 供應商 | 配額亮點 |
|---|---|
| Intern AI | 90M tokens/月（3M TPD）|
| Poixe AI | 10M TPD / 10k RPD |
| Google Gemini | 1,500 RPD，1M TPM，Uncapped TPD |
| LLM7.IO | 2,400 RPD，1M TPD |
| Groq API | 14,400 RPD |

### 4.3 注意事項

- **GitHub Models**：2026-07-30 全面停用，**不建議新工作流程依賴**。
- **Cloudflare Workers AI**：`/chat/completions` 用 `messages` 欄位；
  老版 `/run/{model}` 用 `prompt` 欄位，兩者不同。
- **Google Gemini**：免費配額依模型大幅差異，flash-lite 高，標準模型低至 20 RPD。
- **配額動態性**：上游維護者提醒——免費層配額常改，建工作流程前驗 provider console。

### 4.4 OpenAI-compatible 閘道接線方式（待起動知識）

所有 38 個供應商均接受：

```
POST {base_url}/chat/completions
Authorization: ******
Content-Type: application/json

{
  "model": "{model_id}",
  "messages": [{"role": "user", "content": "..."}],
  "stream": false
}
```

對齊母體現有 `OllamaGateway`，未來可建立 `OpenAIGateway(base_url, api_key, model)`
直接接入 `AgentSession`，無需更改上層迴圈。

---

## 五、當下狀態（依 CLAUDE.md 狀態回報約定）

- 知識目錄建立：**PASS（沙盒，2026-07-10）** — `08_sources/free_byok_providers_v1.yaml`
- sources.manifest.yaml 追加：**PASS（沙盒，2026-07-10）**
- `OpenAIGateway` 程式碼產物：**待起動 / 待實機需求確認** — 知識已就位，程式碼待建
- 任何供應商實際 API 呼叫：**沙盒無對外網路，待實機驗收**

---

## 六、相關母體文件

- 吸收協定模板：`docs/MRL_主線回填清單模板_v1.md`
- AgentHarness 骨架（ModelGateway 可插拔點）：`09_workflow/MRL_AgentHarness_Kernel_v1.py`
- 知識源索引：`08_sources/sources.manifest.yaml`
- 供應商目錄：`08_sources/free_byok_providers_v1.yaml`
