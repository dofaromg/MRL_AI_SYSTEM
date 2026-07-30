/* mrl_mcp_main.c — MRL_Bridge_MCP entry: stdio JSON-RPC 2.0 loop.
 * origin_signature: MrLiouWord (LAW-0)
 *
 * MCP stdio transport: newline-delimited JSON-RPC 2.0, one message per line, UTF-8.
 * stdout carries ONLY MCP messages; all logging goes to stderr. stdin/stdout are set
 * to binary mode so Windows does not inject CR and break the client's line parser.
 */
#include "third_party/cjson/cJSON.h"
#include "MRL_mcp_jsonrpc.h"
#include "MRL_mcp_tools.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

static void log_err(const char *msg) { fprintf(stderr, "[MRL] %s\n", msg); fflush(stderr); }

/* Write one JSON message + newline to stdout, then flush. Frees msg. */
static void emit(char *msg) {
    if (!msg) return;
    fwrite(msg, 1, strlen(msg), stdout);
    fputc('\n', stdout);
    fflush(stdout);
    free(msg);
}

/* Read one newline-delimited line from stdin into a growable buffer.
 * Returns malloc'd line without the trailing newline, or NULL on EOF. */
static char *read_line(void) {
    size_t cap = 4096, len = 0;
    char *buf = (char *)malloc(cap);
    if (!buf) return NULL;
    int c;
    while ((c = getchar()) != EOF) {
        if (c == '\n') break;
        if (c == '\r') continue;           /* tolerate stray CR */
        if (len + 1 >= cap) {
            cap *= 2;
            char *nb = (char *)realloc(buf, cap);
            if (!nb) { free(buf); return NULL; }
            buf = nb;
        }
        buf[len++] = (char)c;
    }
    if (c == EOF && len == 0) { free(buf); return NULL; }
    buf[len] = '\0';
    return buf;
}

/* Dispatch one parsed request. Returns malloc'd response JSON, or NULL for
 * notifications (no reply). */
static char *handle(cJSON *req) {
    cJSON *method = cJSON_GetObjectItem(req, "method");
    cJSON *id     = cJSON_GetObjectItem(req, "id");
    const char *m = (method && cJSON_IsString(method)) ? method->valuestring : NULL;

    if (!m) return MRL_rpc_error(id, MRL_RPC_INVALID_REQUEST, "Missing method");

    /* Notifications (no id): consume silently, never reply. */
    if (strncmp(m, "notifications/", 14) == 0) return NULL;

    if (strcmp(m, "initialize") == 0) {
        const char *cv = NULL;
        cJSON *params = cJSON_GetObjectItem(req, "params");
        cJSON *pv = params ? cJSON_GetObjectItem(params, "protocolVersion") : NULL;
        if (pv && cJSON_IsString(pv)) cv = pv->valuestring;
        return MRL_build_initialize_result(id, cv);
    }
    if (strcmp(m, "ping") == 0) {
        /* Empty result object. */
        cJSON *r = cJSON_CreateObject();
        cJSON_AddStringToObject(r, "jsonrpc", "2.0");
        if (id) cJSON_AddItemToObject(r, "id", cJSON_Duplicate(id, 1));
        else    cJSON_AddNullToObject(r, "id");
        cJSON_AddObjectToObject(r, "result");
        char *s = cJSON_PrintUnformatted(r);
        cJSON_Delete(r);
        return s;
    }
    if (strcmp(m, "tools/list") == 0) {
        return MRL_tools_list(id);
    }
    if (strcmp(m, "tools/call") == 0) {
        cJSON *params = cJSON_GetObjectItem(req, "params");
        cJSON *nm = params ? cJSON_GetObjectItem(params, "name") : NULL;
        cJSON *args = params ? cJSON_GetObjectItem(params, "arguments") : NULL;
        const char *name = (nm && cJSON_IsString(nm)) ? nm->valuestring : NULL;
        if (!name) return MRL_rpc_error(id, MRL_RPC_INVALID_PARAMS, "Missing tool name");
        return MRL_tools_call(id, name, args);
    }

    return MRL_rpc_error(id, MRL_RPC_METHOD_NOT_FOUND, "Method not found");
}

int main(void) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    log_err("MRL_Bridge_MCP starting (origin_signature=MrLiouWord)");

    char *line;
    while ((line = read_line()) != NULL) {
        if (line[0] == '\0') { free(line); continue; }
        cJSON *req = cJSON_Parse(line);
        if (!req) {
            emit(MRL_rpc_error(NULL, MRL_RPC_PARSE_ERROR, "Parse error"));
            free(line);
            continue;
        }
        char *resp = handle(req);
        if (resp) emit(resp);   /* NULL => notification, no reply */
        cJSON_Delete(req);
        free(line);
    }
    log_err("MRL_Bridge_MCP stdin closed; exiting");
    return 0;
}
