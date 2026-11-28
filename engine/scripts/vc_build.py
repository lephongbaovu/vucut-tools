"""vucut · vc_build.py — bộ hàm dựng master.html từ SHOTBOOK (Python), dùng với mẫu vucut_9x16_v4.html.
Mốc viết theo giây của cut/cut.mp4; nếu đã chạy tighten.py thì truyền map.json → shell tự dời mốc (TM) và cue tự dời (M).
    (dựng qua vc.py build: scenes.py dùng V P C R — xem SKILL.md)
    V.finish('build/master.html', 'cues.json', shell='$VC/assets/template/vucut_9x16_v4.html')"""
import json, re
from collections import Counter

H, J, C, FACE, LAYOUT = [], [], [], [], []
RM, T = [], 0.0
AUD = {}
USED, PANELS, GW = [], [], []   # GW: (a, b, đáy y, tên) cửa sổ đồ hoạ → phụ đề tự né
USED_, PANELS_ = None, None   # (t, tên hình) · (t, loại nền) — để chấm ĐA DẠNG
THREAD = {'dlmap', 'journey'}   # hình SỢI CHỈ — được quay lại (callback) mà không tính là lặp
import theme as TH, os, time
THEME = {'name': 'docdo'}
HEAD, SPLITS, SPLIT_RANGES, PIPS = {}, [], [], []   # PIPS: cảnh đồ hoạ có KHUNG NGƯỜI NÓI NHỎ (L_full / L_card)
KIND = {'name': 'phantich'}
# MẶT HIỆU DỤNG: mặt toàn khung 1 · chia đôi .5 · hộp + khung nhỏ .3 · đồ hoạ toàn khung + khung nhỏ .2
FACE_W = {'P': 1, 'SPLIT': .5, 'CARD': .3}
FACE_W_FULL = .2
# khoảng chấp nhận mặt hiệu dụng theo LOẠI video — chỉ CẢNH BÁO khi ra ngoài, không phải đích phải nhắm
BANDS = {'tin': (45, 65, 'tin nóng: vào sự kiện nhanh, nhiều hình'), 'phantich': (50, 72, 'phân tích: thân bài dày dẫn chứng'),
         'nhandinh': (60, 82, 'nhận định / cảnh báo: cần lòng tin, ít hình mà đắt')}
PIP_BOX = (446, 700, 180, 195)   # khung người nói nhỏ x, y, rộng, cao (khung 720×1280) — trong vùng an toàn: phải ≤ 626 < 630, đáy 895 < 1000
PIP_TEXT = (48, 380)             # chữ (.mix) dưới y 560 trong cảnh có khung nhỏ → cột trái x 48–428 (vùng an toàn từ 40), không đè khung
PANEL_H, HEAD_GAP = 604, 40    # mép dưới panel nửa trên (600 + viền 4) · khoảng hở tối thiểu đầu ↔ mép (chừa punch nhẹ)
HIST = os.environ.get('VUCUT_HISTORY') or os.path.join(os.path.expanduser('~'), '.vucut', 'history.json')

def _proj():
    import sys
    return os.path.dirname(os.path.abspath(sys.argv[0] or '.'))

def _hist():
    try: return json.load(open(HIST, encoding='utf-8'))
    except Exception: return []

def _catalog(): return {}   # bộ hình cũ (mg_x, mg_bds) đã gỡ 27/11/2026 — mg_real không chia họ
LIGHT_PANELS = {'dotpanel', 'gridpanel', 'paperpanel', 'diachinh'}
PANEL_KINDS = ('darkpanel', 'dotpanel', 'redpanel', 'gridpanel', 'inkpanel', 'paperpanel', 'blueprint', 'diagpanel', 'goldpanel', 'diachinh', 'betong', 'diahinh')
BOX_STD = 'left:110px;top:180px;width:500px;height:375px'      # hộp đồ hoạ khi panel toàn khung / thẻ người nói
BOX_SPLIT = 'left:150px;top:40px;width:420px;height:315px'     # hộp đồ hoạ khi chia đôi
MIX_SPLIT_TOP = 395                                            # cụm chữ khi chia đôi (không chạm tóc)
SPLIT_DY = 240                                                 # dời người nói xuống trong cảnh chia đôi

