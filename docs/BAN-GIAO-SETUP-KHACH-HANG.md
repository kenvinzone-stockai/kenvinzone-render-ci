# BÀN GIAO — THIẾT LẬP DÂY CHUYỀN VIDEO TỰ ĐỘNG CHO MỘT KHÁCH HÀNG MỚI

> File bàn giao tuần tự: đưa cho một **AI Agent** (Claude / Gemini / GPT) là nó tự dẫn từng bước
> từ khởi tạo GitHub → automation → Telegram → đến video đầu tiên publish lên **kênh YouTube Private của khách**.
> Cũng dùng được như **checklist** để chính bạn (KenvinZone) làm theo khi có đơn.
>
> Hệ thống gốc (engine): repo `kenvinzone-stockai/kenvinzone-render-ci`.
> Tài liệu kỹ thuật chi tiết: `docs/QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md` + bộ khung `docs/scaffold/`.

---

## 0. HƯỚNG DẪN CHO AI AGENT (đọc trước khi bắt đầu)

Bạn là AI Agent được giao thiết lập **một dây chuyền sản xuất video tự động** cho một khách hàng mới của KenvinZone AutoVideo. Hãy làm đúng tinh thần sau:

1. **Đọc hết file này một lượt** trước khi hành động.
2. **Thu thập đủ thông tin ở PHẦN 1** (hỏi người vận hành/khách) trước khi sang PHẦN 2.
3. Thực hiện **tuần tự từng BƯỚC**, không nhảy cóc. Sau mỗi bước, **xác nhận kết quả mong đợi** rồi mới đi tiếp.
4. Việc nào cần thao tác trên máy/trình duyệt của người dùng (tạo bot, OAuth Google, dán secret) thì **hướng dẫn rõ ràng từng cú nhấp**; việc nào gọi được qua API/CLI thì **tự làm rồi báo cáo**.
5. **Nguyên tắc an toàn:** mỗi khách một bộ secret riêng; luôn upload video ở chế độ **Private** để khách duyệt; **không đốt credit** vào render thử (dùng `build-deck` + screenshot để kiểm trước).
6. Nếu thiếu thông tin hoặc một bước thất bại, **dừng lại, báo rõ** thiếu gì / lỗi gì, không đoán bừa với hành động không hoàn tác được.

**Mục tiêu hoàn thành:** khách có một kênh video chạy tự động theo lịch, video đầu tiên đã nằm Private trên kênh YouTube của khách, và khách biết cách “duyệt” để công khai.

---

## PHẦN 1 — THU THẬP THÔNG TIN ĐẦU VÀO (bắt buộc trước khi làm)

Hỏi và ghi lại đủ các mục sau. Thiếu mục nào thì xin trước khi bắt đầu PHẦN 2.

**A. Về nội dung**
- [ ] Loại nội dung khách muốn (vd: review sản phẩm, tin tức, tài chính, giáo dục, bản tin thương hiệu…).
- [ ] Nguồn dữ liệu: **một đường link bài** mỗi lần (Kiểu A) hay **số liệu/JSON định kỳ** (Kiểu B)?
- [ ] Tần suất đăng: theo yêu cầu / hằng ngày / hằng tuần. Có bỏ Thứ 7–CN không?
- [ ] Ngôn ngữ, giọng đọc: giọng mặc định hay **clone giọng** của khách (nếu clone: xin mẫu giọng).
- [ ] Tên thương hiệu / handle hiển thị trên video.

**B. Về tài khoản & khoá (mỗi khách một bộ)**
- [ ] **Kênh YouTube** của khách (để đăng Private). Cần quyền: khách tạo OAuth hoặc cấp quyền đăng (xem BƯỚC 4).
- [ ] **Khóa Gemini API** (`GEMINI_API_KEY`): của khách (khách tự trả credit) hay của KenvinZone (tính vào gói). Chốt rõ ai trả.
- [ ] Tài khoản **GitHub** để chứa dây chuyền (của KenvinZone, hoặc tạo cho khách).
- [ ] **Telegram** của khách (để nhận/điều khiển): tài khoản Telegram + sẵn sàng tạo bot.

**C. Thương mại**
- [ ] Gói/giá đã chốt (báo giá theo dự án). Phạm vi hỗ trợ sau bàn giao.

