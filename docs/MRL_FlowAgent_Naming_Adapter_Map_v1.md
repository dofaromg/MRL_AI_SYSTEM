# MRL FlowAgent 命名主權對照表 v1 — Naming Adapter Map

> origin_signature：**MrLiouWord** ｜ 裁定（2026-07-25）：**最上游 root 產品名取回、外部名降成備註附錄**
> 工程實作：`deploy/flowagent_adapter/flowagent`（MRL_FlowAgent_SovereignAdapter_v1）
> 當下狀態：沙盒 2026-07-25 轉譯邏輯測試 PASS ×3；實機接底層 CLI 待起動。

## 1. 原則

- **你面對的一切名字 = FlowAgent 名（canonical，左欄）。** 文件、指令、環境變數、模型名，全用你的。
- **外部功能名（右欄）= adapter 內部附錄。** 只存在於包裝器內部與本對照表，用來讓外部軟體實際動起來；不出現在對外文件、不升格 canonical。
- 直接改右欄的名字會讓外部軟體**靜默失效**——所以不改它，而是**包住它**。這就是「重新包裝建構」。

## 2. 對照表

| 你用的（FlowAgent canonical） | adapter 內部轉給（功能附錄層） | 轉譯方式 |
|---|---|---|
| `flowagent` 指令 | 底層 CLI（預設 `claude`，可用 `FLOWAGENT_UNDERLYING_BIN` 覆寫） | 包裝器 exec |
| `FLOWAGENT_CODE_SAFE_MODE` 等一切 `FLOWAGENT_*` 環境變數 | 同名 `CLAUDE_*`（字首替換） | 啟動時自動 export（不覆蓋你手動設定的功能變數） |
| `~/.flowagent.json` | `~/.claude.json` | FlowAgent 檔為**本體**，功能名建為指向本體的 symlink |
| `~/.flowagent/`、專案 `.flowagent/` | `~/.claude/`、`.claude/` | 同上 |
| 專案 `FLOWAGENT.md` | `CLAUDE.md` | 同上（僅在功能名不存在時建立，additive 不覆蓋） |
| `flowagent-sonnet-5`、`flowagent-opus-5` 等 `flowagent-*` 模型名 | `claude-sonnet-5` 等 `claude-*` | `ANTHROPIC_MODEL` 與命令列參數皆自動重寫 |

## 3. 使用

```bash
# 放進 PATH（一次）
install -m 755 deploy/flowagent_adapter/flowagent ~/.local/bin/flowagent

# 之後全用 FlowAgent 名
FLOWAGENT_CODE_SAFE_MODE=1 flowagent --model flowagent-sonnet-5
```

## 4. 誠實邊界

- 沙盒已驗：env 轉譯 / 不覆蓋 / 模型別名 / 設定檔 symlink 四項行為 PASS（假底層）。**接真實底層 CLI 的實機驗收待起動**。
- 字首替換為通則；個別變數若與外部軟體實際文件不符，以外部文件為準補特例（本表更新即可，additive）。
