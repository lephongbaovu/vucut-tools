# Cài vucut trên máy mới (Windows / macOS / Linux)

Làm **một lần mỗi máy**. Sau đó chỉ cần nói "vucut" với Claude.

## 1 · Cài 3 phần mềm nền
| Phần mềm | Bản | Windows | macOS |
|---|---|---|---|
| Python | 3.10 – 3.13 (khuyên 3.12) | python.org → tick **Add python.exe to PATH** | `brew install python@3.12` |
| ffmpeg | ≥ 5 | `winget install Gyan.FFmpeg` | `brew install ffmpeg` |
| Node.js | ≥ 18 (bản LTS) | nodejs.org → bản LTS | `brew install node` |

Cài xong **đóng và mở lại** terminal / Claude để nhận PATH mới. Kiểm tra: `python --version`, `ffmpeg -version`, `node -v`.

## 2 · Chạy setup (cần mạng, ~5–15 phút)
```
python -X utf8 <thư mục skill vucut>/scripts/vucut.py setup --rembg
```
Setup tự làm:
- cài thư viện Python theo `requirements.txt` (phiên bản đã kiểm thử);
- cài **playwright + Chromium** riêng vào `~/.vucut/node` (không cần `npm -g`, không cần đặt `NODE_PATH`);
- tải sẵn mô hình phiên âm Whisper `medium` (~1,5 GB) và tách nền `u2net_human_seg` (~176 MB) → các lần dựng sau chạy offline.

Máy yếu (RAM < 8 GB): thêm `--model small` (và dùng `prep --model small`).
Cuối cùng phải thấy dòng **🎉 SẴN SÀNG**. Còn dòng ❌ nào thì làm theo gợi ý ngay dòng đó rồi chạy lại.

## 3 · (Tuỳ chọn) Nhiều máy cùng làm một kênh
vucut nhớ bộ màu / sợi chỉ / hình đã dùng để video sau không lặp video trước. Mặc định file nằm ở `~/.vucut/history.json` (riêng từng máy). Muốn các máy dùng chung → đặt biến môi trường trỏ vào thư mục đồng bộ (Google Drive, OneDrive…):
- Windows: `setx VUCUT_HISTORY "G:\My Drive\vucut\history.json"`
- macOS: thêm `export VUCUT_HISTORY="$HOME/Google Drive/vucut/history.json"` vào `~/.zshrc`

## 4 · (Tuỳ chọn) Máy không có mạng / mạng công ty chặn
Chạy setup trên một máy có mạng, rồi chép các thư mục sau sang đúng chỗ trên máy kia:
| Thư mục | Chứa |
|---|---|
| `~/.cache/huggingface/hub` | mô hình Whisper |
| `~/.u2net` | mô hình tách nền rembg |
| `~/.vucut/node` + bộ nhớ trình duyệt playwright (Windows `%LOCALAPPDATA%\ms-playwright`, macOS `~/Library/Caches/ms-playwright`) | render |
Thư viện Python: trên máy có mạng `pip download -r requirements.txt rembg -d goi_pip`, chép sang, rồi `pip install --no-index --find-links goi_pip -r requirements.txt rembg`.

## Lỗi thường gặp
| Hiện tượng | Cách sửa |
|---|---|
| `'python' is not recognized` | cài lại Python, tick Add to PATH; hoặc dùng `py -3.12` thay `python` |
| `UnicodeEncodeError` / chữ Việt lỗi | luôn chạy `python -X utf8 …` (vucut.py đã tự bật lại nếu quên) |
| ❌ playwright/Chromium | chạy lại `setup`; mạng chặn → mục 4 |
| faster-whisper cài lỗi trên Python 3.14 | dùng Python 3.12 |
| Render rất chậm | `render --draft` khi xem nháp; `cut --frames-h 1280`; `render --jobs 2` nếu máy ít RAM |
| Có cả `opencv-python` và `opencv-python-headless` → lỗi `cv2` | `pip uninstall -y opencv-python opencv-python-headless` rồi chạy lại setup |
