# Bộ kiểm thử zero-credit cho template HyperFrames (Explainer)

Dựng compositions + chụp khung hình bất kỳ của video mà không gọi TTS.
Cần: `pip install playwright pillow && playwright install chromium`.

```bash
# 1) dựng thư mục work từ một bài học (timing giả lập theo thời lượng 9 dòng đo thực)
python tools/qa/mkwork.py lessons/explainer/sample-sideway-b.json /tmp/work
# 2) chụp: số giây toàn cục, hoặc sN@0.85 = 85% thời lượng cảnh N
python tools/qa/shoot.py /tmp/work /tmp/shots s1@0.85 s7@0.95 42.5
# 3) ghép ảnh + phủ đỏ vùng UI che (đáy y>1450, cột nút phải x>888 từ y 840, đỉnh y<240)
python tools/qa/safezone.py /tmp/out.png /tmp/shots/s1_0.85.png /tmp/shots/s7_0.95.png
```

shoot.py nạp index.html, bơm từng composition vào host, rồi seek đồng loạt mọi
timeline GSAP tới thời điểm toàn cục → ra đúng khung hình video (cả lớp nhãn,
phụ đề, camera). Lỗi JS trên trang được in ra dưới dạng "PAGE ERRORS".
