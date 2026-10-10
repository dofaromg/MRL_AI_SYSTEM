# LocalAI Recovery R02 操作說明

origin_signature: MrLiouWord

本目錄是雲端編寫的新增維運補件。對象為 DL580（WIN-PBVUI7VK2A6），採 SUPPLEMENT_EXISTING、Verify→Backfill、APPEND_ONLY。D 槽原件、資料、金鑰及原始 logs 留在 D 槽；本目錄只收錄雲端來源與核對後的執行 metadata。

## 1. 已執行狀態

| 項目 | 實際結果 | 證據界線 |
|---|---|---|
| 固定復原包 | be2f1d63ed355bb972241cc0db4eeecceeb0f04d 的 33 檔已在 D 槽逐檔核對 | 後續補件不改這 33 檔或其 manifest |
| MCP / MetaCode | 實機官方 SDK HTTP、SSE 各 echo／identity 8/8；原始 MetaCode PASS | 實機執行綁定 33551268…；對應 MCP／MetaCode blobs 在 be2f1d63…未變 |
| 推論 7500 | 使用本機既有授權完成合成請求，HTTP 200、預期答案相符 | persist=false；PID 20580 與來源保留 |
| Watchdog | MRL_Watchdog 已設定並啟動；活動觀察驗證 PASS | ASI 自動恢復仍 HELD_UNRESOLVED_RELATIVE_PROCESS；未做故障／重開機測試 |
| Qdrant 1.19.2 | 私有 SYSTEM task 已安裝、啟動；來源、程序、ACL、授權與 loopback 十項 gate PASS | task 有開機與有限重試設定；實際 reboot／restart execution 未測 |
| 常駐 Qdrant 合成讀寫 | 建立／寫入／精確讀回 PASS；v2 自動 CRUD 收據 HOLD（DELETE 回應逾時）；其後唯讀觀察 API 清單已無該集合 | 詳見 OPERATIONS_RUNTIME_EVIDENCE.json 與 RUNTIME_EVIDENCE.md；第一次 timeout 收據保留 |

原 Watchdog 的語法修補候選只作為保留原件的最小差異候選，沒有啟動。現在運行的是另外核對過的 v3 活動觀察程式。7500／7800 在此 Watchdog 中均為 REPORT_ONLY。

## 2. 已安裝 Qdrant 的日常核對

**本次 stage、install、start 均已完成。直接使用既有 instance 做 verify；重跑 stage 會另建 UUID、storage 與 key。**

在本機受授權的 SYSTEM／elevated 管理環境：

~~~powershell
$Python = 'D:\MrlToolchain\python\python.exe'
$OpsBase = 'D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63'
$OpsSource = Join-Path $OpsBase 'qdrant_local_service_20261010_R02'
$Instance = 'D:\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d'
$Control = Join-Path $Instance 'runtime\MRL_qdrant_local_service_v1.py'
& $Python -B $Control verify --instance $Instance
~~~

可接受的狀態為 DURABLE_LOCAL_SERVICE_VERIFIED：exact task Running、固定來源與 executable hash 相符、PID creation identity 相符、私有 ACL 正確、僅 127.0.0.1:6333、有 key 的保護 API 成功且無 key 被拒絕。verify 會新增 D 槽收據，不建立集合，也不代替 CRUD。

連線 metadata 在 instance\connection.json；key 由主機生成並留在 instance\private\api-key.txt，僅 SYSTEM／Administrators 可存取。HTTP header 為 api-key。受授權本機應用必須自行讀取該受保護金鑰；本次沒有將金鑰寫入既有應用或宣告應用已接線。收據不含 key 或 key hash。

服務僅使用 HTTP loopback；gRPC、dedicated metrics、cluster、telemetry 關閉。storage、snapshots、tmp 均在短 D 槽 instance 路徑。程序只控制自己的 Popen child 與 Windows Job，無依 PID 猜測殺程序的行為。

## 3. 有界合成讀寫

本次 v1 第一次 create response timeout 後，未取得建立確認，故未清理該集合。其後唯讀確認為 green／optimizer ok、points 0、vector size 4／Dot。此後的成功不得改寫第一次 HOLD 收據。

