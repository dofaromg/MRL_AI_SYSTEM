"""setup_dropbox_credential.py — 在 DL580 本機建立 Dropbox 憑證檔（憑證只存在 DL580，不經任何對話）
origin_signature: MrLiouWord ｜ 用法：D:\\MrlToolchain\\python\\python.exe setup_dropbox_credential.py
步驟：1) 輸入 Dropbox App 的 App key、App secret
      2) 用瀏覽器開啟顯示的網址、按允許，複製授權碼貼回來
      3) 自動換成長期 refresh_token，寫入 D:\\MRL_Mother\\private\\dropbox_app.json"""
import getpass, json, os, urllib.parse, urllib.request
from pathlib import Path
OUT = Path(r"D:\MRL_Mother\private\dropbox_app.json")
if OUT.exists():
    print("憑證檔已存在，不覆蓋：", OUT); raise SystemExit
key = input("App key: ").strip()
secret = getpass.getpass("App secret（輸入不顯示）: ").strip()
print("\n請用瀏覽器開啟並按「允許」：\nhttps://www.dropbox.com/oauth2/authorize?client_id=" + key + "&response_type=code&token_access_type=offline\n")
code = getpass.getpass("貼上授權碼（輸入不顯示）: ").strip()
data = urllib.parse.urlencode({"code": code, "grant_type": "authorization_code", "client_id": key, "client_secret": secret}).encode()
d = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.dropboxapi.com/oauth2/token", data=data), timeout=60).read())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"app_key": key, "app_secret": secret, "refresh_token": d["refresh_token"]}), encoding="utf-8")
print("完成：", OUT, "（refresh_token 長度", len(d["refresh_token"]), "）")
