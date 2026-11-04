# BỘ KHUNG MẪU (SCAFFOLD) — NHÂN BẢN PIPELINE VIDEO

Thư mục này chứa các **file khung mẫu** để tạo nhanh một pipeline video mới cho **bất kỳ loại nội dung nào**, theo đúng chuẩn trong [`../QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md`](../QUY-TRINH-CHUAN-VIDEO-AUTOMATION.md).

## Có gì ở đây

| File | Dùng để |
|---|---|
| `CHECKLIST-NHAN-BAN.md` | **Bắt đầu từ đây.** Tick từng việc khi làm nội dung mới. |
| `hf-data.schema.json` | Khung "hợp đồng dữ liệu" `hf-data.json` (brain sinh ra, template đọc). |
| `brain_tin_tuc.template.py` | Brain **Kiểu A**: 1 link bài → deck (Gemini viết cả deck). |
| `brain_du_lieu.template.py` | Brain **Kiểu B**: số liệu JSON → deck (số lấy tất định, Gemini chỉ viết chữ). |
| `template_hyperframes.build.py` | Skeleton template HyperFrames — minh họa **LUẬT VÀNG `tline`**, vùng an toàn phụ đề, hiệu ứng số, cover. |
| `workflow_build.yml.template` | Workflow GitHub Actions cho 1 loại (dispatch → brain → render → commit → Telegram). |
| `apps_script_trigger.gs.template` | Trigger Apps Script hẹn giờ (+ chống trùng ngày, bỏ cuối tuần). |

## Dùng thế nào (tóm tắt)

```
1. Mở CHECKLIST-NHAN-BAN.md, đặt <loai> = tên loại nội dung.
2. Copy brain template phù hợp → build_<loai>_deck.py (gốc repo), sửa SPEC/map số liệu.
3. Copy template/<gần-giống>-hf/ → template/<loai>-hf/, sửa cảnh (giữ tline + base).
4. Thêm 1 dòng vào STYLE_PRESET trong ci_build_video.py.
5. Copy workflow_build.yml.template → .github/workflows/<loai>-build.yml, sửa tên/lệnh.
6. Copy hàm Apps Script, đặt Time-driven trigger.
7. TEST rẻ: build-deck.yml (brain) + screenshot container → rồi render-upload.yml (Private) 1 video.
```

## Nguyên tắc vàng (đừng quên)

- **Số câu mỗi dòng kịch bản = [1,3,3,3,4,4,3,3,3]**, đúng 9 dòng.
- **≤ 720 từ** → video **< 3 phút** (đo thực: 619 từ = 152 giây).
- **Animation theo mốc cảnh**: `tline(line, frac, base=start_cảnh)`. Quên trừ base = hình đứng im.
- **Tên/chỉ số tiếng Anh viết chuẩn** (Dow Jones, S&P 500, Nasdaq, VN-Index); "KenvinZone" đọc đúng.
- **Test rẻ trước, render thật sau** — đừng đốt credit Gemini vào render test.
- **Luôn Private → duyệt → public.**

> Các file `.template.py` / `.yml.template` **không chạy trực tiếp** — phải copy ra đúng vị trí và đổi tên (bỏ `.template`) rồi sửa các chỗ `# >>> SỬA`.
