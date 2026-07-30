/* mrl_mcp_tools.c — 8 tools + dispatch to the MRL Bridge (127.0.0.1:7800).
 * origin_signature: MrLiouWord
 *
 * Bridge endpoint mapping (adjust the MRL_EP_* constants below to match your
 * bridge server.js routes if they differ):
 *   mrl_pg_query       POST /MRL_pg/query   body {sql, params}
 *   mrl_run            GET  /MRL_run?cmd=<enc>[&timeout_sec=N]
 *   mrl_cat            GET  /MRL_cat?path=<enc>
 *   mrl_write          GET  /MRL_write?path=<enc>&content=<enc>
 *   mrl_ls             GET  /MRL_ls?path=<enc>
 *   mrl_tables         GET  /MRL_tables
 *   mrl_sysinfo        GET  /MRL_sysinfo
 *   mrl_particle_stats 3x   POST /MRL_pg/query  (count of mrl_particle/persona/memory)
 *
 * Tool execution failures (bad args, Bridge non-200, timeout) => isError:true result,
 * NOT a JSON-RPC protocol error (MCP 2025-11-25 / SEP-1303).
 */
#include "MRL_mcp_tools.h"
#include "MRL_mcp_jsonrpc.h"
#include "MRL_http.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MRL_EP_PG_QUERY  "/MRL_pg/query"
#define MRL_EP_RUN       "/MRL_run"
#define MRL_EP_CAT       "/MRL_cat"
#define MRL_EP_WRITE     "/MRL_write"
#define MRL_EP_LS        "/MRL_ls"
#define MRL_EP_TABLES    "/MRL_tables"
#define MRL_EP_SYSINFO   "/MRL_sysinfo"

/* ---- tools/list ---------------------------------------------------------- */

static cJSON *obj_schema(void) {
    cJSON *s = cJSON_CreateObject();
    cJSON_AddStringToObject(s, "type", "object");
    cJSON_AddObjectToObject(s, "properties");
    return s;
}
static cJSON *prop_string(cJSON *props, const char *name, const char *desc) {
    cJSON *p = cJSON_AddObjectToObject(props, name);
    cJSON_AddStringToObject(p, "type", "string");
    cJSON_AddStringToObject(p, "description", desc);
    return p;
}
static void add_required(cJSON *schema, const char **names, int n) {
    cJSON *req = cJSON_AddArrayToObject(schema, "required");
    for (int i = 0; i < n; i++) cJSON_AddItemToArray(req, cJSON_CreateString(names[i]));
}
static cJSON *tool(const char *name, const char *desc, cJSON *schema) {
    cJSON *t = cJSON_CreateObject();
    cJSON_AddStringToObject(t, "name", name);
    cJSON_AddStringToObject(t, "description", desc);
    cJSON_AddItemToObject(t, "inputSchema", schema);
    return t;
}

char *MRL_tools_list(cJSON *id) {
    cJSON *r = cJSON_CreateObject();
    cJSON_AddStringToObject(r, "jsonrpc", "2.0");
    if (id) cJSON_AddItemToObject(r, "id", cJSON_Duplicate(id, 1));
    else    cJSON_AddNullToObject(r, "id");
    cJSON *res = cJSON_AddObjectToObject(r, "result");
    cJSON *tools = cJSON_AddArrayToObject(res, "tools");

    /* mrl_pg_query */
    {
        cJSON *s = obj_schema(), *props = cJSON_GetObjectItem(s, "properties");
        prop_string(props, "sql", "SQL statement to execute.");
        cJSON *pp = cJSON_AddObjectToObject(props, "params");
        cJSON_AddStringToObject(pp, "type", "array");
        cJSON_AddItemToObject(pp, "items", cJSON_CreateObject());
        cJSON_AddStringToObject(pp, "description", "Optional positional parameters.");
        const char *req[] = { "sql" }; add_required(s, req, 1);
        cJSON_AddItemToArray(tools, tool("mrl_pg_query",
            "Run a PostgreSQL query against the MRL database via the Bridge. Returns rows as JSON.", s));
    }
    /* mrl_run */
    {
        cJSON *s = obj_schema(), *props = cJSON_GetObjectItem(s, "properties");
        prop_string(props, "cmd", "Command line to execute.");
        cJSON *ts = cJSON_AddObjectToObject(props, "timeout_sec");
        cJSON_AddStringToObject(ts, "type", "integer");
        cJSON_AddStringToObject(ts, "description", "Optional timeout in seconds.");
        const char *req[] = { "cmd" }; add_required(s, req, 1);
        cJSON_AddItemToArray(tools, tool("mrl_run",
            "Execute a Windows command on the DL580 server via the Bridge and return stdout/stderr.", s));
    }
    /* mrl_cat */
    {
        cJSON *s = obj_schema(), *props = cJSON_GetObjectItem(s, "properties");
        prop_string(props, "path", "Absolute path of the file to read.");
        const char *req[] = { "path" }; add_required(s, req, 1);
        cJSON_AddItemToArray(tools, tool("mrl_cat",
            "Read the contents of a file on the DL580 server via the Bridge.", s));
    }
    /* mrl_write */
    {
        cJSON *s = obj_schema(), *props = cJSON_GetObjectItem(s, "properties");
        prop_string(props, "path", "Absolute path of the file to write.");
        prop_string(props, "content", "Text content to write.");
        const char *req[] = { "path", "content" }; add_required(s, req, 2);
        cJSON_AddItemToArray(tools, tool("mrl_write",
            "Write text content to a file on the DL580 server via the Bridge (content is URL-encoded).", s));
    }
    /* mrl_ls */
    {
        cJSON *s = obj_schema(), *props = cJSON_GetObjectItem(s, "properties");
        prop_string(props, "path", "Absolute directory path to list.");
        const char *req[] = { "path" }; add_required(s, req, 1);
        cJSON_AddItemToArray(tools, tool("mrl_ls",
            "List the contents of a directory on the DL580 server via the Bridge.", s));
    }
    /* mrl_tables */
    cJSON_AddItemToArray(tools, tool("mrl_tables",
        "List all tables in the MRL PostgreSQL database via the Bridge.", obj_schema()));
    /* mrl_sysinfo */
    cJSON_AddItemToArray(tools, tool("mrl_sysinfo",
        "Return system information about the DL580 server via the Bridge.", obj_schema()));
    /* mrl_particle_stats */
    cJSON_AddItemToArray(tools, tool("mrl_particle_stats",
        "Return combined row counts of mrl_particle, mrl_persona, and mrl_memory tables.", obj_schema()));

    char *out = cJSON_PrintUnformatted(r);
    cJSON_Delete(r);
    return out;
}

