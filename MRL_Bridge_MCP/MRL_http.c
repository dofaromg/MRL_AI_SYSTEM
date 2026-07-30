/* mrl_http.c — WinHTTP client for MRL_Bridge_MCP. origin_signature: MrLiouWord
 * Native WinHTTP (winhttp.dll ships with Windows); link with -lwinhttp.
 * Every request carries x-api-key + x-origin-signature (LAW-0). Growable body reader.
 */
#include "MRL_http.h"

#include <windows.h>
#include <winhttp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

/* Percent-encode per RFC 3986 unreserved set (A-Z a-z 0-9 - _ . ~). Caller frees. */
char *mrl_url_encode(const char *s) {
    static const char hex[] = "0123456789ABCDEF";
    if (!s) s = "";
    size_t n = strlen(s);
    char *out = (char *)malloc(3 * n + 1), *p;
    if (!out) return NULL;
    p = out;
    for (size_t i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
            *p++ = (char)c;
        } else {
            *p++ = '%';
            *p++ = hex[c >> 4];
            *p++ = hex[c & 0xF];
        }
    }
    *p = '\0';
    return out;
}

/* Widen a UTF-8 C string to a freshly-allocated wide string. Caller frees. */
static wchar_t *widen(const char *s) {
    int need = MultiByteToWideChar(CP_UTF8, 0, s, -1, NULL, 0);
    if (need <= 0) return NULL;
    wchar_t *w = (wchar_t *)malloc((size_t)need * sizeof(wchar_t));
    if (!w) return NULL;
    MultiByteToWideChar(CP_UTF8, 0, s, -1, w, need);
    return w;
}

static mrl_http_result do_request(const wchar_t *verb, const char *path,
                                  const char *body, const char *content_type) {
    mrl_http_result R;
    R.status = -1; R.body = NULL; R.len = 0;

    HINTERNET hSession = NULL, hConnect = NULL, hRequest = NULL;
    wchar_t *wpath = NULL, *whost = NULL;
    BOOL ok = FALSE;

    hSession = WinHttpOpen(L"MRL_Bridge_MCP/1.0",
                           WINHTTP_ACCESS_TYPE_NO_PROXY,
                           WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) goto done;

    /* resolve/connect/send/receive timeouts (ms) */
    WinHttpSetTimeouts(hSession, MRL_HTTP_TIMEOUT_MS, MRL_HTTP_TIMEOUT_MS,
                       MRL_HTTP_TIMEOUT_MS, MRL_HTTP_TIMEOUT_MS);

    whost = widen(MRL_BRIDGE_HOST);
    if (!whost) goto done;
    hConnect = WinHttpConnect(hSession, whost, (INTERNET_PORT)MRL_BRIDGE_PORT, 0);
    if (!hConnect) goto done;

    wpath = widen(path);
    if (!wpath) goto done;

    hRequest = WinHttpOpenRequest(hConnect, verb, wpath, NULL,
                                  WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
    if (!hRequest) goto done;

    /* LAW-0 provenance + auth headers on every call. */
    {
        wchar_t *whdr = widen("x-api-key: " MRL_API_KEY "\r\n"
                              "x-origin-signature: " MRL_ORIGIN_SIG "\r\n");
        if (whdr) {
            WinHttpAddRequestHeaders(hRequest, whdr, (DWORD)-1, WINHTTP_ADDREQ_FLAG_ADD);
            free(whdr);
        }
    }
    if (content_type) {
        wchar_t *wct = widen(content_type);
        if (wct) {
            wchar_t hdr[128];
            _snwprintf(hdr, 127, L"Content-Type: %ls\r\n", wct);
            hdr[127] = 0;
            WinHttpAddRequestHeaders(hRequest, hdr, (DWORD)-1, WINHTTP_ADDREQ_FLAG_ADD);
            free(wct);
        }
    }

    ok = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                            (LPVOID)(body ? (void *)body : NULL),
                            (DWORD)(body ? strlen(body) : 0),
                            (DWORD)(body ? strlen(body) : 0), 0);
    if (!ok) { if (GetLastError() == ERROR_WINHTTP_TIMEOUT) R.status = 0; goto done; }

    ok = WinHttpReceiveResponse(hRequest, NULL);
    if (!ok) { if (GetLastError() == ERROR_WINHTTP_TIMEOUT) R.status = 0; goto done; }

    /* status code */
    {
        DWORD code = 0, sz = sizeof(code);
        WinHttpQueryHeaders(hRequest,
            WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
            WINHTTP_HEADER_NAME_BY_INDEX, &code, &sz, WINHTTP_NO_HEADER_INDEX);
        R.status = (int)code;
    }

    /* read body into a growable buffer */
    {
        size_t cap = 4096, len = 0;
        char *buf = (char *)malloc(cap);
        if (!buf) goto done;
        for (;;) {
            DWORD avail = 0;
            if (!WinHttpQueryDataAvailable(hRequest, &avail)) break;
            if (avail == 0) break;
            if (len + avail + 1 > cap) {
                while (len + avail + 1 > cap) cap *= 2;
                char *nb = (char *)realloc(buf, cap);
                if (!nb) { free(buf); buf = NULL; break; }
                buf = nb;
            }
            DWORD got = 0;
            if (!WinHttpReadData(hRequest, buf + len, avail, &got)) break;
            if (got == 0) break;
            len += got;
        }
        if (buf) { buf[len] = '\0'; R.body = buf; R.len = len; }
    }

done:
    if (hRequest) WinHttpCloseHandle(hRequest);
    if (hConnect) WinHttpCloseHandle(hConnect);
    if (hSession) WinHttpCloseHandle(hSession);
    free(wpath);
    free(whost);
    return R;
}

mrl_http_result mrl_http_get(const char *path) {
    return do_request(L"GET", path, NULL, NULL);
}

mrl_http_result mrl_http_post_json(const char *path, const char *json_body) {
    return do_request(L"POST", path, json_body ? json_body : "{}", "application/json");
}

void mrl_http_free(mrl_http_result *r) {
    if (r && r->body) { free(r->body); r->body = NULL; r->len = 0; }
}
