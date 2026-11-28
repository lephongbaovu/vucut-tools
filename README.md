# vucut-tools

Công cụ dựng video talking-head 9:16 cho kênh **Lê Phong Vũ · BĐS Đắk Lắk** (skill `vucut`).
Từ 27/11/2026 **toàn bộ mã dựng nằm trong kho này**; skill `vucut` chỉ còn hướng dẫn (SKILL.md). Sửa công cụ = sửa ở đây.

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `vc.py` | Lệnh chính (`setup · go · cut · sb · build · xem · nhap · out · wait · grid · ranh · diadanh · speakers · kiemtra`) và các cảnh mẫu `P.*` dùng trong `scenes.py` |
| `mg_real.py` | Bộ đồ hoạ chân thực `R.*` (100 hình, 10 chủ đề) |
| `engine/scripts/` | Bộ máy: `vucut.py` (phiên âm, cắt, âm thanh, render), `vc_build.py` (lắp cảnh, phụ đề), `preview.mjs` (chụp khung, đã lắp sẵn chuỗi khung bản đồ 3D), `transcribe · autocut · tighten · facetrack · beats · make_sfx · sfx_mix · sfx_thin · matte_split · theme` |
| `engine/tools/` | `vc_patch.py` (chỉnh vc_build cho kênh: màu phụ đề, tự căn vùng an toàn…), `cine.py` + `cine_sfx.py` (hiệu ứng điện ảnh, âm), `qc_gate.cjs` (cổng kiểm tra trước khi xuất) |
| `engine/assets/` | Font, GSAP, khung HTML, `vucut.js/css`, ranh giới Đắk Lắk (`daklak/`), mô hình dò mặt |
| `engine/reference/` | Từ điển sửa chính tả, từ vựng, số liệu Đắk Lắk |

## Cài (đầu mỗi phiên — đã ghi trong SKILL.md)

```
mkdir -p ~/.vucut/tools && (git -C ~/.vucut/repo pull -q || git clone -q --depth 1 https://github.com/lephongbaovu/vucut-tools ~/.vucut/repo) \
  && cp ~/.vucut/repo/*.py ~/.vucut/tools/ && python3 -X utf8 ~/.vucut/tools/vc.py setup <thư mục skill>
```
`setup` tự lấy bộ máy từ `~/.vucut/repo/engine` (thư mục skill chỉ dùng khi kho chưa có `engine/`).

## Mặc định anh Vũ đã chốt

| Mục | Mặc định | Đổi trong `scenes.py` |
|---|---|---|
| Nhạc nền | **1 bài duy nhất** `'tin'` (đưa tin – kịch tính), −8 dB, tổng −11 LUFS | — (các bài cũ đã xoá 27/11/2026) |
| Chuyển cảnh | **Cắt gọn**: cắt thẳng, cảnh mới khựng nhẹ; mặt tự ẩn trong cảnh đồ hoạ | `P.chuyen('da' \| 'truot' \| 'net')` |
| Mở đầu mặt → bản đồ | — | `P.thu(giây)`: khung cắt đúng phần người trong ô kính rồi thu vào ô kính |
| Màu bản đồ | Chữ địa danh + chữ kêu gọi **vàng nhũ**, viền ranh giới **vàng xước** | `P.mau('nhu' \| 'xuoc' \| 'sampanh' \| 'hong')` |
| Bản đồ | Luôn 3D (Google + AWS Terrain); tuyến đường đỏ phát sáng | `P.sat(a, b, 'Đắk Lắk', t_draw=, focus="M'Drắk", t_focus=, rise=(t0, t1))` = cận xã → bay lên toàn tỉnh → vẽ viền |
| Nền đồ hoạ | Đỏ trầm hạt nhiễu | `P.nen('do_ruc' \| 'than' \| 'dem' \| 'da' \| 'den')` |

## Kiểm tra sau khi sửa công cụ

```
python3 -X utf8 ~/.vucut/tools/vc.py kiemtra            # nạp module + soát cú pháp JS
python3 -X utf8 ~/.vucut/tools/vc.py kiemtra ~/vucut/X  # + dựng lại dự án X, so 16 khung với bản mốc (lần đầu lưu mốc)
```
Đạt → mới đẩy lên kho.

