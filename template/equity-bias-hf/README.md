# Template HyperFrames — Bản tin Bias Vàng daily

Không sửa trực tiếp thư mục này khi làm bản tin. Mỗi bản tin chỉ cần file `hf-data.json`
trong thư mục slide (vd. `slide/gold-daily-bias-29-10/hf-data.json`).

Khi bấm Render trên Web UI, `auto_render.py` thấy `hf-data.json` sẽ:
1. tạo giọng đọc + mốc thời gian từng chữ như cũ,
2. copy template này vào `output/hf/`, sinh composition bằng `build.py`,
3. render từng khung hình bằng HyperFrames → `output/final_video.mp4`.

Cần Node.js 22+ (npx). Nếu máy chưa có Node, hệ thống tự quay về cách quay màn hình cũ.
Chọn "Quay màn hình (cũ)" ở mục Nâng cao của Web UI để ép dùng cách cũ.
