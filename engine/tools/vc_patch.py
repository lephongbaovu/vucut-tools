"""vucut-tools · vc_patch.py — lớp chỉnh vc_build cho kênh anh Vũ (tách từ mg_nganh.py ngày 27/11/2026, bỏ bộ hình cũ).
Import TRƯỚC V.init: màu chữ phụ đề [l:] xanh lá, hook tự thu cỡ/green, nền gradient on-*, TỰ CĂN đồ hoạ vào vùng an toàn,
ngôn ngữ dựng xoay vòng, ghi lịch sử dự án. Không chứa hình."""
import math, random, re, io, json, os, tempfile, contextlib
import vc_build as V, theme as TH
SAFE = dict(top=120, bottom=1000, left=40, right=680, rail_x=630, rail_y=560)   # vùng chữ an toàn TikTok + Reels (khung 720×1280)
STYLES = ('docdo', 'thep', 'bazan', 'reu', 'muc', 'bien')                         # NGÔN NGỮ DỰNG xoay vòng (màu luôn đỏ·xanh·vàng)
_ST0 = {k: dict(v) for k, v in TH.STYLE.items()}; _CUR = {'style': 'docdo'}
# NỀN MÀU GRADIENT ĐIỆN ẢNH (v4 · thay 3 nền thuần): đỏ rượu vang · xanh ngọc lục bảo · vàng sâm panh — cùng 1 cấu trúc:
#   đèn key góc trên-trái + gradient chéo đậm dần xuống đáy gần đen + vân lụa mờ + tối viền; con: quầng key trôi chậm + vệt sáng quét 1 lần
#   *glow = biến thể nền TỐI + hào quang + tia (đỏ / xanh lá / vàng). Chữ trên nền màu tự thêm on-red / on-green / on-gold (từ khoá cùng màu nền → kem trắng)
_LX = ('position:absolute;inset:0;z-index:6;opacity:0;overflow:hidden;background-color:#050403')
_GL = lambda c1, c2, c3: (f'position:absolute;inset:0;z-index:6;opacity:0;overflow:hidden;background:#070605;background-image:radial-gradient(55% 38% at 50% 42%,{c1} 0%,{c2} 45%,rgba(0,0,0,0) 75%),'
                          f'repeating-conic-gradient(from 0deg at 50% 42%,{c3} 0deg 4deg,rgba(0,0,0,0) 4deg 15deg)')
