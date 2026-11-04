# QUY TRÌNH CHUẨN — HỆ THỐNG TỰ ĐỘNG SẢN XUẤT VIDEO KENVINZONE

> Tài liệu gốc để **vận hành, bảo trì và NHÂN BẢN** pipeline tạo video tự động cho bất kỳ loại nội dung nào.
> Mọi thứ chạy **trên đám mây (GitHub Actions)** — KHÔNG phụ thuộc PC văn phòng.
>
> Phiên bản: 2026-11 · Repo: `kenvinzone-stockai/kenvinzone-render-ci`
> Đi kèm bộ khung mẫu tại `docs/scaffold/` (copy-đổi-tên là có pipeline mới).

---

## 0. ĐỌC NHANH (TL;DR)

Một "bản tin video" được sinh ra qua đúng **4 chặng**:

```
   TRIGGER                BRAIN (Gemini)            BUILD VIDEO                 PHÂN PHỐI
(hẹn giờ / gửi link)  →  (viết kịch bản + deck)  →  (TTS giọng clone →       →  (upload YouTube
 Apps Script /            build_*_deck.py /          render HyperFrames)         Private → báo
 Telegram / tay          build_deck_from_url.py      ci_build_video.py           Telegram → "duyệt")
```

- **Chặng 1 — Trigger:** quyết định KHI NÀO chạy và với dữ liệu gì. Dùng Apps Script (hẹn giờ) hoặc bot Telegram (gửi link) hoặc bấm tay.
- **Chặng 2 — Brain:** biến dữ liệu thô (bài báo / số liệu) thành một **deck** chuẩn: `hf-data.json` + `script-90s.txt` + metadata. Có **validator** tự kiểm; sai thì nhờ Gemini sửa tới 3 lượt.
- **Chặng 3 — Build video:** `ci_build_video.py` đọc deck → tạo **giọng đọc clone** (TTS) → **render HyperFrames** từng khung 30fps → ra `final_video.mp4`.
- **Chặng 4 — Phân phối:** upload YouTube ở chế độ **Private**, báo link qua Telegram; xem xong nhắn **"duyệt"** để công khai.

