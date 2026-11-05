# deploy/tailscale

origin_signature = `MrLiouWord`

- 用途：Tailscale 私有網路接線
- `MRL_mac_partner_setup.sh`：一鍵把 mac-mini 準備成「夥伴節點」(Claude Code on Mac)。
  在 Mac 上單行執行：`git clone https://github.com/dofaromg/mrl_ai_system && bash mrl_ai_system/deploy/tailscale/MRL_mac_partner_setup.sh`（冪等、Additive-Only）。

> 部署鏈：Cloud Code → GitHub(dofaromg/MRL_AI_SYSTEM) → deploy/dl580 → Tailscale/SSH/self-hosted runner → DL580 本地 Runtime → MRL_RuntimeServer.js → MRL 母體自行運行。
