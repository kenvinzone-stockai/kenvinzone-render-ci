# Template HyperFrames — AURORA Explainer

Khác 3 mẫu kia: **không cần chép nội dung vào hf-data.json**. Template đọc thẳng `index.html`
của tập (deck 9 slide theo `slide/aurora-explainer-template`) và dựng lại từng thẻ thành cảnh động 1080×1920.

Mỗi tập chỉ cần file `hf-data.json` nằm cạnh `index.html`:

    { "template": "aurora-explainer-hf" }

Tùy chọn: `"hero_color": "#fff2b3"` (mặc định lấy Màu tiêu đề trong preview-settings.json),
`"audio_offset"`, `"outro_hold"`, `"bg_alpha"`, `"bg_speed"`.

Thành phần được nhận diện: hook (`kv-s1-content`), `slide-title`, `gm-source-card`, `gm-stat-row`
(số thì đếm số, chữ thì tự xuống dòng), `gm-quote`, `gm-box`, 3 `gm-impact` (slide highlight sáng lần lượt),
3 `gm-tl` (đèn xanh/vàng/đỏ sáng lần lượt), outro (`kv-outro-*`). Thẻ lạ hiện thành thẻ kính chung.

Nhịp: 1 dòng script = 1 slide. Tiêu đề hiện khi dòng bắt đầu, thẻ đầu ~0,9s sau, các thẻ sau theo
đầu câu kế tiếp. Slide highlight/đèn: mỗi thẻ sáng đúng lúc đọc tới vế sau dấu ":" và các dấu ";"
(công thức "Ba …: A; B; và C"). Cỡ chữ tự co để không tràn vùng an toàn (đã kiểm 43 deck hiện có).
Chỉ dùng thư viện chuẩn Python.
