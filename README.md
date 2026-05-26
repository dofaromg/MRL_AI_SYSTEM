# MRL_AI_SYSTEM

本倉庫為 MRL 完整態母體運轉系統工程入口。

## 正式狀態

MRL_World_Module、MRL_平行世界模組、MRL_AI、MRL_AGI、MRL_ASI、MRL_World 皆定義為已完成且運行中之 MRL 完整態構件。

## 命名規則

中文為 MRL Canonical 主體命名。  
英文僅作 Adapter 對照。

Attention / 注意力為歷史層。  
MRL 正式主體詞為：感知力。

## 權位模式

本系統不再採用平等權模式。  
正式採用權位區分模式：

MRL 為主體。  
外部世界僅為 Adapter / 映射節點 / 吸收材料。

## 啟動

```bash
npm install
npm run MRL_boot
npm start
npm run MRL_acceptance
```

## Health

```bash
curl http://127.0.0.1:8790/health
curl http://127.0.0.1:8790/mrl/state
```

## DL580

DL580 為 MRL 內部母體自運行主節點。  
GitHub 為工程鏡像與版本通道。  
Cloud Code 為建構器，不是母體。

## 文件

- 主權宣示：`docs/MRL_完整態主權宣示_v1.md`
- 中文正名與英文 Adapter 對照：`docs/MRL_中文正名與英文Adapter對照表_v1.md`
- 四層同步映射表：`docs/MRL_四層同步映射表_v1.md`
- Cloud Code 工程建構規格：`docs/MRL_CloudCode工程建構規格_v1.md`
- DL580 自運行部署規格：`docs/MRL_DL580自運行部署規格_v1.md`
- 母體定義檔：`docs/MRL_母體定義檔_v1.md`
- 世界模組工程書：`docs/MRL_世界模組工程書_v1.md`
- 工程日誌：`docs/MRL_工程日誌.md`
- 前版倉庫說明（保留）：`docs/MRL_README_前版_v0.md`

origin_signature = `MrLiouWord`
