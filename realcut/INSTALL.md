# Cài realcut trên máy mới / tài khoản mới

## A · Skill trong tài khoản Claude
Skill chỉ có SKILL.md; code, font, mô hình nằm ở kho github.com/lephongbaovu/vucut-tools (thư mục `realcut/`), mỗi phiên tự tải về `~/.vucut/repo` (dùng chung với vucut).

## B · Khi chạy trên máy tính riêng (Claude Code / máy có Python)
1. Cài **Python 3.10–3.13** (khuyên 3.12) và **ffmpeg ≥ 5**
   - Windows: python.org (tick *Add python.exe to PATH*) · `winget install Gyan.FFmpeg`
   - macOS: `brew install python@3.12 ffmpeg`
2. Chạy (cần mạng lần đầu, ~5–15 phút):
   `git clone --depth 1 https://github.com/lephongbaovu/vucut-tools ~/.vucut/repo` rồi `python -X utf8 ~/.vucut/repo/realcut/scripts/realcut.py setup --model medium`
   → phải thấy **🎉 SẴN SÀNG**. Máy yếu: `--model small`.

## Lỗi thường gặp
| Hiện tượng | Cách sửa |
|---|---|
| `'python' is not recognized` | cài lại Python, tick Add to PATH; hoặc dùng `py -3.12` |
| Chữ Việt lỗi / `UnicodeEncodeError` | chạy `python -X utf8 …` (realcut.py tự bật lại nếu quên) |
| faster-whisper lỗi trên Python 3.14 | dùng Python 3.12 |
| Có cả `opencv-python` và `opencv-python-headless` | `pip uninstall -y opencv-python opencv-python-headless` rồi chạy lại setup |
| GitHub bị chặn khi tải font/mô hình | font đã đóng gói sẵn; thiếu font thì `npm pack @expo-google-fonts/playfair-display @expo-google-fonts/be-vietnam-pro` |
| Máy không có mạng | chạy setup ở máy có mạng, chép `~/.cache/huggingface/hub` (Whisper) sang |