v2 僅將 collection create 的客戶端 socket timeout 改為 60 秒；其他請求維持 12 秒，HTTP 請求時間預算 180 秒。所有來源、task、PID、loopback、auth 檢查、永久 ownership-failure latch，以及明確建立確認後才可清理的規則均與 v1 相同。

如日後需要另做一次有界驗收：

~~~powershell
& $Python -B (Join-Path $OpsSource 'MRL_qdrant_durable_crud_v2.py') --instance $Instance
~~~

每次使用全新 UUID collection／合成 point，先確認名稱不存在，建立、寫入、精確讀回，再刪除本次已確認建立的 collection 並確認 404。任何歸屬檢查失敗即永久 HOLD；回應不明不重試清理。此 client 不啟動、停止或重啟服務，不重用先前 timeout 的集合。

完整單次自動 CRUD 驗收成功必須有本 instance 的 DURABLE_SYNTHETIC_CRUD_PASS 收據。不能以 fixture 成功、health 成功或先前臨時 native probe 的成功替代。

## 4. 安裝來源與保留的失敗紀錄

固定來源包含官方 Qdrant 1.19.2 Windows package 的 digest、來源 helper 與 task wrapper。stage 先建立 SYSTEM／Administrators 私有 DACL，再建立 key，並把 exact source 複本放進私有 instance runtime。install 只以 TASK_CREATE 建全新的停用 task，核對後才可 start。

目前 task：MRL_Qdrant_Local_2d38cbbc0b4d4988a19f100c7b9f2d7d。設定為 SYSTEM、Boot delay 30 秒、IgnoreNew、PT0S、失敗每 60 秒最多三次。這些設定已讀回；尚無主機 reboot 或服務故障注入實測。

R01 instance fca6388e453e4c4a8319561470a42d84 因 Task Scheduler BSTR/XML encoding 宣告不符而未安裝。D 原目錄與失敗輸出保留，未建立 task／listener。R02 僅移除 XML 的 UTF-8 encoding 宣告；Windows COM 記憶體驗證、28 個 fixtures 與實際註冊均通過。

原 native probe 的 JSON 配置失敗與長路徑失敗也保留；v3 改用短路徑後 12/12 CRUD 通過，該臨時程序已停止。它與現在的常駐 instance 分別記錄。

## 5. 手動維護的 stop／remove

以下只供之後有意停止此 instance 時使用，本次未執行：

~~~powershell
& $Python -B $Control stop --instance $Instance
Get-NetTCPConnection -State Listen -ErrorAction Stop |
  Where-Object { $_.LocalPort -in 6333,6334,6335 } |
  Select-Object LocalAddress,LocalPort,OwningProcess
~~~

stop 停用並停止自己的 exact task。若沒有 run_*_ready.json，尤其 startup 中途停止，不得單憑 own_listener_stopped 欄位宣告已清除；須另確認查詢成功且 6333／6334／6335 沒有 listener。歸屬不明保持 HOLD，不代殺其他 PID。

自己的 task 已停用、停止並完成上述確認後，才能 remove：

~~~powershell
& $Python -B $Control remove --instance $Instance
~~~

remove 只移除自己的新 task，保留 instance 的來源、設定、key、storage、log 與收據。

## 6. 來源與尚待接入的項目

OPERATIONS_MANIFEST.json 核對本目錄及新 workflow，manifest 不自雜湊。GitHub CI 執行 metadata／syntax gate、Watchdog 29 個記憶體案例、Qdrant service 28 個案例、CRUD v1 9 個與 v2 10 個案例；這些 source fixtures 與實機收據分開記錄。

執行來源核對：

~~~powershell
& $Python -B .\MRL_Recovery_Operations\20261010_R02\verify_operations_manifest.py
~~~

此 source gate 需有 pwsh 以靜態解析 PowerShell 補件，不會執行 DL580 控制程式。

整體仍有明確未完成項：3050 relative server.js 的啟動來源歸屬、Watchdog 故障／reboot 恢復實測、Qdrant 應用整合、MinIO/S3 的正式端點或可採用部署來源、MetaEnv controller /api/v1/env/* 的實際契約、production OAuth provider／callback／session／logout。這些不能由本次 source、health 或 build PASS 推論為完成。

來源 lineage、失敗歷程、實機收據路徑／bytes／SHA256 與實測時間均見 RUNTIME_EVIDENCE.md 及 OPERATIONS_RUNTIME_EVIDENCE.json。
