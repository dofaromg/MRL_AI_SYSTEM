# MRL Product Canonicalization Gate v1

## 1. 固定主體

```text
product = MrliouAI
source_owner = Mrliou
origin_signature = MrLiouWord
```

## 2. 分層規則

```text
External Source / Platform / Transport
→ Adapter / Provenance / Compatibility
→ MRL Canonicalization Gate
→ Product / Capability / Route / Packet / Trace
```

## 3. 允許

- 外部名稱可存在於 `source_adapter`、`provenance`、`compatibility_alias`、歷史審計文件。
- MRL 產品 route、packet、trace、function 與 public product identity 必須使用 MRL / Mrliou 命名。

## 4. 禁止

- 外部平台名稱直接成為產品 route 主體。
- 外部平台名稱直接成為 packet type。
- 外部平台名稱直接成為 trace prefix。
- 只靠 `origin_signature` 取代產品與來源欄位。
- 測試要求外部名稱存在於 canonical runtime。

## 5. 最小資料契約

```json
{
  "product": "MrliouAI",
  "source_owner": "Mrliou",
  "origin_signature": "MrLiouWord",
  "mrl_kind": "MRL_<Capability>Packet",
  "trace_id": "MRL-<CAPABILITY>-..."
}
```

## 6. 驗收門

每次新增產品 route / packet / trace 時必須驗證：

1. product 為 `MrliouAI`。
2. source_owner 為 `Mrliou`。
3. origin_signature 為 `MrLiouWord`。
4. canonical identifier 不含外部平台名稱。
5. 外部來源若存在，只能進 provenance / adapter metadata。
