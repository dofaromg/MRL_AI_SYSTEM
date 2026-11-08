// MRL_ASI_health_server.cjs — 7700 ASI Engine health server（參考副本）
// origin_signature: MrLiouWord
//
// 2026-07-06 實機修復：DL580 上 D:\mrl\asi-engine\server.js 原檔引號毀損
// （SyntaxError 啟動即死），以本零依賴版重寫（Node 內建 http，不需 express）。
// /health 回應契約維持原樣：{"status":"PASS","origin":"MrLiouWord"}
// 部署時若 D:\mrl\asi-engine\package.json 標 "type":"module"，
// 將 require 行改為 import * as http from "node:http"; 其餘相同。
const http = require("node:http");
const srv = http.createServer((req, res) => {
  if (req.method === "GET" && (req.url || "").split("?")[0] === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "PASS", origin: "MrLiouWord" }));
  } else {
    res.writeHead(404);
    res.end();
  }
});
srv.listen(7700, () => console.log("READY on 7700"));