## Nhật ký
- **28/11/2026** — Dọn mã chết: bỏ `V.panel`/`V.g1` (gọi mg, mg_v4 đã gỡ) và lớp bọc `_panel` trong vc_patch, import mg_bds/mg_x, nhánh nhạc `music.py` (không còn file) + dòng nhắc `build_mau.py` trong vucut.py; nền thương hiệu dùng chung font watermark (không nhúng Cinzel 2 lần); `setup` báo lỗi rõ nếu thiếu `engine/` thay vì lặng lẽ chạy mã cũ trong thư mục skill.
- **28/11/2026** — NỀN THƯƠNG HIỆU mặc định cho mọi cảnh đồ hoạ: lớp `#nenbd` (vc.py `_nen_bd`) — bản đồ Đắk Lắk dập chìm trên nền đỏ trầm, vệt vàng chạy quanh ranh giới tỉnh, chấm vàng lan sóng ở Buôn Ma Thuột + Tuy Hòa, phóng chậm; tên LE PHONG VU khắc chìm (Cinzel) ngay dưới khung người nói. Bật đúng các khoảng cảnh đồ hoạ (`mg_real.NBD`, cả `P.cta`); `P.nen(khác 'do')` hoặc `P.nenbd(False)` tắt. Hình thỏi vàng: bỏ đốm vàng lem, vệt sáng nhoè, sàn loang.
- **28/11/2026** — Khung người nói nhỏ: bỏ chữ LE PHONG VU vàng xước + vạch vàng + lớp tối dưới đáy khung (anh Vũ yêu cầu; tên anh chuyển thành chữ khắc chìm trên nền bản đồ thương hiệu, đang duyệt).

- **28/11/2026** — CTA: chừa khoảng dưới nhãn BÌNH LUẬN để dấu chữ nhũ (Ể, Ấ…) không chồng nhãn.
- **28/11/2026** — `P.sat` routes: `{'line':…, 'lab_at':(lon,lat)}` đặt thẻ tuyến ở điểm chọn (vd ra ngoài ranh giới); `{'line':…, 'gold':True}` nhánh vàng không thẻ (vẽ nút giao có nhánh lên xuống); thẻ tuyến tự giữ trong khung.
- **28/11/2026** — `cautruc` + `vungloi` vẽ lại quy mô lớn (anh yêu cầu hoành tráng hơn): mặt bằng gần kín khung, hạt nhân 9 cao ốc + cột sáng, mỗi cực 6 toà, khu thấp tầng quanh lõi, ruộng – cây – xe chạy trên quốc lộ; mỗi khu đô thị mới có cụm cao ốc + nhà phố; tổng diện tích lên góc phải trên.
- **28/11/2026** — `cautruc`: nhãn nút đặt theo `CT_LAB` (không chồng nhau, không đè trục), bỏ mũi tên nam; thêm `dachucnang` (bệ trung tâm toả tới các khối chức năng) thay bảng liệt kê khi anh muốn đồ hoạ.
- **28/11/2026** — Video Ea Knuếc: bản đồ 3D vùng to hơn (khung vừa 640×520, trước 570×470; cận xã 600×500); 4 hình mới trong `mg_real.py`: `quymo` (màn quy mô 2–3 chỉ số), `dansotang` (dân số 2 mốc năm), `cautruc` (sơ đồ 1 hạt nhân – các cực, chế độ `focus` từng nút), `vungloi` (vùng lõi + n khu đô thị mới + tổng diện tích); storyboard mô tả đúng tên hình dùng qua `P.hinh`.
- **27/11/2026** — Gộp bộ máy từ skill vào `engine/`; bỏ bộ hình cũ (mg_x, mg_bds, mg_v4, mg_journey, mg_nganh, mg, mg_dl), bản đồ 2D, các kiểu chuyển cảnh cũ (wipe/whip/zoom/flash/glitch, bộ "phong cách" xoay vòng), nhạc tạo 2 lần; thêm `vc.py kiemtra` và `vc.py nhap` (bản nháp 540p). Dựng lại video M'Drắk: 31/31 khung giống hệt trước khi dọn.
- **27/11/2026** — Viền vàng xước, chuyển cảnh cắt gọn, `P.thu`, bản đồ bay lên (`focus/rise`), nhạc `'tin'` duy nhất.
- **26/11/2026** — Bản đồ 3D, khung kính, CTA nhũ vàng, nhạc `hung_tin` (đã thay).
