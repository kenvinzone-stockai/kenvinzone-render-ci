# KenvinZone — Render & Upload tự động (cloud)

Render video HyperFrames **từng khung (mượt, 30fps)** và tự đăng YouTube, chạy
hoàn toàn trên **GitHub Actions** — không cần PC văn phòng bật.

Dùng lại nguyên các module của hệ thống gốc `escbase_template_main`:
`generate_tts.py`, `render_hyperframes.py`, `tts/`, `social_upload/`, `template/`.

## Cách hoạt động

1. Một **deck** được đặt ở `slide/<tên>/` gồm 4 file input:
   - `hf-data.json` — số liệu + nhãn + khoá `template` (giaima-tin-hf / vnindex-daily-hf / gold-daily-bias-hf / aurora-explainer-hf)
   - `script-90s.txt` — lời đọc (đúng số dòng của template)
   - `preview-settings.json` — nhạc nền, phụ đề, màu tiêu đề
   - `upload-metadata.json` — tiêu đề/mô tả/tag YouTube
   - (aurora) kèm `index.html` của tập
2. Chạy workflow → cloud sẽ: tạo giọng đọc (Gemini) → render HyperFrames → upload YouTube (private để duyệt).

## Chạy thủ công

Actions → **render-upload** → *Run workflow*:
- `project`: tên thư mục deck (vd `giai-ma-tin-tuc-quangtramctck-27-10`)
- `privacy`: `private` (nên để private để duyệt trước)
- `no_upload`: bật nếu chỉ muốn render thử

Video + log tải về ở mục **Artifacts** của lần chạy.

## Secrets cần đặt (Settings → Secrets and variables → Actions)

| Secret | Nội dung |
|---|---|
| `GEMINI_API_KEY` | Khoá Gemini TTS |
| `SOCIAL_UPLOAD_JSON` | Toàn bộ nội dung `config/social-upload.json` (client + channels + refresh_token) |
| `YT_CHANNEL_ID` | Id kênh YouTube muốn đăng (vd kênh "Kể Chuyện Chứng Khoán") |

Hai file `config/*.json` thật **không bao giờ commit** (xem `.gitignore`); chỉ
có file `*.example.json`. Khoá chỉ sống trong GitHub Secrets (mã hoá, không lộ ra log).

## Trigger từ xa (Telegram — giai đoạn sau)

Workflow nhận `repository_dispatch` loại `render-deck` với
`client_payload = {project, privacy, no_upload}`, để bot Telegram kích hoạt render từ điện thoại.

## Môi trường render

Node 22+, ffmpeg, Chromium (cài qua `playwright install --with-deps chromium`).
HyperFrames `0.8.210` tải qua `npx` lúc chạy.
