"""vucut-tools · mg_real.py — BỘ ĐỒ HOẠ CHÂN THỰC (khối 3D, ánh sáng, bóng đổ, chất liệu) trên bố cục tối giản: nhãn nhỏ + tiêu đề căn trái + số lớn.
Dùng P.hinh(a, b, R.tên, …) hoặc cảnh mẫu P.so / P.ds / P.vanban. Chỉ hiện số có trong lời (chuỗi kiểu Việt '12.000' '7,2'); hình minh hoạ tự ghi chú.
Tham số mỗi hình: dòng docstring của hàm (python3 -c "import mg_real as R; help(R.tên)"). Hầu hết nhận kicker= (nhãn nhỏ) và title= (tiêu đề).
CẢNH MẪU   so · ds · vanban   (không tính vào 100 hình)
— 100 HÌNH · 10 CHỦ ĐỀ × 10 —
PHÁP LÝ     sohong · hopdong · thuephi · thutuc · canhbao · tranhchap · chuyenmd(t0,t_conv,from_,to) · tachthua(t0,t_split,parts,area) · denbu(t0,value,unit) · gpxd(t0,t_ok,stamp)
QUY HOẠCH   khudothi · tyle · matdo · sapnhap · mocqh · xoatreo · phankhu(zones=[(NHÃN,'o'|'tm'|'cx'|'cn'|'gd',t)]) · vanhdai(t0,t_ring,tag) · dothimoi(t0,t_grow,tag) · congvien(t0,value,unit)
HẠ TẦNG     caotoc · tiendo · duongsat · cau · thoigian · anhhuong · sanbay(t0,t_plane,tag) · nutgiao(t0,tag) · dien(t0,value,unit) · cangbien(t0,t_ship,tag)
THỊ TRƯỜNG  chukytt · cungcau · laisuat · nhietke(chot='') · giathue · khanang(t0,t_gap,gap) · giaodich(t0,value,unit) · giadat(rows=[(KHU,giá,t)],unit) · tonkho(t0,value,unit) · kenhdautu(items=[(TÊN,'12%',t)])
NHÀ Ở – DỰ ÁN noxh(t0,value,unit,tag) · mocnam(steps,value,unit) · canho(t0,area,rooms) · nhapho(t0,floors,n,tag) · bietthu(t0,tag) · datnen(t0,lots,tag,area) · bangiao(t0,t_key) · xaydung(t0,pct,floors) · vaymua(t0,ltv,years) · thanhtoan(steps=[(ĐỢT,'30%',t)])
KINH TẾ     vang|vondt · tangtruong · dongvon · chiso · ngansach(t0,value,unit) · fdi(t0,value,unit,sources) · xuatkhau(t0,value,unit,item) · thunhap(t0,value,unit) · danso(t0,value,unit) · dautucong(t0,pct)
NÔNG NGHIỆP caphe|sanluong · giansan · vungtrong · saurieng(t0,value,unit) · hotieu · caosu · traibo · tuoinuoc(t0,tag) · chebien(t0,item,value,unit) · nhakinh(t0,value,unit)
LOGISTICS   cangcan · mangluoi · chiphi · khobai(t0,value,unit) · vantai(t0,from_,to,dist) · thongquan(t0,t_ok,tag) · hangkhong(t0,value,unit) · giaohang(t0,value,unit) · chuoicu(steps=[(NÚT,t)]) · kholanh(t0,tag)
CÔNG NGHIỆP nhamay · lapday · vieclam · khucn(t0,value,unit,tag) · tuabingio(t0,value,unit) · robot(t0,tag) · vatlieu(t0,items) · xuongthue(t0,value,unit) · datacenter(t0,tag) · xulynuoc(t0,tag)
TM – DỊCH VỤ banle · cuakhau · tmdt · dulich · luutru · tienich · tttm(t0,tag) · khachsan(t0,value,unit,tag) · benhvien(t0,value,unit,tag) · truonghoc(t0,value,unit,tag)
Mọi số/chữ chỉ hiện khi truyền vào (lấy từ lời); value có → số lớn đếm + tiếng máy đếm tự gắn."""
import math, random, re, json

# ---------------------------------------------------------------- lõi GSAP / SVG
def _v(x):
    if isinstance(x, dict): return '{' + ','.join(f'{k if k.isidentifier() else repr(k)}:{_v(v)}' for k, v in x.items()) + '}'
    if isinstance(x, str): return "'" + x.replace("'", "\\'") + "'"
    if isinstance(x, bool): return 'true' if x else 'false'
    if isinstance(x, (list, tuple)): return '[' + ','.join(_v(q) for q in x) + ']'
    return f'{x:.3f}'.rstrip('0').rstrip('.') if isinstance(x, float) else str(x)
def _o(p):
    o = p.get('transformOrigin')
    if isinstance(o, str) and re.fullmatch(r'-?[\d.]+px -?[\d.]+px', o): p.pop('transformOrigin'); p['svgOrigin'] = o.replace('px', '')
    return p
def S(sel, t, **p): return f"tl.set('{sel}',{_v(_o(p))},{t:.2f});"
def T(sel, t, **p): return f"tl.to('{sel}',{_v(_o(p))},{t:.2f});"
def _vis(i, a, b): return [S(f'#{i}', a, opacity=1), S(f'#{i}', b, opacity=0)]
def _wrap(i, name, svg, light=False):
    return (f'<div class="vc mg" data-mg="{name}" id="{i}" style="left:0;top:0;width:720px;height:1280px;z-index:8;filter:none">'
            f'<svg viewBox="0 0 720 1280" width="720" height="1280" style="position:absolute;left:0;top:0;overflow:visible">{svg}</svg></div>')

BG, FG, MUT, HAIR, AC = '#0d0d0f', '#f4f4f5', 'rgba(244,244,245,.48)', 'rgba(244,244,245,.14)', 'var(--g)'
UP, DN = '#3ddc84', '#ff5a5f'


def _t(x, y, s, size, fill=FG, anchor='start', cls='', w=700, ls=0, op=1):
    return (f'<text class="{cls}" x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="VCB" font-weight="{w}" font-size="{size}" '
            f'fill="{fill}" fill-opacity="{op}" letter-spacing="{ls}">{s}</text>')
def _w(s, size): return sum(.68 if c.isdigit() else (.3 if c in ',.' else .66) for c in str(s)) * size
def _rv(sel, t, dy=26, d=.7): return S(sel, 0, y=dy, opacity=0) + T(sel, t, y=0, opacity=1, duration=d, ease='expo.out')

def _head(kicker, title):
    s = ''
    if kicker: s += f'<g class="kk"><rect x="60" y="160" width="28" height="4" fill="{AC}"/>{_t(100, 168, kicker, 19, AC, w=800, ls=3)}</g>'
    if title:
        L, cur = [], ''
        for wd in title.split():
            if len(cur + ' ' + wd) > 24 and cur: L.append(cur); cur = wd
            else: cur = (cur + ' ' + wd).strip()
        L.append(cur)
        s += ''.join(f'<g class="hd{k}">{_t(60, 226 + k * 52, l, 44, w=800)}</g>' for k, l in enumerate(L[:2]))
    return s
def _headj(i, a, title):
    return [_rv(f'#{i} .kk', a + .05, 14, .5)] + [_rv(f'#{i} .hd{k}', a + .12 + k * .08) for k in range(2)]
def _num(i, cls, t, v, d=1.1):
    s = str(v).strip(); p = None
    if s and s[0].isdigit() and all(c.isdigit() or c in '.,' for c in s):
        if ',' in s: ip, dp = s.split(',', 1); p = (float(ip.replace('.', '') + '.' + dp), len(dp))
        elif '.' in s and all(len(x) == 3 for x in s.split('.')[1:]): p = (float(s.replace('.', '')), 0)
        else: p = (float(s), len(s.split('.')[1]) if '.' in s else 0)
    if not p: return _rv(f'#{i} .{cls}', t)
    return ("(function(){var n=document.querySelector('#%s .%s'),o={v:0},f=function(){var s=o.v.toFixed(%d).split('.');"
            "s[0]=s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');n.textContent=s.join(',');};"
            "tl.set(o,{v:0,onUpdate:f},0);tl.to(o,{v:%s,duration:%s,ease:'expo.out',onUpdate:f},%.2f);})();" % (i, cls, p[1], p[0], d, t)) + S(f'#{i} .{cls}', 0, opacity=0) + T(f'#{i} .{cls}', t, opacity=1, duration=.2)
def _src(s): return _t(60, 668, s, 16, MUT, w=600) if s else ''
def _out(i, a, b, name, s, j):
    j += [T(f'#{i} .ct', a, y=-8, duration=max(.1, b - a), ease='none'), S(f'#{i}bg', a, opacity=1), S(f'#{i}bg', b, opacity=0)]
    bg = f'<div class="vc" id="{i}bg" style="left:0;top:0;width:720px;height:1280px;background:{BG};z-index:7;opacity:0;filter:none"></div>'
    return bg + _wrap(i, name, f'<g class="ct">{s}</g>', False)



def _defs(i):
    return (f'<defs><filter id="{i}sh" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#000" flood-opacity=".6"/></filter>'
            f'<filter id="{i}sf" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>'
            f'<filter id="{i}nz" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="3"/>'
            f'<feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .55 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>'
            f'<filter id="{i}gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
def _lg(id_, c0, c1, x2=0, y2=1, o0=1, o1=1):
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{c0}" stop-opacity="{o0}"/><stop offset="1" stop-color="{c1}" stop-opacity="{o1}"/></linearGradient>'
def _rg(id_, c0, c1, cx=.35, cy=.3):
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r=".75"><stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></radialGradient>'
def _pt(P): return ' '.join(f'{x:.1f},{y:.1f}' for x, y in P)
def _iso(ox, oy, s):
    return lambda x, y, z=0: (ox + (x - y) * .866 * s, oy + (x + y) * .5 * s - z * s)
def _box(I, x, y, w, d, h, top, left, right, cls='', extra=''):
    T_ = [I(x, y, h), I(x + w, y, h), I(x + w, y + d, h), I(x, y + d, h)]
    L_ = [I(x, y + d, 0), I(x + w, y + d, 0), I(x + w, y + d, h), I(x, y + d, h)]
    R_ = [I(x + w, y, 0), I(x + w, y + d, 0), I(x + w, y + d, h), I(x + w, y, h)]
    return (f'<g class="{cls}"><polygon points="{_pt(L_)}" fill="{left}"/><polygon points="{_pt(R_)}" fill="{right}"/>'
            f'<polygon points="{_pt(T_)}" fill="{top}"/>{extra}</g>')


# ================================================================ SỔ HỒNG ==
def sohong(i, a, b, t0, t_hi=None, fields=(), hi=0, stamp=True, kicker='PHÁP LÝ', source=''):
    """giấy chứng nhận (sổ hồng) giấy thật: trượt lên, dòng thông tin hiện dần, t_hi tô dòng `hi`, mộc đỏ. fields=[('Thửa đất số', '125'), …] ≤4"""
    X0, Y0, W, H = 150, 205, 420, 450; cx = X0 + W / 2
    gu = ''.join(f'<path d="M{X0} {Y0 + 20 + k * 14} q26 -9 52 0 t52 0 t52 0 t52 0 t52 0 t52 0 t52 0 t52 0" fill="none" stroke="hsl(345,55%,70%)" stroke-width=".8" stroke-opacity=".45"/>' for k in range(31))
    s = _defs(i) + _lg(f'{i}pp', 'hsl(350,70%,95%)', 'hsl(343,55%,86%)', 1, 1) + _rg(f'{i}em', 'hsl(48,95%,62%)', 'hsl(36,85%,38%)') + '</defs>'
    s += _head(kicker, '')
    s += (f'<g class="pp" transform="rotate(-3 {cx} {Y0 + H / 2})"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="6" fill="url(#{i}pp)" filter="url(#{i}sh)"/>'
          f'<clipPath id="{i}cl"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="6"/></clipPath><g clip-path="url(#{i}cl)">{gu}</g>'
          f'<rect x="{X0 + 12}" y="{Y0 + 12}" width="{W - 24}" height="{H - 24}" fill="none" stroke="hsl(350,60%,45%)" stroke-width="2"/>'
          f'<rect x="{X0 + 18}" y="{Y0 + 18}" width="{W - 36}" height="{H - 36}" fill="none" stroke="hsl(350,60%,45%)" stroke-width=".8"/>'
          + _t(cx, Y0 + 46, 'CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM', 12, 'hsl(350,55%,30%)', 'middle', w=800)
          + f'<circle cx="{cx}" cy="{Y0 + 92}" r="28" fill="url(#{i}em)" stroke="hsl(356,70%,40%)" stroke-width="3"/>'
          f'<path d="M{cx} {Y0 + 74} l5 12 h13 l-10 8 l4 13 l-12 -8 l-12 8 l4 -13 l-10 -8 h13 z" fill="hsl(356,80%,45%)"/>'
          + _t(cx, Y0 + 158, 'GIẤY CHỨNG NHẬN', 28, 'hsl(356,75%,40%)', 'middle', w=900)
          + _t(cx, Y0 + 182, 'QUYỀN SỬ DỤNG ĐẤT, QUYỀN SỞ HỮU TÀI SẢN', 11, 'hsl(350,45%,28%)', 'middle', w=700)
          + _t(cx, Y0 + 198, 'GẮN LIỀN VỚI ĐẤT', 11, 'hsl(350,45%,28%)', 'middle', w=700))
    rows = list(fields)[:4] or [('', '')] * 4
    for k, (lab, val) in enumerate(rows):
        y = Y0 + 238 + k * 36
        s += f'<rect class="hb{k}" x="{X0 + 30}" y="{y - 24}" width="{W - 60}" height="34" rx="4" fill="hsl(48,100%,60%)" fill-opacity=".55"/>'
        if lab: s += f'<g class="f{k}">' + _t(X0 + 38, y, lab + ':', 17, 'hsl(350,35%,25%)', w=600) + _t(X0 + W - 38, y, val, 19, '#1b1b1b', 'end', w=800) + '</g>'
        else: s += f'<rect class="f{k}" x="{X0 + 38}" y="{y - 12}" width="{W - 90 - (k % 2) * 70}" height="9" rx="4" fill="hsl(350,30%,40%)" fill-opacity=".25"/>'
        s += f'<path d="M{X0 + 36} {y + 8} H{X0 + W - 36}" stroke="hsl(350,40%,50%)" stroke-opacity=".35" stroke-dasharray="2 4"/>'
    sx, sy = X0 + W - 86, Y0 + H - 54
    if stamp:
        s += (f'<g class="sl" opacity=".85"><circle cx="{sx}" cy="{sy}" r="44" fill="none" stroke="hsl(356,85%,46%)" stroke-width="5"/>'
              f'<circle cx="{sx}" cy="{sy}" r="34" fill="none" stroke="hsl(356,85%,46%)" stroke-width="1.5"/>'
              f'<path d="M{sx} {sy - 16} l5 11 h12 l-9 7 l3 12 l-11 -7 l-11 7 l3 -12 l-9 -7 h12 z" fill="hsl(356,85%,46%)"/></g>'
              f'<path class="sg" d="M{X0 + 60} {sy + 6} c14 -26 24 14 38 -6 s16 -20 28 4 s20 8 34 -12" fill="none" stroke="hsl(225,70%,30%)" stroke-width="2.5" stroke-linecap="round" pathLength="1"/>')
    s += f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="6" fill="#fff" filter="url(#{i}nz)" opacity=".5"/></g>'
    s += _t(60, 690, source or 'hình minh hoạ', 15, MUT, w=600)
    j = _vis(i, a, b) + _headj(i, a, '') + [S(f'#{i} .pp', 0, y=120, rotation=6, opacity=0, svgOrigin=f'{cx} {Y0 + H}'),
                                            T(f'#{i} .pp', t0, y=0, rotation=0, opacity=1, duration=.9, ease='expo.out', svgOrigin=f'{cx} {Y0 + H}'),
                                            S(f'#{i} [class^=hb]', 0, scaleX=0, transformOrigin='0% 50%')]
    for k in range(len(rows)): j.append(_rv(f'#{i} .f{k}', t0 + .5 + k * .18, 10, .5))
    if t_hi is not None: j.append(T(f'#{i} .hb{hi}', t_hi, scaleX=1, duration=.5, ease='expo.out'))
    if stamp:
        ts = (t_hi or t0 + 1.2) + .6
        j += [S(f'#{i} .sl', 0, opacity=0, scale=1.8, svgOrigin=f'{sx} {sy}'), T(f'#{i} .sl', ts, opacity=.85, scale=1, duration=.18, ease='power4.in', svgOrigin=f'{sx} {sy}'),
              S(f'#{i} .sg', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .sg', ts - .5, strokeDashoffset=0, duration=.45)]
    j.append(T(f'#{i} .pp', t0 + .9, y=-6, duration=max(.1, b - t0 - .9), ease='none'))
    return _out(i, a, b, 'r_sohong', s, j), j, [(t0, 'paper')] + ([(t_hi, 'pen')] if t_hi else []) + ([((t_hi or t0 + 1.2) + .6, 'stamp')] if stamp else [])


# ================================================================ CAO TỐC ==
def caotoc(i, a, b, t0, sign=('BUÔN MA THUỘT', '45 km'), kicker='HẠ TẦNG', title='', source=''):
    """phối cảnh cao tốc lúc hoàng hôn: vạch chạy, xe đi, biển xanh trên giá long môn"""
    X0, Y0, W, H = 60, 300 if title else 230, 600, 380; HZ = Y0 + 150; VX = 380
    s = _defs(i) + _lg(f'{i}sk', 'hsl(215,45%,22%)', 'hsl(28,85%,62%)') + _lg(f'{i}rd', '#2a2c30', '#43464c') + _lg(f'{i}h1', 'hsl(160,25%,26%)', 'hsl(160,25%,14%)') \
        + _lg(f'{i}h2', 'hsl(140,30%,30%)', 'hsl(140,35%,16%)') + _lg(f'{i}sn', 'hsl(150,65%,30%)', 'hsl(150,70%,22%)') + f'<radialGradient id="{i}sun"><stop offset="0" stop-color="hsl(40,100%,80%)" stop-opacity=".9"/><stop offset=".25" stop-color="hsl(32,100%,65%)" stop-opacity=".5"/><stop offset="1" stop-color="hsl(25,100%,55%)" stop-opacity="0"/></radialGradient>' + _lg(f'{i}tk', '#e8e9ec', '#9da3ab') + '</defs>'
    s += _head(kicker, title)
    s += f'<clipPath id="{i}cc"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="22"/></clipPath><g class="cd" filter="url(#{i}sh)"><g clip-path="url(#{i}cc)">'
    s += f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" fill="url(#{i}sk)"/><circle cx="{VX + 120}" cy="{HZ - 8}" r="30" fill="hsl(38,100%,75%)" filter="url(#{i}sf)"/>'
    s += f'<circle cx="{VX + 120}" cy="{HZ - 8}" r="110" fill="url(#{i}sun)"/>'
    for k, (cx_, cy_, sc) in enumerate(((140, Y0 + 50, 1), (420, Y0 + 34, .8), (600, Y0 + 70, .9), (300, Y0 + 90, .6))):
        s += f'<g class="cl{k}" opacity=".55">' + ''.join(f'<ellipse cx="{cx_ + dx * sc:.0f}" cy="{cy_ + dy * sc:.0f}" rx="{rx * sc:.0f}" ry="{ry * sc:.0f}" fill="hsl(25,60%,85%)" filter="url(#{i}sf)"/>' for dx, dy, rx, ry in ((0, 0, 60, 16), (40, -10, 44, 18), (-40, 4, 40, 12), (80, 6, 30, 10))) + '</g>'
    s += f'<path d="M{X0} {HZ - 30} L100 {HZ - 70} L180 {HZ - 52} L260 {HZ - 92} L360 {HZ - 60} L470 {HZ - 98} L560 {HZ - 64} L{X0 + W} {HZ - 80} V{HZ} H{X0} Z" fill="hsl(230,25%,45%)" opacity=".55"/>'
    s += f'<path d="M{X0} {HZ} L130 {HZ - 46} L230 {HZ - 20} L330 {HZ - 58} L450 {HZ - 24} L560 {HZ - 52} L{X0 + W} {HZ - 18} V{HZ + 20} H{X0} Z" fill="url(#{i}h1)" opacity=".9"/>'
    s += f'<rect x="{X0}" y="{HZ}" width="{W}" height="{H - 150}" fill="url(#{i}h2)"/>'
    road = [(VX - 12, HZ), (VX + 12, HZ), (X0 + W + 60, Y0 + H), (X0 - 60, Y0 + H)]
    s += f'<polygon points="{_pt(road)}" fill="url(#{i}rd)"/><polygon points="{_pt(road)}" fill="#fff" filter="url(#{i}nz)" opacity=".35"/>'
    s += f'<path d="M{VX - 10} {HZ} L{X0 - 30} {Y0 + H} M{VX + 10} {HZ} L{X0 + W + 30} {Y0 + H}" stroke="#e9e3d0" stroke-width="5" opacity=".9"/>'
    for k, xb in enumerate((X0 + 160, X0 + 440)):
        s += f'<path class="ln" d="M{VX + (-4 if k == 0 else 4)} {HZ} L{xb} {Y0 + H}" stroke="#fff" stroke-width="7" stroke-dasharray="22 26" opacity=".85"/>'
    for side in (-1, 1):
        x0r = VX + side * 16; s += f'<path d="M{x0r} {HZ - 3} L{VX + side * 380} {Y0 + H - 70}" stroke="#c9cdd3" stroke-width="4"/>'
        for q in range(9):
            u = (q / 8) ** 1.8; x = x0r + (side * 364) * u; y = HZ - 3 + (H - 220) * u
            s += f'<rect x="{x - 1:.0f}" y="{y:.0f}" width="{2 + 4 * u:.1f}" height="{4 + 22 * u:.1f}" fill="#9aa0a8"/>'
        for q in range(6):
            u = ((q + .5) / 6) ** 1.6; x = VX + side * (60 + 330 * u); y = HZ + 6 + (H - 210) * u; h = 14 + 120 * u
            s += f'<ellipse cx="{x + side * 10:.0f}" cy="{y:.0f}" rx="{h * .32:.0f}" ry="{h * .08:.0f}" fill="#000" opacity=".35"/><path d="M{x:.0f} {y:.0f} l{-h * .26:.0f} 0 l{h * .26:.0f} {-h:.0f} l{h * .26:.0f} {h:.0f} z" fill="hsl(150,35%,{18 + 8 * u:.0f}%)"/>'
    s += (f'<g opacity=".8"><rect x="{X0}" y="{HZ + 6}" width="{W}" height="7" fill="hsl(220,10%,55%)"/><rect x="{X0}" y="{HZ + 13}" width="{W}" height="3" fill="hsl(220,10%,30%)"/>'
          + ''.join(f'<rect x="{x}" y="{HZ + 16}" width="5" height="12" fill="hsl(220,10%,40%)"/>' for x in (VX - 120, VX - 40, VX + 40, VX + 120)) + '</g>')
    for side in (-1, 1):
        for q in range(5):
            u = ((q + .6) / 5) ** 1.7; x = VX + side * (26 + 300 * u); yb = HZ + 4 + (H - 230) * u; ph = 16 + 170 * u
            s += (f'<path d="M{x:.0f} {yb:.0f} V{yb - ph:.0f} h{-side * ph * .22:.0f}" stroke="hsl(220,8%,62%)" stroke-width="{1 + 3 * u:.1f}" fill="none"/>'
                  f'<circle cx="{x - side * ph * .22:.0f}" cy="{yb - ph + 2:.0f}" r="{2 + 5 * u:.1f}" fill="hsl(45,100%,85%)" filter="url(#{i}gl)"/>')
    gy = HZ - 70
    bw = max(240, int(max(len(sign[0]), len(sign[1])) * 12.5) + 36); hb = bw // 2   # biển tự nới theo chữ dài
    c2 = 'hsl(48,100%,70%)' if any(ch.isdigit() for ch in sign[1]) else '#fff'      # dòng 2: vàng nếu là khoảng cách, trắng nếu là tên
    s += (f'<g class="gt"><rect x="{VX - hb - 30}" y="{gy}" width="8" height="78" fill="#7d838c"/><rect x="{VX + hb + 22}" y="{gy}" width="8" height="78" fill="#7d838c"/>'
          f'<rect x="{VX - hb - 34}" y="{gy - 8}" width="{bw + 68}" height="10" fill="#8d939c"/><rect x="{VX - hb}" y="{gy - 60}" width="{bw}" height="58" rx="6" fill="url(#{i}sn)" stroke="#fff" stroke-width="2.5"/>'
          + _t(VX, gy - 36, sign[0], 18, '#fff', 'middle', w=800) + _t(VX, gy - 13, sign[1], 18, c2, 'middle', w=800) + '</g>')
    for k, (lx, col) in enumerate(((VX - 70, 'hsl(0,0%,92%)'), (VX + 80, 'hsl(210,60%,45%)'))):
        s += (f'<g class="car{k}"><ellipse cx="{lx}" cy="{Y0 + H - 22}" rx="58" ry="10" fill="#000" opacity=".45"/><path d="M{lx - 52} {Y0 + H - 30} v-30 q0 -12 12 -14 l14 -24 q4 -6 12 -6 h28 q8 0 12 6 l14 24 q12 2 12 14 v30 z" fill="{col}"/>'
              f'<path d="M{lx - 26} {Y0 + H - 70} l10 -20 h32 l10 20 z" fill="#1d2a38"/><rect x="{lx - 50}" y="{Y0 + H - 54}" width="18" height="8" rx="3" fill="hsl(0,100%,55%)" filter="url(#{i}gl)"/>'
              f'<rect x="{lx + 32}" y="{Y0 + H - 54}" width="18" height="8" rx="3" fill="hsl(0,100%,55%)" filter="url(#{i}gl)"/>'
              f'<rect x="{lx - 14}" y="{Y0 + H - 46}" width="28" height="10" rx="2" fill="#f2f2f2"/><rect x="{lx - 48}" y="{Y0 + H - 32}" width="16" height="10" rx="3" fill="#111"/><rect x="{lx + 32}" y="{Y0 + H - 32}" width="16" height="10" rx="3" fill="#111"/>'
              f'<path d="M{lx - 22} {Y0 + H - 86} l6 -12 h18" stroke="#fff" stroke-opacity=".35" stroke-width="2" fill="none"/></g>')
    tx_ = VX + 30; ty_ = HZ + 70
    s += (f'<g class="tk"><rect x="{tx_ - 22}" y="{ty_ - 44}" width="44" height="40" rx="2" fill="url(#{i}tk)"/><rect x="{tx_ - 22}" y="{ty_ - 6}" width="44" height="5" fill="#333"/>'
          f'<rect x="{tx_ - 20}" y="{ty_ - 8}" width="6" height="3" fill="hsl(0,100%,55%)" filter="url(#{i}gl)"/><rect x="{tx_ + 14}" y="{ty_ - 8}" width="6" height="3" fill="hsl(0,100%,55%)" filter="url(#{i}gl)"/></g>')
    s += f'</g></g><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="22" fill="none" stroke="#fff" stroke-opacity=".08"/>'
    s += _t(60, Y0 + H + 26, source or 'hình minh hoạ', 15, MUT, w=600)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .cd', a + .1, 30, .8), T(f'#{i} .ln', a, strokeDashoffset=-48 * (b - a) * 2.2, duration=b - a, ease='none'),
                                                S(f'#{i} .gt', 0, scale=.35, opacity=0, svgOrigin=f'{VX} {HZ}'), T(f'#{i} .gt', t0, scale=1, opacity=1, duration=1.2, ease='power2.in', svgOrigin=f'{VX} {HZ}'),
                                                T(f'#{i} .gt', t0 + 1.2, scale=1.12, duration=max(.1, b - t0 - 1.2), ease='none', svgOrigin=f'{VX} {HZ}')]
    j += [T(f'#{i} .cl{k}', a, x=(14 + 8 * k) * (b - a) * (1 if k % 2 else -1), duration=b - a, ease='none') for k in range(4)]
    j += [T(f'#{i} .tk', a, scale=.55, y=-26, x=-8, duration=b - a, ease='none', svgOrigin=f'{tx_} {ty_}')]
    for k in range(2):
        lx = (VX - 70, VX + 80)[k]
        j += [T(f'#{i} .car{k}', t0 + .3 + k * .5, scale=.08, x=(VX - lx) * .9, y=-(H - 160), opacity=.2, duration=2.4, ease='power2.in', svgOrigin=f'{lx} {Y0 + H - 22}')]
    return _out(i, a, b, 'r_caotoc', s, j), j, [(t0, 'whoosh'), (t0 + .3, 'air')]


# ============================================================== KHU ĐÔ THỊ ==
def _winL(I, x, y, w, d, h, cols, rows, c='hsl(205,40%,30%)', lit=()):
    """cửa sổ mặt trái (mặt y+d)"""
    s = ''; dw = w / cols; dz = h / (rows + .4)
    for r in range(rows):
        for q in range(cols):
            x0, z0 = x + q * dw + dw * .22, .25 * dz + r * dz + dz * .2; col = 'hsl(45,95%,70%)' if (r, q) in lit else c
            s += f'<polygon points="{_pt([I(x0, y + d, z0), I(x0 + dw * .56, y + d, z0), I(x0 + dw * .56, y + d, z0 + dz * .55), I(x0, y + d, z0 + dz * .55)])}" fill="{col}"/>'
    return s
def _winR(I, x, y, w, d, h, cols, rows, c='hsl(205,40%,24%)', lit=()):
    s = ''; dd = d / cols; dz = h / (rows + .4)
    for r in range(rows):
        for q in range(cols):
            y0, z0 = y + q * dd + dd * .22, .25 * dz + r * dz + dz * .2; col = 'hsl(45,95%,62%)' if (r, q) in lit else c
            s += f'<polygon points="{_pt([I(x + w, y0, z0), I(x + w, y0 + dd * .56, z0), I(x + w, y0 + dd * .56, z0 + dz * .55), I(x + w, y0, z0 + dz * .55)])}" fill="{col}"/>'
    return s


def khudothi(i, a, b, t0, t_hi=None, tag='', kicker='QUY HOẠCH', title='', source=''):
    """khu đô thị 3D chi tiết: toà cao tầng, nhà phố có cửa sổ/ban công, công viên hồ nước, đường có vỉa hè, vạch qua đường, đèn đường, xe chạy; t_hi: lô sáng vàng + nhãn"""
    I = _iso(360, 336 if title else 280, 30)
    s = (_defs(i) + _rg(f'{i}tr', 'hsl(105,55%,55%)', 'hsl(130,50%,20%)') + _rg(f'{i}wt', 'hsl(195,70%,62%)', 'hsl(205,70%,32%)', .4, .35)
         + _lg(f'{i}gw', 'hsl(205,30%,82%)', 'hsl(210,25%,62%)') + '</defs>' + _head(kicker, title))
    P4 = lambda x0, y0, x1, y1, z=0: _pt([I(x0, y0, z), I(x1, y0, z), I(x1, y1, z), I(x0, y1, z)])
    g = [I(0, 0), I(10, 0), I(10, 10), I(0, 10)]
    s += (f'<g class="gd"><polygon points="{_pt([(x, y + 16) for x, y in g])}" fill="#000" opacity=".55" filter="url(#{i}sf)"/>'
          f'<polygon points="{_pt([I(0, 10), I(10, 10), I(10, 10, -.4), I(0, 10, -.4)])}" fill="hsl(30,22%,24%)"/>'
          f'<polygon points="{_pt([I(10, 0), I(10, 10), I(10, 10, -.4), I(10, 0, -.4)])}" fill="hsl(30,22%,16%)"/>'
          f'<polygon points="{_pt(g)}" fill="hsl(100,28%,36%)"/><polygon points="{_pt(g)}" fill="#fff" filter="url(#{i}nz)" opacity=".28"/>'
          f'<polygon points="{P4(4.1, 0, 5.9, 10)}" fill="hsl(40,10%,70%)"/><polygon points="{P4(0, 4.1, 10, 5.9)}" fill="hsl(40,10%,70%)"/></g>')
    s += (f'<g class="rd"><polygon points="{P4(4.4, 0, 5.6, 10)}" fill="#34373c"/><polygon points="{P4(0, 4.4, 10, 5.6)}" fill="#34373c"/>'
          f'<polygon points="{P4(4.4, 4.4, 5.6, 5.6)}" fill="#3a3d42"/>'
          f'<path d="M{_pt([I(5, 0), I(5, 4.2)])} M{_pt([I(5, 5.8), I(5, 10)])} M{_pt([I(0, 5), I(4.2, 5)])} M{_pt([I(5.8, 5), I(10, 5)])}" stroke="hsl(48,90%,60%)" stroke-width="1.4" stroke-dasharray="6 6"/>'
          + ''.join(f'<polygon points="{P4(4.45 + k * .14, 3.75, 4.52 + k * .14, 4.3)}" fill="#eee"/><polygon points="{P4(5.7, 4.45 + k * .14, 6.25, 4.52 + k * .14)}" fill="#eee"/>' for k in range(8))
          + '</g>')
    items = []
    # toà cao tầng (góc sau)
    for (x, y, w, d, h) in ((.8, .8, 1.4, 1.4, 2.5), (2.5, .8, 1.3, 1.3, 1.9)):
        items.append((x + y + w + d, 'tower', x, y, w, d, h))
    random.seed(11)
    for qx, qy in ((6.2, .3), (6.2, 6.2), (.3, 2.6)):
        rows = ((0, 1.7),) if qy == 2.6 else ((0, 1.7), (2.0, 1.7))
        for ry, dd in rows:
            for c in range(4):
                if qy == 6.2 and ry == 0 and c == 0: continue
                if qy == 2.6 and c > 3: continue
                items.append((qx + c * .92 + qy + ry + 1.3, 'house', qx + c * .92, qy + ry, .82, 1.3, 1.1 + random.choice((0, .35, .7)), random.choice((8, 25, 205, 32))))
    # công viên (trước trái)
    park = f'<polygon points="{P4(.3, 6.2, 4.0, 9.7)}" fill="hsl(115,40%,42%)"/><ellipse class="po" cx="{I(1.8, 8.0)[0]:.0f}" cy="{I(1.8, 8.0)[1]:.0f}" rx="56" ry="26" fill="url(#{i}wt)"/>'
    park += f'<path d="M{_pt([I(.3, 6.6), I(2.6, 7.2), I(3.6, 9.7)])}" stroke="hsl(40,30%,78%)" stroke-width="5" fill="none" stroke-linecap="round"/>'
    for k in range(9):
        p = (.6 + (k % 3) * 1.2 + (k // 3) * .3, 6.5 + (k // 3) * 1.15)
        if 1.0 < p[0] < 2.6 and 7.4 < p[1] < 8.6: continue
        items.append((p[0] + p[1], 'tree', p[0], p[1], .9 + (k % 3) * .15))
    for k in range(6): items.append((4.0 + .6 + k * 1.6 + 0, 'tree', 4.0, .6 + k * 1.6, .8)) if not (3.6 < .6 + k * 1.6 < 6.4) else None
    for k in range(4): items.append((6.1 + 3.9 + k * .0, 'lamp', 6.1, 6.3 + k * .95, 0)) if k < 4 else None
    for k in range(4): items.append((.4 + k * .95 + 4.05, 'lamp', .4 + k * 1.0, 4.05, 0))
    items.sort(key=lambda q: q[0])
    s += f'<g class="pk">{park}</g>'
    for it in items:
        kind = it[1]
        if kind == 'tower':
            _, _, x, y, w, d, h = it
            win = _winL(I, x, y, w, d, h, 4, 8, lit={(1, 2), (4, 0), (6, 3), (2, 1)}) + _winR(I, x, y, w, d, h, 4, 8, lit={(3, 1), (5, 2), (0, 3)})
            roof = (f'<polygon points="{P4(x + .1, y + .1, x + w - .1, y + d - .1, h + .02)}" fill="hsl(210,10%,70%)"/>'
                    f'<polygon points="{_pt([I(x + .4, y + .4, h), I(x + .8, y + .4, h), I(x + .8, y + .8, h + .3), I(x + .4, y + .8, h + .3)])}" fill="hsl(210,10%,55%)"/>'
                    f'<circle cx="{I(x + w - .4, y + .5, h + .25)[0]:.0f}" cy="{I(x + w - .4, y + .5, h + .25)[1]:.0f}" r="5" fill="hsl(0,0%,85%)"/>')
            s += _box(I, x, y, w, d, h, 'hsl(210,12%,82%)', f'url(#{i}gw)', 'hsl(212,18%,50%)', 'bd', win + roof)
        elif kind == 'house':
            _, _, x, y, w, d, h, hue = it
            win = _winL(I, x, y, w, d, h, 2, 2, 'hsl(205,35%,28%)', lit={(0, 1)}) + _winR(I, x, y, w, d, h, 3, 2, 'hsl(205,35%,22%)')
            bal = f'<polygon points="{_pt([I(x + .05, y + d + .12, h * .5), I(x + w - .05, y + d + .12, h * .5), I(x + w - .05, y + d + .12, h * .58), I(x + .05, y + d + .12, h * .58)])}" fill="#fff" fill-opacity=".7"/>'
            door = f'<polygon points="{_pt([I(x + .3, y + d, 0), I(x + .52, y + d, 0), I(x + .52, y + d, h * .32), I(x + .3, y + d, h * .32)])}" fill="hsl(25,40%,28%)"/>'
            roof = (f'<polygon points="{P4(x, y, x + w, y + d, h + .02)}" fill="hsl({hue},48%,{46 if hue < 100 else 52}%)"/>'
                    f'<polygon points="{P4(x + .08, y + .08, x + w - .08, y + d - .08, h + .02)}" fill="hsl({hue},40%,{54 if hue < 100 else 60}%)"/>')
            s += _box(I, x, y, w, d, h, 'hsl(40,18%,88%)', 'hsl(38,14%,76%)', 'hsl(32,10%,56%)', 'bd', win + door + bal + roof)
        elif kind == 'tree':
            _, _, x, y, sc = it; cx_, cy_ = I(x, y); r = 13 * sc
            s += (f'<g class="tr"><ellipse cx="{cx_ + 9:.0f}" cy="{cy_ + 2:.0f}" rx="{r:.0f}" ry="{r * .4:.0f}" fill="#000" opacity=".35"/>'
                  f'<rect x="{cx_ - 2:.0f}" y="{cy_ - 14:.0f}" width="4" height="14" fill="hsl(28,35%,26%)"/><circle cx="{cx_:.0f}" cy="{cy_ - 14 - r * .9:.0f}" r="{r:.0f}" fill="url(#{i}tr)"/>'
                  f'<circle cx="{cx_ - r * .35:.0f}" cy="{cy_ - 14 - r * 1.25:.0f}" r="{r * .5:.0f}" fill="hsl(100,60%,62%)" opacity=".35"/></g>')
        else:
            _, _, x, y, _ = it; cx_, cy_ = I(x, y)
            s += f'<g class="lp"><path d="M{cx_:.0f} {cy_:.0f} V{cy_ - 34:.0f} h-7" stroke="hsl(220,8%,30%)" stroke-width="2" fill="none"/><circle cx="{cx_ - 7:.0f}" cy="{cy_ - 33:.0f}" r="3.5" fill="hsl(45,100%,82%)" filter="url(#{i}gl)"/></g>'
    for k, (x, y, dx, dy, col) in enumerate(((4.7, .4, 0, 4, 'hsl(0,70%,50%)'), (5.15, 9.0, 0, -4, '#f0f0f0'), (.6, 5.15, 4, 0, 'hsl(210,60%,50%)'))):
        w, d = (.32, .62) if dx == 0 else (.62, .32)
        car = _box(I, x, y, w, d, .22, col, 'hsl(0,0%,20%)', 'hsl(0,0%,12%)', f'car{k}', f'<polygon points="{P4(x + .05, y + .12, x + w - .05, y + d - .2, .23)}" fill="#1d2a38" fill-opacity=".8"/>')
        s += car
    lot = [I(6.2, 6.2), I(7.05, 6.2), I(7.05, 7.5), I(6.2, 7.5)]
    s += (f'<g class="hl"><polygon points="{_pt(lot)}" fill="hsl(46,100%,60%)" fill-opacity=".5" stroke="hsl(46,100%,66%)" stroke-width="3" filter="url(#{i}gl)"/>'
          + ''.join(f'<path d="M{px:.0f} {py:.0f} v-12" stroke="#fff" stroke-width="3"/><circle cx="{px:.0f}" cy="{py - 12:.0f}" r="3" fill="hsl(356,80%,55%)"/>' for px, py in lot) + '</g>')
    if tag:
        tx, ty = I(6.6, 6.85); s += (f'<g class="tg"><path d="M{tx:.0f} {ty:.0f} V{ty - 96:.0f}" stroke="{FG}" stroke-width="2"/><circle cx="{tx:.0f}" cy="{ty:.0f}" r="4" fill="{FG}"/>'
                                     f'<rect x="{tx - _w(tag, 20) / 2 - 16:.0f}" y="{ty - 136:.0f}" width="{_w(tag, 20) + 32:.0f}" height="40" rx="20" fill="{FG}"/>'
                                     + _t(tx, ty - 109, tag, 20, '#111', 'middle', w=800) + '</g>')
    s += _t(60, 690, source or 'hình minh hoạ', 15, MUT, w=600)
    cx0, cy0 = I(5, 5)
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .gd,#{i} .rd,#{i} .pk', 0, opacity=0, y=30), T(f'#{i} .gd,#{i} .rd,#{i} .pk', a + .1, opacity=1, y=0, duration=.8, ease='expo.out', stagger=.08),
                                                S(f'#{i} .bd', 0, scaleY=0, opacity=0, transformOrigin='50% 100%'),
                                                T(f'#{i} .bd', t0, scaleY=1, opacity=1, duration=.55, ease='expo.out', stagger=.03),
                                                S(f'#{i} .tr,#{i} .lp', 0, scale=0, transformOrigin='50% 100%'), T(f'#{i} .tr,#{i} .lp', t0 + .3, scale=1, duration=.45, ease='back.out(2)', stagger=.025),
                                                S(f'#{i} .hl,#{i} .tg', 0, opacity=0), T(f'#{i} .ct', a, scale=1.05, duration=b - a, ease='none', svgOrigin=f'{cx0:.0f} {cy0:.0f}')]
    for k, (dx, dy) in enumerate(((0, 4), (0, -4), (4, 0))):
        ex, ey = I(dx, dy); ox, oy = I(0, 0)
        j += [S(f'#{i} .car{k}', 0, opacity=0), T(f'#{i} .car{k}', t0 + .6, opacity=1, duration=.2), T(f'#{i} .car{k}', t0 + .6, x=ex - ox, y=ey - oy, duration=max(.5, b - t0 - .8), ease='none')]
    th = t_hi or t0 + 1.6
    j += [T(f'#{i} .hl', th, opacity=1, duration=.3), T(f'#{i} .hl', th + .3, opacity=.6, duration=.5, yoyo=True, repeat=max(0, int((b - th) / .5) - 1)), _rv(f'#{i} .tg', th + .2, 16)]
    return _out(i, a, b, 'r_khudothi', s, j), j, [(t0, 'block'), (th, 'ding')]


# ==================================================================== VÀNG ==
def vang(i, a, b, t0, value, unit='tỷ đồng', kicker='', title='', note='', source=''):
    """thỏi vàng 3D xếp chồng, ánh kim quét qua + số lớn"""
    s = _defs(i) + _lg(f'{i}gt', 'hsl(50,100%,78%)', 'hsl(42,90%,52%)', 1, 1) + _lg(f'{i}gl_', 'hsl(42,85%,46%)', 'hsl(36,80%,30%)') + _lg(f'{i}gr', 'hsl(38,80%,36%)', 'hsl(30,75%,20%)') \
        + f'<radialGradient id="{i}fl" cx=".5" cy=".4" r=".6"><stop offset="0" stop-color="hsl(350,35%,22%)"/><stop offset="1" stop-color="hsl(350,35%,8%)" stop-opacity="0"/></radialGradient>' + _lg(f'{i}cn', 'hsl(48,95%,70%)', 'hsl(36,85%,38%)', 1, 1) + '</defs>'
    z = int(min(150, (600 - (_w(unit, 36) + 16)) / _w(value, 1)))
    NY = 360 if title else 300; z = min(z, 130)
    s += _head(kicker, title); NUM = _t(60, NY, value, z, cls='nv', w=800) + _t(60 + _w(value, z) + 14, NY, unit, 36, MUT, cls='nu', w=700)
    OY = 560 if title else 520; I = _iso(360, OY, 68); bars = []
    for lv, row in enumerate(((0, 1, 2), (.5, 1.5), (1,))):
        for c in row: bars.append((lv, c))
    random.seed(2)
    s += ''.join(f'<circle class="bk{k % 3}" cx="{random.uniform(80, 640):.0f}" cy="{random.uniform(OY - 170, OY + 60):.0f}" r="{random.uniform(8, 26):.0f}" fill="hsl(44,90%,60%)" opacity="{random.uniform(.06, .16):.2f}" filter="url(#{i}sf)"/>' for k in range(14))
    s += (f'<ellipse cx="360" cy="{OY + 100}" rx="290" ry="58" fill="url(#{i}fl)"/><ellipse cx="360" cy="{OY + 105}" rx="170" ry="18" fill="#000" opacity=".32" filter="url(#{i}sf)"/>'
          f'<ellipse cx="360" cy="{OY + 92}" rx="200" ry="10" fill="hsl(44,90%,60%)" opacity=".12" filter="url(#{i}sf)"/>')
    for lv, c in bars:
        h = .55; x0, y0, zz = c * 1.2 - 1.8, -1.1, lv * .55
        Tq = [I(x0 + .08, y0 + .08, zz + h), I(x0 + 1.0, y0 + .08, zz + h), I(x0 + 1.0, y0 + 2.1, zz + h), I(x0 + .08, y0 + 2.1, zz + h)]
        Lq = [I(x0, y0 + 2.2, zz), I(x0 + 1.08, y0 + 2.2, zz), I(x0 + 1.0, y0 + 2.1, zz + h), I(x0 + .08, y0 + 2.1, zz + h)]
        Rq = [I(x0 + 1.08, y0, zz), I(x0 + 1.08, y0 + 2.2, zz), I(x0 + 1.0, y0 + 2.1, zz + h), I(x0 + 1.0, y0 + .08, zz + h)]
        In = [I(x0 + .3, y0 + .5, zz + h), I(x0 + .78, y0 + .5, zz + h), I(x0 + .78, y0 + 1.7, zz + h), I(x0 + .3, y0 + 1.7, zz + h)]
        s += (f'<g class="bar"><polygon points="{_pt(Lq)}" fill="url(#{i}gl_)"/><polygon points="{_pt(Rq)}" fill="url(#{i}gr)"/><polygon points="{_pt(Tq)}" fill="url(#{i}gt)"/>'
              f'<polygon points="{_pt(In)}" fill="none" stroke="hsl(40,85%,45%)" stroke-width="1.5" stroke-opacity=".7"/>'
              f'<path d="M{_pt([Tq[0], Tq[1]])}" stroke="#fff" stroke-opacity=".7" stroke-width="2"/><path d="M{_pt([Tq[3], Tq[2]])}" stroke="hsl(50,100%,85%)" stroke-opacity=".8" stroke-width="1.5"/>'
              f'<path d="M{_pt([Tq[1], Tq[2]])}" stroke="hsl(50,100%,80%)" stroke-opacity=".5" stroke-width="1.2"/>'
              f'<polygon points="{_pt([In[0], In[1], In[2], In[3]])}" fill="hsl(50,100%,75%)" fill-opacity=".25"/></g>')
    for k, (cx_, cy_) in enumerate(((175, OY + 95), (230, OY + 118), (520, OY + 110), (575, OY + 88), (470, OY + 128))):
        s += (f'<g class="cn"><ellipse cx="{cx_}" cy="{cy_ + 5}" rx="26" ry="9" fill="hsl(36,80%,28%)"/><rect x="{cx_ - 26}" y="{cy_}" width="52" height="5" fill="hsl(38,80%,34%)"/>'
              f'<ellipse cx="{cx_}" cy="{cy_}" rx="26" ry="9" fill="url(#{i}cn)" stroke="hsl(40,85%,40%)" stroke-width="1.2" stroke-dasharray="1.5 1.5"/>'
              f'<ellipse cx="{cx_}" cy="{cy_}" rx="17" ry="5.5" fill="none" stroke="hsl(40,80%,40%)" stroke-width="1"/><ellipse cx="{cx_ - 7}" cy="{cy_ - 2}" rx="6" ry="1.6" fill="#fff" opacity=".5"/></g>')
    for k, (px, py) in enumerate(((-1.2, -.6, 1.15), (.2, .4, .6), (1.0, -.8, 1.7))[:3] and ((I(-1.2, -.2, 1.65)), I(.4, .6, .6), I(1.3, -.6, 1.1))):
        s += f'<path class="gn{k}" d="M{px:.0f} {py - 16:.0f} Q{px:.0f} {py:.0f} {px + 16:.0f} {py:.0f} Q{px:.0f} {py:.0f} {px:.0f} {py + 16:.0f} Q{px:.0f} {py:.0f} {px - 16:.0f} {py:.0f} Q{px:.0f} {py:.0f} {px:.0f} {py - 16:.0f} Z" fill="#fff" filter="url(#{i}gl)"/>'
    s += NUM
    if note: s += _t(60, 668, note, 22, MUT, w=600)
    s += _t(60, 690, source, 15, MUT, w=600) if source else ''
    j = _vis(i, a, b) + _headj(i, a, title) + [_num(i, 'nv', t0 + .2, value, 1.3), _rv(f'#{i} .nu', t0 + .4), S(f'#{i} .bar', 0, y=-140, opacity=0), T(f'#{i} .bar', t0, opacity=1, duration=.1, stagger=.15),
                                                T(f'#{i} .bar', t0, y=0, duration=.5, ease='bounce.out', stagger=.15),
                                                S(f'#{i} .cn', 0, opacity=0, y=-60), T(f'#{i} .cn', t0 + 1.0, opacity=1, y=0, duration=.45, ease='bounce.out', stagger=.08),
                                                T(f'#{i} .bk0', a, y=-30, duration=b - a, ease='none'), T(f'#{i} .bk1', a, y=-18, x=10, duration=b - a, ease='none'), T(f'#{i} .bk2', a, y=-42, duration=b - a, ease='none'),
                                                ] + [S(f'#{i} .gn{k}', 0, scale=0, transformOrigin='50% 50%') + T(f'#{i} .gn{k}', t0 + 1.2 + k * .25, scale=1, duration=.25, yoyo=True, repeat=1, ease='power2.out') for k in range(3)]
    return _out(i, a, b, 'r_vang', s, j), j, [(t0, 'metal'), (t0 + .75, 'metal'), (t0 + 1.0, 'count'), (t0 + 1.3, 'ding')]


# =================================================================== CÀ PHÊ ==
def caphe(i, a, b, t0, value='', unit='tấn', label='CÀ PHÊ ĐẮK LẮK', kicker='NÔNG NGHIỆP', title='', source=''):
    """bao bố cà phê (chất liệu bố, dây buộc, chữ in) + hạt cà phê rang đổ ra + số"""
    s = _defs(i) + _lg(f'{i}sk', 'hsl(36,40%,68%)', 'hsl(30,35%,40%)', 1, 1) + _rg(f'{i}bn', 'hsl(25,55%,38%)', 'hsl(18,60%,14%)', .35, .3) + \
        _lg(f'{i}wd', 'hsl(32,45%,52%)', 'hsl(28,45%,36%)') + _rg(f'{i}ch', 'hsl(358,85%,58%)', 'hsl(350,85%,28%)', .35, .3) + _rg(f'{i}cg', 'hsl(80,60%,55%)', 'hsl(95,55%,26%)', .35, .3) + _lg(f'{i}lf', 'hsl(120,45%,38%)', 'hsl(140,55%,16%)', 1, 1) + _lg(f'{i}sc', '#e6e8ec', '#7d838c', 1, 1) + f'<pattern id="{i}wv" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 3 H6 M3 0 V6" stroke="hsl(30,30%,25%)" stroke-width="1" stroke-opacity=".35"/></pattern></defs>'
    top = 330 if title else 270
    s += _head(kicker, title)
    if value: s += _t(60, top + 30, value, int(min(104, (600 - _w(unit, 32) - 16) / _w(value, 1))), cls='nv', w=800) + _t(60 + _w(value, int(min(104, (600 - _w(unit, 32) - 16) / _w(value, 1)))) + 14, top + 30, unit, 32, MUT, cls='nu', w=700)
    by = top + 326 if value else top + 250; s += f'<ellipse cx="360" cy="{by + 34}" rx="300" ry="30" fill="#000" opacity=".6" filter="url(#{i}sf)"/>'
    pal = ''
    for k in range(3): pal += f'<rect x="{150 + k * 0}" y="{by - 2 + k * 0}" width="420" height="12" fill="url(#{i}wd)"/>' if k == 0 else ''
    pal += (f'<rect x="150" y="{by - 4}" width="420" height="12" rx="2" fill="url(#{i}wd)"/>' + ''.join(f'<rect x="{150 + k * 135}" y="{by + 8}" width="40" height="18" fill="hsl(28,40%,{30 - k * 2}%)"/>' for k in range(4))
            + f'<rect x="150" y="{by + 24}" width="420" height="8" fill="hsl(28,40%,26%)"/>' + ''.join(f'<path d="M{160 + k * 52} {by} q20 2 40 0" stroke="hsl(28,40%,25%)" stroke-opacity=".5" fill="none"/>' for k in range(8)))
    s += f'<g class="pl_">{pal}</g>'
    for k, (cx, sc, back) in enumerate(((250, .82, 1), (470, .82, 1), (360, 1, 0))):
        w, h = 170 * sc, 220 * sc; y1 = by - (40 if back else 0); y0 = y1 - h
        body = (f'M{cx - w / 2:.0f} {y1:.0f} Q{cx - w / 2 - 12:.0f} {y0 + h * .45:.0f} {cx - w * .32:.0f} {y0 + 30:.0f} Q{cx:.0f} {y0 + 10:.0f} {cx + w * .32:.0f} {y0 + 30:.0f} '
                f'Q{cx + w / 2 + 12:.0f} {y0 + h * .45:.0f} {cx + w / 2:.0f} {y1:.0f} Q{cx:.0f} {y1 + 14:.0f} {cx - w / 2:.0f} {y1:.0f} Z')
        neck = f'M{cx - w * .3:.0f} {y0 + 32:.0f} L{cx - w * .16:.0f} {y0 - 26:.0f} Q{cx:.0f} {y0 - 40:.0f} {cx + w * .16:.0f} {y0 - 26:.0f} L{cx + w * .3:.0f} {y0 + 32:.0f} Z'
        s += (f'<g class="sk"><path d="{neck}" fill="url(#{i}sk)"/><path d="{neck}" fill="url(#{i}wv)"/><path d="{body}" fill="url(#{i}sk)"/><path d="{body}" fill="url(#{i}wv)"/>'
              f'<path d="{body}" fill="#fff" filter="url(#{i}nz)" opacity=".25"/><path d="M{cx - w * .2:.0f} {y0 + 6:.0f} Q{cx:.0f} {y0 + 18:.0f} {cx + w * .2:.0f} {y0 + 6:.0f}" stroke="hsl(20,30%,20%)" stroke-width="{5 * sc:.1f}" fill="none"/>'
              f'<path d="M{cx - w * .42:.0f} {y0 + h * .55:.0f} Q{cx:.0f} {y0 + h * .5:.0f} {cx + w * .42:.0f} {y0 + h * .58:.0f}" stroke="hsl(30,30%,30%)" stroke-opacity=".35" stroke-width="2" fill="none"/>'
              + f'<path d="M{cx - w / 2 + 8:.0f} {y1 - 6:.0f} Q{cx - w / 2 - 4:.0f} {y0 + h * .45:.0f} {cx - w * .3 + 4:.0f} {y0 + 36:.0f}" stroke="hsl(30,30%,22%)" stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="5 4" fill="none"/>'
              + f'<path d="M{cx + w / 2 - 8:.0f} {y1 - 6:.0f} Q{cx + w / 2 + 4:.0f} {y0 + h * .45:.0f} {cx + w * .3 - 4:.0f} {y0 + 36:.0f}" stroke="hsl(30,30%,22%)" stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="5 4" fill="none"/>'
              + f'<path d="M{cx - w * .2:.0f} {y0 + 2:.0f} Q{cx:.0f} {y0 + 14:.0f} {cx + w * .2:.0f} {y0 + 2:.0f}" stroke="hsl(40,40%,70%)" stroke-width="{2 * sc:.1f}" stroke-dasharray="3 3" fill="none"/>'
              + f'<path d="M{cx - w * .45:.0f} {y0 + h * .2:.0f} Q{cx - w * .5:.0f} {y0 + h * .6:.0f} {cx - w * .38:.0f} {y1 - 10:.0f}" stroke="#000" stroke-opacity=".18" stroke-width="{14 * sc:.0f}" fill="none"/>'
              + ('' if back else _t(cx, y0 + h * .5, 'CÀ PHÊ', 26, 'hsl(18,50%,20%)', 'middle', w=900, op=.75) + _t(cx, y0 + h * .5 + 26, label.replace('CÀ PHÊ ', ''), 15, 'hsl(18,50%,20%)', 'middle', w=800, op=.7)
                 + f'<circle cx="{cx}" cy="{y0 + h * .78:.0f}" r="16" fill="none" stroke="hsl(18,50%,20%)" stroke-opacity=".6" stroke-width="2"/>')
              + '</g>')
    random.seed(4)
    for k in range(18):
        x = 140 + random.random() * 440; y = by + 4 + random.random() * 40; r = random.uniform(-60, 60)
        s += (f'<g class="bn" transform="rotate({r:.0f} {x:.0f} {y:.0f})"><ellipse cx="{x:.0f}" cy="{y + 3:.0f}" rx="12" ry="8" fill="#000" opacity=".4"/><ellipse cx="{x:.0f}" cy="{y:.0f}" rx="12" ry="8.5" fill="url(#{i}bn)"/>'
              f'<path d="M{x - 9:.0f} {y:.0f} q5 -3 9 0 t9 0" stroke="hsl(20,40%,8%)" stroke-width="1.6" fill="none"/></g>')
    br = f'<path d="M40 {by + 60} C110 {by - 10} 150 {by - 80} 210 {by - 120}" stroke="hsl(28,35%,30%)" stroke-width="6" fill="none" stroke-linecap="round"/>'
    for k, (lx, ly, an, sc) in enumerate(((90, by + 10, -40, 1), (150, by - 70, 20, .9), (60, by + 40, 70, .8), (190, by - 120, -70, .8), (120, by - 30, 150, .85))):
        br += (f'<g transform="translate({lx} {ly}) rotate({an}) scale({sc})"><path d="M0 0 C20 -18 60 -18 84 0 C60 18 20 18 0 0 Z" fill="url(#{i}lf)"/>'
               f'<path d="M2 0 H80" stroke="hsl(90,40%,55%)" stroke-width="1.5" opacity=".6"/>' + ''.join(f'<path d="M{18 + q * 14} 0 l8 -7 M{18 + q * 14} 0 l8 7" stroke="hsl(90,40%,55%)" stroke-width="1" opacity=".4"/>' for q in range(4)) + '</g>')
    for k, (ox, oy) in enumerate(((112, by - 34), (124, by - 22), (100, by - 22), (116, by - 10), (176, by - 96), (166, by - 84), (186, by - 84), (132, by - 40))):
        br += f'<circle cx="{ox}" cy="{oy}" r="9" fill="url(#{i}{"cg" if k in (3, 7) else "ch"})"/><circle cx="{ox - 3}" cy="{oy - 3}" r="2.5" fill="#fff" opacity=".6"/>'
    s += f'<g class="br">{br}</g>'
    s += (f'<g class="sc_"><path d="M520 {by + 42} L600 {by + 20} L640 {by + 40} Q610 {by + 74} 560 {by + 70} Z" fill="url(#{i}sc)"/><path d="M600 {by + 20} L680 {by - 4}" stroke="#9aa0a8" stroke-width="8" stroke-linecap="round"/>'
          + ''.join(f'<ellipse cx="{560 + q * 12}" cy="{by + 44 + (q % 2) * 6}" rx="7" ry="5" fill="url(#{i}bn)"/>' for q in range(6)) + '</g>')
    s += _t(60, 690, source or 'hình minh hoạ', 15, MUT, w=600)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pl_', t0 - .2 if t0 - .2 > a else a, 20, .6), S(f'#{i} .br', 0, x=-160, opacity=0), T(f'#{i} .br', t0 + .9, x=0, opacity=1, duration=.9, ease='expo.out'),
                                                _rv(f'#{i} .sc_', t0 + 1.1, 20, .6), T(f'#{i} .br', t0 + 1.8, rotation=2, duration=1.2, yoyo=True, repeat=max(0, int((b - t0 - 1.8) / 1.2) - 1), ease='sine.inOut', svgOrigin=f'40 {by + 60}'),
                                                S(f'#{i} .sk', 0, y=40, opacity=0), T(f'#{i} .sk', t0, y=0, opacity=1, duration=.7, ease='expo.out', stagger=.12),
                                                S(f'#{i} .bn', 0, opacity=0, y=-30), T(f'#{i} .bn', t0 + .5, opacity=1, y=0, duration=.4, ease='bounce.out', stagger=.03)]
    if value: j += [_num(i, 'nv', t0 + .2, value, 1.2), _rv(f'#{i} .nu', t0 + .4)]
    return _out(i, a, b, 'r_caphe', s, j), j, [(t0, 'block'), (t0 + .5, 'pop')]


# ================================================================ KIT 3D DÙNG CHUNG ==
def _kit(i):
    """gradient dùng chung (gọi trong <defs>)"""
    return (_rg(f'{i}tr', 'hsl(105,55%,55%)', 'hsl(130,50%,20%)') + _rg(f'{i}wt', 'hsl(195,70%,62%)', 'hsl(205,70%,32%)', .4, .35)
            + _lg(f'{i}gw', 'hsl(205,30%,82%)', 'hsl(210,25%,62%)') + _lg(f'{i}mt', '#eef0f3', '#7d838c', 1, 1) + _lg(f'{i}dk', '#3a3d44', '#0e0f12')
            + _lg(f'{i}wd', 'hsl(32,45%,52%)', 'hsl(28,45%,34%)') + _rg(f'{i}sk', 'hsl(28,60%,78%)', 'hsl(24,45%,52%)', .4, .3)
            + _lg(f'{i}gl2', '#ffffff', '#ffffff', 1, 1, .22, 0) + _lg(f'{i}pp', 'hsl(40,40%,97%)', 'hsl(38,25%,86%)', 1, 1))
def _P4(I, x0, y0, x1, y1, z=0): return _pt([I(x0, y0, z), I(x1, y0, z), I(x1, y1, z), I(x0, y1, z)])
def _ground(I, i, x0, y0, x1, y1, col='hsl(100,28%,36%)', cls='gd', side=.4):
    g = [I(x0, y0), I(x1, y0), I(x1, y1), I(x0, y1)]
    return (f'<g class="{cls}"><polygon points="{_pt([(x, y + 16) for x, y in g])}" fill="#000" opacity=".55" filter="url(#{i}sf)"/>'
            f'<polygon points="{_pt([I(x0, y1), I(x1, y1), I(x1, y1, -side), I(x0, y1, -side)])}" fill="hsl(30,22%,24%)"/>'
            f'<polygon points="{_pt([I(x1, y0), I(x1, y1), I(x1, y1, -side), I(x1, y0, -side)])}" fill="hsl(30,22%,16%)"/>'
            f'<polygon points="{_pt(g)}" fill="{col}"/><polygon points="{_pt(g)}" fill="#fff" filter="url(#{i}nz)" opacity=".28"/></g>')
def _house(I, x, y, w, d, h, hue=25, cls='bd'):
    win = _winL(I, x, y, w, d, h, 2, 2, 'hsl(205,35%,28%)', lit={(0, 1)}) + _winR(I, x, y, w, d, h, max(2, int(d * 2.2)), 2, 'hsl(205,35%,22%)')
    bal = f'<polygon points="{_pt([I(x + .05, y + d + .12, h * .5), I(x + w - .05, y + d + .12, h * .5), I(x + w - .05, y + d + .12, h * .58), I(x + .05, y + d + .12, h * .58)])}" fill="#fff" fill-opacity=".7"/>'
    door = f'<polygon points="{_pt([I(x + w * .35, y + d, 0), I(x + w * .62, y + d, 0), I(x + w * .62, y + d, h * .32), I(x + w * .35, y + d, h * .32)])}" fill="hsl(25,40%,28%)"/>'
    roof = (f'<polygon points="{_P4(I, x, y, x + w, y + d, h + .02)}" fill="hsl({hue},48%,{46 if hue < 100 else 52}%)"/>'
            f'<polygon points="{_P4(I, x + .08, y + .08, x + w - .08, y + d - .08, h + .02)}" fill="hsl({hue},40%,{54 if hue < 100 else 60}%)"/>')
    return _box(I, x, y, w, d, h, 'hsl(40,18%,88%)', 'hsl(38,14%,76%)', 'hsl(32,10%,56%)', cls, win + door + bal + roof)
def _tower(I, i, x, y, w, d, h, cls='bd', cols=4, rows=8, tint=210):
    win = _winL(I, x, y, w, d, h, cols, rows, lit={(1, 2), (4, 0), (6, 3), (2, 1)}) + _winR(I, x, y, w, d, h, cols, rows, lit={(3, 1), (5, 2), (0, 3)})
    roof = (f'<polygon points="{_P4(I, x + .1, y + .1, x + w - .1, y + d - .1, h + .02)}" fill="hsl({tint},10%,70%)"/>'
            f'<polygon points="{_pt([I(x + .3, y + .3, h), I(x + .7, y + .3, h), I(x + .7, y + .7, h + .3), I(x + .3, y + .7, h + .3)])}" fill="hsl({tint},10%,55%)"/>')
    return _box(I, x, y, w, d, h, f'hsl({tint},12%,82%)', f'url(#{i}gw)', f'hsl({tint + 2},18%,50%)', cls, win + roof)
def _tree(I, i, x, y, sc=1, cls='tr'):
    cx_, cy_ = I(x, y); r = 13 * sc
    return (f'<g class="{cls}"><ellipse cx="{cx_ + 9:.0f}" cy="{cy_ + 2:.0f}" rx="{r:.0f}" ry="{r * .4:.0f}" fill="#000" opacity=".35"/>'
            f'<rect x="{cx_ - 2:.0f}" y="{cy_ - 14:.0f}" width="4" height="14" fill="hsl(28,35%,26%)"/><circle cx="{cx_:.0f}" cy="{cy_ - 14 - r * .9:.0f}" r="{r:.0f}" fill="url(#{i}tr)"/>'
            f'<circle cx="{cx_ - r * .35:.0f}" cy="{cy_ - 14 - r * 1.25:.0f}" r="{r * .5:.0f}" fill="hsl(100,60%,62%)" opacity=".35"/></g>')
def _lamp(I, i, x, y, cls='lp'):
    cx_, cy_ = I(x, y)
    return f'<g class="{cls}"><path d="M{cx_:.0f} {cy_:.0f} V{cy_ - 34:.0f} h-7" stroke="hsl(220,8%,30%)" stroke-width="2" fill="none"/><circle cx="{cx_ - 7:.0f}" cy="{cy_ - 33:.0f}" r="3.5" fill="hsl(45,100%,82%)" filter="url(#{i}gl)"/></g>'
def _car(I, x, y, along_x=False, col='hsl(0,70%,50%)', cls='car'):
    w, d = (.62, .32) if along_x else (.32, .62)
    return _box(I, x, y, w, d, .22, col, 'hsl(0,0%,20%)', 'hsl(0,0%,12%)', cls, f'<polygon points="{_P4(I, x + .06, y + .1, x + w - .06, y + d - .18, .23)}" fill="#1d2a38" fill-opacity=".85"/>')
def _truck(I, x, y, along_x=True, col='hsl(210,60%,45%)', cls='trk'):
    if along_x: return (f'<g class="{cls}">' + _box(I, x, y, 1.1, .4, .45, '#eceef1', '#c9ccd2', '#9aa0a8') + _box(I, x + 1.12, y, .32, .4, .32, col, 'hsl(210,50%,35%)', 'hsl(210,50%,25%)') + '</g>')
    return (f'<g class="{cls}">' + _box(I, x, y + .34, .4, 1.1, .45, '#eceef1', '#c9ccd2', '#9aa0a8') + _box(I, x, y, .4, .32, .32, col, 'hsl(210,50%,35%)', 'hsl(210,50%,25%)') + '</g>')
def _person(x, y, sc=1, shirt='hsl(210,55%,45%)', helmet=False, cls='ps'):
    """người đứng (toạ độ màn hình, chân tại x,y)"""
    h = 64 * sc
    return (f'<g class="{cls}"><ellipse cx="{x + 6 * sc:.0f}" cy="{y:.0f}" rx="{14 * sc:.0f}" ry="{4 * sc:.0f}" fill="#000" opacity=".35"/>'
            f'<rect x="{x - 7 * sc:.0f}" y="{y - h * .45:.0f}" width="{6 * sc:.0f}" height="{h * .45:.0f}" rx="{3 * sc:.0f}" fill="hsl(220,25%,22%)"/><rect x="{x + 1 * sc:.0f}" y="{y - h * .45:.0f}" width="{6 * sc:.0f}" height="{h * .45:.0f}" rx="{3 * sc:.0f}" fill="hsl(220,25%,18%)"/>'
            f'<rect x="{x - 10 * sc:.0f}" y="{y - h * .82:.0f}" width="{20 * sc:.0f}" height="{h * .42:.0f}" rx="{7 * sc:.0f}" fill="{shirt}"/>'
            f'<rect x="{x + 2 * sc:.0f}" y="{y - h * .8:.0f}" width="{8 * sc:.0f}" height="{h * .38:.0f}" rx="{4 * sc:.0f}" fill="#000" opacity=".18"/>'
            f'<circle cx="{x:.0f}" cy="{y - h * .92:.0f}" r="{8 * sc:.1f}" fill="hsl(28,55%,66%)"/>'
            + (f'<path d="M{x - 10 * sc:.0f} {y - h * .94:.0f} q{10 * sc:.0f} {-16 * sc:.0f} {20 * sc:.0f} 0 z" fill="hsl(45,95%,55%)"/><rect x="{x - 11 * sc:.0f}" y="{y - h * .95:.0f}" width="{22 * sc:.0f}" height="{3 * sc:.1f}" fill="hsl(45,90%,45%)"/>'
               if helmet else f'<path d="M{x - 8 * sc:.0f} {y - h * .95:.0f} q{8 * sc:.0f} {-12 * sc:.0f} {16 * sc:.0f} 0 z" fill="hsl(20,25%,15%)"/>') + '</g>')
def _note(s): return _t(60, 690, s or 'hình minh hoạ', 15, MUT, w=600)
def _numblk(value, unit, y, zmax=150, umax=36):
    z = int(min(zmax, (600 - (_w(unit, umax) + 16 if unit else 0)) / max(.1, _w(value, 1))))
    return _t(60, y, value, z, cls='nv', w=800) + (_t(60 + _w(value, z) + 14, y, unit, umax, MUT, cls='nu', w=700) if unit else '')
def _numj(i, t, value): return [_num(i, 'nv', t, value, 1.2), _rv(f'#{i} .nu', t + .25)]
def _paper(i, x, y, w, h, fill=None, cls='pp', rot=0, inner=''):
    return (f'<g class="{cls}" transform="rotate({rot} {x + w / 2} {y + h / 2})"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill or f"url(#{i}pp)"}" filter="url(#{i}sh)"/>'
            f'{inner}<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" filter="url(#{i}nz)" opacity=".45"/></g>')
def _seal(x, y, r=44, txt='', cls='sl'):
    return (f'<g class="{cls}" opacity=".85"><circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="hsl(356,85%,46%)" stroke-width="{r * .11:.1f}"/>'
            f'<circle cx="{x}" cy="{y}" r="{r * .78:.0f}" fill="none" stroke="hsl(356,85%,46%)" stroke-width="1.5"/>'
            f'<path d="M{x} {y - r * .36:.0f} l{r * .11:.1f} {r * .25:.1f} h{r * .27:.1f} l{-r * .2:.1f} {r * .16:.1f} l{r * .07:.1f} {r * .27:.1f} l{-r * .25:.1f} {-r * .16:.1f} l{-r * .25:.1f} {r * .16:.1f} l{r * .07:.1f} {-r * .27:.1f} l{-r * .2:.1f} {-r * .16:.1f} h{r * .27:.1f} z" fill="hsl(356,85%,46%)"/>'
            + (_t(x, y + r * .62, txt, max(8, int(r * .2)), 'hsl(356,85%,46%)', 'middle', w=800) if txt else '') + '</g>')
def _sealj(i, t, x, y, cls='sl'):
    return [S(f'#{i} .{cls}', 0, opacity=0, scale=1.8, svgOrigin=f'{x} {y}'), T(f'#{i} .{cls}', t, opacity=.85, scale=1, duration=.18, ease='power4.in', svgOrigin=f'{x} {y}')]
def _pen(i, x, y, rot=-20, cls='pen'):
    return (f'<g class="{cls}" transform="rotate({rot} {x} {y})"><rect x="{x}" y="{y - 9}" width="230" height="18" rx="9" fill="url(#{i}dk)" filter="url(#{i}sh)"/>'
            f'<rect x="{x + 160}" y="{y - 10}" width="12" height="20" fill="hsl(44,80%,55%)"/><path d="M{x} {y - 9} L{x - 40} {y} L{x} {y + 9} Z" fill="hsl(44,70%,60%)"/>'
            f'<rect x="{x + 10}" y="{y - 6}" width="200" height="3" rx="1.5" fill="#fff" opacity=".35"/></g>')
def _cash(i, x, y, n=5, col='hsl(150,45%,42%)', cls='cs'):
    """xấp tiền polymer khối đặc: mặt trên là tờ tiền có hoa văn, cạnh bên sọc mép giấy, dây thun cam (n ~ độ dày)"""
    h = n * 3.2
    top = [(x, y - h), (x + 120, y - 40 - h), (x + 210, y - 8 - h), (x + 90, y + 32 - h)]
    fl = [(x, y - h), (x + 90, y + 32 - h), (x + 90, y + 32), (x, y)]
    fr = [(x + 90, y + 32 - h), (x + 210, y - 8 - h), (x + 210, y - 8), (x + 90, y + 32)]
    st = ''.join(f'<path d="M{x} {y - k * 3.2:.1f} L{x + 90} {y + 32 - k * 3.2:.1f} L{x + 210} {y - 8 - k * 3.2:.1f}" stroke="{col}" stroke-opacity=".35" stroke-width="1" fill="none"/>' for k in range(1, n))
    return (f'<g class="{cls}"><ellipse cx="{x + 105}" cy="{y + 16}" rx="125" ry="18" fill="#000" opacity=".4" filter="url(#{i}sf)"/>'
            f'<polygon points="{_pt(fl)}" fill="hsl(60,25%,88%)"/><polygon points="{_pt(fr)}" fill="hsl(60,15%,74%)"/>{st}'
            f'<polygon points="{_pt(top)}" fill="{col}"/><polygon points="{_pt([(x + 30, y - 4 - h), (x + 120, y - 34 - h), (x + 180, y - 12 - h), (x + 90, y + 18 - h)])}" fill="none" stroke="#fff" stroke-opacity=".4"/>'
            f'<ellipse cx="{x + 105}" cy="{y - 4 - h:.0f}" rx="18" ry="9" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>'
            f'<path d="M{x + 140} {y - 30 - h:.0f} L{x + 50} {y + 2 - h:.0f} L{x + 50} {y + 2:.0f}" stroke="hsl(28,85%,52%)" stroke-width="6" fill="none"/>'
            f'<path d="M{x + 50} {y + 2 - h:.0f} L{x + 140} {y + 34 - h:.0f}" stroke="hsl(28,85%,45%)" stroke-width="6"/>'
            f'<path d="M{x + 140} {y + 34 - h:.0f} L{x + 140} {y + 34 - 2 if False else y + 18:.0f}" stroke="hsl(28,85%,45%)" stroke-width="0"/></g>')


# ================================================================ CẢNH MẪU ==
def so(i, a, b, t, value, unit='', kicker='', title='', note='', delta='', source=''):
    """1 con số lớn căn trái + đơn vị + chênh lệch + ghi chú (P.so)"""
    s = _head(kicker, title) + _numblk(value, unit, 500, 168, 40) + f'<rect class="hl" x="60" y="548" width="600" height="2" fill="{HAIR}"/>'
    UP, DN = '#3ddc84', '#ff5a5f'
    if delta: s += _t(60, 600, ('▲ ' if not delta.startswith('-') else '▼ ') + delta.lstrip('+-'), 28, UP if not delta.startswith('-') else DN, cls='dl', w=800)
    if note: s += _t(60 + (_w(delta, 28) + 60 if delta else 0), 600, note, 24, MUT, cls='nt', w=600)
    s += _src(source)
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t, value) + [S(f'#{i} .hl', 0, scaleX=0, transformOrigin='0% 50%'), T(f'#{i} .hl', t + .1, scaleX=1, duration=.9, ease='expo.inOut'),
                                                                   _rv(f'#{i} .dl', t + .5), _rv(f'#{i} .nt', t + .6)]
    return _out(i, a, b, 'r_so', s, j), j, [(t, 'tick')]


def ds(i, a, b, items, title='CẦN BIẾT', ket='', t_ket=None, kicker='', source=''):
    """bảng kẹp hồ sơ: tờ giấy trên bìa cứng, kẹp kim loại, mỗi ý một ô tick bút xanh (P.ds) — items=[(chữ, t)] ≤6"""
    n = min(6, len(items)); X0, Y0, W, H = 96, 236 if not kicker else 250, 528, 440
    s = _defs(i) + _kit(i) + _lg(f'{i}bd', 'hsl(28,40%,36%)', 'hsl(24,45%,20%)', 1, 1) + '</defs>' + _head(kicker, '')
    s += (f'<g class="bd_"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="20" fill="url(#{i}bd)" filter="url(#{i}sh)"/>'
          f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="20" fill="#fff" filter="url(#{i}nz)" opacity=".25"/>'
          f'<rect x="{X0 + 24}" y="{Y0 + 34}" width="{W - 48}" height="{H - 50}" rx="4" fill="url(#{i}pp)"/>'
          + ''.join(f'<path d="M{X0 + 44} {Y0 + 160 + k * 50} H{X0 + W - 44}" stroke="hsl(205,50%,70%)" stroke-opacity=".5" stroke-width="1.2"/>' for k in range(n))
          + f'<path d="M{X0 + 70} {Y0 + 40} V{Y0 + H - 20}" stroke="hsl(356,70%,60%)" stroke-opacity=".5" stroke-width="1.5"/>'
          + f'<rect x="{X0 + W / 2 - 80}" y="{Y0 - 14}" width="160" height="48" rx="10" fill="url(#{i}mt)" stroke="#555" stroke-width="1.5"/>'
          f'<rect x="{X0 + W / 2 - 40}" y="{Y0 - 30}" width="80" height="26" rx="13" fill="none" stroke="url(#{i}mt)" stroke-width="8"/>'
          f'<rect x="{X0 + W / 2 - 70}" y="{Y0 - 8}" width="140" height="6" rx="3" fill="#fff" opacity=".6"/>'
          + _t(X0 + 84, Y0 + 92, title, 30, '#1b1b1b', w=900) + '</g>')
    j = _vis(i, a, b) + _headj(i, a, '') + [S(f'#{i} .bd_', 0, y=80, rotation=-4, opacity=0, svgOrigin=f'360 {Y0 + H}'),
                                            T(f'#{i} .bd_', a + .05, y=0, rotation=0, opacity=1, duration=.8, ease='expo.out', svgOrigin=f'360 {Y0 + H}')]
    for k, (txt, t) in enumerate(items[:n]):
        y = Y0 + 152 + k * 50
        s += (f'<g class="r{k}"><rect x="{X0 + 84}" y="{y - 24}" width="26" height="26" rx="4" fill="#fff" stroke="#555" stroke-width="2"/>'
              + _t(X0 + 124, y - 3, txt, 25 if len(txt) < 24 else 20, '#1b1b1b', w=700) + '</g>'
              f'<path class="ck{k}" d="M{X0 + 88} {y - 12} l8 9 l18 -24" fill="none" stroke="hsl(220,75%,40%)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>')
        j += [_rv(f'#{i} .r{k}', t, 10, .5), S(f'#{i} .ck{k}', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .ck{k}', t + .15, strokeDashoffset=0, duration=.3)]
    if ket:
        tk = t_ket or items[n - 1][1] + .6; y = Y0 + H - 30
        s += f'<g class="kt"><rect x="{X0 + 84}" y="{y - 30}" width="{_w(ket, 22) + 34:.0f}" height="40" rx="20" fill="hsl(356,75%,48%)"/>' + _t(X0 + 101, y - 3, ket, 22, '#fff', w=800) + '</g>'
        j.append(_rv(f'#{i} .kt', tk, 12, .5))
    return _out(i, a, b, 'r_ds', s, j), j, [(a + .05, 'paper')] + [(t + .15, 'pen') for _, t in items[:n]]


def vanban(i, a, b, t, title, meta='', t_stamp=None, stamp='BAN HÀNH', head='QUYẾT ĐỊNH', brand='UBND TỈNH ĐẮK LẮK', kicker='VĂN BẢN', source=''):
    """văn bản hành chính: xấp giấy, kẹp giấy, tiêu đề tô dạ quang, dấu đỏ + chữ ký, bút dạ quang (P.vanban)"""
    X0, Y0, W, H = 150, 226, 420, 456; cx = X0 + W / 2; ts = t_stamp or t + 1.3
    L, cur = [], ''
    for wd in title.split():
        if len(cur + ' ' + wd) > 26 and cur: L.append(cur); cur = wd
        else: cur = (cur + ' ' + wd).strip()
    L.append(cur); L = L[:3]
    inner = (_t(X0 + 92, Y0 + 44, brand, 11, '#1b1b1b', 'middle', w=800) + f'<path d="M{X0 + 62} {Y0 + 52} h60" stroke="#1b1b1b" stroke-width="1"/>'
             + _t(X0 + W - 112, Y0 + 44, 'CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM', 9.5, '#1b1b1b', 'middle', w=800) + _t(X0 + W - 112, Y0 + 60, 'Độc lập – Tự do – Hạnh phúc', 9.5, '#1b1b1b', 'middle', w=700)
             + _t(cx, Y0 + 116, head, 28, '#1b1b1b', 'middle', w=900)
             + f'<rect class="hlg" x="{X0 + 40}" y="{Y0 + 132}" width="{W - 80}" height="{len(L) * 28 + 10}" fill="hsl(58,100%,60%)" fill-opacity=".6"/>'
             + ''.join(_t(cx, Y0 + 156 + k * 28, l, 20, '#1b1b1b', 'middle', w=800) for k, l in enumerate(L))
             + (_t(cx, Y0 + 170 + len(L) * 28, meta, 15, '#444', 'middle', w=600) if meta else '')
             + ''.join(f'<rect x="{X0 + 40}" y="{Y0 + 210 + len(L) * 28 + k * 18}" width="{W - 80 - (k % 4) * 40}" height="6" rx="3" fill="#1b1b1b" fill-opacity=".15"/>' for k in range(7))
             + f'<path class="sg" d="M{X0 + W - 170} {Y0 + H - 50} c14 -26 24 14 38 -6 s16 -20 28 4 s20 8 34 -12" fill="none" stroke="hsl(225,70%,30%)" stroke-width="2.5" stroke-linecap="round" pathLength="1"/>'
             + _seal(X0 + W - 110, Y0 + H - 70, 46) + _t(X0 + W - 110, Y0 + H - 14, 'GIÁM ĐỐC', 11, '#1b1b1b', 'middle', w=800))
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, '')
    s += ''.join(f'<rect x="{X0 + 6 + k * 5}" y="{Y0 + 6 + k * 4}" width="{W}" height="{H}" rx="5" fill="hsl(40,25%,{88 - k * 6}%)" transform="rotate({1.5 + k} {cx} {Y0 + H / 2})" filter="url(#{i}sh)"/>' for k in (1, 0))
    s += _paper(i, X0, Y0, W, H, inner=inner, rot=-1.5)
    if stamp:
        sw = _w(stamp, 26) + 40
        s += f'<g class="st" transform="rotate(-12 {X0 + 130} {Y0 + H - 70})"><rect x="{X0 + 130 - sw / 2:.0f}" y="{Y0 + H - 98}" width="{sw:.0f}" height="48" rx="6" fill="none" stroke="hsl(356,85%,46%)" stroke-width="4"/>' + _t(X0 + 130, Y0 + H - 64, stamp, 26, 'hsl(356,85%,46%)', 'middle', w=900) + '</g>'
    s += (f'<g class="cp"><path d="M{X0 + 40} {Y0 - 16} v52 q0 10 10 10 h0 q10 0 10 -10 v-44 q0 -6 -6 -6 q-6 0 -6 6 v38" fill="none" stroke="url(#{i}mt)" stroke-width="4" stroke-linecap="round"/></g>'
          f'<g class="hlp" transform="rotate(-32 560 640)"><rect x="470" y="628" width="200" height="26" rx="8" fill="hsl(58,95%,55%)" filter="url(#{i}sh)"/><rect x="470" y="628" width="70" height="26" rx="8" fill="hsl(58,60%,40%)"/>'
          f'<path d="M670 632 l26 6 v2 l-26 6 z" fill="hsl(58,95%,45%)"/><rect x="545" y="632" width="120" height="5" rx="2" fill="#fff" opacity=".45"/></g>')
    j = _vis(i, a, b) + _headj(i, a, '') + [S(f'#{i} .pp', 0, y=90, opacity=0), T(f'#{i} .pp', a + .05, y=0, opacity=1, duration=.8, ease='expo.out'),
                                            S(f'#{i} .hlg', 0, scaleX=0, transformOrigin='0% 50%'), T(f'#{i} .hlg', t, scaleX=1, duration=.6, ease='power2.out'),
                                            S(f'#{i} .sg', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .sg', ts - .5, strokeDashoffset=0, duration=.45),
                                            S(f'#{i} .hlp', 0, x=140, opacity=0), T(f'#{i} .hlp', t - .3 if t - .3 > a else a, x=0, opacity=1, duration=.6, ease='expo.out')] + _sealj(i, ts, X0 + W - 110, Y0 + H - 70)
    if stamp: j += [S(f'#{i} .st', 0, opacity=0, scale=2, svgOrigin=f'{X0 + 130} {Y0 + H - 70}'), T(f'#{i} .st', ts + .35, opacity=.9, scale=1, duration=.18, ease='power4.in', svgOrigin=f'{X0 + 130} {Y0 + H - 70}')]
    j.append(T(f'#{i} .ct', a, scale=1.03, duration=b - a, ease='none', svgOrigin='360 460'))
    return _out(i, a, b, 'r_vanban', s, j), j, [(a + .05, 'paper'), (t, 'pen'), (ts, 'stamp')] + ([(ts + .35, 'stamp')] if stamp else [])


# ================================================================== PHÁP LÝ ==
def hopdong(i, a, b, t0, t_sign, title='HỢP ĐỒNG ĐẶT CỌC', clauses=(), cash=True, kicker='PHÁP LÝ', source=''):
    """hợp đồng trên bàn: điều khoản tick dần (clauses=[(chữ, t)]), bút ký tự chạy, mộc đỏ, xấp tiền cọc"""
    X0, Y0, W, H = 110, 240, 400, 420
    inner = _t(X0 + W / 2, Y0 + 60, title, 24 if len(title) < 20 else 19, '#1b1b1b', 'middle', w=900) + f'<path d="M{X0 + 100} {Y0 + 74} H{X0 + W - 100}" stroke="#1b1b1b" stroke-width="1.2"/>'
    for k in range(4): inner += f'<rect x="{X0 + 34}" y="{Y0 + 96 + k * 16}" width="{W - 68 - (k % 2) * 50}" height="5" rx="2.5" fill="#1b1b1b" fill-opacity=".14"/>'
    for k, (c, t) in enumerate(list(clauses)[:4]):
        y = Y0 + 186 + k * 40
        inner += f'<g class="c{k}"><path d="M{X0 + 36} {y - 8} l7 7 l13 -15" fill="none" stroke="hsl(145,60%,34%)" stroke-width="3.5" stroke-linecap="round"/>' + _t(X0 + 62, y, c, 19, '#1b1b1b', w=700) + '</g>'
    sy = Y0 + H - 60
    inner += (f'<path d="M{X0 + 30} {sy + 10} h130 M{X0 + W - 160} {sy + 10} h130" stroke="#1b1b1b" stroke-width="1" stroke-dasharray="3 3"/>'
              + _t(X0 + 95, sy + 30, 'BÊN A', 12, '#444', 'middle', w=800) + _t(X0 + W - 95, sy + 30, 'BÊN B', 12, '#444', 'middle', w=800)
              + f'<path class="sg0" d="M{X0 + 44} {sy + 4} c12 -22 22 12 34 -6 s14 -18 26 4 s18 6 30 -10" fill="none" stroke="hsl(225,70%,30%)" stroke-width="2.4" stroke-linecap="round" pathLength="1"/>'
              f'<path class="sg1" d="M{X0 + W - 146} {sy + 4} c10 -20 26 16 40 -8 s16 -14 30 6 s14 4 26 -12" fill="none" stroke="hsl(225,70%,30%)" stroke-width="2.4" stroke-linecap="round" pathLength="1"/>'
              + _seal(X0 + W - 70, sy - 26, 34))
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, '') + _paper(i, X0, Y0, W, H, inner=inner, rot=-3)
    if cash: s += _cash(i, 420, 650, 6)
    s += _pen(i, 0, 0, -30, 'pen')
    j = _vis(i, a, b) + _headj(i, a, '') + [S(f'#{i} .pp', 0, y=80, opacity=0), T(f'#{i} .pp', t0 - .3 if t0 - .3 > a else a, y=0, opacity=1, duration=.8, ease='expo.out')]
    for k, (c, t) in enumerate(list(clauses)[:4]): j.append(_rv(f'#{i} .c{k}', t, 10, .45))
    for k in range(2): j += [S(f'#{i} .sg{k}', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .sg{k}', t_sign + k * .55, strokeDashoffset=0, duration=.45)]
    px0, py0 = X0 + 44, sy + 4
    j += [S(f'#{i} .pen', 0, x=px0 + 300, y=py0 + 120, opacity=0), T(f'#{i} .pen', t_sign - .35, x=px0, y=py0, opacity=1, duration=.35, ease='expo.out'),
          T(f'#{i} .pen', t_sign, x=px0 + 120, duration=.45, ease='none'), T(f'#{i} .pen', t_sign + .5, x=X0 + W - 146, duration=.1),
          T(f'#{i} .pen', t_sign + .55, x=X0 + W - 30, duration=.45, ease='none'), T(f'#{i} .pen', t_sign + 1.05, x=px0 + 420, y=py0 + 160, opacity=0, duration=.4)]
    j += _sealj(i, t_sign + 1.2, X0 + W - 70, sy - 26)
    if cash: j += [S(f'#{i} .cs', 0, y=-120, opacity=0), T(f'#{i} .cs', t0 + .4, y=0, opacity=1, duration=.6, ease='bounce.out')]
    j.append(T(f'#{i} .ct', a, scale=1.03, duration=b - a, ease='none', svgOrigin='360 460'))
    return _out(i, a, b, 'r_hopdong', s, j), j, [(t0, 'paper'), (t_sign, 'pen'), (t_sign + 1.2, 'stamp')] + ([(t0 + .4, 'block')] if cash else [])


def thuephi(i, a, b, rows, total=None, t_total=None, kicker='THUẾ PHÍ', title='', source=''):
    """máy tính + biên lai in ra: rows=[(khoản, '2%', t)] · total=('TỔNG', '…') — màn hình máy tính hiện tổng"""
    n = min(5, len(rows)); RX, RY, RW = 300, 236 if not title else 300, 300; RH = 120 + n * 52 + (80 if total else 10)
    zig = ''.join(f'L{RX + k * 15 + 7.5} {RY + RH + 9} L{RX + k * 15 + 15} {RY + RH}' for k in range(RW // 15))
    s = _defs(i) + _kit(i) + _lg(f'{i}cb', '#2c2f36', '#14161a', 1, 1) + _lg(f'{i}lcd', 'hsl(90,25%,72%)', 'hsl(90,20%,58%)') + '</defs>' + _head(kicker, title)
    s += (f'<g class="rc"><rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" fill="url(#{i}pp)" filter="url(#{i}sh)"/><path d="M{RX} {RY + RH} {zig} Z" fill="hsl(38,25%,86%)"/>'
          f'<rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" fill="#fff" filter="url(#{i}nz)" opacity=".45"/>'
          + _t(RX + RW / 2, RY + 50, 'BIÊN LAI THU', 22, '#1b1b1b', 'middle', w=900) + f'<path d="M{RX + 24} {RY + 76} H{RX + RW - 24}" stroke="#1b1b1b" stroke-opacity=".4" stroke-dasharray="4 5"/>')
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .rc', 0, y=-RH, opacity=0), T(f'#{i} .rc', a + .1, y=0, opacity=1, duration=1.0, ease='power2.out')]
    for k, (nm, v, t) in enumerate(rows[:n]):
        y = RY + 118 + k * 52
        s += f'<g class="r{k}">' + _t(RX + 24, y, nm, 19, '#1b1b1b', w=700) + _t(RX + RW - 24, y, v, 22, 'hsl(356,70%,42%)', 'end', w=900) + '</g>'
        j.append(_rv(f'#{i} .r{k}', t, 8, .35))
    if total:
        y = RY + 118 + n * 52 + 22; tt = t_total or rows[n - 1][2] + .5
        s += (f'<path d="M{RX + 24} {y - 34} H{RX + RW - 24}" stroke="#1b1b1b" stroke-width="2"/>'
              f'<g class="tl">' + _t(RX + 24, y + 6, total[0], 22, '#1b1b1b', w=900) + _t(RX + RW - 24, y + 8, total[1], 30, 'hsl(356,70%,42%)', 'end', w=900) + '</g>')
        j.append(_rv(f'#{i} .tl', tt, 8, .4))
    CX, CY = 70, 410 if not title else 450
    keys = ''.join(f'<rect x="{CX + 20 + c * 46}" y="{CY + 100 + r * 40}" width="38" height="32" rx="7" fill="{"hsl(30,85%,55%)" if c == 3 else "#3b3f47"}"/>'
                   f'<rect x="{CX + 22 + c * 46}" y="{CY + 102 + r * 40}" width="34" height="8" rx="4" fill="#fff" opacity=".12"/>' for r in range(4) for c in range(4))
    s += (f'<g class="calc" transform="rotate(-8 {CX + 105} {CY + 140})"><rect x="{CX}" y="{CY}" width="210" height="280" rx="22" fill="url(#{i}cb)" filter="url(#{i}sh)"/>'
          f'<rect x="{CX + 18}" y="{CY + 20}" width="174" height="62" rx="8" fill="url(#{i}lcd)"/>{keys}'
          + (_t(CX + 182, CY + 64, total[1] if total else '', 26, '#1d2a1d', 'end', cls='lcd', w=800) if total else '') + '</g>')
    j += [S(f'#{i} .calc', 0, x=-60, opacity=0), T(f'#{i} .calc', a + .2, x=0, opacity=1, duration=.8, ease='expo.out')]
    if total: j.append(_rv(f'#{i} .lcd', (t_total or rows[n - 1][2] + .5) + .1, 4, .3))
    s += _src(source)
    return _out(i, a, b, 'r_thuephi', s, j), j, [(a + .1, 'paper')] + [(t, 'tick') for *_, t in rows[:n]] + ([(t_total or rows[n - 1][2] + .5, 'ding')] if total else [])


def thutuc(i, a, b, steps, t_done=None, done='HOÀN TẤT', kicker='THỦ TỤC', title='', source=''):
    """từng bộ hồ sơ (bìa giấy kraft có nhãn) trượt vào xếp lớp, mỗi bước có dấu tick xanh; t_done → dấu HOÀN TẤT"""
    n = min(5, len(steps)); y0 = 300 if title else 240; g = min(84, 380 / max(1, n))
    s = _defs(i) + _kit(i) + _lg(f'{i}fd', 'hsl(36,55%,66%)', 'hsl(32,45%,50%)', 1, 1) + '</defs>' + _head(kicker, title)
    j = _vis(i, a, b) + _headj(i, a, title)
    for k, (st, t, *m) in enumerate(steps[:n]):
        y = y0 + k * g; x = 80 + k * 14
        s += (f'<g class="f{k}"><path d="M{x} {y + 10} h120 l14 -14 h70 l14 14 h{500 - 218 - k * 28} v{g + 6} h-{500 - k * 28} z" fill="url(#{i}fd)" filter="url(#{i}sh)"/>'
              f'<path d="M{x} {y + 10} h{500 - k * 28}" stroke="#fff" stroke-opacity=".35"/><rect x="{x + 20}" y="{y + 24}" width="46" height="{min(40, g - 18)}" rx="4" fill="#fff" opacity=".9"/>'
              + _t(x + 43, y + 24 + min(40, g - 18) / 2 + 7, f'{k + 1:02d}', 18, '#1b1b1b', 'middle', w=900)
              + _t(x + 82, y + 24 + min(40, g - 18) / 2 + 9, st, 25 if len(st) < 22 else 20, '#1b1b1b', w=800)
              + (_t(x + 486 - k * 28, y + 24 + min(40, g - 18) / 2 + 7, m[0], 15, 'hsl(28,40%,25%)', 'end', w=800) if m else '') + '</g>'
              f'<g class="k{k}"><circle cx="{x + 500 - k * 28}" cy="{y + 14}" r="17" fill="hsl(145,60%,40%)" stroke="#fff" stroke-width="3"/><path d="M{x + 492 - k * 28} {y + 14} l6 6 l10 -12" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round"/></g>')
        j += [S(f'#{i} .f{k}', 0, x=-50, opacity=0), T(f'#{i} .f{k}', t, x=0, opacity=1, duration=.55, ease='expo.out'),
              S(f'#{i} .k{k}', 0, scale=0, svgOrigin=f'{x + 500 - k * 28} {y + 14}'), T(f'#{i} .k{k}', t + .35, scale=1, duration=.35, ease='back.out(2.5)', svgOrigin=f'{x + 500 - k * 28} {y + 14}')]
    if t_done:
        sx, sy = 470, y0 + n * g + 30; sw = _w(done, 30) + 40
        s += f'<g class="dn" transform="rotate(-10 {sx} {sy})"><rect x="{sx - sw / 2:.0f}" y="{sy - 30}" width="{sw:.0f}" height="50" rx="8" fill="none" stroke="hsl(145,60%,45%)" stroke-width="5"/>' + _t(sx, sy + 6, done, 30, 'hsl(145,60%,45%)', 'middle', w=900) + '</g>'
        j += [S(f'#{i} .dn', 0, opacity=0, scale=2, svgOrigin=f'{sx} {sy}'), T(f'#{i} .dn', t_done, opacity=1, scale=1, duration=.2, ease='power4.in', svgOrigin=f'{sx} {sy}')]
    s += _src(source)
    return _out(i, a, b, 'r_thutuc', s, j), j, [(t, 'paper') for _, t, *_ in steps[:n]] + ([(t_done, 'stamp')] if t_done else [])


def canhbao(i, a, b, items, t_stamp=None, stamp='RỦI RO', kicker='CẢNH BÁO', title='', source=''):
    """khu đất bị rào chắn sọc đỏ trắng + biển tam giác cảnh báo + đèn nháy; items=[(chữ, t)] ≤3 thẻ đỏ bên dưới"""
    I = _iso(360, 250 if not title else 300, 28)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 6, 6, 'hsl(35,30%,42%)')
    s += f'<polygon points="{_P4(I, 1, 1, 5, 5)}" fill="hsl(30,35%,48%)"/><polygon points="{_P4(I, 1, 1, 5, 5)}" fill="#fff" filter="url(#{i}nz)" opacity=".3"/>'
    posts = [(1, 1), (3, 1), (5, 1), (5, 3), (5, 5), (3, 5), (1, 5), (1, 3)]
    for k in range(8):
        p, q = posts[k], posts[(k + 1) % 8]
        bar = [I(p[0], p[1], .55), I(q[0], q[1], .55), I(q[0], q[1], .8), I(p[0], p[1], .8)]
        s += (f'<g class="fc"><polygon points="{_pt(bar)}" fill="#fff"/>'
              + ''.join(f'<polygon points="{_pt([I(p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u, .55), I(p[0] + (q[0] - p[0]) * (u + .12), p[1] + (q[1] - p[1]) * (u + .12), .55), I(p[0] + (q[0] - p[0]) * (u + .2), p[1] + (q[1] - p[1]) * (u + .2), .8), I(p[0] + (q[0] - p[0]) * (u + .08), p[1] + (q[1] - p[1]) * (u + .08), .8)])}" fill="hsl(356,80%,50%)"/>' for u in (0, .25, .5, .75))
              + f'<path d="M{_pt([I(p[0], p[1]), I(p[0], p[1], .9)])}" stroke="#555" stroke-width="3"/></g>')
    sx, sy = I(3, 3)
    s += (f'<g class="sgn"><path d="M{sx:.0f} {sy:.0f} V{sy - 120:.0f}" stroke="#777" stroke-width="5"/><path d="M{sx:.0f} {sy - 210:.0f} L{sx + 56:.0f} {sy - 112:.0f} H{sx - 56:.0f} Z" fill="hsl(48,100%,55%)" stroke="#111" stroke-width="6" stroke-linejoin="round"/>'
          + _t(sx, sy - 128, '!', 64, '#111', 'middle', w=900) + '</g>'
          f'<circle class="bl" cx="{_pt([I(5, 1, .95)]).split(",")[0]}" cy="{_pt([I(5, 1, .95)]).split(",")[1]}" r="7" fill="hsl(30,100%,55%)" filter="url(#{i}gl)"/>')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .fc', 0, scaleY=0, transformOrigin='50% 100%'),
                                                T(f'#{i} .fc', a + .3, scaleY=1, duration=.35, stagger=.06, ease='back.out(2)'),
                                                S(f'#{i} .sgn', 0, scale=0, svgOrigin=f'{sx:.0f} {sy:.0f}'), T(f'#{i} .sgn', a + .6, scale=1, duration=.5, ease='back.out(1.8)', svgOrigin=f'{sx:.0f} {sy:.0f}'),
                                                T(f'#{i} .bl', a, opacity=.15, duration=.35, yoyo=True, repeat=max(0, int((b - a) / .35) - 1))]
    yb = (250 if not title else 300) + 6 * 28 + 70
    for k, (txt, t) in enumerate(items[:3]):
        y = yb + 20 + k * 58
        s += f'<g class="r{k}"><rect x="60" y="{y - 36}" width="600" height="48" rx="12" fill="hsl(356,70%,45%)" fill-opacity=".18" stroke="hsl(356,80%,55%)" stroke-opacity=".6"/><path d="M80 {y - 22} l16 16 m0 -16 l-16 16" stroke="hsl(356,85%,62%)" stroke-width="4" stroke-linecap="round"/>' + _t(110, y - 4, txt, 24, w=800) + '</g>'
        j.append(_rv(f'#{i} .r{k}', t, 12, .4))
    if t_stamp:
        sw = _w(stamp, 34) + 40; px, py = 500, yb - 50
        s += f'<g class="sp" transform="rotate(-10 {px} {py})"><rect x="{px - sw / 2:.0f}" y="{py - 32}" width="{sw:.0f}" height="54" rx="8" fill="rgba(0,0,0,.35)" stroke="hsl(356,85%,58%)" stroke-width="5"/>' + _t(px, py + 8, stamp, 34, 'hsl(356,85%,62%)', 'middle', w=900) + '</g>'
        j += [S(f'#{i} .sp', 0, opacity=0, scale=2, svgOrigin=f'{px} {py}'), T(f'#{i} .sp', t_stamp, opacity=1, scale=1, duration=.2, ease='power4.in', svgOrigin=f'{px} {py}')]
    s += _src(source)
    return _out(i, a, b, 'r_canhbao', s, j), j, [(a + .3, 'block')] + [(t, 'hit') for _, t in items[:3]] + ([(t_stamp, 'stamp')] if t_stamp else [])


def tranhchap(i, a, b, t0, t_hit, left='BÊN A', right='BÊN B', kicker='PHÁP LÝ', title='TRANH CHẤP ĐẤT', source=''):
    """thửa đất có hàng rào gỗ chia đôi, 2 nhà 2 bên; t_hit: búa toà gõ xuống, đất nứt"""
    I = _iso(360, 310 if title else 260, 30)
    s = (_defs(i) + _kit(i) + _lg(f'{i}gv', 'hsl(25,55%,42%)', 'hsl(20,60%,20%)', 1, 1) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 8, 8)
         + f'<polygon points="{_P4(I, .6, .6, 7.4, 7.4)}" fill="hsl(44,45%,52%)" fill-opacity=".35" stroke="hsl(44,80%,60%)" stroke-width="2" stroke-dasharray="6 5"/>')
    s += _house(I, 1.2, 1.2, 1.4, 2.0, 1.3, 205, 'h0') + _tree(I, i, 2.2, 5.6, 1.1) + _tree(I, i, 1.1, 6.4, .9)
    fence = ''
    for k in range(15):
        u = .6 + k * .48; fence += f'<polygon points="{_pt([I(u, u, 0), I(u + .08, u + .08, 0), I(u + .08, u + .08, .7), I(u, u, .78)])}" fill="hsl(30,45%,{48 - (k % 2) * 6}%)"/>'
    fence += f'<path d="M{_pt([I(.6, .6, .5), I(7.4, 7.4, .5)])}" stroke="hsl(30,40%,35%)" stroke-width="3"/><path d="M{_pt([I(.6, .6, .25), I(7.4, 7.4, .25)])}" stroke="hsl(30,40%,35%)" stroke-width="3"/>'
    s += f'<g class="fn">{fence}</g>' + _house(I, 5.2, 2.0, 1.6, 1.6, 1.1, 8, 'h1') + _tree(I, i, 6.6, 5.2, 1)
    s += f'<path class="ck" d="M{_pt([I(3.6, 3.4), I(4.4, 4.0), I(4.0, 4.6), I(4.9, 5.3), I(4.6, 6.0), I(5.4, 6.8)])}" fill="none" stroke="hsl(20,30%,10%)" stroke-width="4" stroke-linejoin="round" pathLength="1"/>'
    gx, gy = 490, 330 if title else 280
    s += (f'<g class="gv" transform="rotate(-35 {gx + 80} {gy + 10})"><rect x="{gx}" y="{gy - 6}" width="160" height="14" rx="7" fill="url(#{i}gv)" filter="url(#{i}sh)"/>'
          f'<rect x="{gx - 40}" y="{gy - 34}" width="70" height="70" rx="14" fill="url(#{i}gv)"/><rect x="{gx - 44}" y="{gy - 34}" width="10" height="70" rx="4" fill="hsl(44,70%,50%)"/>'
          f'<rect x="{gx + 26}" y="{gy - 34}" width="10" height="70" rx="4" fill="hsl(44,70%,50%)"/><rect x="{gx - 34}" y="{gy - 28}" width="58" height="10" rx="5" fill="#fff" opacity=".25"/></g>')
    lx, ly = I(1.2, 7.4); rx, ry = I(7.4, 1.2)
    s += f'<g class="pa">' + _t(lx - 10, ly + 46, left, 22, 'hsl(145,60%,60%)', 'middle', w=900) + '</g><g class="pb">' + _t(rx + 10, ry - 20, right, 22, 'hsl(356,80%,65%)', 'middle', w=900) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .h0,#{i} .h1', 0, scaleY=0, transformOrigin='50% 100%'),
                                                T(f'#{i} .h0,#{i} .h1', a + .3, scaleY=1, duration=.5, ease='expo.out', stagger=.15),
                                                S(f'#{i} .fn', 0, opacity=0), T(f'#{i} .fn', t0, opacity=1, duration=.4), _rv(f'#{i} .pa', t0 + .2, 10), _rv(f'#{i} .pb', t0 + .35, 10),
                                                S(f'#{i} .gv', 0, opacity=0, rotation=-30, svgOrigin=f'{gx + 160} {gy}'),
                                                T(f'#{i} .gv', t_hit - .4, opacity=1, duration=.2), T(f'#{i} .gv', t_hit - .2, rotation=12, duration=.2, ease='power4.in', svgOrigin=f'{gx + 160} {gy}'),
                                                T(f'#{i} .gv', t_hit, rotation=0, duration=.3, ease='back.out(3)', svgOrigin=f'{gx + 160} {gy}'),
                                                S(f'#{i} .ck', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .ck', t_hit, strokeDashoffset=0, duration=.3, ease='power4.out'),
                                                T(f'#{i} .ct', t_hit, x=5, duration=.05, yoyo=True, repeat=5)]
    s += _note(source)
    return _out(i, a, b, 'r_tranhchap', s, j), j, [(t0, 'block'), (t_hit, 'hit')]


# ================================================================ QUY HOẠCH ==
def tyle(i, a, b, t0, t_zoom, lo='1/2000', hi='1/500', kicker='QUY HOẠCH', title='Tỷ lệ bản đồ', source=''):
    """bản đồ quy hoạch giấy trên bàn; kính lúp lướt tới, trong mắt kính hiện từng lô chi tiết (tỷ lệ hi)"""
    X0, Y0, W, H = 90, 320 if title else 260, 540, 340
    Z = [((0, 0, .45, .55), 'hsl(44,80%,64%)'), ((.45, 0, 1, .35), 'hsl(356,60%,62%)'), ((.45, .35, 1, 1), 'hsl(44,80%,64%)'), ((0, .55, .45, 1), 'hsl(120,40%,52%)')]
    mp = ''.join(f'<rect x="{X0 + x0 * W:.0f}" y="{Y0 + y0 * H:.0f}" width="{(x1 - x0) * W:.0f}" height="{(y1 - y0) * H:.0f}" fill="{c}" fill-opacity=".75"/>' for (x0, y0, x1, y1), c in Z)
    mp += f'<path d="M{X0} {Y0 + H * .55} H{X0 + W} M{X0 + W * .45} {Y0} V{Y0 + H}" stroke="#fff" stroke-width="12"/><path d="M{X0} {Y0 + H * .55} H{X0 + W} M{X0 + W * .45} {Y0} V{Y0 + H}" stroke="#888" stroke-width="1" stroke-dasharray="6 6"/>'
    det = ''
    for gx in range(X0 + 10, X0 + W, 26):
        for gy in range(Y0 + 8, Y0 + H, 22):
            if abs(gx - (X0 + W * .45)) < 18 or abs(gy - (Y0 + H * .55)) < 16: continue
            det += f'<rect x="{gx}" y="{gy}" width="22" height="17" fill="none" stroke="#5a4a30" stroke-width="1"/>'
    s = (_defs(i) + _kit(i) + f'<clipPath id="{i}lz"><circle class="lzc" cx="0" cy="0" r="92"/></clipPath>'
         + f'<radialGradient id="{i}gs" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".6" stop-color="#bfe0ff" stop-opacity=".08"/><stop offset="1" stop-color="#9cc" stop-opacity=".2"/></radialGradient></defs>'
         + _head(kicker, title))
    s += _paper(i, X0 - 14, Y0 - 14, W + 28, H + 28, inner=f'<g>{mp}</g>' + _t(X0 + 6, Y0 + H + 2, 'BẢN ĐỒ QUY HOẠCH SỬ DỤNG ĐẤT', 10, '#333', w=800), rot=-1.5)
    lx, ly = X0 + W * .62, Y0 + H * .42
    s += (f'<g class="lz"><g clip-path="url(#{i}lz)"><g class="lzi"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" fill="url(#{i}pp)"/>{mp}{det}</g></g>'
          f'<circle cx="0" cy="0" r="92" fill="url(#{i}gs)"/><circle cx="0" cy="0" r="96" fill="none" stroke="url(#{i}mt)" stroke-width="14" filter="url(#{i}sh)"/>'
          f'<path d="M64 70 L150 156" stroke="url(#{i}dk)" stroke-width="26" stroke-linecap="round"/><path d="M-50 -60 a80 80 0 0 1 70 -16" stroke="#fff" stroke-opacity=".6" stroke-width="5" fill="none" stroke-linecap="round"/></g>')
    s += f'<g class="ca">' + _t(660, Y0 - 26, 'TỶ LỆ ' + lo, 24, MUT, 'end', w=800) + '</g><g class="cb">' + _t(660, Y0 - 26, 'TỶ LỆ ' + hi, 24, AC, 'end', w=800) + '</g>'
    x1, y1 = X0 + W + 140, Y0 + H + 60; x3, y3 = lx - 50, ly + 30; d3 = max(.3, b - t_zoom - .4)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pp', a + .05, 40, .8), _rv(f'#{i} .ca', t0, 10), S(f'#{i} .cb', 0, opacity=0),
                                                S(f'#{i} .lz', 0, x=x1, y=y1, opacity=0), S(f'#{i} .lzi', 0, x=-2 * x1, y=-2 * y1, scale=2, svgOrigin='0 0'),
                                                T(f'#{i} .lz', t_zoom - .6, x=lx, y=ly, opacity=1, duration=.8, ease='expo.out'), T(f'#{i} .lzi', t_zoom - .6, x=-2 * lx, y=-2 * ly, duration=.8, ease='expo.out'),
                                                T(f'#{i} .lz', t_zoom + .3, x=x3, y=y3, duration=d3, ease='sine.inOut'), T(f'#{i} .lzi', t_zoom + .3, x=-2 * x3, y=-2 * y3, duration=d3, ease='sine.inOut'),
                                                T(f'#{i} .ca', t_zoom + .2, opacity=0, duration=.2), _rv(f'#{i} .cb', t_zoom + .3, 10)]
    s += _note(source)
    return _out(i, a, b, 'r_tyle', s, j), j, [(t0, 'paper'), (t_zoom, 'whoosh'), (t_zoom + .3, 'ding')]


def matdo(i, a, b, t0, pct='', floors='', kicker='QUY HOẠCH', title='Mật độ xây dựng', source=''):
    """khu đất 3D: phần xây dựng (pct%) mọc thành khối nhà cao `floors` tầng, phần còn lại sân vườn cây xanh"""
    f = (_isn(pct) or 60) / 100; nf = int(_isn(floors) or 6); I = _iso(360, 380 if title else 330, 40)
    side = 6 * math.sqrt(f); x0 = (6 - side) / 2; h = min(3.4, .36 * nf)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 6, 6, 'hsl(110,32%,40%)')
    s += f'<polygon points="{_P4(I, .1, .1, 5.9, 5.9)}" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="8 6" opacity=".7"/>'
    s += f'<polygon class="fp" points="{_P4(I, x0, x0, x0 + side, x0 + side)}" fill="hsl(44,100%,60%)" fill-opacity=".35" stroke="hsl(44,100%,62%)" stroke-width="3"/>'
    for k, (tx, ty) in enumerate(((.5, 5.3), (1.4, 5.5), (5.3, .6), (5.4, 1.6), (5.4, 4.8), (.6, .6))): s += _tree(I, i, tx, ty, .9, 'tr')
    s += _tower(I, i, x0 + .1, x0 + .1, side - .2, side - .2, h, 'bd', max(3, int(side * 1.4)), max(2, nf), 30)
    if pct: s += _numblk(pct, '%', 660, 96, 40)
    if floors: s += _t(624, 660, f'{floors} TẦNG', 30, FG, 'end', cls='flt', w=800)
    bx, by_ = I(3, 3)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .fp', 0, opacity=0), T(f'#{i} .fp', t0, opacity=1, duration=.4),
                                                S(f'#{i} .bd', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .bd', t0 + .3, scaleY=1, duration=1.0, ease='expo.out'),
                                                S(f'#{i} .tr', 0, scale=0, transformOrigin='50% 100%'), T(f'#{i} .tr', t0 + .5, scale=1, duration=.4, stagger=.06, ease='back.out(2)')]
    if pct: j += _numj(i, t0 + .2, pct)
    if floors: j.append(_rv(f'#{i} .flt', t0 + .8))
    s += _note(source if (pct or floors) else '') if source else ''
    return _out(i, a, b, 'r_matdo', s, j), j, [(t0, 'block'), (t0 + .3, 'ratchet')]
def _isn(v):
    try: return float(str(v).replace('.', '').replace(',', '.')) if v not in ('', None) else None
    except ValueError: return None


def sapnhap(i, a, b, t0, t_merge, left='ĐẮK LẮK', right='PHÚ YÊN', new='ĐẮK LẮK', kicker='SÁP NHẬP', title='', source=''):
    """2 mảnh bản đồ nổi khối (3D) trượt vào nhau, đường ghép sáng vàng, tên mới hiện ở giữa"""
    A = [(140, 300), (250, 270), (340, 320), (360, 400), (340, 500), (370, 590), (250, 620), (160, 560), (120, 440)]
    Bp = [(370, 330), (480, 280), (590, 330), (620, 450), (590, 560), (470, 610), (370, 590), (340, 500), (360, 400)]
    dy = 40 if title else 0
    def ext(P, top, side, cls, th=22):
        P = [(x, y + dy) for x, y in P]; sides = ''
        for k in range(len(P)):
            p, q = P[k], P[(k + 1) % len(P)]
            if p[0] + q[0] > 0 and (q[1] + p[1]) / 2 >= 0: sides += f'<polygon points="{_pt([p, q, (q[0], q[1] + th), (p[0], p[1] + th)])}" fill="{side}"/>'
        return (f'<g class="{cls}"><polygon points="{_pt([(x + 8, y + th + 14) for x, y in P])}" fill="#000" opacity=".5" filter="url(#{i}sf)"/>{sides}'
                f'<polygon points="{_pt(P)}" fill="{top}"/><polygon points="{_pt(P)}" fill="#fff" filter="url(#{i}nz)" opacity=".25"/>'
                + ''.join(f'<path d="M{x0} {y0 + dy} q20 -10 40 0 t40 0" stroke="#fff" stroke-opacity=".25" fill="none"/>' for x0, y0 in ((P[0][0] + 20, P[0][1] + 60 - dy), (P[0][0] + 40, P[0][1] + 140 - dy))) + '</g>')
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title)
    s += ext(A, 'hsl(140,38%,44%)', 'hsl(140,35%,26%)', 'ga') + ext(Bp, 'hsl(200,40%,46%)', 'hsl(200,35%,28%)', 'gb')
    seam = [(370, 330), (360, 400), (340, 500), (370, 590)]
    s += f'<path class="sm" d="M{_pt([(x, y + dy) for x, y in seam])}" fill="none" stroke="hsl(46,100%,65%)" stroke-width="6" filter="url(#{i}gl)" pathLength="1"/>'
    s += f'<g class="la">' + _t(230, 420 + dy, left, 24, FG, 'middle', w=900) + '</g><g class="lb">' + _t(490, 440 + dy, right, 24, FG, 'middle', w=900) + '</g>'
    s += f'<g class="nw"><rect x="{360 - _w(new, 30) / 2 - 24:.0f}" y="{646 + dy - 44}" width="{_w(new, 30) + 48:.0f}" height="58" rx="29" fill="{AC}"/>' + _t(360, 646 + dy - 5, new, 30, '#111', 'middle', w=900) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .ga', 0, x=-70, opacity=0), S(f'#{i} .gb', 0, x=70, opacity=0),
                                                T(f'#{i} .ga', t0, x=-40, opacity=1, duration=.6, ease='expo.out'), T(f'#{i} .gb', t0 + .15, x=40, opacity=1, duration=.6, ease='expo.out'),
                                                _rv(f'#{i} .la', t0 + .3, 10), _rv(f'#{i} .lb', t0 + .45, 10),
                                                T(f'#{i} .ga', t_merge, x=0, duration=.5, ease='power3.in'), T(f'#{i} .gb', t_merge, x=0, duration=.5, ease='power3.in'),
                                                T(f'#{i} .la', t_merge, x=0, duration=.5), S(f'#{i} .sm', 0, strokeDasharray=1, strokeDashoffset=1),
                                                T(f'#{i} .sm', t_merge + .5, strokeDashoffset=0, duration=.6), T(f'#{i} .ct', t_merge + .5, y=4, duration=.06, yoyo=True, repeat=3),
                                                _rv(f'#{i} .nw', t_merge + .9, 16)]
    s += _note(source)
    return _out(i, a, b, 'r_sapnhap', s, j), j, [(t0, 'whoosh'), (t_merge + .5, 'block'), (t_merge + .9, 'ding')]


def mocqh(i, a, b, steps, kicker='QUY HOẠCH', title='Tiến trình', source=''):
    """con đường 3D có cột mốc cắm cờ cho từng giai đoạn; cờ dựng lên theo lời, đoạn đã qua trải nhựa vàng; steps=[(giai đoạn, t)] ≤5"""
    n = min(5, len(steps)); I = _iso(90, 360 if title else 310, 34)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, -.6, 10, 1.6, 'hsl(105,28%,36%)')
    s += f'<polygon points="{_P4(I, 0, 0, 10, 1)}" fill="hsl(30,25%,48%)"/><polygon class="pv" points="{_P4(I, 0, 0, 10, 1)}" fill="#33363b"/>'
    s += f'<path class="pl" d="M{_pt([I(0, .5), I(10, .5)])}" stroke="hsl(46,95%,60%)" stroke-width="3" stroke-dasharray="10 8"/>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .pv,#{i} .pl', 0, scaleX=0, transformOrigin='0% 50%')]
    for k, (st, t) in enumerate(steps[:n]):
        u = .6 + k * 8.8 / max(1, n - 1); px, py = I(u, -.1); up = k % 2 == 0
        s += (f'<g class="m{k}"><ellipse cx="{px + 6:.0f}" cy="{py + 2:.0f}" rx="10" ry="4" fill="#000" opacity=".4"/><path d="M{px:.0f} {py:.0f} V{py - 90:.0f}" stroke="#ddd" stroke-width="4"/>'
              f'<path d="M{px:.0f} {py - 90:.0f} l44 12 l-44 12 z" fill="{AC if k == n - 1 else "hsl(356,75%,52%)"}"/><circle cx="{px:.0f}" cy="{py - 92:.0f}" r="4" fill="#fff"/>'
              + _t(px + 6, py - 66, f'{k + 1:02d}', 14, '#111', 'start', w=900) + '</g>'
              f'<g class="t{k}">' + ''.join(_t(px + 52, py - 70 + q * 24, l, 21, FG, 'start', w=800) for q, l in enumerate(_wrap2(st, 14))) + '</g>')
        j += [S(f'#{i} .m{k}', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .m{k}', t, scaleY=1, duration=.5, ease='back.out(2)'), _rv(f'#{i} .t{k}', t + .1, 12, .5),
              T(f'#{i} .pv,#{i} .pl', t, scaleX=(k + .6) / n if k < n - 1 else 1, duration=.5, ease='power2.out')]
    s += _src(source)
    return _out(i, a, b, 'r_mocqh', s, j), j, [(t, 'tick') for _, t in steps[:n]]
def _wrap2(t, n=12):
    w = t.split()
    if len(t) <= n or len(w) < 2: return [t]
    k = min(range(1, len(w)), key=lambda m: abs(len(' '.join(w[:m])) - len(t) / 2)); return [' '.join(w[:k]), ' '.join(w[k:])]


def xoatreo(i, a, b, t0, t_free, tag='', kicker='QUY HOẠCH', title='Gỡ quy hoạch treo', source=''):
    """khu đất bỏ hoang cỏ dại, rào xích + ổ khoá; t_free: khoá bật, rào đổ, cẩu tháp dựng, nhà mọc lên"""
    I = _iso(360, 320 if title else 260, 32)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 7, 7, 'hsl(80,25%,38%)')
    random.seed(5)
    s += f'<g class="wd">' + ''.join(f'<path d="M{x:.0f} {y:.0f} l-3 -10 M{x:.0f} {y:.0f} l2 -12 M{x:.0f} {y:.0f} l6 -9" stroke="hsl(70,35%,{40 + random.randint(0, 15)}%)" stroke-width="2"/>' for x, y in (I(random.uniform(.3, 6.7), random.uniform(.3, 6.7)) for _ in range(70))) + '</g>'
    fen = ''.join(f'<path d="M{_pt([I(*p), I(*q)])}" stroke="#aab" stroke-width="2" stroke-dasharray="5 3"/>' for p, q in (((.3, .3), (6.7, .3)), ((6.7, .3), (6.7, 6.7)), ((6.7, 6.7), (.3, 6.7)), ((.3, 6.7), (.3, .3))))
    fen += ''.join(f'<path d="M{_pt([I(x, y), I(x, y, .9)])}" stroke="#889" stroke-width="3"/>' for x, y in ((.3, .3), (3.5, .3), (6.7, .3), (6.7, 3.5), (6.7, 6.7), (3.5, 6.7), (.3, 6.7), (.3, 3.5)))
    fen += ''.join(f'<path d="M{_pt([I(*p, .7), I(*q, .7)])}" stroke="#aab" stroke-width="2" stroke-dasharray="5 3"/>' for p, q in (((.3, 6.7), (6.7, 6.7)), ((6.7, .3), (6.7, 6.7))))
    s += f'<g class="fn">{fen}</g>'
    hs = ''.join(_house(I, x, y, .9, 1.4, 1.2, hue, 'bd') for x, y, hue in ((1, 1, 25), (2.1, 1, 205), (3.2, 1, 8), (1, 4.2, 32), (2.1, 4.2, 25), (4.6, 3.6, 205), (5.6, 3.6, 8)))
    s += hs
    cx_, cy_ = I(5.6, 1.2)
    s += (f'<g class="cr"><path d="M{cx_:.0f} {cy_:.0f} V{cy_ - 190:.0f}" stroke="hsl(46,95%,52%)" stroke-width="7"/>'
          + ''.join(f'<path d="M{cx_ - 4:.0f} {cy_ - 10 - q * 18:.0f} l8 -18 M{cx_ + 4:.0f} {cy_ - 10 - q * 18:.0f} l-8 -18" stroke="hsl(46,80%,40%)" stroke-width="1.5"/>' for q in range(10))
          + f'<path d="M{cx_ - 150:.0f} {cy_ - 190:.0f} H{cx_ + 60:.0f}" stroke="hsl(46,95%,52%)" stroke-width="7"/><rect x="{cx_ + 30:.0f}" y="{cy_ - 198:.0f}" width="30" height="20" fill="#555"/>'
          f'<path class="hk" d="M{cx_ - 110:.0f} {cy_ - 186:.0f} V{cy_ - 120:.0f}" stroke="#333" stroke-width="2"/><rect x="{cx_ - 122:.0f}" y="{cy_ - 120:.0f}" width="24" height="14" fill="hsl(28,45%,45%)"/></g>')
    lx, ly = 360, 440 if title else 380
    s += (f'<g class="lk"><path class="sh" d="M{lx - 28} {ly} V{ly - 34} a28 28 0 0 1 56 0 V{ly}" fill="none" stroke="url(#{i}mt)" stroke-width="12"/>'
          f'<rect x="{lx - 46}" y="{ly - 4}" width="92" height="76" rx="12" fill="hsl(44,80%,48%)" filter="url(#{i}sh)"/><rect x="{lx - 46}" y="{ly - 4}" width="92" height="20" rx="10" fill="#fff" opacity=".2"/>'
          f'<circle cx="{lx}" cy="{ly + 30}" r="9" fill="#2a2a2a"/><rect x="{lx - 3}" y="{ly + 32}" width="6" height="18" fill="#2a2a2a"/></g>')
    if tag: s += f'<g class="tg"><rect x="{360 - _w(tag, 22) / 2 - 22:.0f}" y="{(320 if title else 260) + 7 * 32 + 66}" width="{_w(tag, 22) + 44:.0f}" height="48" rx="24" fill="{AC}"/>' + _t(360, (320 if title else 260) + 7 * 32 + 98, tag, 22, '#111', 'middle', w=900) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .bd,#{i} .cr,#{i} .tg', 0, opacity=0),
                                                S(f'#{i} .lk', 0, scale=0, svgOrigin=f'{lx} {ly + 30}'), T(f'#{i} .lk', t0, scale=1, duration=.45, ease='back.out(2)', svgOrigin=f'{lx} {ly + 30}'),
                                                T(f'#{i} .sh', t_free, y=-22, duration=.25, ease='back.out(3)'), T(f'#{i} .lk', t_free + .35, y=80, opacity=0, rotation=25, duration=.45, ease='power2.in', svgOrigin=f'{lx} {ly + 30}'),
                                                T(f'#{i} .fn', t_free + .3, opacity=0, y=14, duration=.4), T(f'#{i} .wd', t_free + .5, opacity=0, duration=.5),
                                                S(f'#{i} .bd', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .bd', t_free + .8, opacity=1, scaleY=1, duration=.5, stagger=.08, ease='expo.out'),
                                                S(f'#{i} .cr', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .cr', t_free + .6, opacity=1, scaleY=1, duration=.5, ease='expo.out'),
                                                T(f'#{i} .hk', t_free + 1.2, attr={'d': f'M{cx_ - 110:.0f} {cy_ - 186:.0f} V{cy_ - 150:.0f}'}, duration=.6, yoyo=True, repeat=3), _rv(f'#{i} .tg', t_free + 1.4, 12)]
    s += _note(source)
    return _out(i, a, b, 'r_xoatreo', s, j), j, [(t0, 'metal'), (t_free, 'ratchet'), (t_free + .8, 'block'), (t_free + 1.4, 'ding')]


# ================================================================== HẠ TẦNG ==
def tiendo(i, a, b, t0, pct, tag='', kicker='TIẾN ĐỘ', title='', source=''):
    """đoạn đường 3D đang thi công: phần đã trải nhựa tới pct%, xe lu ở mép, máy xúc trên nền đất, cọc tiêu; số % lớn"""
    f = min(1, (_isn(pct) or 50) / 100); I = _iso(130, 470 if title else 420, 36); L = 10
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _numblk(pct, '%', 380 if title else 330, 140, 56)
    s += _ground(I, i, 0, -1.2, L, 2.4, 'hsl(100,26%,36%)')
    s += f'<polygon points="{_P4(I, 0, 0, L, 1.3)}" fill="hsl(30,35%,46%)"/><polygon points="{_P4(I, 0, 0, L, 1.3)}" fill="#fff" filter="url(#{i}nz)" opacity=".35"/>'
    s += f'<g class="rd"><polygon points="{_P4(I, 0, 0, L * f, 1.3)}" fill="#2f3237"/><path d="M{_pt([I(0, .65), I(L * f, .65)])}" stroke="#fff" stroke-width="3" stroke-dasharray="14 12"/>'
    s += f'<path d="M{_pt([I(0, 0), I(L * f, 0)])}" stroke="#ddd" stroke-width="2"/><path d="M{_pt([I(0, 1.3), I(L * f, 1.3)])}" stroke="#ddd" stroke-width="2"/></g>'
    for k in range(9): s += f'<g class="cn">' + _box(I, .5 + k * 1.1, 1.5, .14, .14, .35, 'hsl(20,90%,55%)', 'hsl(20,85%,45%)', 'hsl(20,80%,35%)') + f'<polygon points="{_P4(I, .5 + k * 1.1, 1.5, .64 + k * 1.1, 1.64, .2)}" fill="#fff"/></g>'
    rx = L * f
    roller = (_box(I, rx - .9, .3, .8, .7, .45, 'hsl(46,95%,55%)', 'hsl(44,90%,45%)', 'hsl(40,85%,35%)') + _box(I, rx - .75, .4, .4, .5, .85, '#d8dce2', '#9aa0a8', '#6c727a')
              + _box(I, rx - .1, .2, .35, .9, .4, '#7d838c', '#5c6168', '#3f4348'))
    s += f'<g class="rl">{roller}</g>'
    ex_ = I(L * f + 2.2, .4)
    s += (f'<g class="ex">' + _box(I, L * f + 1.6, .1, 1.0, .9, .5, 'hsl(46,95%,55%)', 'hsl(44,90%,45%)', 'hsl(40,85%,35%)') + _box(I, L * f + 1.7, .2, .5, .6, .9, 'hsl(46,95%,58%)', 'hsl(44,90%,45%)', 'hsl(40,85%,35%)')
          + f'<path class="arm" d="M{ex_[0]:.0f} {ex_[1] - 40:.0f} l60 -46 l40 50" stroke="hsl(44,90%,45%)" stroke-width="9" fill="none" stroke-linejoin="round"/>'
          f'<path d="M{ex_[0] + 100:.0f} {ex_[1] - 36:.0f} l12 14 h-26 z" fill="#555"/></g>')
    if tag: s += f'<g class="tg">' + _t(60, (380 if title else 330) + 50, tag, 22, AC, w=900, ls=1) + '</g>'
    ox, oy = I(0, 0); ex, ey = I(rx, 0)
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0, pct) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .rd', 0, scaleX=0, transformOrigin='0% 50%'),
                                                                   T(f'#{i} .rd', t0, scaleX=1, duration=1.4, ease='expo.out'), S(f'#{i} .rl', 0, x=ox - ex, y=oy - ey),
                                                                   T(f'#{i} .rl', t0, x=0, y=0, duration=1.4, ease='expo.out'), S(f'#{i} .cn', 0, scale=0, transformOrigin='50% 100%'),
                                                                   T(f'#{i} .cn', a + .3, scale=1, duration=.3, stagger=.05, ease='back.out(2)'),
                                                                   T(f'#{i} .arm', t0 + .5, rotation=-8, duration=.6, yoyo=True, repeat=max(0, int((b - t0 - .5) / .6) - 1), svgOrigin=f'{ex_[0]:.0f} {ex_[1] - 40:.0f}')]
    if tag: j.append(_rv(f'#{i} .tg', t0 + 1.2, 10))
    s += _src(source)
    return _out(i, a, b, 'r_tiendo', s, j), j, [(t0, 'ratchet'), (t0 + 1.3, 'ding')]


def _card(i, X0, Y0, W, H, body):
    return (f'<clipPath id="{i}cc"><rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="22"/></clipPath><g class="cd" filter="url(#{i}sh)"><g clip-path="url(#{i}cc)">{body}</g></g>'
            f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="22" fill="none" stroke="#fff" stroke-opacity=".08"/>')
def _sky(i, X0, Y0, W, H, HZ, c0='hsl(215,45%,22%)', c1='hsl(28,85%,62%)', sunx=None):
    s = f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" fill="url(#{i}sk)"/>'
    if sunx: s += f'<circle cx="{sunx}" cy="{HZ - 8}" r="110" fill="url(#{i}sun)"/>'
    for k, (cx_, cy_, sc) in enumerate(((X0 + 80, Y0 + 50, 1), (X0 + 360, Y0 + 34, .8), (X0 + 540, Y0 + 70, .9))):
        s += f'<g class="cl{k}" opacity=".5">' + ''.join(f'<ellipse cx="{cx_ + dx * sc:.0f}" cy="{cy_ + dy * sc:.0f}" rx="{rx * sc:.0f}" ry="{ry * sc:.0f}" fill="hsl(25,60%,85%)" filter="url(#{i}sf)"/>' for dx, dy, rx, ry in ((0, 0, 60, 16), (40, -10, 44, 18), (-40, 4, 40, 12))) + '</g>'
    s += f'<path d="M{X0} {HZ - 30} L{X0 + 40} {HZ - 70} L{X0 + 120} {HZ - 52} L{X0 + 200} {HZ - 92} L{X0 + 300} {HZ - 60} L{X0 + 410} {HZ - 98} L{X0 + 500} {HZ - 64} L{X0 + W} {HZ - 80} V{HZ} H{X0} Z" fill="hsl(230,25%,45%)" opacity=".55"/>'
    s += f'<path d="M{X0} {HZ} L{X0 + 70} {HZ - 46} L{X0 + 170} {HZ - 20} L{X0 + 270} {HZ - 58} L{X0 + 390} {HZ - 24} L{X0 + 500} {HZ - 52} L{X0 + W} {HZ - 18} V{HZ + 20} H{X0} Z" fill="hsl(160,25%,20%)" opacity=".9"/>'
    return s
def _skydefs(i, c0='hsl(215,45%,22%)', c1='hsl(28,85%,62%)'):
    return (_lg(f'{i}sk', c0, c1) + f'<radialGradient id="{i}sun"><stop offset="0" stop-color="hsl(40,100%,80%)" stop-opacity=".9"/><stop offset=".25" stop-color="hsl(32,100%,65%)" stop-opacity=".5"/>'
            f'<stop offset="1" stop-color="hsl(25,100%,55%)" stop-opacity="0"/></radialGradient>')


def duongsat(i, a, b, t0, stations=('BUÔN MA THUỘT', 'TUY HÒA'), kicker='ĐƯỜNG SẮT', title='', source=''):
    """phối cảnh đường ray đôi, tà vẹt, cột điện kéo; đoàn tàu lao tới từ chân trời, đèn pha sáng; biển ga ghi tuyến"""
    X0, Y0, W, H = 60, 300 if title else 230, 600, 380; HZ = Y0 + 150; VX = 360
    s = _defs(i) + _kit(i) + _skydefs(i, 'hsl(220,40%,25%)', 'hsl(35,80%,66%)') + _lg(f'{i}tn', '#f2f4f7', '#b8bec7') + '</defs>' + _head(kicker, title)
    body = _sky(i, X0, Y0, W, H, HZ, sunx=VX - 160) + f'<rect x="{X0}" y="{HZ}" width="{W}" height="{H - 150}" fill="hsl(95,28%,26%)"/>'
    body += f'<polygon points="{_pt([(VX - 30, HZ), (VX + 30, HZ), (X0 + W + 120, Y0 + H), (X0 - 120, Y0 + H)])}" fill="hsl(30,15%,40%)"/><polygon points="{_pt([(VX - 30, HZ), (VX + 30, HZ), (X0 + W + 120, Y0 + H), (X0 - 120, Y0 + H)])}" fill="#fff" filter="url(#{i}nz)" opacity=".4"/>'
    for q in range(22):
        u = (q / 21) ** 2.2; y = HZ + (H - 150) * u; hw = 26 + 330 * u
        body += f'<rect class="sl" x="{VX - hw:.0f}" y="{y:.0f}" width="{hw * 2:.0f}" height="{1 + 10 * u:.1f}" fill="hsl(28,30%,{30 + 6 * u:.0f}%)"/>'
    for r in (-1, 1):
        for g_ in (-1, 1):
            xb = VX + r * 150 + g_ * 70
            body += f'<path d="M{VX + r * 12 + g_ * 5} {HZ} L{xb} {Y0 + H}" stroke="hsl(210,8%,72%)" stroke-width="5"/>'
    for side in (-1, 1):
        for q in range(5):
            u = ((q + .5) / 5) ** 1.7; x = VX + side * (40 + 330 * u); yb = HZ + (H - 160) * u; ph = 20 + 200 * u
            body += f'<path d="M{x:.0f} {yb:.0f} V{yb - ph:.0f} h{-side * ph * .35:.0f}" stroke="hsl(220,8%,55%)" stroke-width="{1 + 3 * u:.1f}" fill="none"/>'
        body += f'<path d="M{VX + side * 14} {HZ - 18} L{VX + side * 150} {Y0 - 10}" stroke="#222" stroke-width="1.2" opacity=".6"/>'
    tw = 150
    train = (f'<g class="tn"><path d="M{VX - tw} {HZ + 210} V{HZ + 20} Q{VX - tw} {HZ - 40} {VX - tw + 40} {HZ - 46} H{VX + tw - 40} Q{VX + tw} {HZ - 40} {VX + tw} {HZ + 20} V{HZ + 210} Z" fill="url(#{i}tn)"/>'
             f'<path d="M{VX - tw + 18} {HZ + 40} Q{VX - tw + 22} {HZ - 20} {VX - tw + 56} {HZ - 24} H{VX + tw - 56} Q{VX + tw - 22} {HZ - 20} {VX + tw - 18} {HZ + 40} Z" fill="#1d2a38"/>'
             f'<path d="M{VX - tw + 40} {HZ - 10} L{VX - 20} {HZ - 18}" stroke="#fff" stroke-opacity=".35" stroke-width="6"/>'
             f'<rect x="{VX - tw}" y="{HZ + 110}" width="{tw * 2}" height="26" fill="hsl(356,75%,48%)"/><rect x="{VX - tw}" y="{HZ + 140}" width="{tw * 2}" height="8" fill="hsl(46,95%,55%)"/>'
             f'<circle cx="{VX - tw + 46}" cy="{HZ + 176}" r="15" fill="#fffbe6" filter="url(#{i}gl)"/><circle cx="{VX + tw - 46}" cy="{HZ + 176}" r="15" fill="#fffbe6" filter="url(#{i}gl)"/>'
             f'<rect x="{VX - 40}" y="{HZ + 70}" width="80" height="22" rx="4" fill="#111"/>' + _t(VX, HZ + 87, 'SE', 16, 'hsl(46,95%,60%)', 'middle', w=900) + '</g>')
    body += train
    sg = ' → '.join(stations[:3])
    body += (f'<g class="sg"><rect x="{X0 + 24}" y="{Y0 + 22}" width="{min(W - 48, _w(sg, 18) + 40):.0f}" height="44" rx="8" fill="hsl(210,70%,30%)" stroke="#fff" stroke-width="2"/>'
             + _t(X0 + 44, Y0 + 51, sg, 18, '#fff', w=800) + '</g>')
    s += _card(i, X0, Y0, W, H, body) + _note(source).replace('y="690"', f'y="{Y0 + H + 26}"')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .cd', a + .1, 30, .8), S(f'#{i} .tn', 0, scale=.06, svgOrigin=f'{VX} {HZ}'),
                                                T(f'#{i} .tn', t0, scale=1.25, duration=max(1, b - t0 - .2), ease='power2.in', svgOrigin=f'{VX} {HZ}'),
                                                _rv(f'#{i} .sg', a + .4, 10), T(f'#{i} .cl0', a, x=30, duration=b - a, ease='none'), T(f'#{i} .cl2', a, x=-24, duration=b - a, ease='none')]
    return _out(i, a, b, 'r_duongsat', s, j), j, [(t0, 'air'), (b - 1, 'whoosh')]


def cau(i, a, b, t0, t_done=None, tag='', kicker='HẠ TẦNG', title='', source=''):
    """cầu dây văng lúc hoàng hôn: trụ tháp, dây văng toả, mặt cầu 2 bên vươn ra hợp long, mặt sông phản chiếu"""
    X0, Y0, W, H = 60, 300 if title else 230, 600, 380; HZ = Y0 + 210; td = t_done or t0 + 1.6
    s = _defs(i) + _kit(i) + _skydefs(i, 'hsl(225,45%,24%)', 'hsl(20,85%,62%)') + _lg(f'{i}rv', 'hsl(20,50%,45%)', 'hsl(215,45%,18%)') + '</defs>' + _head(kicker, title)
    body = _sky(i, X0, Y0, W, H, HZ, sunx=X0 + 470) + f'<rect x="{X0}" y="{HZ}" width="{W}" height="{H - 210}" fill="url(#{i}rv)"/>'
    body += ''.join(f'<path class="wv" d="M{X0 - 60} {HZ + 20 + k * 24} q20 -5 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0" stroke="#fff" stroke-opacity="{.12 + k * .04:.2f}" fill="none"/>' for k in range(6))
    body += f'<rect x="{X0 + 430}" y="{HZ + 4}" width="80" height="120" fill="hsl(40,100%,70%)" opacity=".18" filter="url(#{i}sf)"/>'
    DY = HZ - 30
    for k, x in enumerate((X0 + 180, X0 + 420)):
        body += (f'<g class="py{k}"><path d="M{x - 26} {HZ + 40} L{x - 8} {Y0 + 40} H{x + 8} L{x + 26} {HZ + 40} Z" fill="hsl(215,10%,78%)"/><path d="M{x + 2} {Y0 + 40} L{x + 26} {HZ + 40} H{x + 8} Z" fill="hsl(215,12%,58%)"/>'
                 f'<rect x="{x - 22}" y="{HZ + 40}" width="44" height="40" fill="hsl(215,10%,40%)" opacity=".5"/></g>')
        for d in (-1, 1):
            for q in range(6): body += f'<path class="cb" d="M{x} {Y0 + 52 + q * 10} L{x + d * (24 + q * 22)} {DY}" stroke="hsl(46,80%,70%)" stroke-width="1.6" opacity=".9" pathLength="1"/>'
    body += (f'<rect class="dl" x="{X0}" y="{DY}" width="{W / 2}" height="14" fill="hsl(215,15%,32%)"/><rect class="dr" x="{X0 + W / 2}" y="{DY}" width="{W / 2}" height="14" fill="hsl(215,15%,32%)"/>'
             f'<rect class="dl" x="{X0}" y="{DY - 4}" width="{W / 2}" height="4" fill="hsl(215,10%,70%)"/><rect class="dr" x="{X0 + W / 2}" y="{DY - 4}" width="{W / 2}" height="4" fill="hsl(215,10%,70%)"/>'
             + ''.join(f'<circle class="lt" cx="{X0 + 20 + q * 40}" cy="{DY - 8}" r="2.5" fill="hsl(45,100%,80%)" filter="url(#{i}gl)"/>' for q in range(15))
             + f'<circle class="fl" cx="{X0 + W / 2}" cy="{DY + 7}" r="16" fill="hsl(46,100%,70%)" filter="url(#{i}gl)"/>')
    if tag: body += f'<g class="tg"><rect x="{X0 + W / 2 - _w(tag, 20) / 2 - 18:.0f}" y="{Y0 + 18}" width="{_w(tag, 20) + 36:.0f}" height="40" rx="20" fill="{AC}"/>' + _t(X0 + W / 2, Y0 + 45, tag, 20, '#111', 'middle', w=900) + '</g>'
    s += _card(i, X0, Y0, W, H, body) + _note(source).replace('y="690"', f'y="{Y0 + H + 26}"')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .cd', a + .1, 30, .8), T(f'#{i} .wv', a, x=40, duration=b - a, ease='none'),
                                                S(f'#{i} .py0,#{i} .py1', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .py0,#{i} .py1', t0, scaleY=1, duration=.7, stagger=.15, ease='expo.out'),
                                                S(f'#{i} .cb', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .cb', t0 + .6, strokeDashoffset=0, duration=.5, stagger=.02),
                                                S(f'#{i} .dl', 0, scaleX=0, transformOrigin='0% 50%'), S(f'#{i} .dr', 0, scaleX=0, transformOrigin='100% 50%'),
                                                T(f'#{i} .dl,#{i} .dr', t0 + .5, scaleX=1, duration=max(.4, td - t0 - .5), ease='power1.inOut'),
                                                S(f'#{i} .lt,#{i} .fl', 0, opacity=0), T(f'#{i} .lt', td + .1, opacity=1, duration=.05, stagger=.03),
                                                T(f'#{i} .fl', td, opacity=1, attr={'r': 70}, duration=.15), T(f'#{i} .fl', td + .15, opacity=0, attr={'r': 16}, duration=.6)]
    if tag: j.append(_rv(f'#{i} .tg', td + .3, 10))
    return _out(i, a, b, 'r_cau', s, j), j, [(t0, 'metal'), (td, 'ding')]


def thoigian(i, a, b, t0, t1, before, after, lb='HIỆN NAY', la='KHI CÓ ĐƯỜNG MỚI', kicker='THỜI GIAN DI CHUYỂN', title='', source=''):
    """đồng hồ bấm giờ kim loại: vòng đỏ = before, t1 rút ngắn thành vòng xanh = after; số trước bị gạch, số sau hiện lớn"""
    pb, pa = _isn(re.sub(r'[^\d.,]', '', str(before)) or None), _isn(re.sub(r'[^\d.,]', '', str(after)) or None); fa = (pa / pb) if pb and pa else .5
    cx, cy, r = 470, 470 if title else 420, 150
    s = (_defs(i) + _kit(i) + _rg(f'{i}fc', '#fbfbfa', '#d9dbde', .4, .3) + '</defs>' + _head(kicker, title)
         + f'<g class="wt"><rect x="{cx - 22}" y="{cy - r - 58}" width="44" height="34" rx="6" fill="url(#{i}mt)"/><rect x="{cx - 30}" y="{cy - r - 70}" width="60" height="18" rx="6" fill="url(#{i}mt)"/>'
         f'<rect x="{cx + r * .62}" y="{cy - r * .9}" width="26" height="20" rx="5" fill="url(#{i}mt)" transform="rotate(40 {cx + r * .62} {cy - r * .9})"/>'
         f'<circle cx="{cx}" cy="{cy}" r="{r + 22}" fill="url(#{i}mt)" filter="url(#{i}sh)"/><circle cx="{cx}" cy="{cy}" r="{r + 8}" fill="#2a2d33"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{i}fc)"/>'
         + ''.join(f'<path d="M{cx + (r - 10) * math.sin(k * math.pi / 30):.1f} {cy - (r - 10) * math.cos(k * math.pi / 30):.1f} L{cx + (r - (24 if k % 5 == 0 else 16)) * math.sin(k * math.pi / 30):.1f} {cy - (r - (24 if k % 5 == 0 else 16)) * math.cos(k * math.pi / 30):.1f}" stroke="#222" stroke-width="{3 if k % 5 == 0 else 1.2}"/>' for k in range(60))
         + f'<circle class="ar" cx="{cx}" cy="{cy}" r="{r - 46}" fill="none" stroke="hsl(356,80%,52%)" stroke-width="22" pathLength="100" stroke-dasharray="0 100" transform="rotate(-90 {cx} {cy})" opacity=".9"/>'
         f'<g class="hd"><path d="M{cx - 4} {cy + 20} L{cx} {cy - r + 22} L{cx + 4} {cy + 20} Z" fill="hsl(356,80%,48%)"/></g><circle cx="{cx}" cy="{cy}" r="9" fill="#222"/>'
         f'<path d="M{cx - r * .7} {cy - r * .55} a{r} {r} 0 0 1 {r * .8} {-r * .45}" stroke="#fff" stroke-opacity=".7" stroke-width="10" fill="none" stroke-linecap="round"/></g>')
    s += (f'<g class="lb_">' + _t(60, cy - 70, lb, 18, MUT, w=800, ls=2) + _t(60, cy - 10, before, 64, MUT, cls='bv', w=900) + f'<rect class="st" x="56" y="{cy - 34}" width="{_w(before, 64) + 8:.0f}" height="5" fill="#ff5a5f"/></g>'
          f'<g class="la_">' + _t(60, cy + 60, la, 18, AC, w=800, ls=2) + _t(60, cy + 130, after, 76, FG, w=900) + '</g>')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .wt', a + .05, 30, .8), _rv(f'#{i} .lb_', t0, 14),
                                                T(f'#{i} .ar', t0, attr={'stroke-dasharray': '92 8'}, duration=1, ease='expo.out'),
                                                S(f'#{i} .hd', 0, rotation=0, svgOrigin=f'{cx} {cy}'), T(f'#{i} .hd', t0, rotation=331, duration=1, ease='expo.out', svgOrigin=f'{cx} {cy}'),
                                                S(f'#{i} .st', 0, scaleX=0, transformOrigin='0% 50%'), T(f'#{i} .st', t1, scaleX=1, duration=.4),
                                                T(f'#{i} .ar', t1, attr={'stroke-dasharray': f'{92 * fa:.1f} {100 - 92 * fa:.1f}', 'stroke': 'hsl(145,62%,45%)'}, duration=.9, ease='expo.inOut'),
                                                T(f'#{i} .hd', t1, rotation=331 * fa, duration=.9, ease='expo.inOut', svgOrigin=f'{cx} {cy}'), _rv(f'#{i} .la_', t1 + .4, 20)]
    s += _src(source)
    return _out(i, a, b, 'r_thoigian', s, j), j, [(t0, 'tick'), (t1, 'whoosh'), (t1 + .4, 'ding')]


def anhhuong(i, a, b, center='SÂN BAY', rings=(), pins=(), kind='sanbay', kicker='VỊ TRÍ', title='Bán kính ảnh hưởng', source=''):
    """mặt bằng 3D: công trình trung tâm (sân bay có đường băng + nhà ga / toà nhà), vòng bán kính loang trên mặt đất, ghim đỏ 3D các điểm; rings=[('5 KM', t)] pins=[('TÊN', t)]"""
    I = _iso(360, 290 if title else 240, 36); C = (5, 5)
    s = _defs(i) + _kit(i) + _rg(f'{i}pn', 'hsl(356,90%,62%)', 'hsl(356,80%,35%)', .35, .3) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,26%,36%)')
    random.seed(8)
    for _ in range(14):
        x, y = random.uniform(.5, 9.5), random.uniform(.5, 9.5)
        if abs(x - 5) + abs(y - 5) > 3: s += _tree(I, i, x, y, .7, 'tr')
    if kind == 'sanbay':
        s += (f'<g class="cc"><polygon points="{_P4(I, 4.6, 2.2, 5.4, 7.8)}" fill="#3a3d42"/><path d="M{_pt([I(5, 2.4), I(5, 7.6)])}" stroke="#fff" stroke-width="2" stroke-dasharray="10 8"/>'
              + _box(I, 5.8, 4.2, 1.6, .9, .55, '#e9ecef', '#c3c8ce', '#8e959d') + f'<polygon points="{_P4(I, 5.85, 4.25, 7.35, 5.05, .56)}" fill="hsl(205,40%,55%)" opacity=".6"/>'
              + _box(I, 6.9, 3.4, .3, .3, 1.4, '#e9ecef', '#c3c8ce', '#8e959d') + f'<polygon points="{_P4(I, 6.82, 3.32, 7.28, 3.78, 1.4)}" fill="hsl(195,60%,50%)"/></g>')
    else:
        s += '<g class="cc">' + _tower(I, i, 4.4, 4.4, 1.2, 1.2, 2.6, 'twr') + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), _rv(f'#{i} .cc', a + .3, 20, .7),
                                                S(f'#{i} .tr', 0, scale=0, transformOrigin='50% 100%'), T(f'#{i} .tr', a + .4, scale=1, duration=.3, stagger=.03, ease='back.out(2)')]
    for k, (lab, t) in enumerate(list(rings)[:3]):
        rr = 1.6 + k * 1.4; P = [I(C[0] + rr * math.cos(u), C[1] + rr * math.sin(u)) for u in [q * math.pi / 30 for q in range(61)]]
        s += f'<polygon class="rg{k}" points="{_pt(P)}" fill="hsl(46,100%,60%)" fill-opacity="{.12 - k * .03:.2f}" stroke="hsl(46,100%,65%)" stroke-width="2.5" stroke-dasharray="8 6"/>'
        lx, ly = I(C[0] - rr * .707, C[1] - rr * .707)
        s += f'<g class="rl{k}"><rect x="{lx - 34:.0f}" y="{ly - 16:.0f}" width="68" height="28" rx="14" fill="rgba(0,0,0,.65)"/>' + _t(lx, ly + 4, lab, 15, AC, 'middle', w=800) + '</g>'
        cx_, cy_ = I(*C)
        j += [S(f'#{i} .rg{k}', 0, scale=0, opacity=0, svgOrigin=f'{cx_:.0f} {cy_:.0f}'), T(f'#{i} .rg{k}', t, scale=1, opacity=1, duration=.9, ease='expo.out', svgOrigin=f'{cx_:.0f} {cy_:.0f}'), _rv(f'#{i} .rl{k}', t + .3, 8)]
    PP = [(8.6, 3.2), (2.2, 8.4), (8.4, 8.0), (1.8, 2.6), (6.8, 9.2)]
    for k, (lab, t) in enumerate(list(pins)[:5]):
        px, py = I(*PP[k])
        s += (f'<g class="pn{k}"><ellipse cx="{px + 6:.0f}" cy="{py:.0f}" rx="9" ry="3.5" fill="#000" opacity=".4"/><path d="M{px:.0f} {py:.0f} C{px - 16:.0f} {py - 22:.0f} {px - 16:.0f} {py - 40:.0f} {px:.0f} {py - 40:.0f} C{px + 16:.0f} {py - 40:.0f} {px + 16:.0f} {py - 22:.0f} {px:.0f} {py:.0f} Z" fill="url(#{i}pn)"/>'
              f'<circle cx="{px:.0f}" cy="{py - 28:.0f}" r="5" fill="#fff"/>' + _t(px, py - 50, lab, 17, FG, 'middle', w=900) + '</g>')
        j += [S(f'#{i} .pn{k}', 0, y=-40, opacity=0), T(f'#{i} .pn{k}', t, y=0, opacity=1, duration=.5, ease='bounce.out')]
    cx_, cy_ = I(*C)
    s += f'<g class="cl_"><rect x="{cx_ - _w(center, 18) / 2 - 16:.0f}" y="{cy_ + 34:.0f}" width="{_w(center, 18) + 32:.0f}" height="34" rx="17" fill="{AC}"/>' + _t(cx_, cy_ + 57, center, 18, '#111', 'middle', w=900) + '</g>'
    j.append(_rv(f'#{i} .cl_', a + .6, 10))
    s += _note(source)
    return _out(i, a, b, 'r_anhhuong', s, j), j, [(a + .3, 'block')] + [(t, 'air') for _, t in list(rings)[:3]] + [(t, 'pop') for _, t in list(pins)[:5]]


# ============================================================ THIẾT BỊ (màn hình thật) ==
def _device(i, x, y, w, h, kind='tablet'):
    """khung thiết bị nhôm + kính phản chiếu; trả (khung_dưới, phủ_kính_trên). Nội dung đặt giữa 2 lớp, trong vùng (x+b, y+b, w-2b, h-2b)"""
    bz = 16 if kind == 'tablet' else 12
    base = (f'<rect x="{x - 4}" y="{y - 4}" width="{w + 8}" height="{h + 8}" rx="{30 if kind == "tablet" else 14}" fill="url(#{i}mt)" filter="url(#{i}sh)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{26 if kind == "tablet" else 10}" fill="#0b0c0f"/>'
            f'<rect x="{x + bz}" y="{y + bz}" width="{w - 2 * bz}" height="{h - 2 * bz}" rx="8" fill="#12151b"/>')
    if kind == 'monitor':
        base = (f'<path d="M{x + w / 2 - 40} {y + h} L{x + w / 2 - 60} {y + h + 60} H{x + w / 2 + 60} L{x + w / 2 + 40} {y + h} Z" fill="url(#{i}mt)"/>'
                f'<ellipse cx="{x + w / 2}" cy="{y + h + 64}" rx="110" ry="12" fill="url(#{i}mt)"/>') + base
    glass = f'<path d="M{x + bz} {y + bz} H{x + w * .55} L{x + w * .3} {y + h - bz} H{x + bz} Z" fill="#fff" opacity=".05"/>'
    if kind == 'tablet': glass += f'<circle cx="{x + w / 2}" cy="{y + 8}" r="3" fill="#333"/>'
    return base, glass


# =============================================================== THỊ TRƯỜNG ==
def chukytt(i, a, b, t0, t_pin, pos=1, phases=('PHỤC HỒI', 'TĂNG TRƯỞNG', 'BÃO HOÀ', 'ĐIỀU CHỈNH'), now='HIỆN TẠI', kicker='THỊ TRƯỜNG', title='Chu kỳ bất động sản', source=''):
    """máy tính bảng hiển thị sóng chu kỳ 4 pha; chấm sáng chạy tới pha `pos` (nhận định cá nhân)"""
    X, Y, W, H = 70, 300 if title else 240, 580, 360
    base, glass = _device(i, X, Y, W, H)
    sx0, sx1, cy, amp = X + 50, X + W - 50, Y + H / 2 + 10, 95
    def P(u): return sx0 + (sx1 - sx0) * u, cy + amp * math.cos(2 * math.pi * u)
    pts = [P(k / 100) for k in range(101)]; d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    U = [.12, .37, .63, .88]; COL = ['#3ddc84', AC, '#ff5a5f', '#7aa7ff']
    scr = (''.join(f'<path d="M{X + 30} {Y + 40 + k * 40} H{X + W - 30}" stroke="#fff" stroke-opacity=".05"/>' for k in range(8))
           + f'<path d="{d} L{sx1} {Y + H - 20} L{sx0} {Y + H - 20} Z" fill="{AC}" opacity=".08"/><path class="wv" d="{d}" fill="none" stroke="{FG}" stroke-width="4" pathLength="1"/>')
    for k, ph in enumerate(phases[:4]):
        x, y = P(U[k]); up = y < cy
        scr += f'<g class="ph{k}"><circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{COL[k]}"/>' + _t(x + (14, -14, 14, -14)[k], y + (30, 6, 6, 30)[k], ph, 17, COL[k], ('start', 'end', 'start', 'end')[k], w=800) + '</g>'
    x, y = P(U[pos])
    scr += (f'<circle class="pl" cx="{x:.0f}" cy="{y:.0f}" r="14" fill="none" stroke="{AC}" stroke-width="3"/><circle class="dt" cx="{x:.0f}" cy="{y:.0f}" r="12" fill="{AC}" filter="url(#{i}gl)"/>'
            f'<g class="nw"><rect x="{x - _w(now, 16) / 2 - 14:.0f}" y="{y + (44 if y < cy else -70):.0f}" width="{_w(now, 16) + 28:.0f}" height="30" rx="15" fill="{AC}"/>'
            + _t(x, y + (65 if y < cy else -49), now, 16, '#111', 'middle', w=900) + '</g>')
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + f'<g class="dv">{base}{scr}{glass}</g>' + _note(source or OBS_)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .dv', a + .05, 40, .8), S(f'#{i} .wv', 0, strokeDasharray=1, strokeDashoffset=1),
                                                T(f'#{i} .wv', t0, strokeDashoffset=0, duration=1.0, ease='power2.inOut'), S(f'#{i} [class^=ph]', 0, opacity=0),
                                                T(f'#{i} g[class^=ph]', t0 + .5, opacity=1, duration=.3, stagger=.15), S(f'#{i} .dt,#{i} .pl,#{i} .nw', 0, opacity=0),
                                                T(f'#{i} .dt', t_pin - .2, opacity=1, duration=.2), T(f'#{i} .pl', t_pin, opacity=1, attr={'r': 50}, duration=1, repeat=2), T(f'#{i} .pl', t_pin + 3, opacity=0, duration=.1),
                                                _rv(f'#{i} .nw', t_pin + .1, 10)]
    return _out(i, a, b, 'r_chukytt', s, j), j, [(t0, 'whoosh'), (t_pin, 'ding')]
OBS_ = 'nhận định cá nhân'


def cungcau(i, a, b, t0, t_tip, tip='cau', supply='CUNG', demand='CẦU', gap='', kicker='THỊ TRƯỜNG', title='Cung – cầu', source=''):
    """cân đồng: đĩa trái CUNG (nhà), đĩa phải CẦU (người); t_tip cân nghiêng về bên nặng hơn (tip='cau' | 'cung')"""
    cx, top = 360, 330 if title else 270; arm = 200; ang = 9 if tip == 'cau' else -9
    s = _defs(i) + _kit(i) + _lg(f'{i}br', 'hsl(44,75%,62%)', 'hsl(36,70%,32%)', 1, 1) + '</defs>' + _head(kicker, title)
    s += (f'<ellipse cx="{cx}" cy="{top + 330}" rx="150" ry="20" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
          f'<path d="M{cx - 110} {top + 330} Q{cx} {top + 290} {cx + 110} {top + 330} Z" fill="url(#{i}br)"/><rect x="{cx - 10}" y="{top + 10}" width="20" height="300" fill="url(#{i}br)"/>'
          f'<rect x="{cx - 4}" y="{top + 10}" width="5" height="300" fill="#fff" opacity=".3"/><circle cx="{cx}" cy="{top}" r="18" fill="url(#{i}br)"/>')
    def pan(side, items):
        px = cx + side * arm
        return (f'<g class="pan{side + 1}"><path d="M{px} {top} L{px - 70} {top + 130} M{px} {top} L{px + 70} {top + 130}" stroke="hsl(40,50%,55%)" stroke-width="2"/>'
                f'<path d="M{px - 90} {top + 130} Q{px} {top + 180} {px + 90} {top + 130} Z" fill="url(#{i}br)"/><ellipse cx="{px}" cy="{top + 130}" rx="90" ry="12" fill="hsl(44,70%,70%)"/>{items}</g>')
    I1 = _iso(cx - arm, top + 92, 18)
    houses = ''.join(_house(I1, x, y, .9, 1.2, 1.0, hue, 'hh') for x, y, hue in ((-1.4, .2, 25), (.1, -1.0, 205), (.4, .5, 8)))
    people = ''.join(_person(cx + arm + dx, top + 128, .7, sh) for dx, sh in ((-50, 'hsl(210,55%,45%)'), (-18, 'hsl(356,60%,50%)'), (14, 'hsl(145,45%,40%)'), (46, 'hsl(44,80%,50%)'), (-34, 'hsl(270,40%,50%)'), (30, 'hsl(20,70%,50%)')))
    beam = (f'<g class="bm"><rect x="{cx - arm - 10}" y="{top - 7}" width="{2 * arm + 20}" height="14" rx="7" fill="url(#{i}br)"/><rect x="{cx - arm}" y="{top - 6}" width="{2 * arm}" height="4" fill="#fff" opacity=".35"/></g>')
    s += beam + pan(-1, houses) + pan(1, people) + f'<circle cx="{cx}" cy="{top}" r="12" fill="url(#{i}br)"/>'
    s += _t(cx - arm, top + 262, supply, 26, FG, 'middle', cls='l1', w=900) + _t(cx + arm, top + 262, demand, 26, FG, 'middle', cls='l2', w=900)
    if gap: s += f'<g class="gp"><rect x="{cx - _w(gap, 20) / 2 - 18:.0f}" y="{top + 284}" width="{_w(gap, 20) + 36:.0f}" height="40" rx="20" fill="#ff5a5f"/>' + _t(cx, top + 311, gap, 20, '#fff', 'middle', w=900) + '</g>'
    dy = arm * math.sin(math.radians(ang))
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bm,#{i} .pan0,#{i} .pan2', a + .1, -30, .8), _rv(f'#{i} .l1', t0, 10), _rv(f'#{i} .l2', t0 + .15, 10),
                                                S(f'#{i} .hh', 0, y=-80, opacity=0), T(f'#{i} .hh', t0, y=0, opacity=1, duration=.4, stagger=.12, ease='bounce.out'),
                                                S(f'#{i} .ps', 0, y=-80, opacity=0), T(f'#{i} .ps', t0 + .3, y=0, opacity=1, duration=.4, stagger=.08, ease='bounce.out'),
                                                T(f'#{i} .bm', t_tip, rotation=ang, duration=1.2, ease='elastic.out(1,.5)', svgOrigin=f'{cx} {top}'),
                                                T(f'#{i} .pan0', t_tip, y=-dy, duration=1.2, ease='elastic.out(1,.5)'),
                                                T(f'#{i} .pan2', t_tip, y=dy, duration=1.2, ease='elastic.out(1,.5)')]
    if gap: j.append(_rv(f'#{i} .gp', t_tip + .5, 10))
    s += _note(source)
    return _out(i, a, b, 'r_cungcau', s, j), j, [(t0, 'block'), (t_tip, 'metal')]


def laisuat(i, a, b, t0, points, unit='%', kicker='TÀI CHÍNH', title='Lãi suất vay mua nhà', source=''):
    """bảng điện tử lãi suất ở quầy ngân hàng: chữ LED vàng phát sáng, dòng cuối nhấp nháy; points=[('2024', '9'), …] ≤5"""
    n = min(5, len(points)); X, Y, W = 70, 300 if title else 240, 580; RH = 60; H = 90 + n * RH
    s = _defs(i) + _kit(i) + f'<pattern id="{i}dm" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".9" fill="#000" opacity=".55"/></pattern></defs>' + _head(kicker, title)
    s += (f'<g class="bd_"><rect x="{X - 10}" y="{Y - 10}" width="{W + 20}" height="{H + 20}" rx="14" fill="url(#{i}mt)" filter="url(#{i}sh)"/><rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="6" fill="#080808"/>'
          + _t(X + 24, Y + 46, 'KỲ HẠN', 18, 'hsl(40,30%,70%)', w=800, ls=2) + _t(X + W - 24, Y + 46, 'LÃI SUẤT', 18, 'hsl(40,30%,70%)', 'end', w=800, ls=2)
          + f'<path d="M{X + 16} {Y + 62} H{X + W - 16}" stroke="#333"/>')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bd_', a + .05, 30, .8)]
    for k, (lab, v) in enumerate(points[:n]):
        y = Y + 110 + k * RH; last = k == n - 1; col = 'hsl(44,100%,58%)' if not last else 'hsl(10,100%,60%)'
        s += (f'<g class="r{k}">' + _t(X + 24, y, lab, 30, 'hsl(44,100%,58%)', w=800) + _t(X + W - 24, y, f'{v}{unit}', 40, col, 'end', w=900)
              + f'<text x="{X + W - 24}" y="{y}" text-anchor="end" font-family="VCB" font-weight="900" font-size="40" fill="{col}" opacity=".6" filter="url(#{i}gl)">{v}{unit}</text>'
              + f'<path d="M{X + 16} {y + 16} H{X + W - 16}" stroke="#1d1d1d"/></g>')
        j.append(S(f'#{i} .r{k}', 0, opacity=0)); j.append(T(f'#{i} .r{k}', t0 + k * .3, opacity=1, duration=.05)); j.append(T(f'#{i} .r{k}', t0 + k * .3 + .05, opacity=.3, duration=.05, yoyo=True, repeat=1))
        if last: j.append(T(f'#{i} .r{k}', t0 + k * .3 + .5, opacity=.55, duration=.4, yoyo=True, repeat=max(0, int((b - t0 - k * .3 - .5) / .4) - 1)))
    s += f'<rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="6" fill="url(#{i}dm)" pointer-events="none"/><path d="M{X} {Y} H{X + W * .6} L{X + W * .4} {Y + H} H{X} Z" fill="#fff" opacity=".04"/></g>'
    s += _src(source)
    return _out(i, a, b, 'r_laisuat', s, j), j, [(t0 + k * .3, 'tick') for k in range(n)]


def nhietke(i, a, b, t0, level=.5, zones=('SỢ HÃI', 'THẬN TRỌNG', 'CÂN BẰNG', 'KỲ VỌNG', 'HƯNG PHẤN'), kicker='TÂM LÝ', title='Tâm lý nhà đầu tư', source='', chot=''):
    """đồng hồ đo kiểu taplô: viền kim loại, cung 5 màu, kim vung tới level (0–1), mặt kính loá — nhận định cá nhân"""
    cx, cy, r = 360, 520 if title else 470, 210; n = len(zones); col = ['hsl(356,76%,52%)', 'hsl(24,85%,55%)', 'hsl(44,92%,56%)', 'hsl(95,55%,48%)', 'hsl(145,62%,42%)']
    s = _defs(i) + _kit(i) + _rg(f'{i}fc', '#23262c', '#0c0d10', .5, .3) + '</defs>' + _head(kicker, title)
    s += (f'<g class="gg"><path d="M{cx - r - 30} {cy + 30} A{r + 30} {r + 30} 0 0 1 {cx + r + 30} {cy + 30} Z" fill="url(#{i}mt)" filter="url(#{i}sh)"/>'
          f'<path d="M{cx - r - 16} {cy + 22} A{r + 16} {r + 16} 0 0 1 {cx + r + 16} {cy + 22} Z" fill="url(#{i}fc)"/>')
    for k in range(n):
        a0, a1 = math.pi + k * math.pi / n + .015, math.pi + (k + 1) * math.pi / n - .015; P = lambda an, rr: (cx + rr * math.cos(an), cy + rr * math.sin(an))
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = P(a0, r - 10), P(a1, r - 10), P(a1, r - 46), P(a0, r - 46)
        s += f'<path d="M{x0:.1f} {y0:.1f} A{r - 10} {r - 10} 0 0 1 {x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f} A{r - 46} {r - 46} 0 0 0 {x3:.1f} {y3:.1f} Z" fill="{col[k * 5 // n]}"/>'
        am = (a0 + a1) / 2; tx, ty = P(am, r - 80)
        s += _t(tx, ty + 5, zones[k], 13, '#ddd', 'middle', w=800)
    s += ''.join(f'<path d="M{cx + (r - 50) * math.cos(math.pi + q * math.pi / 40):.1f} {cy + (r - 50) * math.sin(math.pi + q * math.pi / 40):.1f} L{cx + (r - 58) * math.cos(math.pi + q * math.pi / 40):.1f} {cy + (r - 58) * math.sin(math.pi + q * math.pi / 40):.1f}" stroke="#888" stroke-width="1.5"/>' for q in range(41))
    k_sel = min(n - 1, int(level * n))
    s += (f'<g class="nd"><path d="M{cx - 7} {cy} L{cx} {cy - r + 34} L{cx + 7} {cy} Z" fill="hsl(10,95%,55%)" filter="url(#{i}gl)"/></g><circle cx="{cx}" cy="{cy}" r="22" fill="url(#{i}mt)"/><circle cx="{cx}" cy="{cy}" r="8" fill="#222"/>'
          f'<path d="M{cx - r * .8} {cy - r * .35} A{r} {r} 0 0 1 {cx - r * .1} {cy - r * .9}" stroke="#fff" stroke-opacity=".25" stroke-width="16" fill="none" stroke-linecap="round"/></g>')
    if chot: zones = list(zones); zones[k_sel] = chot   # nhãn chốt CHỈ khi lời có (chot='…'); mặc định không tự kết luận
    s += f'<g class="zl"><rect x="{cx - _w(zones[k_sel], 26) / 2 - 22:.0f}" y="{cy + 52}" width="{_w(zones[k_sel], 26) + 44:.0f}" height="50" rx="25" fill="{col[k_sel * 5 // n]}"/>' + _t(cx, cy + 86, zones[k_sel], 26, '#111', 'middle', w=900) + '</g>' if chot else ''
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gg', a + .05, 30, .8), S(f'#{i} .nd', 0, rotation=-90, svgOrigin=f'{cx} {cy}'),
                                                T(f'#{i} .nd', t0, rotation=-90 + 180 * level, duration=1.4, ease='elastic.out(1,.4)', svgOrigin=f'{cx} {cy}'), _rv(f'#{i} .zl', t0 + .7, 12)]
    s += _note(source or OBS_)
    return _out(i, a, b, 'r_nhietke', s, j), j, [(t0, 'ratchet'), (t0 + .7, 'ding')]


def giathue(i, a, b, t0, price='', rent='', yld='', kicker='ĐẦU TƯ', title='Tỷ suất cho thuê', source=''):
    """căn nhà 3D có chìa khoá treo, tiền thuê bay ra đều đặn; 3 ô số GIÁ MUA · THUÊ/THÁNG · TỶ SUẤT (chỉ ô có trong lời)"""
    I = _iso(360, 300 if title else 250, 40)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 4, 4, 'hsl(100,30%,40%)')
    s += _house(I, .8, .6, 2.2, 2.6, 1.6, 8, 'hs') + _tree(I, i, .5, 3.6, 1.1) + _tree(I, i, 3.6, .5, 1)
    kx, ky = I(3.1, 3.4, 1.0)
    s += (f'<g class="ky"><path d="M{kx:.0f} {ky - 40:.0f} V{ky - 10:.0f}" stroke="#bbb" stroke-width="2"/><circle cx="{kx:.0f}" cy="{ky:.0f}" r="12" fill="none" stroke="url(#{i}mt)" stroke-width="6"/>'
          f'<path d="M{kx:.0f} {ky + 12:.0f} v34 h10 m-10 -12 h8" stroke="url(#{i}mt)" stroke-width="6" fill="none"/></g>')
    for k in range(3):
        s += f'<g class="m{k}"><rect x="{kx - 30:.0f}" y="{ky:.0f}" width="54" height="28" rx="3" fill="hsl(150,45%,45%)" stroke="hsl(150,40%,28%)"/><circle cx="{kx - 3:.0f}" cy="{ky + 14:.0f}" r="7" fill="none" stroke="#fff" stroke-opacity=".6"/></g>'
    tiles = [(t, v) for t, v in (('GIÁ MUA', price), ('THUÊ / THÁNG', rent), ('TỶ SUẤT', yld)) if v]; nt = len(tiles); w = 600 / max(1, nt); ty0 = (300 if title else 250) + 4 * 40 + 120
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .hs', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .hs', a + .3, scaleY=1, duration=.6, ease='expo.out'),
                                                T(f'#{i} .ky', a + .8, rotation=8, duration=.8, yoyo=True, repeat=max(0, int((b - a - .8) / .8) - 1), ease='sine.inOut', svgOrigin=f'{kx:.0f} {ky - 40:.0f}')]
    for k in range(3): j += [S(f'#{i} .m{k}', 0, opacity=0), T(f'#{i} .m{k}', t0 + k * .5, opacity=1, x=120, y=-180, rotation=25, duration=1.2, ease='power1.out', repeat=max(0, int((b - t0 - k * .5) / 1.5) - 1), repeatDelay=.3)]
    for k, (lab, v) in enumerate(tiles):
        x = 60 + k * w; hl = lab == 'TỶ SUẤT'
        s += (f'<g class="tl{k}"><rect x="{x + 6:.0f}" y="{ty0}" width="{w - 12:.0f}" height="120" rx="16" fill="{AC if hl else "rgba(255,255,255,.07)"}"/>'
              + _t(x + 26, ty0 + 36, lab, 16, '#111' if hl else MUT, w=800, ls=1) + _t(x + 26, ty0 + 94, v, 40 if len(v) < 7 else 30, '#111' if hl else FG, cls=f'v{k}', w=900) + '</g>')
        j += [_rv(f'#{i} .tl{k}', t0 + .3 + k * .25, 20), _num(i, f'v{k}', t0 + .4 + k * .25, v, .8)]
    s += _src(source)
    return _out(i, a, b, 'r_giathue', s, j), j, [(t0, 'count')] + [(t0 + .3 + k * .25, 'pop') for k in range(nt)]


# ================================================================== KINH TẾ ==
def tangtruong(i, a, b, t0, value, years=(), unit='%', kicker='KINH TẾ', title='Tăng trưởng GRDP', source=''):
    """cột kính vàng 3D tăng dần + mũi tên 3D vút lên + số lớn; years=[('2023', '6,1'), …] (số có trong lời)"""
    vals = [(_isn(v) or 0) for _, v in years] if years else [3, 4, 5, 6.5, 8]; n = len(vals); mx = max(vals) or 1
    I = _iso(170, 570 if title else 530, 40)
    s = _defs(i) + _kit(i) + _lg(f'{i}bt', 'hsl(46,100%,72%)', 'hsl(42,90%,52%)') + '</defs>' + _head(kicker, title) + _numblk(value, unit, 350 if title else 300, 110, 46)
    s += _ground(I, i, -.4, -.6, n * 1.7 + .2, 1.4, 'hsl(220,10%,22%)', side=.3)
    for k, v in enumerate(vals):
        h = .6 + 4.0 * v / mx; x = k * 1.7
        lab = (f'<g class="yl">' + _t(*I(x + .5, 1.6), years[k][0], 15, MUT, 'middle', w=800) + _t(I(x + .5, .5, h + .3)[0], I(x + .5, .5, h + .3)[1], years[k][1], 17, FG, 'middle', w=900) + '</g>') if years else ''
        s += _box(I, x, 0, 1.0, 1.0, h, 'url(#' + i + 'bt)', f'hsla(44,90%,55%,{.55 + .35 * k / n:.2f})', f'hsla(38,85%,40%,{.6 + .3 * k / n:.2f})', 'br') + lab
    ax0, ay0 = I(-.2, .5, 1.2); ax1, ay1 = I(n * 1.7 - .4, .5, 5.6)
    s += f'<path class="ar" d="M{ax0:.0f} {ay0:.0f} C{ax0 + 120:.0f} {ay0 - 10:.0f} {ax1 - 140:.0f} {ay1 + 60:.0f} {ax1:.0f} {ay1:.0f}" stroke="#3ddc84" stroke-width="12" fill="none" stroke-linecap="round" filter="url(#{i}gl)" pathLength="1"/>'
    s += f'<path class="ah" d="M{ax1 - 34:.0f} {ay1 - 2:.0f} L{ax1 + 12:.0f} {ay1 - 12:.0f} L{ax1 - 6:.0f} {ay1 + 32:.0f} Z" fill="#3ddc84"/>'
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0 + .3, value) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .br', 0, scaleY=0, transformOrigin='50% 100%'),
                                                                         T(f'#{i} .br', t0, scaleY=1, duration=.6, stagger=.12, ease='expo.out'), S(f'#{i} .ar', 0, strokeDasharray=1, strokeDashoffset=1),
                                                                         T(f'#{i} .ar', t0 + .5, strokeDashoffset=0, duration=.8, ease='power2.inOut'), S(f'#{i} .ah,#{i} .yl', 0, opacity=0),
                                                                         T(f'#{i} .ah', t0 + 1.25, opacity=1, duration=.1), T(f'#{i} .yl', t0 + .4, opacity=1, duration=.3, stagger=.1)]
    s += _note(source if years else '')
    return _out(i, a, b, 'r_tangtruong', s, j), j, [(t0, 'whoosh'), (t0 + 1.25, 'ding')]


def dongvon(i, a, b, t0, sources, target='ĐẮK LẮK', kicker='KINH TẾ', title='Dòng vốn đổ về', source=''):
    """bệ 3D trung tâm (toà nhà) nhận dòng đồng xu vàng chạy theo cung từ các nguồn vốn; sources=[(tên, t)] ≤5"""
    I = _iso(360, 300 if title else 250, 32); C = I(5, 5)
    s = _defs(i) + _kit(i) + _lg(f'{i}cn', 'hsl(48,95%,70%)', 'hsl(36,85%,38%)', 1, 1) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(215,15%,24%)')
    s += f'<polygon points="{_P4(I, 0, 0, 10, 10)}" fill="none" stroke="#fff" stroke-opacity=".06"/>' + ''.join(f'<path d="M{_pt([I(k, 0), I(k, 10)])}" stroke="#fff" stroke-opacity=".05"/><path d="M{_pt([I(0, k), I(10, k)])}" stroke="#fff" stroke-opacity=".05"/>' for k in range(1, 10))
    s += '<g class="cc">' + _box(I, 3.8, 3.8, 2.4, 2.4, .5, 'hsl(44,60%,45%)', 'hsl(40,55%,32%)', 'hsl(36,50%,24%)') + _tower(I, i, 4.3, 4.3, 1.4, 1.4, 2.8, 'tw', 4, 7) + '</g>'
    s += f'<g class="tg"><rect x="{C[0] - _w(target, 20) / 2 - 18:.0f}" y="{C[1] + 70:.0f}" width="{_w(target, 20) + 36:.0f}" height="38" rx="19" fill="{AC}"/>' + _t(C[0], C[1] + 96, target, 20, '#111', 'middle', w=900) + '</g>'
    SP = [(.6, 8.8), (8.8, .6), (9.2, 9.2), (4.4, 9.6), (9.6, 4.4)]
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), _rv(f'#{i} .cc', a + .2, 30), _rv(f'#{i} .tg', a + .5, 10)]
    tx, ty = I(5, 5, 3.2)
    for k, (nm, t) in enumerate(sources[:5]):
        sx, sy = I(*SP[k]); mx_, my_ = (sx + tx) / 2, min(sy, ty) - 80
        d = f'M{sx:.0f} {sy:.0f} Q{mx_:.0f} {my_:.0f} {tx:.0f} {ty:.0f}'
        s += (f'<path class="f{k}" d="{d}" stroke="{AC}" stroke-width="3" stroke-dasharray="3 9" fill="none" opacity=".7"/>'
              f'<g class="n{k}"><ellipse cx="{sx:.0f}" cy="{sy:.0f}" rx="22" ry="9" fill="{AC}" opacity=".35"/>' + _t(sx, sy + 32, nm, 18, FG, 'middle', w=900) + '</g>')
        for q in range(3):
            s += f'<g class="c{k}_{q}"><ellipse cx="0" cy="0" rx="10" ry="4" fill="hsl(36,80%,30%)" transform="translate(0 3)"/><ellipse cx="0" cy="0" rx="10" ry="4" fill="url(#{i}cn)"/></g>'
        j += [_rv(f'#{i} .n{k}', t, 10), S(f'#{i} .f{k}', 0, opacity=0), T(f'#{i} .f{k}', t, opacity=.7, duration=.3)]
        for q in range(3):
            j.append("(function(){var p=document.querySelector('#%s .f%d'),c=document.querySelector('#%s .c%d_%d'),o={u:0},L=0;"
                     "var f=function(){L=L||p.getTotalLength();var r=p.getPointAtLength(L*o.u);c.setAttribute('transform','translate('+r.x+' '+r.y+')');c.style.opacity=o.u>0&&o.u<1?1:0;};"
                     "tl.set(o,{u:0,onUpdate:f},0);tl.to(o,{u:1,duration:1.1,ease:'power1.in',repeat:%d,onUpdate:f},%.2f);})();" % (i, k, i, k, q, max(0, int((b - t - .2 - q * .35) / 1.1) - 1), t + .2 + q * .35))
    s += _src(source)
    return _out(i, a, b, 'r_dongvon', s, j), j, [(t, 'count') for _, t in sources[:5]]


def chiso(i, a, b, kpis, kicker='KINH TẾ', title='Đắk Lắk', source=''):
    """màn hình máy tính để bàn hiện bảng chỉ số; kpis=[('GRDP', '7,2', t[, '%'])] ≤4"""
    X, Y, W, H = 70, 290 if title else 230, 580, 330
    base, glass = _device(i, X, Y, W, H, 'monitor')
    scr = ''; n = min(4, len(kpis)); j = []
    for k, (lab, v, t, *u) in enumerate(kpis[:n]):
        u = u[0] if u else ''; x = X + 30 + (k % 2) * 266; y = Y + 30 + (k // 2) * 140
        scr += (f'<g class="k{k}"><rect x="{x}" y="{y}" width="254" height="128" rx="12" fill="#1a1e26" stroke="{AC}" stroke-opacity=".35"/>'
                + _t(x + 18, y + 34, lab, 16, AC, w=800, ls=1) + _t(x + 18, y + 98, v, 46 if len(v) < 7 else 34, FG, cls=f'v{k}', w=900)
                + (_t(x + 236, y + 98, u, 18, MUT, 'end', w=800) if u else '') + f'<path d="M{x + 140} {y + 60} l20 -8 l20 10 l20 -16 l20 -6" stroke="#3ddc84" stroke-width="2.5" fill="none" opacity=".7"/></g>')
        j += [_rv(f'#{i} .k{k}', t, 14, .5), _num(i, f'v{k}', t + .1, v, .8)]
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + f'<g class="dv">{base}{scr}{glass}</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .dv', a + .05, 40, .8)] + j
    s += _src(source)
    return _out(i, a, b, 'r_chiso', s, j), j, [(k[2], 'pop') for k in kpis[:n]]


# ============================================================== NÔNG NGHIỆP ==
def giansan(i, a, b, rows, unit='Đ/KG', kicker='NÔNG SẢN', title='Giá hôm nay', source=''):
    """bảng giá điện tử ở đại lý thu mua: tên nông sản + giá chữ LED + mũi tên tăng/giảm; rows=[('Cà phê', '120.000', '+5%', t)] ≤5"""
    n = min(5, len(rows)); X, Y, W = 60, 300 if title else 240, 600; RH = 64; H = 80 + n * RH
    s = _defs(i) + _kit(i) + _rg(f'{i}bn', 'hsl(25,55%,40%)', 'hsl(18,60%,14%)') + _rg(f'{i}du', 'hsl(80,55%,55%)', 'hsl(90,50%,25%)') + _rg(f'{i}pe', 'hsl(0,0%,25%)', 'hsl(0,0%,5%)') + '</defs>' + _head(kicker, title)
    s += (f'<g class="bd_"><rect x="{X - 10}" y="{Y - 10}" width="{W + 20}" height="{H + 20}" rx="14" fill="url(#{i}mt)" filter="url(#{i}sh)"/><rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="6" fill="#070707"/>'
          + _t(X + W - 20, Y + 40, unit, 16, 'hsl(40,30%,65%)', 'end', w=800, ls=2) + f'<path d="M{X + 14} {Y + 56} H{X + W - 14}" stroke="#2a2a2a"/>')
    def icn(nm, x, y):
        nm = nm.lower()
        if 'sầu' in nm: return f'<ellipse cx="{x}" cy="{y}" rx="16" ry="19" fill="url(#{i}du)"/>' + ''.join(f'<path d="M{x + dx} {y + dy} l3 -5 l3 5" fill="hsl(80,45%,35%)"/>' for dx, dy in ((-9, -6), (2, -10), (-4, 4), (6, 2), (-10, 10)))
        if 'tiêu' in nm: return ''.join(f'<circle cx="{x + dx}" cy="{y + dy}" r="6" fill="url(#{i}pe)"/>' for dx, dy in ((-7, -6), (6, -4), (-2, 6), (9, 8), (-10, 8)))
        return f'<ellipse cx="{x}" cy="{y}" rx="13" ry="17" fill="url(#{i}bn)" transform="rotate(-20 {x} {y})"/><path d="M{x - 3} {y - 13} q8 13 0 26" stroke="hsl(18,40%,8%)" stroke-width="2" fill="none"/>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bd_', a + .05, 30, .8)]
    for k, (nm, pr, ch, t) in enumerate(rows[:n]):
        y = Y + 104 + k * RH; up = not str(ch).startswith('-'); c = '#3ddc84' if up else '#ff5a5f'
        s += (f'<g class="r{k}">' + icn(nm, X + 40, y - 10) + _t(X + 72, y, nm.upper(), 24, '#eee', w=800)
              + _t(X + W - 120, y + 2, pr, 34, 'hsl(44,100%,58%)', 'end', cls=f'p{k}', w=900)
              + (f'<path d="M{X + W - 100} {y - (2 if up else 22)} l10 {-14 if up else 14} l10 {14 if up else -14} z" fill="{c}"/>' + _t(X + W - 20, y, str(ch).lstrip('+-'), 18, c, 'end', w=900) if ch else '')
              + f'<path d="M{X + 14} {y + 22} H{X + W - 14}" stroke="#1d1d1d"/></g>')
        j += [S(f'#{i} .r{k}', 0, opacity=0), T(f'#{i} .r{k}', t, opacity=1, duration=.05), _num(i, f'p{k}', t, pr, .7)]
    s += f'<path d="M{X} {Y} H{X + W * .6} L{X + W * .4} {Y + H} H{X} Z" fill="#fff" opacity=".04"/></g>' + _src(source)
    return _out(i, a, b, 'r_giansan', s, j), j, [(r[3], 'tick') for r in rows[:n]]


def vungtrong(i, a, b, t0, value='', unit='ha', crop='cà phê', kicker='NÔNG NGHIỆP', title='Diện tích canh tác', source=''):
    """đồi trồng 3D: các hàng cây cà phê có trái đỏ, lối đi, nhà kho nhỏ, nông dân; cây mọc theo đợt + số diện tích"""
    I = _iso(360, 380 if title else 330, 30)
    s = _defs(i) + _kit(i) + _rg(f'{i}cf', 'hsl(120,45%,40%)', 'hsl(140,55%,16%)') + '</defs>' + _head(kicker, title)
    if value: s += _numblk(value, unit, 340 if title else 290, 110, 40)
    s += _ground(I, i, 0, 0, 10, 8, 'hsl(28,35%,36%)')
    s += f'<polygon points="{_P4(I, 0, 3.8, 10, 4.3)}" fill="hsl(36,30%,58%)"/>'
    pl = []
    for r in range(8):
        for c in range(10):
            y = .4 + r * .95 + (.0 if r < 4 else .6); x = .5 + c * .95
            if 3.6 < y < 4.6: continue
            pl.append((x + y, x, y))
    pl.sort()
    for _, x, y in pl:
        px, py = I(x, y)
        s += (f'<g class="pl"><ellipse cx="{px + 6:.0f}" cy="{py + 1:.0f}" rx="13" ry="4" fill="#000" opacity=".35"/><circle cx="{px:.0f}" cy="{py - 12:.0f}" r="13" fill="url(#{i}cf)"/>'
              f'<circle cx="{px - 4:.0f}" cy="{py - 17:.0f}" r="5" fill="hsl(100,55%,55%)" opacity=".35"/><circle cx="{px + 5:.0f}" cy="{py - 8:.0f}" r="2.5" fill="hsl(356,85%,52%)"/><circle cx="{px - 6:.0f}" cy="{py - 6:.0f}" r="2" fill="hsl(356,85%,52%)"/></g>')
    s += _box(I, 8.6, 4.6, 1.0, 1.2, .9, 'hsl(10,45%,45%)', 'hsl(35,20%,70%)', 'hsl(30,15%,52%)', 'wh')
    fx, fy = I(5.2, 4.05); s += _person(fx, fy, .8, 'hsl(210,40%,40%)', False, 'fm').replace('hsl(20,25%,15%)', 'hsl(44,60%,60%)')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .pl', 0, scale=0, transformOrigin='50% 100%'),
                                                T(f'#{i} .pl', t0, scale=1, duration=.35, stagger=.015, ease='back.out(2)'), _rv(f'#{i} .wh', a + .3, 20), _rv(f'#{i} .fm', t0 + .4, 10)]
    if value: j += _numj(i, t0 + .2, value)
    s += _note(source)
    return _out(i, a, b, 'r_vungtrong', s, j), j, [(t0, 'air'), (t0 + .8, 'count')]


def sanluong(i, a, b, t0, value='', unit='tấn', crop='cà phê', kicker='NÔNG NGHIỆP', title='Sản lượng', source=''):
    """bao nông sản trên pallet + cành cà phê trái chín + số sản lượng (cùng hình caphe)"""
    return caphe(i, a, b, t0, value, unit, ('CÀ PHÊ ĐẮK LẮK' if 'cà phê' in crop.lower() else crop.upper()), kicker, title, source)


def vondt(i, a, b, t0, value, unit='tỷ đồng', kicker='VỐN ĐẦU TƯ', title='', note='', source=''):
    """thỏi vàng 3D xếp chồng + đồng xu + số vốn (cùng hình vang)"""
    return vang(i, a, b, t0, value, unit, kicker, title, note, source)


# ================================================================ LOGISTICS ==
CC = ['hsl(356,62%,48%)', 'hsl(205,58%,42%)', 'hsl(145,45%,36%)', 'hsl(36,85%,50%)', 'hsl(0,0%,82%)']
def _cont(I, x, y, z, col, along_x=True, cls='bx'):
    w, d, h = (1.5, .6, .62) if along_x else (.6, 1.5, .62)
    rib = ''.join(f'<path d="M{_pt([I(x + (q * w / 8 if along_x else w), y + (d if along_x else q * d / 8), z), I(x + (q * w / 8 if along_x else w), y + (d if along_x else q * d / 8), z + h)])}" stroke="#000" stroke-opacity=".22" stroke-width="1.5"/>' for q in range(1, 8))
    return _box(I, x, y, w, d, h, col, col, col, cls, rib + f'<polygon points="{_pt([I(x, y + d, z), I(x + w, y + d, z), I(x + w, y + d, z + h), I(x, y + d, z + h)])}" fill="#000" opacity=".12"/>'
                + f'<polygon points="{_pt([I(x + w, y, z), I(x + w, y + d, z), I(x + w, y + d, z + h), I(x + w, y, z + h)])}" fill="#000" opacity=".3"/>').replace(f'<g class="{cls}">', f'<g class="{cls}" transform="translate(0 {-z * 0:.0f})">')


def cangcan(i, a, b, t0, tag='', kicker='LOGISTICS', title='Cảng cạn', source=''):
    """bãi container 3D: các chồng container nhiều màu, cẩu giàn vàng chạy ray, container được cẩu hạ xuống, xe đầu kéo vào bãi"""
    I = _iso(360, 300 if title else 250, 30)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 10, 9, 'hsl(220,6%,40%)')
    s += ''.join(f'<path d="M{_pt([I(0, y), I(10, y)])}" stroke="#fff" stroke-opacity=".25" stroke-width="1.5" stroke-dasharray="10 8"/>' for y in (3.0, 6.0))
    random.seed(6); items = []
    for row, y in enumerate((.6, 3.6)):
        for c in range(5):
            hgt = random.choice((1, 2, 2, 3))
            for z in range(hgt): items.append((c * 1.8 + .4, y + (z % 2) * 0, z, random.choice(CC)))
    for x, y, z, col in sorted(items, key=lambda q: (q[0] + q[1], q[2])):
        s += _cont(I, x, y, z * .64, col, True, 'bx')
    s += _truck(I, 6.5, 7.2, True, 'hsl(210,60%,45%)', 'trk').replace('#eceef1', CC[0]).replace('#c9ccd2', CC[0]).replace('#9aa0a8', 'hsl(356,55%,35%)')
    gx = 3.4
    def gantry(xx):
        legs = ''.join(_box(I, xx + dx, dy, .25, .25, 3.0, 'hsl(46,95%,58%)', 'hsl(44,90%,48%)', 'hsl(40,85%,38%)') for dx, dy in ((0, .2), (0, 7.6), (1.9, .2), (1.9, 7.6)))
        beam = _box(I, xx, .2, .25, 7.65, .3, 'hsl(46,95%,58%)', 'hsl(44,90%,48%)', 'hsl(40,85%,38%)') + _box(I, xx + 1.9, .2, .25, 7.65, .3, 'hsl(46,95%,58%)', 'hsl(44,90%,48%)', 'hsl(40,85%,38%)')
        beam = beam.replace('<g class="">', '<g>')
        return legs, beam
    legs, beam = gantry(gx)
    hx, hy = I(gx + 1.1, 4.4, 3.0); hz = I(gx + 1.1, 4.4, 1.6)
    s += (f'<g class="gt">{legs}<g transform="translate(0 {-3.0 * 30:.0f})">{beam}</g>'
          f'<path class="cab" d="M{hx:.0f} {hy:.0f} V{hz[1]:.0f}" stroke="#222" stroke-width="2"/><g class="hc">' + _cont(I, gx + .35, 4.1, 1.6, CC[3], True, 'hcx') + '</g></g>')
    if tag: s += f'<g class="tg">' + _t(60, (300 if title else 250) + 9 * 30 + 66, tag, 22, AC, w=900, ls=1) + '</g>'
    ox, oy = I(0, 0); tx, ty = I(-2.5, 0)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .bx', 0, y=-60, opacity=0), T(f'#{i} .bx', t0, y=0, opacity=1, duration=.35, stagger=.04, ease='power2.in'),
                                                _rv(f'#{i} .gt', a + .3, -30, .7), T(f'#{i} .gt', t0 + .6, x=(I(2, 0)[0] - ox), y=(I(2, 0)[1] - oy), duration=1.4, yoyo=True, repeat=max(0, int((b - t0 - .6) / 1.4) - 1), ease='sine.inOut'),
                                                T(f'#{i} .hc', t0 + .6, y=40, duration=.7, yoyo=True, repeat=max(0, int((b - t0 - .6) / .7) - 1), ease='sine.inOut'),
                                                S(f'#{i} .trk', 0, x=ox - tx, y=oy - ty), T(f'#{i} .trk', t0 + .3, x=0, y=0, duration=1.2, ease='power2.out')]
    if tag: j.append(_rv(f'#{i} .tg', t0 + 1, 10))
    s += _note(source)
    return _out(i, a, b, 'r_cangcan', s, j), j, [(t0, 'metal'), (t0 + .6, 'block')]


def mangluoi(i, a, b, t0, hub, spokes, kicker='LOGISTICS', title='Mạng lưới vận tải', source=''):
    """kho trung tâm 3D, các tuyến đường toả ra tới kho vệ tinh, xe tải chạy đi về; spokes=[(tên, t)] ≤5"""
    I = _iso(360, 300 if title else 250, 30); C = (5, 5)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,34%)')
    EP = [(5, .4), (9.6, 5), (5, 9.6), (.4, 5), (9.2, 9.2), (.8, .8)]
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8)]
    for k, (nm, t) in enumerate(spokes[:5]):
        ex, ey = EP[k]
        P = [I(C[0] + (ex - C[0]) * u, C[1] + (ey - C[1]) * u) for u in (0, 1)]
        s += f'<path class="rd{k}" d="M{_pt(P)}" stroke="#2f3237" stroke-width="12" stroke-linecap="round"/><path class="rl{k}" d="M{_pt(P)}" stroke="hsl(46,90%,60%)" stroke-width="1.5" stroke-dasharray="6 6"/>'
        s += '<g class="sp{0}">'.format(k) + _box(I, ex - .5, ey - .4, 1.0, .8, .6, 'hsl(210,10%,80%)', 'hsl(210,10%,62%)', 'hsl(210,10%,46%)') + '</g>'
        lx, ly = I(ex, ey, .6)
        s += f'<g class="lb{k}">' + _t(lx, ly - 18, nm, 17, FG, 'middle', w=900) + '</g>'
        s += _truck(I, C[0] - .2, C[1] - .2, abs(ex - C[0]) > abs(ey - C[1]), CC[k % 4], f'tk{k}')
        sx, sy = I(*C); tx, ty = I(ex, ey)
        j += [S(f'#{i} .rd{k},#{i} .rl{k}', 0, opacity=0), T(f'#{i} .rd{k},#{i} .rl{k}', t, opacity=1, duration=.3), S(f'#{i} .sp{k}', 0, scaleY=0, transformOrigin='50% 100%'),
              T(f'#{i} .sp{k}', t + .1, scaleY=1, duration=.4, ease='back.out(2)'), _rv(f'#{i} .lb{k}', t + .2, 8), S(f'#{i} .tk{k}', 0, opacity=0),
              T(f'#{i} .tk{k}', t + .3, opacity=1, duration=.2), T(f'#{i} .tk{k}', t + .3, x=(tx - sx) * .85, y=(ty - sy) * .85, duration=1.3, ease='sine.inOut', yoyo=True, repeat=max(0, int((b - t - .3) / 1.3) - 1))]
    s += '<g class="hb">' + _box(I, 4.0, 4.1, 2.0, 1.8, 1.0, 'hsl(205,25%,72%)', 'hsl(205,20%,58%)', 'hsl(205,20%,42%)') + ''.join(f'<polygon points="{_pt([I(4.2 + q * .45, 5.9, 0), I(4.55 + q * .45, 5.9, 0), I(4.55 + q * .45, 5.9, .6), I(4.2 + q * .45, 5.9, .6)])}" fill="hsl(210,10%,30%)"/>' for q in range(4)) + '</g>'
    hx, hy = I(5, 5, 1.0)
    s += f'<g class="hl"><rect x="{hx - _w(hub, 18) / 2 - 16:.0f}" y="{hy - 54:.0f}" width="{_w(hub, 18) + 32:.0f}" height="34" rx="17" fill="{AC}"/>' + _t(hx, hy - 31, hub, 18, '#111', 'middle', w=900) + '</g>'
    j += [S(f'#{i} .hb', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .hb', t0, scaleY=1, duration=.5, ease='expo.out'), _rv(f'#{i} .hl', t0 + .2, 10)]
    s += _note(source)
    return _out(i, a, b, 'r_mangluoi', s, j), j, [(t0, 'block')] + [(t, 'whoosh') for _, t in spokes[:5]]


def chiphi(i, a, b, t0, t1, before, after, lb='HIỆN NAY', la='SAU KHI CÓ HẠ TẦNG', kicker='LOGISTICS', title='Chi phí vận chuyển', source=''):
    """2 xấp tiền 3D: TRƯỚC cao (đỏ) → t1 xấp SAU thấp hơn (xanh) đặt cạnh; số trước bị gạch"""
    pb, pa = _isn(re.sub(r'[^\d.,]', '', str(before)) or None), _isn(re.sub(r'[^\d.,]', '', str(after)) or None); fa = (pa / pb) if pb and pa else .6
    nb = 34; na = max(4, round(nb * fa)); top = 250 if title else 200
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title)
    s += f'<g class="sa">{_cash(i, 120, top + 300, nb, "hsl(356,40%,52%)", "csa")}</g><g class="sb">{_cash(i, 400, top + 300, na, "hsl(150,45%,42%)", "csb")}</g>'
    s += (f'<g class="la_">' + _t(225, top + 372, lb, 16, MUT, 'middle', w=800, ls=2) + _t(225, top + 420, before, 44, MUT, 'middle', cls='bv', w=900)
          + f'<rect class="st" x="{225 - _w(before, 44) / 2 - 4:.0f}" y="{top + 404}" width="{_w(before, 44) + 8:.0f}" height="4" fill="#ff5a5f"/></g>'
          f'<g class="lb_">' + _t(505, top + 372, la, 16, AC, 'middle', w=800, ls=1) + _t(505, top + 424, after, 52, FG, 'middle', w=900) + '</g>')
    s = s.replace(f'{_t(225, top + 380, lb, 16, MUT, "middle", w=800, ls=2)}', _t(225, top + 380, lb, 16, MUT, 'middle', w=800, ls=2))
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .csa', 0, scaleY=0, opacity=0, transformOrigin='50% 100%'), T(f'#{i} .csa', t0, scaleY=1, opacity=1, duration=.8, ease='expo.out'),
                                                _rv(f'#{i} .la_', t0 + .3, 12), S(f'#{i} .csb', 0, scaleY=0, opacity=0, transformOrigin='50% 100%'), T(f'#{i} .csb', t1, scaleY=1, opacity=1, duration=.8, ease='expo.out'),
                                                S(f'#{i} .st', 0, scaleX=0, transformOrigin='0% 50%'), T(f'#{i} .st', t1, scaleX=1, duration=.4), _rv(f'#{i} .lb_', t1 + .3, 16)]
    s += _src(source)
    return _out(i, a, b, 'r_chiphi', s, j), j, [(t0, 'count'), (t1, 'whoosh'), (t1 + .3, 'ding')]


# ============================================================== CÔNG NGHIỆP ==
def _hall(I, x, y, w, d, h, cls='bd', col=(205, 18)):
    """nhà xưởng mái răng cưa"""
    hue, sat = col
    body = _box(I, x, y, w, d, h, f'hsl({hue},{sat}%,78%)', f'hsl({hue},{sat}%,64%)', f'hsl({hue},{sat}%,48%)', '')
    teeth = ''
    for q in range(int(w / .8)):
        x0 = x + q * .8
        teeth += (f'<polygon points="{_pt([I(x0, y, h), I(x0, y + d, h), I(x0 + .8, y + d, h + .45), I(x0 + .8, y, h + .45)])}" fill="hsl({hue},{sat}%,82%)"/>'
                  f'<polygon points="{_pt([I(x0 + .8, y, h), I(x0 + .8, y + d, h), I(x0 + .8, y + d, h + .45), I(x0 + .8, y, h + .45)])}" fill="hsl(205,45%,55%)"/>'
                  f'<polygon points="{_pt([I(x0, y + d, h), I(x0 + .8, y + d, h), I(x0 + .8, y + d, h + .45)])}" fill="hsl({hue},{sat}%,60%)"/>')
    door = f'<polygon points="{_pt([I(x + w * .3, y + d, 0), I(x + w * .55, y + d, 0), I(x + w * .55, y + d, h * .7), I(x + w * .3, y + d, h * .7)])}" fill="hsl(220,10%,32%)"/>'
    return f'<g class="{cls}">{body}{teeth}{door}</g>'


def nhamay(i, a, b, t0, value='', unit='', tag='', kicker='CÔNG NGHIỆP', title='Nhà máy', source=''):
    """nhà máy 3D: xưởng mái răng cưa, ống khói nhả khói, bồn silo, xe tải ra vào; value tuỳ chọn"""
    I = _iso(360, 330 if title else 270, 32)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title)
    if value: s += _numblk(value, unit, (330 if title else 270) - 10, 90, 34)
    s += _ground(I, i, 0, 0, 9, 8, 'hsl(220,6%,42%)') + f'<polygon points="{_P4(I, .2, 6.2, 8.8, 7.6)}" fill="#34373c"/>'
    s += _hall(I, .8, 1.0, 4.8, 3.2, 1.2)
    for k, (sx, sy) in enumerate(((6.6, 1.2), (7.6, 1.2))):
        cx_, cy_ = I(sx, sy); top_ = I(sx, sy, 1.8)
        s += (f'<g class="sl"><rect x="{cx_ - 18:.0f}" y="{top_[1]:.0f}" width="36" height="{cy_ - top_[1]:.0f}" fill="url(#{i}mt)"/><ellipse cx="{cx_:.0f}" cy="{cy_:.0f}" rx="18" ry="8" fill="#8d939c"/>'
              f'<ellipse cx="{cx_:.0f}" cy="{top_[1]:.0f}" rx="18" ry="8" fill="#e6e8ec"/></g>')
    for k, (sx, sy) in enumerate(((1.4, 3.6), (2.4, 3.6))):
        bx_, by_ = I(sx, sy, 1.2); tx_, ty_ = I(sx, sy, 3.2)
        s += f'<g class="ch"><rect x="{bx_ - 9:.0f}" y="{ty_:.0f}" width="18" height="{by_ - ty_:.0f}" fill="hsl(10,35%,45%)"/><rect x="{bx_ - 9:.0f}" y="{ty_ + 10:.0f}" width="18" height="6" fill="#fff" opacity=".7"/></g>'
        for q in range(3): s += f'<circle class="sm{k}{q}" cx="{tx_:.0f}" cy="{ty_ - 6:.0f}" r="{12 + q * 3}" fill="#c9cdd3" opacity="0" filter="url(#{i}sf)"/>'
    s += _truck(I, 1.0, 6.5, True, CC[1], 'tk0') + _truck(I, 6.4, 5.0, False, CC[0], 'tk1')
    if tag: s += f'<g class="tg">' + _t(60, (330 if title else 270) + 8 * 32 + 70, tag, 22, AC, w=900, ls=1) + '</g>'
    ox, oy = I(0, 0); dx_, dy_ = I(5, 0)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .bd,#{i} .sl,#{i} .ch', 0, scaleY=0, transformOrigin='50% 100%'),
                                                T(f'#{i} .bd,#{i} .sl,#{i} .ch', a + .3, scaleY=1, duration=.6, stagger=.1, ease='expo.out'),
                                                T(f'#{i} .tk0', t0 + .3, x=dx_ - ox, y=dy_ - oy, duration=max(1, b - t0 - .5), ease='none')]
    for k in range(2):
        for q in range(3):
            tq = t0 + q * .5 + k * .2
            j.append(f"tl.fromTo('#{i} .sm{k}{q}',{{opacity:.75,y:0,x:0,scale:1}},{{opacity:0,y:-110,x:30,scale:2.2,duration:1.5,ease:'power1.out',repeat:{max(0, int((b - tq) / 1.5) - 1)}}},{tq:.2f});")
    if value: j += _numj(i, t0 + .2, value)
    if tag: j.append(_rv(f'#{i} .tg', t0 + .6, 10))
    s += _note(source)
    return _out(i, a, b, 'r_nhamay', s, j), j, [(t0, 'metal')]


def lapday(i, a, b, t0, pct, name='KHU CÔNG NGHIỆP', kicker='CÔNG NGHIỆP', title='Tỷ lệ lấp đầy', source=''):
    """khu công nghiệp 3D chia lô; nhà xưởng mọc lên đủ pct% số lô, lô trống viền đứt; số % lớn"""
    f = min(1, (_isn(pct) or 60) / 100); I = _iso(380, 400 if title else 350, 26)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _numblk(pct, '%', 360 if title else 300, 100, 44)
    s += _ground(I, i, 0, 0, 12, 10, 'hsl(95,22%,36%)') + f'<polygon points="{_P4(I, 5.6, 0, 6.4, 10)}" fill="#34373c"/><polygon points="{_P4(I, 0, 4.6, 12, 5.4)}" fill="#34373c"/>'
    lots = [(x, y) for y in (.4, 2.5, 5.8, 7.9) for x in (.4, 2.9, 6.8, 9.3)]
    random.seed(3); order = lots[:]; random.shuffle(order); on = set(order[:round(f * len(lots))])
    for x, y in sorted(lots, key=lambda p: p[0] + p[1]):
        s += f'<polygon points="{_P4(I, x, y, x + 2.2, y + 1.8)}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.5" stroke-dasharray="6 5"/>'
        if (x, y) in on: s += _hall(I, x + .1, y + .1, 2.0, 1.6, .8, 'fc', random.choice(((205, 18), (30, 15), (0, 0))))
    s += f'<g class="nm">' + _t(60, (360 if title else 300) + 40, name, 20, AC, w=900, ls=1) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0, pct) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .fc', 0, scaleY=0, opacity=0, transformOrigin='50% 100%'),
                                                                   T(f'#{i} .fc', t0, scaleY=1, opacity=1, duration=.4, stagger={'each': .08, 'from': 'random'}, ease='expo.out'), _rv(f'#{i} .nm', t0 + .2, 8)]
    s += _src(source)
    return _out(i, a, b, 'r_lapday', s, j), j, [(t0, 'ratchet'), (t0 + 1, 'ding')]


def vieclam(i, a, b, t0, value, unit='lao động', kicker='CÔNG NGHIỆP', title='Việc làm', source=''):
    """đội công nhân đội mũ bảo hộ đứng thành hàng trước nhà xưởng 3D + số đếm"""
    I = _iso(360, 420 if title else 370, 28); top = 330 if title else 270
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _numblk(value, unit, top + 40, 110, 40)
    s += _ground(I, i, 0, 0, 10, 7, 'hsl(220,6%,42%)') + _hall(I, 1.0, .6, 6.4, 2.2, 1.1, 'hl')
    ppl = []
    for r in range(3):
        for c in range(8):
            px, py = I(1.2 + c * .9 + r * .2, 3.6 + r * .9); ppl.append((py, px))
    shirts = ['hsl(210,55%,45%)', 'hsl(24,85%,52%)', 'hsl(210,40%,35%)', 'hsl(145,40%,38%)']
    for k, (py, px) in enumerate(sorted(ppl)): s += _person(px, py, .75, shirts[k % 4], True, 'ps')
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0 + .2, value) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .hl', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .hl', a + .3, scaleY=1, duration=.5, ease='expo.out'),
                                                                         S(f'#{i} .ps', 0, opacity=0, y=20), T(f'#{i} .ps', t0, opacity=1, y=0, duration=.3, stagger=.03, ease='power2.out')]
    s += _src(source)
    return _out(i, a, b, 'r_vieclam', s, j), j, [(t0, 'pop'), (t0 + .8, 'count')]


# =============================================================== THƯƠNG MẠI ==
def banle(i, a, b, t0, value, unit='tỷ đồng', kicker='THƯƠNG MẠI', title='Doanh thu bán lẻ', source=''):
    """xe đẩy siêu thị inox đầy hàng (hộp, chai, rau củ) + số doanh thu"""
    top = 300 if title else 240; cx, cy = 380, top + 250
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _numblk(value, unit, top + 30, 110, 40)
    goods = (f'<g class="gd_"><rect x="{cx - 120}" y="{cy - 90}" width="70" height="80" rx="4" fill="hsl(356,65%,52%)"/><rect x="{cx - 112}" y="{cy - 70}" width="54" height="16" fill="#fff" opacity=".8"/>'
             f'<rect x="{cx - 40}" y="{cy - 120}" width="30" height="110" rx="10" fill="hsl(145,45%,40%)"/><rect x="{cx - 36}" y="{cy - 130}" width="22" height="14" rx="4" fill="hsl(145,45%,30%)"/>'
             f'<rect x="{cx}" y="{cy - 80}" width="80" height="70" rx="4" fill="hsl(44,85%,55%)"/><path d="M{cx} {cy - 60} h80" stroke="#fff" stroke-opacity=".6" stroke-width="6"/>'
             f'<circle cx="{cx + 110}" cy="{cy - 40}" r="26" fill="hsl(25,90%,55%)"/><path d="M{cx + 110} {cy - 66} q6 -10 14 -8" stroke="hsl(110,50%,35%)" stroke-width="4" fill="none"/>'
             f'<circle cx="{cx - 80}" cy="{cy - 100}" r="20" fill="hsl(95,55%,45%)"/><rect x="{cx + 40}" y="{cy - 140}" width="40" height="60" rx="6" fill="hsl(205,60%,55%)"/></g>')
    wire = ''.join(f'<path d="M{cx - 150 + q * 22} {cy - 20} L{cx - 130 + q * 20} {cy + 80}" stroke="url(#{i}mt)" stroke-width="2.5"/>' for q in range(15))
    wire += ''.join(f'<path d="M{cx - 150 + q * 4} {cy - 20 + q * 25} H{cx + 150 - q * 2}" stroke="url(#{i}mt)" stroke-width="2.5"/>' for q in range(5))
    cart = (f'<g class="ca"><ellipse cx="{cx}" cy="{cy + 160}" rx="200" ry="18" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
            f'<path d="M{cx - 160} {cy - 26} H{cx + 160} L{cx + 140} {cy + 84} H{cx - 130} Z" fill="#fff" opacity=".06"/>{goods}{wire}'
            f'<path d="M{cx - 160} {cy - 26} H{cx + 160} L{cx + 140} {cy + 84} H{cx - 130} Z" fill="none" stroke="url(#{i}mt)" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{cx + 160} {cy - 26} L{cx + 200} {cy - 90} H{cx + 240}" stroke="url(#{i}mt)" stroke-width="8" fill="none" stroke-linecap="round"/><rect x="{cx + 220}" y="{cy - 98}" width="40" height="16" rx="8" fill="hsl(356,70%,50%)"/>'
            f'<path d="M{cx - 120} {cy + 84} L{cx - 110} {cy + 130} H{cx + 120} L{cx + 130} {cy + 84}" stroke="url(#{i}mt)" stroke-width="6" fill="none"/>'
            + ''.join(f'<circle cx="{x}" cy="{cy + 146}" r="14" fill="#222"/><circle cx="{x}" cy="{cy + 146}" r="5" fill="#aaa"/>' for x in (cx - 100, cx + 110)) + '</g>')
    s += cart
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0 + .3, value) + [S(f'#{i} .ca', 0, x=-300, opacity=0), T(f'#{i} .ca', a + .1, x=0, opacity=1, duration=.9, ease='expo.out'),
                                                                         S(f'#{i} .gd_ > *', 0, y=-160, opacity=0), T(f'#{i} .gd_ > *', t0, y=0, opacity=1, duration=.45, stagger=.08, ease='bounce.out')]
    s += _src(source)
    return _out(i, a, b, 'r_banle', s, j), j, [(t0, 'pop'), (t0 + .9, 'count')]


def cuakhau(i, a, b, t0, left='VIỆT NAM', right='CAMPUCHIA', kicker='THƯƠNG MẠI', title='Cửa khẩu', tag='', source=''):
    """phối cảnh cửa khẩu: nhà cổng mái, cột cờ, barie nâng ở t0, hàng xe tải qua lại"""
    X0, Y0, W, H = 60, 300 if title else 230, 600, 380; HZ = Y0 + 170; VX = 360
    s = _defs(i) + _kit(i) + _skydefs(i, 'hsl(205,55%,55%)', 'hsl(40,70%,82%)') + '</defs>' + _head(kicker, title)
    body = _sky(i, X0, Y0, W, H, HZ, sunx=None) + f'<rect x="{X0}" y="{HZ}" width="{W}" height="{H - 170}" fill="hsl(95,28%,34%)"/>'
    body += f'<polygon points="{_pt([(VX - 60, HZ), (VX + 60, HZ), (X0 + W + 80, Y0 + H), (X0 - 80, Y0 + H)])}" fill="#3a3d42"/><path d="M{VX} {HZ} L{VX} {Y0 + H}" stroke="#fff" stroke-width="4" stroke-dasharray="18 16"/>'
    body += (f'<g class="gt"><rect x="{VX - 200}" y="{HZ - 110}" width="400" height="34" fill="hsl(36,30%,86%)"/><path d="M{VX - 220} {HZ - 110} L{VX} {HZ - 160} L{VX + 220} {HZ - 110} Z" fill="hsl(10,55%,45%)"/>'
             f'<rect x="{VX - 200}" y="{HZ - 76}" width="40" height="110" fill="hsl(36,25%,78%)"/><rect x="{VX + 160}" y="{HZ - 76}" width="40" height="110" fill="hsl(36,25%,70%)"/>'
             + _t(VX, HZ - 86, 'CỬA KHẨU QUỐC TẾ', 16, 'hsl(356,70%,40%)', 'middle', w=900) + '</g>')
    for k, (fx, fc) in enumerate(((VX - 250, 'hsl(356,80%,50%)'), (VX + 250, 'hsl(220,70%,45%)'))):
        body += f'<g class="fl{k}"><path d="M{fx} {HZ + 20} V{HZ - 150}" stroke="#ddd" stroke-width="4"/><path class="fg{k}" d="M{fx} {HZ - 150} q30 -8 60 0 v36 q-30 -8 -60 0 z" fill="{fc}"/></g>'
    body += f'<g class="br"><rect x="{VX - 150}" y="{HZ + 10}" width="10" height="40" fill="#555"/><rect x="{VX - 145}" y="{HZ + 12}" width="150" height="10" rx="5" fill="hsl(356,80%,52%)"/><rect x="{VX - 115}" y="{HZ + 12}" width="20" height="10" fill="#fff"/><rect x="{VX - 75}" y="{HZ + 12}" width="20" height="10" fill="#fff"/></g>'
    body += f'<g class="tk">' + ''.join(f'<g transform="translate({VX - 70} {HZ + 60 + q * 10}) scale({.5 + q * .25})"><rect x="-40" y="-60" width="80" height="60" rx="3" fill="{CC[q % 4]}"/><rect x="-36" y="-56" width="72" height="20" fill="#000" opacity=".15"/><rect x="-40" y="0" width="16" height="10" fill="#111"/><rect x="24" y="0" width="16" height="10" fill="#111"/></g>' for q in range(2, -1, -1)) + '</g>'
    s += _card(i, X0, Y0, W, H, body)
    s += f'<g class="l0">' + _t(X0 + 10, Y0 + H + 40, '◀ ' + left, 22, '#3ddc84', w=900) + '</g><g class="l1">' + _t(X0 + W - 10, Y0 + H + 40, right + ' ▶', 22, '#ff8a8a', 'end', w=900) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .cd', a + .1, 30, .8), _rv(f'#{i} .l0', a + .4, 10), _rv(f'#{i} .l1', a + .5, 10),
                                                T(f'#{i} .br rect:not(:first-child)', t0, rotation=-75, duration=.6, ease='back.out(1.6)', svgOrigin=f'{VX - 145} {HZ + 17}'),
                                                T(f'#{i} .tk', t0 + .5, y=-90, scale=.6, duration=max(1, b - t0 - .6), ease='power1.in', svgOrigin=f'{VX - 70} {HZ}'),
                                                T(f'#{i} .fg0,#{i} .fg1', a, skewY=4, duration=.5, yoyo=True, repeat=max(0, int((b - a) / .5) - 1), ease='sine.inOut')]
    return _out(i, a, b, 'r_cuakhau', s, j), j, [(t0, 'creak'), (t0 + .5, 'whoosh')]


def tmdt(i, a, b, items, kicker='THƯƠNG MẠI', title='Thương mại điện tử', source=''):
    """điện thoại thật cầm trên tay: thông báo đơn hàng bật liên tục, hộp hàng 3D xếp chồng bên cạnh; items=[(chữ, t)] ≤4"""
    X, Y, W, H = 120, 300 if title else 240, 260, 400
    base, glass = _device(i, X, Y, W, H, 'phone')
    scr = f'<rect x="{X + 12}" y="{Y + 12}" width="{W - 24}" height="{H - 24}" rx="10" fill="#f4f5f7"/><rect x="{X + W / 2 - 40}" y="{Y + 18}" width="80" height="16" rx="8" fill="#0b0c0f"/>'
    j = []
    for k, (txt, t) in enumerate(items[:4]):
        y = Y + 54 + k * 82
        scr += (f'<g class="o{k}"><rect x="{X + 24}" y="{y}" width="{W - 48}" height="70" rx="14" fill="#fff" filter="url(#{i}sh)"/><rect x="{X + 34}" y="{y + 14}" width="40" height="40" rx="10" fill="hsl(24,90%,55%)"/>'
                + _t(X + 54, y + 41, '✓', 20, '#fff', 'middle', w=900) + _t(X + 84, y + 30, 'ĐƠN HÀNG MỚI', 12, 'hsl(145,55%,36%)', w=900) + _t(X + 84, y + 54, txt, 15 if len(txt) < 16 else 12, '#1b1b1b', w=800) + '</g>')
        j += [S(f'#{i} .o{k}', 0, opacity=0, y=-20), T(f'#{i} .o{k}', t, opacity=1, y=0, duration=.35, ease='back.out(2)')]
    I = _iso(520, 500 if title else 440, 42); boxes = ''
    for k, (x, y, z) in enumerate(((0, 0, 0), (1.2, 0, 0), (.6, .2, .9), (0, 1.2, 0), (1.2, 1.2, 0))):
        boxes += _box(I, x, y, 1.1, 1.1, .85 + 0 * z, 'hsl(32,50%,66%)', 'hsl(30,45%,54%)', 'hsl(28,40%,42%)', 'pk', f'<path d="M{_pt([I(x + .55, y, .85), I(x + .55, y + 1.1, .85)])}" stroke="hsl(40,30%,85%)" stroke-width="6"/>').replace('<g class="pk">', f'<g class="pk" transform="translate(0 {-z * 30:.0f})">')
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + f'<g class="dv">{base}{scr}{glass}</g>' + boxes
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .dv', a + .05, 40, .8), S(f'#{i} .pk', 0, opacity=0, y=-60), T(f'#{i} .pk', a + .5, opacity=1, y=0, duration=.4, stagger=.15, ease='bounce.out')] + j
    s += _src(source)
    return _out(i, a, b, 'r_tmdt', s, j), j, [(t, 'pop') for _, t in items[:4]]


# ================================================================= DỊCH VỤ ==
def dulich(i, a, b, t0, value, unit='lượt khách', dest='ĐẮK LẮK', kicker='DU LỊCH', title='', source=''):
    """máy bay thân bạc bay ngang trời hoàng hôn kéo vệt khói, thác nước & núi đồi bên dưới; số lượt khách"""
    X0, Y0, W, H = 60, 380 if title else 320, 600, 300; HZ = Y0 + 190
    s = _defs(i) + _kit(i) + _skydefs(i, 'hsl(210,55%,40%)', 'hsl(30,85%,72%)') + _lg(f'{i}fu', '#ffffff', '#9aa3ad') + '</defs>' + _head(kicker, title)
    s += _numblk(value, unit, (380 if title else 320) - 30, 110, 36)
    body = _sky(i, X0, Y0, W, H, HZ, sunx=X0 + 480) + f'<rect x="{X0}" y="{HZ}" width="{W}" height="{H - 190}" fill="hsl(130,30%,26%)"/>'
    body += f'<path d="M{X0 + 120} {HZ - 40} L{X0 + 150} {HZ - 70} L{X0 + 180} {HZ - 40} V{HZ + 40} H{X0 + 120} Z" fill="hsl(150,25%,22%)"/><rect x="{X0 + 142}" y="{HZ - 60}" width="16" height="100" fill="#e8f4ff" opacity=".85"/>'
    body += f'<ellipse cx="{X0 + 150}" cy="{HZ + 44}" rx="50" ry="10" fill="#e8f4ff" opacity=".6"/>'
    plane = (f'<g class="pl"><path d="M-120 0 Q-130 -14 -100 -16 H60 Q100 -14 110 0 Q100 14 60 14 H-100 Q-130 14 -120 0 Z" fill="url(#{i}fu)"/>'
             f'<path d="M-20 0 L-60 50 H-36 L30 4 Z" fill="#c9ced6"/><path d="M-20 -4 L-50 -40 H-30 L20 -6 Z" fill="#aeb4bd"/><path d="M-100 -14 L-124 -46 H-108 L-80 -14 Z" fill="hsl(356,70%,50%)"/>'
             + ''.join(f'<circle cx="{-70 + q * 14}" cy="-5" r="2.5" fill="#1d2a38"/>' for q in range(10)) + f'<path d="M84 -8 q12 2 16 8 h-16 z" fill="#1d2a38"/><path d="M-100 -9 H70" stroke="hsl(210,60%,45%)" stroke-width="3"/></g>')
    body += f'<path class="tr" d="M{X0 - 40} {Y0 + 110} Q{X0 + 200} {Y0 + 90} {X0 + 420} {Y0 + 60}" stroke="#fff" stroke-opacity=".7" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#{i}sf)" pathLength="1"/>' + plane
    s += _card(i, X0, Y0, W, H, body) + f'<g class="ds">' + _t(X0 + W - 10, Y0 + H + 34, '✈ ' + dest, 22, AC, 'end', w=900) + '</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0 + .3, value) + [_rv(f'#{i} .cd', a + .1, 30, .8), S(f'#{i} .pl', 0, x=X0 - 160, y=Y0 + 116, rotation=-6, scale=.6),
                                                                         T(f'#{i} .pl', t0, x=X0 + 440, y=Y0 + 58, scale=.9, duration=max(1.2, b - t0 - .3), ease='sine.inOut'),
                                                                         S(f'#{i} .tr', 0, strokeDasharray=1, strokeDashoffset=1), T(f'#{i} .tr', t0 + .1, strokeDashoffset=0, duration=max(1.2, b - t0 - .3), ease='sine.inOut'),
                                                                         _rv(f'#{i} .ds', t0 + .6, 10)]
    return _out(i, a, b, 'r_dulich', s, j), j, [(t0, 'air'), (t0 + .9, 'count')]


def luutru(i, a, b, t0, pct, kicker='DỊCH VỤ', title='Công suất phòng', source=''):
    """khách sạn cao tầng 3D về đêm: cửa sổ lần lượt sáng đèn tới pct%, biển HOTEL, hồ bơi; số % lớn"""
    f = min(1, (_isn(pct) or 60) / 100); I = _iso(470, 600 if title else 550, 30)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _numblk(pct, '%', 450 if title else 400, 120, 50)
    s += _ground(I, i, -.5, -.5, 4.5, 4.5, 'hsl(215,18%,24%)') + f'<polygon points="{_P4(I, 2.6, .3, 4.2, 1.6)}" fill="url(#{i}wt)"/>'
    cols, rows = 4, 8; x, y, w, d, h = .3, 1.8, 2.2, 2.2, 6.6
    winL = [(r, q) for r in range(rows) for q in range(cols)]; random.seed(5); order = winL[:]; random.shuffle(order)
    nOn = round(f * len(winL)); onL = set(order[:nOn]); onR = set(order[len(winL) - nOn:]) if nOn else set()
    body = _box(I, x, y, w, d, h, 'hsl(215,15%,40%)', 'hsl(215,18%,28%)', 'hsl(215,20%,20%)', '')
    dz = h / (rows + .4)
    for (r, q) in winL:
        for face in ('L', 'R'):
            if face == 'L':
                x0, z0 = x + q * w / cols + w / cols * .2, .25 * dz + r * dz + dz * .2
                P = [I(x0, y + d, z0), I(x0 + w / cols * .6, y + d, z0), I(x0 + w / cols * .6, y + d, z0 + dz * .55), I(x0, y + d, z0 + dz * .55)]; lit = (r, q) in onL
            else:
                y0 = y + q * d / cols + d / cols * .2; z0 = .25 * dz + r * dz + dz * .2
                P = [I(x + w, y0, z0), I(x + w, y0 + d / cols * .6, z0), I(x + w, y0 + d / cols * .6, z0 + dz * .55), I(x + w, y0, z0 + dz * .55)]; lit = (r, q) in onR
            body += f'<polygon class="{"wo" if lit else "wf"}" points="{_pt(P)}" fill="{"hsl(44,95%,62%)" if lit else "#1c2230"}"/>'
    sx, sy = I(x + w / 2, y + d, h + .4)
    body += f'<rect x="{sx - 56:.0f}" y="{sy - 34:.0f}" width="112" height="30" rx="4" fill="#111"/>' + _t(sx, sy - 12, 'HOTEL', 20, 'hsl(44,100%,62%)', 'middle', w=900).replace('<text', f'<text filter="url(#{i}gl)"')
    s += f'<g class="bd">{body}</g>'
    j = _vis(i, a, b) + _headj(i, a, title) + _numj(i, t0, pct) + [_rv(f'#{i} .gd', a + .05, 30, .8), S(f'#{i} .bd', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .bd', a + .2, scaleY=1, duration=.8, ease='expo.out'),
                                                                   S(f'#{i} .wo', 0, attr={'fill': '#1c2230'}), T(f'#{i} .wo', t0, attr={'fill': 'hsl(44,95%,62%)'}, duration=.1, stagger={'each': .02, 'from': 'random'})]
    s += _src(source)
    return _out(i, a, b, 'r_luutru', s, j), j, [(t0, 'tick'), (t0 + 1, 'ding')]


def _poi(I, i, kind, x, y, cls):
    if kind == 'school':
        return (f'<g class="{cls}">' + _box(I, x, y, 1.4, .8, .8, 'hsl(44,60%,80%)', 'hsl(40,50%,66%)', 'hsl(36,45%,52%)')
                + f'<path d="M{_pt([I(x + 1.2, y + .2, .8), I(x + 1.2, y + .2, 1.6)])}" stroke="#ddd" stroke-width="2"/><polygon points="{_pt([I(x + 1.2, y + .2, 1.6), I(x + 1.2, y - .3, 1.45), I(x + 1.2, y + .2, 1.3)])}" fill="hsl(356,80%,50%)"/></g>')
    if kind == 'hospital':
        cx_, cy_ = I(x + .7, y + .4, 1.05)
        return (f'<g class="{cls}">' + _box(I, x, y, 1.4, .9, 1.0, '#f4f6f8', '#d5dade', '#aab1b8')
                + f'<rect x="{cx_ - 9:.0f}" y="{cy_ - 3:.0f}" width="18" height="6" fill="hsl(356,80%,50%)"/><rect x="{cx_ - 3:.0f}" y="{cy_ - 9:.0f}" width="6" height="18" fill="hsl(356,80%,50%)"/></g>')
    if kind == 'market':
        return f'<g class="{cls}">' + ''.join(_box(I, x + q * .55, y, .5, .9, .55, ('hsl(356,70%,55%)', 'hsl(44,90%,55%)', 'hsl(205,60%,50%)')[q], '#ddd', '#bbb') for q in range(3)) + '</g>'
    if kind == 'park':
        return f'<g class="{cls}"><polygon points="{_P4(I, x, y, x + 1.4, y + 1.2)}" fill="hsl(110,45%,45%)"/>' + ''.join(_tree(I, i, x + dx, y + dy, .8, 'x') for dx, dy in ((.3, .3), (1.0, .4), (.6, .9))) + '</g>'
    if kind == 'mall':
        return f'<g class="{cls}">' + _box(I, x, y, 1.6, 1.0, .8, 'hsl(205,20%,80%)', f'url(#{i}gw)', 'hsl(205,25%,48%)') + '</g>'
    return f'<g class="{cls}">' + _house(I, x, y, .9, .9, .8, 25, '') + '</g>'


def tienich(i, a, b, items, center='DỰ ÁN', rings=(), kicker='VỊ TRÍ', title='Tiện ích xung quanh', source=''):
    """mặt bằng 3D: toà dự án ở giữa, các tiện ích dựng hình thật (trường có cờ, bệnh viện chữ thập, chợ mái màu, công viên, TTTM kính) + khoảng cách;
    items=[('school' | 'hospital' | 'market' | 'park' | 'mall', 'TÊN', '500 m', t)] ≤6 · rings=[('1 km', t)] ≤2"""
    I = _iso(360, 290 if title else 240, 30); C = (5, 5)
    s = _defs(i) + _kit(i) + '</defs>' + _head(kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,24%,36%)')
    s += f'<polygon points="{_P4(I, 4.7, 0, 5.3, 10)}" fill="#34373c"/><polygon points="{_P4(I, 0, 4.7, 10, 5.3)}" fill="#34373c"/>'
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .8)]
    for k, (lab, t) in enumerate(list(rings)[:2]):
        rr = 2.3 + k * 1.7; P = [I(C[0] + rr * math.cos(u), C[1] + rr * math.sin(u)) for u in [q * math.pi / 30 for q in range(61)]]; cx_, cy_ = I(*C)
        s += f'<polygon class="rg{k}" points="{_pt(P)}" fill="none" stroke="hsl(46,100%,65%)" stroke-width="2" stroke-dasharray="8 6" opacity=".8"/>'
        lx, ly = I(C[0] - rr * .707, C[1] - rr * .707); s += f'<g class="rl{k}">' + _t(lx, ly - 6, lab, 15, AC, 'middle', w=900) + '</g>'
        j += [S(f'#{i} .rg{k}', 0, scale=0, opacity=0, svgOrigin=f'{cx_:.0f} {cy_:.0f}'), T(f'#{i} .rg{k}', t, scale=1, opacity=1, duration=.9, ease='expo.out', svgOrigin=f'{cx_:.0f} {cy_:.0f}'), _rv(f'#{i} .rl{k}', t + .3, 8)]
    SL = [(1.4, 1.4), (7.2, 1.2), (7.6, 7.2), (1.2, 7.4), (7.4, 4.0), (1.0, 3.6)]
    pl = []
    for k, it in enumerate(list(items)[:6]):
        kind, nm, dist, t = (list(it) + ['', 0])[:4] if len(it) >= 4 else (it[0], it[1], '', it[-1])
        x, y = SL[k]; pl.append((x + y, k, kind, nm, dist, t, x, y))
    pl.append((10, -1, 'tower', center, '', a + .3, 4.4, 4.4))
    for _, k, kind, nm, dist, t, x, y in sorted(pl):
        if k < 0:
            s += '<g class="ctr">' + _tower(I, i, 4.4, 4.4, 1.2, 1.2, 3.0, '', 4, 8, 30) + '</g>'
            cx_, cy_ = I(5, 5, 3.4); s += f'<g class="cl_"><rect x="{cx_ - _w(nm, 18) / 2 - 16:.0f}" y="{cy_ - 42:.0f}" width="{_w(nm, 18) + 32:.0f}" height="34" rx="17" fill="{AC}"/>' + _t(cx_, cy_ - 19, nm, 18, '#111', 'middle', w=900) + '</g>'
            j += [S(f'#{i} .ctr', 0, scaleY=0, transformOrigin='50% 100%'), T(f'#{i} .ctr', a + .3, scaleY=1, duration=.7, ease='expo.out'), _rv(f'#{i} .cl_', a + .7, 10)]
            continue
        s += _poi(I, i, kind, x, y, f'p{k}')
        lx, ly = I(x + .7, y + .5, 1.8)
        s += f'<g class="pl{k}">' + _t(lx, ly - 14, nm, 16, FG, 'middle', w=900) + (_t(lx, ly + 6, dist, 14, AC, 'middle', w=800) if dist else '') + '</g>'
        j += [S(f'#{i} .p{k}', 0, scaleY=0, opacity=0, transformOrigin='50% 100%'), T(f'#{i} .p{k}', t, scaleY=1, opacity=1, duration=.5, ease='back.out(2)'), _rv(f'#{i} .pl{k}', t + .15, 8)]
    s += _note(source)
    return _out(i, a, b, 'r_tienich', s, j), j, [(a + .3, 'block')] + [(it[-1], 'pop') for it in list(items)[:6]]



# ================================================================ NHÀ Ở · KHẢ NĂNG CHI TRẢ · LỘ TRÌNH (19/11/2026) ==
def khanang(i, a, b, t0, t_gap=None, income='THU NHẬP', price='GIÁ NHÀ', gap='', kicker='KHẢ NĂNG CHI TRẢ', title='', source=''):
    """chồng xu vàng THU NHẬP (thấp) cạnh khối nhà đỏ GIÁ NHÀ vươn cao; t_gap: vạch so + ngoặc đỏ khoảng cách (gap='VƯỢT XA' chỉ khi lời có)"""
    t_gap = t0 + 1.6 if t_gap is None else t_gap; OY = 600 if title else 570; s_ = 62; I = _iso(360, OY, s_)
    s = (_defs(i) + _kit(i) + _lg(f'{i}cs', 'hsl(44,85%,58%)', 'hsl(36,80%,34%)', 1, 0) + _lg(f'{i}ct', 'hsl(50,100%,80%)', 'hsl(42,90%,55%)', 1, 1)
         + _lg(f'{i}rt', 'hsl(358,80%,62%)', 'hsl(356,75%,48%)', 1, 1) + _lg(f'{i}rl', 'hsl(356,70%,42%)', 'hsl(352,70%,26%)') + _lg(f'{i}rr', 'hsl(354,72%,34%)', 'hsl(350,70%,18%)')
         + _lg(f'{i}rf', 'hsl(20,30%,40%)', 'hsl(18,30%,22%)') + '</defs>' + _head(kicker, title))
    s += _box(I, -2.3, -2.3, 4.6, 4.6, .14, 'hsl(28,10%,24%)', 'hsl(28,10%,15%)', 'hsl(28,10%,11%)', 'pl')   # bệ
    s += f'<ellipse cx="360" cy="{OY + 18}" rx="230" ry="40" fill="#000" opacity=".35" filter="url(#{i}sf)"/>'
    # chồng xu thu nhập
    cx, cy = I(-.95, .95, .14); n = 7; coins = ''
    for k in range(n):
        y = cy - k * 12
        coins += (f'<g class="cn{k}"><rect x="{cx - 50:.0f}" y="{y - 12:.0f}" width="100" height="12" fill="url(#{i}cs)"/>'
                  f'<ellipse cx="{cx:.0f}" cy="{y:.0f}" rx="50" ry="17" fill="url(#{i}cs)"/><ellipse cx="{cx:.0f}" cy="{y - 12:.0f}" rx="50" ry="17" fill="url(#{i}ct)"/>'
                  f'<ellipse cx="{cx:.0f}" cy="{y - 12:.0f}" rx="36" ry="11" fill="none" stroke="hsl(40,80%,45%)" stroke-width="1.5" opacity=".7"/></g>')
    top_inc = cy - n * 12 - 17
    s += f'<ellipse cx="{cx:.0f}" cy="{cy + 4:.0f}" rx="60" ry="20" fill="#000" opacity=".45" filter="url(#{i}sf)"/>' + coins
    # khối nhà giá cao
    x0, y0, w, h = .35, -1.45, 1.1, 4.2
    blk = _box(I, x0, y0, w, w, h, f'url(#{i}rt)', f'url(#{i}rl)', f'url(#{i}rr)', 'rb')
    win = ''.join(f'<polygon points="{_pt([I(x0 + .18 + c * .32, y0 + w, .35 + r * .55), I(x0 + .36 + c * .32, y0 + w, .35 + r * .55), I(x0 + .36 + c * .32, y0 + w, .62 + r * .55), I(x0 + .18 + c * .32, y0 + w, .62 + r * .55)])}" fill="hsl(40,90%,75%)" opacity=".28"/>'
                  for r in range(7) for c in range(3))
    roof = (f'<polygon points="{_pt([I(x0, y0 + w, h), I(x0 + w, y0 + w, h), I(x0 + w / 2, y0 + w, h + .75)])}" fill="url(#{i}rl)"/>'
            f'<polygon points="{_pt([I(x0 + w / 2, y0 + w, h + .75), I(x0 + w / 2, y0, h + .75), I(x0 + w, y0, h), I(x0 + w, y0 + w, h)])}" fill="url(#{i}rf)"/>')
    bx, by = I(x0 + w, y0 + w, 0); rtop = I(x0 + w / 2, y0 + w, h + .75)[1]
    s += f'<clipPath id="{i}cl"><rect class="clr" x="0" y="{by + 4:.0f}" width="720" height="0"/></clipPath><g clip-path="url(#{i}cl)">{blk}{win}{roof}</g>'
    # vạch so + ngoặc khoảng cách
    gx = I(x0, y0 + w, 0)[0] - 26; rt = I(x0, y0 + w, h)[1]
    s += (f'<path class="dl" d="M{cx + 55:.0f} {top_inc:.0f} H{gx + 14:.0f}" stroke="#fff" stroke-opacity=".55" stroke-width="2" stroke-dasharray="6 6"/>'
          f'<path class="br" d="M{gx + 10:.0f} {top_inc:.0f} H{gx:.0f} V{rt:.0f} H{gx + 10:.0f}" fill="none" stroke="{DN}" stroke-width="4" stroke-linecap="round" filter="url(#{i}gl)"/>')
    if gap: s += f'<g class="gp">{_t(gx - 14, (top_inc + rt) / 2 + 9, gap, 26, DN, "end", w=900, ls=1)}</g>'
    s += (f'<g class="lb">{_t(cx, by + 62, income, 22, "hsl(44,85%,65%)", "middle", w=800, ls=2)}{_t(I(x0 + w / 2, y0 + w / 2, 0)[0], by + 62, price, 22, "#ff8a8d", "middle", w=800, ls=2)}</g>')
    s += _note(source or 'hình minh hoạ')
    L = (rt - top_inc) ** 2
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pl', a + .05, 20, .6), _rv(f'#{i} .lb', a + .3, 10, .5)]
    j += [S(f'#{i} .cn{k}', 0, y=-40, opacity=0) + T(f'#{i} .cn{k}', t0 + k * .07, y=0, opacity=1, duration=.35, ease='back.out(2)') for k in range(n)]
    j += [T(f'#{i} .clr', t0 + .4, attr={'y': rtop - 10, 'height': by - rtop + 14}, duration=1.3, ease='power3.out'),
          S(f'#{i} .dl', 0, opacity=0) + T(f'#{i} .dl', t_gap, opacity=1, duration=.4),
          S(f'#{i} .br', 0, opacity=0, scaleY=0, transformOrigin=f'{gx:.0f}px {top_inc:.0f}px') + T(f'#{i} .br', t_gap + .1, opacity=1, scaleY=1, duration=.6, ease='expo.out')]
    if gap: j.append(_rv(f'#{i} .gp', t_gap + .4, 10, .5))
    return _out(i, a, b, 'r_khanang', s, j), j, [(t0, 'count'), (t0 + .4, 'riser'), (t_gap + .1, 'block')]


def noxh(i, a, b, t0, value='', unit='căn', tag='NOXH', t_num=None, kicker='NHÀ Ở XÃ HỘI', title='', source=''):
    """cụm 3 toà chung cư 3D mọc lên, cửa sổ sáng dần, cây xanh quanh bệ, biển tên trên nóc (tag); value: số căn đếm (chỉ khi lời có)"""
    big = bool(value); s_ = 32 if big else 36; OY = 630 if big else 585; I = _iso(360, OY, s_)
    s = (_defs(i) + _kit(i) + _lg(f'{i}wl', 'hsl(36,18%,86%)', 'hsl(30,12%,70%)') + _lg(f'{i}wr', 'hsl(30,10%,60%)', 'hsl(28,10%,42%)') + _lg(f'{i}wt', 'hsl(36,20%,92%)', 'hsl(36,15%,80%)', 1, 1)
         + '</defs>' + _head(kicker, title))
    if big: s += _numblk(value, unit, 330, 120)
    s += f'<ellipse cx="360" cy="{OY + 22}" rx="250" ry="46" fill="#000" opacity=".4" filter="url(#{i}sf)"/>'
    s += _box(I, -3.2, -1.6, 6.6, 3.4, .16, 'hsl(100,22%,34%)', 'hsl(100,20%,22%)', 'hsl(100,20%,17%)', 'pl')
    T3 = [(-2.6, -.9, 1.5, 1.5, 6.0), (-.55, -1.2, 1.5, 1.5, 7.6), (1.5, -.9, 1.5, 1.5, 5.2)]
    js_t = []
    for n, (x0, y0, w, d, h) in enumerate(T3):
        body = _box(I, x0, y0, w, d, h, f'url(#{i}wt)', f'url(#{i}wl)', f'url(#{i}wr)')
        ws = ''
        for r in range(int((h - .5) / .55)):
            z = .4 + r * .55
            for c in range(3):
                u = .18 + c * .44
                ws += f'<polygon class="w{n}" points="{_pt([I(x0 + u, y0 + d, z), I(x0 + u + .26, y0 + d, z), I(x0 + u + .26, y0 + d, z + .3), I(x0 + u, y0 + d, z + .3)])}" fill="hsl(205,30%,28%)"/>'
                ws += f'<polygon class="w{n}" points="{_pt([I(x0 + w, y0 + u, z), I(x0 + w, y0 + u + .26, z), I(x0 + w, y0 + u + .26, z + .3), I(x0 + w, y0 + u, z + .3)])}" fill="hsl(205,30%,22%)"/>'
        lit = ws.replace(f'class="w{n}"', f'class="l{n}"').replace('fill="hsl(205,30%,28%)"', 'fill="hsl(42,95%,68%)"').replace('fill="hsl(205,30%,22%)"', 'fill="hsl(40,90%,58%)"')
        bx, by = I(x0 + w, y0 + d, 0); ty = I(x0, y0, h)[1]
        s += (f'<clipPath id="{i}c{n}"><rect class="cr{n}" x="0" y="{by + 4:.0f}" width="720" height="0"/></clipPath>'
              f'<g clip-path="url(#{i}c{n})">{body}{ws}<g class="lt{n}" opacity="0">{lit}</g></g>')
        js_t.append((n, by, ty))
    for k, (tx, ty_) in enumerate([(-3.0, 1.4), (-1.4, 1.6), (.4, 1.5), (2.2, 1.55), (3.1, .2)]):
        px, py = I(tx, ty_, .16)
        s += f'<g class="tr{k}"><ellipse cx="{px:.0f}" cy="{py + 2:.0f}" rx="14" ry="5" fill="#000" opacity=".4"/><rect x="{px - 2:.0f}" y="{py - 16:.0f}" width="4" height="16" fill="hsl(28,40%,28%)"/><circle cx="{px:.0f}" cy="{py - 24:.0f}" r="15" fill="hsl(115,40%,36%)"/><circle cx="{px - 5:.0f}" cy="{py - 29:.0f}" r="7" fill="hsl(105,45%,48%)"/></g>'
    if tag:
        x0, y0, w, d, h = T3[1]; px, py = I(x0 + w / 2, y0 + d / 2, h)
        tw = _w(tag, 22) + 30
        if big: px, py = 60 + tw / 2, 430   # có số lớn → biển tên thành nhãn dưới số, không đè số
        s += f'<g class="tg"><rect x="{px - tw / 2:.0f}" y="{py - 62:.0f}" width="{tw:.0f}" height="38" rx="8" fill="hsl(44,85%,58%)" filter="url(#{i}sh)"/>{_t(px, py - 36, tag, 22, "#17140f", "middle", w=900, ls=2)}' + ('' if big else f'<path d="M{px:.0f} {py - 24:.0f} V{py:.0f}" stroke="hsl(44,85%,58%)" stroke-width="3"/>') + '</g>'
    s += _note(source or 'hình minh hoạ')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pl', a + .05, 20, .6)]
    for n, by, ty in js_t:
        j += [T(f'#{i} .cr{n}', t0 + n * .25, attr={'y': ty - 10, 'height': by - ty + 14}, duration=1.1, ease='power3.out'),
              T(f'#{i} .lt{n}', t0 + 1.1 + n * .2, opacity=1, duration=.8, ease='steps(6)')]
    j += [S(f'#{i} .tr{k}', 0, scale=0, transformOrigin='50% 100%') + T(f'#{i} .tr{k}', t0 + .8 + k * .08, scale=1, duration=.5, ease='back.out(2.5)') for k in range(5)]
    if tag: j.append(S(f'#{i} .tg', 0, opacity=0, y=-20) + T(f'#{i} .tg', t0 + 1.5, opacity=1, y=0, duration=.5, ease='back.out(2)'))
    if big: j += _numj(i, t0 if t_num is None else t_num, value)
    return _out(i, a, b, 'r_noxh', s, j), j, [(t0, 'rumble'), (t0 + 1.5, 'pop')] + ([((t0 if t_num is None else t_num), 'count')] if big else [])


def mocnam(i, a, b, steps, value='', unit='', kicker='LỘ TRÌNH', title='', source=''):
    """lộ trình theo năm: thanh ray kim loại, cột mốc vàng cao dần theo thời gian, thanh tiến độ sáng chạy tới từng mốc; steps=[('2026', t), ('2030', t)] ≤4; value: mục tiêu (đếm ở mốc cuối)"""
    n = min(4, len(steps)); X0, X1, Y = 110, 610, 590; xs = [X0 + (X1 - X0) * (k / (n - 1) if n > 1 else .5) for k in range(n)]
    s = (_defs(i) + _kit(i) + _lg(f'{i}pg', 'hsl(50,100%,78%)', 'hsl(38,85%,42%)', 1, 0) + _lg(f'{i}ps', 'hsl(42,85%,52%)', 'hsl(34,80%,28%)', 1, 0)
         + _lg(f'{i}fl', 'hsl(44,95%,62%)', 'hsl(36,90%,48%)', 1, 0) + '</defs>' + _head(kicker, title))
    if value: s += _numblk(value, unit, 330 if title else 290, 120)
    s += (f'<ellipse cx="360" cy="{Y + 26}" rx="290" ry="22" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
          f'<rect x="{X0 - 30}" y="{Y - 9}" width="{X1 - X0 + 60}" height="18" rx="9" fill="url(#{i}mt)"/><rect x="{X0 - 30}" y="{Y - 5}" width="{X1 - X0 + 60}" height="10" rx="5" fill="#121214"/>'
          f'<rect class="pf" x="{X0 - 26}" y="{Y - 5}" width="0" height="10" rx="5" fill="url(#{i}fl)" filter="url(#{i}gl)"/>')
    for k, (lb, t) in enumerate(steps[:n]):
        hgt = 60 + (90 if value else 150) * (k / (n - 1) if n > 1 else 1); x = xs[k]
        s += (f'<g class="m{k}"><rect x="{x - 22:.0f}" y="{Y - hgt:.0f}" width="44" height="{hgt:.0f}" fill="url(#{i}ps)"/>'
              f'<rect x="{x - 22:.0f}" y="{Y - hgt:.0f}" width="16" height="{hgt:.0f}" fill="url(#{i}pg)" opacity=".85"/>'
              f'<ellipse cx="{x:.0f}" cy="{Y - hgt:.0f}" rx="22" ry="8" fill="hsl(50,100%,82%)"/>'
              f'<circle cx="{x:.0f}" cy="{Y:.0f}" r="11" fill="hsl(44,95%,62%)" stroke="#fff" stroke-width="3"/>'
              + _t(x, Y - hgt - 22, lb, 40, FG, 'middle', w=800) + '</g>')
    s += _note(source or '')
    j = _vis(i, a, b) + _headj(i, a, title)
    for k, (lb, t) in enumerate(steps[:n]):
        hgt = 60 + (90 if value else 150) * (k / (n - 1) if n > 1 else 1)
        j.append(S(f'#{i} .m{k}', 0, opacity=0, scaleY=0, transformOrigin=f'{xs[k]:.0f}px {Y}px') + T(f'#{i} .m{k}', t, opacity=1, scaleY=1, duration=.7, ease='back.out(1.6)'))
        j.append(T(f'#{i} .pf', max(a, t - .5), attr={'width': xs[k] - X0 + 26}, duration=.6, ease='power2.inOut'))
    if value: j += _numj(i, steps[n - 1][1], value)
    return _out(i, a, b, 'r_mocnam', s, j), j, [(t, 'tick') for _, t in steps[:n]] + ([(steps[n - 1][1], 'count')] if value else [])


# ================================================================ BỘ MỞ RỘNG 100 HÌNH (19/11/2026) — trợ thủ chung ==
def _qL(title, value):
    """bố cục chuẩn: (sc, Y0 đỉnh bệ, y số lớn) — có số lớn thì bệ nhỏ và thấp hơn"""
    if value and title: return 22, 420, 370
    if value: return 25, 360, 305
    return 30, (300 if title else 240), 0
def _qpop(i, cls, t, d=.5, o='50% 100%', e='back.out(2)'):
    return S(f'#{i} .{cls}', 0, scale=0, opacity=0, transformOrigin=o) + T(f'#{i} .{cls}', t, scale=1, opacity=1, duration=d, ease=e)
def _qgrow(i, cls, t, d=.8, e='expo.out'):
    return S(f'#{i} .{cls}', 0, scaleY=0, opacity=0, transformOrigin='50% 100%') + T(f'#{i} .{cls}', t, scaleY=1, opacity=1, duration=d, ease=e)
def _qfade(i, cls, t, d=.5): return S(f'#{i} .{cls}', 0, opacity=0) + T(f'#{i} .{cls}', t, opacity=1, duration=d)
def _qdraw(i, cls, t, L, d=1.0, e='power2.inOut'):
    return S(f'#{i} .{cls}', 0, strokeDasharray=f'{L:.0f} {L:.0f}', strokeDashoffset=L) + T(f'#{i} .{cls}', t, strokeDashoffset=0, duration=d, ease=e)
def _qpill(x, y, txt, bg, fg='#111', cls='pl', size=18, anchor='middle'):
    w = _w(txt, size) + 28; x0 = x - w / 2 if anchor == 'middle' else x
    return (f'<g class="{cls}"><rect x="{x0:.0f}" y="{y - size - 4:.0f}" width="{w:.0f}" height="{size + 16:.0f}" rx="{(size + 16) / 2:.0f}" fill="{bg}"/>'
            + _t(x0 + w / 2, y + 1, txt, size, fg, 'middle', w=900, ls=1) + '</g>')
def _qcyl(cx, cy, rx, ry, h, side, top, cls=''):
    return (f'<g class="{cls}"><ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{side}"/><rect x="{cx - rx:.0f}" y="{cy - h:.0f}" width="{2 * rx:.0f}" height="{h:.0f}" fill="{side}"/>'
            f'<ellipse cx="{cx:.0f}" cy="{cy - h:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{top}"/></g>')
def _qnum(i, value, unit, ny, t):
    if not value: return '', []
    return _numblk(value, unit, ny, 120), _numj(i, t, value)
def _qpin(x, y, col='hsl(356,80%,52%)', cls='pn', lab='', lc=FG):
    return (f'<g class="{cls}"><ellipse cx="{x:.0f}" cy="{y:.0f}" rx="9" ry="4" fill="#000" opacity=".45"/>'
            f'<path d="M{x:.0f} {y:.0f} C{x - 4:.0f} {y - 14:.0f} {x - 16:.0f} {y - 22:.0f} {x - 16:.0f} {y - 34:.0f} A16 16 0 1 1 {x + 16:.0f} {y - 34:.0f} C{x + 16:.0f} {y - 22:.0f} {x + 4:.0f} {y - 14:.0f} {x:.0f} {y:.0f}Z" fill="{col}"/>'
            f'<circle cx="{x:.0f}" cy="{y - 34:.0f}" r="6" fill="#fff"/>' + (_t(x, y - 58, lab, 16, lc, 'middle', w=900) if lab else '') + '</g>')
def _qroadx(I, x0, x1, y, wd=.6, cls='rd'):
    return (f'<g class="{cls}"><polygon points="{_P4(I, x0, y - wd / 2, x1, y + wd / 2, .01)}" fill="#2e3136"/>'
            f'<path d="M{_pt([I(x0, y, .02), I(x1, y, .02)])}" stroke="#e8e2c8" stroke-width="2" stroke-dasharray="10 9" opacity=".8"/></g>')
def _qroady(I, y0, y1, x, wd=.6, cls='rd'):
    return (f'<g class="{cls}"><polygon points="{_P4(I, x - wd / 2, y0, x + wd / 2, y1, .01)}" fill="#2e3136"/>'
            f'<path d="M{_pt([I(x, y0, .02), I(x, y1, .02)])}" stroke="#e8e2c8" stroke-width="2" stroke-dasharray="10 9" opacity=".8"/></g>')
def _qarrow(x0, y0, x1, y1, col, w=5, cls='ar'):
    an = math.atan2(y1 - y0, x1 - x0); hx, hy = x1 - 16 * math.cos(an), y1 - 16 * math.sin(an)
    p = [(x1, y1), (hx + 9 * math.sin(an), hy - 9 * math.cos(an)), (hx - 9 * math.sin(an), hy + 9 * math.cos(an))]
    return (f'<g class="{cls}"><path d="M{x0:.0f} {y0:.0f} L{hx:.0f} {hy:.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{_pt(p)}" fill="{col}"/></g>')
def _qhead(i, kicker, title, extra=''):
    return _defs(i) + _kit(i) + extra + '</defs>' + _head(kicker, title)
def _qlab(x, y, txt, col=FG, size=17, cls='lb', anchor='middle'):
    return f'<g class="{cls}">' + _t(x, y, txt, size, col, anchor, w=900, ls=1) + '</g>' if txt else ''
GOLD, RED, GRN = 'hsl(44,90%,60%)', 'hsl(356,78%,58%)', 'hsl(145,55%,48%)'


# ---------------------------------------------------------------- PHÁP LÝ +4
def chuyenmd(i, a, b, t0, t_conv=None, from_='ĐẤT NÔNG NGHIỆP', to='ĐẤT Ở', kicker='PHÁP LÝ', title='', source=''):
    """chuyển mục đích sử dụng đất: thửa ruộng xanh lật thành nền đất ở, nhà mọc lên; nhãn trước → sau"""
    t_conv = t0 + 1.2 if t_conv is None else t_conv; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 20, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,18%,30%)')
    s += f'<g class="fd"><polygon points="{_P4(I, 1, 1, 9, 9, .02)}" fill="hsl(98,48%,40%)"/>' + ''.join(f'<path d="M{_pt([I(1 + k * .5, 1, .03), I(1 + k * .5, 9, .03)])}" stroke="hsl(95,55%,30%)" stroke-width="2"/>' for k in range(1, 16)) + '</g>'
    s += f'<g class="lot"><polygon points="{_P4(I, 1, 1, 9, 9, .02)}" fill="hsl(36,30%,62%)"/><polygon points="{_P4(I, 1, 1, 9, 9, .02)}" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="8 6"/></g>'
    s += ''.join(f'<g class="h{k}">' + _house(I, x, y, 1.6, 1.6, 1.4, 18 + k * 8, '') + '</g>' for k, (x, y) in enumerate([(2, 2), (5.6, 2), (2, 5.6), (5.6, 5.6)]))
    s += _qpill(200, 640, from_, 'hsl(98,45%,40%)', '#fff', 'p1', 17) + _qarrow(300, 634, 400, 634, GOLD, 4, 'ar') + _qpill(500, 640, to, GOLD, '#111', 'p2', 17) + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'fd', a + .2), _rv(f'#{i} .p1', t0, 10),
         S(f'#{i} .lot', 0, opacity=0) + T(f'#{i} .lot', t_conv, opacity=1, duration=.5), T(f'#{i} .fd', t_conv, opacity=0, duration=.5), _qfade(i, 'ar', t_conv), _rv(f'#{i} .p2', t_conv + .2, 10)]
    j += [_qgrow(i, f'h{k}', t_conv + .4 + k * .12, .6, 'back.out(1.6)') for k in range(4)]
    return _out(i, a, b, 'r_chuyenmd', s, j), j, [(t0, 'paper'), (t_conv, 'whoosh'), (t_conv + .4, 'block')]


def tachthua(i, a, b, t0, t_split=None, parts=2, area='', kicker='PHÁP LÝ', title='Tách thửa', source=''):
    """thửa đất 3D bị tia sáng cắt thành 2–3 thửa con, các thửa tách nhẹ ra; area='100 m²' nhãn diện tích (chỉ khi lời có)"""
    t_split = t0 + 1 if t_split is None else t_split; n = max(2, min(3, parts)); sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 30, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,30%)')
    wid = 7 / n
    for k in range(n):
        x0 = 1.5 + k * wid
        s += f'<g class="lt{k}">' + _box(I, x0 + .05, 1.5, wid - .1, 7, .35, 'hsl(34,38%,58%)', 'hsl(30,35%,40%)', 'hsl(28,35%,30%)') + _qlab(*I(x0 + wid / 2, 5, .4), area, '#fff', 18) + '</g>'
    for k in range(1, n):
        x = 1.5 + k * wid; P = [I(x, 1.2, .5), I(x, 8.8, .5)]
        s += f'<path class="cut{k}" d="M{_pt(P)}" stroke="hsl(10,100%,60%)" stroke-width="4" filter="url(#{i}gl)"/>'
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_rv(f'#{i} .lt{k}', t0 + k * .05, 14, .5) for k in range(n)]
    for k in range(1, n):
        x0, y0 = I(1.5 + k * wid, 1.2, .5); x1, y1 = I(1.5 + k * wid, 8.8, .5); L = math.dist((x0, y0), (x1, y1))
        j.append(_qdraw(i, f'cut{k}', t_split, L, .6)); j.append(T(f'#{i} .cut{k}', t_split + .8, opacity=0, duration=.3))
    j += [T(f'#{i} .lt{k}', t_split + .7, x=(k - (n - 1) / 2) * 26, y=(k - (n - 1) / 2) * 14, duration=.6, ease='expo.out') for k in range(n)]
    return _out(i, a, b, 'r_tachthua', s, j), j, [(t0, 'block'), (t_split, 'scan'), (t_split + .7, 'thud')]


def denbu(i, a, b, t0, value='', unit='tỷ đồng', kicker='BỒI THƯỜNG', title='', source=''):
    """bồi thường giải phóng mặt bằng: nhà cũ trên thửa đất có cọc mốc đỏ, xấp tiền trượt vào; value = số tiền (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc)
    sn, jn = _qnum(i, value, unit, ny, t0 + .8)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(90,22%,32%)')
    s += '<g class="hs">' + _house(I, 3, 3, 2.6, 2.4, 1.8, 20, '') + '</g>'
    for k, (x, y) in enumerate([(2, 2), (8, 2), (8, 7.5), (2, 7.5)]):
        px, py = I(x, y); s += f'<g class="mk{k}"><rect x="{px - 3:.0f}" y="{py - 30:.0f}" width="6" height="30" fill="hsl(0,0%,92%)"/><rect x="{px - 3:.0f}" y="{py - 30:.0f}" width="6" height="10" fill="{RED}"/></g>'
    s += '<g class="cs_">' + _cash(i, 430, Y0 + 230 * sc / 30, 6) + '</g>' + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'hs', a + .2)] + [_qgrow(i, f'mk{k}', t0 + k * .1, .4, 'back.out(2)') for k in range(4)]
    j += [S(f'#{i} .cs_', 0, x=180, opacity=0) + T(f'#{i} .cs_', t0 + .6, x=0, opacity=1, duration=.7, ease='expo.out')] + jn
    return _out(i, a, b, 'r_denbu', s, j), j, [(t0, 'pop'), (t0 + .6, 'swish')] + ([(t0 + .8, 'count')] if value else [])


def gpxd(i, a, b, t0, t_ok=None, stamp='ĐÃ CẤP PHÉP', kicker='PHÁP LÝ', title='Giấy phép xây dựng', source=''):
    """giấy phép xây dựng: bản vẽ mặt đứng công trình trên giấy xanh, cẩu tháp vươn lên, dấu xanh 'đã cấp phép' đóng xuống"""
    t_ok = t0 + 1.3 if t_ok is None else t_ok; Y = 300 if title else 250
    s = _qhead(i, kicker, title, _lg(f'{i}bp', 'hsl(212,60%,36%)', 'hsl(214,65%,24%)', 1, 1))
    bp = ''.join(f'<path d="M{110 + q * 40} {Y + 30} V{Y + 330}" stroke="#fff" stroke-opacity=".08"/>' for q in range(11)) + ''.join(f'<path d="M100 {Y + 30 + q * 40} H520" stroke="#fff" stroke-opacity=".08"/>' for q in range(8))
    bld = (f'<g class="dr" fill="none" stroke="#dbe8ff" stroke-width="2.5"><rect x="190" y="{Y + 120}" width="240" height="200"/><path d="M170 {Y + 120} L310 {Y + 50} L450 {Y + 120}"/>'
           + ''.join(f'<rect x="{215 + c * 60}" y="{Y + 150 + r * 55}" width="36" height="34"/>' for r in range(3) for c in range(4)) + f'<rect x="290" y="{Y + 270}" width="40" height="50"/></g>')
    s += _paper(i, 90, Y + 20, 450, 330, f'url(#{i}bp)', 'pp', -3, bp + bld)
    s += (f'<g class="cr"><path d="M560 {Y + 360} V{Y + 20}" stroke="{GOLD}" stroke-width="10"/><path d="M470 {Y + 30} H640" stroke="{GOLD}" stroke-width="8"/>'
          f'<path d="M560 {Y + 20} L600 {Y + 30} M560 {Y + 20} L520 {Y + 30}" stroke="{GOLD}" stroke-width="3"/><path d="M490 {Y + 34} V{Y + 110}" stroke="#ccc" stroke-width="2"/><rect x="478" y="{Y + 110}" width="24" height="18" fill="hsl(28,50%,45%)"/></g>')
    sx, sy = 420, Y + 270
    s += (f'<g class="st" opacity="0"><rect x="{sx - 120}" y="{sy - 34}" width="240" height="68" rx="10" fill="none" stroke="{GRN}" stroke-width="5" transform="rotate(-8 {sx} {sy})"/>'
          + f'<g transform="rotate(-8 {sx} {sy})">' + _t(sx, sy + 10, stamp, 26, GRN, 'middle', w=900, ls=2) + '</g></g>') + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pp', a + .05, 40, .8), _qdraw(i, 'dr rect', t0, 900, 1.2), _qdraw(i, 'dr path', t0, 400, 1.0), _qgrow(i, 'cr', t0 + .3, .8),
         S(f'#{i} .st', 0, opacity=0, scale=1.8, svgOrigin=f'{sx} {sy}') + T(f'#{i} .st', t_ok, opacity=1, scale=1, duration=.2, ease='power4.in', svgOrigin=f'{sx} {sy}')]
    return _out(i, a, b, 'r_gpxd', s, j), j, [(t0, 'pen'), (t0 + .3, 'metal'), (t_ok, 'stamp')]


# ---------------------------------------------------------------- QUY HOẠCH +4
def phankhu(i, a, b, zones, kicker='QUY HOẠCH', title='Phân khu chức năng', source=''):
    """mặt bằng quy hoạch: các ô phân khu nổi khối theo màu chức năng; zones=[(NHÃN, 'o'|'tm'|'cx'|'cn'|'gd', t)] ≤6
    o=đất ở vàng · tm=thương mại đỏ · cx=cây xanh · cn=công nghiệp tím · gd=giáo dục cam"""
    COL = {'o': ('hsl(46,85%,62%)', 'hsl(42,70%,46%)'), 'tm': ('hsl(356,70%,60%)', 'hsl(356,60%,42%)'), 'cx': ('hsl(120,45%,48%)', 'hsl(120,40%,32%)'),
           'cn': ('hsl(275,40%,62%)', 'hsl(275,35%,44%)'), 'gd': ('hsl(26,85%,60%)', 'hsl(24,70%,44%)')}
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,10%,28%)') + _qroadx(I, 0, 10, 5, .5, 'r1') + _qroady(I, 0, 10, 5, .5, 'r2')
    SL = [(.5, .5), (5.4, .5), (.5, 5.4), (5.4, 5.4), (.5, 2.6), (5.4, 2.6)]
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'r1', a + .2), _qfade(i, 'r2', a + .25)]
    zl = list(zones)[:4]; cues = []
    for k, (lab, kind, t) in enumerate(zl):
        x, y = SL[k]; c0, c1 = COL.get(kind, COL['o']); h = .35 + .25 * (k % 2)
        s += f'<g class="z{k}">' + _box(I, x, y, 4.1, 4.1, h, c0, c1, c1) + _qlab(*I(x + 2.05, y + 2.05, h + .1), lab, '#111', 17) + '</g>'
        j.append(_qgrow(i, f'z{k}', t, .6, 'back.out(1.6)')); cues.append((t, 'pop'))
    s += _note(source)
    return _out(i, a, b, 'r_phankhu', s, j), j, cues


def vanhdai(i, a, b, t0, t_ring=None, tag='', kicker='QUY HOẠCH', title='Vành đai', source=''):
    """lõi đô thị nhiều toà nhà, tuyến vành đai xanh sáng tự vẽ bao quanh; tag = tên tuyến (chỉ khi lời có)"""
    t_ring = t0 + .6 if t_ring is None else t_ring; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc); C = (5, 5)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,20%,30%)')
    random.seed(4); bl = ''
    for k, (x, y) in enumerate([(4, 3.6), (5.2, 3.8), (3.7, 4.9), (5.3, 5.1), (4.4, 6.0), (6.2, 4.4)]):
        h = random.uniform(1.6, 3.4); bl += f'<g class="b{k}">' + _tower(I, i, x, y, .9, .9, h, '', 2, int(h * 2), 210) + '</g>'
    P = [I(C[0] + 3.9 * math.cos(u), C[1] + 3.9 * math.sin(u), .03) for u in [q * math.pi / 40 for q in range(81)]]; L = sum(math.dist(P[q], P[q + 1]) for q in range(80))
    s += f'<path class="rg" d="M{_pt(P)}" fill="none" stroke="hsl(150,90%,60%)" stroke-width="12" opacity=".35" filter="url(#{i}gl)"/><path class="rl" d="M{_pt(P)}" fill="none" stroke="hsl(150,95%,72%)" stroke-width="4"/>'
    s += bl
    if tag: x, y = I(C[0] + 2.8, C[1] + 2.8, 0); s += _qpill(x + 60, y + 40, tag, 'hsl(150,70%,45%)', '#06140c', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qgrow(i, f'b{k}', t0 + k * .08, .6) for k in range(6)]
    j += [_qdraw(i, 'rg', t_ring, L, 1.4), _qdraw(i, 'rl', t_ring, L, 1.4)] + ([_rv(f'#{i} .tg', t_ring + 1.2, 10)] if tag else [])
    return _out(i, a, b, 'r_vanhdai', s, j), j, [(t0, 'block'), (t_ring, 'riser')]


def dothimoi(i, a, b, t0, t_grow=None, tag='', kicker='QUY HOẠCH', title='Đô thị mới', source=''):
    """đất trống → lưới đường tự kẻ → nhà phố, toà cao, cây xanh mọc dần (đô thị hình thành); tag = tên khu (chỉ khi lời có)"""
    t_grow = t0 + .9 if t_grow is None else t_grow; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(36,28%,40%)')
    s += ''.join(_qroadx(I, 0, 10, y, .45, f'rx{k}') for k, y in enumerate((3.3, 6.7))) + ''.join(_qroady(I, 0, 10, x, .45, f'ry{k}') for k, x in enumerate((3.3, 6.7)))
    items = []
    for bx in range(3):
        for by in range(3):
            x, y = .55 + bx * 3.35, .55 + by * 3.35
            if (bx + by) % 3 == 0: items.append(_tower(I, i, x + .5, y + .5, 1.3, 1.3, 2.6 + bx * .4, '', 3, 6, 200))
            elif (bx + by) % 3 == 1: items.append(''.join(_house(I, x + q * .9, y + .3, .8, 1.6, 1.0, 20 + q * 10, '') for q in range(3)))
            else: items.append(f'<polygon points="{_P4(I, x, y, x + 2.4, y + 2.4, .02)}" fill="hsl(115,45%,42%)"/>' + ''.join(_tree(I, i, x + dx, y + dy, .8, '') for dx, dy in ((.6, .6), (1.6, .9), (1.0, 1.8))))
    order = sorted(range(9), key=lambda k: (k // 3) + (k % 3))
    for n, k in enumerate(order): s += f'<g class="c{n}">{items[k]}</g>'
    if tag: s += _qpill(360, Y0 - 20, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qfade(i, f'rx{k}', t0 + k * .15) for k in range(2)] + [_qfade(i, f'ry{k}', t0 + .3 + k * .15) for k in range(2)]
    j += [_qgrow(i, f'c{n}', t_grow + n * .12, .5, 'back.out(1.6)') for n in range(9)] + ([_rv(f'#{i} .tg', t_grow + 1.2, 10)] if tag else [])
    return _out(i, a, b, 'r_dothimoi', s, j), j, [(t0, 'scan'), (t_grow, 'block')]


def congvien(i, a, b, t0, value='', unit='ha', kicker='CÂY XANH', title='Công viên – hồ điều hoà', source=''):
    """công viên: hồ nước lấp lánh, đường dạo, hàng cây mọc, ghế đá; value = diện tích (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .4)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(110,42%,38%)')
    lake = [I(5 + 2.6 * math.cos(u) + .4 * math.sin(3 * u), 5 + 2.0 * math.sin(u), .02) for u in [q * math.pi / 24 for q in range(49)]]
    s += f'<polygon class="lk" points="{_pt(lake)}" fill="url(#{i}wt)"/><polygon points="{_pt(lake)}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>'
    s += ''.join(f'<path class="sp{k}" d="M{_pt([I(3.6 + k * .9, 4.2 + (k % 2) * .9, .03), I(4.3 + k * .9, 4.2 + (k % 2) * .9, .03)])}" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/>' for k in range(3))
    P = [I(.6 + 8.8 * q / 30, 8.9 - 1.2 * math.sin(q / 30 * math.pi), .02) for q in range(31)]
    s += f'<path d="M{_pt(P)}" stroke="hsl(36,30%,72%)" stroke-width="9" fill="none" stroke-linecap="round"/>'
    TP = [(1, 1), (2.2, .8), (8.6, 1.2), (9, 2.6), (1, 6.8), (8.8, 7), (1.2, 3.4), (3.4, 9.3), (6.8, 9.4), (8.2, 4.5)]
    s += ''.join(_tree(I, i, x, y, 1.1, f't{k}') for k, (x, y) in enumerate(sorted(TP, key=lambda p: p[0] + p[1]))) + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'lk', t0)] + [_qpop(i, f't{k}', t0 + .2 + k * .07, .45) for k in range(len(TP))]
    j += [S(f'#{i} .sp{k}', 0, opacity=.2) + T(f'#{i} .sp{k}', t0 + .3 * k, opacity=.9, duration=.6, yoyo=True, repeat=6) for k in range(3)] + jn
    return _out(i, a, b, 'r_congvien', s, j), j, [(t0, 'air')] + ([(t0 + .4, 'count')] if value else [])


# ---------------------------------------------------------------- HẠ TẦNG +4
def sanbay(i, a, b, t0, t_plane=None, tag='', kicker='HẠ TẦNG', title='Sân bay', source=''):
    """sân bay: đường băng có vạch, nhà ga kính, tháp điều khiển; máy bay lăn rồi cất cánh ở t_plane; tag = tên sân bay (chỉ khi lời có)"""
    t_plane = t0 + .8 if t_plane is None else t_plane; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,25%,34%)')
    s += f'<polygon points="{_P4(I, .6, 5.6, 9.6, 7.0, .02)}" fill="#2b2e33"/>' + ''.join(f'<polygon points="{_P4(I, 1.2 + q * .9, 6.25, 1.65 + q * .9, 6.35, .03)}" fill="#fff"/>' for q in range(9))
    s += _box(I, 2, 1.5, 5, 1.8, .9, 'hsl(205,15%,82%)', f'url(#{i}gw)', 'hsl(205,25%,45%)', 'tm') + _box(I, 7.6, 1.6, .6, .6, 2.4, '#e9ecef', '#c3c8ce', '#8f969e', 'tw')
    s += _box(I, 7.35, 1.35, 1.1, 1.1, .35, 'hsl(200,40%,55%)', 'hsl(200,40%,40%)', 'hsl(200,40%,30%)', 'tw2').replace('<g class="tw2">', f'<g class="tw2" transform="translate(0 {-2.4 * sc:.0f})">')
    px, py = I(1.6, 6.3, .3)
    pl = (f'<g class="pl"><g transform="translate({px:.0f} {py:.0f}) rotate(30)"><ellipse cx="0" cy="0" rx="46" ry="8" fill="#f2f4f7"/><path d="M-6 0 L-26 -30 L-14 -30 L10 0 Z M-6 0 L-26 30 L-14 30 L10 0 Z" fill="#d7dce2"/>'
          f'<path d="M-40 0 L-50 -14 L-44 -14 L-34 0 Z" fill="hsl(205,70%,45%)"/><path d="M30 -3 h10" stroke="#335" stroke-width="3"/></g></g>')
    s += pl
    if tag: tx, ty = I(4.5, 1.5, 1.2); s += _qpill(tx, ty - 10, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    ex, ey = I(9.4, 6.3, 3.5)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'tm', t0), _qgrow(i, 'tw', t0 + .15), _qfade(i, 'tw2', t0 + .4),
         S(f'#{i} .pl', 0, opacity=0) + T(f'#{i} .pl', t0 + .3, opacity=1, duration=.3) + T(f'#{i} .pl', t_plane, x=ex - px, y=ey - py, duration=1.6, ease='power2.in')]
    if tag: j.append(_rv(f'#{i} .tg', t0 + .6, 10))
    return _out(i, a, b, 'r_sanbay', s, j), j, [(t0, 'block'), (t_plane, 'whoosh'), (t_plane + .4, 'rumble')]


def nutgiao(i, a, b, t0, tag='', kicker='HẠ TẦNG', title='Nút giao', source=''):
    """nút giao khác mức: 2 tuyến vuông góc, cầu vượt nâng trên trụ, nhánh rẽ cong tự vẽ, xe chạy; tag = tên nút (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,24%,33%)') + _qroadx(I, 0, 10, 5, 1.1, 'r1')
    s += ''.join(f'<path d="M{_pt([I(x, 5, 0), I(x, 5, .9)])}" stroke="#9aa0a8" stroke-width="10"/>' for x in (3.6, 6.4))
    s += f'<g class="ov"><polygon points="{_P4(I, 4.45, 0, 5.55, 10, .9)}" fill="#3a3d43"/><polygon points="{_pt([I(5.55, 0, .9), I(5.55, 10, .9), I(5.55, 10, .7), I(5.55, 0, .7)])}" fill="#22252a"/>'
    s += f'<path d="M{_pt([I(5, 0, .92), I(5, 10, .92)])}" stroke="#e8e2c8" stroke-width="2" stroke-dasharray="10 9"/></g>'
    ramps = []
    for k, (cx, cy, a0) in enumerate([(3.4, 3.4, 0), (6.6, 3.4, .5), (6.6, 6.6, 1), (3.4, 6.6, 1.5)]):
        P = [I(cx + 1.6 * math.cos(math.pi * (a0 + q / 20 * 1.5)), cy + 1.6 * math.sin(math.pi * (a0 + q / 20 * 1.5)), .45) for q in range(21)]
        L = sum(math.dist(P[q], P[q + 1]) for q in range(20)); ramps.append(L)
        s += f'<path class="rp{k}" d="M{_pt(P)}" fill="none" stroke="#3a3d43" stroke-width="12" stroke-linecap="round"/>'
    cars = [(_car(I, 1.0, 4.65, True, 'hsl(356,70%,52%)', 'c0')), (_car(I, 8.4, 5.1, True, 'hsl(205,70%,55%)', 'c1')), (_car(I, 4.85, 1.2, False, GOLD, 'c2'))]
    s += ''.join(cars)
    if tag: s += _qpill(360, Y0 - 20, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'r1', a + .2), _qgrow(i, 'ov', t0, .7)]
    j += [_qdraw(i, f'rp{k}', t0 + .3 + k * .15, ramps[k], .7) for k in range(4)]
    d1 = I(9, 4.65); d0 = I(1, 4.65); dx, dy = d1[0] - d0[0], d1[1] - d0[1]
    j += [_qfade(i, 'c0', t0 + .8) + T(f'#{i} .c0', t0 + .8, x=dx * .8, y=dy * .8, duration=2.4, ease='none'),
          _qfade(i, 'c1', t0 + .8) + T(f'#{i} .c1', t0 + .8, x=-dx * .7, y=-dy * .7, duration=2.4, ease='none'),
          _qfade(i, 'c2', t0 + 1) + T(f'#{i} .c2', t0 + 1, x=(I(4.85, 8.5)[0] - I(4.85, 1.2)[0]), y=(I(4.85, 8.5)[1] - I(4.85, 1.2)[1]), duration=2.2, ease='none')]
    if tag: j.append(_rv(f'#{i} .tg', t0 + 1, 10))
    return _out(i, a, b, 'r_nutgiao', s, j), j, [(t0, 'block'), (t0 + .3, 'whoosh')]


def dien(i, a, b, t0, value='', unit='MW', kind='nangluong', kicker='NĂNG LƯỢNG', title='', source=''):
    """trang trại điện: hàng tấm pin mặt trời lấp lánh + tua-bin gió quay + đường dây; value = công suất (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title, _lg(f'{i}pv', 'hsl(215,60%,40%)', 'hsl(220,65%,22%)', 1, 1)) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(80,25%,36%)')
    for r in range(4):
        for c in range(3):
            x, y = .8 + c * 2.1, 4.6 + r * 1.3
            s += f'<g class="pv{r}"><polygon points="{_pt([I(x, y, .5), I(x + 1.8, y, .5), I(x + 1.8, y + .8, .15), I(x, y + .8, .15)])}" fill="url(#{i}pv)" stroke="hsl(210,30%,70%)" stroke-width="1"/>' \
                 f'<path d="M{_pt([I(x + .6, y, .5), I(x + .6, y + .8, .15)])} M{_pt([I(x + 1.2, y, .5), I(x + 1.2, y + .8, .15)])}" stroke="hsl(210,30%,70%)" stroke-width=".8"/></g>'
    s += f'<rect class="gl_" x="60" y="{Y0}" width="80" height="400" fill="#fff" opacity="0" transform="skewX(-25)"/>'
    for k, (x, y) in enumerate([(6.2, .9), (8.0, 1.8), (9.2, 3.6)]):
        bx, by = I(x, y); hh = (95 if value else 150) * sc / 30
        s += (f'<g class="wt{k}"><path d="M{bx - 3:.0f} {by:.0f} L{bx - 1.5:.0f} {by - hh:.0f} H{bx + 1.5:.0f} L{bx + 3:.0f} {by:.0f}Z" fill="#eef1f4"/>'
              f'<g class="bl{k}">' + ''.join(f'<path d="M{bx:.0f} {by - hh:.0f} l{50 * math.cos(math.radians(u)) * sc / 30:.0f} {50 * math.sin(math.radians(u)) * sc / 30:.0f}" stroke="#f6f8fa" stroke-width="5" stroke-linecap="round"/>' for u in (-90, 30, 150))
              + f'</g><circle cx="{bx:.0f}" cy="{by - hh:.0f}" r="5" fill="#cfd5db"/></g>')
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_rv(f'#{i} .pv{r}', t0 + r * .1, 12, .5) for r in range(4)]
    for k, (x, y) in enumerate([(6.2, .9), (8.0, 1.8), (9.2, 3.6)]):
        bx, by = I(x, y); hh = (95 if value else 150) * sc / 30
        j += [_qgrow(i, f'wt{k}', t0 + .2 + k * .15, .7), T(f'#{i} .bl{k}', t0 + .5, rotation=720, svgOrigin=f'{bx:.0f} {by - hh:.0f}', duration=max(1, b - t0 - .5), ease='none')]
    j += [S(f'#{i} .gl_', 0, opacity=0, x=0) + T(f'#{i} .gl_', t0 + .8, opacity=.12, x=520, duration=1.2, ease='power1.inOut')] + jn
    return _out(i, a, b, 'r_dien', s, j), j, [(t0, 'air'), (t0 + .8, 'shimmer')] + ([(t0 + .5, 'count')] if value else [])


def cangbien(i, a, b, t0, t_ship=None, tag='', kicker='HẠ TẦNG', title='Cảng biển', source=''):
    """cảng biển: mặt nước, cầu cảng bê tông, cẩu giàn đỏ trắng, tàu hàng chở container cập bến ở t_ship; tag = tên cảng (chỉ khi lời có)"""
    t_ship = t0 + .4 if t_ship is None else t_ship; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + f'<polygon points="{_P4(I, 0, 0, 10, 10)}" fill="url(#{i}wt)"/>'
    s += ''.join(f'<path class="wv{k}" d="M{_pt([I(1 + k * 1.6, 7 + (k % 3) * .7, 0), I(1.6 + k * 1.6, 7 + (k % 3) * .7, 0)])}" stroke="#fff" stroke-opacity=".4" stroke-width="2"/>' for k in range(5))
    s += _box(I, 0, 0, 10, 3.4, .5, 'hsl(30,6%,62%)', 'hsl(30,6%,46%)', 'hsl(30,6%,36%)', 'dk')
    for k, x in enumerate((2.5, 6.0)):
        s += (f'<g class="cr{k}"><path d="M{_pt([I(x, 2.6, .5), I(x, 2.6, 3.6)])} M{_pt([I(x + .9, 2.6, .5), I(x + .9, 2.6, 3.6)])}" stroke="{RED}" stroke-width="6"/>'
              f'<path d="M{_pt([I(x - .2, 1.2, 3.6), I(x - .2, 5.8, 3.6)])}" stroke="#f0f0f0" stroke-width="8"/><path d="M{_pt([I(x + 1.1, 1.2, 3.6), I(x + 1.1, 5.8, 3.6)])}" stroke="#f0f0f0" stroke-width="8"/></g>')
    sh = _box(I, 1.2, 4.2, 7.4, 1.6, .7, 'hsl(210,20%,30%)', 'hsl(0,0%,18%)', 'hsl(0,0%,12%)')
    random.seed(9); CC_ = ['hsl(356,62%,48%)', 'hsl(205,58%,42%)', 'hsl(145,45%,36%)', 'hsl(36,85%,50%)']
    for c in range(8):
        for r in range(2): sh += _box(I, 1.6 + c * .8, 4.4 + r * .65, .75, .6, .45, CC_[(c + r) % 4], CC_[(c + r) % 4], CC_[(c + r) % 4]).replace('<g class="">', f'<g transform="translate(0 {-.7 * sc:.0f})">')
    s += f'<g class="sh">{sh}</g>'
    if tag: tx, ty = I(5, 1.5, .5); s += _qpill(tx, ty - 6, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .dk', a + .05, 30, .7)] + [_qgrow(i, f'cr{k}', t0 + .1 + k * .15, .7) for k in range(2)]
    j += [S(f'#{i} .sh', 0, x=260, y=150, opacity=0) + T(f'#{i} .sh', t_ship, x=0, y=0, opacity=1, duration=1.6, ease='power2.out')]
    j += [S(f'#{i} .wv{k}', 0, opacity=.1) + T(f'#{i} .wv{k}', a + .2 * k, opacity=.6, duration=.9, yoyo=True, repeat=5) for k in range(5)] + ([_rv(f'#{i} .tg', t0 + .5, 10)] if tag else [])
    return _out(i, a, b, 'r_cangbien', s, j), j, [(t0, 'metal'), (t_ship, 'rumble')]


# ---------------------------------------------------------------- THỊ TRƯỜNG +4
def giaodich(i, a, b, t0, value='', unit='giao dịch', kicker='THỊ TRƯỜNG', title='', source=''):
    """giao dịch: 2 bàn tay trao chìa khoá nhà vàng trên nền hợp đồng, dấu tick; value = số giao dịch (chỉ khi lời có)"""
    Y = 330 if not value else 400; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .4)
    s = _qhead(i, kicker, title, _lg(f'{i}sl', 'hsl(215,30%,30%)', 'hsl(215,35%,18%)', 1, 1) + _lg(f'{i}sr', 'hsl(28,30%,32%)', 'hsl(24,30%,18%)', 1, 1)
                + _lg(f'{i}ky', 'hsl(50,100%,78%)', 'hsl(38,85%,42%)', 1, 1)) + sn
    s += _paper(i, 170, Y - 10, 380, 230, None, 'pp', 4, ''.join(f'<rect x="{200}" y="{Y + 20 + q * 26}" width="{300 - (q % 3) * 50}" height="6" rx="3" fill="#bbb"/>' for q in range(7)))
    s += (f'<g class="hl"><path d="M20 {Y + 140} C120 {Y + 120} 200 {Y + 110} 300 {Y + 95} L320 {Y + 125} C230 {Y + 150} 140 {Y + 170} 20 {Y + 200}Z" fill="url(#{i}sl)"/>'
          f'<path d="M290 {Y + 92} c18 -6 34 -4 40 6 c4 10 -6 22 -20 26 l-10 4Z" fill="hsl(28,50%,68%)"/></g>'
          f'<g class="hr"><path d="M700 {Y + 140} C600 {Y + 120} 520 {Y + 110} 420 {Y + 95} L400 {Y + 125} C490 {Y + 150} 580 {Y + 170} 700 {Y + 200}Z" fill="url(#{i}sr)"/>'
          f'<path d="M430 {Y + 92} c-18 -6 -34 -4 -40 6 c-4 10 6 22 20 26 l10 4Z" fill="hsl(28,50%,62%)"/></g>')
    kx, ky = 360, Y + 90
    s += (f'<g class="ky"><circle cx="{kx - 30}" cy="{ky}" r="24" fill="none" stroke="url(#{i}ky)" stroke-width="10"/><rect x="{kx - 8}" y="{ky - 6}" width="90" height="12" rx="4" fill="url(#{i}ky)"/>'
          f'<rect x="{kx + 54}" y="{ky + 4}" width="10" height="18" fill="url(#{i}ky)"/><rect x="{kx + 70}" y="{ky + 4}" width="10" height="14" fill="url(#{i}ky)"/>'
          f'<path d="M{kx - 42} {ky - 10} l10 -14 l10 14 v14 h-20Z" fill="hsl(44,80%,50%)"/></g>')
    s += f'<g class="ok"><circle cx="560" cy="{Y - 20}" r="30" fill="{GRN}"/><path d="M546 {Y - 20} l10 10 l18 -20" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/></g>' + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pp', a + .05, 30, .6),
         S(f'#{i} .hl', 0, x=-260) + T(f'#{i} .hl', t0, x=0, duration=.8, ease='expo.out'), S(f'#{i} .hr', 0, x=260) + T(f'#{i} .hr', t0, x=0, duration=.8, ease='expo.out'),
         _qpop(i, 'ky', t0 + .5, .5, '50% 50%'), _qpop(i, 'ok', t0 + 1.0, .4, '50% 50%')] + jn
    return _out(i, a, b, 'r_giaodich', s, j), j, [(t0, 'swish'), (t0 + .5, 'metal'), (t0 + 1.0, 'ding')] + ([(t0 + .4, 'count')] if value else [])


def giadat(i, a, b, rows, unit='triệu/m²', kicker='GIÁ ĐẤT', title='', source=''):
    """bảng giá theo khu: các lô đất 3D với cờ giá cắm lên lần lượt; rows=[('KHU A', '25', t)] ≤4 (chỉ giá có trong lời)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 10, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,32%)') + _qroadx(I, 0, 10, 5, .5, 'r1') + _qroady(I, 0, 10, 5, .5, 'r2')
    SL = [(1.2, 1.2), (6.2, 1.2), (1.2, 6.2), (6.2, 6.2)]; j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)]; cues = []
    for k, (lab, price, t) in enumerate(list(rows)[:4]):
        x, y = SL[k]
        s += f'<g class="lt{k}"><polygon points="{_P4(I, x, y, x + 2.6, y + 2.6, .03)}" fill="hsl(36,40%,58%)"/><polygon points="{_P4(I, x, y, x + 2.6, y + 2.6, .03)}" fill="none" stroke="#fff" stroke-dasharray="6 5" stroke-width="2"/></g>'
        px, py = I(x + 1.3, y + 1.3, .03); txt = f'{price} {unit}'; w = _w(txt, 18) + 26
        s += (f'<g class="fl{k}"><path d="M{px:.0f} {py:.0f} V{py - 90:.0f}" stroke="#ddd" stroke-width="3"/><rect x="{px:.0f}" y="{py - 92:.0f}" width="{w:.0f}" height="44" rx="6" fill="{GOLD}" filter="url(#{i}sh)"/>'
              + _t(px + w / 2, py - 75, lab, 12, '#3a2a08', 'middle', w=900, ls=1) + _t(px + w / 2, py - 56, txt, 18, '#111', 'middle', w=900) + '</g>')
        j += [_qfade(i, f'lt{k}', a + .2 + k * .08), _qgrow(i, f'fl{k}', t, .6, 'back.out(1.8)')]; cues.append((t, 'pop'))
    s += _note(source)
    return _out(i, a, b, 'r_giadat', s, j), j, cues


def tonkho(i, a, b, t0, value='', unit='căn', kicker='THỊ TRƯỜNG', title='Hàng tồn kho', source=''):
    """tồn kho BĐS: các khối căn hộ mô hình xếp chồng trên pallet trong kho, nhãn TỒN KHO; value = số lượng (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(30,8%,36%)')
    n = 0
    for r in range(3):
        for c in range(3):
            x, y = 1 + c * 2.9, 1 + r * 2.9
            s += f'<g class="pk{n}">' + _box(I, x, y, 2.2, 2.2, .2, 'hsl(32,40%,55%)', 'hsl(30,40%,40%)', 'hsl(28,40%,30%)')
            for z in range(1 + (n % 3)):
                s += _house(I, x + .3, y + .3, 1.6, 1.6, .9, 20 + 15 * ((n + z) % 4), '').replace('<g class="">', f'<g transform="translate(0 {-(.2 + z * 1.0) * sc:.0f})">')
            s += '</g>'; n += 1
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_rv(f'#{i} .pk{k}', t0 + k * .08, 40, .5) for k in range(9)] + jn
    return _out(i, a, b, 'r_tonkho', s, j), j, [(t0, 'block')] + ([(t0 + .5, 'count')] if value else [])


def kenhdautu(i, a, b, items, kicker='KÊNH ĐẦU TƯ', title='', source=''):
    """so sánh kênh đầu tư: bục 3D cao thấp theo mức (vàng, gửi tiết kiệm, chứng khoán, BĐS…) có biểu tượng; items=[('BĐS', '12%', t)] ≤4 (chỉ số có trong lời)"""
    n = min(4, len(items)); Y = 610; W = 520 / n
    s = _qhead(i, kicker, title, _lg(f'{i}pd', 'hsl(44,85%,62%)', 'hsl(36,80%,40%)', 1, 0) + _lg(f'{i}ps', 'hsl(36,70%,38%)', 'hsl(30,70%,22%)', 1, 0))
    vals = []
    for it in items[:n]:
        try: vals.append(float(str(it[1]).replace('%', '').replace(',', '.')))
        except Exception: vals.append(1)
    mx = max(vals) or 1; j = _vis(i, a, b) + _headj(i, a, title); cues = []
    s += f'<ellipse cx="360" cy="{Y + 10}" rx="300" ry="24" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
    for k, (lab, v, t) in enumerate(items[:n]):
        x = 100 + k * W + W / 2; h = 60 + 240 * vals[k] / mx
        s += (f'<g class="pd{k}"><rect x="{x - W * .36:.0f}" y="{Y - h:.0f}" width="{W * .72:.0f}" height="{h:.0f}" fill="url(#{i}pd)"/><polygon points="{_pt([(x + W * .36, Y - h), (x + W * .46, Y - h - 10), (x + W * .46, Y - 10), (x + W * .36, Y)])}" fill="url(#{i}ps)"/>'
              f'<polygon points="{_pt([(x - W * .36, Y - h), (x - W * .26, Y - h - 10), (x + W * .46, Y - h - 10), (x + W * .36, Y - h)])}" fill="hsl(48,95%,78%)"/>'
              + _t(x + W * .05, Y - h - 26, v, 30, FG, 'middle', w=800) + _t(x, Y + 40, lab, 17, MUT, 'middle', w=800, ls=1) + '</g>')
        j.append(_qgrow(i, f'pd{k}', t, .8, 'expo.out')); cues.append((t, 'pop'))
    s += _note(source)
    return _out(i, a, b, 'r_kenhdautu', s, j), j, cues


# ---------------------------------------------------------------- NHÀ Ở & DỰ ÁN +8
def canho(i, a, b, t0, area='', rooms=(), kicker='CĂN HỘ', title='', source=''):
    """mặt bằng căn hộ 3D cắt nóc: tường trắng, sàn gỗ, phòng khách–ngủ–bếp có nội thất; area='68 m²', rooms=[('2PN', t)] nhãn (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 10, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,8%,24%)')
    s += f'<polygon class="fl" points="{_P4(I, .8, .8, 9.2, 9.2, .05)}" fill="url(#{i}wd)"/>' + ''.join(f'<path d="M{_pt([I(.8 + q * .6, .8, .06), I(.8 + q * .6, 9.2, .06)])}" stroke="hsl(28,40%,30%)" stroke-opacity=".35"/>' for q in range(1, 14))
    W = lambda x0, y0, x1, y1: _box(I, x0, y0, max(.12, x1 - x0), max(.12, y1 - y0), 1.1, '#f4f2ee', '#d9d5cd', '#b9b3a8')
    walls = W(.8, .8, 9.2, .92) + W(.8, .8, .92, 9.2) + W(5, .8, 5.12, 5.5) + W(.8, 5.4, 5.12, 5.52) + W(5, 6.6, 5.12, 9.2)
    s += f'<g class="wl">{walls}</g>'
    fur = (_box(I, 1.4, 1.4, 2.4, 1.8, .45, 'hsl(210,25%,85%)', 'hsl(210,20%,70%)', 'hsl(210,20%,55%)') + _box(I, 1.4, 1.4, 2.4, .3, .8, 'hsl(28,30%,40%)', 'hsl(28,30%,30%)', 'hsl(28,30%,22%)')
           + _box(I, 6, 1.6, 2.6, 1.2, .5, 'hsl(28,25%,72%)', 'hsl(28,25%,55%)', 'hsl(28,25%,42%)') + _box(I, 6.3, 3.4, 1.4, 1.4, .5, 'hsl(200,10%,40%)', 'hsl(200,10%,30%)', 'hsl(200,10%,22%)')
           + _box(I, 1.4, 6.2, .8, 2.6, .9, '#e8e8e8', '#c9c9c9', '#a8a8a8') + _box(I, 6, 7.3, 2.6, 1.3, .55, 'hsl(28,35%,48%)', 'hsl(28,35%,36%)', 'hsl(28,35%,26%)') + _tree(I, i, 8.6, 5.6, .8, ''))
    s += f'<g class="fu">{fur}</g>'
    if area: s += _qpill(360, Y0 - 16, area, GOLD, '#111', 'ar_', 22)
    for k, (lab, t) in enumerate(list(rooms)[:3]):
        x, y = [(2.6, 3.6), (7, 3), (3, 7.6)][k]; px, py = I(x, y, 1.3); s += _qpill(px, py, lab, 'rgba(14,13,12,.75)', FG, f'r{k}', 16)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'fl', a + .2), _qgrow(i, 'wl', t0, .7), _rv(f'#{i} .fu', t0 + .5, 20, .6)]
    j += ([_rv(f'#{i} .ar_', t0 + .3, 10)] if area else []) + [_qpop(i, f'r{k}', t, .4, '50% 50%') for k, (_, t) in enumerate(list(rooms)[:3])]
    return _out(i, a, b, 'r_canho', s, j), j, [(t0, 'block'), (t0 + .5, 'pop')]


def nhapho(i, a, b, t0, floors=4, n=5, tag='', kicker='NHÀ PHỐ', title='', source=''):
    """dãy nhà phố / shophouse liền kề: mặt tiền kính tầng trệt, ban công tầng trên, vỉa hè cây xanh, mọc lần lượt; tag = tên dãy (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 20, sc); n = max(3, min(6, n)); fh = .75
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,8%,34%)') + _qroadx(I, 0, 10, 8.6, 1.4, 'rd')
    s += f'<polygon points="{_P4(I, 0, 7.2, 10, 7.9, .04)}" fill="hsl(30,10%,62%)"/>'
    w = 8.4 / n
    for k in range(n):
        x = .8 + k * w; h = fh * floors + (.3 if k % 2 else 0); hue = (30, 205, 40, 18, 160, 0)[k % 6]
        win = ''.join(f'<polygon points="{_pt([I(x + .15, 7.0, .7 + f * fh), I(x + w - .15, 7.0, .7 + f * fh), I(x + w - .15, 7.0, 1.2 + f * fh), I(x + .15, 7.0, 1.2 + f * fh)])}" fill="hsl(205,35%,30%)"/>'
                      f'<polygon points="{_pt([I(x + .1, 7.12, .62 + f * fh), I(x + w - .1, 7.12, .62 + f * fh), I(x + w - .1, 7.12, .7 + f * fh), I(x + .1, 7.12, .7 + f * fh)])}" fill="#fff" fill-opacity=".75"/>' for f in range(floors - 1))
        shop = f'<polygon points="{_pt([I(x + .1, 7.0, .05), I(x + w - .1, 7.0, .05), I(x + w - .1, 7.0, .6), I(x + .1, 7.0, .6)])}" fill="hsl(45,90%,72%)" fill-opacity=".85"/>'
        s += f'<g class="h{k}">' + _box(I, x, 5, w - .05, 2, h, f'hsl({hue},20%,82%)', f'hsl({hue},22%,74%)', f'hsl({hue},20%,56%)', '', shop + win) + '</g>'
    s += ''.join(_tree(I, i, .9 + k * 2.1, 7.6, .8, f't{k}') for k in range(5))
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'rd', a + .2)] + [_qgrow(i, f'h{k}', t0 + k * .12, .6, 'back.out(1.4)') for k in range(n)]
    j += [_qpop(i, f't{k}', t0 + .8 + k * .08, .4) for k in range(5)] + ([_rv(f'#{i} .tg', t0 + 1, 10)] if tag else [])
    return _out(i, a, b, 'r_nhapho', s, j), j, [(t0, 'block'), (t0 + .8, 'pop')]


def bietthu(i, a, b, t0, tag='', kicker='BIỆT THỰ', title='', source=''):
    """biệt thự sân vườn: nhà 2 tầng mái bằng ốp gỗ, kính lớn, hồ bơi xanh lấp lánh, bãi cỏ, hàng rào cây; tag = tên dự án (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 10, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(105,40%,38%)')
    s += f'<g class="pl"><polygon points="{_P4(I, 5.6, 5.4, 9, 8.6, .02)}" fill="hsl(36,20%,80%)"/><polygon points="{_P4(I, 6, 5.8, 8.6, 8.2, .03)}" fill="url(#{i}wt)"/>' \
         + ''.join(f'<path class="sp{k}" d="M{_pt([I(6.5 + k * .6, 6.6 + k * .4, .04), I(7 + k * .6, 6.6 + k * .4, .04)])}" stroke="#fff" stroke-width="2" opacity=".6"/>' for k in range(3)) + '</g>'
    house = (_box(I, 1.2, 1.2, 4, 3.6, 1.6, '#f5f3ef', '#dedad2', '#bdb7ab', '', _winL(I, 1.2, 1.2, 4, 3.6, 1.6, 3, 1, 'hsl(200,35%,40%)', lit={(0, 1)}))
             + _box(I, 1.6, 1.4, 3.4, 2.8, 1.3, 'hsl(28,35%,48%)', 'hsl(28,35%,40%)', 'hsl(28,35%,30%)', '', _winR(I, 1.6, 1.4, 3.4, 2.8, 1.3, 3, 1, 'hsl(200,35%,34%)')).replace('<g class="">', f'<g transform="translate(0 {-1.6 * sc:.0f})">', 1)
             + f'<polygon points="{_P4(I, 1.4, 1.2, 5.4, 5.0, 2.95)}" fill="hsl(30,8%,30%)"/>')
    s += f'<g class="hs">{house}</g>' + ''.join(_tree(I, i, x, y, 1.0, f't{k}') for k, (x, y) in enumerate([(.6, 6), (.6, 8.2), (2.6, 9.2), (4.6, 9.3), (9.2, 1.2), (9.3, 3.4)]))
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'pl', t0), _qgrow(i, 'hs', t0 + .2, .8)] + [_qpop(i, f't{k}', t0 + .6 + k * .07, .45) for k in range(6)]
    j += [S(f'#{i} .sp{k}', 0, opacity=.1) + T(f'#{i} .sp{k}', t0 + .3 * k, opacity=.8, duration=.6, yoyo=True, repeat=6) for k in range(3)] + ([_rv(f'#{i} .tg', t0 + 1, 10)] if tag else [])
    return _out(i, a, b, 'r_bietthu', s, j), j, [(t0, 'air'), (t0 + .2, 'block')]


def datnen(i, a, b, t0, lots=12, tag='', area='', kicker='ĐẤT NỀN', title='', source=''):
    """khu đất nền phân lô: các lô có cọc mốc và số lô, đường nội khu nhựa, 1 lô được tô vàng; area='100 m²' (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 10, sc); n = max(6, min(16, lots)); cols = n // 2
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,25%,32%)') + _qroadx(I, 0, 10, 5, .9, 'rd')
    w = 9 / cols; k = 0
    for row, y in enumerate((1.2, 5.7)):
        for c in range(cols):
            x = .5 + c * w; hi = (k == cols + 1)
            s += (f'<g class="l{k}"><polygon points="{_P4(I, x + .06, y, x + w - .06, y + 3.1, .03)}" fill="{"hsl(46,85%,60%)" if hi else "hsl(34,40%,56%)"}"/>'
                  f'<polygon points="{_P4(I, x + .06, y, x + w - .06, y + 3.1, .03)}" fill="none" stroke="#fff" stroke-width="1.5" stroke-dasharray="5 4"/>'
                  + _t(*I(x + w / 2, y + 1.55, .05), f'{k + 1:02d}', 13, '#3a2a10', 'middle', w=900) + '</g>')
            k += 1
    if area:
        x = .5 + 1 * w; px, py = I(x + w / 2, 5.7 + 1.55, .05); s += _qpill(px, py - 46, area, GOLD, '#111', 'ar_', 18)
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'rd', a + .2)] + [_qpop(i, f'l{q}', t0 + q * .05, .35, '50% 50%') for q in range(k)]
    j += ([_rv(f'#{i} .ar_', t0 + .9, 10)] if area else []) + ([_rv(f'#{i} .tg', t0 + 1, 10)] if tag else [])
    return _out(i, a, b, 'r_datnen', s, j), j, [(t0, 'scan'), (t0 + .9, 'pop')]


def bangiao(i, a, b, t0, t_key=None, kicker='BÀN GIAO', title='', source=''):
    """bàn giao nhà: ngôi nhà hoàn thiện, chiếc chìa khoá vàng lớn bay vào ổ cửa và xoay, cửa sáng đèn, pháo giấy vàng"""
    t_key = t0 + .8 if t_key is None else t_key; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 40, 38)
    s = _qhead(i, kicker, title, _lg(f'{i}ky', 'hsl(50,100%,80%)', 'hsl(38,85%,42%)', 1, 1)) + _ground(I, i, 0, 0, 8, 8, 'hsl(105,35%,36%)')
    s += '<g class="hs">' + _house(I, 1.6, 1.6, 4.6, 4.2, 2.6, 18, '') + '</g>'
    dx, dy = I(1.6 + 4.6 * .48, 5.8, .5)
    s += f'<circle class="lt" cx="{dx:.0f}" cy="{dy:.0f}" r="40" fill="hsl(45,100%,70%)" opacity="0" filter="url(#{i}sf)"/>'
    s += (f'<g class="ky"><circle cx="0" cy="0" r="22" fill="none" stroke="url(#{i}ky)" stroke-width="9"/><rect x="18" y="-6" width="80" height="12" rx="4" fill="url(#{i}ky)"/>'
          f'<rect x="72" y="4" width="9" height="16" fill="url(#{i}ky)"/><rect x="86" y="4" width="9" height="11" fill="url(#{i}ky)"/></g>')
    random.seed(5)
    s += ''.join(f'<rect class="cf{k}" x="{dx:.0f}" y="{dy:.0f}" width="8" height="12" fill="hsl({random.choice((44, 48, 36, 0))},90%,{random.choice((60, 70))}%)"/>' for k in range(16)) + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'hs', t0, .8),
         S(f'#{i} .ky', 0, x=dx + 220, y=dy - 200, rotation=-40, opacity=0) + T(f'#{i} .ky', t_key - .5, x=dx - 100, y=dy, rotation=0, opacity=1, duration=.6, ease='power3.out')
         + T(f'#{i} .ky', t_key + .15, rotation=90, svgOrigin=f'{dx:.0f} {dy:.0f}', duration=.35, ease='back.out(2)'),
         T(f'#{i} .lt', t_key + .45, opacity=.9, duration=.4)]
    j += [S(f'#{i} .cf{k}', 0, opacity=0) + T(f'#{i} .cf{k}', t_key + .5, opacity=1, x=random.uniform(-220, 220), y=random.uniform(-260, -60), rotation=random.uniform(-360, 360), duration=1.2, ease='power2.out')
          + T(f'#{i} .cf{k}', t_key + 1.7, opacity=0, duration=.5) for k in range(16)]
    return _out(i, a, b, 'r_bangiao', s, j), j, [(t0, 'block'), (t_key - .5, 'swish'), (t_key + .15, 'metal'), (t_key + .5, 'shimmer')]


def xaydung(i, a, b, t0, pct='', floors=10, kicker='TIẾN ĐỘ', title='', source=''):
    """công trường: toà nhà xây dần từng sàn (khung bê tông + kính), cẩu tháp quay, lưới an toàn; pct = % hoàn thành (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, pct); I = _iso(360, Y0 + 10, sc); sn, jn = _qnum(i, pct, '%' if pct else '', ny, t0 + .3)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(32,20%,38%)')
    n = max(4, min(14, floors)); fh = 6.0 / n; done = n if not pct else max(1, round(n * float(str(pct).replace(',', '.')) / 100))
    for f in range(n):
        fin = f < done
        s += f'<g class="f{f}">' + _box(I, 3, 3, 3.4, 3.4, fh * .9, 'hsl(30,6%,72%)', (f'url(#{i}gw)' if fin else 'hsl(30,6%,52%)'), ('hsl(205,25%,46%)' if fin else 'hsl(30,6%,40%)')).replace('<g class="">', f'<g transform="translate(0 {-f * fh * sc:.0f})">') + '</g>'
    cx, cy = I(7.6, 3.2)
    s += (f'<g class="cr"><path d="M{cx:.0f} {cy:.0f} V{cy - 9.2 * sc:.0f}" stroke="{GOLD}" stroke-width="7"/><g class="jb"><path d="M{cx - 150:.0f} {cy - 9 * sc:.0f} H{cx + 60:.0f}" stroke="{GOLD}" stroke-width="6"/>'
          f'<path d="M{cx - 120:.0f} {cy - 9 * sc + 3:.0f} V{cy - 6 * sc:.0f}" stroke="#ccc" stroke-width="1.5"/><rect x="{cx - 130:.0f}" y="{cy - 6 * sc:.0f}" width="20" height="14" fill="hsl(205,50%,45%)"/></g></g>')
    s += _person(*I(1.5, 8), .8, 'hsl(28,90%,52%)', True, 'p1') + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'cr', a + .2, .7)]
    j += [S(f'#{i} .f{f}', 0, opacity=0, y=-20) + T(f'#{i} .f{f}', t0 + f * .09, opacity=1, y=0, duration=.3, ease='power2.out') for f in range(n)]
    j += [T(f'#{i} .jb', t0, x=40, duration=1.6, yoyo=True, repeat=1, ease='sine.inOut'), _qpop(i, 'p1', t0 + .4)] + jn
    return _out(i, a, b, 'r_xaydung', s, j), j, [(t0, 'metal'), (t0 + .5, 'block')] + ([(t0 + .3, 'count')] if pct else [])


def vaymua(i, a, b, t0, ltv='', years='', kicker='VAY MUA NHÀ', title='', source=''):
    """vay mua nhà: ngân hàng cột đá bên trái, đồng xu vàng chạy theo cung sang ngôi nhà bên phải; ltv='70%' tỷ lệ cho vay, years='25 năm' (chỉ khi lời có)"""
    Y = 470 if not title else 500
    s = _qhead(i, kicker, title, _lg(f'{i}cn', 'hsl(48,95%,72%)', 'hsl(38,85%,40%)', 1, 1))
    s += (f'<g class="bk"><polygon points="70,{Y - 120} 200,{Y - 175} 330,{Y - 120}" fill="hsl(40,10%,78%)"/><rect x="80" y="{Y - 120}" width="240" height="14" fill="hsl(40,10%,70%)"/>'
          + ''.join(f'<rect x="{96 + q * 52}" y="{Y - 104}" width="22" height="96" fill="hsl(40,10%,{84 - q % 2 * 4}%)"/>' for q in range(5))
          + f'<rect x="70" y="{Y - 8}" width="260" height="18" fill="hsl(40,10%,66%)"/><ellipse cx="200" cy="{Y + 18}" rx="150" ry="14" fill="#000" opacity=".4" filter="url(#{i}sf)"/></g>')
    I = _iso(540, Y - 70, 34); s += '<g class="hs">' + _house(I, 0, 0, 2.6, 2.2, 1.8, 18, '') + '</g>'
    P = [(200 + (540 - 200) * q / 20, Y - 190 - 140 * math.sin(math.pi * q / 20)) for q in range(21)]
    s += f'<path class="arc" d="M{_pt(P)}" fill="none" stroke="hsl(44,90%,60%)" stroke-width="2" stroke-dasharray="6 8" opacity=".6"/>'
    s += ''.join(f'<g class="cn{k}"><circle cx="200" cy="{Y - 190}" r="16" fill="url(#{i}cn)" stroke="hsl(40,80%,38%)" stroke-width="2"/></g>' for k in range(5))
    if ltv: s += f'<g class="lv">' + _t(370, Y + 90, ltv, 64, GOLD, 'middle', w=800) + _t(370, Y + 120, 'CHO VAY', 16, MUT, 'middle', w=800, ls=3) + '</g>'
    if years: s += _qpill(560, Y + 70, years, 'rgba(255,255,255,.08)', FG, 'yr', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bk', a + .05, 30, .7), _qgrow(i, 'hs', a + .2, .7), _qfade(i, 'arc', t0)]
    for k in range(5):
        j.append(S(f'#{i} .cn{k}', 0, opacity=0) + T(f'#{i} .cn{k}', t0 + k * .22, opacity=1, duration=.1)
                 + f"tl.to('#{i} .cn{k}',{{keyframes:[{','.join('{x:%d,y:%d,duration:.15}' % (x - 200, y - (Y - 190)) for x, y in P[4::3])}],ease:'none'}},{t0 + k * .22:.2f});"
                 + T(f'#{i} .cn{k}', t0 + k * .22 + .9, opacity=0, duration=.15))
    j += ([_rv(f'#{i} .lv', t0 + .4, 14)] if ltv else []) + ([_rv(f'#{i} .yr', t0 + .7, 10)] if years else [])
    return _out(i, a, b, 'r_vaymua', s, j), j, [(t0 + k * .22, 'tick') for k in range(5)] + ([(t0 + .4, 'count')] if ltv else [])


def thanhtoan(i, a, b, steps, kicker='TIẾN ĐỘ THANH TOÁN', title='', source=''):
    """lịch thanh toán theo đợt: các khối vàng xếp bậc thang, mỗi đợt % nổi lên; steps=[('ĐỢT 1', '30%', t)] ≤5 (chỉ số có trong lời)"""
    n = min(5, len(steps)); Y = 600; W = 520 / n
    s = _qhead(i, kicker, title, _lg(f'{i}bt', 'hsl(48,95%,70%)', 'hsl(38,85%,44%)', 1, 0) + _lg(f'{i}bs', 'hsl(36,70%,38%)', 'hsl(30,70%,22%)', 1, 0))
    s += f'<ellipse cx="360" cy="{Y + 8}" rx="300" ry="22" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
    j = _vis(i, a, b) + _headj(i, a, title); cues = []
    for k, (lab, v, t) in enumerate(steps[:n]):
        x = 100 + k * W; h = 70 + 200 * (k + 1) / n
        s += (f'<g class="st{k}"><rect x="{x + 4:.0f}" y="{Y - h:.0f}" width="{W - 16:.0f}" height="{h:.0f}" fill="url(#{i}bt)"/><polygon points="{_pt([(x + W - 12, Y - h), (x + W - 2, Y - h - 9), (x + W - 2, Y - 9), (x + W - 12, Y)])}" fill="url(#{i}bs)"/>'
              f'<polygon points="{_pt([(x + 4, Y - h), (x + 14, Y - h - 9), (x + W - 2, Y - h - 9), (x + W - 12, Y - h)])}" fill="hsl(50,100%,82%)"/>'
              + _t(x + W / 2 - 4, Y - h + 40, v, 28, '#2a1d05', 'middle', w=900) + _t(x + W / 2 - 4, Y + 34, lab, 15, MUT, 'middle', w=800, ls=1) + '</g>')
        j.append(_qgrow(i, f'st{k}', t, .6, 'back.out(1.5)')); cues.append((t, 'block'))
    s += _note(source)
    return _out(i, a, b, 'r_thanhtoan', s, j), j, cues


# ---------------------------------------------------------------- KINH TẾ +6
def ngansach(i, a, b, t0, value='', unit='tỷ đồng', kicker='NGÂN SÁCH', title='', source=''):
    """thu ngân sách: toà nhà trụ sở cột đá, két sắt mở, dòng xu vàng đổ vào chồng cao; value = số thu (chỉ khi lời có)"""
    Y = 600; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .5)
    s = _qhead(i, kicker, title, _lg(f'{i}cs', 'hsl(44,85%,58%)', 'hsl(36,80%,34%)', 1, 0) + _lg(f'{i}ct', 'hsl(50,100%,80%)', 'hsl(42,90%,55%)', 1, 1)) + sn
    s += (f'<g class="bd_"><polygon points="90,{Y - 150} 250,{Y - 210} 410,{Y - 150}" fill="hsl(40,10%,80%)"/><rect x="100" y="{Y - 150}" width="300" height="16" fill="hsl(40,10%,70%)"/>'
          + ''.join(f'<rect x="{118 + q * 58}" y="{Y - 134}" width="24" height="120" fill="hsl(40,10%,{86 - q % 2 * 4}%)"/>' for q in range(5))
          + f'<rect x="88" y="{Y - 14}" width="324" height="20" fill="hsl(40,10%,64%)"/><polygon points="250,{Y - 196} 236,{Y - 166} 264,{Y - 166}" fill="{RED}"/><polygon points="250,{Y - 192} 246,{Y - 180} 254,{Y - 180}" fill="{GOLD}"/></g>')
    for k in range(3):
        cx = 500 + k * 70; nn = 4 + k * 2
        for q in range(nn):
            y = Y - q * 11
            s += (f'<g class="c{k}_{q}"><rect x="{cx - 30}" y="{y - 11}" width="60" height="11" fill="url(#{i}cs)"/><ellipse cx="{cx}" cy="{y}" rx="30" ry="10" fill="url(#{i}cs)"/>'
                  f'<ellipse cx="{cx}" cy="{y - 11}" rx="30" ry="10" fill="url(#{i}ct)"/></g>')
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bd_', a + .05, 30, .7)]
    j += [S(f'#{i} .c{k}_{q}', 0, y=-60, opacity=0) + T(f'#{i} .c{k}_{q}', t0 + (k * 6 + q) * .05, y=0, opacity=1, duration=.3, ease='bounce.out') for k in range(3) for q in range(4 + k * 2)] + jn
    return _out(i, a, b, 'r_ngansach', s, j), j, [(t0, 'metal'), (t0 + .3, 'tick')] + ([(t0 + .5, 'count')] if value else [])


def fdi(i, a, b, t0, value='', unit='triệu USD', sources=(), kicker='VỐN FDI', title='', source=''):
    """đầu tư nước ngoài: quả địa cầu xoay với lưới kinh vĩ, các cung sáng bay về ghim vàng Đắk Lắk; sources=[('NHẬT BẢN', t)] ≤4 nhãn nguồn; value (chỉ khi lời có)"""
    Y = 480 if not value else 520; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .6); R_ = 150 if not value else 120; cx, cy = 360, Y
    s = _qhead(i, kicker, title, _rg(f'{i}gb', 'hsl(205,60%,40%)', 'hsl(215,70%,14%)', .4, .35)) + sn
    s += f'<circle cx="{cx}" cy="{cy}" r="{R_ + 20}" fill="hsl(205,80%,50%)" opacity=".12" filter="url(#{i}sf)"/><circle cx="{cx}" cy="{cy}" r="{R_}" fill="url(#{i}gb)"/>'
    s += f'<g class="gr" opacity=".35">' + ''.join(f'<ellipse cx="{cx}" cy="{cy}" rx="{R_ * abs(math.cos(math.radians(q * 30))):.0f}" ry="{R_}" fill="none" stroke="#9fd0ff" stroke-width="1"/>' for q in range(6)) \
         + ''.join(f'<ellipse cx="{cx}" cy="{cy + R_ * math.sin(math.radians(q)):.0f}" rx="{R_ * math.cos(math.radians(q)):.0f}" ry="{R_ * .12 * math.cos(math.radians(q)):.0f}" fill="none" stroke="#9fd0ff" stroke-width="1"/>' for q in (-60, -30, 0, 30, 60)) + '</g>'
    s += f'<path d="M{cx - R_ * .5:.0f} {cy - R_ * .3:.0f} q40 -30 80 -6 q20 30 60 20 q10 40 -30 60 q-50 10 -80 -20 q-40 -10 -30 -54Z" fill="hsl(120,30%,40%)" opacity=".75"/>'
    tx, ty = cx + R_ * .28, cy + R_ * .1
    s += _qpin(tx, ty, GOLD, 'pin')
    SRC = [(-1, -1), (1, -1), (-1, .4), (1, .5)]; j = _vis(i, a, b) + _headj(i, a, title) + [_qpop(i, 'gr', a + .1, .8, '50% 50%'), _qpop(i, 'pin', t0, .5)]; cues = [(t0, 'pop')]
    for k, (lab, t) in enumerate(list(sources)[:4]):
        sx, sy = cx + SRC[k][0] * (R_ + 110), cy + SRC[k][1] * (R_ + 40); sx = min(max(sx, 120), 600)
        mx, my = (sx + tx) / 2, min(sy, ty) - 80; P = [((1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx, (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * (ty - 34)) for u in [q / 20 for q in range(21)]]
        L = sum(math.dist(P[q], P[q + 1]) for q in range(20))
        s += f'<path class="ar{k}" d="M{_pt(P)}" fill="none" stroke="{GOLD}" stroke-width="3" filter="url(#{i}gl)"/>' + _qlab(sx, sy - 12, lab, FG, 16, f'lb{k}')
        j += [_rv(f'#{i} .lb{k}', t, 8, .4), _qdraw(i, f'ar{k}', t + .1, L, .8)]; cues.append((t, 'whoosh'))
    s += _note(source); j += jn
    return _out(i, a, b, 'r_fdi', s, j), j, cues + ([(t0 + .6, 'count')] if value else [])


def xuatkhau(i, a, b, t0, value='', unit='triệu USD', item='', kicker='XUẤT KHẨU', title='', source=''):
    """xuất khẩu: tàu container rẽ sóng sang phải, mũi tên vàng đi lên, bao hàng (cà phê/nông sản) xếp trên boong; item = mặt hàng (chỉ khi lời có)"""
    Y = 560; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .5)
    s = _qhead(i, kicker, title, _lg(f'{i}sea', 'hsl(205,60%,32%)', 'hsl(212,65%,14%)')) + sn
    s += f'<rect x="40" y="{Y}" width="640" height="110" rx="12" fill="url(#{i}sea)"/>' + ''.join(f'<path class="wv{k}" d="M{70 + k * 120} {Y + 30 + (k % 2) * 30} q20 -8 40 0" stroke="#fff" stroke-opacity=".35" stroke-width="2" fill="none"/>' for k in range(5))
    hull = f'<path d="M150 {Y - 10} H560 L530 {Y + 34} H180Z" fill="hsl(356,55%,40%)"/><path d="M150 {Y - 10} H560 L556 {Y} H154Z" fill="hsl(0,0%,90%)"/>'
    random.seed(3); CC_ = ['hsl(356,62%,48%)', 'hsl(205,58%,42%)', 'hsl(145,45%,36%)', 'hsl(36,85%,50%)']
    boxes = ''.join(f'<rect x="{200 + c * 40}" y="{Y - 34 - r * 24}" width="38" height="22" fill="{CC_[(c + r) % 4]}" stroke="#000" stroke-opacity=".25"/>' for c in range(8) for r in range(2 if c % 3 else 3))
    s += f'<g class="sh">{hull}{boxes}<rect x="490" y="{Y - 90}" width="44" height="80" fill="#eceef1"/><rect x="496" y="{Y - 80}" width="32" height="10" fill="hsl(205,40%,30%)"/></g>'
    s += _qarrow(120, Y - 110, 600, Y - 230, GOLD, 6, 'ar')
    if item: s += _qpill(240, Y - 170, item, 'rgba(14,13,12,.7)', GOLD, 'it', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .sh', 0, x=-240, opacity=0) + T(f'#{i} .sh', t0, x=0, opacity=1, duration=1.4, ease='power2.out'),
         _qdraw(i, 'ar path', t0 + .6, 520, .8), _qfade(i, 'ar polygon', t0 + 1.3, .2)] + ([_rv(f'#{i} .it', t0 + .8, 10)] if item else []) + jn
    j += [S(f'#{i} .wv{k}', 0, opacity=.1) + T(f'#{i} .wv{k}', a + .2 * k, opacity=.6, duration=.8, yoyo=True, repeat=5) for k in range(5)]
    return _out(i, a, b, 'r_xuatkhau', s, j), j, [(t0, 'rumble'), (t0 + .6, 'riser')] + ([(t0 + .5, 'count')] if value else [])


def thunhap(i, a, b, t0, value='', unit='triệu đồng', kicker='THU NHẬP', title='', source=''):
    """thu nhập bình quân: 3 người đứng cạnh các cột tiền giấy cao dần, ví vàng; value = mức thu nhập (chỉ khi lời có)"""
    Y = 610; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .4)
    s = _qhead(i, kicker, title, _lg(f'{i}bl', 'hsl(150,40%,55%)', 'hsl(150,45%,30%)', 1, 0)) + sn
    s += f'<ellipse cx="360" cy="{Y + 6}" rx="300" ry="20" fill="#000" opacity=".45" filter="url(#{i}sf)"/>'
    for k in range(3):
        x = 150 + k * 180; h = 70 + k * 60
        s += _person(x - 40, Y, 1.25, ('hsl(210,55%,45%)', 'hsl(28,80%,52%)', 'hsl(150,45%,40%)')[k], False, f'p{k}')
        s += f'<g class="b{k}">' + ''.join(f'<rect x="{x}" y="{Y - (q + 1) * 10:.0f}" width="70" height="9" rx="2" fill="url(#{i}bl)" stroke="hsl(150,40%,24%)" stroke-width=".8"/>' for q in range(h // 10)) + '</g>'
    s += _qarrow(110, Y - 140, 620, Y - 290, GOLD, 4, 'ar') + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_qpop(i, f'p{k}', a + .1 + k * .1, .4) for k in range(3)] + [_qgrow(i, f'b{k}', t0 + k * .2, .7) for k in range(3)]
    j += [_qdraw(i, 'ar path', t0 + .7, 540, .7), _qfade(i, 'ar polygon', t0 + 1.3, .2)] + jn
    return _out(i, a, b, 'r_thunhap', s, j), j, [(t0, 'tick'), (t0 + .7, 'riser')] + ([(t0 + .4, 'count')] if value else [])


def danso(i, a, b, t0, value='', unit='người', kicker='DÂN SỐ', title='', source=''):
    """dân số – lao động: đám đông người tí hon xuất hiện lan rộng trên quảng trường; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .4)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(30,10%,52%)')
    random.seed(11); P = []
    for k in range(46):
        r = 4.3 * math.sqrt(random.random()); u = random.uniform(0, 2 * math.pi); P.append((5 + r * math.cos(u), 5 + r * math.sin(u), r))
    P.sort(key=lambda p: p[0] + p[1]); cols = ['hsl(210,55%,45%)', 'hsl(28,80%,52%)', 'hsl(150,45%,40%)', 'hsl(356,60%,50%)', 'hsl(44,85%,55%)', 'hsl(270,35%,50%)']
    order = sorted(range(len(P)), key=lambda k: P[k][2])
    for k, (x, y, r) in enumerate(P): s += _person(*I(x, y), .55 * sc / 30, cols[k % 6], False, f'q{k}')
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)]
    j += [_qpop(i, f'q{k}', t0 + n * .025, .3) for n, k in enumerate(order)] + jn
    return _out(i, a, b, 'r_danso', s, j), j, [(t0, 'air')] + ([(t0 + .4, 'count')] if value else [])


def dautucong(i, a, b, t0, pct='', kicker='ĐẦU TƯ CÔNG', title='Giải ngân', source=''):
    """giải ngân đầu tư công: công trường có cọc tiêu, xe lu, thanh tiến độ ống thuỷ tinh đổ đầy vàng tới pct (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 80, 26)
    s = _qhead(i, kicker, title, _lg(f'{i}lq', 'hsl(48,100%,66%)', 'hsl(38,90%,46%)', 1, 0)) + _ground(I, i, 0, 0, 10, 6, 'hsl(32,25%,40%)') + _qroadx(I, 0, 10, 3, 1.4, 'rd')
    s += ''.join(f'<g class="cn{k}"><polygon points="{_pt([(lambda p: (p[0] - 8, p[1]))(I(1 + k * 1.6, 1.8)), (lambda p: (p[0], p[1] - 22))(I(1 + k * 1.6, 1.8)), (lambda p: (p[0] + 8, p[1]))(I(1 + k * 1.6, 1.8))])}" fill="hsl(24,95%,55%)"/></g>' for k in range(6))
    s += '<g class="rl">' + _box(I, 6, 2.6, 1.6, .9, .8, 'hsl(44,90%,55%)', 'hsl(42,80%,42%)', 'hsl(40,80%,32%)') + '</g>'
    X0, Yb, W = 80, Y0 + 300, 560; p = float(str(pct).replace(',', '.').replace('%', '')) / 100 if pct else .7
    s += (f'<rect x="{X0}" y="{Yb}" width="{W}" height="34" rx="17" fill="rgba(255,255,255,.06)" stroke="rgba(255,255,255,.25)"/>'
          f'<rect class="lq" x="{X0 + 4}" y="{Yb + 4}" width="0" height="26" rx="13" fill="url(#{i}lq)" filter="url(#{i}gl)"/>'
          f'<rect x="{X0 + 12}" y="{Yb + 7}" width="{W - 24}" height="6" rx="3" fill="#fff" opacity=".18"/>')
    if pct: s += f'<g class="pv">' + _t(X0 + W * p, Yb - 18, f'{pct}%' if '%' not in str(pct) else pct, 40, GOLD, 'middle', w=800) + '</g>'
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'rd', a + .2)] + [_qpop(i, f'cn{k}', a + .3 + k * .07, .3) for k in range(6)]
    j += [S(f'#{i} .rl', 0, x=-120) + T(f'#{i} .rl', t0, x=60, duration=2.2, ease='none'), T(f'#{i} .lq', t0 + .2, attr={'width': (W - 8) * p}, duration=1.4, ease='power2.out')] + ([_rv(f'#{i} .pv', t0 + 1.2, 10)] if pct else [])
    return _out(i, a, b, 'r_dautucong', s, j), j, [(t0, 'rumble'), (t0 + .2, 'riser'), (t0 + 1.4, 'ding')]


# ---------------------------------------------------------------- NÔNG NGHIỆP +7
def _fruitscene(i, a, b, t0, value, unit, kicker, title, source, name, art, cues_extra=()):
    Y = 470 if not value else 520; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .5)
    s = _qhead(i, kicker, title, art[0]) + sn + f'<ellipse cx="360" cy="{Y + 130}" rx="230" ry="26" fill="#000" opacity=".5" filter="url(#{i}sf)"/>' + art[1].replace('{Y}', str(Y))
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + art[2] + jn
    return _out(i, a, b, name, s, j), j, list(cues_extra) + ([(t0 + .5, 'count')] if value else [])


def saurieng(i, a, b, t0, value='', unit='tấn', kicker='SẦU RIÊNG', title='', source=''):
    """trái sầu riêng 3D gai nhọn, múi vàng bổ đôi, lá xanh; value = sản lượng/giá trị (chỉ khi lời có)"""
    Y = 470 if not value else 520
    defs = _rg(f'{i}dr', 'hsl(78,45%,52%)', 'hsl(85,45%,22%)', .4, .3) + _rg(f'{i}pu', 'hsl(48,95%,72%)', 'hsl(40,85%,48%)', .4, .3)
    sp = ''.join(f'<path d="M{300 + 90 * math.cos(u):.0f} {Y + 90 * math.sin(u) * .95:.0f} l{14 * math.cos(u):.0f} {14 * math.sin(u):.0f}" stroke="hsl(80,40%,30%)" stroke-width="7" stroke-linecap="round"/>' for u in [q * math.pi / 14 for q in range(28)])
    sp += ''.join(f'<path d="M{300 + r * math.cos(u):.0f} {Y + r * math.sin(u):.0f} l4 -8 l4 8" fill="hsl(78,40%,40%)"/>' for r in (30, 55, 75) for u in [q * math.pi / 5 + r for q in range(10)])
    art = (f'<g class="fr"><ellipse cx="300" cy="{Y}" rx="92" ry="88" fill="url(#{i}dr)"/>{sp}<path d="M300 {Y - 88} q4 -26 18 -34" stroke="hsl(30,35%,28%)" stroke-width="8" fill="none" stroke-linecap="round"/></g>'
           f'<g class="hf"><path d="M430 {Y + 80} a70 60 0 0 1 140 0Z" fill="hsl(78,45%,36%)"/><path d="M442 {Y + 78} a58 48 0 0 1 116 0Z" fill="hsl(50,60%,88%)"/>'
           f'<ellipse cx="475" cy="{Y + 58}" rx="26" ry="20" fill="url(#{i}pu)"/><ellipse cx="525" cy="{Y + 56}" rx="26" ry="20" fill="url(#{i}pu)"/></g>'
           f'<g class="lf"><path d="M210 {Y + 70} q-60 -10 -90 30 q50 20 90 -30Z" fill="hsl(120,45%,34%)"/></g>')
    js = [_qpop(i, 'fr', t0, .6, '50% 50%'), _qpop(i, 'hf', t0 + .3, .5), _qpop(i, 'lf', t0 + .2, .4)]
    return _fruitscene(i, a, b, t0, value, unit, kicker, title, source, 'r_saurieng', (defs, art, js), [(t0, 'pop')])


def hotieu(i, a, b, t0, value='', unit='tấn', kicker='HỒ TIÊU', title='', source=''):
    """vườn tiêu: các trụ tiêu phủ lá xanh, chùm hạt tiêu đỏ – xanh, bao tiêu đen; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(25,35%,30%)')
    k = 0
    for r in range(3):
        for c in range(4):
            x, y = 1.4 + c * 2.3, 1.4 + r * 3; px, py = I(x, y); h = 110 * sc / 30
            s += (f'<g class="v{k}"><ellipse cx="{px + 6:.0f}" cy="{py + 2:.0f}" rx="18" ry="6" fill="#000" opacity=".35"/><rect x="{px - 4:.0f}" y="{py - h:.0f}" width="8" height="{h:.0f}" fill="hsl(28,30%,35%)"/>'
                  f'<ellipse cx="{px:.0f}" cy="{py - h * .55:.0f}" rx="{16 * sc / 30:.0f}" ry="{h * .5:.0f}" fill="hsl(120,42%,30%)"/><ellipse cx="{px - 4:.0f}" cy="{py - h * .62:.0f}" rx="{9 * sc / 30:.0f}" ry="{h * .36:.0f}" fill="hsl(110,45%,40%)"/>'
                  + ''.join(f'<circle cx="{px + dx:.0f}" cy="{py - h * dy:.0f}" r="3" fill="hsl({(0, 100)[(k + q) % 2]},70%,45%)"/>' for q, (dx, dy) in enumerate([(-8, .4), (7, .55), (-5, .75), (9, .3)])) + '</g>')
            k += 1
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qgrow(i, f'v{q}', t0 + q * .06, .5, 'back.out(1.5)') for q in range(k)] + jn
    return _out(i, a, b, 'r_hotieu', s, j), j, [(t0, 'air')] + ([(t0 + .5, 'count')] if value else [])


def caosu(i, a, b, t0, value='', unit='ha', kicker='CAO SU', title='', source=''):
    """rừng cao su thẳng hàng: thân cây xám có vết cạo và chén mủ trắng, tán xanh; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(80,25%,30%)')
    k = 0; T_ = []
    for r in range(4):
        for c in range(4):
            x, y = 1.2 + c * 2.4, 1.2 + r * 2.4; T_.append((x + y, x, y))
    for _, x, y in sorted(T_):
        px, py = I(x, y); h = 120 * sc / 30
        s += (f'<g class="t{k}"><ellipse cx="{px + 8:.0f}" cy="{py + 2:.0f}" rx="20" ry="7" fill="#000" opacity=".35"/><rect x="{px - 5:.0f}" y="{py - h:.0f}" width="10" height="{h:.0f}" fill="hsl(30,6%,58%)"/>'
              f'<path d="M{px - 5:.0f} {py - h * .3:.0f} l10 -6 M{px - 5:.0f} {py - h * .36:.0f} l10 -6" stroke="hsl(30,10%,35%)" stroke-width="1.5"/><path d="M{px - 7:.0f} {py - h * .22:.0f} h14 l-2 8 h-10Z" fill="#fafafa"/>'
              f'<ellipse cx="{px:.0f}" cy="{py - h - 14:.0f}" rx="{30 * sc / 30:.0f}" ry="{24 * sc / 30:.0f}" fill="hsl(115,40%,32%)"/><ellipse cx="{px - 8:.0f}" cy="{py - h - 22:.0f}" rx="{14 * sc / 30:.0f}" ry="{10 * sc / 30:.0f}" fill="hsl(105,45%,44%)"/></g>')
        k += 1
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qgrow(i, f't{q}', t0 + q * .05, .5, 'back.out(1.4)') for q in range(k)] + jn
    return _out(i, a, b, 'r_caosu', s, j), j, [(t0, 'air')] + ([(t0 + .5, 'count')] if value else [])


def traibo(i, a, b, t0, value='', unit='tấn', kicker='TRÁI BƠ', title='', source=''):
    """quả bơ bổ đôi (vỏ xanh sẫm, thịt vàng xanh, hạt nâu bóng) cạnh quả nguyên và lá; value (chỉ khi lời có)"""
    Y = 470 if not value else 520
    defs = _rg(f'{i}av', 'hsl(95,40%,30%)', 'hsl(100,45%,12%)', .4, .3) + _rg(f'{i}fl', 'hsl(62,70%,78%)', 'hsl(80,55%,50%)', .5, .45) + _rg(f'{i}sd', 'hsl(28,55%,50%)', 'hsl(20,50%,22%)', .35, .3)
    art = (f'<g class="w"><ellipse cx="250" cy="{Y + 10}" rx="80" ry="104" fill="url(#{i}av)" transform="rotate(-18 250 {Y})"/><ellipse cx="226" cy="{Y - 40}" rx="16" ry="30" fill="#fff" opacity=".12" transform="rotate(-18 250 {Y})"/></g>'
           f'<g class="h"><ellipse cx="450" cy="{Y + 20}" rx="82" ry="106" fill="hsl(100,45%,18%)" transform="rotate(14 450 {Y})"/><ellipse cx="450" cy="{Y + 20}" rx="72" ry="96" fill="url(#{i}fl)" transform="rotate(14 450 {Y})"/>'
           f'<circle cx="456" cy="{Y + 44}" r="38" fill="url(#{i}sd)"/><circle cx="444" cy="{Y + 30}" r="10" fill="#fff" opacity=".25"/></g>'
           f'<g class="lf"><path d="M330 {Y + 110} q40 -60 110 -50 q-30 60 -110 50Z" fill="hsl(115,45%,32%)"/><path d="M330 {Y + 110} q50 -40 110 -50" stroke="hsl(110,40%,22%)" stroke-width="2" fill="none"/></g>')
    js = [_qpop(i, 'w', t0, .6, '50% 50%'), _qpop(i, 'h', t0 + .25, .6, '50% 50%'), _qpop(i, 'lf', t0 + .4, .4)]
    return _fruitscene(i, a, b, t0, value, unit, kicker, title, source, 'r_traibo', (defs, art, js), [(t0, 'pop')])


def tuoinuoc(i, a, b, t0, tag='', kicker='THUỶ LỢI', title='', source=''):
    """thuỷ lợi: hồ chứa sau đập bê tông, kênh dẫn nước chảy xuống ruộng xanh, ống tưới nhỏ giọt lấp lánh; tag = tên công trình (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,35%,36%)')
    s += f'<polygon class="lk" points="{_P4(I, .4, .4, 9.6, 3.2, .02)}" fill="url(#{i}wt)"/>' + _box(I, .4, 3.2, 9.2, .5, .7, 'hsl(30,6%,72%)', 'hsl(30,6%,56%)', 'hsl(30,6%,44%)', 'dam')
    s += f'<polygon points="{_P4(I, 4.7, 3.7, 5.3, 9.6, .03)}" fill="hsl(205,45%,30%)"/><path class="fl" d="M{_pt([I(5, 3.8, .05), I(5, 9.5, .05)])}" stroke="hsl(195,90%,70%)" stroke-width="5" stroke-dasharray="14 12" opacity=".9"/>'
    for side in (0, 1):
        for r in range(4):
            x0 = .8 if side == 0 else 5.8; y = 4.4 + r * 1.3
            s += f'<g class="rw{side}{r}"><polygon points="{_P4(I, x0, y, x0 + 3.4, y + .9, .03)}" fill="hsl(105,50%,40%)"/><path d="M{_pt([I(x0, y + .45, .06), I(x0 + 3.4, y + .45, .06)])}" stroke="hsl(195,80%,70%)" stroke-width="1.5" stroke-dasharray="3 6"/></g>'
    if tag: tx, ty = I(5, 1.6, .1); s += _qpill(tx, ty, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'lk', a + .2), _qgrow(i, 'dam', t0, .6)]
    j += [S(f'#{i} .fl', 0, strokeDashoffset=0, opacity=0) + T(f'#{i} .fl', t0 + .4, opacity=.9, duration=.3) + T(f'#{i} .fl', t0 + .4, strokeDashoffset=-200, duration=max(1, b - t0 - .4), ease='none')]
    j += [_qfade(i, f'rw{sd}{r}', t0 + .7 + r * .12 + sd * .06) for sd in (0, 1) for r in range(4)] + ([_rv(f'#{i} .tg', t0 + .5, 10)] if tag else [])
    return _out(i, a, b, 'r_tuoinuoc', s, j), j, [(t0, 'block'), (t0 + .4, 'air')]


def chebien(i, a, b, t0, item='', value='', unit='tấn', kicker='CHẾ BIẾN', title='', source=''):
    """chế biến nông sản: băng chuyền chở hạt (cà phê) vào máy rang thép, ra bao đóng gói xếp pallet; item = tên sản phẩm in trên bao (chỉ khi lời có)"""
    Y = 540; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .6)
    s = _qhead(i, kicker, title, _lg(f'{i}st', '#e9ecef', '#7d838c', 1, 1)) + sn
    s += f'<ellipse cx="360" cy="{Y + 70}" rx="310" ry="22" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
    s += f'<rect x="40" y="{Y + 20}" width="300" height="14" rx="7" fill="#3a3d43"/>' + ''.join(f'<circle cx="{56 + q * 30}" cy="{Y + 27}" r="5" fill="#777"/>' for q in range(10))
    s += ''.join(f'<ellipse class="bn{k}" cx="{60}" cy="{Y + 12}" rx="8" ry="6" fill="hsl(25,55%,{30 + (k % 3) * 6}%)"/>' for k in range(10))
    s += (f'<g class="ro"><rect x="330" y="{Y - 110}" width="150" height="150" rx="16" fill="url(#{i}st)"/><circle cx="405" cy="{Y - 36}" r="44" fill="#2a2d32" stroke="#bbb" stroke-width="6"/>'
          f'<circle class="fan" cx="405" cy="{Y - 36}" r="30" fill="none" stroke="hsl(25,80%,50%)" stroke-width="6" stroke-dasharray="20 14"/><rect x="380" y="{Y - 150}" width="50" height="44" fill="url(#{i}st)"/></g>')
    for k in range(3):
        x = 520 + (k % 2) * 70; y = Y + 40 - (k // 2) * 56
        s += (f'<g class="bg{k}"><path d="M{x - 30} {y} q-6 -40 4 -52 h52 q10 12 4 52Z" fill="hsl(36,40%,70%)"/><path d="M{x - 22} {y - 50} h44" stroke="hsl(28,40%,40%)" stroke-width="3"/>'
              + (_t(x, y - 20, item, 11, 'hsl(20,50%,25%)', 'middle', w=900) if item else '') + '</g>')
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .ro', a + .1, 30, .7), T(f'#{i} .fan', t0, rotation=720, svgOrigin=f'405 {Y - 36}', duration=max(1, b - t0), ease='none')]
    j += [S(f'#{i} .bn{k}', 0, x=0, opacity=0) + T(f'#{i} .bn{k}', t0 + k * .18, opacity=1, duration=.05) + T(f'#{i} .bn{k}', t0 + k * .18, x=280, duration=1.0, ease='none') + T(f'#{i} .bn{k}', t0 + k * .18 + 1.0, opacity=0, duration=.05) for k in range(10)]
    j += [_qpop(i, f'bg{k}', t0 + 1.0 + k * .25, .4) for k in range(3)] + jn
    return _out(i, a, b, 'r_chebien', s, j), j, [(t0, 'metal'), (t0 + 1.0, 'thud')] + ([(t0 + .6, 'count')] if value else [])


def nhakinh(i, a, b, t0, value='', unit='ha', kicker='NÔNG NGHIỆP CÔNG NGHỆ CAO', title='', source=''):
    """nhà kính công nghệ cao: dãy nhà màng mái vòm trong suốt, luống rau xanh bên trong, cảm biến; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(30,15%,40%)')
    for k in range(4):
        x0 = .6 + k * 2.3; y0, y1 = 1, 9
        rows = ''.join(f'<polygon points="{_P4(I, x0 + .3 + q * .45, y0 + .3, x0 + .55 + q * .45, y1 - .3, .03)}" fill="hsl(110,55%,{40 + q % 2 * 8}%)"/>' for q in range(4))
        arcL = [I(x0 + .1 + 1.9 * (1 - math.cos(math.pi * q / 12)) / 2, y1, 1.2 * math.sin(math.pi * q / 12)) for q in range(13)]
        arcR = [I(x0 + .1 + 1.9 * (1 - math.cos(math.pi * q / 12)) / 2, y0, 1.2 * math.sin(math.pi * q / 12)) for q in range(13)]
        roof = f'<polygon points="{_pt(arcL + arcR[::-1])}" fill="hsl(200,60%,90%)" fill-opacity=".28" stroke="#fff" stroke-opacity=".55"/>' + f'<polygon points="{_pt(arcL)}" fill="hsl(200,60%,92%)" fill-opacity=".35" stroke="#fff"/>'
        ribs = ''.join(f'<path d="M{_pt([I(x0 + .1 + 1.9 * (1 - math.cos(math.pi * q / 12)) / 2, y0, 1.2 * math.sin(math.pi * q / 12)), I(x0 + .1 + 1.9 * (1 - math.cos(math.pi * q / 12)) / 2, y1, 1.2 * math.sin(math.pi * q / 12))])}" stroke="#fff" stroke-opacity=".25"/>' for q in (3, 6, 9))
        s += f'<g class="g{k}">{rows}{roof}{ribs}</g>'
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qgrow(i, f'g{k}', t0 + k * .15, .7, 'back.out(1.3)') for k in range(4)] + jn
    return _out(i, a, b, 'r_nhakinh', s, j), j, [(t0, 'air'), (t0 + .4, 'shimmer')] + ([(t0 + .5, 'count')] if value else [])


# ---------------------------------------------------------------- LOGISTICS +7
def khobai(i, a, b, t0, value='', unit='m²', kicker='KHO BÃI', title='', source=''):
    """trung tâm kho: nhà kho mái tôn cửa cuốn mở, kệ pallet hàng, xe nâng chạy; value = diện tích (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(30,6%,40%)')
    s += '<g class="wh">' + _hall(I, .8, .8, 6.4, 4, 2.0, '', (210, 12)) + '</g>'
    for k in range(3):
        x = 1.6 + k * 1.8; s += f'<g class="dr{k}"><polygon points="{_pt([I(x, 4.8, 0), I(x + 1.2, 4.8, 0), I(x + 1.2, 4.8, 1.4), I(x, 4.8, 1.4)])}" fill="hsl(30,8%,22%)"/></g>'
    for c in range(4):
        for r in range(2):
            x, y = 1 + c * 1.4, 6.4 + r * 1.4
            s += f'<g class="pl{c}{r}">' + _box(I, x, y, 1.1, 1.1, .15, 'hsl(32,40%,55%)', 'hsl(30,40%,40%)', 'hsl(28,40%,30%)') + _box(I, x + .1, y + .1, .9, .9, .7, 'hsl(36,45%,62%)', 'hsl(34,40%,48%)', 'hsl(32,40%,38%)').replace('<g class="">', f'<g transform="translate(0 {-.15 * sc:.0f})">') + '</g>'
    s += '<g class="fk">' + _box(I, 7.6, 6.6, .8, .6, .5, GOLD, 'hsl(42,80%,42%)', 'hsl(40,80%,32%)') + f'<path d="M{_pt([I(7.6, 6.7, .5), I(7.6, 6.7, 1.4)])}" stroke="#333" stroke-width="3"/></g>' + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'wh', a + .2, .8)] + [_qfade(i, f'dr{k}', t0 + k * .1) for k in range(3)]
    j += [_rv(f'#{i} .pl{c}{r}', t0 + .3 + (c + r) * .08, 30, .4) for c in range(4) for r in range(2)] + [S(f'#{i} .fk', 0, x=60, opacity=0) + T(f'#{i} .fk', t0 + .5, x=-40, opacity=1, duration=1.6, ease='power1.inOut')] + jn
    return _out(i, a, b, 'r_khobai', s, j), j, [(t0, 'metal'), (t0 + .5, 'block')] + ([(t0 + .5, 'count')] if value else [])


def vantai(i, a, b, t0, from_='', to='', dist='', kicker='VẬN TẢI', title='', source=''):
    """xe tải container chạy trên tuyến đường giữa 2 ghim, vệt sáng phía sau; from_/to tên điểm, dist='180 km' (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,32%)')
    P = [I(1, 8.5 - 7 * q / 30 + .8 * math.sin(q / 30 * math.pi * 2), .02) for q in range(31)]; P = [I(1 + 8 * q / 30, 8.5 - 7 * q / 30 + .9 * math.sin(q / 30 * math.pi * 2), .02) for q in range(31)]
    L = sum(math.dist(P[q], P[q + 1]) for q in range(30))
    s += f'<path d="M{_pt(P)}" stroke="#2e3136" stroke-width="26" fill="none" stroke-linecap="round"/><path class="ln" d="M{_pt(P)}" stroke="{GOLD}" stroke-width="4" fill="none" stroke-dasharray="12 10"/>'
    s += _qpin(*P[0], 'hsl(205,70%,55%)', 'p0', from_) + _qpin(*P[-1], RED, 'p1', to)
    tx, ty = P[0]; s += f'<g class="tk"><g transform="translate({tx - 30:.0f} {ty - 40:.0f})"><rect x="0" y="0" width="46" height="26" rx="3" fill="#eceef1"/><rect x="46" y="8" width="16" height="18" rx="3" fill="hsl(205,60%,45%)"/><circle cx="12" cy="28" r="5" fill="#222"/><circle cx="52" cy="28" r="5" fill="#222"/></g></g>'
    if dist: mx, my = P[15]; s += _qpill(mx + 70, my - 20, dist, 'rgba(14,13,12,.8)', GOLD, 'ds', 18)
    s += _note(source)
    kf = ','.join('{x:%d,y:%d,duration:%.2f}' % (x - tx, y - ty, 1.8 / 6) for x, y in P[5::5])
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qpop(i, 'p0', a + .3, .4), _qpop(i, 'p1', a + .45, .4), _qdraw(i, 'ln', t0, L, 1.8, 'none'),
         _qfade(i, 'tk', t0, .2) + f"tl.to('#{i} .tk',{{keyframes:[{kf}],ease:'none'}},{t0:.2f});"] + ([_rv(f'#{i} .ds', t0 + .9, 10)] if dist else [])
    return _out(i, a, b, 'r_vantai', s, j), j, [(t0, 'rumble'), (t0 + 1.8, 'ding')]


def thongquan(i, a, b, t0, t_ok=None, tag='', kicker='THÔNG QUAN', title='', source=''):
    """cổng kiểm soát: trạm mái che, barrier sọc đỏ trắng nâng lên ở t_ok, xe container đi qua, đèn xanh; tag = tên cửa khẩu/cảng (chỉ khi lời có)"""
    t_ok = t0 + .8 if t_ok is None else t_ok; sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,6%,40%)') + _qroadx(I, 0, 10, 5, 2.0, 'rd')
    s += _box(I, 3.4, 2.6, 3.2, 4.8, .12, 'hsl(205,20%,82%)', 'hsl(205,20%,64%)', 'hsl(205,20%,50%)', 'cv').replace('<g class="cv">', f'<g class="cv" transform="translate(0 {-2.2 * sc:.0f})">')
    s += ''.join(f'<path d="M{_pt([I(x, y, 0), I(x, y, 2.2)])}" stroke="#bfc4ca" stroke-width="6"/>' for x, y in ((3.5, 2.7), (6.5, 2.7), (3.5, 7.3), (6.5, 7.3)))
    bx, by = I(5.6, 4.1, .9)
    s += f'<g class="br"><path d="M{bx:.0f} {by:.0f} l170 -12" stroke="#fff" stroke-width="9" stroke-linecap="round"/><path d="M{bx:.0f} {by:.0f} l170 -12" stroke="{RED}" stroke-width="9" stroke-dasharray="20 20"/></g>'
    s += f'<circle class="lr" cx="{bx - 6:.0f}" cy="{by - 30:.0f}" r="8" fill="{RED}"/><circle class="lg" cx="{bx - 6:.0f}" cy="{by - 30:.0f}" r="8" fill="{GRN}" opacity="0" filter="url(#{i}gl)"/>'
    s += _truck(I, .3, 4.8, True, 'hsl(205,60%,45%)', 'tk')
    if tag: tx, ty = I(5, 2.6, 2.4); s += _qpill(tx, ty - 10, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    d0 = I(.3, 4.8); d1 = I(8.4, 4.8)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'cv', a + .2), _qfade(i, 'tk', t0, .3) + T(f'#{i} .tk', t0, x=(d1[0] - d0[0]) * .35, y=(d1[1] - d0[1]) * .35, duration=.7, ease='power2.out'),
         T(f'#{i} .br', t_ok, rotation=-70, svgOrigin=f'{bx:.0f} {by:.0f}', duration=.5, ease='back.out(1.5)'), T(f'#{i} .lg', t_ok, opacity=1, duration=.2), T(f'#{i} .lr', t_ok, opacity=0, duration=.2),
         T(f'#{i} .tk', t_ok + .4, x=(d1[0] - d0[0]), y=(d1[1] - d0[1]), duration=1.4, ease='power2.in')] + ([_rv(f'#{i} .tg', t0 + .3, 10)] if tag else [])
    return _out(i, a, b, 'r_thongquan', s, j), j, [(t0, 'rumble'), (t_ok, 'ding'), (t_ok + .4, 'whoosh')]


def hangkhong(i, a, b, t0, value='', unit='tấn', kicker='HÀNG KHÔNG', title='', source=''):
    """vận tải hàng không: máy bay chở hàng mở cửa hông, thùng hàng ULD trượt lên băng tải; value (chỉ khi lời có)"""
    Y = 500 if not value else 540; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .5)
    s = _qhead(i, kicker, title, _lg(f'{i}fu', '#f4f6f8', '#aeb5bd')) + sn
    s += f'<ellipse cx="360" cy="{Y + 70}" rx="320" ry="24" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
    s += (f'<g class="pl"><path d="M70 {Y} C70 {Y - 50} 130 {Y - 64} 200 {Y - 64} H600 C640 {Y - 64} 660 {Y - 40} 680 {Y - 20} L690 {Y + 10} H120 C90 {Y + 10} 70 {Y + 4} 70 {Y}Z" fill="url(#{i}fu)"/>'
          f'<path d="M620 {Y - 64} L660 {Y - 150} H700 L690 {Y - 40}Z" fill="#dfe3e8"/><path d="M300 {Y} L240 {Y + 70} H330 L420 {Y}Z" fill="#cfd5db"/>'
          + ''.join(f'<circle cx="{180 + q * 30}" cy="{Y - 40}" r="5" fill="hsl(205,40%,30%)"/>' for q in range(12)) + f'<path d="M80 {Y - 18} q10 -24 40 -30" stroke="hsl(205,40%,30%)" stroke-width="8" fill="none"/></g>')
    s += f'<g class="dr"><rect x="430" y="{Y - 56}" width="90" height="56" fill="#2a2d32"/></g><path class="bt" d="M450 {Y + 60} L470 {Y - 4}" stroke="#555" stroke-width="10"/>'
    s += ''.join(f'<g class="u{k}"><rect x="{380 - k * 70}" y="{Y + 26}" width="60" height="44" rx="4" fill="hsl({(205, 36, 0)[k]},40%,{(55, 60, 55)[k]}%)"/><path d="M{380 - k * 70} {Y + 34} h60" stroke="#fff" stroke-opacity=".4"/></g>' for k in range(3))
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [S(f'#{i} .pl', 0, x=-300, opacity=0) + T(f'#{i} .pl', a + .1, x=0, opacity=1, duration=1.0, ease='expo.out'),
         S(f'#{i} .dr', 0, scaleY=0, transformOrigin='50% 0%') + T(f'#{i} .dr', t0, scaleY=1, duration=.4), _qfade(i, 'bt', t0 + .3)]
    j += [_qpop(i, f'u{k}', t0 + .4 + k * .15, .4) + T(f'#{i} .u{k}', t0 + 1.0 + k * .35, x=60 + k * 70, y=-60, opacity=0, duration=.6, ease='power2.in') for k in range(3)] + jn
    return _out(i, a, b, 'r_hangkhong', s, j), j, [(t0, 'whoosh'), (t0 + 1, 'thud')] + ([(t0 + .5, 'count')] if value else [])


def giaohang(i, a, b, t0, value='', unit='đơn', kicker='GIAO HÀNG', title='', source=''):
    """giao hàng chặng cuối: các xe máy chở thùng hàng toả ra từ kho trung tâm tới các ngôi nhà có ghim; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,34%)') + _qroadx(I, 0, 10, 5, .7, 'r1') + _qroady(I, 0, 10, 5, .7, 'r2')
    s += '<g class="hb">' + _hall(I, 4, 4, 2, 2, 1.0, '', (36, 30)) + '</g>'
    D = [(1.5, 1.5), (8.5, 1.5), (1.5, 8.5), (8.5, 8.5)]; j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'hb', a + .2, .6)]
    for k, (x, y) in enumerate(D):
        s += f'<g class="h{k}">' + _house(I, x - .6, y - .6, 1.2, 1.2, 1.0, 20 + 20 * k, '') + '</g>'
        hx, hy = I(5, 5, .3); px, py = I(x, 5 if k < 2 else 5, .3)
        mx, my = I(x, y, .3)
        s += f'<g class="m{k}"><g transform="translate({hx:.0f} {hy:.0f})"><circle cx="-8" cy="6" r="5" fill="#222"/><circle cx="10" cy="6" r="5" fill="#222"/><rect x="-12" y="-6" width="24" height="10" rx="4" fill="{RED}"/><rect x="-14" y="-20" width="16" height="14" fill="{GOLD}"/></g></g>'
        j += [_qpop(i, f'h{k}', a + .3 + k * .08, .4), _qfade(i, f'm{k}', t0 + k * .15, .2) + T(f'#{i} .m{k}', t0 + k * .15, x=mx - hx, y=my - hy, duration=1.2, ease='power1.inOut')]
    s += ''.join(_qpin(*I(x, y, 1.6), GOLD, f'pn{k}') for k, (x, y) in enumerate(D)) + _note(source)
    j += [_qpop(i, f'pn{k}', t0 + 1.2 + k * .15, .4) for k in range(4)] + jn
    return _out(i, a, b, 'r_giaohang', s, j), j, [(t0, 'whoosh'), (t0 + 1.2, 'pop')] + ([(t0 + .5, 'count')] if value else [])


def chuoicu(i, a, b, steps, kicker='CHUỖI CUNG ỨNG', title='', source=''):
    """chuỗi cung ứng: các nút tròn kim loại có biểu tượng (trang trại → nhà máy → kho → cảng → tàu) nối bằng dòng sáng chạy; steps=[('VÙNG TRỒNG', t)] ≤5"""
    n = min(5, len(steps)); Y = 470; X0, X1 = 110, 610; xs = [X0 + (X1 - X0) * k / max(1, n - 1) for k in range(n)]
    ICON = ['<path d="M-14 8 q14 -30 28 0Z" fill="hsl(110,50%,45%)"/><rect x="-1" y="-2" width="2" height="12" fill="hsl(28,40%,30%)"/>',
            '<rect x="-14" y="-6" width="28" height="16" fill="#bbb"/><rect x="6" y="-16" width="6" height="10" fill="#999"/>',
            '<path d="M-14 10 V-4 L0 -12 L14 -4 V10Z" fill="hsl(36,45%,60%)"/>',
            '<path d="M-2 10 V-14 M-2 -14 H12" stroke="hsl(356,60%,50%)" stroke-width="3"/><rect x="-14" y="2" width="24" height="8" fill="#888"/>',
            '<path d="M-16 0 H16 L10 10 H-10Z" fill="hsl(356,50%,42%)"/><rect x="-8" y="-8" width="14" height="8" fill="hsl(205,50%,45%)"/>']
    s = _qhead(i, kicker, title, _rg(f'{i}nd', '#f0f2f4', '#7d838c', .4, .3))
    s += f'<path d="M{X0} {Y} H{X1}" stroke="rgba(255,255,255,.12)" stroke-width="6"/><path class="fl" d="M{X0} {Y} H{X1}" stroke="{GOLD}" stroke-width="6" filter="url(#{i}gl)"/>'
    j = _vis(i, a, b) + _headj(i, a, title); cues = []
    for k, (lab, t) in enumerate(steps[:n]):
        x = xs[k]
        s += (f'<g class="n{k}"><circle cx="{x:.0f}" cy="{Y}" r="50" fill="url(#{i}nd)" filter="url(#{i}sh)"/><circle cx="{x:.0f}" cy="{Y}" r="40" fill="#1b1c20"/>'
              f'<g transform="translate({x:.0f} {Y}) scale(1.6)">{ICON[k % 5]}</g>' + _t(x, Y + 84, lab, 17, FG, 'middle', w=800, ls=1) + '</g>')
        j += [_qpop(i, f'n{k}', t, .5, '50% 50%')]; cues.append((t, 'pop'))
    j.append(S(f'#{i} .fl', 0, scaleX=0, transformOrigin=f'{X0}px {Y}px') + T(f'#{i} .fl', steps[0][1], scaleX=1, duration=max(.5, steps[n - 1][1] - steps[0][1]), ease='none'))
    s += _note(source)
    return _out(i, a, b, 'r_chuoicu', s, j), j, cues


def kholanh(i, a, b, t0, tag='', kicker='KHO LẠNH', title='', source=''):
    """kho lạnh bảo quản nông sản: khối kho panel trắng, cửa kho hơi lạnh toả, bông tuyết, kệ thùng trái cây; tag (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(205,10%,40%)')
    s += '<g class="cb">' + _box(I, 1.2, 1.2, 6.6, 5, 2.6, '#f4f7fa', '#dfe6ee', '#b7c3cf', '', ''.join(f'<path d="M{_pt([I(1.2 + q * .6, 6.2, 0), I(1.2 + q * .6, 6.2, 2.6)])}" stroke="#c9d3dd" stroke-width="1"/>' for q in range(1, 11))) + '</g>'
    dx0, dy0 = I(3.4, 6.2, 0)
    s += f'<g class="dr"><polygon points="{_pt([I(3.4, 6.2, 0), I(5.4, 6.2, 0), I(5.4, 6.2, 1.8), I(3.4, 6.2, 1.8)])}" fill="hsl(200,40%,22%)"/></g>'
    s += ''.join(f'<ellipse class="fg{k}" cx="{dx0 + 30 + k * 18:.0f}" cy="{dy0 - 10:.0f}" rx="40" ry="16" fill="#e8f4ff" opacity="0" filter="url(#{i}sf)"/>' for k in range(4))
    s += ''.join(f'<g class="sn{k}" transform="translate({120 + k * 110} {Y0 - 10 + (k % 2) * 30})" opacity=".8">' + ''.join(f'<path d="M0 0 L{12 * math.cos(math.radians(u)):.1f} {12 * math.sin(math.radians(u)):.1f}" stroke="#cfe8ff" stroke-width="2.5"/>' for u in range(0, 360, 60)) + '</g>' for k in range(5))
    if tag: tx, ty = I(4.5, 1.2, 2.8); s += _qpill(tx, ty - 10, tag, 'hsl(200,70%,60%)', '#06121c', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'cb', a + .2, .8), _qfade(i, 'dr', t0)]
    j += [T(f'#{i} .fg{k}', t0 + .2 + k * .15, opacity=.55, x=40, duration=1.4, ease='sine.out') for k in range(4)]
    j += [S(f'#{i} .sn{k}', 0, opacity=0, y=-20) + T(f'#{i} .sn{k}', t0 + .3 + k * .1, opacity=.8, y=20, rotation=60, duration=1.8, ease='none') for k in range(5)] + ([_rv(f'#{i} .tg', t0 + .5, 10)] if tag else [])
    return _out(i, a, b, 'r_kholanh', s, j), j, [(t0, 'air'), (t0 + .3, 'shimmer')]


# ---------------------------------------------------------------- CÔNG NGHIỆP +7
def khucn(i, a, b, t0, value='', unit='ha', tag='', kicker='KHU CÔNG NGHIỆP', title='', source=''):
    """mặt bằng khu công nghiệp: lưới đường nội khu, các lô xưởng mái xanh dương mọc lần lượt, cổng chính; value = diện tích (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(90,18%,36%)') + _qroadx(I, 0, 10, 5, .6, 'r1') + _qroady(I, 0, 10, 3.4, .6, 'r2') + _qroady(I, 0, 10, 6.8, .6, 'r3')
    k = 0
    for bx, x in enumerate((.4, 3.9, 7.3)):
        for y in (.5, 5.5):
            s += f'<g class="f{k}">' + _hall(I, x + .1, y + .2, 2.4, 3.4, .9, '', (205 if k % 2 else 210, 25 + k * 3)) + '</g>'; k += 1
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'r1', a + .2), _qfade(i, 'r2', a + .25), _qfade(i, 'r3', a + .3)]
    j += [_qgrow(i, f'f{q}', t0 + q * .12, .6, 'back.out(1.4)') for q in range(k)] + ([_rv(f'#{i} .tg', t0 + .9, 10)] if tag else []) + jn
    return _out(i, a, b, 'r_khucn', s, j), j, [(t0, 'block'), (t0 + .6, 'metal')] + ([(t0 + .5, 'count')] if value else [])


def tuabingio(i, a, b, t0, value='', unit='MW', kicker='ĐIỆN GIÓ', title='', source=''):
    """điện gió: hàng tua-bin trắng trên đồi, cánh quay đều, đường dây truyền tải; value = công suất (chỉ khi lời có)"""
    Y = 640; sn, jn = _qnum(i, value, unit, 300 if not title else 360, t0 + .5)
    s = _qhead(i, kicker, title, _lg(f'{i}hl', 'hsl(95,35%,40%)', 'hsl(100,35%,20%)')) + sn
    s += f'<path d="M40 {Y} C160 {Y - 90} 300 {Y - 120} 420 {Y - 80} C520 {Y - 50} 600 {Y - 90} 680 {Y - 60} V{Y + 20} H40Z" fill="url(#{i}hl)"/>'
    T_ = [(130, Y - 50, 1.0), (280, Y - 98, 1.15), (440, Y - 80, 1.05), (600, Y - 78, .9)]; j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .hl', a, 10)]
    for k, (x, y, z) in enumerate(T_):
        h = 220 * z * (.8 if value else 1); hx, hy = x, y - h
        s += (f'<g class="t{k}"><path d="M{x - 5} {y} L{x - 2} {hy:.0f} H{x + 2} L{x + 5} {y}Z" fill="#f2f4f6"/><path d="M{x + 1} {y} L{x + 2} {hy:.0f} L{x + 5} {y}Z" fill="#c9ced4"/>'
              f'<g class="bl{k}">' + ''.join(f'<path d="M{hx} {hy:.0f} l{80 * z * math.cos(math.radians(u)):.0f} {80 * z * math.sin(math.radians(u)):.0f}" stroke="#f7f9fb" stroke-width="{7 * z:.0f}" stroke-linecap="round"/>' for u in (-90, 30, 150))
              + f'</g><rect x="{hx - 6}" y="{hy - 5:.0f}" width="16" height="10" rx="4" fill="#dfe3e8"/></g>')
        j += [_qgrow(i, f't{k}', t0 + k * .15, .7), T(f'#{i} .bl{k}', t0 + .3, rotation=360 * 3, svgOrigin=f'{hx} {hy:.0f}', duration=max(1, b - t0), ease='none')]
    s += _note(source); j += jn
    return _out(i, a, b, 'r_tuabingio', s, j), j, [(t0, 'air')] + ([(t0 + .5, 'count')] if value else [])


def robot(i, a, b, t0, tag='', kicker='SẢN XUẤT', title='Dây chuyền tự động', source=''):
    """dây chuyền tự động: cánh tay robot cam gắp linh kiện trên băng chuyền, đèn trạng thái xanh; tag (chỉ khi lời có)"""
    Y = 560
    s = _qhead(i, kicker, title, _lg(f'{i}rb', 'hsl(28,95%,62%)', 'hsl(22,85%,42%)', 1, 1) + _lg(f'{i}st', '#e9ecef', '#7d838c', 1, 1))
    s += f'<ellipse cx="360" cy="{Y + 60}" rx="320" ry="22" fill="#000" opacity=".5" filter="url(#{i}sf)"/><rect x="40" y="{Y + 10}" width="640" height="20" rx="10" fill="#33363c"/>'
    s += ''.join(f'<circle cx="{60 + q * 40}" cy="{Y + 20}" r="6" fill="#777"/>' for q in range(16))
    s += ''.join(f'<g class="pc{k}"><rect x="{60}" y="{Y - 18}" width="40" height="28" rx="4" fill="hsl(205,30%,60%)"/><rect x="66" y="{Y - 12}" width="28" height="6" fill="hsl(205,40%,80%)"/></g>' for k in range(4))
    bx, by = 360, Y + 10
    s += (f'<g class="arm"><rect x="{bx - 40}" y="{by - 30}" width="80" height="30" rx="8" fill="url(#{i}st)"/><g class="a1"><rect x="{bx - 14}" y="{by - 170}" width="28" height="150" rx="14" fill="url(#{i}rb)"/>'
          f'<circle cx="{bx}" cy="{by - 30}" r="18" fill="#444"/><g class="a2"><rect x="{bx - 12}" y="{by - 170}" width="130" height="24" rx="12" fill="url(#{i}rb)"/><circle cx="{bx}" cy="{by - 158}" r="16" fill="#444"/>'
          f'<path d="M{bx + 118} {by - 158} v30 m-10 0 h20" stroke="#444" stroke-width="6"/></g></g></g>')
    s += f'<circle class="led" cx="{bx}" cy="{by - 16}" r="6" fill="{GRN}" filter="url(#{i}gl)"/>'
    if tag: s += _qpill(560, Y - 200, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .arm', a + .1, 30, .7)]
    j += [S(f'#{i} .pc{k}', 0, x=0, opacity=0) + T(f'#{i} .pc{k}', t0 + k * .7, opacity=1, duration=.1) + T(f'#{i} .pc{k}', t0 + k * .7, x=540, duration=2.4, ease='none') for k in range(4)]
    j += [T(f'#{i} .a1', t0, rotation=-18, svgOrigin=f'{bx} {by - 30}', duration=.7, yoyo=True, repeat=5, ease='sine.inOut'),
          T(f'#{i} .a2', t0, rotation=24, svgOrigin=f'{bx} {by - 158}', duration=.7, yoyo=True, repeat=5, ease='sine.inOut'),
          S(f'#{i} .led', 0, opacity=.3) + T(f'#{i} .led', t0, opacity=1, duration=.35, yoyo=True, repeat=8)] + ([_rv(f'#{i} .tg', t0 + .5, 10)] if tag else [])
    return _out(i, a, b, 'r_robot', s, j), j, [(t0, 'metal'), (t0 + .7, 'tick'), (t0 + 1.4, 'tick')]


def vatlieu(i, a, b, t0, items=(), kicker='VẬT LIỆU XÂY DỰNG', title='', source=''):
    """vật liệu xây dựng: bao xi măng xếp chồng, bó thép cây, kiện gạch đỏ, đống cát; items=[('XI MĂNG', t), ('THÉP', t), ('GẠCH', t)] nhãn (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 40, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 8, 'hsl(30,8%,42%)')
    cem = ''.join(_box(I, .8 + c * .9, .8 + r * .55, .85, .5, .35, 'hsl(40,10%,82%)', 'hsl(40,10%,66%)', 'hsl(40,10%,52%)').replace('<g class="">', f'<g transform="translate(0 {-z * .36 * sc:.0f})">') for z in range(3) for r in range(3) for c in range(2))
    st = ''.join(f'<path d="M{_pt([I(4.3, 1 + q * .12, .15 + (q % 3) * .1), I(8.8, 1 + q * .12, .15 + (q % 3) * .1)])}" stroke="hsl(210,6%,{40 + (q % 3) * 8}%)" stroke-width="5" stroke-linecap="round"/>' for q in range(12))
    br = ''.join(_box(I, .8 + c * .6, 4.6 + r * .35, .55, .3, .22, 'hsl(10,60%,52%)', 'hsl(10,55%,40%)', 'hsl(8,55%,30%)').replace('<g class="">', f'<g transform="translate(0 {-z * .23 * sc:.0f})">') for z in range(4) for r in range(4) for c in range(4))
    sx, sy = I(7, 5.6)
    sand = f'<path d="M{sx - 110:.0f} {sy + 20:.0f} Q{sx:.0f} {sy - 110:.0f} {sx + 110:.0f} {sy + 20:.0f}Z" fill="hsl(38,55%,62%)"/><path d="M{sx - 40:.0f} {sy - 30:.0f} Q{sx:.0f} {sy - 60:.0f} {sx + 30:.0f} {sy - 34:.0f}" stroke="#fff" stroke-opacity=".3" stroke-width="4" fill="none"/>'
    s += f'<g class="g0">{cem}</g><g class="g1">{st}</g><g class="g2">{br}</g><g class="g3">{sand}</g>'
    P = [I(1.7, 1.4, 1.6), I(6.5, 1.6, .8), I(2, 5.4, 1.4), I(7, 5.6, 3.6)]
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qgrow(i, f'g{k}', t0 + k * .2, .6, 'back.out(1.4)') for k in range(4)]
    for k, (lab, t) in enumerate(list(items)[:4]): s += _qpill(P[k][0], P[k][1] - 10, lab, 'rgba(14,13,12,.8)', GOLD, f'lb{k}', 16); j.append(_rv(f'#{i} .lb{k}', t, 8, .4))
    s += _note(source)
    return _out(i, a, b, 'r_vatlieu', s, j), j, [(t0, 'thud'), (t0 + .2, 'metal'), (t0 + .4, 'block')]


def xuongthue(i, a, b, t0, value='', unit='m²', kicker='NHÀ XƯỞNG', title='Nhà xưởng xây sẵn', source=''):
    """nhà xưởng xây sẵn cho thuê: dãy xưởng tiền chế giống nhau, biển CHO THUÊ, xe container đỗ; value = diện tích (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(30,6%,42%)') + _qroadx(I, 0, 10, 8.2, 1.2, 'rd')
    for k in range(3): s += f'<g class="x{k}">' + _hall(I, .6 + k * 3.1, 1.2, 2.8, 5.4, 1.4, '', (210, 15)) + '</g>'
    px, py = I(5, 7.2, 0)
    s += f'<g class="sg"><path d="M{px:.0f} {py:.0f} V{py - 70:.0f}" stroke="#ccc" stroke-width="4"/><rect x="{px - 60:.0f}" y="{py - 106:.0f}" width="120" height="40" rx="6" fill="{GOLD}"/>' + _t(px, py - 79, 'CHO THUÊ', 18, '#111', 'middle', w=900, ls=1) + '</g>'
    s += _truck(I, 1, 8, True, 'hsl(356,60%,50%)', 'tk') + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'rd', a + .2)] + [_qgrow(i, f'x{k}', t0 + k * .15, .7) for k in range(3)]
    j += [_qgrow(i, 'sg', t0 + .7, .5, 'back.out(2)'), _qfade(i, 'tk', t0 + .3) + T(f'#{i} .tk', t0 + .3, x=120, y=70, duration=1.4, ease='power2.out')] + jn
    return _out(i, a, b, 'r_xuongthue', s, j), j, [(t0, 'block'), (t0 + .7, 'pop')] + ([(t0 + .5, 'count')] if value else [])


def datacenter(i, a, b, t0, tag='', kicker='CÔNG NGHỆ CAO', title='', source=''):
    """công nghệ cao: dãy tủ máy chủ đen có đèn LED nhấp nháy xanh, chip vi mạch vàng nổi phía trên, đường mạch sáng chạy; tag (chỉ khi lời có)"""
    Y = 600
    s = _qhead(i, kicker, title, _lg(f'{i}rk', '#2a2d33', '#0f1013', 1, 0) + _lg(f'{i}ch', 'hsl(48,95%,70%)', 'hsl(38,85%,40%)', 1, 1))
    s += f'<ellipse cx="360" cy="{Y + 8}" rx="300" ry="20" fill="#000" opacity=".5" filter="url(#{i}sf)"/>'
    for k in range(5):
        x = 90 + k * 110
        s += (f'<g class="r{k}"><rect x="{x}" y="{Y - 200}" width="90" height="200" rx="4" fill="url(#{i}rk)" stroke="#3a3d44"/>'
              + ''.join(f'<rect x="{x + 8}" y="{Y - 190 + q * 18}" width="74" height="12" rx="2" fill="#16181c"/><circle class="ld{k}{q % 3}" cx="{x + 74}" cy="{Y - 184 + q * 18}" r="2.5" fill="{("hsl(150,90%,55%)", "hsl(200,90%,60%)", GOLD)[q % 3]}"/>' for q in range(10)) + '</g>')
    cx, cy = 360, Y - 300
    s += (f'<g class="cp"><rect x="{cx - 60}" y="{cy - 60}" width="120" height="120" rx="10" fill="url(#{i}ch)" filter="url(#{i}sh)"/><rect x="{cx - 38}" y="{cy - 38}" width="76" height="76" rx="6" fill="#1b1c20"/>'
          + ''.join(f'<rect x="{cx - 52 + q * 15}" y="{cy - 74}" width="6" height="14" fill="url(#{i}ch)"/><rect x="{cx - 52 + q * 15}" y="{cy + 60}" width="6" height="14" fill="url(#{i}ch)"/>' for q in range(8)) + '</g>')
    lines = [(cx - 60, cy, 140, cy), (cx + 60, cy, 580, cy), (cx, cy + 74, cx, Y - 210)]
    s += ''.join(f'<path class="ln{k}" d="M{x0} {y0} L{x1} {y1}" stroke="{GOLD}" stroke-width="3" filter="url(#{i}gl)"/>' for k, (x0, y0, x1, y1) in enumerate(lines))
    if tag: s += _qpill(cx, cy + 4, tag, 'rgba(0,0,0,0)', GOLD, 'tg', 16)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_qgrow(i, f'r{k}', a + .1 + k * .08, .6) for k in range(5)] + [_qpop(i, 'cp', t0, .6, '50% 50%')]
    j += [_qdraw(i, f'ln{k}', t0 + .4, math.dist(l[:2], l[2:]), .6) for k, l in enumerate(lines)]
    j += [S(f'#{i} .ld{k}{q}', 0, opacity=.2) + T(f'#{i} .ld{k}{q}', t0 + .1 * (k + q), opacity=1, duration=.25, yoyo=True, repeat=9) for k in range(5) for q in range(3)]
    return _out(i, a, b, 'r_datacenter', s, j), j, [(t0, 'scan'), (t0 + .4, 'shimmer')]


def xulynuoc(i, a, b, t0, tag='', kicker='MÔI TRƯỜNG', title='Xử lý nước thải', source=''):
    """trạm xử lý nước thải: các bể tròn bê tông nước xanh xoáy, ống dẫn, nước sạch chảy ra mương xanh; tag (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(95,22%,36%)')
    for k, (x, y, c) in enumerate([(2.2, 2.4, 'hsl(80,30%,38%)'), (5.2, 2.4, 'hsl(170,35%,40%)'), (2.2, 6.0, 'hsl(185,50%,45%)'), (5.2, 6.0, 'hsl(195,70%,55%)')]):
        cx, cy = I(x, y)
        s += (f'<g class="tk{k}"><ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{58 * sc / 30:.0f}" ry="{30 * sc / 30:.0f}" fill="hsl(30,6%,48%)"/><rect x="{cx - 58 * sc / 30:.0f}" y="{cy - 20 * sc / 30:.0f}" width="{116 * sc / 30:.0f}" height="{20 * sc / 30:.0f}" fill="hsl(30,6%,48%)"/>'
              f'<ellipse cx="{cx:.0f}" cy="{cy - 20 * sc / 30:.0f}" rx="{58 * sc / 30:.0f}" ry="{30 * sc / 30:.0f}" fill="hsl(30,6%,64%)"/><ellipse cx="{cx:.0f}" cy="{cy - 20 * sc / 30:.0f}" rx="{50 * sc / 30:.0f}" ry="{25 * sc / 30:.0f}" fill="{c}"/>'
              f'<ellipse class="sw{k}" cx="{cx:.0f}" cy="{cy - 20 * sc / 30:.0f}" rx="{30 * sc / 30:.0f}" ry="{14 * sc / 30:.0f}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2" stroke-dasharray="14 10"/></g>')
    s += f'<path d="M{_pt([I(2.2, 2.4, .5), I(5.2, 2.4, .5), I(5.2, 6, .5), I(2.2, 6, .5)])}" stroke="#9aa0a8" stroke-width="5" fill="none"/>'
    s += f'<polygon points="{_P4(I, 7.2, 0, 8.2, 10, .02)}" fill="hsl(195,70%,50%)"/><path class="fl" d="M{_pt([I(7.7, .2, .03), I(7.7, 9.8, .03)])}" stroke="#e8f8ff" stroke-width="3" stroke-dasharray="12 14"/>'
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7)] + [_qpop(i, f'tk{k}', t0 + k * .15, .5, '50% 50%') for k in range(4)]
    j += [T(f'#{i} .sw{k}', t0 + .4, strokeDashoffset=-200, duration=max(1, b - t0), ease='none') for k in range(4)] + [T(f'#{i} .fl', t0 + .5, strokeDashoffset=-300, duration=max(1, b - t0), ease='none')] + ([_rv(f'#{i} .tg', t0 + .7, 10)] if tag else [])
    return _out(i, a, b, 'r_xulynuoc', s, j), j, [(t0, 'air'), (t0 + .4, 'pop')]


# ---------------------------------------------------------------- THƯƠNG MẠI – DỊCH VỤ +4
def tttm(i, a, b, t0, tag='', kicker='THƯƠNG MẠI', title='Trung tâm thương mại', source=''):
    """trung tâm thương mại: khối kính nhiều tầng có biển sáng, sảnh vào, người mua sắm với túi, đèn sáng dần; tag = tên TTTM (chỉ khi lời có)"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0 + 20, sc)
    s = _qhead(i, kicker, title) + _ground(I, i, 0, 0, 10, 10, 'hsl(30,8%,46%)')
    s += '<g class="ml">' + _box(I, 1.4, 1.4, 7, 5, 2.8, 'hsl(205,15%,78%)', f'url(#{i}gw)', 'hsl(205,25%,42%)', '', _winL(I, 1.4, 1.4, 7, 5, 2.8, 7, 3, 'hsl(205,40%,32%)', lit={(0, 1), (1, 3), (2, 5), (0, 6), (1, 0)})) + '</g>'
    lx, ly = I(4.9, 6.4, 2.2)
    s += f'<g class="sg"><rect x="{lx - 90:.0f}" y="{ly - 20:.0f}" width="180" height="34" rx="6" fill="#111" stroke="{GOLD}" stroke-width="2"/>' + _t(lx, ly + 4, tag or 'MALL', 20, GOLD, 'middle', w=900, ls=3) + '</g>'
    random.seed(2)
    s += ''.join(_person(*I(2 + k * 1.2, 7.4 + (k % 2) * .9), .6, ('hsl(356,60%,55%)', 'hsl(205,55%,50%)', 'hsl(44,85%,55%)', 'hsl(150,45%,40%)')[k % 4], False, f'p{k}') for k in range(6)) + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'ml', t0, .8), _qpop(i, 'sg', t0 + .6, .5, '50% 50%')] + [_qpop(i, f'p{k}', t0 + .8 + k * .08, .35) for k in range(6)]
    return _out(i, a, b, 'r_tttm', s, j), j, [(t0, 'block'), (t0 + .6, 'shimmer')]


def khachsan(i, a, b, t0, value='', unit='phòng', tag='', kicker='DU LỊCH', title='', source=''):
    """khu nghỉ dưỡng ven biển: khách sạn cao tầng kính, hồ bơi, hàng dừa, bãi cát và sóng biển; value = số phòng (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + f'<polygon points="{_P4(I, 0, 0, 10, 10)}" fill="hsl(40,55%,72%)"/><polygon points="{_P4(I, 7.2, 0, 10, 10, .01)}" fill="url(#{i}wt)"/>'
    s += ''.join(f'<path class="wv{k}" d="M{_pt([I(7.4 + k * .5, .5 + k * 1.8, .02), I(7.4 + k * .5, 1.5 + k * 1.8, .02)])}" stroke="#fff" stroke-width="3" opacity=".6"/>' for k in range(5))
    s += '<g class="ht">' + _tower(I, i, 1, 1.4, 3, 2, 4.2, '', 5, 9, 200) + '</g>' + f'<polygon class="pl" points="{_P4(I, 1.2, 5, 4.8, 7, .02)}" fill="url(#{i}wt)"/>'
    for k, (x, y) in enumerate([(5.6, 1.2), (6, 3.4), (5.6, 5.8), (6.2, 8.2)]):
        px, py = I(x, y); s += f'<g class="pm{k}"><path d="M{px:.0f} {py:.0f} q6 -40 -6 -80" stroke="hsl(28,35%,35%)" stroke-width="6" fill="none"/>' + ''.join(f'<path d="M{px - 6:.0f} {py - 80:.0f} q{30 * math.cos(math.radians(u)):.0f} {-14 + 20 * math.sin(math.radians(u)):.0f} {48 * math.cos(math.radians(u)):.0f} {16 + 24 * math.sin(math.radians(u)):.0f}" stroke="hsl(120,45%,35%)" stroke-width="6" fill="none" stroke-linecap="round"/>' for u in (200, 250, 290, 340)) + '</g>'
    if tag: tx, ty = I(2.5, 1.4, 4.6); s += _qpill(tx, ty - 10, tag, GOLD, '#111', 'tg', 18)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_qgrow(i, 'ht', t0, .8), _qfade(i, 'pl', t0 + .3)] + [_qgrow(i, f'pm{k}', t0 + .4 + k * .1, .5, 'back.out(1.6)') for k in range(4)]
    j += [S(f'#{i} .wv{k}', 0, opacity=.1) + T(f'#{i} .wv{k}', a + .2 * k, opacity=.7, duration=.8, yoyo=True, repeat=6) for k in range(5)] + ([_rv(f'#{i} .tg', t0 + .7, 10)] if tag else []) + jn
    return _out(i, a, b, 'r_khachsan', s, j), j, [(t0, 'air'), (t0 + .4, 'pop')] + ([(t0 + .5, 'count')] if value else [])


def benhvien(i, a, b, t0, value='', unit='giường', tag='', kicker='Y TẾ', title='', source=''):
    """bệnh viện: khối nhà trắng nhiều tầng, chữ thập đỏ phát sáng trên nóc, sân đỗ trực thăng H, xe cứu thương; value = số giường (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(100,25%,40%)')
    s += '<g class="hp">' + _box(I, 1.5, 1.5, 6, 3, 2.8, '#f6f8fa', '#d8dee4', '#aab3bc', '', _winL(I, 1.5, 1.5, 6, 3, 2.8, 8, 5, 'hsl(200,40%,40%)', lit={(1, 2), (3, 5), (0, 7)})) + _box(I, 1.5, 4.5, 2.4, 3, 1.4, '#f6f8fa', '#d8dee4', '#aab3bc') + '</g>'
    cx, cy = I(4.5, 3, 3.4)
    s += f'<g class="cr"><rect x="{cx - 22:.0f}" y="{cy - 8:.0f}" width="44" height="16" rx="3" fill="{RED}" filter="url(#{i}gl)"/><rect x="{cx - 8:.0f}" y="{cy - 22:.0f}" width="16" height="44" rx="3" fill="{RED}" filter="url(#{i}gl)"/></g>'
    hx, hy = I(6, 6.6, .02); s += f'<g class="hl"><ellipse cx="{hx:.0f}" cy="{hy:.0f}" rx="60" ry="30" fill="#33363c"/><ellipse cx="{hx:.0f}" cy="{hy:.0f}" rx="50" ry="24" fill="none" stroke="#fff" stroke-width="2"/>' + _t(hx, hy + 9, 'H', 26, '#fff', 'middle', w=900) + '</g>'
    s += _box(I, 2.2, 8.2, 1.2, .6, .5, '#fff', '#e3e6ea', '#b9c0c8', 'am') + _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'hp', t0, .8), _qpop(i, 'cr', t0 + .6, .5, '50% 50%'), _qfade(i, 'hl', t0 + .4),
         _qfade(i, 'am', t0 + .5) + T(f'#{i} .am', t0 + .5, x=70, y=-35, duration=1.4, ease='power2.out')] + ([_rv(f'#{i} .tg', t0 + .7, 10)] if tag else []) + jn
    if tag: s = s.replace(_note(source), _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20) + _note(source))
    return _out(i, a, b, 'r_benhvien', s, j), j, [(t0, 'block'), (t0 + .6, 'ding')] + ([(t0 + .5, 'count')] if value else [])


def truonghoc(i, a, b, t0, value='', unit='học sinh', tag='', kicker='GIÁO DỤC', title='', source=''):
    """trường học: dãy lớp học mái ngói đỏ hình chữ L, sân trường có cột cờ đỏ phấp phới, cây phượng, học sinh; value (chỉ khi lời có)"""
    sc, Y0, ny = _qL(title, value); I = _iso(360, Y0, sc); sn, jn = _qnum(i, value, unit, ny, t0 + .5)
    s = _qhead(i, kicker, title) + sn + _ground(I, i, 0, 0, 10, 10, 'hsl(36,25%,58%)')
    s += '<g class="sc">' + _box(I, 1, 1, 7.5, 1.8, 1.6, 'hsl(10,60%,48%)', 'hsl(44,65%,78%)', 'hsl(42,55%,62%)', '', _winL(I, 1, 1, 7.5, 1.8, 1.6, 9, 2, 'hsl(205,35%,32%)')) \
         + _box(I, 1, 2.8, 1.8, 5.2, 1.6, 'hsl(10,60%,48%)', 'hsl(44,65%,78%)', 'hsl(42,55%,62%)', '', _winR(I, 1, 2.8, 1.8, 5.2, 1.6, 6, 2, 'hsl(205,35%,30%)')) + '</g>'
    fx, fy = I(6, 6.2)
    s += f'<g class="fl"><path d="M{fx:.0f} {fy:.0f} V{fy - 120:.0f}" stroke="#ddd" stroke-width="3"/><path class="fg" d="M{fx:.0f} {fy - 120:.0f} h44 v28 h-44Z" fill="hsl(356,85%,50%)"/><path d="M{fx + 22:.0f} {fy - 112:.0f} l3 7 h7 l-6 4 l2 7 l-6 -4 l-6 4 l2 -7 l-6 -4 h7Z" fill="{GOLD}"/></g>'
    s += _tree(I, i, 8.6, 4.2, 1.3, 't0').replace('url(#' + i + 'tr)', 'hsl(8,75%,52%)') + ''.join(_person(*I(4 + k * .8, 5 + (k % 2) * 1.2), .5, 'hsl(0,0%,96%)', False, f'p{k}') for k in range(5))
    if tag: s += _qpill(360, Y0 - 10, tag, GOLD, '#111', 'tg', 20)
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qgrow(i, 'sc', t0, .8), _qgrow(i, 'fl', t0 + .4, .6), _qpop(i, 't0', t0 + .5, .5)]
    j += [T(f'#{i} .fg', t0 + .8, skewY=6, duration=.5, yoyo=True, repeat=6, ease='sine.inOut', transformOrigin='0% 50%')] + [_qpop(i, f'p{k}', t0 + .6 + k * .08, .35) for k in range(5)] + ([_rv(f'#{i} .tg', t0 + .9, 10)] if tag else []) + jn
    return _out(i, a, b, 'r_truonghoc', s, j), j, [(t0, 'block'), (t0 + .6, 'pop')] + ([(t0 + .5, 'count')] if value else [])


# ---------------------------------------------------------------- TIN BÁO CHÍ (ảnh thật từ báo, ghi nguồn)
def bao(i, a, b, img, outlet='BÁO XÂY DỰNG', head='', cap='', author='', value='', unit='', label='', t_num=None, kicker='THEO BÁO CHÍ', title='', source=''):
    """trang báo giấy: tên báo (chữ serif, không dùng logo), ảnh thật của bài hiện ĐỦ khung (không cắt), chú thích + "Tác giả: …" nhỏ góc phải dưới ảnh + "Nguồn: …";
    img = đường dẫn ảnh; head = tít ngắn; value/unit/label = ô số vàng trên ảnh, đếm ở t_num (chỉ số có trong lời)"""
    import base64, io
    from PIL import Image
    im = Image.open(img).convert('RGB'); ar = im.width / im.height; im.thumbnail((1200, 1200)); bf = io.BytesIO(); im.save(bf, 'JPEG', quality=88)
    b64 = base64.b64encode(bf.getvalue()).decode()
    PY = 262 if title else 196; BOT = 684
    wrap = lambda n: [ln for ln in re.sub(r'(.{1,%d})(\s|$)' % n, r'\1\n', cap).strip().split('\n')][:2] if cap else []
    capL = wrap(62)
    top = PY + 52 + (36 if head else 6); low = (18 if author else 0) + 21 * len(capL) + 34   # chỗ dưới ảnh: tác giả · chú thích · nguồn
    ph_h = BOT - low - top; ph_w = min(596, ph_h * ar); ph_h = ph_w / ar          # ảnh giữ đúng tỉ lệ → không mất đầu người
    PW = max(ph_w + 32, 440); capL = wrap(int((PW - 32) / 8.3)); PX = 352 - PW / 2; ph_x = PX + (PW - ph_w) / 2; PH = top - PY + ph_h + low
    fs = lambda x, y, txt, sz, col, anc='start', it=False, cls='': (f'<text class="{cls}" x="{x:.0f}" y="{y:.0f}" text-anchor="{anc}" font-family="DejaVu Serif,Georgia,serif" font-weight="700" '
                                                                 f'{"font-style=\"italic\" " if it else ""}font-size="{sz}" fill="{col}">{txt}</text>')
    s = _qhead(i, kicker, title, f'<linearGradient id="{i}np" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f1e6"/><stop offset="1" stop-color="#ebe3d2"/></linearGradient>')
    yb = top + ph_h
    s += (f'<g class="pp" transform="rotate(-1 360 {PY + PH / 2:.0f})"><rect x="{PX:.0f}" y="{PY}" width="{PW:.0f}" height="{PH:.0f}" rx="4" fill="url(#{i}np)" filter="url(#{i}sh)"/>'
          f'<rect x="{PX:.0f}" y="{PY}" width="{PW:.0f}" height="{PH:.0f}" rx="4" fill="#fff" filter="url(#{i}nz)" opacity=".35"/>'
          + fs(PX + 16, PY + 34, outlet, 25, '#1d1a16')
          + f'<rect x="{PX + 16:.0f}" y="{PY + 44}" width="{PW - 32:.0f}" height="2" fill="#1d1a16"/><rect x="{PX + 16:.0f}" y="{PY + 48}" width="{PW - 32:.0f}" height=".8" fill="#1d1a16"/>'
          + (fs(PX + 16, PY + 52 + 26, head, 22, '#14110d') if head else '')
          + f'<image href="data:image/jpeg;base64,{b64}" x="{ph_x:.1f}" y="{top:.1f}" width="{ph_w:.1f}" height="{ph_h:.1f}" preserveAspectRatio="xMidYMid meet"/>'
          + (fs(ph_x + ph_w, yb + 15, f'Tác giả: {author}', 12, '#6b6357', 'end', True, 'au') if author else '')
          + ''.join(f'<text class="cp" x="{PX + 16:.0f}" y="{yb + (18 if author else 0) + 20 + k * 21:.0f}" font-family="VCB" font-weight="600" font-size="15" fill="#4a443b">{ln}</text>' for k, ln in enumerate(capL))
          + fs(PX + PW - 16, PY + PH - 12, f'Nguồn: {outlet.title() if outlet.isupper() else outlet}', 15, '#8a2a1c', 'end', True, 'src') + '</g>')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .pp', a + .08, 40, .8), _qfade(i, 'cp', a + .5), _qfade(i, 'au', a + .6), _qfade(i, 'src', a + .7)]
    cues = [(a + .1, 'paper')]
    if value:
        tn = t_num if t_num is not None else a + .6; bx, by = ph_x + 12, yb - 86
        bw = max(140, int(_w(value, 44) + (_w(unit, 22) + 8 if unit else 0) + 30), int(_w(label, 12) + 1.5 * len(label) + 28) if label else 0)
        s += (f'<g class="bd"><rect x="{bx:.0f}" y="{by:.0f}" width="{bw}" height="74" rx="8" fill="rgba(12,10,8,.8)" stroke="{GOLD}" stroke-width="2"/>'
              + (_t(bx + 14, by + 21, label, 12, GOLD, w=800, ls=1.5) if label else '')
              + _t(bx + 14, by + 64, value, 44, '#fff', cls='nv', w=800) + (_t(bx + 20 + _w(value, 44), by + 64, unit, 22, GOLD, cls='nu', w=800) if unit else '') + '</g>')
        j += [_qpop(i, 'bd', tn - .25, .45, '0% 100%')] + _numj(i, tn, value); cues.append((tn, 'count'))
    return _out(i, a, b, 'r_bao', s, j), j, cues


# ---------------------------------------------------------------- BỔ SUNG 25/11/2026
def duan4(i, a, b, t0=None, plots=(), items=(), t_save=None, kicker='DỰ ÁN', title='', source=''):
    """khu đất chia 4 ô dự án 3D: điện mặt trời (2 ô), sân sát hạch lái xe có xe chạy + cọc, nhà máy (phân bón) có silo + khói;
    plots=[(kind 'pv'|'pv2'|'lx'|'nm', t)] ô hiện theo lời · items=[(kind, NHÃN, t)] nhãn từng dự án · t_save → nhãn LƯU LẠI"""
    sc, Y0, _ = _qL(title, ''); I = _iso(360, Y0, sc)
    s = _qhead(i, kicker, title, _lg(f'{i}pv', 'hsl(215,60%,42%)', 'hsl(220,65%,20%)', 1, 1)) + _ground(I, i, 0, 0, 10, 10, 'hsl(85,22%,34%)')
    s += _qroadx(I, 0, 10, 5, .45, 'rx') + _qroady(I, 0, 10, 5, .45, 'ry')
    Q = {'pv': (0, 0), 'lx': (5.2, 0), 'nm': (0, 5.2), 'pv2': (5.2, 5.2)}
    def pv(x0, y0):
        g = ''
        for r in range(4):
            for c in range(2):
                x, y = x0 + .35 + c * 2.0, y0 + .4 + r * 1.0
                g += (f'<polygon points="{_pt([I(x, y, .45), I(x + 1.75, y, .45), I(x + 1.75, y + .6, .12), I(x, y + .6, .12)])}" fill="url(#{i}pv)" stroke="hsl(210,30%,72%)" stroke-width="1"/>'
                      f'<path d="M{_pt([I(x + .58, y, .45), I(x + .58, y + .6, .12)])} M{_pt([I(x + 1.17, y, .45), I(x + 1.17, y + .6, .12)])}" stroke="hsl(210,30%,72%)" stroke-width=".7"/>')
        return g
    def lx(x0, y0):
        g = f'<polygon points="{_P4(I, x0 + .3, y0 + .3, x0 + 4.4, y0 + 4.4, .01)}" fill="#2f3237"/>'
        g += f'<polygon points="{_P4(I, x0 + 1.2, y0 + 1.2, x0 + 3.5, y0 + 3.5, .02)}" fill="hsl(95,25%,36%)"/>'
        g += f'<path d="M{_pt([I(x0 + .75, y0 + .75, .03), I(x0 + 3.95, y0 + .75, .03), I(x0 + 3.95, y0 + 3.95, .03), I(x0 + .75, y0 + 3.95, .03)])}Z" fill="none" stroke="#f1ead0" stroke-width="2" stroke-dasharray="9 8"/>'
        for k, (x, y) in enumerate([(x0 + 1.0, y0 + 4.1), (x0 + 2.2, y0 + 4.1), (x0 + 3.4, y0 + 4.1), (x0 + 4.15, y0 + 2.2)]):
            cx_, cy_ = I(x, y, 0)
            g += f'<path d="M{cx_ - 6:.0f} {cy_:.0f} L{cx_:.0f} {cy_ - 18:.0f} L{cx_ + 6:.0f} {cy_:.0f}Z" fill="hsl(24,95%,55%)"/><rect x="{cx_ - 4:.0f}" y="{cy_ - 10:.0f}" width="8" height="3" fill="#fff"/>'
        return g + f'<g class="car">{_car(I, x0 + .9, y0 + .62, True, "hsl(44,90%,55%)", "cc")}</g>'
    def nm(x0, y0):
        g = _box(I, x0 + .6, y0 + 1.0, 2.6, 2.6, 1.1, 'hsl(210,8%,70%)', 'hsl(210,8%,58%)', 'hsl(210,10%,42%)')
        for k in range(4): g += f'<polygon points="{_pt([I(x0 + .6 + k * .65, y0 + 1.0, 1.1), I(x0 + .6 + k * .65, y0 + 3.6, 1.1), I(x0 + .95 + k * .65, y0 + 3.6, 1.45), I(x0 + .95 + k * .65, y0 + 1.0, 1.45)])}" fill="hsl(210,10%,{62 + k % 2 * 8}%)"/>'
        sx, sy = I(x0 + 3.9, y0 + 1.4, 0); g += _qcyl(sx, sy, 16, 7, 70, 'hsl(40,10%,72%)', 'hsl(40,10%,86%)')
        sx2, sy2 = I(x0 + 3.9, y0 + 2.4, 0); g += _qcyl(sx2, sy2, 16, 7, 60, 'hsl(40,10%,66%)', 'hsl(40,10%,84%)')
        cx_, cy_ = I(x0 + 1.0, y0 + 1.3, 1.45)
        g += f'<rect x="{cx_ - 5:.0f}" y="{cy_ - 60:.0f}" width="10" height="60" fill="hsl(8,55%,45%)"/><rect x="{cx_ - 5:.0f}" y="{cy_ - 52:.0f}" width="10" height="5" fill="#eee"/>'
        g += ''.join(f'<circle class="sm{k}" cx="{cx_ + k * 9:.0f}" cy="{cy_ - 70 - k * 16:.0f}" r="{8 + k * 4}" fill="#e9ecef" opacity=".55"/>' for k in range(3))
        return g
    FN = {'pv': pv, 'pv2': pv, 'lx': lx, 'nm': nm}
    for k in ('pv', 'lx', 'nm', 'pv2'): s += f'<g class="q{k}">{FN[k](*Q[k])}</g>'
    LP = {'pv': I(2.5, 2.4, 1.8), 'lx': I(7.6, 2.4, 1.6), 'nm': I(2.4, 7.6, 3.0), 'pv2': I(7.6, 7.6, 1.6)}
    for k, (kind, lab, t) in enumerate(list(items)[:6]): s += _qpill(LP[kind][0], LP[kind][1], lab, 'rgba(14,13,12,.85)', GOLD, f'lb{k}', 15)
    if t_save is not None: s += _qpill(60, 128, 'LƯU LẠI', GOLD, '#111', 'sv', 14, 'start')
    s += _src(source)
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .gd', a + .05, 30, .7), _qfade(i, 'rx', a + .3), _qfade(i, 'ry', a + .3)]
    for k in ('pv', 'lx', 'nm', 'pv2'):
        t = dict(plots).get(k, a + .4); j.append(_rv(f'#{i} .q{k}', t, 22, .6))
    dx, dy = 2.6 * .866 * sc, 2.6 * .5 * sc; tl_ = dict(plots).get('lx', a + .4) + .3
    j.append(S(f'#{i} .car', 0, x=0, y=0) + T(f'#{i} .car', tl_, x=dx, y=dy, duration=max(.5, b - tl_ - .2), ease='sine.inOut'))
    for k in range(3): j.append(T(f'#{i} .sm{k}', a + k * .3, y=-60, opacity=.1, duration=max(1, b - a), ease='none'))
    for k, (kind, lab, t) in enumerate(list(items)[:6]): j.append(_rv(f'#{i} .lb{k}', t, 10, .4))
    if t_save is not None: j.append(_qpop(i, 'sv', t_save, .4, '0% 50%'))
    return _out(i, a, b, 'r_duan4', s, j), j, [(a, 'air')] + [(t, 'thud') for _, t in plots] + ([(t_save, 'shimmer')] if t_save else [])


def trucot(i, a, b, cols=(), t_roof=None, roof='', t_save=None, kicker='TRỤ CỘT', title='', source=''):
    """công trình đá cẩm thạch: bệ bậc thềm, các cột trụ dựng lên theo lời (mỗi cột 1 nhãn + vai trò), mái tam giác hạ xuống chốt;
    cols=[(NHÃN, vai trò, t)] ≤4 · roof = chữ trên mái (chỉ chữ có trong lời) · t_save → nhãn LƯU LẠI"""
    s = (_defs(i) + _lg(f'{i}mb', '#f3efe6', '#8f887b', 1, 0) + _lg(f'{i}st', '#d9d3c6', '#77705f') + _lg(f'{i}rf', 'hsl(42,40%,86%)', 'hsl(38,30%,58%)')
         + _lg(f'{i}gd', 'hsl(46,95%,72%)', 'hsl(38,80%,46%)') + '</defs>' + _head(kicker, title))
    n = max(1, len(cols[:4])); X = [360 + (k - (n - 1) / 2) * 142 for k in range(n)]
    s += '<g class="bs" filter="url(#%ssh)">' % i + ''.join(f'<rect x="{360 - w / 2:.0f}" y="{y}" width="{w}" height="15" fill="url(#{i}st)"/><rect x="{360 - w / 2:.0f}" y="{y}" width="{w}" height="3" fill="#fff" opacity=".35"/>'
                                                     for w, y in ((560, 552), (600, 567), (640, 582))) + '</g>'
    for k, x in enumerate(X):
        s += (f'<g class="c{k}" filter="url(#{i}sh)"><rect x="{x - 44:.0f}" y="536" width="88" height="16" fill="url(#{i}st)"/>'
              f'<rect x="{x - 30:.0f}" y="378" width="60" height="158" fill="url(#{i}mb)"/>'
              + ''.join(f'<line x1="{x - 18 + q * 12:.0f}" y1="380" x2="{x - 18 + q * 12:.0f}" y2="534" stroke="#000" stroke-opacity=".13" stroke-width="2"/>' for q in range(4))
              + f'<rect x="{x - 40:.0f}" y="364" width="80" height="14" fill="url(#{i}st)"/><rect x="{x - 46:.0f}" y="356" width="92" height="9" fill="url(#{i}mb)"/></g>')
    s += (f'<g class="rf" filter="url(#{i}sh)"><rect x="70" y="334" width="580" height="22" fill="url(#{i}rf)"/><polygon points="58,334 662,334 360,278" fill="url(#{i}rf)"/>'
          f'<polygon points="96,328 624,328 360,288" fill="#000" opacity=".12"/>' + (_t(360, 323, roof, 22, 'hsl(34,70%,28%)', 'middle', w=900, ls=4) if roof else '') + '</g>')
    for k, ((lab, role, t), x) in enumerate(zip(cols[:4], X)):
        s += f'<g class="l{k}">' + _t(x, 626, lab, 16, GOLD, 'middle', w=900, ls=.5) + (_t(x, 650, role, 14, MUT, 'middle', w=700) if role else '') + '</g>'
    if t_save is not None: s += _qpill(60, 128, 'LƯU LẠI', GOLD, '#111', 'sv', 14, 'start')
    j = _vis(i, a, b) + _headj(i, a, title) + [_rv(f'#{i} .bs', a + .05, 30, .7)]
    for k, (lab, role, t) in enumerate(cols[:4]): j += [_qgrow(i, f'c{k}', t, .7, 'back.out(1.3)'), _rv(f'#{i} .l{k}', t + .15, 10, .4)]
    tr = t_roof if t_roof is not None else (cols[-1][2] + .7 if cols else a + .5)
    j.append(S(f'#{i} .rf', 0, y=-90, opacity=0) + T(f'#{i} .rf', tr, y=0, opacity=1, duration=.8, ease='bounce.out'))
    if t_save is not None: j.append(_qpop(i, 'sv', t_save, .4, '0% 50%'))
    return _out(i, a, b, 'r_trucot', s, j), j, [(t, 'thud') for _, _, t in cols[:4]] + [(tr + .3, 'block')] + ([(t_save, 'shimmer')] if t_save else [])


def haihoa(i, a, b, items=(), t_core=None, core='', kicker='ĐỊNH HƯỚNG', title='', source=''):
    """3 vòng kim loại đan nhau (vàng · bạc · xanh lá) tự vẽ theo lời, mỗi vòng 1 nhãn; lõi giao nhau phát sáng + chữ core ở t_core;
    items=[(NHÃN, t)] đúng 3 (chỉ chữ có trong lời)"""
    C = [(282, 410), (438, 410), (360, 545)]; R_ = 100; L = 2 * math.pi * R_
    COL = [('hsl(46,95%,70%)', 'hsl(38,80%,40%)'), ('hsl(210,15%,92%)', 'hsl(210,10%,52%)'), ('hsl(140,60%,60%)', 'hsl(150,60%,28%)')]
    s = _defs(i) + ''.join(_lg(f'{i}r{k}', c0, c1, 1, 1) for k, (c0, c1) in enumerate(COL)) + _rg(f'{i}cg', 'hsl(48,100%,85%)', 'hsl(40,90%,50%)', .5, .5) + '</defs>' + _head(kicker, title)
    s += f'<circle class="cg" cx="360" cy="455" r="46" fill="url(#{i}cg)" opacity=".0" filter="url(#{i}sf)"/>'
    for k, (x, y) in enumerate(C):
        s += (f'<g filter="url(#{i}sh)"><circle class="r{k}" cx="{x}" cy="{y}" r="{R_}" fill="none" stroke="url(#{i}r{k})" stroke-width="22" transform="rotate(-90 {x} {y})"/></g>'
              f'<circle class="h{k}" cx="{x}" cy="{y}" r="{R_ + 6}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="2" transform="rotate(-90 {x} {y})"/>')
    LP = [(228, 392), (492, 392), (360, 600)]
    for k, ((lab, t), (x, y)) in enumerate(zip(items[:3], LP)): s += f'<g class="l{k}">' + _t(x, y, lab, 19, FG, 'middle', w=900, ls=1) + '</g>'
    if core: s += f'<g class="cc">' + _t(360, 462, core, 17, '#1a1408', 'middle', w=900, ls=1) + '</g>'
    s += _note(source)
    j = _vis(i, a, b) + _headj(i, a, title)
    for k, (lab, t) in enumerate(items[:3]):
        j += [_qdraw(i, f'r{k}', t - .25, L, .9), _qdraw(i, f'h{k}', t - .15, 2 * math.pi * (R_ + 6), .9), _rv(f'#{i} .l{k}', t + .2, 10, .4)]
    tc = t_core if t_core is not None else (items[-1][1] + .8 if items else a + .5)
    j += [S(f'#{i} .cg', 0, opacity=0, scale=.3, transformOrigin='360px 455px') + T(f'#{i} .cg', tc, opacity=.95, scale=1, duration=.7, ease='back.out(2)')]
    if core: j.append(_qpop(i, 'cc', tc + .15, .4, '50% 50%'))
    return _out(i, a, b, 'r_haihoa', s, j), j, [(t - .2, 'air') for _, t in items[:3]] + [(tc, 'shimmer')]
