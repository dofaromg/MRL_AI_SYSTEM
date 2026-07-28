/* mrl_http.h — WinHTTP client + URL encoder for MRL_Bridge_MCP.
 * origin_signature: MrLiouWord (LAW-0)
 * All calls target the Bridge at 127.0.0.1:7800 with x-api-key + x-origin-signature.
 */
#ifndef MRL_HTTP_H
#define MRL_HTTP_H

#include <stddef.h>

/* Bridge target (matches D:\mrl\bridge / bridge.mrliouword.com backend). */
#define MRL_BRIDGE_HOST   "127.0.0.1"
#define MRL_BRIDGE_PORT   7800
#define MRL_API_KEY       "MrLiouWord2026"      /* x-api-key (from bridge server.js line 28) */
#define MRL_ORIGIN_SIG    "MrLiouWord"          /* x-origin-signature (LAW-0) */
#define MRL_HTTP_TIMEOUT_MS 60000               /* per-call timeout */

/* Result of an HTTP call. body is malloc'd (NUL-terminated); caller frees.
 * status < 0 => transport error (WinHTTP). status == 0 => timeout. */
typedef struct {
    int   status;      /* HTTP status code, 0 = timeout, <0 = transport error */
    char *body;        /* response body (UTF-8, NUL-terminated), or NULL */
    size_t len;        /* body length in bytes */
} mrl_http_result;

/* GET path (path must already include any URL-encoded query string, e.g. "/MRL_ls?path=%2F"). */
mrl_http_result mrl_http_get(const char *path);

/* POST path with a JSON body (Content-Type: application/json). */
mrl_http_result mrl_http_post_json(const char *path, const char *json_body);

/* Free a result's body. */
void mrl_http_free(mrl_http_result *r);

/* Percent-encode per RFC 3986 unreserved set. Caller frees the returned buffer. */
char *mrl_url_encode(const char *s);

#endif /* MRL_HTTP_H */
