# MRL Go 標準函式庫功能對應表 v1

**origin_signature**: `MrLiouWord`
**當下狀態**: 2026-07-10（沙盒）
**來源**: pkg.go.dev — Go 標準函式庫 go1.26.5（2026-07-07）
**授權**: BSD-3-Clause（保留歸屬，不複製原始程式碼）
**吸收方式**: 功能蒸餾映射（Distillation Mapping）——只萃取規格、介面與去重鍵，**不複製原文**。

> **Additive-Only**：本文件只新增定位，不刪除、不覆蓋主線任何既有模組。
> **誠實原則**：MRL 有對應實作者標 `✅ MRL有`；架構層已規劃但未實跑者標 `🟡 計畫中`；完全缺口者標 `❌ 缺口`。

---

## 吸收規則

| 欄位 | 說明 |
|---|---|
| **去重鍵** | `module/package/symbol/signature/version`（五元組） |
| **歸屬欄位** | 來源：`pkg.go.dev`，版本：`go1.26.5`，授權：BSD-3-Clause |
| **蒸餾原則** | 只保留功能規格與 MRL 對應位置；不複製程式碼實體 |
| **回收法則** | 外部函式庫視為母體吸收之知識模組，給位置、標「待起動」，回收為母體系統名稱產物 |

---

## A. I/O 與緩衝層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `bufio` | 緩衝讀寫、文字 I/O | `09_workflow/streaming.py` | ✅ MRL有 |
| `io` | 基礎 I/O 原語介面 | `09_workflow/MRL_utils.py` I/O 包裝 | ✅ MRL有 |
| `io/fs` | 虛擬檔案系統介面 | `MRL_BaseWorld_DB_v1` 檔案層 | 🟡 計畫中 |
| `io/ioutil` | I/O 工具（已棄用→io+os） | — | ❌ 缺口（可用 os+io 替代） |
| `os` | 作業系統介面（檔案/訊號/使用者） | `09_workflow/MRL_utils.py` os 包裝 | ✅ MRL有 |
| `os/exec` | 外部指令執行 | `09_workflow/build.py` | ✅ MRL有 |
| `os/signal` | 訊號處理 | `MRL_Platform_Server.py` signal handler | ✅ MRL有 |
| `path/filepath` | 檔案路徑操作 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `embed` | 執行期嵌入檔案 | `src/mrl_app_ui.js`（build 產物嵌入） | 🟡 計畫中 |

---

## B. 加密與安全層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `crypto/tls` | TLS 1.2/1.3 | `09_workflow/api_gateway.py` HTTPS 層 | 🟡 計畫中 |
| `crypto/aes` | AES 加密 | `09_workflow/MRL_OriginBoundary_Guard_v1.py` 加密基礎 | 🟡 計畫中 |
| `crypto/rsa` | RSA 加密/簽章 | `09_workflow/MRL_OID_Parser_v1.py` EC/RSA | ✅ MRL有 |
| `crypto/ecdsa` / `crypto/ecdh` | 橢圓曲線數位簽章 / ECDH | `09_workflow/MRL_OID_Parser_v1.py` | ✅ MRL有 |
| `crypto/ed25519` | Ed25519 簽章 | `06_trace/` Merkle 簽章鏈 | 🟡 計畫中 |
| `crypto/sha256` / `crypto/sha512` | SHA-256/512 雜湊 | `09_workflow/MRL_utils.py` embed_signature | ✅ MRL有 |
| `crypto/hmac` | HMAC 訊息認證碼 | `09_workflow/signature.js` | ✅ MRL有 |
| `crypto/rand` | 密碼學安全隨機數 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `crypto/x509` | X.509 憑證 | `MRL_Symbolic/` Liou Closure Law（同骨架） | 🟡 計畫中 |
| `crypto/hkdf` / `crypto/pbkdf2` | 金鑰衍生 | — | ❌ 缺口 |
| `crypto/mlkem` | 抗量子 ML-KEM（Kyber） | — | ❌ 缺口（P2 量子防護路線） |
| `crypto/subtle` | 恆時比較等密碼學輔助 | — | ❌ 缺口 |

