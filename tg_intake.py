#!/usr/bin/env python3
"""Telegram intake (chạy trên GitHub Actions theo lịch).
Đọc tin nhắn mới gửi cho bot; với tin đầu tiên có link bài báo ->
  build_deck_from_url.py (Gemini) -> ci_build_video.py (render giọng clone + upload) -> báo link về Telegram.
Mỗi lần chạy xử lý 1 link (render lâu); link còn lại để lần chạy sau.
Lưu offset đã xử lý ở ci-state/tg-offset.txt (commit vào repo).
Env: TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, SOCIAL_UPLOAD_JSON, TTS_CONFIG_JSON, YT_CHANNEL_ID.
"""
import json, os, re, subprocess, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
STATE = REPO / "ci-state" / "tg-offset.txt"
URL_RE = re.compile(r"https?://[^\s]+")


def tg(method, **params):
    u = f"https://api.telegram.org/bot{TG}/{method}"
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(u, data=data), timeout=50) as r:
        return json.loads(r.read())


def send(chat, text):
    try:
        tg("sendMessage", chat_id=chat, text=text)
    except Exception as e:
        print("send fail:", e)


def git_commit(msg):
    subprocess.run(["git", "config", "user.name", "ci-bot"], cwd=str(REPO))
    subprocess.run(["git", "config", "user.email", "ci@kenvinzone.local"], cwd=str(REPO))
    subprocess.run(["git", "add", "-A"], cwd=str(REPO))
    subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO))
    subprocess.run(["git", "push"], cwd=str(REPO))


def read_offset():
    try:
        return int(STATE.read_text().strip())
    except Exception:
        return 0


def write_offset(v):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(v))


def main():
    if not TG:
        sys.exit("Thiếu TELEGRAM_BOT_TOKEN")
    offset = read_offset()
    upd = tg("getUpdates", offset=offset + 1, timeout=0)
    results = upd.get("result", [])
    if not results:
        print("Không có tin mới.")
        return
    jobs = []       # (update_id, chat, url, title)
    nonurl_max = offset
    for u in results:
        uid = u.get("update_id", 0)
        m = u.get("message") or u.get("edited_message") or {}
        chat = (m.get("chat") or {}).get("id")
        text = (m.get("text") or m.get("caption") or "").strip()
        urls = [x for x in URL_RE.findall(text) if "youtu" not in x and "youtube" not in x]
        if urls and chat:
            # tiêu đề ép: phần text không phải URL (nếu có), dạng "title: ..." hoặc dòng riêng
            title = ""
            rest = URL_RE.sub("", text).strip(" \n-|:")
            mt = re.search(r"(?:ti[êe]u ?đ[eề]|title)\s*[:\-]\s*(.+)", text, re.I)
            if mt:
                title = mt.group(1).strip()
            elif rest and len(rest) < 120:
                title = rest
            jobs.append((uid, chat, urls[0], title))
        else:
            nonurl_max = max(nonurl_max, uid)

    if "--check" in sys.argv:
        out = os.environ.get("GITHUB_OUTPUT")
        val = "true" if jobs else "false"
        if out:
            open(out, "a").write(f"has_job={val}\n")
        print("has_job=" + val)
        return

    if not jobs:
        write_offset(max(nonurl_max, max(u.get("update_id", 0) for u in results)))
        git_commit("tg: khong co link, bo qua tin chatter")
        print("Không có link bài trong tin mới.")
        return

    uid, chat, url, title = jobs[0]
    write_offset(uid)  # tiêu thụ tới job này; job sau để lần chạy kế
    git_commit(f"tg: nhan job update {uid}")
    send(chat, f"✅ Đã nhận link, đang dựng video (giọng clone + render + upload, ~15 phút):\n{url}")

    # 1) build deck (Gemini)
    cmd = [sys.executable, str(REPO / "build_deck_from_url.py"), "--url", url]
    if title:
        cmd += ["--title", title]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    print(r.stdout[-3000:]); print(r.stderr[-1500:])
    mproj = re.search(r"PROJECT=(\S+)", r.stdout)
    if r.returncode != 0 or not mproj:
        send(chat, f"❌ Lỗi khi dựng nội dung từ link. Thử lại hoặc kiểm tra link.\n{url}")
        sys.exit("build_deck failed")
    proj = mproj.group(1)
    git_commit(f"tg: deck {proj}")

    # 2) render + upload (giọng clone)
    r2 = subprocess.run([sys.executable, str(REPO / "ci_build_video.py"), f"slide/{proj}", "--privacy", "private"],
                        cwd=str(REPO))
    res_path = REPO / "upload-result.json"
    if r2.returncode == 0 and res_path.exists():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        send(chat, f"✅ Xong video [{proj}]:\n{res.get('url','')}\n(private — vào duyệt rồi chuyển public)")
    else:
        send(chat, f"⚠️ Dựng nội dung xong nhưng render/upload lỗi [{proj}]. Xem log repo.")
        sys.exit("render/upload failed")


if __name__ == "__main__":
    main()
