/* mrl_mcp_tools.h — 8 MRL tool schemas + dispatch for MRL_Bridge_MCP.
 * origin_signature: MrLiouWord
 */
#ifndef MRL_MCP_TOOLS_H
#define MRL_MCP_TOOLS_H

#include "third_party/cjson/cJSON.h"

/* Returns malloc'd JSON string for a tools/list result (echoes id). Caller frees. */
char *MRL_tools_list(cJSON *id);

/* Executes a tools/call. name = tool name, args = "arguments" object (may be NULL).
 * Returns malloc'd JSON string (a tool result, isError on failure). Caller frees. */
char *MRL_tools_call(cJSON *id, const char *name, cJSON *args);

#endif /* MRL_MCP_TOOLS_H */