def init(T_=None, tighten=None, face=None, theme='auto', topic='', head=None, **kw):
    """face=(fx,fy): tâm mặt trong khung (0–1) từ `vucut.py cut` (facetrack) → tâm của punch/push/slam
    theme: 'auto' (tự chọn, không trùng 2 video gần nhất; topic='quy hoạch'|'đất'|'thị trường'|'biển'… gợi ý) hoặc tên trong theme.THEMES"""
    global T, RM
    h = [x for x in _hist() if x.get('project') != _proj()]
    THEME['name'] = TH.pick([x.get('theme') for x in h], topic) if theme == 'auto' else theme
    if THEME['name'] not in TH.THEMES: raise ValueError(f'theme {theme!r} không có; chọn: {list(TH.THEMES)}')
    recent = set(n for x in h[-3:] for n in x.get('shapes', []))
    F = _catalog(); fresh = [n for n in F if n not in recent and n not in ('chapter', 'cta', 'disclaimer')]
    by = {}
    for n in fresh: by.setdefault(F[n], []).append(n)
    print(f"BỘ MÀU: {THEME['name']} — {TH.THEMES[THEME['name']][5]}" + (f" · 2 video trước: {[x.get('theme') for x in h[-2:]]}" if h else ''))
    if h:
        print(f"SỢI CHỈ video trước: {h[-1].get('thread') or '—'} → lần này chọn sợi chỉ KHÁC")
        print('HÌNH CHƯA DÙNG 3 video gần nhất (ưu tiên):', ' · '.join(f'{k}: {", ".join(v[:4])}' for k, v in by.items()))
    KIND['name'] = kw.get('kind', 'phantich')
    if KIND['name'] not in BANDS: raise ValueError(f"kind={KIND['name']!r} không có; chọn: {list(BANDS)}")
    T = T_ if T_ is not None else kw['T']; RM = json.load(open(tighten, encoding='utf-8'))['removed'] if tighten else []
    for L in (H, J, C, FACE, LAYOUT, USED, PANELS, GW): L.clear()
    AUD.clear()
    if face: J.append(f"VC.face({face[0]},{face[1]});")
    HEAD.clear(); SPLITS.clear(); SPLIT_RANGES.clear(); PIPS.clear()
    if isinstance(head, str) and os.path.exists(head):
        tr = json.load(open(head, encoding='utf-8')); HEAD.update(step=tr.get('step', .2), top=tr.get('top') or [], cy=tr.get('cy') or [], const=tr.get('head'), fy=(tr.get('face') or [0, .38])[1])
    elif isinstance(head, (int, float)): HEAD.update(const=float(head))
    if face and 'fy' not in HEAD: HEAD['fy'] = face[1]

def M(t): return t - sum((e - s) if t >= e else max(0, t - s) for s, e in RM)
def cue(t, s, **k): C.append(dict(t=round(M(t), 3), s=s, **k))

def fixbox(html, box):
    w, h = [int(x.split(':')[1][:-2]) for x in box.split(';')[2:4]]
    return html.replace('left:160px;top:240px;width:400px;height:300px', box).replace('width="400" height="300"', f'width="{w}" height="{h}"')

def mix(i, parts, top, cls='', left=50, out=None, outd=.16, width=None):
    """parts: ('w'|'sm'|'s'|'xl', chữ, mốc) hoặc 'br'. Cảnh có khung người nói nhỏ: chữ dưới y 560 tự sang cột trái (pip_apply)."""
    st = f'left:{left}px;top:{top}px' + (f';width:{width}px' if width else '')
    h = f'<div class="vc mix {cls}" id="{i}" data-check="box" style="{st}">'; times = []
    for p in parts:
        if p == 'br': h += '<span class="br"></span>'; continue
        k, txt, t = p
        card = 'cardmix' in cls; W = (width or (430 if card else 620)) * .95
        fs = _fs(k, txt, card, W)
        h += f'<span class="{ {"w": "w", "sm": "w sm", "s": "s", "xl": "s xl", "g": "s gold", "gxl": "s xl gold"}[k] }"{fs}>{txt}</span>'; times.append(t)
    H.append(h + '</div>'); J.append(f"VC.mix('#{i}',{json.dumps(times)});")
    if out is not None: J.append(f"VC.out('#{i}',{out},{outd});")

def _fs(k, txt, card, W):
    """cỡ chữ inline: ước bề rộng → tự thu nhỏ để KHÔNG xuống dòng ('' = giữ cỡ CSS)"""
    sans = TH.STYLE[THEME['name']]['kw'] == 'sans'
    base = {'w': 32 if card else 40, 'sm': 26 if card else 30, 's': (46 if sans else 56) if card else (66 if sans else 84),
            'g': (46 if sans else 56) if card else (66 if sans else 84), 'xl': (58 if sans else 70) if card else (86 if sans else 108),
            'gxl': (58 if sans else 70) if card else (86 if sans else 108)}[k]
    est = len(txt.replace('\u2063', '')) * base * (.6 if k in ('w', 'sm') else (.74 if sans else .57))   # sans IN HOA rộng hơn serif nghiêng
    return f' style="font-size:{int(base * W / est)}px"' if est > W else ''

