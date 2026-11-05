# 放 cJSON v1.7.19 於此

本模組不內含 cJSON（保持你倉庫乾淨、且尊重上游 MIT 授權）。建置前把 **cJSON v1.7.19**
的兩個檔案放進本資料夾：

```
third_party/cjson/cJSON.c
third_party/cjson/cJSON.h
```

來源（單檔、MIT）：https://github.com/DaveGamble/cJSON （tag v1.7.19）
只需要 `cJSON.c` 與 `cJSON.h` 兩個檔（`cJSON_Utils` 非必要）。

放好後於 `MRL_Bridge_MCP/` 執行 `make`（或用 README 的一行 gcc 指令）即可產生
`MRL_Bridge_MCP.exe`。

origin_signature: MrLiouWord
