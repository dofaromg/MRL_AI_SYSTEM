# deploy/tailscale

origin_signature = `MrLiouWord`

- 用途：Tailscale 私有網路接線
- `MRL_mac_partner_setup.sh`：一鍵把 mac-mini 準備成「夥伴節點」(Claude Code on Mac)。
  在 Mac 上單行執行：`git clone https://github.com/dofaromg/mrl_ai_system && bash mrl_ai_system/deploy/tailscale/MRL_mac_partner_setup.sh`（冪等、Additive-Only）。
- `MRL_dl580_partner_setup.sh` / `MRL_dl580_partner_setup.ps1`：以同樣方式在 DL580 本機配置 Claude Code 工程夥伴，支援 Linux / Windows；DL580 仍為母體自運行節點。

## DL580 一鍵夥伴設定

先以日常登入帳號取得 repo；已有 checkout 就直接在該目錄執行，**不用重新 clone**。
以下初次 clone 指令使用目前既有母體分支 `MrliouAI`；若使用其他部署分支，請沿用該 checkout。

Linux（systemd）：

```bash
git clone --branch MrliouAI https://github.com/dofaromg/MRL_AI_SYSTEM.git
bash MRL_AI_SYSTEM/deploy/tailscale/MRL_dl580_partner_setup.sh
```

Windows（PowerShell；原生 Claude Code 需要 Git for Windows / Git Bash）：

```powershell
git clone --branch MrliouAI https://github.com/dofaromg/MRL_AI_SYSTEM.git
& .\MRL_AI_SYSTEM\deploy\tailscale\MRL_dl580_partner_setup.ps1
```

既有 checkout：Linux 執行 `bash deploy/tailscale/MRL_dl580_partner_setup.sh`；
Windows 執行 `& .\deploy\tailscale\MRL_dl580_partner_setup.ps1`。
請遵循本機 PowerShell 執行原則，不需要永久放寬執行原則。

### 前置依賴與設定邊界

- Linux：Git、Python 3、curl、systemd、已安裝的 OpenSSH server（`ssh.service` 或 `sshd.service`）；只有啟用服務時需要 sudo。
- Windows：Git for Windows、可用的 `python`（Python 3，不是 Store alias）、curl、已安裝的 OpenSSH Server optional feature；只有啟用服務時需要管理員權限。請先由管理員啟用 `sshd`，再以日常帳號執行，讓 Claude 安裝到正確帳號。
- DL580 與 iPhone 均須安裝並登入同一 Tailscale Tailnet；Tailscale 安裝／互動登入及 ACL 由管理員維護。腳本不接收或儲存 auth key。
- Claude Code 使用官方 HTTPS 安裝程式，僅在找不到既有 CLI 時下載至暫存檔並執行、清理；需可存取 `claude.ai` 及其官方下載端點，且主機符合官方 OS／CPU 需求。首次 `claude` 登入仍需使用者互動。
- repo 僅在工作目錄乾淨且有 upstream 時 `pull --ff-only`；本地變更、無 upstream、網路／分歧失敗均保留原檔並標記 PARTIAL。獨立下載腳本不支援，必須位於母體 checkout。
- 不覆寫 `sshd_config`、認證方式、電源策略或現有 Runtime；不開公開防火牆埠、不執行 `tailscale up --ssh`、不自動安裝模型。若 SSH 原埠不是 22，請沿用原埠。
- 依序檢查／啟用 SSH、讀取實際 Tailscale IPv4、檢查／安裝 Claude Code、執行 `09_workflow/MRL_mother_assembly.py status`，最後印出 Secure ShellFish 的 Host／Port／User 及登入後命令。既有 Runtime 啟動仍沿用 `deploy/dl580` 入口。
- 發生待處理項目時退出碼為 1，處理後可重跑；退出碼 0 僅表示本機設定檢查通過，**不代表 SSH 端到端、DL580 上線或真模型驗收通過**。

### 實機驗收（當下狀態：待實機）

1. 在 DL580 本機執行對應入口，確認沒有 PARTIAL，再重跑確認沿用既有 CLI／服務。
2. iPhone 接入同一 Tailnet，在 Secure ShellFish 使用腳本列出的帳號與位址，確認 ACL／主機防火牆允許私網 SSH 及既有認證方式。
3. 登入後切到母體 checkout，Windows 先進入 PowerShell，執行輸出的命令並完成 Claude 登入。
4. 分別驗收母體 Runtime 與真模型 endpoint；`status` smoke 不能替代這兩項。

> 部署鏈：Cloud Code → GitHub(dofaromg/MRL_AI_SYSTEM) → deploy/dl580 → Tailscale/SSH/self-hosted runner → DL580 本地 Runtime → MRL_RuntimeServer.js → MRL 母體自行運行。