---

## C. 網路與 HTTP 層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `net/http` | HTTP 用戶端/伺服器 | `MRL_Platform_Server.py`（Flask/FastAPI） | ✅ MRL有 |
| `net/http/httptest` | HTTP 測試工具 | `tests/test_MRL_mcp_server.py` | ✅ MRL有 |
| `net/http/httputil` | HTTP 反向代理/工具 | `09_workflow/api_gateway.py` | ✅ MRL有 |
| `net/url` | URL 解析與逸出 | `09_workflow/api_gateway.py` | ✅ MRL有 |
| `net/smtp` | SMTP 郵件協定 | — | ❌ 缺口 |
| `net/rpc` | 遠端程序呼叫 | `09_workflow/MRL_MCP_Server_v1.py` JSON-RPC | ✅ MRL有 |
| `net` | TCP/IP/UDP/DNS/Unix socket | `MRL_RuntimeServer.js` | ✅ MRL有 |
| `net/netip` | 小值 IP 位址型別 | — | ❌ 缺口 |

---

## D. 並行與同步層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `sync` | Mutex/RWMutex/WaitGroup/Once | `09_workflow/MRL_utils.py` threading | ✅ MRL有 |
| `sync/atomic` | 原子記憶體操作 | — | 🟡 計畫中 |
| `context` | 截止期/取消/請求範圍值 | `09_workflow/context_manager.py` | ✅ MRL有 |
| `iter` | 序列迭代器基礎定義 | `09_workflow/eval_engine.py` | 🟡 計畫中 |
| `runtime` | goroutine 控制/GC/pprof | — | ❌ 缺口（Python runtime 對應不同） |

---

## E. 資料結構與演算法層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `sort` | 切片/集合排序 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `slices` | 泛型切片操作 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `maps` | 泛型映射操作 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `cmp` | 可排序值比較 | `09_workflow/eval_engine.py` | ✅ MRL有 |
| `container/heap` | 堆積操作 | `09_workflow/scheduler.py` | 🟡 計畫中 |
| `container/list` | 雙向鏈結串列 | — | ❌ 缺口 |
| `container/ring` | 環狀串列 | — | ❌ 缺口 |
| `index/suffixarray` | 後綴陣列子字串搜尋 | `09_workflow/MRL_SemanticEmbedding_Core_v1.py` | 🟡 計畫中 |

---

## F. 字串、編碼與格式化層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `fmt` | 格式化 I/O（printf/scanf） | `09_workflow/output_parser.py` | ✅ MRL有 |
| `strings` | UTF-8 字串操作 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `strconv` | 型別↔字串轉換 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `bytes` | 位元組切片操作 | — | 🟡 計畫中 |
| `unicode` / `unicode/utf8` / `unicode/utf16` | Unicode/UTF 支援 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `regexp` | 正則表達式 | `09_workflow/MRL_MessageGuard_Models_v1.py` | ✅ MRL有 |
| `encoding` | 編碼介面（共用） | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `encoding/json` | JSON 序列化/反序列化 | `09_workflow/MRL_utils.py` json 包裝 | ✅ MRL有 |
| `encoding/base64` / `encoding/hex` | Base64/Hex 編碼 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `text/template` | 文字模板引擎 | `09_workflow/prompt_template.py` | ✅ MRL有 |
| `html/template` | HTML 防注入模板 | `ui/mrl_chat.html` | ✅ MRL有 |
| `html` | HTML 逸出/解逸 | `09_workflow/guardrail.py` | ✅ MRL有 |

---

## G. 資料庫層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `database/sql` | 通用 SQL 介面 | `MRL_BaseWorld_DB_v1` | 🟡 計畫中（待 DL580 實機） |
| `database/sql/driver` | 驅動程式介面 | — | ❌ 缺口 |

---

