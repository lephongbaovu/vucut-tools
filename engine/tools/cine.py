"""vucut-tools v6 · cine.py — CHUYỂN CẢNH ĐIỆN ẢNH (lớp phủ HTML + GSAP, tự gắn âm). import cine as C; C.init(DA) sau V.init.
dip(t) nhúng đen · dipw(t) nhúng trắng · leak(t) rò sáng · letterbox(a,b) khung điện ảnh · focus(t) kéo nét · lens(t) zoom xuyên ống kính · vignette(a,b) tối góc · sfx(t,'tên') gắn tay"""
import vc_build as V, json, os, atexit
_n = [0]; CUES = []; _DA = ['']
def init(da): _DA[0] = da
@atexit.register
def _save():
    if _DA[0]: json.dump(sorted(CUES, key=lambda c: c['t']), open(os.path.join(_DA[0], 'cine_cues.json'), 'w'))
def _id(p): _n[0] += 1; return f'{p}{_n[0]}'
def _ov(i, style, z=60):
    V.H.append(f'<div id="{i}" style="position:absolute;left:0;top:0;width:720px;height:1280px;pointer-events:none;z-index:{z};{style}"></div>')
def _js(body): V.J.append("(function(tl){" + body + "})(window.__timelines.master);")
def sfx(t, s): CUES.append(dict(t=round(V.M(t), 3), s=s))
def dip(t, d=.2, color='#000'):
    i = _id('dip'); _ov(i, f'background:{color};opacity:0')
    _js(f"tl.to('#{i}',{{opacity:1,duration:{d},ease:'power2.in'}},{t - d:.3f});tl.to('#{i}',{{opacity:0,duration:{d * 1.8:.2f},ease:'power2.out'}},{t:.3f});")
    sfx(t - d - .45, 'reverse'); sfx(t, 'impact')
def dipw(t, d=.16): dip(t, d, '#fff8ee'); CUES[-1]['s'] = 'shimmer'
def leak(t, d=1.1):
    i = _id('leak')
    _ov(i, 'opacity:0;mix-blend-mode:screen;background:radial-gradient(60% 45% at 30% 40%,rgba(255,170,90,.85),rgba(255,90,60,.35) 45%,transparent 70%)')
    _js(f"tl.fromTo('#{i}',{{opacity:0,x:-260}},{{opacity:1,x:60,duration:{d * .45:.2f},ease:'sine.out'}},{t - .1:.3f});tl.to('#{i}',{{opacity:0,x:300,duration:{d * .55:.2f},ease:'sine.in'}},{t + d * .45 - .1:.3f});")
    sfx(t - .1, 'shimmer')
def letterbox(a, b, h=120):
    i = _id('lb')
    V.H.append(f'<div id="{i}" style="position:absolute;inset:0;pointer-events:none;z-index:59"><i style="position:absolute;left:0;right:0;top:0;height:{h}px;background:#000;display:block" class="t"></i><i style="position:absolute;left:0;right:0;bottom:0;height:{h}px;background:#000;display:block" class="b"></i></div>')
    _js(f"tl.set('#{i} .t',{{yPercent:-100}},0);tl.set('#{i} .b',{{yPercent:100}},0);"
        f"tl.to('#{i} .t,#{i} .b',{{yPercent:0,duration:.45,ease:'power3.out'}},{a:.3f});tl.to('#{i} .t',{{yPercent:-100,duration:.35,ease:'power2.in'}},{b - .35:.3f});tl.to('#{i} .b',{{yPercent:100,duration:.35,ease:'power2.in'}},{b - .35:.3f});")
    sfx(a, 'braam')
def focus(t, d=.5):
    _js(f"tl.fromTo('#personWrap',{{filter:'blur(16px) brightness(1.15)'}},{{filter:'blur(0px) brightness(1)',duration:{d},ease:'power2.out',immediateRender:false}},{t:.3f});")
    sfx(t, 'camera')
def lens(t):
    _js(f"tl.to('#root',{{scale:1.35,filter:'blur(14px)',duration:.18,ease:'power2.in'}},{t - .18:.3f});tl.fromTo('#root',{{scale:.88,filter:'blur(12px)'}},{{scale:1,filter:'blur(0px)',duration:.32,ease:'power3.out',immediateRender:false}},{t:.3f});")
    sfx(t - .2, 'reverse'); sfx(t, 'impact')
def vignette(a, b):
    i = _id('vig'); _ov(i, 'opacity:0;background:radial-gradient(75% 60% at 50% 42%,transparent 55%,rgba(0,0,0,.75))', 58)
    _js(f"tl.to('#{i}',{{opacity:1,duration:.6,ease:'sine.out'}},{a:.3f});tl.to('#{i}',{{opacity:0,duration:.3}},{b - .3:.3f});")
    sfx(a, 'rumble')
