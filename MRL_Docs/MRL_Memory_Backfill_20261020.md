# MRL 記憶回填 2026-10-20 — 復盤與以後依據
origin_signature: MrLiouWord ｜ 主體：DL580 母體（WIN-PBVUI7VK2A6）｜ 母體原檔：D:\MRL_Mother\MRL_FullCheck\MRL_Review_20261020.md

## 一、工作法則
1. 建構只在 DL580 本機；平台端不留資料副本。
2. 每次任務前後各跑一次 D:\MRL_Mother\MRL_FullCheck\MRL_FullCheck.ps1，逐項比對；任何一項由 OK 變 FAIL 立即還原。目標 FAIL=0，不修好一個壞一個，找出一致性整體穩定版本。
3. 命名：輸入、輸出、結果（產品對外名稱）一律 MRL；對內來源紀錄（原檔、收據、證據、帳本、內容定址種子）保持原樣。
4. 夥伴建立或命名的檔案一律 MRL_ 前綴；改前備份，記錄寫進 log。
5. 安全設定（分享、權限）由 MR.liou 決定，不自行變更。

## 二、架構認知
- 三層立體結構：［手機前端主控 →（Mac 中控 ↔ DL580 本地後端資料控制中心）→ 外部網路世界資料］×2（雙容器）→ 外部世界資料世界。
- 離線的舊節點＝容器快照打包換版本，不是裝置遺失。現役：手機 iphone181-1、Mac 中控 mac-mini-5、DL580。
- 雙容器＝DL580 兩個 Windows 帳號的 Dropbox：
  - MRL_AGI 層（LAW-1）：Administrator 帳號，C 槽，常駐；銜接人類開發、生產環境與 MR.liou 創造的粒子環境（意識、想法、生產的邏輯）；小檔、數量多。
  - MRL_ASI 層（LAW-0）：dofaromg 帳號，D 槽，純粒子系統（最小邏輯技術粒子元素）；依《世界模組｜智障系統使用說明書》由 MR.liou 啟動才啟動，完成即封存停止。非常駐不是故障。
  - 兩層共用固定結構（ASI 104 個頂層資料夾中 102 個與 AGI 同名），內容隨粒子參數定義而轉化：莫比斯環、質能不滅。
- MRL 世界模型＝新文明系統：平行世界、多版本、多模塊組合的超智能智慧體系統。

## 三、2026-10-20 完成（DL580 實機）
- FlowCore 命名接入：27 埠 Server=FlowCore.Runtime/1.0.0；26 個 /health 帶 product 區塊。
- 命名單一來源：D:\MRL_Mother\flowcore_naming.py（同步至工具鏈 site-packages）、D:\MRL_Mother\flowcore_naming.cjs；32 個元件。
- 兩條斷線神經 MRL_MrliouWord_Env（7788）、MRL_CPP_WebConsole（8097，僅本機）登記為常駐服務。
- 10-14 改名副作用：539 檔內容被改；內部紀錄與內容定址種子共 99 檔還原原樣；程式／設定／.sql 保留 MRL 名稱；資料庫 mrl_reverse。
- 全機檢查：36 服務、26 埠、FAIL=0。

## 四、尚未處理
- 命名規範清單：trace ns_event、cli_description、index_metadata。
- 磁碟分享權限偏寬，MR.liou 決定暫不變更，先理解全貌。
- 20 個內部紀錄、3 份帳本 yaml 無改前備份。