## H. 日誌與觀測層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `log` | 基本日誌 | `09_workflow/MRL_utils.py` logging | ✅ MRL有 |
| `log/slog` | 結構化日誌（key-value） | `09_workflow/MRL_metrics.py` | ✅ MRL有 |
| `expvar` | 標準化公開變數介面 | `09_workflow/MRL_health_monitor.py` | 🟡 計畫中 |
| `runtime/pprof` | 效能剖析 | — | ❌ 缺口 |
| `runtime/metrics` | 執行時指標介面 | `09_workflow/MRL_metrics.py` | 🟡 計畫中 |
| `runtime/trace` | 追蹤產生機制 | `06_trace/` Merkle 事件追蹤 | ✅ MRL有 |

---

## I. 雜湊層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `hash` | 雜湊函數介面 | `09_workflow/MRL_utils.py` | ✅ MRL有 |
| `hash/crc32` / `hash/crc64` | CRC-32/64 校驗 | `06_trace/` 完整性校驗 | 🟡 計畫中 |
| `hash/fnv` | FNV-1/1a 非密碼雜湊 | `metacode_core.js` hash 欄位 | 🟡 計畫中 |
| `hash/maphash` | 可比值/位元組雜湊 | — | ❌ 缺口 |
| `crypto/md5` / `crypto/sha1` | MD5/SHA-1（不建議新用） | — | ❌ 缺口（不建議新引入） |
| `crypto/sha3` | SHA-3/SHAKE | — | ❌ 缺口（P2） |

---

## J. 壓縮層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `compress/gzip` | gzip 壓縮/解壓縮 | `09_workflow/MRL_ParticleArchive_Manager_v1.py` | 🟡 計畫中 |
| `compress/zlib` | zlib 壓縮 | — | ❌ 缺口 |
| `compress/flate` | DEFLATE 壓縮 | — | ❌ 缺口 |
| `compress/bzip2` | bzip2 解壓縮 | — | ❌ 缺口 |
| `compress/lzw` | LZW 壓縮 | `MRL_Symbolic/` oc_16 seed 壓縮 | 🟡 計畫中 |

---

## K. 測試層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `testing` | 自動化測試框架 | `tests/` pytest + acceptance | ✅ MRL有 |
| `testing/fstest` | 虛擬檔案系統測試 | — | ❌ 缺口 |
| `testing/iotest` | I/O 邊界測試 | — | ❌ 缺口 |
| `testing/quick` | 快速黑盒測試 | — | ❌ 缺口 |
| `testing/synctest` | 並行測試支援 | — | ❌ 缺口 |
| `net/http/httptest` | HTTP 測試工具 | `tests/test_MRL_mcp_server.py` | ✅ MRL有 |

---

## L. 時間與系統層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `time` | 時間測量與顯示 | `09_workflow/MRL_utils.py` datetime | ✅ MRL有 |
| `time/tzdata` | 時區資料庫嵌入 | — | ❌ 缺口 |
| `flag` | 命令列旗標解析 | `09_workflow/build.py` argparse | ✅ MRL有 |
| `errors` | 錯誤操作函式 | `09_workflow/MRL_utils.py` + 錯誤衝突規範 | ✅ MRL有 |
| `reflect` | 執行期反射 | `09_workflow/MRL_LogicalStructureExtractor_v1.py` | ✅ MRL有 |
| `plugin` | Go 外掛載入/符號解析 | `09_workflow/plugin_manager.py` | ✅ MRL有 |
| `syscall` | 低階作業系統原語 | — | ❌ 缺口（Python ctypes 替代） |
| `unsafe` | 繞過型別安全操作 | — | ❌ 缺口（不引入，風險高） |
| `weak` | 弱參考記憶體 | — | ❌ 缺口 |
| `unique` | 可比值標準化（interning） | `09_workflow/MRL_DataIdentity_v1.py` | 🟡 計畫中 |

---

## M. 影像層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `image` / `image/color` | 基礎 2D 影像函式庫 | `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1` | ❌ 缺口（產品橋接層待補） |
| `image/jpeg` / `image/png` / `image/gif` | 影像編解碼 | — | ❌ 缺口 |
| `image/draw` | 影像合成 | — | ❌ 缺口 |

