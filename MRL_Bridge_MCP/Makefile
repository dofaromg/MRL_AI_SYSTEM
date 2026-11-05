# Makefile — MRL_Bridge_MCP (MinGW-W64, Windows, stdio). origin_signature: MrLiouWord
# 需要：cJSON v1.7.19 已放進 third_party/cjson/（cJSON.c + cJSON.h）。
# 產物：MRL_Bridge_MCP.exe（純 C、-static、零非系統 DLL、-lwinhttp）。

CC      := D:/MrlToolchain/mingw64/mingw64/bin/gcc.exe
CFLAGS  := -O2 -Wall -Wextra -std=c11 -I.
LDFLAGS := -lwinhttp -static -s
SRC     := mrl_mcp_main.c mrl_mcp_jsonrpc.c mrl_mcp_tools.c mrl_http.c third_party/cjson/cJSON.c
OUT     := MRL_Bridge_MCP.exe

$(OUT): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(OUT) $(LDFLAGS)

.PHONY: clean smoke
clean:
	del /q $(OUT) 2>NUL || rm -f $(OUT)

# 無 Claude Desktop 的 headless 煙霧測試（PowerShell）：
#   Get-Content .\smoke.jsonl | .\MRL_Bridge_MCP.exe
smoke: $(OUT)
	@echo Run: Get-Content .\smoke.jsonl ^| .\MRL_Bridge_MCP.exe