> **Mô hình triển khai mặc định:** mỗi khách = **một repo riêng** (bản sao engine) + **một bộ secret riêng** + **một bot Telegram riêng**. Cách này cô lập dữ liệu và kênh của từng khách. (Phương án gọn hơn: dùng chung một repo và tách theo nhiều pipeline — chỉ nên dùng khi bạn tự quản toàn bộ.)

---

## PHẦN 2 — CÁC BƯỚC THIẾT LẬP (tuần tự)

### BƯỚC 1 — Tạo kho GitHub cho khách (nền tảng chạy tự động)
**Mục tiêu:** có một repo chứa engine, bật GitHub Actions (nơi mọi thứ chạy, miễn phí với repo public).
1. Tạo repo mới, ví dụ `kenvinzone-stockai/autovideo-<tên-khách>` (hoặc trong tài khoản khách).
2. Đưa toàn bộ nội dung engine `kenvinzone-render-ci` vào repo này (copy/clone-push, hoặc “Use this template” nếu đã đặt engine làm template).
3. Để repo **public** để Actions chạy miễn phí (code lộ nhưng **secret vẫn an toàn**, không bao giờ nằm trong code). Nếu bắt buộc private → cần tài khoản có phút Actions trả phí.
4. Vào **Settings → Actions → General**: bật “Allow all actions”, và “Workflow permissions” = **Read and write**.
**Kết quả mong đợi:** repo tồn tại, tab **Actions** bật được, thấy danh sách workflow (`tg-intake.yml`, `gold-build.yml`, `build-deck.yml`, `render-upload.yml`…).

### BƯỚC 2 — Lấy khoá Gemini API
**Mục tiêu:** có `GEMINI_API_KEY` để viết kịch bản + tạo giọng đọc.
1. Vào Google AI Studio (aistudio.google.com) → tạo API key.
2. **Bật thanh toán/nạp credit** cho key (hệ thống dùng cả Gemini Flash text + Flash TTS trả phí). Ước tính vận hành đúng lịch: ~$4–7/tháng.
3. Lưu lại khoá để nạp vào Secrets ở BƯỚC 5.
**Kết quả mong đợi:** có một API key Gemini còn credit.

