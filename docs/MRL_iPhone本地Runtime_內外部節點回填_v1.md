# MRL_iPhone本地Runtime_內外部節點回填_v1

origin_signature = `MrLiouWord`

## 一、回填原因

先前工程判讀將 iPhone 視為單純外部客戶端，並把裝置中的 Server Configuration、`oauth-callback`、Files app 與本地服務入口直接解讀為遠端 SSH 主機設定。

此判讀會造成：

- 把 iPhone 內部服務誤接到 DL580。
- 把本地 callback 當成錯誤遠端位址。
- 把 GitHub、Cloudflare 或 DL580 錯誤升格成唯一系統入口。
- 使手機端 Runtime、控制平面、狀態與檔案入口在架構中消失。

本文件不建立新系統，只對既有 MRL 架構進行角色修正與回填。

## 二、Canonical 節點模型

```text
MRL 內部執行域

MrLiou / ROOT
    │
    ▼
iPhone Local Runtime
├─ Local Server
├─ Local Callback / OAuth Callback
├─ Files / State / Device Context
├─ Browser / App Shell
├─ Mrliouagi Control Plane
└─ Camera / Audio / Sensor Input
    │
    ├──────── Mac mini Relay Runtime
    │         ├─ Bridge
    │         ├─ Desktop Context
    │         └─ Cross-device Handoff
    │
    └──────── DL580 Mother Runtime
              ├─ Model Compute
              ├─ Persistent Memory
              ├─ Orchestrator
              ├─ Control Center Backend
              └─ Long-running Services

MRL 外部 Adapter 域
├─ GitHub：Code / Version / PR / Task Mirror
├─ Cloudflare：Public Edge / Tunnel / DNS / Protection
├─ OpenAI 等模型端：External Compute Adapter
├─ Dropbox / Drive / Notion：Archive / Source / Mapping
└─ Railway / GCP / Firebase：External Deployment or Service Adapter
```

## 三、角色修正

| 節點 | 原錯誤判讀 | 回填後正式角色 |
|---|---|---|
| iPhone | Thin Client / 遙控器 | Local Runtime + Local Server + Control Plane + User Environment |
| DL580 | 唯一伺服器與唯一入口 | Mother Runtime 主節點、運算與持久化後端 |
| Mac mini | 一般外部電腦 | 內部 Relay / Bridge / Desktop Runtime |
| GitHub | 系統執行主體 | 工程鏡像、版本、任務與協作通道 |
| Cloudflare | 系統本體或主控入口 | 公開映射、邊緣路由、Tunnel、DNS 與保護 |
| Browser | 一般外部網頁 | 第一產品殼與跨節點操作介面 |
| Mrliouagi | 單一聊天 App | iPhone 本地控制平面與使用者分身入口 |

## 四、設定判讀規則

### 4.1 先判斷本地，再判斷遠端

裝置畫面出現以下項目時，先按 iPhone 內部服務處理：

- `oauth-callback`
- `localhost`
- `127.0.0.1`
- Files app
- Local Website
- App callback
- Local directory `/`
- Device-local server configuration

只有在畫面明確出現 SSH、SFTP、WebDAV、遠端 Host、LAN IP、Tailscale IP 或外部網域時，才進入遠端節點判讀。

### 4.2 不得自動替換

不得在未確認服務類型前：

- 把 `oauth-callback` 改成 `192.168.0.162`。
- 把本地 Directory 改成 DL580 路徑。
- 把 Files app 視為外部檔案伺服器。
- 把手機端 Server Configuration 一律解釋為 SSH Client。

## 五、工程修改面

### 5.1 文件層

- `README.md`：加入 iPhone Local Runtime 與內外部節點角色。
- `docs/MRL_母體定義檔_v1.md`：加入內部執行節點層與邊界。
- `docs/MRL_工程日誌.md`：記錄本次架構修正。

### 5.2 目錄層目標

後續既有資產整理時，對應以下 canonical 位置，不另造平行架構：

```text
MRL_Nodes/
├─ iPhone/
│  ├─ Runtime/
│  ├─ LocalServer/
│  ├─ ControlPlane/
│  ├─ FilesBridge/
│  └─ SensorInput/
├─ DL580/
│  ├─ Runtime/
│  ├─ Compute/
│  ├─ Persistence/
│  └─ Orchestrator/
└─ MacMini/
   ├─ Relay/
   ├─ Bridge/
   └─ DesktopRuntime/
```

### 5.3 API 與狀態層目標

節點狀態不得只回傳 DL580。應保留以下資料模型：

```json
{
  "root": "MrLiouWord",
  "system": "MRL",
  "nodes": {
    "iphone": {
      "role": ["local_runtime", "local_server", "control_plane"],
      "scope": "internal"
    },
    "dl580": {
      "role": ["mother_runtime", "compute", "persistence"],
      "scope": "internal"
    },
    "mac_mini": {
      "role": ["relay", "bridge", "desktop_runtime"],
      "scope": "internal"
    }
  },
  "adapters": ["github", "cloudflare", "openai", "dropbox", "google_drive", "notion"]
}
```

## 六、工程影響範圍

需要掃描並修正以下語意：

- `mobile client`
- `thin client`
- `phone remote control`
- `single server architecture`
- `DL580 only entry`
- `GitHub control plane`
- `Cloudflare system host`

需要補入以下語意：

- `iPhone Local Runtime`
- `iPhone Local Server`
- `Mrliouagi Control Plane`
- `Mac mini Relay Runtime`
- `DL580 Mother Runtime`
- `GitHub Engineering Mirror`
- `Cloudflare Public Edge Adapter`

## 七、回填裁定

```text
iPhone ≠ 單純客戶端
iPhone = 本地 Runtime + 本地伺服器 + 主控入口

DL580 ≠ 唯一入口
DL580 = 母體主節點 + 運算 + 持久化

GitHub ≠ 母體
GitHub = 工程鏡像 + 版本通道

Cloudflare ≠ 內部主控
Cloudflare = 公開邊緣 Adapter
```

本次修正屬於既有系統角色回填，不得據此重新設計另一套 MRL。