Muốn làm **nội dung mới**? → nhảy xuống [Mục 6 — QUY TRÌNH NHÂN BẢN 7 BƯỚC](#6-quy-trình-nhân-bản-cho-nội-dung-mới-7-bước).

---

## 1. TRIẾT LÝ THIẾT KẾ (vì sao làm như vậy)

| Nguyên tắc | Lý do |
|---|---|
| **Chạy 100% trên GitHub Actions** | Repo public → CI **miễn phí**. Không cần PC nhà/văn phòng bật 24/7. Trigger từ điện thoại cũng được. |
| **Tách bạch "số liệu" và "kể chuyện"** | Số liệu lấy **tất định** từ nguồn (JSON/bài báo); Gemini chỉ viết lời. Giảm sai số, giảm bịa số. |
| **Mọi deck theo một "hợp đồng dữ liệu" chung** (`hf-data.json`) | Một bộ máy render dùng chung cho mọi template. Thêm nội dung = thêm template, KHÔNG viết lại render. |
| **Validator chặn lỗi trước khi tốn tiền render** | Sai cấu trúc/quá dài → loại ở bước brain (rẻ), không để lọt tới TTS/render (tốn credit + phút CI). |
| **Giọng đọc = giọng clone của anh** | Lấy từ `config/tts.json` (Gemini TTS auto-clone). Thương hiệu nhất quán. |
| **Log commit vào repo** | Proxy thiết bị chặn tải log Actions. Nên log được **ghi thẳng vào `ci-logs/`** để đọc lại bằng git. |
| **Luôn upload Private trước** | Người thật xem và "duyệt" mới công khai → không bao giờ lỡ đăng bài sai. |

---

## 2. BẢN ĐỒ HỆ THỐNG (repo, secrets, file)

### 2.1. Hai repo

| Repo | Vai trò | Public? |
|---|---|---|
| `kenvinzone-stockai/kenvinzone-render-ci` | **Bộ máy** — toàn bộ brain, template, render, workflow, trigger | ✅ (để CI free) |
| `kenvinzone-stockai/kenvinzone-bias-web` | **Nguồn số liệu** — `data/latest.json` (điểm Bias các tài sản) · site `bias.kenvinzone.com` | ✅ |

### 2.2. Secrets (GitHub → Settings → Secrets and variables → Actions)

| Secret | Dùng cho | Ghi chú |
|---|---|---|
| `GEMINI_API_KEY` | Brain (viết kịch bản) + TTS giọng clone | Gemini trả phí theo credit trả trước |
| `TTS_CONFIG_JSON` | Toàn bộ `config/tts.json` | giọng clone + style preset + api_key |
| `SOCIAL_UPLOAD_JSON` | Toàn bộ `config/social-upload.json` | client + channels + **refresh_token** YouTube |
| `YT_CHANNEL_ID` | Kênh YouTube mặc định | |
| `GOLD_YT_CHANNEL_ID`, `EQUITY_YT_CHANNEL_ID`, `INTERMARKET_YT_CHANNEL_ID` | (tùy chọn) kênh riêng từng loại | fallback về `YT_CHANNEL_ID` nếu trống |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Bot báo trạng thái + nhận link | |

> Secret được **tái tạo thành file** lúc chạy: `restore_tts_config()` và `restore_social_config()` trong `ci_build_video.py` ghi ra `config/tts.json` / `config/social-upload.json` (chmod 600).

### 2.3. Bản đồ file quan trọng

```
kenvinzone-render-ci/
├── build_deck_from_url.py     # BRAIN kiểu 1: 1 link bài báo → deck (tin tức)
├── build_gold_deck.py         # BRAIN kiểu 2: số liệu latest.json → deck (Vàng)
├── build_equity_deck.py       # BRAIN kiểu 2: S&P500 + Nasdaq
├── build_intermarket_deck.py  # BRAIN kiểu 2: liên thị trường (tổng hợp 3 tài sản)
├── build_vnindex_deck.py      # BRAIN kiểu 2: VNINDEX
├── check_deck_cloud.py        # VALIDATOR: kiểm deck đạt chuẩn chưa
├── ci_build_video.py          # ORCHESTRATOR: TTS → render → upload (dùng chung)
├── generate_tts.py            # tạo giọng đọc (clone) + timing.json
├── render_hyperframes.py      # render video từng khung 30fps
├── tg_intake.py               # bot Telegram: nhận link / "duyệt" → gọi pipeline
├── pronunciation.json         # từ điển phát âm cho TTS (KenvinZone…) — chỉ sửa giọng, không đổi chữ
├── config/
│   ├── tts.json               # (tái tạo từ secret) giọng clone + style
│   └── social-upload.json     # (tái tạo từ secret) YouTube oauth
├── template/
│   ├── giaima-tin-hf/build.py        # template tin tức (9 cảnh s0..s8)
│   ├── gold-daily-bias-hf/build.py   # template Vàng
│   ├── equity-bias-hf/build.py       # template S&P500+Nasdaq
│   ├── intermarket-weekly-hf/build.py
│   └── vnindex-daily-hf/build.py
├── slide/<project>/           # MỘT DECK đã dựng (đầu ra của brain, đầu vào của render)
│   ├── hf-data.json           #   dữ liệu hiển thị (hợp đồng dữ liệu)
│   ├── script-90s.txt         #   9 dòng lời đọc
│   ├── upload-metadata.json   #   tiêu đề/mô tả/tag YouTube
│   ├── preview-settings.json  #   nhạc nền, phụ đề…
│   ├── source/source.md       #   dẫn nguồn
│   └── output/                #   final_video.mp4, voiceover_concat.mp3, timing.json (sinh ra khi render)
├── .github/workflows/
│   ├── build-deck.yml         # chạy RIÊNG brain (không render) — để TEST/CHẨN LỖI rẻ
│   ├── render-upload.yml      # render + upload một deck có sẵn
│   ├── tg-intake.yml          # poll Telegram mỗi 30' (7,37 * * * *)
│   ├── gold-build.yml / equity-build.yml / intermarket-build.yml / vnindex-build.yml
│   └── ...
├── ci-logs/                   # log các lần chạy (đọc được bằng git — proxy chặn tải log Actions)
└── docs/
    ├── QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md   # (tài liệu này)
    └── scaffold/              # BỘ KHUNG MẪU để nhân bản
```

---

## 3. HỢP ĐỒNG DỮ LIỆU — `hf-data.json` (xương sống của mọi deck)

Đây là thứ **gắn kết brain ↔ template ↔ render**. Mọi template đọc cùng cấu trúc; brain nào cũng phải sinh ra đúng cấu trúc này.

```jsonc
{
  "template": "giaima-tin-hf",          // tên thư mục template dưới template/
  "date": "04/11/2026",                 // DD/MM/YYYY — phải khớp đuôi ngày của tên project
  "handle": "@kechuyen.chungkhoan",
  "audio_offset": 1.0,                  // giây lặng đầu video
  "outro_hold": 3.6,                    // giây giữ cảnh cuối
  "source": { "site":"CafeF","short":"CafeF","author":"…","headline":"…","date":"…","url":"…" },
  "hook":   { "eyebrow":"Chuyện Chứng Khoán",
              "title_lines":["dòng 1 ≤20 ký tự","dòng 2 ≤20 ký tự"],  // TIÊU ĐỀ COVER
              "sub":"1 câu phụ", "chips":[{"icon":"↘","text":"…","tone":"down"}, …3 chip…] },
  "s1": { … }, "s2": { … }, … "s7": { … },   // nội dung từng cảnh (tùy template)
  "outro": { "tag":"…","closing":"…","cta":"…" }
}
```

Hai file đi kèm:

- **`script-90s.txt`** — lời đọc, **đúng 9 dòng**. Số câu mỗi dòng (tách bằng `.?!`) phải đúng `[1,3,3,3,4,4,3,3,3]`. Số trong lời đọc **viết thành chữ** ("bốn mươi hai phần trăm") để TTS đọc đúng; nhưng số hiển thị trên slide để nguyên chữ số.
- **`upload-metadata.json`** — `youtube.title` (≤100 ký tự, mở đầu `[Giải mã]`…), `description` (có link nguồn + câu "không phải khuyến nghị đầu tư"), `tags`, `privacyStatus`.

> **Quy tắc đặt tên project:** `slide/giai-ma-tin-tuc-<slug>-<DD>-<MM>/` (tin) hoặc `slide/<loại>-<DDMMYYYY>/` (dữ liệu). Đuôi ngày phải khớp `hf-data.date`, nếu không validator báo lệch.

---

## 4. HAI KIỂU "BỘ NÃO" (chọn đúng kiểu trước khi làm)

### 4.1. Kiểu A — TIN TỪ LINK (`build_deck_from_url.py`)

Dành cho: **1 bài báo** → video giải mã. Gemini đọc bài rồi **viết toàn bộ deck**.

Luồng: `fetch_article(url)` (rút tag HTML, lấy ~12k ký tự) → `resolve_model()` chọn model Flash → vòng lặp **tối đa 3 lượt**: `gemini(SPEC, prompt)` → `json.loads` → `assemble()` ghi deck → `check_deck_cloud.py`. Lượt sau nhận phản hồi lỗi của lượt trước để **tự sửa**. In `PROJECT=<tên>` ở dòng cuối cho workflow.

Điểm mấu chốt đã tinh chỉnh (đừng bỏ):
- `gemini()` **tự thử lại** khi timeout/nghẽn mạng/HTTP 429/5xx (không để 1 cú chậm làm sập cả tiến trình).
- `maxOutputTokens = 16384` để deck dài không bị cắt cụt JSON.
- Khi lỗi "QUÁ DÀI", prompt lượt sau **ép cắt định lượng** (mục tiêu ~500–540 từ).
- `normalize_names()`: lưới an toàn đổi phiên âm tiếng Việt về chuẩn Anh (Dow Jones, Nasdaq, S&P 500, VN-Index, KenvinZone).

### 4.2. Kiểu B — DỮ LIỆU ĐỊNH LƯỢNG (`build_gold_deck.py`, `build_equity_deck.py`, …)

Dành cho: **báo cáo số liệu định kỳ** (điểm Bias, Gamma, 6 lực kéo…). Số liệu lấy **TẤT ĐỊNH** từ `latest.json`; **Gemini chỉ viết phần kể chuyện** (kịch bản, nhãn đọc, mô tả). An toàn hơn kiểu A vì số không do AI bịa.

Mẫu: đọc `--data latest.json`, lấy `assets.<TÀI SẢN>.<daily|weekly>` (score, regime, categories[].contribution, gamma…) → map sang các khối template (ví dụ `FORCE_MAP` 6 lực kéo, màu theo dấu âm/dương) → gọi `gemini()` **chỉ cho phần chữ** → `assemble()` → in `PROJECT=`. Hỗ trợ `--frame daily|weekly`.

> Hai kiểu **dùng chung** `gemini()`, `resolve_model()`, `normalize_names()` (import từ `build_deck_from_url.py`) và **chung** `ci_build_video.py` + `check_deck_cloud.py`.

---

## 5. BỘ MÁY DỰNG VIDEO (dùng chung cho mọi nội dung)

### 5.1. `ci_build_video.py` — nhạc trưởng

```
python ci_build_video.py slide/<project> [--privacy private|unlisted|public] [--no-upload] [--engine gemini]
```

Các bước: (1) tái tạo `config/tts.json` + `config/social-upload.json` từ secret → (2) áp `pronunciation.json` vào **bản text gửi TTS**, chạy `generate_tts.py` (ra `output/voiceover_concat.mp3` + `output/timing.json`), rồi **khôi phục** script gốc + sửa `timing.json` về nguyên bản (để phụ đề hiển thị đúng "KenvinZone" dù TTS đọc theo phiên âm) → (3) `render_hyperframes.py` render 30fps ra `output/final_video.mp4` → (4) upload YouTube (`social_upload.youtube`), ghi `upload-result.json`.

`STYLE_PRESET` trong file này ánh xạ **template → preset giọng** (ví dụ `giaima-tin-hf → giai-ma-nganh`, `vnindex-daily-hf → ban-tin-vnindex`). **Thêm template mới nhớ thêm 1 dòng vào đây.**

### 5.2. Template HyperFrames — `template/<name>-hf/build.py`

Mỗi template là một `build.py` sinh ra **các cảnh** (`s0`…`s8` + `captions`) dưới dạng **HTML tự chứa**, mỗi cảnh có **timeline GSAP riêng**. Khung hình dọc **1080×1920**.

**LUẬT VÀNG về animation (sai là hình đứng im):** mỗi cảnh chạy timeline **tương đối theo mốc bắt đầu cảnh**. Dùng helper kiểu:

```python
def tline(line, frac, base=0.0):
    s, d = BEATS[line]          # thời điểm & độ dài câu 'line' trong lời đọc
    return round(s + frac*d + OFF - base, 3)   # TRỪ base = start của cảnh → ra thời gian NỘI BỘ cảnh
# Trong mỗi cảnh: truyền base = st (start của cảnh). Quên trừ base → animation nằm ngoài cửa sổ hiển thị → "đứng hình".
```

Các chuẩn trong template (giữ nguyên để đồng bộ toàn kênh):
- **Phụ đề trong vùng an toàn** (ví dụ `top ≤ 1205px`) — không để chìm khỏi khung người xem.
- **Hiệu ứng số học**: đếm số (counter), thanh nhiệt/kim đồng hồ chạy rồi dừng (VU-meter sweep), scale-punch khi chốt — tạo cảm giác "sống".
- **SFX** theo sự kiện: tick ở mỗi số, impact khi chốt điểm/score.
- **Tiêu đề cover** (`s0`): cỡ chữ có sàn tối thiểu + `white-space:nowrap` (không xuống hàng), khung cách dòng phụ đề đủ rộng (không chèn lên viền).
- **Reveal theo câu**: mỗi khối hiện đúng vào câu lời đọc tương ứng (dùng `beat` trong data + `tline`).

### 5.3. `check_deck_cloud.py` — validator (chuẩn chất lượng dạng mã)

Trả 0 = ĐẠT, 1 = CHƯA ĐẠT. Các luật **cứng** (fail):
- `script-90s.txt` đúng **9 dòng**, số câu/dòng = `[1,3,3,3,4,4,3,3,3]`.
- **≤ 720 từ** (hiệu chỉnh thực đo: 619 từ = 152 giây ⇒ 720 từ ≈ 2:56, **đảm bảo < 3 phút Shorts**). Cảnh báo mềm khi > 680.
- Không chứa **từ cấm** (xem Mục 7).
- `hf-data.json` đủ khóa; `template` đúng; `date` khớp tên thư mục; `hook.title_lines` = 2; `hook.chips` = 3; `s5.lights` đúng green/yellow/red; `source` có site + headline.
- `upload-metadata`: title ≤100, mô tả có "khuyến nghị" (câu disclaimer).

---

## 6. QUY TRÌNH NHÂN BẢN CHO NỘI DUNG MỚI (7 BƯỚC)

> Dùng bộ khung tại `docs/scaffold/`. Xem `docs/scaffold/CHECKLIST-NHAN-BAN.md` để tick từng việc.

**Bước 1 — Xác định nội dung & nguồn.** Trả lời: nguồn là **1 link bài** (→ Kiểu A) hay **số liệu/JSON định kỳ** (→ Kiểu B)? Nhịp đăng (ngày/tuần/theo sự kiện)? Kênh YouTube nào? Đặt tên loại, ví dụ `crypto-daily`.

**Bước 2 — Thiết kế "hợp đồng dữ liệu".** Liệt kê các cảnh (thường 9) và **mỗi cảnh cần số/nội dung gì**. Viết ra `hf-data.schema` của riêng loại này (tham khảo `docs/scaffold/hf-data.schema.json`).

**Bước 3 — Viết BRAIN.** Copy `brain_tin_tuc.template.py` (Kiểu A) hoặc `brain_du_lieu.template.py` (Kiểu B). Sửa: `SPEC` (prompt + schema), hàm map số liệu (Kiểu B), tên template, quy tắc đặt tên project. Tái dùng `gemini/resolve_model/normalize_names`.

**Bước 4 — Tạo TEMPLATE HyperFrames.** Copy thư mục `template/<gần-giống-nhất>-hf/` → `template/<loại-mới>-hf/`. Sửa các cảnh trong `build.py` (giữ **LUẬT VÀNG `tline` + base**, vùng an toàn phụ đề, SFX). **Thêm 1 dòng vào `STYLE_PRESET`** trong `ci_build_video.py`.

**Bước 5 — Luật chất lượng.** Tái dùng `check_deck_cloud.py` nếu cấu trúc 9 cảnh giống; nếu khác, thêm/sửa luật cho đúng cảnh mới. Nhớ giữ **ngưỡng ≤720 từ** và **từ cấm**.

**Bước 6 — Tạo WORKFLOW.** Copy `docs/scaffold/workflow_build.yml.template` → `.github/workflows/<loại>-build.yml`. Sửa: tên, `repository_dispatch` types, lệnh brain (`--frame`/`--data`/`--url`), secret kênh YouTube. Giữ bước **commit log** + **báo Telegram** + **artifact**.

**Bước 7 — Tạo TRIGGER + KIỂM THỬ RẺ.**
1. Thêm hàm vào Apps Script (copy `apps_script_trigger.gs.template`) bắn `repository_dispatch` đúng type; đặt Time-driven trigger; thêm **chống trùng theo ngày** + **bỏ cuối tuần** nếu là tin ngày.
2. **TEST bằng `build-deck.yml`** (chỉ brain, gần như không tốn tiền) để chắc deck ĐẠT.
3. **Xem hình bằng screenshot container** (Playwright, **zero credit Gemini**) trước khi render thật.
4. Khi deck + hình OK → chạy `render-upload.yml` (Private) **một** video thật để nghiệm thu.

---

## 7. QUY TẮC BẤT BIẾN (chuẩn chất lượng toàn kênh — luôn áp)

1. **Video "Giải Mã"/Chuyện Chứng Khoán < 3 phút** (Shorts). Ngưỡng cứng **≤ 720 từ** (đo thực: 619 từ = 152 giây).
2. **Giữ nguyên văn tiêu đề** khi anh đưa sẵn — không rút gọn, không bỏ chữ (kể cả "Cổ phiếu").
3. **Tiêu đề cover + hook phải rõ ràng, nói thẳng sự việc** — không ẩn dụ khó hiểu (cover là khung hình đầu).
4. **Thuật ngữ/chỉ số tiếng Anh viết chuẩn quốc tế** trên slide: Dow Jones, S&P 500, Nasdaq, VN-Index — **không phiên âm** ("Đao Giôn", "Ét pi"). TTS đọc tiếng Anh tốt nên để nguyên.
5. **"KenvinZone" phải được TTS đọc đúng** (dùng `pronunciation.json`); chữ hiển thị luôn là "KenvinZone".
6. **VNINDEX đăng thứ Sáu** → hẹn bản tin **thứ Hai**, không nói "ngày mai" (T7/CN nghỉ).
7. **Tin ngày (Vàng/Chứng Mỹ) bỏ Thứ 7 & Chủ Nhật** (thị trường đóng) — chặn ở Apps Script `isWeekendICT()`.
8. **Phụ đề trong vùng an toàn**; **animation theo mốc cảnh** (`tline` trừ base).
9. **Luôn upload Private** → người duyệt → mới public.
10. **Từ cấm** trong lời đọc: "thao túng", "mua ngay", "bán ngay", "chắc chắn tăng/giảm", "cam kết lãi", "x2/x3 tài khoản", "làm giàu nhanh", "bí mật nội bộ", "all in", "lãi đảm bảo". Giọng luôn là "góc nhìn tham khảo", KHÔNG phải khuyến nghị đầu tư.

---

## 8. VẬN HÀNH HẰNG NGÀY

- **Đăng 1 bài tin bất kỳ:** gửi link bài vào bot Telegram → tự dựng (Private) → báo link → nhắn **"duyệt"** để công khai.
- **Chạy tay 1 loại:** GitHub → Actions → chọn workflow (`gold-build`…) → *Run workflow* → chọn `frame`/nhập ngày.
- **Lịch tự động:** do **Apps Script** (Google) bắn `repository_dispatch` đúng giờ ICT (KHÔNG dùng cron GitHub vì hay trễ). Mỗi loại có chống trùng theo ngày.
- **Xem log khi lỗi:** proxy chặn tải log Actions → đọc file trong **`ci-logs/`** (đã commit vào repo): `git pull` rồi mở `ci-logs/<loại>-brain-*.log` / `*-run-*.log`.

---

## 9. CHẨN LỖI & CHI PHÍ (bài học thực chiến)

### 9.1. Cách chẩn lỗi RẺ (không đốt credit)
- **`build-deck.yml`** chạy **chỉ bước brain** (không render/không TTS) và **luôn commit `ci-logs/brain-<id>.log`** kể cả khi lỗi → đây là nơi đọc lỗi thật. Kích hoạt qua Actions UI hoặc API `workflow_dispatch` với input `url`.
- **Screenshot bằng Playwright trong container** (Node + Chromium có sẵn) để soi bố cục/khung hình **không tốn Gemini**. Dùng `timeline.seek(t)` để xem đúng khoảnh khắc.
- **Đừng render hàng loạt để test** — mỗi video thật tốn TTS. Chỉ render thật khi deck + hình đã OK.

### 9.2. Các lỗi đã gặp & cách hệ thống xử lý
| Triệu chứng | Nguyên nhân | Đã xử lý |
|---|---|---|
| "Lỗi khi dựng nội dung từ link" | Script quá dài (tin dày) vượt ngưỡng từ | Ép cắt định lượng + nâng ngưỡng 670→**720** (đo thực) |
| Tiến trình sập giữa chừng | Gemini **timeout/nghẽn** | `gemini()` tự **thử lại** (timeout/429/5xx) |
| JSON không hợp lệ (cắt cụt) | Tràn `maxOutputTokens` | Nâng lên **16384** |
| HTTP 402 "credits depleted" | Hết credit Gemini | Nạp credit; hạn chế test |
| Animation "đứng hình", chỉ có tiếng + phụ đề | Dùng thời gian tuyệt đối trong timeline cảnh | **`tline(line,frac,base=st)`** — thời gian theo cảnh |
| Cảnh/phụ đề lệch nhau | Lệch số dòng kịch bản | Khớp `beat` + reveal theo câu |
| File gửi về máy bị cũ | `device_commit_files` cache theo tên | Luôn dùng **tên file mới** mỗi lần chuyển |

### 9.3. Chi phí Gemini (tham khảo)
- Vận hành đúng lịch (vài video/ngày): **~$4–7/tháng**.
- Cấu thành: Flash (text, viết kịch bản) rẻ; **Flash TTS ~$0.0135/phút** audio là phần chính.
- **Chạy test nhiều = đốt credit nhanh** → luôn ưu tiên `build-deck` + screenshot trước khi render thật.

---

## 10. CÁC PIPELINE ĐANG CHẠY (tham chiếu nhanh)

| Loại | Brain | Template | Nhịp | Workflow |
|---|---|---|---|---|
| Giải Mã tin CK | `build_deck_from_url.py` | `giaima-tin-hf` | theo link (bot) | `tg-intake.yml` |
| VNINDEX | `build_vnindex_deck.py` | `vnindex-daily-hf` | hằng ngày | `vnindex-build.yml` |
| Vàng (ngày/tuần) | `build_gold_deck.py` | `gold-daily-bias-hf` | ngày + T2 tuần | `gold-build.yml` |
| S&P500 + Nasdaq | `build_equity_deck.py` | `equity-bias-hf` | ngày + tuần | `equity-build.yml` |
| Liên thị trường | `build_intermarket_deck.py` | `intermarket-weekly-hf` | Chủ Nhật | `intermarket-build.yml` |

---

*Hết. Bộ khung mẫu để nhân bản: `docs/scaffold/`.*