/* ---- helpers ------------------------------------------------------------- */

static const char *arg_str(cJSON *args, const char *key) {
    cJSON *v = args ? cJSON_GetObjectItem(args, key) : NULL;
    return (v && cJSON_IsString(v)) ? v->valuestring : NULL;
}

/* Build "/EP?key=enc(val)&..." — pairs is {k,v,k,v,...,NULL}. Caller frees. */
static char *build_query(const char *ep, const char **pairs) {
    size_t cap = strlen(ep) + 2, len;
    char *out = (char *)malloc(cap);
    if (!out) return NULL;
    strcpy(out, ep);
    len = strlen(out);
    int first = 1;
    for (int i = 0; pairs[i] != NULL; i += 2) {
        const char *k = pairs[i];
        const char *v = pairs[i + 1] ? pairs[i + 1] : "";
        char *ev = mrl_url_encode(v);
        if (!ev) { free(out); return NULL; }
        size_t add = strlen(k) + strlen(ev) + 2;
        char *nb = (char *)realloc(out, len + add + 1);
        if (!nb) { free(ev); free(out); return NULL; }
        out = nb;
        out[len++] = first ? '?' : '&';
        first = 0;
        memcpy(out + len, k, strlen(k)); len += strlen(k);
        out[len++] = '=';
        memcpy(out + len, ev, strlen(ev)); len += strlen(ev);
        out[len] = '\0';
        free(ev);
    }
    return out;
}

/* Turn an http result into a tool-result JSON string (isError on non-200/timeout). */
static char *result_from_http(cJSON *id, mrl_http_result *r) {
    char *out;
    if (r->status == 0) {
        out = MRL_tool_result(id, "Bridge timed out.", 1);
    } else if (r->status < 0) {
        out = MRL_tool_result(id, "Bridge transport error (WinHTTP).", 1);
    } else if (r->status < 200 || r->status >= 300) {
        char msg[256];
        snprintf(msg, sizeof(msg), "Bridge returned HTTP %d: %.180s",
                 r->status, r->body ? r->body : "");
        out = MRL_tool_result(id, msg, 1);
    } else {
        out = MRL_tool_result(id, r->body ? r->body : "", 0);
    }
    return out;
}

/* POST a pg query; return the scalar count from the first row, or -1. */
static long pg_count(const char *table) {
    cJSON *body = cJSON_CreateObject();
    char sql[128];
    snprintf(sql, sizeof(sql), "SELECT count(*) FROM %s", table);
    cJSON_AddStringToObject(body, "sql", sql);
    cJSON_AddItemToObject(body, "params", cJSON_CreateArray());
    char *bs = cJSON_PrintUnformatted(body);
    cJSON_Delete(body);

    mrl_http_result r = mrl_http_post_json(MRL_EP_PG_QUERY, bs);
    free(bs);
    long n = -1;
    if (r.status >= 200 && r.status < 300 && r.body) {
        cJSON *j = cJSON_Parse(r.body);
        if (j) {
            /* Accept {rows:[[N]]} or {rows:[{count:N}]} or [[N]] shapes. */
            cJSON *rows = cJSON_IsArray(j) ? j : cJSON_GetObjectItem(j, "rows");
            if (rows && cJSON_IsArray(rows)) {
                cJSON *row0 = cJSON_GetArrayItem(rows, 0);
                if (row0) {
                    cJSON *c = cJSON_IsArray(row0) ? cJSON_GetArrayItem(row0, 0)
                                                   : cJSON_GetObjectItem(row0, "count");
                    if (c) {
                        if (cJSON_IsNumber(c)) n = (long)c->valuedouble;
                        else if (cJSON_IsString(c)) n = atol(c->valuestring);
                    }
                }
            }
            cJSON_Delete(j);
        }
    }
    mrl_http_free(&r);
    return n;
}

