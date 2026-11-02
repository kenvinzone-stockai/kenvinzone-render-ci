#!/usr/bin/env python3
"""Telegram intake (chạy trên GitHub Actions theo lịch).

- Tin có LINK bài báo (không phải youtube) -> build_deck_from_url.py (Gemini)
  -> ci_build_video.py (render giọng clone + upload PRIVATE) -> gửi link + nhắc "duyệt".
- Tin "duyệt / công khai / public / lên sóng" -> chuyển video sang PUBLIC
  (video trong link nếu có, không thì video upload gần nhất ở ci-state/last-upload.json).

Thứ tự xử lý mỗi lần chạy: duyệt mọi tin duyệt ĐỨNG TRƯỚC tin render đầu tiên, rồi làm 1 render.
Các tin sau tin render để lần chạy kế (polling / dispatch).

Env: TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, SOCIAL_UPLOAD_JSON, TTS_CONFIG_JSON, YT_CHANNEL_ID.
"""
import json, os, re, subprocess, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
STATE = REPO / "ci-state" / "tg-offset.txt"
LASTUP = REPO / "ci-state" / "last-upload.json"
URL_RE = re.compile(r"https?://[^\s]+")
YTID_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|live/))([A-Za-z0-9_-]{6,})")
APPROVE_RE = re.compile(r"(duy[eệ]t|c[oô]ng\s*khai|public|l[eê]n\s*s[oó]ng|cho\s*l[eê]n)", re.I)


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
    subprocess.run(["git", "pull", "--rebase"], cwd=str(REPO))
    subprocess.run(["git", "push"], cwd=str(REPO))


def read_offset():
    try:
        return int(STATE.read_text().strip())
    except Exception:
        return 0


def write_offset(v):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(v))


def classify(text):
    """('render', url, title) | ('approve', video_id_or_'') | ('skip', '', '')."""
    t = (text or "").strip()
    if not t:
        return ("skip", "", "")
    article_urls = [x for x in URL_RE.findall(t) if "youtu" not in x]
    if article_urls:
        title = ""
        rest = URL_RE.sub("", t).strip(" \n-|:")
        mt = re.search(r"(?:ti[êe]u ?đ[eề]|title)\s*[:\-]\s*(.+)", t, re.I)
        if mt:
            title = mt.group(1).strip()
        elif rest and len(rest) < 120:
            title = rest
        return ("render", article_urls[0], title)
    if APPROVE_RE.search(t):
        m = YTID_RE.search(t)
        return ("approve", m.group(1) if m else "", "")
    return ("skip", "", "")


def _lastup():
    try:
        return json.loads(LASTUP.read_text(encoding="utf-8"))
    except Exception:
        return {}


def do_approve(chat, video_id):
    sys.path.insert(0, str(REPO))
    last = _lastup()
    if not video_id:
        video_id = last.get("video_id", "")
    if not video_id:
        send(chat, "⚠️ Chưa có video nào để công khai. Gửi link bài để dựng video trước đã.")
        return
    chan = last.get("channel_id", "") or os.environ.get("YT_CHANNEL_ID", "").strip()
    try:
        if chan:
            from social_upload.youtube import set_youtube_active_channel
            set_youtube_active_channel(chan)
        from social_upload.youtube import youtube_set_privacy
        res = youtube_set_privacy(video_id, "public")
        send(chat, f"✅ Đã CÔNG KHAI video:\n{res.get('url', 'https://youtu.be/' + video_id)}")
    except Exception as e:
        send(chat, f"❌ Không công khai được video {video_id}: {e}")
        print("approve fail:", e)


def do_render(chat, url, title):
    send(chat, f"✅ Đã nhận link, đang dựng video (giọng clone + render + upload Private, ~15 phút):\n{url}")
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
    r2 = subprocess.run([sys.executable, str(REPO / "ci_build_video.py"), f"slide/{proj}", "--privacy", "private"],
                        cwd=str(REPO))
    res_path = REPO / "upload-result.json"
    if r2.returncode == 0 and res_path.exists():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        vid = res.get("video_id", "")
        LASTUP.parent.mkdir(parents=True, exist_ok=True)
        LASTUP.write_text(json.dumps({"video_id": vid, "project": proj,
                                      "channel_id": os.environ.get("YT_CHANNEL_ID", "").strip(),
                                      "chat": chat}, ensure_ascii=False), encoding="utf-8")
        git_commit(f"tg: last-upload {proj} ({vid})")
        send(chat, f"✅ Xong video [{proj}] — đang để PRIVATE:\n{res.get('url', '')}\n\nXem xong, nhắn \"duyệt\" để công khai.")
    else:
        send(chat, f"⚠️ Dựng nội dung xong nhưng render/upload lỗi [{proj}]. Xem log repo.")
        sys.exit("render/upload failed")


def main():
    if not TG:
        sys.exit("Thiếu TELEGRAM_BOT_TOKEN")
    offset = read_offset()
    upd = tg("getUpdates", offset=offset + 1, timeout=0)
    results = sorted(upd.get("result", []), key=lambda u: u.get("update_id", 0))
    if not results:
        print("Không có tin mới.")
        return

    approvals = []   # (uid, chat, video_id)  — chỉ các tin ĐỨNG TRƯỚC render đầu tiên
    render = None    # (uid, chat, url, title)
    max_uid = offset
    for u in results:
        uid = u.get("update_id", 0)
        max_uid = max(max_uid, uid)
        m = u.get("message") or u.get("edited_message") or {}
        chat = (m.get("chat") or {}).get("id")
        text = (m.get("text") or m.get("caption") or "")
        c = classify(text)
        if c[0] == "render" and chat:
            render = (uid, chat, c[1], c[2])
            break  # dừng tại render đầu tiên; tin sau để lần chạy kế
        elif c[0] == "approve" and chat:
            approvals.append((uid, chat, c[1]))

    if "--check" in sys.argv:
        out = os.environ.get("GITHUB_OUTPUT")
        hj = "true" if render else "false"
        ha = "true" if (render or approvals) else "false"
        if out:
            open(out, "a").write(f"has_job={hj}\nhas_action={ha}\n")
        print(f"has_job={hj} has_action={ha}")
        return

    for uid, chat, vid in approvals:
        do_approve(chat, vid)

    if render:
        uid, chat, url, title = render
        write_offset(uid)  # tiêu thụ tới tin render (các tin duyệt trước đó cũng xong)
        git_commit(f"tg: nhan job update {uid}")
        do_render(chat, url, title)
    else:
        write_offset(max_uid)  # không có render: đã xử lý hết (duyệt + chatter)
        git_commit("tg: xu ly duyet / bo qua chatter")


if __name__ == "__main__":
    main()
