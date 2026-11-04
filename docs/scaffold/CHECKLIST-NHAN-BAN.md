# CHECKLIST — NHÂN BẢN PIPELINE CHO NỘI DUNG MỚI

> In/копy checklist này cho mỗi loại nội dung mới. Tick từ trên xuống. Đặt `<loai>` = tên loại (vd `crypto-daily`).

## Bước 1 — Xác định (5 phút)
- [ ] Nguồn dữ liệu: ☐ 1 link bài (Kiểu A) ☐ số liệu/JSON định kỳ (Kiểu B)
- [ ] Nhịp đăng: ☐ theo link ☐ hằng ngày ☐ hằng tuần ☐ theo sự kiện
- [ ] Bỏ cuối tuần? (tin thị trường ngày → có). Đăng thứ mấy nếu là tuần?
- [ ] Kênh YouTube đích + có cần secret `<LOAI>_YT_CHANNEL_ID` riêng không
- [ ] Đặt tên loại: `<loai>` = ____________

## Bước 2 — Hợp đồng dữ liệu (10 phút)
- [ ] Liệt kê 9 cảnh và mỗi cảnh cần số/nội dung gì
- [ ] Copy `hf-data.schema.json` → chỉnh các khối `s1..s7` cho loại này

## Bước 3 — Brain (30–60 phút)
- [ ] Copy brain template phù hợp → `build_<loai>_deck.py` ở GỐC repo
  - Kiểu A: `brain_tin_tuc.template.py`
  - Kiểu B: `brain_du_lieu.template.py`
- [ ] Sửa `TEMPLATE_NAME`, `STYLE_PRESET`
- [ ] Sửa `SPEC` (Kiểu A) hoặc `pick_data()`+`build_scenes()`+`SPEC_STORY` (Kiểu B)
- [ ] Sửa quy tắc đặt tên project
- [ ] Giữ ràng buộc: 9 dòng · [1,3,3,3,4,4,3,3,3] · ≤720 từ · tên tiếng Anh chuẩn · từ cấm

## Bước 4 — Template HyperFrames (1–3 giờ)
- [ ] Copy `template/<gần-giống>-hf/` → `template/<loai>-hf/`
- [ ] Sửa từng cảnh trong `build.py`
- [ ] ✅ KIỂM: mọi animation dùng `tline(line, frac, base=st)` (trừ base = start cảnh)
- [ ] ✅ KIỂM: phụ đề trong vùng an toàn (top ≤ ~1205px)
- [ ] ✅ KIỂM: cover `s0` cỡ chữ có sàn + `white-space:nowrap` + cách phụ đề đủ rộng
- [ ] Thêm hiệu ứng số (counter/VU-meter) + SFX nếu có số liệu
- [ ] **Thêm 1 dòng vào `STYLE_PRESET` trong `ci_build_video.py`**: `"<loai>-hf": "<preset giọng>"`

## Bước 5 — Validator (15 phút)
- [ ] Nếu cấu trúc 9 cảnh giống chuẩn → dùng lại `check_deck_cloud.py`
- [ ] Nếu khác → thêm/sửa luật cho đúng cảnh mới (giữ ngưỡng ≤720 từ + từ cấm)

## Bước 6 — Workflow (20 phút)
- [ ] Copy `workflow_build.yml.template` → `.github/workflows/<loai>-build.yml`
- [ ] Sửa `name`, `concurrency.group`, `repository_dispatch.types`
- [ ] Sửa lệnh brain (`--url` / `--data --frame`)
- [ ] Sửa secret kênh YouTube
- [ ] Giữ bước: commit log → báo Telegram → upload artifact

## Bước 7 — Trigger + Kiểm thử RẺ (30 phút)
- [ ] Copy hàm từ `apps_script_trigger.gs.template` vào Apps Script
- [ ] Đặt Time-driven trigger đúng giờ (ngoài 6–9h sáng Pacific để tránh trễ)
- [ ] Thêm chống trùng theo ngày + bỏ cuối tuần (nếu cần)
- [ ] Chạy `testOnce()` → thấy HTTP 204
- [ ] **TEST brain bằng `build-deck.yml`** (Actions → Run workflow → nhập url/khung) → đọc `ci-logs/brain-*.log` thấy `KẾT QUẢ: ĐẠT`
- [ ] **Soi hình bằng screenshot container** (Playwright, không tốn Gemini)
- [ ] Chạy `render-upload.yml` (Private) MỘT video thật để nghiệm thu
- [ ] Xem video + kiểm **< 3 phút** → nhắn "duyệt" nếu OK

## Nghiệm thu cuối
- [ ] Video đúng bố cục, animation chạy mượt, phụ đề đúng vùng
- [ ] Giọng đọc đúng (KenvinZone đọc chuẩn), tên tiếng Anh không phiên âm
- [ ] Độ dài < 3 phút
- [ ] Trigger tự chạy đúng giờ (theo dõi 1–2 ngày đầu)