CSS = ('<style>:root{--vc-grad:linear-gradient(180deg,#FFFFFF 0%,#FFFFFF 30%,#F6C4BE 56%,#D8343B 80%,#97101A 100%);'
       '--vc-gsh:blur(0px) drop-shadow(0px 2px 4px rgba(0,0,0,.6)) drop-shadow(0px 0px 16px rgba(150,16,26,.45));'
       '--l:#2DB866;--vc-grad-green:linear-gradient(180deg,#FFFFFF 0%,#FFFFFF 30%,#BFEBD0 56%,#34B46C 80%,#0F6B3A 100%);'
       '--vc-gsh-green:blur(0px) drop-shadow(0px 2px 4px rgba(0,0,0,.6)) drop-shadow(0px 0px 16px rgba(15,107,58,.5));'
       '--vc-grad-cream:linear-gradient(180deg,#FFFFFF 0%,#FFFFFF 48%,#F6EBD3 100%)}'
       '.mix .s.green,.hook.green .ch{background-image:var(--vc-grad-green);filter:var(--vc-gsh-green)}'
       '.mix.on-light .s.green{background-image:linear-gradient(180deg,#2DB866 0%,#137A3E 60%,#0A4A26 100%);filter:none}'
       f'.redpanel,.greenpanel,.goldpanel{{{_LX}}}'
       '.redpanel{background-image:radial-gradient(70% 42% at 24% 14%,rgba(255,138,122,.34) 0%,rgba(255,138,122,0) 70%),linear-gradient(168deg,#8C141B 0%,#5C0B11 34%,#2B0508 66%,#0D0203 100%);'
       '--lx-k:rgba(255,120,100,.55);--lx-s:rgba(255,205,190,.16)}'
       '.greenpanel{background-image:radial-gradient(70% 42% at 24% 14%,rgba(150,240,190,.26) 0%,rgba(150,240,190,0) 70%),linear-gradient(168deg,#167A49 0%,#0C5131 34%,#052A19 66%,#010D07 100%);'
       '--lx-k:rgba(120,240,170,.42);--lx-s:rgba(210,255,225,.13)}'
       '.goldpanel{background-image:radial-gradient(70% 42% at 24% 14%,rgba(255,232,180,.36) 0%,rgba(255,232,180,0) 70%),linear-gradient(168deg,#B98B42 0%,#7C5821 30%,#3F2B0E 62%,#120B03 100%);'
       '--lx-k:rgba(255,236,180,.6);--lx-s:rgba(255,246,220,.22)}'
       '.redpanel:before,.greenpanel:before,.goldpanel:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(118deg,rgba(255,255,255,.022) 0 1px,rgba(255,255,255,0) 1px 7px);'
       '-webkit-mask:linear-gradient(180deg,#000 0%,rgba(0,0,0,.35) 45%,transparent 75%);mask:linear-gradient(180deg,#000 0%,rgba(0,0,0,.35) 45%,transparent 75%)}'
       '.redpanel:after,.greenpanel:after,.goldpanel:after{content:"";position:absolute;inset:0;z-index:2;background:radial-gradient(130% 85% at 50% 40%,rgba(0,0,0,0) 48%,rgba(0,0,0,.62) 100%),linear-gradient(180deg,rgba(0,0,0,0) 62%,rgba(0,0,0,.38) 100%)}'
       '.lx-key{position:absolute;left:-30%;top:-22%;width:110%;height:70%;border-radius:50%;filter:blur(40px);opacity:.55;background:radial-gradient(closest-side,var(--lx-k) 0%,rgba(0,0,0,0) 100%)}'
       '.lx-sheen{position:absolute;left:-40%;top:-20%;width:30%;height:140%;transform:rotate(18deg);opacity:0;filter:blur(26px);background:linear-gradient(90deg,rgba(255,255,255,0) 0%,var(--lx-s) 50%,rgba(255,255,255,0) 100%)}'
       '.redpanel.half,.greenpanel.half,.goldpanel.half,.redglow.half,.greenglow.half,.goldglow.half{border-bottom:2px solid rgba(232,201,135,.7)}'
       f'.redglow{{{_GL("rgba(200,40,50,.40)", "rgba(110,12,20,.18)", "rgba(255,170,160,.05)")}}}'
       f'.greenglow{{{_GL("rgba(45,184,102,.40)", "rgba(19,122,62,.18)", "rgba(150,232,180,.06)")}}}'
       f'.goldglow{{{_GL("rgba(201,164,92,.42)", "rgba(138,106,46,.18)", "rgba(232,201,135,.06)")}}}'
       '.redglow:after,.greenglow:after,.goldglow:after{content:"";position:absolute;inset:0;background:radial-gradient(120% 90% at 50% 45%,rgba(0,0,0,0) 45%,rgba(0,0,0,.65) 100%)}'
       '.mix.on-red .w,.mix.on-green .w,.mix.on-gold .w{text-shadow:0 2px 6px rgba(0,0,0,.55),0 0 22px rgba(0,0,0,.35)}'
       '.mix.on-red .s:not(.gold):not(.green),.mix.on-green .s.green,.mix.on-gold .s.gold,.stack .w,.stack .s,.stack .q{background-image:var(--vc-grad-cream);'
       'filter:blur(0px) drop-shadow(0px 2px 6px rgba(0,0,0,.5)) drop-shadow(0px 0px 18px rgba(0,0,0,.25))}'
       '.mix.on-red .s.gold,.mix.on-red .s.green,.mix.on-green .s.gold,.mix.on-green .s:not(.gold):not(.green){filter:blur(0px) drop-shadow(0px 2px 5px rgba(0,0,0,.7)) drop-shadow(0px 0px 12px rgba(0,0,0,.35))}'
       '.mix.on-gold .s:not(.gold),.mix.on-gold .s.green{filter:blur(0px) drop-shadow(0px 2px 5px rgba(0,0,0,.75)) drop-shadow(0px 0px 10px rgba(0,0,0,.45))}</style>')
