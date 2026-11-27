# vucut-tools

Công cụ dựng video talking-head 9:16 cho kênh **Lê Phong Vũ · BĐS Đắk Lắk** (skill `vucut`).
Từ 27/11/2026 **toàn bộ mã dựng nằm trong kho này**; skill `vucut` chỉ còn hướng dẫn (SKILL.md). Sửa công cụ = sửa ở đây.

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `vc.py` | Lệnh chính (`setup · go · cut · sb · build · xem · out · wait · grid · ranh · diadanh · speakers · kiemtra`) và các cảnh mẫu `P.*` dùng trong `scenes.py` |
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

- **27/11/2026** — Gộp bộ máy từ skill vào `engine/`; bỏ bộ hình cũ (mg_x, mg_bds, mg_v4, mg_journey, mg_nganh, mg, mg_dl), bản đồ 2D, các kiểu chuyển cảnh cũ (wipe/whip/zoom/flash/glitch, bộ "phong cách" xoay vòng), nhạc tạo 2 lần; thêm `vc.py kiemtra`. Dựng lại video M'Drắk: 31/31 khung giống hệt trước khi dọn.
- **27/11/2026** — Viền vàng xước, chuyển cảnh cắt gọn, `P.thu`, bản đồ bay lên (`focus/rise`), nhạc `'tin'` duy nhất.
- **26/11/2026** — Bản đồ 3D, khung kính, CTA nhũ vàng, nhạc `hung_tin` (đã thay).