### BƯỚC 3 — Tạo bot Telegram (kênh điều khiển qua chat)
**Mục tiêu:** khách gửi link / nhận video / nhắn “duyệt” ngay trong Telegram.
1. Trong Telegram, nhắn **@BotFather** → `/newbot` → đặt tên + username → nhận **TELEGRAM_BOT_TOKEN**.
2. Mở đoạn chat với bot vừa tạo, bấm **Start** và gửi một tin bất kỳ.
3. Lấy **TELEGRAM_CHAT_ID**: mở `https://api.telegram.org/bot<TOKEN>/getUpdates` trên trình duyệt → đọc trường `chat.id` (repo cũng có workflow `tg-chatid.yml` hỗ trợ lấy nhanh).
**Kết quả mong đợi:** có `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (chat của khách, hoặc nhóm chung khách–bạn).

### BƯỚC 4 — Kết nối kênh YouTube của khách (OAuth → refresh token)
**Mục tiêu:** hệ thống đăng video lên **đúng kênh YouTube của khách**, ở chế độ Private.
> Đây là bước nhạy cảm nhất — thao tác trên tài khoản Google của khách. Làm cùng khách.
1. Google Cloud Console → tạo project → **bật YouTube Data API v3**.
2. **OAuth consent screen**: kiểu External, thêm email khách làm **Test user** (scope cần: `.../auth/youtube.upload` và `youtube`).
3. **Credentials → Create OAuth client ID** → loại **Desktop app** → lấy `client_id` + `client_secret`.
4. Chạy luồng OAuth (offline access) **đăng nhập bằng tài khoản sở hữu kênh YouTube của khách** để lấy **refresh_token**.
5. Ghép thành `config/social-upload.json` (client + channel + refresh_token) theo đúng cấu trúc engine đang dùng; lấy **YT_CHANNEL_ID** của kênh khách.
**Kết quả mong đợi:** có nội dung JSON `social-upload.json` hợp lệ + `YT_CHANNEL_ID`, thử đăng 1 video Private thành công.

### BƯỚC 5 — Nạp Secrets vào GitHub
**Mục tiêu:** đưa mọi khoá vào kho an toàn của repo (không bao giờ ghi vào code).
Vào **repo → Settings → Secrets and variables → Actions → New repository secret**, tạo đủ:
- `GEMINI_API_KEY` — khoá Gemini (BƯỚC 2)
- `SOCIAL_UPLOAD_JSON` — **toàn bộ** nội dung `config/social-upload.json` (BƯỚC 4)
- `TTS_CONFIG_JSON` — nội dung `config/tts.json` (giọng clone/style; nếu dùng giọng mặc định vẫn nên có bản tối thiểu)
- `YT_CHANNEL_ID` — id kênh khách
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — BƯỚC 3
**Kết quả mong đợi:** đủ secret; chạy thử workflow `check-token.yml` (nếu có) để xác nhận khoá hợp lệ.

### BƯỚC 6 — Chọn/khởi tạo loại nội dung (brain + template)
**Mục tiêu:** có “bộ não” và “mẫu video” đúng loại nội dung của khách.
1. Nếu loại nội dung **giống sẵn có** (tin tức/tài chính…) → dùng luôn brain + template tương ứng.
2. Nếu **mới** → theo `docs/QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md` mục “7 bước nhân bản”, dùng `docs/scaffold/`:
   - Copy brain mẫu (`brain_tin_tuc.template.py` hoặc `brain_du_lieu.template.py`) → `build_<loại>_deck.py`, sửa `SPEC`/map số liệu.
   - Copy một thư mục `template/*-hf/` → `template/<loại>-hf/`, sửa cảnh (**giữ LUẬT VÀNG `tline` + base**, phụ đề vùng an toàn).
   - Thêm 1 dòng vào `STYLE_PRESET` trong `ci_build_video.py`.
   - Giữ validator `check_deck_cloud.py` (ngưỡng **≤720 từ** để video **<3 phút**).
**Kết quả mong đợi:** có `build_<loại>_deck.py` + `template/<loại>-hf/` + dòng STYLE_PRESET.

### BƯỚC 7 — Thiết lập lịch tự động (trigger)
**Mục tiêu:** dây chuyền tự chạy đúng giờ, không cần ai bấm.
1. **Theo link (Kiểu A):** đã có `tg-intake.yml` poll Telegram mỗi 30’ — khách chỉ cần gửi link vào bot.
2. **Theo lịch (Kiểu B / định kỳ):** tạo workflow `<loại>-build.yml` từ `docs/scaffold/workflow_build.yml.template`; hẹn giờ bằng **Google Apps Script** (bắn `repository_dispatch`) theo `docs/scaffold/apps_script_trigger.gs.template` — **không dùng cron GitHub** (hay trễ). Thêm **chống trùng theo ngày** + **bỏ cuối tuần** nếu là tin ngày.
**Kết quả mong đợi:** trigger chạy thử ra HTTP 204; workflow nhận được và khởi động.

### BƯỚC 8 — Kiểm thử RẺ (không đốt credit)
**Mục tiêu:** chắc chắn “bộ não” ra deck đạt chuẩn trước khi render thật.
1. Chạy workflow **`build-deck.yml`** (chỉ bước não, gần như không tốn tiền) với 1 link/nguồn mẫu.
2. Mở log committed tại **`ci-logs/brain-*.log`** → cần thấy `KẾT QUẢ: ĐẠT` và dòng `PROJECT=...`.
3. (Tuỳ chọn) chụp màn hình bố cục bằng Playwright (không tốn Gemini) để soi khung hình.
**Kết quả mong đợi:** deck ĐẠT, script <720 từ, bố cục ổn.

### BƯỚC 9 — Dựng video thật đầu tiên (Private)
**Mục tiêu:** ra `final_video.mp4` và upload lên kênh khách ở chế độ Private.
1. Chạy **`render-upload.yml`** cho `project` vừa dựng, `privacy = private`.
2. Theo dõi: TTS (giọng clone) → render HyperFrames → upload. Log tại `ci-logs/run-*.log`.
**Kết quả mong đợi:** video Private xuất hiện trên kênh khách; bot Telegram báo link.

### BƯỚC 10 — Nghiệm thu chất lượng
**Mục tiêu:** đạt chuẩn KenvinZone trước khi bàn giao.
- [ ] Độ dài **< 3 phút**.
- [ ] Animation chạy mượt (không “đứng hình”), phụ đề trong vùng an toàn.
- [ ] Giọng đọc đúng (tên riêng/brand đọc chuẩn), thuật ngữ tiếng Anh viết chuẩn (không phiên âm).
- [ ] Tiêu đề cover rõ ràng; nếu khách đưa tiêu đề thì **giữ nguyên văn**.
**Kết quả mong đợi:** video đạt; nếu chưa, quay lại BƯỚC 6–9 chỉnh.

### BƯỚC 11 — Bàn giao & hướng dẫn vận hành cho khách
**Mục tiêu:** khách tự vận hành bằng thao tác đơn giản nhất.
1. Chỉ khách cách **gửi link** (Kiểu A) hoặc để **lịch tự chạy** (Kiểu B).
2. Chỉ khách cách **xem video Private** và nhắn **“duyệt”** trong Telegram để công khai.
3. Gửi khách bản tóm tắt: kênh chạy gì, giờ nào, liên hệ hỗ trợ.
**Kết quả mong đợi:** khách hiểu và tự chạy được; dây chuyền bàn giao hoàn tất. ✅

---

## PHẦN 3 — QUY TRÌNH NHẬN ĐƠN & BÀN GIAO (phía kinh doanh của KenvinZone)

1. **Khách liên hệ** qua landing `autovideo.kenvinzone.com` (Zalo/Email/Form).
2. **Tư vấn** nhu cầu, chốt loại nội dung + tần suất + kênh đăng.
3. **Chốt gói & báo giá** theo dự án; thống nhất ai trả credit Gemini.
4. **Thu thập thông tin** theo PHẦN 1 (đặc biệt: quyền YouTube + Telegram của khách).
5. **Thiết lập** theo PHẦN 2 (tự làm, hoặc giao file này cho AI Agent dẫn từng bước).
6. **Nghiệm thu** video đầu (BƯỚC 10) cùng khách.
7. **Bàn giao** + hướng dẫn “duyệt” (BƯỚC 11).
8. **Hỗ trợ & nâng cấp** theo gói (thêm loại nội dung, đổi mẫu, mở rộng kênh).

---

## PHẦN 4 — PHỤ LỤC

**Bảo mật (bắt buộc):** mỗi khách **một bộ secret riêng**; secret chỉ nằm trong GitHub Secrets, **không bao giờ** trong code/log. Không chia sẻ refresh_token/khoá giữa các khách. Thu hồi quyền khi kết thúc hợp đồng (xoá secret, gỡ OAuth client).

**Chi phí:** chủ yếu là Gemini Flash TTS (~$0,0135/phút audio) + Flash text (rẻ). Vận hành đúng lịch ~$4–7/tháng/kênh. **Chạy test nhiều = đốt credit nhanh** → luôn ưu tiên `build-deck` + screenshot trước khi render thật.

**Chẩn lỗi nhanh:** log Actions không tải trực tiếp được → đọc file trong **`ci-logs/`** (đã commit). `build-deck.yml` commit log kể cả khi lỗi. Các lỗi hay gặp & cách xử lý: xem bảng trong `docs/QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md` (script quá dài → ngưỡng 720 từ; Gemini timeout → tự thử lại; JSON cắt cụt → tăng maxOutputTokens; hình “đứng im” → dùng `tline(... base=st)`).

**Quy tắc bất biến (áp cho mọi khách):** video <3 phút; phụ đề vùng an toàn; animation theo mốc cảnh; tên/chỉ số tiếng Anh viết chuẩn; brand đọc đúng; luôn Private → duyệt → public; không dùng từ cấm (“mua ngay”, “chắc chắn tăng”, “cam kết lãi”…), giọng là “góc nhìn tham khảo, không phải khuyến nghị đầu tư”.

**Tài liệu liên quan trong repo:**
- `docs/QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md` — kiến trúc & cách nhân bản chi tiết.
- `docs/scaffold/` — bộ khung mẫu (brain, template, workflow, Apps Script, checklist).

---

*Hết. Giao file này cho một AI Agent kèm câu: “Hãy đọc file bàn giao và dẫn tôi làm tuần tự từ PHẦN 1”.*
