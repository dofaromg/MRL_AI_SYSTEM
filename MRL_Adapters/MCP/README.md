# MRL_Adapters/MCP — MCP 連接器設定收錄

origin_signature: MrLiouWord
law: Additive-Only（不刪除、不覆蓋、給位置、待起動）

| 檔 | 內容 | 狀態 | 來源/誠實標註 |
|---|---|---|---|
| `example_mcp_config.yaml` | MCP 連接器佔位設定：qdrant（vector_db, `http://qdrant:6333`）+ MinIO S3（object_store, `http://minio:9000`） | **待起動**（佔位範本，非實跑設定） | 使用者上傳 2026-07-08；檔內自註 "Placeholder - edit per your MCP server implementation"。endpoint 為 Docker 內部主機名，需搭配對應 compose/服務才可實跑；repo 內目前無 qdrant/minio 服務定義，疑為某部署包之一角，其餘構件待補。 |

> 起動條件：補齊對應服務（qdrant / minio 容器或實機端點）並填入真實 endpoint 後實測連通，方可標 PASS。