def _to_left(h):
    """chuyển 1 cụm .mix sang cột trái cạnh khung người nói nhỏ (x 48–428, cỡ chữ thẻ) — giữ nguyên top"""
    L, Wd = PIP_TEXT
    h = re.sub(r'class="vc mix ([^"]*)"', lambda m: f'class="vc mix {m.group(1)} left cardmix"', h, 1)
    h = re.sub(r'left:\d+px', f'left:{L}px', h, 1)
    h = re.sub(r';width:\d+px', '', h, 1)
    h = re.sub(r'(style="left:\d+px;top:\d+px)', rf'\1;width:{Wd}px', h, 1)
    def one(m):
        c, txt = m.group(1).split(), m.group(3)
        k = ('sm' if 'sm' in c else 'w') if 'w' in c else ('xl' if 'xl' in c else 's')   # g/gxl cùng cỡ s/xl
        return f'<span class="{m.group(1)}"{_fs(k, txt, True, Wd * .95)}>{txt}</span>'
    return re.sub(r'<span class="([^"]+)"( style="font-size:\d+px")?>([^<]*)</span>', one, h)

def pip_apply():
    """KHUNG NGƯỜI NÓI NHỎ: mọi cảnh đồ hoạ (L_full, L_card) tự hiện khung người nói ở góc phải-dưới TRONG vùng an toàn.
    Cảnh liền nhau gộp thành 1 khung (không nháy). Chữ .mix dưới y 560 trong các cảnh đó tự sang cột trái."""
    if not PIPS: return
    W = []
    for a, b in sorted(PIPS):
        if W and a <= W[-1][1] + .15: W[-1][1] = max(W[-1][1], b)
        else: W.append([a, b])
    for a, b in W: J.append(f"VC.pip({a},{b});")
    moved = []
    for k, h in enumerate(H):
        m = re.match(r'<div class="vc mix ([^"]*)" id="([^"]+)"[^>]*style="[^"]*top:(\d+)px', h)
        if not m or 'cardmix' in m.group(1) or int(m.group(3)) < 560: continue
        tm = next((re.search(r"\[([^\]]*)\]", x) for x in J if x.startswith(f"VC.mix('#{m.group(2)}',")), None)
        ts = [float(x) for x in (tm.group(1).split(',') if tm else []) if x.strip() not in ('', 'null')]
        if ts and any(a - .05 <= min(ts) < b for a, b in W):
            H[k] = _to_left(h); moved.append(m.group(2))
    print(f'KHUNG NGƯỜI NÓI NHỎ: {len(W)} lần · ' + ', '.join(f'{a}–{b}' for a, b in W) + (f' · chữ sang cột trái: {", ".join(moved)}' if moved else ''))


def full(res, b=None, extra=()):
    """đồ hoạ toàn khung (mg_real qua P.hinh / V.full) — tự ẩn ở b của nó"""
    html, js, cues = res; H.append(html); J.extend(js); _used(html, js); _gw(html, js)
    for t, s, *_ in cues: cue(t, s)
    for x in extra: J.append(f"VC.cut('#{x}',{b});")