/* ---- tools/call dispatch ------------------------------------------------- */

char *MRL_tools_call(cJSON *id, const char *name, cJSON *args) {
    if (!name) return MRL_tool_result(id, "Missing tool name.", 1);

    if (strcmp(name, "mrl_tables") == 0) {
        mrl_http_result r = mrl_http_get(MRL_EP_TABLES);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_sysinfo") == 0) {
        mrl_http_result r = mrl_http_get(MRL_EP_SYSINFO);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_pg_query") == 0) {
        const char *sql = arg_str(args, "sql");
        if (!sql) return MRL_tool_result(id, "mrl_pg_query requires 'sql'.", 1);
        cJSON *body = cJSON_CreateObject();
        cJSON_AddStringToObject(body, "sql", sql);
        cJSON *params = cJSON_GetObjectItem(args, "params");
        cJSON_AddItemToObject(body, "params",
            (params && cJSON_IsArray(params)) ? cJSON_Duplicate(params, 1) : cJSON_CreateArray());
        char *bs = cJSON_PrintUnformatted(body);
        cJSON_Delete(body);
        mrl_http_result r = mrl_http_post_json(MRL_EP_PG_QUERY, bs);
        free(bs);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_run") == 0) {
        const char *cmd = arg_str(args, "cmd");
        if (!cmd) return MRL_tool_result(id, "mrl_run requires 'cmd'.", 1);
        char tbuf[32]; const char *tsec = NULL;
        cJSON *t = args ? cJSON_GetObjectItem(args, "timeout_sec") : NULL;
        if (t && cJSON_IsNumber(t)) { snprintf(tbuf, sizeof(tbuf), "%d", (int)t->valuedouble); tsec = tbuf; }
        const char *pairs[] = { "cmd", cmd, tsec ? "timeout_sec" : NULL, tsec, NULL };
        char *path = build_query(MRL_EP_RUN, pairs);
        if (!path) return MRL_tool_result(id, "OOM building request.", 1);
        mrl_http_result r = mrl_http_get(path); free(path);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_cat") == 0) {
        const char *p = arg_str(args, "path");
        if (!p) return MRL_tool_result(id, "mrl_cat requires 'path'.", 1);
        const char *pairs[] = { "path", p, NULL };
        char *path = build_query(MRL_EP_CAT, pairs);
        if (!path) return MRL_tool_result(id, "OOM building request.", 1);
        mrl_http_result r = mrl_http_get(path); free(path);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_ls") == 0) {
        const char *p = arg_str(args, "path");
        if (!p) return MRL_tool_result(id, "mrl_ls requires 'path'.", 1);
        const char *pairs[] = { "path", p, NULL };
        char *path = build_query(MRL_EP_LS, pairs);
        if (!path) return MRL_tool_result(id, "OOM building request.", 1);
        mrl_http_result r = mrl_http_get(path); free(path);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_write") == 0) {
        const char *p = arg_str(args, "path");
        const char *c = arg_str(args, "content");
        if (!p || !c) return MRL_tool_result(id, "mrl_write requires 'path' and 'content'.", 1);
        const char *pairs[] = { "path", p, "content", c, NULL };
        char *path = build_query(MRL_EP_WRITE, pairs);
        if (!path) return MRL_tool_result(id, "OOM building request.", 1);
        mrl_http_result r = mrl_http_get(path); free(path);
        char *out = result_from_http(id, &r); mrl_http_free(&r); return out;
    }
    if (strcmp(name, "mrl_particle_stats") == 0) {
        long a = pg_count("mrl_particle"), b = pg_count("mrl_persona"), c = pg_count("mrl_memory");
        cJSON *o = cJSON_CreateObject();
        cJSON_AddNumberToObject(o, "mrl_particle", (double)a);
        cJSON_AddNumberToObject(o, "mrl_persona", (double)b);
        cJSON_AddNumberToObject(o, "mrl_memory", (double)c);
        cJSON_AddStringToObject(o, "x-origin-signature", "MrLiouWord");
        char *txt = cJSON_PrintUnformatted(o);
        cJSON_Delete(o);
        int err = (a < 0 || b < 0 || c < 0);
        char *out = MRL_tool_result(id, txt ? txt : "{}", err);
        free(txt);
        return out;
    }

    /* Unknown tool name is a tool error (model can self-correct), per SEP-1303. */
    {
        char msg[128];
        snprintf(msg, sizeof(msg), "Unknown tool: %.80s", name);
        return MRL_tool_result(id, msg, 1);
    }
}
