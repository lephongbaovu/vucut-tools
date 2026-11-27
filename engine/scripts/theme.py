"""vucut · theme.py — BỘ MÀU xoay vòng để các video không giống nhau.
Cách làm: mọi màu hex / rgb(a) trong CSS + HTML dựng ra được phân loại theo sắc độ:
  họ ĐỎ (màu nhấn chính, chữ gradient, panel đỏ, rủi ro)  → sắc NHẤN của bộ màu
  họ VÀNG ĐỒNG (mốc đã xác nhận, điểm nhấn phụ)           → sắc PHỤ của bộ màu
  màu trung tính (đen, trắng, xám) giữ nguyên · màu viết bằng hsl() (sổ hồng, loại đất, dấu) KHÔNG đổi.
Độ sáng giữ nguyên → độ tương phản chữ không đổi giữa các bộ màu."""
import colorsys, re

# tên: (sắc nhấn °, hệ số bão hoà nhấn, bù sáng nhấn, sắc phụ °, bão hoà phụ, mô tả)
THEMES = {
    'docdo':  (356, 1.00, 0.00, 40, 1.00, 'đỏ đô + vàng đồng (gốc) — chính sách, cảnh báo'),
    'thep':   (212, 0.85, 0.06, 38, 1.05, 'xanh thép + hổ phách — hạ tầng, giao thông, quy hoạch'),
    'bazan':  (16,  0.80, 0.04, 46, 0.70, 'đất đỏ bazan + cát — đất đai, nông nghiệp, Tây Nguyên'),
    'reu':    (160, 0.70, 0.05, 44, 1.00, 'xanh rêu ngọc + vàng — cây xanh, sinh thái, nghỉ dưỡng'),
    'muc':    (266, 0.65, 0.10, 34, 0.80, 'mực tím + sâm panh — thị trường, nhận định, tài chính'),
    'bien':   (190, 0.85, 0.04, 14, 0.85, 'xanh biển + san hô — liên kết vùng ra biển, du lịch'),
}
ORDER = list(THEMES)
GOAL_HINT = {'quy hoạch': 'thep', 'hạ tầng': 'thep', 'đất': 'bazan', 'pháp lý': 'bazan', 'thị trường': 'muc', 'biển': 'bien', 'sinh thái': 'reu'}

HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGB = re.compile(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})')


def _map(r, g, b, th):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s < .2 or l < .06 or l > .97: return None          # trung tính
    deg = h * 360
    ha, sa, la, hg, sg = th[:5]
    if deg >= 330 or deg <= 12:                          # họ đỏ
        h2, s2, l2 = ha / 360, min(1, s * sa), min(.95, l + la * (1 - l) if l > .15 else l + la * .3)
    elif 25 <= deg <= 55:                                # họ vàng đồng
        h2, s2, l2 = hg / 360, min(1, s * sg), l
    else:
        return None
    r2, g2, b2 = colorsys.hls_to_rgb(h2, l2, s2)
    return round(r2 * 255), round(g2 * 255), round(b2 * 255)


def apply(text, name):
    """đổi màu trong chuỗi CSS/HTML theo bộ màu `name` ('docdo' = không đổi)"""
    if not name or name == 'docdo': return text
    th = THEMES[name]

    def hx(m):
        v = m.group(1)
        if len(v) == 3: v = ''.join(c * 2 for c in v)
        q = _map(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), th)
        return m.group(0) if q is None else '#%02X%02X%02X' % q

    def rg(m):
        q = _map(int(m.group(1)), int(m.group(2)), int(m.group(3)), th)
        if q is None: return m.group(0)
        pre = m.group(0).split('(')[0]
        return f'{pre}({q[0]},{q[1]},{q[2]}'
    return RGB.sub(rg, HEX.sub(hx, text))


def pick(last=(), hint=''):
    """chọn bộ màu: ưu tiên gợi ý theo chủ đề, nhưng KHÔNG trùng 2 video gần nhất"""
    avoid = set(last[-2:])
    for key, th in GOAL_HINT.items():
        if key in hint.lower() and th not in avoid: return th
    for th in ORDER:
        if th not in avoid and th not in last[-len(ORDER) + 1:]: return th
    return next(th for th in ORDER if th not in avoid)


# NGÔN NGỮ DỰNG theo bộ màu — mỗi video một "giọng" hình nhất quán, khác video trước:
#   kw    = kiểu chữ TỪ KHOÁ (serif nghiêng Playfair | sans IN HOA Montserrat 900)
#   entry = cách từ khoá vào (blur đập · slide quét mở · drop rơi nảy · rise trồi · ink mực loang)
#   wipe  = chuyển cảnh chính (bar thanh chéo · scan quét bản vẽ · torn mép đất xé · iris vòng tròn · blinds rèm · wave sóng)
#   sfx   = âm của chuyển cảnh chính
STYLE = {
    'docdo': dict(kw='serif', entry='blur',  wipe='bar',    sfx='whoosh'),
    'thep':  dict(kw='sans',  entry='slide', wipe='scan',   sfx='scan'),
    'bazan': dict(kw='serif', entry='drop',  wipe='torn',   sfx='thud'),
    'reu':   dict(kw='sans',  entry='rise',  wipe='iris',   sfx='air'),
    'muc':   dict(kw='serif', entry='ink',   wipe='blinds', sfx='shutter'),
    'bien':  dict(kw='sans',  entry='slide', wipe='wave',   sfx='wash'),
}