def graphic(res, box=BOX_STD, b=None):
    """mg.build(...) → (html, js, cues[(t,s,db)]); b = mốc ẩn (bỏ trống thì phải nằm trong extra_ids của panel)"""
    html, js, cues = res; H.append(fixbox(html, box)); J.extend(js); _used(html, js); _gw(html, js, box, b)
    if b is not None:
        import re; J.append(f"VC.cut('#{re.search(r'id="([^"]+)"', html).group(1)}',{b});")
    for t, s, db in cues: cue(t, s)


def _bottom(html):
    """đáy (y lớn nhất) của phần hình THẬT trong SVG toàn khung 720×1280 — bỏ nền phủ cả khung"""
    if 'data-mg="dlmap"' in html:
        return 610 if 'height:600' in html or 'half' in html[:400] else (1060 if 'fact' in html else 850)
    ys = []
    num = r'(-?[\d.]+)'
    for tag in re.finditer(r'<(rect|image|text|circle|ellipse|line|path|polygon)\b([^>]*)>', html):
        k, at = tag.group(1), tag.group(2); g = lambda n: (lambda m: float(m.group(1)) if m else None)(re.search(r'\b' + n + r'="' + num + '"', at))
        try:
            if k in ('rect', 'image'):
                y, h, w = g('y') or 0, g('height') or 0, g('width') or 0
                if w >= 700 and h >= 900: continue
                ys.append(y + h)
            elif k == 'text': ys.append((g('y') or 0) + 6)
            elif k == 'circle': ys.append((g('cy') or 0) + (g('r') or 0))
            elif k == 'ellipse': ys.append((g('cy') or 0) + (g('ry') or 0))
            elif k == 'line': ys.append(max(g('y1') or 0, g('y2') or 0))
            elif k == 'polygon':
                m = re.search(r'points="([^"]+)"', at)
                if m: ys += [float(p.split(',')[1]) for p in m.group(1).split() if ',' in p]
            elif k == 'path':
                m = re.search(r'\bd="([^"]+)"', at)
                if not m: continue
                for cmd, args in re.findall(r'([MLCQTSV])([^A-Za-z]*)', m.group(1)):
                    v = [float(x) for x in re.findall(r'-?[\d.]+', args)]
                    ys += v if cmd == 'V' else v[1::2]
        except (ValueError, IndexError): pass
    ys = [y for y in ys if y < 1250]
    return max(ys) if ys else 0

def _gw(html, js, box=None, b=None, a=None):
    m = re.search(r'data-mg="(\w+)"', html); jj = ' '.join(js[:4])
    ta = re.search(r",\{opacity:1\},([\d.]+)\)", jj); tb = re.search(r",\{opacity:0\},([\d.]+)\)", jj)
    a = a if a is not None else (float(ta.group(1)) if ta else None)
    b = b if b is not None else (float(tb.group(1)) if tb else (a + 3 if a is not None else None))
    if a is None: return
    if box:
        d = dict(x.split(':') for x in box.split(';')); bot = int(d['top'][:-2]) + int(d['height'][:-2])
    else: bot = _bottom(html)
    mi = re.search(r'id="([^"]+)"', html)
    GW.append((a, b, bot, m.group(1) if m else '?', mi.group(1) if mi else ''))

def _mix_h(h):
    """ước chiều cao cụm .mix theo số dòng + cỡ chữ lớn nhất mỗi dòng"""
    lines = h.split('<span class="br"></span>'); tot = 0
    for L in lines:
        big = re.search(r'class="s', L); fs = [int(x) for x in re.findall(r'font-size:(\d+)px', L)]
        tot += (max(fs) if fs else (84 if big else 40)) * (1.0 if big else 1.2) + 6
    return int(tot) + 10

def fit_split():
    """CẢNH CHIA ĐÔI — nội dung panel không bao giờ nằm dưới đầu:
    vùng nội dung = từ đỉnh panel tới (đỉnh đầu sau khi dời − 18) [không nổi: tới 588].
    Cụm chữ trên panel dồn xuống sát đáy vùng; đồ hoạ thu nhỏ (gốc giữa-trên) vừa phần còn lại."""
    for sa, sb, dy, ht, known, fl in SPLITS:
        zone = min(588, int(ht * 1280 + dy - 18)) if fl else 588
        mixes = []
        for k, h in enumerate(H):
            m = re.match(r'<div class="vc mix [^"]*" id="([^"]+)"[^>]*style="[^"]*top:(\d+)px', h)
            if not m or int(m.group(2)) >= 600: continue
            tm = next((re.search(r"\[([^\]]*)\]", x) for x in J if x.startswith(f"VC.mix('#{m.group(1)}',")), None)
            ts = [float(x) for x in (tm.group(1).split(',') if tm else []) if x.strip() not in ('', 'null')]
            if ts and sa - .05 <= min(ts) < sb: mixes.append((k, m.group(1), int(m.group(2)), _mix_h(h)))
        lim = zone
        for k, mid, top, mh in mixes:
            new = max(120, zone - mh)
            if new != top:
                H[k] = H[k].replace(f'top:{top}px', f'top:{new}px', 1); print(f'  SPLIT {sa}–{sb}: chữ {mid} {top}→{new} (trên đỉnh đầu)')
            lim = min(lim, new - 10)
        for a, b, bot, n, gid in GW:
            if not gid or a >= sb - .05 or b <= sa + .05 or bot <= lim: continue
            sc = round(max(.4, lim / bot), 3)
            J.append(f"tl.set('#{gid}',{{scale:{sc},transformOrigin:'50% 0%'}},0);")
            print(f'  SPLIT {sa}–{sb}: thu hình {n} ×{sc} (đáy {bot:.0f} → {lim})' + (' ⚠ hình còn nhỏ — bớt chữ hoặc dùng toàn khung' if sc < .5 else ''))

def place_mix():
    """PHỤ ĐỀ TỰ NÉ: cụm .mix đang hiện cùng lúc với đồ hoạ mà nằm đè lên phần hình → đẩy xuống dưới đáy hình 24 px (tối đa 860).
    Bỏ qua chữ thẻ (cardmix) và chữ đặt chủ ý ở nửa trên (top < 500, vd cảnh chia đôi)."""
    moved = []
    for k, h in enumerate(H):
        m = re.match(r'<div class="vc mix ([^"]*)" id="([^"]+)"[^>]*style="[^"]*top:(\d+)px', h)
        if not m or 'cardmix' in m.group(1): continue
        mid, top = m.group(2), int(m.group(3))
        if top < 500: continue
        tm = next((re.search(r"\[([^\]]*)\]", x) for x in J if x.startswith(f"VC.mix('#{mid}',")), None)
        if not tm or not tm.group(1).strip(): continue
        times = [float(x) for x in tm.group(1).split(',') if x.strip() not in ('', 'null')]
        to = next((float(re.search(r",([\d.]+),", x).group(1)) for x in J if x.startswith(f"VC.out('#{mid}',")), max(times) + 2.5)
        hit = [(bot, n) for a, b, bot, n, _ in GW if a < to - .05 and b > min(times) + .05 and bot + 24 > top]
        if not hit: continue
        bot, n = max(hit); new = min(int(bot + 24), 860)
        if new <= top: continue
        H[k] = h.replace(f'top:{top}px', f'top:{new}px', 1); moved.append(f'{mid} {top}→{new} (né {n})')
        if bot + 24 > 860: print(f'  ⚠ phụ đề {mid}: hình {n} xuống tới y {bot:.0f} — chữ chỉ hạ được tới 860, rút gọn chữ hoặc dùng CARD')
    if moved: print('PHỤ ĐỀ TỰ NÉ:', ' · '.join(moved))

def _used(html, js):
    m = re.search(r'data-mg="(\w+)"', html); t = re.search(r",\{opacity:1\},([\d.]+)\)", ' '.join(js[:3]))
    USED.append((float(t.group(1)) if t else 0.0, m.group(1) if m else '?'))

def variety():
    """chấm ĐA DẠNG B-roll: lặp hình, lặp họ, lặp nền, độ phủ màu vàng → in cảnh báo + gợi ý"""
    try:
        FAMILY = _catalog()
    except ImportError:
        FAMILY = {}
    U = sorted((M(t), n) for t, n in USED); P = sorted((M(t), k) for t, k in PANELS); warn = []
    for k in range(len(U)):
        for q in range(k):
            if U[k][1] == U[q][1] and U[k][1] not in THREAD and U[k][0] - U[q][0] < 20: warn.append(f'hình "{U[k][1]}" lặp lại sau {U[k][0] - U[q][0]:.0f} s (cần ≥ 20 s)')
    fam = [FAMILY.get(n, n) for _, n in U]
    for k in range(1, len(fam)):
        if fam[k] == fam[k - 1]: warn.append(f'2 hình liền cùng họ "{fam[k]}" ở {U[k][0]:.1f} s — đổi sang họ khác')
    for k in range(1, len(P)):
        if P[k][1] == P[k - 1][1]: warn.append(f'2 nền liền cùng loại "{P[k][1]}" ở {P[k][0]:.1f} s')
    TT = M(T); per = max(1, TT / 30)
    nf, nb, nn = len(set(fam)), len(set(k for _, k in P)), len(set(n for _, n in U))
    if U and nf < min(len(U), 3 * per): warn.append(f'chỉ {nf} họ hình / {TT:.0f} s — mục tiêu ≥ {min(len(U), round(3 * per))} họ')
    if P and nb < min(len(P), round(3 * per)): warn.append(f'chỉ {nb} loại nền / {TT:.0f} s — mục tiêu ≥ {min(len(P), round(3 * per))}')
    gold = sum(1 for _, k in P if k in ('goldpanel', 'inkpanel', 'blueprint')) + sum(1 for x in H if 'var(--g)' in x or 'gold' in x)
    print(f'ĐA DẠNG: {len(U)} hình · {nn} loại · {nf} họ {sorted(set(fam))} · {len(P)} nền / {nb} loại · điểm nhấn vàng {gold}')
    if not gold and U: warn.append('chưa có điểm nhấn VÀNG nào — thêm ở chỗ giá trị / kết quả / đích đến')
    for w in dict.fromkeys(warn): print('  ⚠', w)
    if not warn and U: print('  ✓ không lặp nhàm')

# ---- bố cục người nói (v6 talking-head: mặt 60 % / B-roll 40 %; P = mặt, SPLIT/CARD = ½ mặt + ½ B-roll)
def L_full(a, b, name):
    """cảnh đồ hoạ — LUÔN kèm khung người nói nhỏ (PIP_BOX, vùng an toàn) do pip_apply() gắn lúc finish"""
    LAYOUT.append((name, a, b)); PIPS.append((a, b))
def L_person(a, b): FACE.append((a, b)); LAYOUT.append(('P', a, b))
def _win(key, a, b):
    tp = HEAD.get(key) or []
    if not tp: return []
    st = HEAD['step']; i0, i1 = int(M(a) / st), int(M(b) / st) + 1
    return tp[max(0, i0):max(i0 + 1, i1)]

def _head_top(a, b):
    """đỉnh đầu cao nhất + tâm mặt cao nhất (tỉ lệ khung) trong [a,b] (giây cut → giây video cuối)"""
    seg, cy = _win('top', a, b), _win('cy', a, b)
    fy = min(cy) if cy else HEAD.get('fy', .38)
    if seg: return min(seg), fy, True
    return (HEAD['const'], fy, True) if HEAD.get('const') is not None else (.08, fy, False)

HEAD_POKE = 110   # đầu nổi: phần đầu (tóc → trán) nhô vào panel bao nhiêu px; mắt/mặt luôn ở DƯỚI mép panel

def L_split(a, b, dy=None, float_=True):
    """chia đôi: panel half=True ở trên (y 0–600), người nói ở dưới.
    MẶC ĐỊNH float_=True — ĐẦU NỔI: panel CHÌM SAU phần đầu (tách nền build/cut, render tự chạy), dy tự tính theo đỉnh đầu + tâm mặt
    thật (facetrack): đầu nhô vào panel ~HEAD_POKE px, mặt vẫn dưới mép; đồ hoạ + chữ trên panel tự dồn lên VÙNG TRÊN ĐẦU → đầu không che nội dung.
    float_=False: không nổi — dời hẳn người nói xuống dưới mép panel (khi không tách nền được)."""
    ht, fy, known = _head_top(a, b)
    if dy is None:
        if float_: dy = round(max(PANEL_H - HEAD_POKE - ht * 1280, PANEL_H + 30 - fy * 1280, 120))
        else: dy = round(max(PANEL_H + HEAD_GAP - ht * 1280, 160))
    if not float_ and dy > 640:
        print(f'  ⚠ SPLIT {a}–{b}: đầu người nói quá cao trong khung (đỉnh y≈{ht * 1280:.0f}) → cần dời {dy}px, mặt sẽ sát đáy. Dùng V.L_card hoặc giữ mặt toàn khung ở câu này.')
        dy = 640
    SPLITS.append((a, b, dy, ht, known, float_))
    if float_: SPLIT_RANGES.append((a, b))
    FACE.append((a, b)); LAYOUT.append(('SPLIT', a, b)); J.append(f"VC.split({a},{b},{dy},{'true' if float_ else 'false'});")
def L_card(a, b):
    """đồ hoạ trong hộp BOX_STD + khung người nói nhỏ (cùng khung với L_full); chữ tự sang cột trái"""
    FACE.append((a, b)); LAYOUT.append(('CARD', a, b)); PIPS.append((a, b))

# ---- chuyển cảnh: wipe (thanh đỏ quét) · whip (vuốt nhanh) · zoom (zoom xuyên) · flash · glitch
def TR(kind, t):   # 27/11/2026: bỏ wipe/whip/zoom/flash/glitch — chuyển cảnh mặc định CẮT GỌN do vc.py lo
    return

def hook(text, t=0.05, out=1.7, top=60, step=.063, gold=False, size=None):
    """HOOK đầu video: chữ IN HOA gradient gõ từng ký tự ở đỉnh khung + tick mỗi chữ (≤ 1 s) + hit khi đủ chữ.
    Kênh phân tích: hook là MỐC TIN / CON SỐ / CÂU HỎI (vd 'THÔNG XE?', '117,5 KM', 'QUY HOẠCH MỚI') — không giật gân."""
    k = len([x for x in H if 'class="vc hook' in x])
    if size is None and len(text) * 118 * .66 > 660: size = int(660 / (len(text) * .66))   # tự thu cho vừa khung
    hid = f'hook{k}'; st = f'left:0;right:0;width:720px;top:{top}px;text-align:center' + (f';font-size:{size}px' if size else '')
    H.append(f'<div class="vc hook{" gold" if gold else ""}" id="{hid}" data-check="box" style="{st}">{text}</div>')
    J.append(f"VC.hook('#{hid}',{t},{step});"); J.append(f"VC.out('#{hid}',{out},.16);")
    n = len(text.replace(' ', ''))
    for q in range(n):
        if t + q * step <= 1.0: cue(t + q * step, 'tick')
    cue(t + n * step + .05, 'hit')

def disclaimer(a, b, text='Thông tin tham khảo · không phải khuyến nghị đầu tư'):
    """dòng miễn trừ nhỏ ở chân khung (y≈950) — dùng cho video có giá, dự báo, nhận định thị trường"""
    H.append(f'<div class="vc" data-mg="disclaimer" id="dsc{len(H)}" style="left:0;right:0;top:936px;width:720px;text-align:center;z-index:30">'
             f'<span style="display:inline-block;padding:7px 16px;border-radius:9px;background:rgba(0,0,0,.55);font-family:VCB6;font-weight:600;'
             f'font-size:17px;color:rgba(255,255,255,.85)">{text}</span></div>')
    J.append(f"tl.set('#dsc{len(H) - 1}',{{opacity:1}},{a}); tl.set('#dsc{len(H) - 1}',{{opacity:0}},{b});")

def progress(a, b, marks):
    """thanh tiến độ 3 nấc ở đỉnh khung cho phần liệt kê; marks = mốc tô từng nấc"""
    J.append(f"tl.set('#prog',{{opacity:1}},{a}); tl.set('#prog',{{opacity:0}},{b}); tl.set('#prog i b',{{scaleX:0,transformOrigin:'0 50%'}},0);")
    for k, t in enumerate(marks): J.append(f"tl.to('#prog i:nth-child({k+1}) b',{{scaleX:1,duration:.4}},{t});")

def audio(impacts=(), muffle=(), duck=()):
    """kế hoạch nhạc (mốc theo giây cut/cut.mp4 như mọi hàm khác — tự dời sang giây video cuối):
    impacts = mốc impact nhạc (hook, panel đỏ, chương, quan điểm, cao trào, CTA)
    muffle  = [(a,b)] đoạn nhạc NGHẸT (vấn đề, nút thắt, câu hỏi mở)
    duck    = [t] câu ĐẮT — nhạc tắt 0.55 s trước t. finish() ghi audio.json cạnh cues.json → `vucut.py audio` đọc."""
    AUD.update(impacts=[round(M(t), 3) for t in impacts], muffle=[[round(M(a), 3), round(M(b), 3)] for a, b in muffle],
               duck=[[round(max(0, M(t) - .55), 3), round(M(t), 3)] for t in duck])

def finish(out_html, out_cues, shell):
    import os
    if AUD: json.dump(AUD, open(os.path.join(os.path.dirname(os.path.abspath(out_cues)), 'audio.json'), 'w', encoding='utf-8'), indent=1)
    J.append(f"(function(){{var r=7;for(var t=0;t<{T};t+=1/15){{r=(r*9301+49297)%233280;tl.set('#grain',{{backgroundPosition:(r%256)+'px '+((r*7)%256)+'px'}},t);}}}})();")
    J.append(f"VC.end({T});")
    pip_apply(); fit_split(); place_mix()
    json.dump([[round(M(a), 3), round(M(b), 3)] for a, b in SPLIT_RANGES], open(os.path.join(os.path.dirname(os.path.abspath(out_cues)), 'splits.json'), 'w'))
    J.insert(0, f"VC.style({json.dumps(TH.STYLE[THEME['name']])});")
    tpl = open(shell, encoding='utf-8').read()
    th = THEME['name']
    if th != 'docdo':   # bộ màu: chép vucut.css → lib/vucut_<bộ>.css đã đổi màu, và đổi màu luôn phần tử dựng
        lib = os.path.join(os.path.dirname(os.path.abspath(out_html)), 'lib')
        src = os.path.join(lib, 'vucut.css')
        if not os.path.exists(src): src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'vucut.css')
        os.makedirs(lib, exist_ok=True)
        open(os.path.join(lib, f'vucut_{th}.css'), 'w', encoding='utf-8').write(TH.apply(open(src, encoding='utf-8').read(), th))
        tpl = tpl.replace('lib/vucut.css', f'lib/vucut_{th}.css')
        H[:] = [TH.apply(x, th) for x in H]; J[:] = [TH.apply(x, th) for x in J]
    html = (tpl.replace('<!--ROOT-->', '\n'.join(H)).replace('//JS', '\n'.join(J))
               .replace('__T__', str(round(M(T), 3))).replace('__RM__', json.dumps(RM)))
    open(out_html, 'w', encoding='utf-8').write(html)
    C.sort(key=lambda c: c['t']); json.dump(C, open(out_cues, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    TT = M(T); LS = sorted(LAYOUT, key=lambda x: x[1])
    wf = lambda n: FACE_W.get(n, FACE_W_FULL)
    json.dump([dict(canh=n, a=round(M(a), 2), b=round(M(b), 2)) for n, a, b in LS],
              open(os.path.join(os.path.dirname(os.path.abspath(out_cues)), 'shots.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    seq = [x[0] for x in LS]; du = [M(b) - M(a) for n, a, b in LS]
    rep = [f'{seq[k]}' for k in range(1, len(seq)) if seq[k] == seq[k-1] and seq[k] != 'P']
    def eff(x0, x1):   # % mặt hiệu dụng trong [x0, x1] (giây video cuối)
        tot = sum(max(0, min(M(b), x1) - max(M(a), x0)) for n, a, b in LS)
        f = sum(max(0, min(M(b), x1) - max(M(a), x0)) * wf(n) for n, a, b in LS)
        return 100 * f / tot if tot else 0
    lo, hi, why = BANDS[KIND['name']]; E = eff(0, TT)
    full = 100 * sum((M(b) - M(a)) for n, a, b in LS if n == 'P') / TT
    gap = max([0] + [TT - sum(du)])
    print(f"MẶT HIỆU DỤNG {E:.0f}% (mặt toàn khung {full:.0f}%) · loại '{KIND['name']}' chấp nhận {lo}–{hi}% — {why}"
          + ('' if lo <= E <= hi else f"  ⚠ ngoài khoảng → xem lại câu có `vì sao` yếu nhất (không ép cho đủ số)")
          + (f' · chưa gán bố cục {gap:.1f} s' if gap > .3 else ''))
    acts = [('mở', 0, .15), ('thân', .15, .7), ('cao trào', .7, .88), ('kết', .88, 1)]
    print('  ĐƯỜNG CONG: ' + ' → '.join(f'{n} {eff(TT * x, TT * y):.0f}%' for n, x, y in acts)
          + '  (thường: mở cao → thân thấp → kết cao; khác đi được nếu SHOTBOOK có lý do)')
    run_p, run_g, mp_, mg_ = 0, 0, 0, 0     # run_p: liền KHÔNG có mặt toàn khung · run_g: liền KHÔNG có hình
    for n, a, b in LS:
        d = M(b) - M(a)
        if n == 'P': run_p, run_g = 0, run_g + d
        else: run_p, run_g = run_p + d, 0
        mp_, mg_ = max(mp_, run_p), max(mg_, run_g)
    if mp_ > 12: print(f'  ⚠ mặt toàn khung vắng liền {mp_:.1f} s (> 12) → chen 1 nhịp mặt ≥ 1.7 s để giữ kết nối')
    if mg_ > 15 and KIND['name'] != 'nhandinh': print(f'  ⚠ {mg_:.1f} s liền không có hình (> 15) → người xem chỉ nghe; thêm 1 hình cho ý đang nói')
    if du:
        print(f'Cảnh TB {sum(du)/len(du):.2f} s (mục tiêu 2.6–3.2) · ngắn nhất {min(du):.2f} s (≥ 0.9) · dài nhất {max(du):.2f} s')
        flat = [k for k in range(2, len(du)) if max(du[k-2:k+1]) - min(du[k-2:k+1]) <= .3]
        if flat: print('Cảnh liền đều nhau (±0.3 s) — đổi độ dài cho có nhịp:', [round(M(LS[k][1]), 2) for k in flat])
        long_ = [round(M(a), 2) for (n, a, b), d in zip(LS, du) if (n == 'P' and d > 6.5) or (n not in FACE_W and d > 5.2)]
        if long_: print('Cảnh quá dài (mặt > 6.5 s / B-roll > 5.2 s):', long_)
    print('Bố cục:', dict(Counter(seq)), '· lặp liền:', rep or 'không')
    variety()
    for a, b, dy, ht, known, fl in SPLITS:
        top = ht * 1280 + dy
        zs = [float(m.group(2)) for x in J for m in [re.match(r"VC\.(punch|slam)\(([\d.]+)", x)] if m and a <= float(m.group(2)) < b]
        msg = (f'SPLIT {a}–{b}: dời {dy}px · ' + (f'ĐẦU NỔI: panel chìm sau đầu (đỉnh đầu y≈{top:.0f}, nội dung panel ở trên y {min(588, top - 18):.0f}) · tách nền tự chạy khi render'
               if fl else f'đỉnh đầu y≈{top:.0f} ' + ('✓ dưới mép panel' if top >= PANEL_H + 20 else '⚠ SÁT/ĐÈ mép panel'))
               + ('' if known else ' · (chưa có facetrack → ước lượng, soát qc/sheet)'))
        print(('  ' if top >= PANEL_H + 20 or fl else '  ⚠ ') + msg + (f' · ⚠ punch/slam trong cảnh chia đôi ở {zs} → đầu phóng lên mép panel, bỏ đi' if zs else ''))
    print(' → '.join(seq))
    remember(out_html)

def remember(out_html):
    """ghi video này vào lịch sử (~/.vucut/history.json) + so với 3 video trước: lặp hình / lặp sợi chỉ / lặp bộ màu"""
    names = [n for _, n in sorted(USED)]
    thr = next((n for n in names if n in THREAD and names.count(n) >= 2), next((n for n in names if n in THREAD), ''))
    proj = _proj()
    h = [x for x in _hist() if x.get('project') != proj]
    cur = set(names) - {'chapter', 'cta', 'disclaimer'}
    for x in h[-3:]:
        same = cur & set(x.get('shapes', []))
        if cur and len(same) / len(cur) > .5:
            print(f"  ⚠ GIỐNG video {os.path.basename(x['project'])} ({x.get('date', '')}): {len(same)}/{len(cur)} hình trùng {sorted(same)} — thay ≥ {len(same) - len(cur) // 2} hình bằng hình CHƯA DÙNG (init đã in)")
    if h and thr and thr == h[-1].get('thread'): print(f"  ⚠ sợi chỉ '{thr}' trùng video trước — đổi sang sợi chỉ khác")
    if h and THEME['name'] == h[-1].get('theme'): print(f"  ⚠ bộ màu '{THEME['name']}' trùng video trước")
    h.append(dict(project=proj, date=time.strftime('%Y-%m-%d'), theme=THEME['name'], thread=thr, shapes=sorted(cur),
                  panels=sorted(set(k for _, k in PANELS))))
    try:
        os.makedirs(os.path.dirname(HIST), exist_ok=True); json.dump(h[-30:], open(HIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f"Lịch sử: {len(h)} video · bộ màu {THEME['name']} · sợi chỉ {thr or '—'}")
    except OSError as e: print('  (không ghi được lịch sử:', e, ')')