V.PANEL_KINDS = tuple(V.PANEL_KINDS) + ('greenpanel', 'redglow', 'greenglow', 'goldglow')
LUX = []                                                   # (a, b, kind) nền màu gradient → chữ tự on-*
_ON = {'redpanel': 'on-red', 'greenpanel': 'on-green', 'goldpanel': 'on-gold'}
_panel0 = V.panel
def _panel(pid, kind, a, b, light=None, seed=0, extra_ids=(), half=False):
    _panel0(pid, kind, a, b, light, seed, extra_ids, half)
    if kind not in _ON: return
    LUX.append((a, b, kind)); tag = f'id="{pid}"></div>'
    for k in range(len(V.H) - 1, -1, -1):
        if tag in V.H[k]: V.H[k] = V.H[k].replace(tag, f'id="{pid}"><i class="lx-key"></i><i class="lx-sheen"></i></div>'); break
    d = b - a; sw = min(2.6, max(1.2, d * .7))
    V.J.append(f"tl.fromTo('#{pid} .lx-key',{{x:-30,y:-20,scale:1}},{{x:70,y:40,scale:1.12,duration:{d:.2f},ease:'sine.inOut'}},{a:.3f});"
               f"tl.fromTo('#{pid} .lx-sheen',{{x:0,opacity:0}},{{x:1150,duration:{sw:.2f},ease:'power2.inOut'}},{a + .12:.3f});"
               f"tl.to('#{pid} .lx-sheen',{{opacity:.85,duration:{sw * .3:.2f},yoyo:true,repeat:1,ease:'sine.inOut'}},{a + .12 + sw * .2:.3f});")
V.panel = _panel
V.disclaimer = lambda *a, **k: print('(bỏ qua V.disclaimer — kênh không dùng dòng miễn trừ)')

_fin0 = V.finish
def _finish(out_html, out_cues, shell):
    t0 = {m.group(1): min(json.loads(m.group(2)) or [0]) for x in V.J for m in re.finditer(r"VC\.mix\('#([^']+)',(\[[^\]]*\])\)", x)}
    for k, h in enumerate(V.H):
        m = re.match(r'<div class="vc mix ([^"]*)" id="([^"]+)"', h)
        if not m or 'on-' in m.group(1) or 'cardmix' in m.group(1) or m.group(2) not in t0: continue
        for a, b, kind in LUX:
            if a - .05 <= t0[m.group(2)] < b:
                V.H[k] = h.replace(m.group(0), f'<div class="vc mix {(m.group(1) + " " + _ON[kind]).strip()}" id="{m.group(2)}"', 1); break
    tpl = open(shell, encoding='utf-8').read().replace('<!--ROOT--> (', 'ROOT (').replace('//JS (', 'JS (')   # ghi chú đầu khung có tên mốc → bị chèn 2 lần
    sh = os.path.join(tempfile.gettempdir(), 'vucut_khung.html'); open(sh, 'w', encoding='utf-8').write(tpl)
    _fin0(out_html, out_cues, sh)
V.finish = _finish


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): r = fn(*a, **k)
    return r, buf.getvalue().splitlines()


_init0 = V.init
def _init(*a, **k):
    k['theme'] = 'docdo'; k.pop('topic', None)
    _, out = _quiet(_init0, *a, **k)
    h = [x for x in V._hist() if x.get('project') != V._proj()]
    last = h[-1].get('style') if h else None; pool = [x for x in STYLES if x != last]
    _CUR['style'] = pool[len(h) % len(pool)]; TH.STYLE['docdo'] = dict(_ST0[_CUR['style']])
    for ln in out:
        if 'SỢI CHỈ' in ln: continue
        if ln.startswith('BỘ MÀU'): ln = f"MÀU: đỏ · xanh lá · vàng · NGÔN NGỮ DỰNG lần này: {_CUR['style']} {TH.STYLE['docdo']} (video trước: {last or '—'})"
        print(ln)
    LUX.clear(); V.H.append(CSS)
V.init = _init