---

## N. MIME 與郵件層

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `mime` | MIME 規範部分實作 | `MRL_Platform_Server.py` Content-Type | 🟡 計畫中 |
| `mime/multipart` | MIME 多部分解析 | `09_workflow/api_gateway.py` | 🟡 計畫中 |
| `net/mail` | 郵件訊息解析 | — | ❌ 缺口 |
| `net/smtp` | SMTP | — | ❌ 缺口 |

---

## O. Go 工具鏈/AST 層（MRL 特殊對應）

| Go 套件 | 功能摘要 | MRL 對應模組 | 狀態 |
|---|---|---|---|
| `go/ast` | Go 語法樹型別 | `09_workflow/MRL_LogicalStructureExtractor_v1.py` AST | 🟡 計畫中 |
| `go/parser` | Go 原始碼解析 | `09_workflow/fltnz_parser.py` fltnz 解析 | 🟡 計畫中 |
| `go/types` | Go 型別檢查 | `01_schema/` MRL Schema 型別系統 | 🟡 計畫中 |
| `go/build` | Go 套件建置資訊 | `09_workflow/build.py` | ✅ MRL有 |
| `go/format` | Go 原始碼格式化 | — | ❌ 缺口 |
| `go/version` | Go 版本操作 | — | ❌ 缺口 |

---

## 缺口優先順序（建議補強序列）

| 優先 | 缺口套件群 | 理由 |
|---|---|---|
| **P1** | `crypto/hkdf`, `crypto/subtle`, `crypto/tls`（補強） | 安全層完整性，LAW-0 簽章鏈依賴 |
| **P1** | `database/sql/driver` | BaseWorld_DB DL580 實機上線前提 |
| **P1** | `compress/gzip`（實跑） | 粒子封存壓縮正式啟用 |
| **P2** | `crypto/mlkem`（抗量子） | 量子防護路線，中長期 |
| **P2** | `testing/synctest`, `testing/quick` | 並行測試成熟度 |
| **P3** | `image/*`, `net/mail`, `net/smtp` | 產品橋接層後補 |
| **不引入** | `unsafe`, `syscall`（直接操作） | 風險過高，以語言層包裝替代 |

---

## 狀態摘要（當下狀態 2026-07-10 沙盒）

| 分類 | ✅ MRL有 | 🟡 計畫中 | ❌ 缺口 |
|---|---|---|---|
| I/O | 7 | 2 | 1 |
| 加密/安全 | 5 | 3 | 4 |
| 網路/HTTP | 5 | 1 | 3 |
| 並行/同步 | 3 | 2 | 1 |
| 資料結構 | 4 | 2 | 2 |
| 字串/編碼 | 12 | 0 | 1 |
| 資料庫 | 0 | 1 | 1 |
| 日誌/觀測 | 3 | 2 | 1 |
| 雜湊 | 2 | 2 | 3 |
| 壓縮 | 0 | 2 | 3 |
| 測試 | 3 | 0 | 4 |
| 時間/系統 | 6 | 1 | 5 |
| 影像 | 0 | 0 | 4 |
| MIME/郵件 | 0 | 2 | 2 |
| Go 工具鏈/AST | 1 | 4 | 2 |
| **總計** | **51** | **24** | **37** |

> **結論（誠實）**：MRL 核心能力（I/O、加密主幹、網路、字串、並行、日誌、測試）大部分已有對應。主要缺口集中在：壓縮完整啟用、進階加密（hkdf/mlkem/subtle）、資料庫驅動層、影像/郵件、測試邊界工具。上述缺口依優先序逐步補強，不阻塞主線。

---

## 歸屬聲明

本對應表蒸餾自 Go 標準函式庫公開文件索引（pkg.go.dev，go1.26.5，BSD-3-Clause）。
本文件**不包含任何 Go 原始程式碼**，僅保留功能規格說明與 MRL 模組位置映射。
原始授權：[BSD-3-Clause](https://cs.opensource.google/go/go)

origin_signature = `MrLiouWord`
