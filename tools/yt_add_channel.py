"""Lấy token OAuth YouTube cho MỘT kênh (vd @kenvinzone) → file JSON để dán vào GitHub Secret.

Chạy trên máy có trình duyệt (Windows/Mac), chỉ cần Python 3, không cài thêm gì:

    python yt_add_channel.py

Script sẽ:
  1. hỏi client_id + client_secret của OAuth client Google (Google Cloud Console → APIs & Services
     → Credentials → OAuth 2.0 Client IDs; dùng lại client đang dùng cho kênh cũ cũng được);
  2. mở trình duyệt → đăng nhập Google → CHỌN ĐÚNG KÊNH @kenvinzone → Cho phép;
  3. tự bắt mã trả về ở http://localhost:8765 (nếu không bắt được, dán URL thanh địa chỉ vào cửa sổ này);
  4. ghi file social-upload-kenvinzone.json cạnh script.

Sau đó: mở file, copy TOÀN BỘ nội dung → GitHub repo → Settings → Secrets and variables → Actions →
New repository secret, tên SOCIAL_UPLOAD_JSON_KZ. Xong thì XOÁ file JSON trên máy (chứa refresh token).
"""
from __future__ import annotations

import json
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

PORT = 8765
REDIRECT = f"http://localhost:{PORT}/api/social/youtube/callback"
SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
OUT = Path(__file__).resolve().parent / "social-upload-kenvinzone.json"

_got: dict = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        q = parse_qs(urlparse(self.path).query)
        if "code" in q or "error" in q:
            _got.update({k: v[0] for k, v in q.items()})
            msg = "Đã nhận mã. Quay lại cửa sổ dòng lệnh." if "code" in q else f"Lỗi: {q['error'][0]}"
        else:
            msg = "Đang chờ Google..."
        body = f"<html><meta charset='utf-8'><body style='font:20px sans-serif;padding:40px'>{msg}</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *a):
        pass


def _post(url: str, data: dict) -> dict:
    req = Request(url, data=urlencode(data).encode(), method="POST",
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        sys.exit(f"Google từ chối: HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")


def _channel(access_token: str) -> dict:
    req = Request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                  headers={"Authorization": f"Bearer {access_token}"})
    with urlopen(req, timeout=60) as r:
        items = json.loads(r.read().decode()).get("items") or []
    if not items:
        sys.exit("Tài khoản vừa chọn không có kênh YouTube. Chạy lại và chọn đúng kênh @kenvinzone.")
    it = items[0]
    sn = it.get("snippet") or {}
    return {"id": it["id"], "title": sn.get("title", ""),
            "thumbnail": ((sn.get("thumbnails") or {}).get("default") or {}).get("url", "")}


def main() -> None:
    print(__doc__.split("Sau đó:")[0])
    cid = input("client_id: ").strip()
    csec = input("client_secret: ").strip()
    if not cid or not csec:
        sys.exit("Thiếu client_id / client_secret.")
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent select_account", "state": state})

    server = None
    try:
        server = HTTPServer(("localhost", PORT), _Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except OSError:
        print(f"(Cổng {PORT} đang bận — sẽ cần dán URL bằng tay.)")

    print("\nĐang mở trình duyệt. Nếu không tự mở, copy link này:\n" + url + "\n")
    print(">>> Ở bước chọn tài khoản/kênh: CHỌN KÊNH @kenvinzone (không phải @kechuyen.chungkhoan). <<<\n")
    webbrowser.open(url)

    t0 = time.time()
    while server and not _got and time.time() - t0 < 300:
        time.sleep(0.5)
    if not _got:
        pasted = input("Dán URL trên thanh địa chỉ sau khi bấm Cho phép (bắt đầu bằng http://localhost...): ").strip()
        _got.update({k: v[0] for k, v in parse_qs(urlparse(pasted).query).items()})
    if server:
        server.shutdown()
    if _got.get("error"):
        sys.exit(f"Google báo lỗi: {_got['error']}")
    if _got.get("state") != state or not _got.get("code"):
        sys.exit("Mã không hợp lệ (state sai hoặc thiếu code). Chạy lại script.")

    tok = _post("https://oauth2.googleapis.com/token", {
        "code": _got["code"], "client_id": cid, "client_secret": csec,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"})
    if not tok.get("refresh_token"):
        sys.exit("Google không trả refresh_token. Vào https://myaccount.google.com/permissions gỡ quyền app rồi chạy lại.")
    ch = _channel(tok["access_token"])
    cfg = {"youtube": {
        "client_id": cid, "client_secret": csec, "redirect_uri": REDIRECT,
        "active_channel_id": ch["id"],
        "channels": [{**ch, "tokens": {
            "access_token": tok["access_token"], "refresh_token": tok["refresh_token"],
            "expires_at": time.time() + float(tok.get("expires_in") or 3600),
            "scope": tok.get("scope", SCOPE), "token_type": tok.get("token_type", "Bearer")}}]}}
    OUT.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Đã kết nối kênh: {ch['title']}  (id {ch['id']})")
    print(f"   File: {OUT}")
    print("   → Copy toàn bộ nội dung file vào GitHub Secret tên SOCIAL_UPLOAD_JSON_KZ.")
    print(f"   → (Tuỳ chọn) tạo secret KENVINZONE_YT_CHANNEL_ID = {ch['id']}")
    print("   → Xong thì xoá file này khỏi máy.")
    if "kechuyen" in ch["title"].lower():
        print("\n⚠️ Tên kênh có vẻ là @kechuyen.chungkhoan — có thể chọn nhầm kênh! Chạy lại và chọn @kenvinzone.")


if __name__ == "__main__":
    main()
