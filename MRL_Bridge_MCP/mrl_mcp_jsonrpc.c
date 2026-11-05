/* mrl_mcp_jsonrpc.c — JSON-RPC 2.0 builders for MRL_Bridge_MCP. origin_signature: MrLiouWord
 * Error/result builders follow the MRL_Bridge_MCP C Implementation Guide verbatim,
 * plus a protocolVersion-echoing initialize builder (forward-safe negotiation).
 */
#include "mrl_mcp_jsonrpc.h"
#include <string.h>

char *MRL_rpc_error(cJSON *id, int code, const char *msg) {
    cJSON *r = cJSON_CreateObject();
    cJSON_AddStringToObject(r, "jsonrpc", "2.0");
    if (id) cJSON_AddItemToObject(r, "id", cJSON_Duplicate(id, 1));
    else    cJSON_AddNullToObject(r, "id");
    cJSON *e = cJSON_AddObjectToObject(r, "error");
    cJSON_AddNumberToObject(e, "code", code);
    cJSON_AddStringToObject(e, "message", msg ? msg : "error");
    char *s = cJSON_PrintUnformatted(r);
    cJSON_Delete(r);
    return s;
}

char *MRL_tool_result(cJSON *id, const char *text, int is_error) {
    cJSON *r = cJSON_CreateObject();
    cJSON_AddStringToObject(r, "jsonrpc", "2.0");
    if (id) cJSON_AddItemToObject(r, "id", cJSON_Duplicate(id, 1));
    else    cJSON_AddNullToObject(r, "id");
    cJSON *res = cJSON_AddObjectToObject(r, "result");
    cJSON *arr = cJSON_AddArrayToObject(res, "content");
    cJSON *item = cJSON_CreateObject();
    cJSON_AddStringToObject(item, "type", "text");
    cJSON_AddStringToObject(item, "text", text ? text : "");  /* cJSON escapes for us */
    cJSON_AddItemToArray(arr, item);
    cJSON_AddBoolToObject(res, "isError", is_error ? 1 : 0);
    char *s = cJSON_PrintUnformatted(r);
    cJSON_Delete(r);
    return s;
}

char *MRL_build_initialize_result(cJSON *id, const char *client_ver) {
    static const char *allowed[] = {
        "2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"
    };
    const char *nego = "2025-11-25";  /* server latest / default */
    if (client_ver) {
        for (size_t i = 0; i < sizeof(allowed) / sizeof(allowed[0]); i++) {
            if (strcmp(client_ver, allowed[i]) == 0) { nego = client_ver; break; }
        }
    }
    cJSON *r = cJSON_CreateObject();
    cJSON_AddStringToObject(r, "jsonrpc", "2.0");
    if (id) cJSON_AddItemToObject(r, "id", cJSON_Duplicate(id, 1));
    else    cJSON_AddNullToObject(r, "id");
    cJSON *res = cJSON_AddObjectToObject(r, "result");
    cJSON_AddStringToObject(res, "protocolVersion", nego);
    /* tools-only server: advertise the tools capability. */
    cJSON *caps = cJSON_AddObjectToObject(res, "capabilities");
    cJSON_AddObjectToObject(caps, "tools");
    cJSON *info = cJSON_AddObjectToObject(res, "serverInfo");
    cJSON_AddStringToObject(info, "name", "MRL_Bridge_MCP");
    cJSON_AddStringToObject(info, "version", "1.0.0");
    cJSON_AddStringToObject(info, "x-origin-signature", "MrLiouWord");  /* LAW-0 provenance */
    char *s = cJSON_PrintUnformatted(r);
    cJSON_Delete(r);
    return s;
}
