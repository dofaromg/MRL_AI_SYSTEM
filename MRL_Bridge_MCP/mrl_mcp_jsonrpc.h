/* mrl_mcp_jsonrpc.h — JSON-RPC 2.0 helpers for MRL_Bridge_MCP.
 * origin_signature: MrLiouWord
 */
#ifndef MRL_MCP_JSONRPC_H
#define MRL_MCP_JSONRPC_H

#include "third_party/cjson/cJSON.h"

/* JSON-RPC error codes. */
#define MRL_RPC_PARSE_ERROR      -32700
#define MRL_RPC_INVALID_REQUEST  -32600
#define MRL_RPC_METHOD_NOT_FOUND -32601
#define MRL_RPC_INVALID_PARAMS   -32602
#define MRL_RPC_INTERNAL_ERROR   -32603

/* All return a malloc'd, unformatted JSON string (caller frees) — one MCP message. */

/* Protocol-level error object (bad JSON, unknown method, ...). id may be NULL. */
char *MRL_rpc_error(cJSON *id, int code, const char *msg);

/* Successful tool result: { result: { content:[{type:text,text}], isError } }.
 * Per MCP 2025-11-25 (SEP-1303): tool execution/validation failures use isError:true,
 * NOT a protocol error. */
char *MRL_tool_result(cJSON *id, const char *text, int is_error);

/* initialize result echoing the client's protocolVersion if in the allow-list,
 * else the server's latest ("2025-11-25"). */
char *MRL_build_initialize_result(cJSON *id, const char *client_ver);

#endif /* MRL_MCP_JSONRPC_H */