_mix0 = V.mix
def _mix(i, parts, top, cls='', left=None, out=None, outd=.16, width=None):
    card = 'cardmix' in cls
    if left is None: left = 48 if card else 60
    if width is None and not card: width = 540
    P = [((('g', 'gxl')[p[0] == 'lxl']), '⁣' + p[1], p[2]) if p != 'br' and p[0] in ('l', 'lxl') else p for p in parts]
    _mix0(i, P, top, cls, left, out, outd, width)
    V.H[-1] = re.sub('class="s( xl)? gold"([^>]*)>⁣', r'class="s\1 green"\2>', V.H[-1])
V.mix = _mix

_hook0 = V.hook
def _hook(text, t=.05, out=1.7, top=None, step=.063, gold=False, size=None, green=False):
    if size is None and len(text) * 118 * .66 > 600: size = int(600 / (len(text) * .66))
    _hook0(text, t, out, max(SAFE['top'] + 12, top or 0), step, gold and not green, size)
    if green: V.H[-1] = V.H[-1].replace('class="vc hook', 'class="vc hook green', 1)
V.hook = _hook


def _tw(t, size): return len(t) * size * (.66 if t.upper() == t else .56)
def _fit(html):
    if 'viewBox="0 0 720 1280"' not in html or 'data-mg="dlmap"' in html: return html
    box = []
    for m in re.finditer(r'<text\b([^>]*)>([^<]*)</text>', html):
        at, tx = m.group(1), m.group(2).strip()
        g = lambda n, d=0: float((re.search(r'\b' + n + r'="(-?[\d.]+)"', at) or [0, d])[1])
        if not tx: continue
        x, y, sz = g('x'), g('y'), g('font-size', 20); w = _tw(tx, sz); an = (re.search(r'text-anchor="(\w+)"', at) or [0, 'start'])[1]
        x0 = x - w / 2 if an == 'middle' else (x - w if an == 'end' else x)
        box.append((x0, y - sz * .8, x0 + w, y + sz * .25))
    if not box: return html
    top = min(q[1] for q in box); dy = max(0, SAFE['top'] + 24 - top); sc = 1.0
    for _ in range(3):
        f = lambda v: 400 + (v - 400) * sc + dy
        bad = [q for q in box if f(q[3]) > SAFE['rail_y'] and (q[2] > SAFE['rail_x'] or q[0] < SAFE['left'])]
        bot = max(f(q[3]) for q in box)
        need = 1.0
        for q in bad: need = min(need, (SAFE['rail_x'] - 360) / max(1, (q[2] - 360)) * sc, (360 - SAFE['left']) / max(1, 360 - q[0]) * sc)
        if bot > SAFE['bottom']: need = min(need, sc * (SAFE['bottom'] - dy - 400) / max(1, (bot - dy - 400)))
        if need >= sc - .005: break
        sc = max(.78, need); dy = max(0, SAFE['top'] + 24 - (400 + (top - 400) * sc))
    if dy < 1 and sc > .995: return html
    k = html.index('>', html.index('<svg')) + 1; e = html.rindex('</svg>')
    old = V._bottom(html); nb = 400 + (old - 400) * sc + dy
    return (html[:k] + f'<g transform="translate(0 {dy:.0f}) translate(360 400) scale({sc:.3f}) translate(-360 -400)">' + html[k:e] + '</g>'
            + f'<rect x="0" y="{nb:.0f}" width="0" height="0" fill="none"/>' + html[e:])

_full0 = V.full
def _full(res, b=None, extra=()):
    html, js, cues = res
    html = html.replace('nhận định của người nói', 'nhận định cá nhân').replace(' · không phải dự báo', '')
    _full0((_fit(html), js, cues), b, extra)
V.full = _full

_rem0 = V.remember
def _remember(out_html):
    thr = set(V.THREAD); V.THREAD.clear(); V.THEME['name'] = _CUR['style']
    _, out = _quiet(_rem0, out_html)
    V.THEME['name'] = 'docdo'; V.THREAD |= thr
    for ln in out:
        if 'sợi chỉ' in ln and '⚠' in ln or 'bộ màu' in ln and '⚠' in ln: continue
        print(re.sub(r' · bộ màu \w+ · sợi chỉ .*', f" · ngôn ngữ dựng {_CUR['style']}", ln))
    try:
        h = V._hist()
        if h and h[-1].get('project') == V._proj(): h[-1].update(theme='3mau', style=_CUR['style']); json.dump(h, open(V.HIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    except Exception: pass
V.remember = _remember

