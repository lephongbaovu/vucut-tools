"""vc.py · vucut gọn: setup | go VIDEO DA [thu] | cut DA ["sai=>đúng"…] [--keep a-b] [--drop a-b] | sb DA [--read FILE] | build DA | out DA | wait DA | grid DA [video.mp4] [giây…] | ranh [tên…] | speakers DA
Trong build.py (tự sinh): import vc as P → P.sub / P.skip / P.kinetic / P.hook / P.hide / P.speaker · cảnh mẫu P.mat / P.vanban / P.ds / P.so / P.hinh / P.sat"""
import base64, glob, json, os, re, shutil, subprocess, sys, tarfile, tempfile, time
HOME = os.path.expanduser('~/.vucut'); T_DIR = os.path.join(HOME, 'tools'); FONT = os.path.join(T_DIR, 'vsub_font.css')
VCP = os.path.join(HOME, 'vc_path')
def VC(): return open(VCP).read().strip()
def sh(cmd, keep=None, tail=None, cwd=None):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    L = (r.stdout + r.stderr).splitlines()
    if keep: L = [l for l in L if re.search(keep, l)]
    if tail: L = L[-tail:]
    if L: print('\n'.join(L))
    if r.returncode: print('\n'.join((r.stdout + r.stderr).splitlines()[-15:])); sys.exit(f'✖ lỗi lệnh (mã {r.returncode}): {cmd[:120]}')
def PY(): return f'python3 -X utf8 {VC()}/scripts/vucut.py'

CSS = r"""#pip{left:426px!important;top:650px!important;width:200px!important;height:250px!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:transparent!important;-webkit-mask-image:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjUwIiB2aWV3Qm94PSIwIDAgMjAwIDI1MCI+PHBhdGggZD0iTTI0IDEwIEgxNzYgUTE5MiAxMCAxOTIgMjYgVjIyMiBRMTkyIDIzOCAxNzYgMjM4IEgyNCBROCAyMzggOCAyMjIgVjI2IFE4IDEwIDI0IDEwIFoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=)!important;-webkit-mask-size:100% 100%!important;mask-image:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjUwIiB2aWV3Qm94PSIwIDAgMjAwIDI1MCI+PHBhdGggZD0iTTI0IDEwIEgxNzYgUTE5MiAxMCAxOTIgMjYgVjIyMiBRMTkyIDIzOCAxNzYgMjM4IEgyNCBROCAyMzggOCAyMjIgVjI2IFE4IDEwIDI0IDEwIFoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=)!important;mask-size:100% 100%!important}#pip:after{content:""!important;position:absolute!important;left:0!important;top:0!important;width:200px!important;height:250px!important;bottom:auto!important;border-radius:0!important;opacity:1!important;z-index:3!important;background:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjUwIiB2aWV3Qm94PSIwIDAgMjAwIDI1MCI+PGRlZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZmQiIHgxPSIwIiB5MT0iMCIgeDI9IjAiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiMwYjBjMTAiIHN0b3Atb3BhY2l0eT0iMCIvPjxzdG9wIG9mZnNldD0iLjQ1IiBzdG9wLWNvbG9yPSIjMGIwYzEwIiBzdG9wLW9wYWNpdHk9Ii4zOCIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzBiMGMxMCIgc3RvcC1vcGFjaXR5PSIuNzIiLz48L2xpbmVhckdyYWRpZW50Pgo8bGluZWFyR3JhZGllbnQgaWQ9ImdiIiB4MT0iMCIgeTE9IjAiIHgyPSIxIiB5Mj0iMCI+PHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjOEU2NDIwIiBzdG9wLW9wYWNpdHk9IjAiLz48c3RvcCBvZmZzZXQ9Ii4xOCIgc3RvcC1jb2xvcj0iI0Q5QTg0RSIvPjxzdG9wIG9mZnNldD0iLjQyIiBzdG9wLWNvbG9yPSIjRkZGMUM0Ii8+PHN0b3Agb2Zmc2V0PSIuNiIgc3RvcC1jb2xvcj0iI0YyQ0M3NCIvPjxzdG9wIG9mZnNldD0iLjgyIiBzdG9wLWNvbG9yPSIjQjg4NjJGIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjOEU2NDIwIiBzdG9wLW9wYWNpdHk9IjAiLz48L2xpbmVhckdyYWRpZW50Pgo8Y2xpcFBhdGggaWQ9ImMiPjxwYXRoIGQ9Ik0yNCAxMCBIMTc2IFExOTIgMTAgMTkyIDI2IFYyMjIgUTE5MiAyMzggMTc2IDIzOCBIMjQgUTggMjM4IDggMjIyIFYyNiBROCAxMCAyNCAxMCBaIi8+PC9jbGlwUGF0aD48L2RlZnM+CjxyZWN0IHg9IjAiIHk9IjE3OCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSI3MiIgZmlsbD0idXJsKCNmZCkiIGNsaXAtcGF0aD0idXJsKCNjKSIvPgo8cmVjdCB4PSI0NiIgeT0iMjEyLjQiIHdpZHRoPSIxMDgiIGhlaWdodD0iMS4zIiBmaWxsPSJ1cmwoI2diKSIvPgo8cGF0aCBkPSJNMjQgMTAgSDE3NiBRMTkyIDEwIDE5MiAyNiBWMjIyIFExOTIgMjM4IDE3NiAyMzggSDI0IFE4IDIzOCA4IDIyMiBWMjYgUTggMTAgMjQgMTAgWiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utb3BhY2l0eT0iLjEyIiBzdHJva2Utd2lkdGg9IjUiLz4KPHBhdGggZD0iTTI0IDEwIEgxNzYgUTE5MiAxMCAxOTIgMjYgVjIyMiBRMTkyIDIzOCAxNzYgMjM4IEgyNCBROCAyMzggOCAyMjIgVjI2IFE4IDEwIDI0IDEwIFoiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii42IiBzdHJva2Utd2lkdGg9IjEuNCIvPjwvc3ZnPg==) 0 0/100% 100% no-repeat!important}#pip:before{content:"LE PHONG VU";position:absolute;left:0;width:200px;text-align:center;padding-left:.32em;box-sizing:border-box;top:219px;z-index:4;font-family:VWM,serif;font-weight:600;font-size:12px;letter-spacing:.32em;color:transparent;background:repeating-linear-gradient(100deg,rgba(255,255,255,0) 0 1.6px,rgba(255,250,225,.38) 1.6px 2.2px,rgba(90,60,10,.22) 2.2px 3px),linear-gradient(180deg,#FFF1C4 0%,#F2CC74 38%,#B8862F 62%,#FFE39A 82%,#8E6420 100%);-webkit-background-clip:text;background-clip:text;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.75));white-space:nowrap}#pipImg{transform:translate(10px,26px)}
.mix{row-gap:2px!important;column-gap:9px!important}.mix:not(.cardmix){width:600px!important}
.mix .w{font-family:VSUB,sans-serif!important;font-weight:600!important;font-size:30px!important;line-height:1.24!important;letter-spacing:.005em;color:#F6F1E7!important;text-shadow:0 1px 2px rgba(0,0,0,.55),0 2px 10px rgba(0,0,0,.45),0 0 22px rgba(0,0,0,.25)!important}
.mix .w.sm{font-size:24px!important;font-weight:500!important}
.mix .s{font-size:68px!important;line-height:1.08!important;padding:.24em .1em .22em!important;margin:-.24em -.04em -.22em!important}.mix .s.xl{font-size:80px!important}
.mix.cardmix{padding-left:10px}.mix.cardmix .w{font-size:27px!important}.mix.cardmix .s{font-size:50px!important}.mix.cardmix .s.xl{font-size:56px!important}
"""
KCSS = r"""#K{row-gap:10px;padding-bottom:300px!important}#K>div{line-height:1.22!important;letter-spacing:.01em!important}
#K .k0{font-family:VSUB,sans-serif!important;font-weight:600!important;font-size:34px!important;color:#F6F1E7!important;text-shadow:0 2px 10px rgba(0,0,0,.5)}
#K .k1{font-family:VCS,serif!important;font-style:italic;font-weight:700!important;font-size:78px!important;line-height:1.08!important;letter-spacing:0!important;padding:.24em .1em .22em!important;margin:-.24em 0 -.22em!important;background-image:var(--vc-grad-gold);-webkit-background-clip:text;background-clip:text;color:transparent!important;-webkit-text-fill-color:transparent;filter:drop-shadow(0 2px 4px rgba(0,0,0,.6)) drop-shadow(0 0 14px rgba(201,164,92,.45))}
"""
def font_css():
    if os.path.exists(FONT): return open(FONT, encoding='utf-8').read()
    tmp = tempfile.mkdtemp()
    subprocess.run(['npm', 'pack', '@fontsource/be-vietnam-pro@5', '--silent'], cwd=tmp, check=True, capture_output=True)
    faces = []
    with tarfile.open(glob.glob(tmp + '/*.tgz')[0]) as tf:
        for wt in ('500', '600'):
            for blk in re.findall(r'@font-face\s*{[^}]*}', tf.extractfile(f'package/{wt}.css').read().decode()):
                f = re.search(r'url\(\./files/([^)]+\.woff2)\)', blk).group(1)
                if not re.search(r'-(latin|vietnamese)-', f): continue
                b64 = base64.b64encode(tf.extractfile('package/files/' + f).read()).decode()
                faces.append("@font-face{font-family:VSUB;font-weight:%s;font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');%s}"
                             % (wt, b64, re.search(r'unicode-range:[^;]+;', blk).group(0)))
    open(FONT, 'w', encoding='utf-8').write('\n'.join(faces))
    return open(FONT, encoding='utf-8').read()

LPV_URL = 'https://raw.githubusercontent.com/lephongbaovu/realcut-tools/main/assets/fonts/LPVDisplay-Black.ttf'
def lpv_css():   # FONT CHỮ NHẤN cố định của anh Vũ: LPV Display (bản dày) thay Playfair cho họ VCS + chữ hook; màu giữ nguyên luật vucut
    fp = os.path.join(T_DIR, 'LPVDisplay-Black.ttf')
    if not os.path.exists(fp) or os.path.getsize(fp) < 50000:
        os.makedirs(T_DIR, exist_ok=True); subprocess.run(['curl', '-sL', '-m', '120', '-o', fp, LPV_URL])
    if not os.path.exists(fp) or os.path.getsize(fp) < 50000: print('  ⚠ không tải được font LPV — giữ font cũ'); return ''
    b64 = base64.b64encode(open(fp, 'rb').read()).decode()
    face = "@font-face{font-family:%s;font-style:%s;font-weight:100 900;font-display:block;src:url(data:font/ttf;base64,%s) format('truetype')}"
    return (face % ('VCS', 'italic', b64) + face % ('VCS', 'normal', b64) + face % ('VLPV', 'normal', b64)
            + '.hook{font-family:VLPV,sans-serif!important;font-style:normal!important}')

WM_URL = 'https://raw.githubusercontent.com/lephongbaovu/realcut-tools/main/assets/fonts/Cinzel-SemiBold.ttf'
WM = {'text': 'LE PHONG VU', 'on': True}
def watermark(text='LE PHONG VU', on=True): WM.update(text=text, on=on)   # P.watermark(on=False) = tắt cho video này
def _wm_html():   # watermark chung với realcut: tên anh Vũ, Cinzel, trôi chậm. z 7 + gắn cuối DOM: trên người nói, panel, nền đồ hoạ, bản đồ (vẫn thấy ở cảnh đồ hoạ toàn khung); dưới nội dung đồ hoạ (z 8), phụ đề/chữ (z ≥ 10), khung người nói nhỏ (z 30)
    if not WM['on']: return
    fp = os.path.join(T_DIR, 'Cinzel-SemiBold.ttf')
    if not os.path.exists(fp) or os.path.getsize(fp) < 30000:
        os.makedirs(T_DIR, exist_ok=True); subprocess.run(['curl', '-sL', '-m', '120', '-o', fp, WM_URL])
    if not os.path.exists(fp) or os.path.getsize(fp) < 30000: print('  ⚠ không tải được font watermark — bỏ watermark'); return
    b64 = base64.b64encode(open(fp, 'rb').read()).decode()
    V.H.append("<style>@font-face{font-family:VWM;font-weight:600;font-display:block;src:url(data:font/ttf;base64,%s) format('truetype')}</style>" % b64
               + '<div id="wmk" style="position:absolute;left:360px;top:512px;z-index:7;pointer-events:none;white-space:nowrap;font-family:VWM,serif;'
               'font-weight:600;font-size:25px;letter-spacing:.32em;color:rgba(247,241,231,.50);text-shadow:0 1px 3px rgba(0,0,0,.3)">' + WM['text'] + '</div>')
    T = float(V.T); rx = max(1, int(T / 13) + 1); ry = max(1, int(T / 18.5) + 1)   # x chu kỳ 26 s, y 37 s (như realcut)
    V.J.append("tl.set('#wmk',{xPercent:-50,yPercent:-50,x:0,y:0},0);"
               f"tl.fromTo('#wmk',{{x:-194}},{{x:194,duration:13,ease:'sine.inOut',repeat:{rx},yoyo:true}},0);"
               f"tl.fromTo('#wmk',{{y:-218}},{{y:218,duration:18.5,ease:'sine.inOut',repeat:{ry},yoyo:true}},0);")

# ---------- lời ----------
def _norm(s): return s.strip(',.?!:;"“”').replace('_', ' ').lower()
def _p(DA, cut=True): return os.path.join(DA, 'cut', 'words_cut.json') if cut else os.path.join(DA, 'words.json')
def _load(DA, cut=True): return json.load(open(_p(DA, cut), encoding='utf-8'))
NOI = {'thì', 'để', 'nhưng', 'vì', 'nên', 'mà', 'hay', 'hoặc', 'khi', 'nếu'}
def _chunks(W, maxn=8):
    out, cur = [], []
    for i, w in enumerate(W):
        if len(cur) >= 3 and _norm(w['word']) in NOI: out.append(cur); cur = []
        cur.append(w)
        nxt = W[i + 1] if i + 1 < len(W) else None
        gap = nxt['start'] - w.get('end', w['start']) if nxt else 9
        if not nxt or gap >= .3 or w['word'][-1:] in '.?!,' or len(cur) >= maxn: out.append(cur); cur = []
    res = []
    for c in out:
        if res and len(res[-1]) < 3 and res[-1][-1]['word'][-1:] not in '.?!' and len(res[-1]) + len(c) <= maxn + 1 and c[0]['start'] - res[-1][-1].get('end', 0) < .5: res[-1] += c
        else: res.append(c)
    return res
def _fix(DA, rules):
    W, n = _load(DA, False), 0
    for r in rules:
        a, b = r.split('=>'); a = a.split(); i = 0
        while i <= len(W) - len(a):
            if [_norm(w['word']) for w in W[i:i + len(a)]] == [_norm(x) for x in a]:
                last = W[i + len(a) - 1]['word']; pun = last[len(last.rstrip(',.?!:;')):]; bb = b.split()
                if len(bb) == len(a) > 1: W[i:i + len(a)] = [dict(w, word=x + (pun if k == len(a) - 1 else '')) for k, (w, x) in enumerate(zip(W[i:i + len(a)], bb))]
                else: W[i:i + len(a)] = [{'word': b + pun, 'start': W[i]['start'], 'end': W[i + len(a) - 1].get('end', W[i]['start'])}]
                n += 1
            i += 1
    json.dump(W, open(_p(DA, False), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'✓ sửa lời {n} chỗ')

# ---------- lệnh ----------
def setup(vc):
    os.makedirs(T_DIR, exist_ok=True); vc = _skill_copy(os.path.abspath(vc)); open(VCP, 'w').write(vc)   # bản chép đã vá preview.mjs (bản đồ 3D)
    sh(f'cp {vc}/tools/* {T_DIR}/')
    font_css()
    sh(f'python3 -c "import faster_whisper,rembg" 2>/dev/null && node {vc}/scripts/preview.mjs --check | grep -q ok && echo "✅ sẵn sàng" || python3 -X utf8 {vc}/scripts/vucut.py setup --rembg', keep='✅|✖|lỗi|SẴN')

# lỗi Whisper hay gặp ở kênh (thêm dòng mỗi khi sửa tay 1 lỗi mới) — ghi vào DA/sua_chinh_ta.tsv trước phiên âm, transcribe tự áp
SUA = """bó đồng sản	bất động sản
bóng đồng sản	bất động sản
bất đồng sản	bất động sản
bong sản	bất động sản
đắt lắc	Đắk Lắk
đắc lắt	Đắk Lắk
quy hạch	quy hoạch
quy hoặc	quy hoạch
tích lĩ	tích lũy
tích lủy	tích lũy
bình vững	bền vững
điểm nghẻng	điểm nghẽn
sinh họt	sinh hoạt
tổ án riêng	tổ ấm riêng
ngay càng	ngày càng
bay vốn	vay vốn
gia bán	giá bán
tuyền thế nha	tiền thuê nhà
tiền thế nhà	tiền thuê nhà
hòn thành	hoàn thành
bài tỏa	bài toán
đại nhân tiến độ	đẩy nhanh tiến độ
nhà ở xả hội	nhà ở xã hội
theo vũ	Theo Vũ
vũ cho rằng	Vũ cho rằng
follow vũ	Follow Vũ
phồ lâu vũ	Follow Vũ
hạ tần	hạ tầng
cao tốt	cao tốc
giải phóng mặt bằn	giải phóng mặt bằng
"""
def _sua(DA):
    os.makedirs(DA, exist_ok=True); f = os.path.join(DA, 'sua_chinh_ta.tsv')
    old = open(f, encoding='utf-8').read() if os.path.exists(f) else ''
    open(f, 'w', encoding='utf-8').write(old + ''.join(l + '\n' for l in SUA.strip().splitlines() if l not in old))
def go(video, DA, *a):
    DA = os.path.abspath(os.path.expanduser(DA)); _sua(DA)
    sh(f'{PY()} prep "{video}" {DA}' + (' --clip 0-30' if 'thu' in a else ''), keep='✅|tự sửa|✖')
    for c in _chunks(_load(DA, False), 14): print(f"{c[0]['start']:6.2f}  " + ' '.join(w['word'] for w in c))

def cut(DA, *a):
    DA = os.path.abspath(os.path.expanduser(DA)); rules = [x for x in a if '=>' in x]
    opt = ' '.join(x for x in a if '=>' not in x)
    if rules: _fix(DA, rules)
    sh(f'{PY()} cut {DA} --no-tighten {opt}', keep=r'^Gốc|Mối nối cần phủ|^\s+\d+\.\d+–\d+\.\d+ ·|✖')
    sh(f'{PY()} beats {DA}', keep=r'^\s+\d+\.\d+–|Câu lửa')
    speakers(DA)
    st = json.load(open(os.path.join(DA, 'state.json')))
    print(f"T = {st['T']} · mặt {st.get('face')}  — nháp phụ đề (lời chính xác để viết subs.py):")
    for c in _chunks(_load(DA)):
        tk = [f"[g:{w['word']}]" if re.search(r'\d', w['word']) else w['word'] for w in c]
        print(f"  {c[0]['start']:6.2f}  {' '.join(tk)}")
    diadanh(DA)

# địa danh cấp xã/phường KHÔNG trùng nghĩa thường (lọc khi dò tự động)
DD_BO = set()
def diadanh(DA):   # vc.py diadanh DA — dò tên xã/phường Đắk Lắk (102 đơn vị 2025) trong lời → giây nhắc + dòng P.sat gợi ý
    DA = os.path.abspath(os.path.expanduser(DA)); W = _load(DA); D = _ranh_data()['xa']
    tok = [(_plain(x).strip(',.?!:;"“”'), w['start']) for w in W for x in w['word'].split()]
    hits = {}
    for k, v in D.items():
        n = _plain(v['ten']).split()
        if len(n) < 2 or v['ten'] in DD_BO: continue
        for q in range(len(tok) - len(n) + 1):
            if [t for t, _ in tok[q:q + len(n)]] == n: hits.setdefault(v['ten'], []).append(tok[q][1])
    tinh = [tok[q][1] for q in range(len(tok) - 1) if [t for t, _ in tok[q:q + 2]] == ['dak', 'lak'] and not (q > 1 and [t for t, _ in tok[q - 2:q]] == ['lien', 'son'])]
    if tinh: hits.setdefault('Đắk Lắk', tinh)   # nói chung cả tỉnh → bản đồ ranh giới tỉnh (anh duyệt 20/11/2026)
    if not hits:
        print('ĐỊA DANH: không nhắc địa phương nào của Đắk Lắk'); return
    print('ĐỊA DANH được nhắc (mỗi nơi 1 bản đồ vệ tinh ở lần nhắc đầu hoặc đoạn nói kỹ về nơi đó; Đắk Lắk = ranh giới cả tỉnh; cảnh bắt đầu ≥ 1.2 s trước giây nhắc):')
    for ten, ts in sorted(hits.items(), key=lambda x: x[1][0]):
        t = ts[0]; print(f"  {t:6.2f}  {ten}  (nhắc {len(ts)} lần: {', '.join(f'{x:.1f}' for x in ts[:6])})  →  P.sat({max(0, t - 1.4):.2f}, {max(t + 1.8, max(0, t - 1.4) + 2.8):.2f}, '{ten}', t_draw={max(t, max(0, t - 1.4) + 1.2):.2f})")

def _assemble(DA):
    st = json.load(open(os.path.join(DA, 'state.json'))); sc = open(os.path.join(DA, 'scenes.py'), encoding='utf-8').read()
    kind = (re.search(r"KIND\s*=\s*'(\w+)'", sc) or [0, 'phantich'])[1]; vc = VC()
    head = os.path.join(DA, 'facetrack.json'); face = tuple(st.get('face') or (.5, .38))
    src = (f"import sys, os; sys.path[:0] = [r'{vc}/scripts', r'{T_DIR}']\n"
           "import vc_build as V, mg_nganh as N, cine as C, vc as P\n"
           "import mg_x as X, mg_bds as B, mg_dl as DL, mg_v4, mg_journey as MJ, mg\n"
           "import mg_real as R\n"
           f"V.init(T={st['T']}, face={face}, head=r'{head}', kind='{kind}')\n"
           f"C.init(r'{DA}'); P.init(V, r'{DA}')\n# ---- scenes.py ----\n{sc}\n# ---- hết scenes ----\n"
           f"exec(open(r'{DA}/subs.py', encoding='utf-8').read())\nP.finish()\n"
           f"V.finish(r'{DA}/build/master.html', r'{DA}/cues.json', shell=r'{vc}/assets/template/vucut_9x16_v4.html')\n")
    open(os.path.join(DA, 'build.py'), 'w', encoding='utf-8').write(src)

def build(DA):
    DA = os.path.abspath(os.path.expanduser(DA)); _assemble(DA)
    sh(f'python3 -X utf8 {DA}/build.py', keep=r'⚠|✖|MẶT HIỆU|phụ đề|phong cách|Error|Traceback|line \d+|^\w+Error', tail=30)
    lay = json.load(open(os.path.join(DA, 'layout.json')))   # mốc của cảnh mẫu (P.mat/P.ds/…) → chú thích cho cổng đọc
    fn = {'P': 'person', 'SPLIT': 'split'}
    open(os.path.join(DA, 'build.py'), 'a', encoding='utf-8').write(''.join(f"# V.L_{fn.get(n, 'full')}({a}, {b})\n" for n, a, b in lay))
    _gate_wm()
    sh(f'node {T_DIR}/qc_gate.cjs {DA}', keep=r'⚠|✖|✅|TỰ CĂN')
    for f in glob.glob(os.path.join(DA, 'qc', 't_*.png')): os.remove(f)
    r = subprocess.run(f'{PY()} probe {DA} --scan --cuts', shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    L = (r.stdout + r.stderr).splitlines(); wrap = sorted(set(re.findall(r'#(sb\d+) từ to xuống dòng', '\n'.join(L))), key=lambda x: int(x[2:]))
    print('\n'.join(dict.fromkeys(l for l in L if re.search(r'⚠|KHUNG TRỐNG|✅ không|✖', l) and 'xuống dòng' not in l)))
    if wrap: print('⚠ từ khoá xuống dòng (xem ảnh, chỉ sửa nếu gãy xấu):', ' '.join(wrap))
    grid(DA)

def _cuts(DA):
    src = open(os.path.join(DA, 'build.py'), encoding='utf-8').read()
    return sorted({float(x) for m in re.finditer(r'V\.L_(?:person|full|split|card)\(\s*([\d.]+)\s*,\s*([\d.]+)', src) for x in m.groups()})

# ---------- nhạc nền theo MOOD nội dung (tự tổng hợp, không bản quyền) ----------
MOODS = {   # anh Vũ chốt 27/11/2026: CHỈ GIỮ 1 bài nhạc nền cho mọi video (đã xoá sang/hung/phantich/toi/hung_tin)
    'tin':  dict(ch=[[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 56, 59]], root=[45, 41, 38, 40], bpm=96, gain=-8,
                 desc='đưa tin – phân tích, kịch tính (La thứ Am–F–Dm–E), -8 dB như video M\'Drắk anh duyệt'),
}
# ---------- MỨC ÂM ANH VŨ ĐÃ DUYỆT (22/11/2026) — mặc định cho mọi video ----------
NHAC_MACDINH = 'tin'   # nhạc nền mặc định (anh Vũ chốt 27/11/2026, video M'Drắk): đưa tin – phân tích, kịch tính (La thứ, 96 BPM), gain -8 dB như bản anh duyệt · trước: 'hung_tin'
SFX_DB = -9            # hiệu ứng trong lời (whoosh, pop, chuyển cảnh…) — nhỏ, không gây khó chịu
CINE_DB = dict(impact=-17, reverse=-22, braam=-19, tape=-20, heart=-18, shimmer=-23, camera=-21, rumble=-23, ranh=-20, countup=-22, paper=-20)   # âm điện ảnh / máy đếm / vẽ viền
CINE_DB_KHAC = -22
LUFS, TP = -11, -1.0   # độ to tổng chuẩn TikTok/Facebook
# giọng: lọc 80 Hz + nén 3:1 (ngưỡng -22 dB, +3 dB) + sáng 3 kHz +2 dB · nhạc: gain theo mood (tin -8 dB), khoét 2.2 kHz -5 dB, nhường giọng 2.5:1
def nhac(mood=NHAC_MACDINH):   # P.nhac() — nhạc nền duy nhất anh duyệt ('tin', -8 dB); tên mood cũ bị bỏ qua
    if mood not in MOODS: print(f"  · nhạc '{mood}' đã xoá (anh chốt 27/11/2026) → dùng nhạc mặc định '{NHAC_MACDINH}'"); mood = NHAC_MACDINH
    json.dump({'mood': mood}, open(os.path.join(DA_, 'nhac.json'), 'w'))
def _music_tin(dur, impacts, path):   # nền tin tức: drone trầm + ostinato móc 16 + tiếng tích tắc đồng hồ + nhịp trống thưa, căng dần tới cao trào
    import numpy as np, wave
    from scipy.signal import butter, sosfilt
    M = MOODS['tin']; sr = 48000; N = int(sr * dur); L = np.zeros(N); Rr = np.zeros(N); rng = np.random.default_rng(7)
    BEAT = 60 / M['bpm']; BAR = 4 * BEAT; nb = int(dur / BAR) + 1; hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    lpf = lambda x, f: sosfilt(butter(2, f, 'low', fs=sr, output='sos'), x); hpf = lambda x, f: sosfilt(butter(2, f, 'high', fs=sr, output='sos'), x)
    def add(x, t, gl, gr=None):
        a = int(t * sr)
        if a >= N or a < 0: return
        x = x[:N - a]; L[a:a + len(x)] += gl * x; Rr[a:a + len(x)] += (gl if gr is None else gr) * x
    imp = sorted(impacts); peak = max([t for t in imp if t > dur * .6] or [dur * .8])
    energy = lambda t: .4 + .3 * min(1, t / 10) + .3 * math.exp(-((t - peak) / 10) ** 2)
    saw = lambda f, m: 2 * ((f * m) % 1) - 1
    for b in range(nb):   # DRONE: hợp âm thứ trầm, lọc tối, phồng chậm
        t0 = b * BAR; d = BAR + 1.0; m = np.arange(int(sr * d)) / sr; e = np.minimum(1, m / 1.2) * np.minimum(1, (d - m) / 1.0)
        for k, q in enumerate(M['ch'][b % 4]):
            f = hz(q - 12); x = lpf((saw(f * 1.003, m) + saw(f * .997, m)) * .5, 650) * .06 + np.sin(2 * np.pi * f * m) * .03
            add(x * e, t0, .75 if k % 2 else .55, .55 if k % 2 else .75)
    for b in range(nb):   # OSTINATO móc 16 (kiểu dây pizz/staccato) — gốc + quãng 8 xen kẽ, sáng dần theo năng lượng
        for st in range(16):
            t0 = b * BAR + st * BEAT / 4; e = energy(t0); q = M['root'][b % 4] + (12 if st % 4 == 2 else 24 if st % 8 == 6 else 12 * 0)
            m = np.arange(int(sr * .16)) / sr; f = hz(q + 12)
            x = lpf(saw(f, m), 900 + 900 * e) * np.exp(-m * 26); acc = 1.0 if st % 4 == 0 else .6
            add(x, t0, .085 * acc * e, .07 * acc * e)
    TK = hpf(rng.standard_normal(int(sr * .012)), 6500) * np.exp(-np.arange(int(sr * .012)) / sr * 400)
    for b in range(1, nb):   # TÍCH TẮC đồng hồ tin tức (móc 8), rất nhỏ
        for st in range(8): add(TK, b * BAR + st * BEAT / 2, .035 if st % 2 == 0 else .021, .021 if st % 2 == 0 else .035)   # tích tắc: = 70% mức gốc (anh duyệt)
    def kick():
        m = np.arange(int(sr * .4)) / sr; return np.sin(2 * np.pi * np.cumsum(44 + 70 * np.exp(-m * 30)) / sr) * np.exp(-m * 8)
    K = kick()
    for b in range(2, nb):   # TRỐNG thưa: phách 1 (+ phách 3 khi căng); mỗi 4 ô nhịp một tiếng "boom" trầm
        e = energy(b * BAR); add(K, b * BAR, .32)
        if e > .65: add(K, b * BAR + 2 * BEAT, .22)
        if b % 4 == 0:
            m = np.arange(int(sr * 2.0)) / sr; bm = np.sin(2 * np.pi * np.cumsum(40 + 25 * np.exp(-m * 5)) / sr) * np.exp(-m * 2); add(bm, b * BAR, .22)
    for b in range(0, nb, 2):   # chuông cao thưa (nốt chủ âm hợp âm), tạo cảm giác "bản tin"
        m = np.arange(int(sr * 1.6)) / sr; f = hz(M['ch'][b % 4][0] + 24)
        x = (np.sin(2 * np.pi * f * m) + .3 * np.sin(2 * np.pi * 2.76 * f * m) * np.exp(-m * 6)) * np.exp(-m * 2.8); add(x, b * BAR + BEAT * 3.5, .035, .05)
    for t in imp:   # mốc lớn: riser 1.5 s + hit trầm + cymbal
        m = np.arange(int(sr * 1.5)) / sr; rs = hpf(rng.standard_normal(len(m)), 2000) * (m / 1.5) ** 3; add(rs, t - 1.5, .05)
        m = np.arange(int(sr * 2.6)) / sr; cy = hpf(rng.standard_normal(len(m)), 5000) * np.exp(-m * 2.0)
        sb = np.sin(2 * np.pi * np.cumsum(50 + 35 * np.exp(-m * 9)) / sr) * np.exp(-m * 2.2); add(cy * .05 + sb * .28, t, 1.0)
    x = np.stack([L, Rr], 1); fi = np.minimum(1, np.arange(N) / (sr * 1.0)); fo = np.minimum(1, (N - np.arange(N)) / (sr * 1.5))
    x *= (fi * fo)[:, None]; x = hpf(x.T, 30).T; x = x / (np.abs(x).max() + 1e-9) * 10 ** (-1 / 20)
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
def _music(dur, impacts, mood, path):   # 1 bài duy nhất: nền tin tức kịch tính
    return _music_tin(dur, impacts, path)
def _remix(DA):   # thay nhạc mặc định bằng nhạc theo mood (P.nhac), trộn lại đúng như vucut.py audio (nghẹt · tắt trước câu đắt · nhường giọng)
    nf = os.path.join(DA, 'nhac.json'); mood = json.load(open(nf))['mood'] if os.path.exists(nf) else NHAC_MACDINH
    mood = mood if mood in MOODS else NHAC_MACDINH
    if mood == 'toi': return
    j = lambda *x: os.path.join(DA, *x); plan = json.load(open(j('audio.json'), encoding='utf-8')) if os.path.exists(j('audio.json')) else {}
    T = json.load(open(j('state.json')))['T']; _music(T, plan.get('impacts', []), mood, j('music.wav'))
    if os.path.exists(j('cues_lite.json')):   # hiệu ứng trong lời nhỏ lại (SFX_DB)
        subprocess.run([*PY().split(' ')[:3][:1], '-X', 'utf8', os.path.join(VC(), 'scripts', 'sfx_mix.py'), j('voice.wav'), j('cues_lite.json'), j('sfx'), j('voice_sfx.m4a'), '--sfx-db', str(SFX_DB)], check=True)
    btw = lambda W: '+'.join(f'between(t,{x},{y})' for x, y in W) or '0'; Wm, Dk = btw(plan.get('muffle', [])), btw(plan.get('duck', []))
    g = MOODS[mood].get('gain', -12)   # nền dưới giọng: nhạc khoét 1–4 kHz (dải rõ lời), nhường giọng khi anh nói
    fc = (f"[1:a]aresample=48000,volume={g}dB,equalizer=f=2200:t=o:w=1.6:g=-5,asplit=2[mA][mB];[mA]volume='if({Wm},0,1)':eval=frame[full];"
          f"[mB]lowpass=f=520,lowpass=f=520,volume=2dB,volume='if({Wm},1,0)':eval=frame[muff];"
          f"[full][muff]amix=inputs=2:normalize=0,volume='if({Dk},0.03,1)':eval=frame[m];"
          f"[2:a]pan=stereo|c0=c0|c1=c0[key];[m][key]sidechaincompress=threshold=0.1:ratio=2.5:attack=60:release=700:knee=6[md];"
          f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=8:release=150:makeup=3dB,equalizer=f=3000:t=o:w=1.2:g=2[v];[v][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I={LUFS}:TP={TP}:LRA=9[out]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', j('voice_sfx.m4a'), '-i', j('music.wav'), '-i', j('voice.wav'), '-filter_complex', fc,
                    '-map', '[out]', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', j('final_audio.m4a')], check=True)
    print(f'xong → nhạc nền mood "{mood}": {MOODS[mood]["desc"]}')

def _layer(DA):   # lớp âm điện ảnh ở mức CINE_DB (thay cine_sfx --layer để giữ mức anh duyệt)
    j = lambda *x: os.path.join(DA, *x); cues = json.load(open(j('cine_cues.json'))) if os.path.exists(j('cine_cues.json')) else []
    base = j('final_audio_base.m4a')
    if not os.path.exists(base): shutil.copy(j('final_audio.m4a'), base)
    if not cues: shutil.copy(base, j('final_audio.m4a')); print('không có âm điện ảnh'); return
    ins, fc = ['-i', base], []
    for k, c in enumerate(cues):
        ins += ['-i', j('sfx', c['s'] + '.wav')]; ms = max(0, int(c['t'] * 1000))
        fc.append(f"[{k + 1}:a]aresample=48000,volume={CINE_DB.get(c['s'], CINE_DB_KHAC)}dB,adelay={ms}|{ms},pan=stereo|c0=c0|c1=c0[c{k}]")
    fc.append('[0:a]' + ''.join(f'[c{k}]' for k in range(len(cues))) + f'amix=inputs={len(cues) + 1}:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I={LUFS}:TP={TP}:LRA=9[o]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fc), '-map', '[o]', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', j('final_audio.m4a')], check=True)
    print(f'xong → lớp điện ảnh {len(cues)} âm:', ', '.join(f"{c['s']}@{c['t']}" for c in cues))

def _gate_wm():   # cổng không kiểm watermark trôi (lớp chìm) — tránh báo nhầm "ngoài vùng an toàn" làm chặn xuất
    g = os.path.join(T_DIR, 'qc_gate.cjs')
    if not os.path.exists(g): return
    x = open(g, encoding='utf-8').read(); old = "      if (o.own === '#pip') continue;\n"
    if old in x: open(g, 'w', encoding='utf-8').write(x.replace(old, "      if (o.own === '#pip' || o.tx === WM_TEXT) continue;\n".replace('WM_TEXT', json.dumps(WM['text'])), 1))
    x = open(g, encoding='utf-8').read()   # khung người nói mới 200×250 tại x426 y650 (anh duyệt 26/11/2026: kính mờ, đáy mờ dần + chỉ vàng, LE PHONG VU vàng xước căn giữa) — cổng kiểm chữ đè theo khung mới
    y = x.replace("const P = { l: 446, t: 700, r: 626, b: 895 };", "const P = { l: 426, t: 650, r: 626, b: 900 };").replace("r: [446, 700, 626, 895]", "r: [426, 650, 626, 900]")
    if y != x: open(g, 'w', encoding='utf-8').write(y)

def out(DA):
    DA = os.path.abspath(os.path.expanduser(DA))
    for f in ('final_audio_base.m4a', 'final_audio.m4a'):
        if os.path.exists(os.path.join(DA, f)): os.remove(os.path.join(DA, f))
    sh(f'python3 {T_DIR}/cine_sfx.py sfx', cwd=DA, tail=1)
    sh(f'{PY()} audio {DA}', keep='LUFS|✖')
    _remix(DA)
    _layer(DA)
    sp, dn = os.path.join(DA, 'splits.json'), os.path.join(DA, 'splits.done.json')
    s = open(sp).read() if os.path.exists(sp) else ''
    if s != (open(dn).read() if os.path.exists(dn) else None):
        subprocess.run(['rm', '-rf', os.path.join(DA, 'build', 'cut')]); open(dn, 'w').write(s)
    subprocess.Popen(f'nohup {PY()} render {DA} > {DA}/render.log 2>&1 &', shell=True)
    time.sleep(3); wait(DA)

def wait(DA):
    DA = os.path.abspath(os.path.expanduser(DA)); log = os.path.join(DA, 'render.log'); t0 = time.time()
    while time.time() - t0 < 540:
        L = open(log, encoding='utf-8', errors='replace').read() if os.path.exists(log) else ''
        m = re.search(r'✅ (\S+\.mp4)', L)
        if m:
            v = m.group(1); st = json.load(open(os.path.join(DA, 'state.json')))
            d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', v], capture_output=True, text=True).stdout)
            print(f"✅ {v} · {d:.2f} s (T {st['T']})" + ('' if abs(d - st['T']) < .15 else ' ⚠ LỆCH THỜI LƯỢNG'))
            cs = [c for c in _cuts(DA) if .3 < c < st['T'] - .3][:4]
            grid(DA, os.path.basename(v), *[f'{c + .15:.2f}' for c in cs]); return
        if re.search(r'Traceback|✖', L): print(L[-1500:]); sys.exit('✖ render lỗi')
        time.sleep(15)
    print('… chưa xong, chạy: vc.py wait DA  ·', (L.strip().splitlines() or [''])[-1][-80:])

def xem(DA, *ts):   # vc.py xem DA 14.2 42 71.9 — chụp ĐÚNG giây từ bản dựng (trước khi xuất) → qc/grid.jpg
    DA = os.path.abspath(os.path.expanduser(DA)); sh(f'{PY()} probe {DA} ' + ','.join(ts), keep='✖|⚠'); grid(DA, *ts)

def grid(DA, *a):
    from PIL import Image
    DA = os.path.abspath(os.path.expanduser(DA))
    src = next((x for x in a if x.endswith('.mp4')), None); ts = [float(x) for x in a if not x.endswith('.mp4')]
    if src:
        fs = []
        for t in ts:
            f = os.path.join(DA, 'qc', f'x_{t}.jpg'); fs.append((t, f))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', os.path.join(DA, src), '-frames:v', '1', f], check=True)
    else:
        fs = sorted((float(f.rsplit('t_', 1)[1][:-4]), f) for f in glob.glob(os.path.join(DA, 'qc', 't_*.png')))
        if ts: fs = [min(fs, key=lambda x: abs(x[0] - t)) for t in ts]
        elif len(fs) > 24: fs = [fs[round(k * (len(fs) - 1) / 23)] for k in range(24)]
    ims = [Image.open(f).convert('RGB') for _, f in fs]; w = 240; h = round(w * ims[0].height / ims[0].width); n = min(6, len(ims))
    o = Image.new('RGB', (w * n, h * ((len(ims) + n - 1) // n)))
    for k, im in enumerate(ims): o.paste(im.resize((w, h)), (w * (k % n), h * (k // n)))
    o.save(os.path.join(DA, 'qc', 'grid.jpg'), quality=85); print(f'→ Read {DA}/qc/grid.jpg ·', ' '.join(f'{t:g}' for t, _ in fs))

# ---------- phỏng vấn: ai đang nói (dò mặt + chuyển động miệng) ----------
def _voice(DA, ch, k):   # MFCC từng cụm → k cụm giọng (bỏ cụm < 1 s khi học, làm mượt lượt lẻ)
    import numpy as np; from scipy.fft import dct; from sklearn.cluster import KMeans
    sr = 16000; raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(DA, 'cut', 'cut.mp4'), '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n, h = 400, 160; nf = 1 + (len(x) - n) // h
    S = np.abs(np.fft.rfft(np.lib.stride_tricks.as_strided(x, (nf, n), (x.strides[0] * h, x.strides[0])) * np.hamming(n), 512)) ** 2
    mel = lambda f: 2595 * np.log10(1 + f / 700); pts = 700 * (10 ** (np.linspace(mel(60), mel(7600), 42) / 2595) - 1); bins = np.floor(513 * pts / sr).astype(int)
    fb = np.zeros((40, 257))
    for i in range(40):
        p, q, r = bins[i], bins[i + 1], bins[i + 2]; fb[i, p:q] = (np.arange(p, q) - p) / max(1, q - p); fb[i, q:r] = (r - np.arange(q, r)) / max(1, r - q)
    E = S @ fb.T; mf = dct(np.log(E + 1e-9), norm='ortho')[:, 1:20]; en = np.log(E.sum(1) + 1e-9); X = []
    for c in ch:
        p, q = int(c[0]['start'] * 100), max(int(c[-1].get('end', c[-1]['start'] + .3) * 100), int(c[0]['start'] * 100) + 5)
        sg, e = mf[p:q], en[p:q]; sg = sg[e > np.percentile(e, 40)] if len(e) > 5 else sg
        X.append(np.r_[sg.mean(0), sg.std(0)])
    X = np.array(X); X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    dur = np.array([c[-1].get('end', c[-1]['start'] + .3) - c[0]['start'] for c in ch]); ok = dur >= 1.0
    lab = KMeans(k, n_init=20, random_state=0).fit(X[ok] if ok.sum() >= k * 2 else X).predict(X)
    for i in range(1, len(lab) - 1):
        if lab[i - 1] == lab[i + 1] != lab[i] and dur[i] < 1.5: lab[i] = lab[i - 1]
    return lab

def speakers(DA, *a):   # vc.py speakers DA → DA/speakers.json (tự chạy trong `cut`): giọng chia lượt, hình gán mặt
    import cv2, numpy as np, itertools
    DA = os.path.abspath(os.path.expanduser(DA)); cap = cv2.VideoCapture(os.path.join(DA, 'cut', 'cut.mp4'))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30; W_, H_ = int(cap.get(3)), int(cap.get(4)); sw = 480 / W_; hs = int(H_ * sw)
    det = cv2.FaceDetectorYN.create(os.path.join(VC(), 'assets', 'models', 'face_yunet.onnx'), '', (480, hs), .7, .3, 50)
    step = max(1, round(fps / 8)); boxes, frames, k = [], [], 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if k % step == 0:
            frames.append((k / fps, cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)))
            if len(frames) % 8 == 1:
                _, fc = det.detect(cv2.resize(f, (480, hs)))
                if fc is not None: boxes += [[v / sw for v in b[:4]] for b in fc if b[2] > 20]
        k += 1
    cl = []
    for bx in sorted(boxes, key=lambda b: b[0]):
        c = (bx[0] + bx[2] / 2, bx[1] + bx[3] / 2)
        for g in cl:
            if abs(g['c'][0] - c[0]) < g['w'] * .8 and abs(g['c'][1] - c[1]) < g['w'] * .8: g['b'].append(bx); g['c'] = c; break
        else: cl.append({'c': c, 'w': bx[2], 'b': [bx]})
    cl = [g for g in cl if len(g['b']) >= max(2, len(frames) // 32)]
    F = [tuple(float(np.median([b[j] for b in g['b']])) for j in range(4)) for g in sorted(cl, key=lambda g: np.median([b[0] for b in g['b']]))][:3]
    out = {'faces': [[round((x + w / 2) / W_, 3), round((y + h / 2) / H_, 3)] for x, y, w, h in F], 'seg': []}
    nm = ['trái', 'giữa', 'phải'] if len(F) == 3 else ['trái', 'phải']
    if len(F) >= 2:
        ch = _chunks(_load(DA)); lab = _voice(DA, ch, len(F))
        M = np.zeros((len(frames), len(F)))
        for t in range(1, len(frames)):
            d = cv2.absdiff(frames[t][1], frames[t - 1][1])
            for j, (x, y, w, h) in enumerate(F): M[t, j] = d[int(y):int(y + h * 1.1), int(x):int(x + w)].mean()
        M = M / (np.median(M[1:], axis=0) + 1e-6); ts = np.array([t for t, _ in frames])
        sc = np.zeros((len(F), len(F)))   # điểm cử động: cụm giọng × mặt
        for c, l in zip(ch, lab):
            m = (ts >= c[0]['start']) & (ts <= c[-1].get('end', c[-1]['start'] + .3))
            if m.sum(): sc[l] += M[m].mean(axis=0) - M[m].mean()
        pm = max(itertools.permutations(range(len(F))), key=lambda p: sum(sc[i, p[i]] for i in range(len(F))))
        for c, l in zip(ch, lab):
            s_ = [round(c[0]['start'], 2), round(c[-1].get('end', c[-1]['start'] + .3), 2), int(pm[l])]
            if out['seg'] and out['seg'][-1][2] == s_[2]: out['seg'][-1][1] = s_[1]
            else: out['seg'].append(s_)
        print(f'{len(F)} người · lượt nói theo giọng (khung nhỏ tự bám):', ' · '.join(f'{x:g}–{y:g} {nm[j]}' for x, y, j in out['seg']),
              '— soát ảnh lưới; sai người → P.speaker(giây, "trái"|"phải")')
    else: print('1 người — khung nhỏ bám mặt mặc định')
    json.dump(out, open(os.path.join(DA, 'speakers.json'), 'w'))

# ---------- ranh giới xã/phường (dữ liệu 2025: Bộ NN&MT qua vietnamese-provinces-database) ----------
import math, unicodedata
RANH = os.path.join(HOME, 'ranh_66.json')
def _plain(s): return ''.join(c for c in unicodedata.normalize('NFD', s.replace('đ', 'd').replace('Đ', 'D')) if unicodedata.category(c) != 'Mn').lower().strip()
def _rdp(P, eps):
    if len(P) < 4: return P
    if P[0] == P[-1]:
        k = max(range(len(P)), key=lambda n: math.dist(P[0], P[n])); return _rdp(P[:k + 1], eps) + _rdp(P[k:], eps)[1:]
    keep = [0, len(P) - 1]; st = [(0, len(P) - 1)]
    while st:
        i, j = st.pop(); (x1, y1), (x2, y2) = P[i], P[j]; dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy) or 1e-12; bi, bd = 0, 0
        for k in range(i + 1, j):
            d = abs(dy * (P[k][0] - x1) - dx * (P[k][1] - y1)) / n
            if d > bd: bi, bd = k, d
        if bd > eps: keep.append(bi); st += [(i, bi), (bi, j)]
    return [P[k] for k in sorted(set(keep))]
def _rings(geom, eps):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [[[round(x, 5), round(y, 5)] for x, y in _rdp(p[0], eps)] for p in polys if len(p[0]) > 3]
def _ranh_data():
    if os.path.exists(RANH): return json.load(open(RANH, encoding='utf-8'))
    repo = os.path.join(HOME, 'vpd'); base = os.path.join(repo, 'json', 'geojson', '66_dak_lak')
    if not os.path.isdir(os.path.join(repo, '.git')):
        sh(f'GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 --filter=blob:none --sparse https://github.com/ThangLeQuoc/vietnamese-provinces-database {repo}')
    sh(f'git -C {repo} sparse-checkout set json/geojson/66_dak_lak')
    pv = json.load(open(os.path.join(base, '66_dak_lak.geojson'), encoding='utf-8'))['features'][0]
    D = {'tinh': _rings(pv['geometry'], .004), 'xa': {}}
    for f in sorted(glob.glob(os.path.join(base, 'wards', '*.geojson'))):
        ft = json.load(open(f, encoding='utf-8'))['features'][0]; pr = ft['properties']
        D['xa'][pr['codeName']] = {'ten': pr['name'], 'full': pr['fullName'], 'km2': pr.get('areaKm2'), 'r': _rings(ft['geometry'], .0005)}
    json.dump(D, open(RANH, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return D
def ranh(*q):   # vc.py ranh [tên…] → tải dữ liệu (lần đầu ~1–2 phút) + tra tên đúng
    D = _ranh_data()['xa']
    if not q: print(' · '.join(f"{v['full']}" for v in D.values())); return
    for s in q:
        m = [v['full'] for k, v in D.items() if _plain(s) in (_plain(v['ten']), _plain(v['full']), k.replace('_', ' '))] or \
            [v['full'] for k, v in D.items() if _plain(s) in _plain(v['full'])]
        print(f'{s} → ' + (' | '.join(m) if m else 'KHÔNG CÓ (xem: vc.py ranh)'))
TINH_ALIAS = ('dak lak', 'tinh dak lak', 'tinh', 'ca tinh', 'toan tinh')
def _dtinh():   # các xã/phường + ranh giới CẢ TỈNH Đắk Lắk (sau sáp nhập 2025, gồm Phú Yên cũ) dưới khoá '__tinh'
    R_ = _ranh_data(); D = dict(R_['xa']); D['__tinh'] = {'ten': 'Đắk Lắk', 'full': 'Đắk Lắk', 'km2': None, 'r': R_['tinh']}; return D
def _pick(D, s):
    if '__tinh' in D and _plain(s) in TINH_ALIAS: return '__tinh'
    for k, v in D.items():
        if _plain(s) in (_plain(v['ten']), _plain(v['full']), k.replace('_', ' ')): return k
    sys.exit(f'✖ không có xã/phường "{s}" — tra: vc.py ranh {s}')
def _tiles(z, x0, y0, x1, y1):   # ảnh vệ tinh GOOGLE MAPS (anh chốt 26/11/2026; Bing chỉ dự phòng khi Google lỗi; cache ~/.vucut/tiles_g) → PIL mosaic từ pixel (x0,y0) tới (x1,y1) ở zoom z
    from PIL import Image; from concurrent.futures import ThreadPoolExecutor
    cd = os.path.join(HOME, 'tiles_g'); os.makedirs(cd, exist_ok=True); tx = range(int(x0 // 256), int(x1 // 256) + 1); ty = range(int(y0 // 256), int(y1 // 256) + 1)
    def qk(x, y): return ''.join(str((((x >> i) & 1) | (((y >> i) & 1) << 1))) for i in range(z - 1, -1, -1))
    def get(xy):
        x, y = xy; f = os.path.join(cd, f'{z}_{x}_{y}.jpg')
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            subprocess.run(['curl', '-s', '--max-time', '20', '-A', 'Mozilla/5.0', '-o', f, f'https://mt{(x + y) % 4}.google.com/vt/lyrs=s&hl=vi&x={x}&y={y}&z={z}'])
            if not os.path.exists(f) or os.path.getsize(f) < 1000:   # Google lỗi → Bing dự phòng
                subprocess.run(['curl', '-s', '--max-time', '20', '-o', f, f'https://ecn.t{(x + y) % 4}.tiles.virtualearth.net/tiles/a{qk(x, y)}.jpeg?g=1'])
        return xy, f
    with ThreadPoolExecutor(12) as ex: fs = list(ex.map(get, [(x, y) for x in tx for y in ty]))
    for xy, f in fs:   # tải lại ô hỏng (mép đen)
        if not os.path.exists(f) or os.path.getsize(f) < 1000: os.path.exists(f) and os.remove(f); get(xy)
    im = Image.new('RGB', (len(tx) * 256, len(ty) * 256))
    for (x, y), f in fs:
        try: im.paste(Image.open(f).convert('RGB'), ((x - tx[0]) * 256, (y - ty[0]) * 256))
        except Exception: pass
    return im.crop((int(x0 - tx[0] * 256), int(y0 - ty[0] * 256), int(x1 - tx[0] * 256), int(y1 - ty[0] * 256)))
def _wm(lon, lat, z):   # Web Mercator → pixel
    n = 256 * 2 ** z; s = math.sin(math.radians(lat)); return (lon + 180) / 360 * n, (.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
def _b64(im, q=80):
    import io; b = io.BytesIO(); im.save(b, 'JPEG', quality=q); return base64.b64encode(b.getvalue()).decode()
def _sfx_ranh(path, d=1.0):   # "vút" quét 0.1 s (0.9→14.6 kHz) + lấp lánh 4 nốt cao rung ~37 Hz trong lúc viền vẽ (đo từ video mẫu)
    import numpy as np, wave; sr = 48000
    t = np.arange(int(sr * .1)) / sr; f = 900 * (14600 / 900) ** (t / .1); sw = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.sin(np.pi * t / .1) ** .5
    t2 = np.arange(int(sr * d)) / sr; P = [(5286, -18.4), (7048, 0), (9984, -3.9), (10573, -26.7), (11160, -21.6), (11747, -3.6), (13509, -6.1)]
    sh = sum(10 ** (g / 20) * np.sin(2 * np.pi * fr * t2 + k) for k, (fr, g) in enumerate(P)) * (.25 + .75 * (.5 + .5 * np.cos(2 * np.pi * 36.7 * t2)))
    env = np.minimum(1, t2 / .01) * np.minimum(1, (d - t2) / .04); sh *= env
    x = np.concatenate([sw / np.abs(sw).max() * .8, sh / np.abs(sh).max()]); x = x / np.abs(x).max() * .89
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()

def _sfx_count(path, d=1.2, n=26):   # tiếng đếm số: n tiếng tách cơ khí đặt theo đều giá trị của đường expo.out (dày lúc đầu, thưa dần) + chốt "ting" sáng + đệm trầm
    import numpy as np, wave; sr = 48000; rng = np.random.default_rng(7); L = int(sr * (d + 1.1)); x = np.zeros(L)
    ts = [-d / 10 * math.log2(1 - k / (n + 1)) for k in range(1, n + 1)]
    for k, t in enumerate(ts):
        m = np.arange(int(sr * .018)) / sr; f = 2600 + 1400 * k / n
        c = (np.sin(2 * np.pi * f * m) * .6 + rng.standard_normal(len(m)) * .4) * np.exp(-m * 380)
        a = int(t * sr); x[a:a + len(c)] += c * (.55 + .25 * k / n)
    te = min(d, ts[-1] + .06); m = np.arange(int(sr * 1.0)) / sr
    bell = sum(g * np.sin(2 * np.pi * f * m) * np.exp(-m * dk) for f, g, dk in [(1568, 1, 4.5), (2352, .55, 6), (3136, .35, 8), (4704, .18, 11)])
    th = np.sin(2 * np.pi * np.cumsum(90 + 60 * np.exp(-m * 40)) / sr) * np.exp(-m * 14) * .9
    a = int(te * sr); seg = (bell * .7 + th)[:L - a]; x[a:a + len(seg)] += seg
    x = x / np.abs(x).max() * .89
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()

# ---------- địa điểm & tuyến đường (OSRM đi theo đường thật · Nominatim tra tên) ----------
GEO = os.path.join(HOME, 'geo.json')
def _geo_cache():
    return json.load(open(GEO, encoding='utf-8')) if os.path.exists(GEO) else {}
def _geo_save(c): json.dump(c, open(GEO, 'w', encoding='utf-8'), ensure_ascii=False)
def _pt(p):   # (lon,lat) | khoá điểm có sẵn ('buonmathuot'…) | tên xã/phường | tên địa điểm (tra Nominatim)
    if isinstance(p, (list, tuple)): return float(p[0]), float(p[1])
    pts = json.load(open(os.path.join(VC(), 'assets', 'daklak', 'daklak.json'), encoding='utf-8'))['pts']
    if p in pts: return tuple(pts[p]['lonlat'])
    D = _ranh_data()['xa']
    for k, v in D.items():
        if _plain(p) in (_plain(v['ten']), _plain(v['full'])):
            r = max(v['r'], key=len); return sum(x for x, _ in r) / len(r), sum(y for _, y in r) / len(r)
    c = _geo_cache(); key = 'n:' + _plain(p)
    if key not in c:
        import urllib.parse
        q = urllib.parse.quote(p + ', Đắk Lắk, Việt Nam')
        r = subprocess.run(['curl', '-s', '--max-time', '20', '-A', 'vucut/1.0', f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1'], capture_output=True, text=True).stdout
        js = json.loads(r or '[]')
        if not js: sys.exit(f'✖ không tìm thấy địa điểm "{p}" — đưa (lon, lat)')
        c[key] = [float(js[0]['lon']), float(js[0]['lat'])]; _geo_save(c)
    return tuple(c[key])
def _road(wps):   # tuyến theo đường thật qua các điểm · {'line': [(lon, lat)…]} = vẽ đúng hình học cho sẵn (vd cao tốc lấy từ OSM)
    if isinstance(wps, dict): return [list(p) for p in wps['line']]
    P = [_pt(w) for w in wps]; c = _geo_cache(); key = 'r:' + ';'.join(f'{x:.4f},{y:.4f}' for x, y in P)
    if key not in c:
        r = subprocess.run(['curl', '-s', '--max-time', '30', 'https://router.project-osrm.org/route/v1/driving/' + ';'.join(f'{x},{y}' for x, y in P) + '?overview=full&geometries=geojson'], capture_output=True, text=True).stdout
        try: g = json.loads(r)['routes'][0]['geometry']['coordinates']
        except Exception: g = [list(p) for p in P]
        c[key] = [[round(x, 5), round(y, 5)] for x, y in _rdp([tuple(p) for p in g], .0002)]; _geo_save(c)
    return c[key]

def _tam(rings):   # tâm THỊ GIÁC của vùng (điểm trong vùng xa mép nhất — kiểu polylabel) trên khung bản đồ, tránh khung người nói góc phải dưới → (x, y, bán kính trong)
    import numpy as np
    seg = np.array([(r[n][0], r[n][1], r[(n + 1) % len(r)][0], r[(n + 1) % len(r)][1]) for r in rings for n in range(len(r))])
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    gx, gy = np.meshgrid(np.arange(max(80, min(xs)), min(640, max(xs)), 5.0), np.arange(max(190, min(ys)), min(630, max(ys)), 5.0))
    px, py = gx.ravel(), gy.ravel()
    if not len(px): return (sum(xs) / len(xs), sum(ys) / len(ys), 40)
    x1, y1, x2, y2 = (seg[:, k][None, :] for k in range(4)); X, Y = px[:, None], py[:, None]
    inside = (((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1 + 1e-12) + x1)).sum(1) % 2 == 1
    dx, dy = x2 - x1, y2 - y1; u = np.clip(((X - x1) * dx + (Y - y1) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
    d = np.hypot(X - x1 - u * dx, Y - y1 - u * dy).min(1)
    d = np.where(inside, d, -1) - np.where((px > 470) & (py > 540), 1e4, 0)   # né khung người nói
    k = int(d.argmax()); return float(px[k]), float(py[k]), float(max(d[k], 30))

def map_ranh(i, a, b, names=(), t_draw=None, label='', sub='', km2=False, routes=(), pins=(), center=None, km=6, d3=False, areas=(), border=(), focus=None, t_focus=None, rise=None, focus_sub=''):
    """bản đồ vệ tinh: zoom từ xa vào · xã/phường (names) viền vàng tự vẽ + vệt trắng chạy · tuyến đường (routes) xanh sáng tự vẽ · ghim (pins)
    routes=[('QUỐC LỘ 14', ['buonmathuot', 'Ea Kao'], t)] · pins=[('SÂN BAY', 'sanbaybmt', t)] · center=(điểm) km= bán kính khi không có xã"""
    D = _dtinh(); names = [names] if isinstance(names, str) else list(names); ks = [_pick(D, s) for s in names]
    t_draw = max(a + 1.2, a + .35 if t_draw is None else t_draw); DR = 1.0
    RT = [(lb, _road(w), (t if t is not None else t_draw + .3 + .4 * n)) for n, (lb, w, *t_) in enumerate(routes) for t in [t_[0] if t_ else None]]
    PN = [(lb, _pt(p), (t_[0] if t_ else t_draw + .5 + .3 * n)) for n, (lb, p, *t_) in enumerate(pins)]
    if d3: return _sat3d(i, a, b, D, ks, t_draw, label, sub, RT, PN, center, km, [(lb, _pt(p)) for lb, p in areas], [_pick(D, x) for x in ([border] if isinstance(border, str) else border)],
                          FK=_pick(D, focus) if focus else None, TF=t_focus, RISE=rise, FSUB=focus_sub)
    pts = [p for k in ks for r in D[k]['r'] for p in r] + [p for _, ln, _ in RT for p in ln] + [p for _, p, _ in PN]
    if center is not None or not pts:
        cx_, cy_ = _pt(center) if center is not None else (pts[0] if pts else (108.038, 12.667)); dl = km / 111
        pts = (pts if ks else []) + [(cx_ - dl, cy_ - dl), (cx_ + dl, cy_ + dl)]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    BX = (70, 170, 650, 640)
    z = 18
    while z > 8:
        ax, ay = _wm(x0, y1, z); bx, by = _wm(x1, y0, z)
        if (bx - ax) <= (BX[2] - BX[0]) * 1.5 and (by - ay) <= (BX[3] - BX[1]) * 1.5: break
        z -= 1
    ax, ay = _wm(x0, y1, z); bx, by = _wm(x1, y0, z); k_ = min((BX[2] - BX[0]) / max(1, bx - ax), (BX[3] - BX[1]) / max(1, by - ay))
    cxp, cyp = (ax + bx) / 2, (ay + by) / 2; ox, oy = (BX[0] + BX[2]) / 2, (BX[1] + BX[3]) / 2
    def S(lon, lat): px, py = _wm(lon, lat, z); return ox + (px - cxp) * k_, oy + (py - cyp) * k_
    def box(zz, f):
        s = k_ * 2 ** (z - zz); c = (cxp / 2 ** (z - zz), cyp / 2 ** (z - zz))
        X0, Y0 = c[0] - (ox + 720 * (f - 1) / 2) / s, c[1] - (oy + 1280 * (f - 1) / 2) / s
        return _tiles(zz, X0, Y0, X0 + 720 * f / s, Y0 + 1280 * f / s), f
    det, fd = box(z, 1.08); wid, fw = box(max(1, z - 2), 4.0)
    def path(rs, close=True): return ''.join('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in (S(*p) for p in r)) + ('Z' if close else '') for r in rs)
    def plen(r, close=True): q = [S(*p) for p in r] + ([S(*r[0])] if close else []); return sum(math.dist(q[n], q[n + 1]) for n in range(len(q) - 1))
    js = [f"tl.set('#{i}',{{autoAlpha:0}},0);", f"tl.set('#{i}',{{autoAlpha:1}},{a});"]
    tz = t_draw - .15; lap = 2.2; svg = ''
    js += [f"tl.fromTo('#{i} .cam',{{scale:{1 / 2.8:.4f},transformOrigin:'{ox:.0f}px {oy:.0f}px'}},{{scale:1,duration:{tz - a:.2f},ease:'power2.inOut'}},{a});",
           f"tl.to('#{i} .dt',{{opacity:1,duration:{min(.8, (tz - a) * .5):.2f}}},{tz - min(.8, (tz - a) * .5):.2f});",
           f"tl.fromTo('#{i} .cam',{{scale:1}},{{scale:1.04,duration:{max(.5, b - tz):.2f},ease:'none'}},{tz:.2f});"]
    def chip(x, y, txt, col, cls, t):
        w = len(txt) * 12 + 28; x = min(max(x, 50 + w / 2), 650 - w / 2); y = min(max(y, 190), 650)
        js.extend([f"tl.set('#{i} .{cls}',{{opacity:0}},0);", f"tl.to('#{i} .{cls}',{{opacity:1,duration:.3}},{t:.2f});"])
        return (f'<g class="{cls}"><rect x="{x - w / 2:.0f}" y="{y - 18:.0f}" width="{w:.0f}" height="34" rx="8" fill="rgba(8,20,14,.72)" stroke="{col}" stroke-width="2"/>'
                f'<text x="{x:.0f}" y="{y + 6:.0f}" text-anchor="middle" font-family="VCB,sans-serif" font-weight="800" font-size="19" fill="{col}">{txt}</text></g>')
    if ks:
        allp = ''.join(path(D[k]['r']) for k in ks); L = sum(plen(r) for k in ks for r in D[k]['r'])
        ccx, ccy, rin = _tam([[S(*p) for p in r] for k in ks for r in D[k]['r']])
        ttl = label or (D[ks[0]]['full'].upper() if len(ks) == 1 else ' · '.join(D[k]['ten'].upper() for k in ks))
        if km2 and len(ks) == 1 and D[ks[0]].get('km2'): sub = sub or f"{D[ks[0]]['km2']:g} km²"
        fs_ = int(max(30, min(78, 2.2 * rin / (len(ttl) * .62), .95 * rin, 600 / (len(ttl) * .64)))); hw = len(ttl) * fs_ * .32
        ccx = min(max(ccx, 60 + hw), 660 - hw); ccy = min(max(ccy + fs_ * .35, 200), 600)   # ccy: đường chân chữ → tâm chữ đúng tâm vùng
        nlap = max(0, int((b - t_draw - DR) / lap))
        svg += (f'<path class="dim" d="M0 0H720V1280H0Z{allp}" fill="#000" fill-rule="evenodd" opacity="0"/>'
                f'<path class="gl" d="{allp}" fill="none" stroke="#F0C460" stroke-width="16" stroke-linejoin="round" stroke-linecap="round" filter="url(#{i}g)" opacity=".85" stroke-dasharray="{L:.0f} {L:.0f}" stroke-dashoffset="{L:.0f}"/>'
                f'<path class="ln" d="{allp}" fill="none" stroke="#F6D37E" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{L:.0f} {L:.0f}" stroke-dashoffset="{L:.0f}"/>'
                f'<path class="cm" d="{allp}" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-dasharray="{L * .1:.0f} {L * .9:.0f}" filter="url(#{i}g2)" opacity="0"/>')
        tt = (f'<g class="tt"><text x="{ccx:.0f}" y="{ccy:.0f}" text-anchor="middle" font-family="VCB,sans-serif" font-weight="800" font-size="{fs_}" letter-spacing="1" fill="#F2CC74" '
              f'style="paint-order:stroke;stroke:rgba(0,0,0,.55);stroke-width:5px;filter:drop-shadow(0 2px 8px rgba(0,0,0,.8))">{ttl}</text>'
              + (f'<text x="{ccx:.0f}" y="{ccy + fs_ * .9:.0f}" text-anchor="middle" font-family="VCB,sans-serif" font-weight="800" font-size="{int(fs_ * .55)}" fill="#fff" '
                 f'style="paint-order:stroke;stroke:rgba(0,0,0,.6);stroke-width:4px">{sub}</text>' if sub else '') + '</g>')
        js += [f"tl.to('#{i} .dim',{{opacity:.5,duration:.5}},{tz:.2f});",
               f"tl.to('#{i} .ln',{{strokeDashoffset:0,duration:{DR},ease:'none'}},{t_draw:.2f});",
               f"tl.to('#{i} .gl',{{strokeDashoffset:0,duration:{DR},ease:'none'}},{t_draw:.2f});",
               f"tl.set('#{i} .tt',{{opacity:0,y:8}},0);", f"tl.to('#{i} .tt',{{opacity:1,y:0,duration:.4,ease:'power2.out'}},{t_draw + DR * .7:.2f});",
               f"tl.set('#{i} .cm',{{opacity:1}},{t_draw + DR:.2f});",
               f"tl.fromTo('#{i} .cm',{{strokeDashoffset:0}},{{strokeDashoffset:{-L:.0f},duration:{lap},repeat:{nlap},ease:'none'}},{t_draw + DR:.2f});"]
    else:
        tt = ''; js.append(f"tl.fromTo('#{i} .vg',{{opacity:0}},{{opacity:.45,duration:.5}},{tz:.2f});")
        svg += '<rect class="vg" width="720" height="1280" fill="#000" opacity="0"/>'
    for n, (lb, ln, t) in enumerate(RT):   # tuyến đường xanh sáng (như QUỐC LỘ 14 trong mẫu)
        L2 = plen(ln, False); d = path([ln], False); mid = S(*ln[len(ln) // 2])
        svg += (f'<path class="rg{n}" d="{d}" fill="none" stroke="#FF1A1A" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" filter="url(#{i}g)" opacity=".8" stroke-dasharray="{L2:.0f} {L2:.0f}" stroke-dashoffset="{L2:.0f}"/>'
                f'<path class="rl{n}" d="{d}" fill="none" stroke="#FF6A5A" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L2:.0f} {L2:.0f}" stroke-dashoffset="{L2:.0f}"/>')
        js += [f"tl.to('#{i} .rg{n},#{i} .rl{n}',{{strokeDashoffset:0,duration:1.1,ease:'power1.inOut'}},{t:.2f});"]
        if lb: svg += chip(mid[0], mid[1] - 30, lb, '#FF7A6B', f'rc{n}', t + .6)
    for n, (lb, p, t) in enumerate(PN):
        x, y = S(*p)
        svg += (f'<g class="pn{n}"><circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="#F2CC74" stroke="#fff" stroke-width="3"/>'
                f'<circle class="pr{n}" cx="{x:.0f}" cy="{y:.0f}" r="9" fill="none" stroke="#F2CC74" stroke-width="3"/></g>')
        js += [f"tl.set('#{i} .pn{n}',{{opacity:0}},0);", f"tl.to('#{i} .pn{n}',{{opacity:1,duration:.25}},{t:.2f});",
               f"tl.fromTo('#{i} .pr{n}',{{attr:{{r:9}},opacity:1}},{{attr:{{r:34}},opacity:0,duration:1,repeat:2}},{t:.2f});"]
        if lb: svg += chip(x, y - 34, lb, '#F2CC74', f'pc{n}', t + .1)
    html = (f'<div class="vc" data-mg="ranh" id="{i}" style="left:0;top:0;width:720px;height:1280px;z-index:7;overflow:hidden;background:#0b0c0a">'
            f'<div class="cam" style="position:absolute;left:0;top:0;width:720px;height:1280px">'
            f'<img class="wd" src="data:image/jpeg;base64,{_b64(wid.resize((1440, 2560)), 72)}" style="position:absolute;left:{-720 * (fw - 1) / 2:.0f}px;top:{-1280 * (fw - 1) / 2:.0f}px;width:{720 * fw:.0f}px;height:{1280 * fw:.0f}px"/>'
            f'<img class="dt" src="data:image/jpeg;base64,{_b64(det, 82)}" style="position:absolute;left:{-720 * (fd - 1) / 2:.0f}px;top:{-1280 * (fd - 1) / 2:.0f}px;width:{720 * fd:.0f}px;height:{1280 * fd:.0f}px;opacity:0"/></div>'
            f'<svg viewBox="0 0 720 1280" width="720" height="1280" style="position:absolute;left:0;top:0"><defs>'
            f'<filter id="{i}g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9"/></filter>'
            f'<filter id="{i}g2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.5"/></filter></defs>'
            f'{svg}{tt}<text class="cr" x="40" y="985" font-family="VCB6,sans-serif" font-weight="600" font-size="14" fill="rgba(255,255,255,.55)">Ảnh vệ tinh: Google · '
            + ('Ranh giới 2025: Bộ NN&amp;MT' if ks else '') + (' · ' if ks and RT else '') + ('Tuyến: OpenStreetMap' if RT else '') + '</text></svg></div>')
    js.append(f"tl.set('#{i}',{{autoAlpha:0}},{b});")
    if DA_:
        import cine
        if ks or RT: os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_ranh(os.path.join(DA_, 'sfx', 'ranh.wav'), DR)
        if ks: cine.sfx(t_draw - .05, 'ranh')
        for _, _, t in RT: cine.sfx(t - .05, 'ranh')   # tuyến đường: cùng âm vẽ viền (anh yêu cầu 26/11/2026)
    return html, js, [(a, 'whoosh')] + [(t, 'pop') for _, _, t in PN]

# ---------- BẢN ĐỒ VỆ TINH 3D (P.sat(..., d3=True)) — anh duyệt mẫu Liên Sơn Lắk 26/11/2026 ----------
# Ảnh Google + độ cao AWS Terrain (phóng ×1.8) dựng bằng three.js → chuỗi khung DA/s3d/<mã>/NNNN.jpg (đệm theo mã, build lại không dựng lại)
# → trình dựng (preview.mjs đã vá ở setup) lắp khung theo giây qua <img data-seq>. Chỉ xã/phường; có routes/pins → tự về 2D.
S3D_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:LPV;src:url(LPV.ttf)}html,body{margin:0;width:720px;height:1280px;overflow:hidden;background:#0b1016}canvas{position:absolute;left:0;top:0}
#vig{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 45%,rgba(0,0,0,0) 45%,rgba(0,0,0,.55) 100%),linear-gradient(180deg,rgba(0,0,0,.5) 0%,rgba(0,0,0,0) 18%,rgba(0,0,0,0) 70%,rgba(0,0,0,.6) 100%)}
#lab{position:absolute;left:0;top:0;text-align:center;opacity:0;white-space:nowrap}
#lab .n,#lab .k,#lab .s,.foil{font-family:LPV,serif;font-style:italic;letter-spacing:1px;background:linear-gradient(100deg,#7a5a24 0%,#c9a25a 14%,#f6e2a2 24%,#fff6d6 28%,#d9b468 38%,#8c6a2c 52%,#e8c983 64%,#fff1c2 70%,#b88f45 82%,#6e5020 100%);background-size:240% 100%;background-position:100% 0;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;padding:.22em .06em .26em;margin:-.22em -.06em -.26em;filter:drop-shadow(0 1.5px 0 rgba(70,48,12,.95)) drop-shadow(0 8px 18px rgba(0,0,0,.7))}
#lab .k{letter-spacing:4px}#lab .k:empty,#lab .s:empty{display:none}
</style></head><body><div id="vig"></div><div id="lab"><div class="k" id="kk"></div><div class="n" id="nm"></div><div class="s" id="ss"></div></div>
<script type="importmap">{"imports":{"three":"./node_modules/three/build/three.module.js","three/addons/":"./node_modules/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';import {Line2} from 'three/addons/lines/Line2.js';import {LineGeometry} from 'three/addons/lines/LineGeometry.js';import {LineMaterial} from 'three/addons/lines/LineMaterial.js';
const D=await (await fetch('data.json')).json();const nm=document.getElementById('nm');nm.textContent=D.name;nm.style.fontSize=Math.min(58,600/(D.name.length*.62))+'px';
document.getElementById('kk').textContent=D.kicker;document.getElementById('ss').textContent=D.sub;
const W=720,H=1280,S=D.size/1000,G=D.G,EX=1.8,emin=D.emin;
const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setSize(W,H);r.setPixelRatio(1);document.body.prepend(r.domElement);r.outputColorSpace=THREE.SRGBColorSpace;
const sc=new THREE.Scene();sc.background=new THREE.Color(0x0b1016);sc.fog=new THREE.Fog(0x0b1016,60,140);const cam=new THREE.PerspectiveCamera(38,W/H,S*.001,S*10);
function mkH(E,G){return (u,v)=>{const x=Math.min(G-1.001,Math.max(0,u*(G-1))),y=Math.min(G-1.001,Math.max(0,v*(G-1)));const i=Math.floor(x),j=Math.floor(y),fx=x-i,fy=y-j,e=(a,b)=>Math.max(emin,E[b*G+a]);
 return ((e(i,j)*(1-fx)+e(i+1,j)*fx)*(1-fy)+(e(i,j+1)*(1-fx)+e(i+1,j+1)*fx)*fy-emin)/1000*EX}}
const hAt=mkH(D.elev,G),h2=mkH(D.elev2,D.G2);
function plane(Sz,Gn,hf,dz){const g=new THREE.PlaneGeometry(Sz,Sz,Gn-1,Gn-1);g.rotateX(-Math.PI/2);const p=g.attributes.position;for(let k=0;k<p.count;k++){p.setY(k,hf(p.getX(k)/Sz+.5,p.getZ(k)/Sz+.5)+dz)}return g}
const L=new THREE.TextureLoader();const ld=async f=>{const t=await L.loadAsync(f);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t};
const VS=`varying vec2 vUv;
#include <fog_pars_vertex>
void main(){vUv=uv;vec4 mvPosition=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*mvPosition;
#include <fog_vertex>
}`;
const U={tex:{value:await ld('sat.jpg')},mask:{value:await L.loadAsync('mask.png')},mask2:{value:await L.loadAsync(D.frings&&D.frings.length?'mask2.png':'mask.png')},sw:{value:1},dim:{value:0},fogColor:{value:sc.fog.color},fogNear:{value:1},fogFar:{value:2}};
const mat=new THREE.ShaderMaterial({uniforms:U,fog:true,transparent:true,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4,vertexShader:VS,fragmentShader:`uniform sampler2D tex,mask,mask2;uniform float dim,sw;varying vec2 vUv;
#include <fog_pars_fragment>
void main(){vec3 c=texture2D(tex,vUv).rgb;float m=mix(texture2D(mask2,vUv).r,texture2D(mask,vUv).r,sw);c*=mix(1.,mix(.3,1.15,m),dim);c=mix(vec3(dot(c,vec3(.3,.59,.11))),c,1.+.25*m*dim);
c=mix(c,vec3(dot(c,vec3(.3,.59,.11))),dim*(1.-m)*.6);vec2 e=min(vUv,1.-vUv);gl_FragColor=vec4(c,smoothstep(0.,.12,min(e.x,e.y)));
#include <colorspace_fragment>
#include <fog_fragment>
}`});const md=new THREE.Mesh(plane(S,G,hAt,0),mat);md.renderOrder=2;sc.add(md);
const S2=D.size2/1000;const UW={tex:{value:await ld('satw.jpg')},dim:{value:0},fogColor:{value:sc.fog.color},fogNear:{value:1},fogFar:{value:2}};
const matw=new THREE.ShaderMaterial({uniforms:UW,fog:true,vertexShader:VS,fragmentShader:`uniform sampler2D tex;uniform float dim;varying vec2 vUv;
#include <fog_pars_fragment>
void main(){vec3 c=texture2D(tex,vUv).rgb;c*=mix(1.,.3,dim);c=mix(c,vec3(dot(c,vec3(.3,.59,.11))),dim*.6);gl_FragColor=vec4(c,1.);
#include <colorspace_fragment>
#include <fog_fragment>
}`});const mw=new THREE.Mesh(plane(S2,D.G2,(u,v)=>h2(u,v),-S*.0037),matw);mw.renderOrder=1;sc.add(mw);
const lines=[];let NS=0;for(const R of D.rings){const pts=[];for(let n=0;n<=R.length;n++){const[a,b]=R[n%R.length];pts.push((a-.5)*S,hAt(a,b)+S*.0013,(b-.5)*S)}
 const mk=(w,col,op)=>{const lg=new LineGeometry();lg.setPositions(pts);const lm=new LineMaterial({color:col,linewidth:w,transparent:true,opacity:op,depthTest:false});lm.resolution.set(W,H);const l=new Line2(lg,lm);l.renderOrder=5;sc.add(l);return l};
 const n=pts.length/3-1;const core=mk(5,0xffffff,1);{const cols=[];let acc=0;for(let k=0;k<pts.length/3;k++){if(k)acc+=Math.hypot(pts[3*k]-pts[3*k-3],pts[3*k+2]-pts[3*k-1]);const f=.5+.5*Math.sin(acc/(S*.025));const c0=[.50,.35,.13],c1=[1,.93,.70];cols.push(c0[0]+(c1[0]-c0[0])*f,c0[1]+(c1[1]-c0[1])*f,c0[2]+(c1[2]-c0[2])*f)}core.geometry.setColors(cols);core.material.vertexColors=true;core.material.needsUpdate=true}
 lines.push({pts,n,glow:mk(16,0xC9A25A,.35),core,hot:mk(8,0xFFF1C2,.85)});NS+=n}
const FL=[];for(const R of (D.frings||[])){const pts=[];for(let n=0;n<=R.length;n++){const[a,b]=R[n%R.length];pts.push((a-.5)*S,hAt(a,b)+S*.0013,(b-.5)*S)}
 const mk=(w,col,op)=>{const lg=new LineGeometry();lg.setPositions(pts);const lm=new LineMaterial({color:col,linewidth:w,transparent:true,opacity:op,depthTest:false});lm.resolution.set(W,H);const l=new Line2(lg,lm);l.renderOrder=5;sc.add(l);return l};
 FL.push({pts,n:pts.length/3-1,glow:mk(14,0xC9A25A,.35),core:mk(4.5,0xF6E2A2,1),hot:mk(7,0xFFF1C2,.85)})}
const RTS=[];for(const Q of (D.routes||[])){const pts=[];for(const[a,b]of Q.pts)pts.push((a-.5)*S,hAt(a,b)+S*.0018,(b-.5)*S);
 const mk=(w,col,op)=>{const lg=new LineGeometry();lg.setPositions(pts);const lm=new LineMaterial({color:col,linewidth:w,transparent:true,opacity:op,depthTest:false});lm.resolution.set(W,H);const l=new Line2(lg,lm);l.renderOrder=6;sc.add(l);return l};
 const n=pts.length/3-1,NR=(D.routes||[]).length,fr=NR>1?.58-.16*RTS.length/(NR-1):.5,m=Q.pts[Math.min(Q.pts.length-1,Math.floor(Q.pts.length*fr))];RTS.push({n,td:Q.td,glow:mk(18,0xFF1A1A,.6),core:mk(5.5,0xFF5A4A,1),hot:mk(1.6,0xFFE0D8,.95),mid:new THREE.Vector3((m[0]-.5)*S,hAt(m[0],m[1]),(m[1]-.5)*S),el:Q.lab?chip(Q.lab,'#FF7A6B'):null})}
for(const B of (D.borders||[])){const pts=[];for(const[u,v]of B)pts.push((u-.5)*S,hAt(u,v)+S*.0012,(v-.5)*S);const lg=new LineGeometry();lg.setPositions(pts);
 const lm=new LineMaterial({color:0xffffff,linewidth:2.2,transparent:true,opacity:.75,depthTest:false,dashed:true,dashSize:S*.006,gapSize:S*.004});lm.resolution.set(W,H);const l=new Line2(lg,lm);l.computeLineDistances();l.renderOrder=4;sc.add(l)}
const ARS=[];for(const Q of (D.areas||[])){const[u,v]=Q.p;const e=document.createElement('div');e.className='foil';e.style.cssText='position:absolute;left:0;top:0;opacity:0;white-space:nowrap;font-size:30px;letter-spacing:2px';
 e.textContent=Q.lab;document.body.appendChild(e);ARS.push({el:e,v:new THREE.Vector3((u-.5)*S,hAt(u,v),(v-.5)*S)})}
const PNS=[];for(const Q of (D.pins||[])){const[a,b]=Q.p;PNS.push({td:Q.td,v:new THREE.Vector3((a-.5)*S,hAt(a,b),(b-.5)*S),el:chip(Q.lab||'','#F2CC74',true)})}
function chip(t,col,dot){const e=document.createElement('div');e.style.cssText='position:absolute;left:0;top:0;opacity:0;white-space:nowrap;text-align:center';
 e.innerHTML=dot?`<div style="display:flex;align-items:center;gap:8px"><div style="flex:none;width:18px;height:18px;border-radius:50%;background:#F2CC74;border:3px solid #fff;box-shadow:0 0 14px #F2CC74"></div>${t?`<div style="padding:6px 14px;border-radius:8px;background:rgba(8,20,14,.72);border:2px solid ${col};color:${col};font:800 19px LPV,sans-serif;letter-spacing:.5px">${t}</div>`:''}</div>`:(t?`<div style="display:inline-block;padding:6px 14px;border-radius:8px;background:rgba(8,20,14,.72);border:2px solid ${col};color:${col};font:800 19px LPV,sans-serif;letter-spacing:.5px">${t}</div>`:'');document.body.appendChild(e);return e}
function place(e,v,op,dot){const p=v.clone().project(cam);const x=Math.min(600,Math.max(110,(p.x+1)/2*W)),y=Math.min(640,Math.max(220,(1-p.y)/2*H));e.style.opacity=op;e.style.transform=dot?`translate(${x}px,${y}px) translate(-12px,-50%)`:`translate(${x}px,${y}px) translate(-50%,-130%)`}
const ctr=new THREE.Vector3((D.ctr[0]-.5)*S,hAt(D.ctr[0],D.ctr[1]),(D.ctr[1]-.5)*S);const lab=document.getElementById('lab');
const E=x=>x<0?0:x>1?1:x*x*(3-2*x),io=x=>x<0?0:x>1?1:1-Math.pow(1-x,3);const TD=D.td,TZ=Math.max(1.,Math.min(2.2,TD+.4));
// anh 26/11: bản đồ hiện HẾT vùng/tuyến trong khung đồ hoạ (x 60–600, y 200–620), né khung tivi góc phải dưới
const FP=[];for(const o of lines)for(let k=0;k<o.pts.length;k+=3)FP.push(new THREE.Vector3(o.pts[k],o.pts[k+1],o.pts[k+2]));
for(const Q of (D.routes||[]))for(const[u,v]of Q.pts)FP.push(new THREE.Vector3((u-.5)*S,hAt(u,v),(v-.5)*S));for(const o of PNS)FP.push(o.v);
let FM=1,OX=0,OY=0;const DUR=D.dur||6;
function setCam(t,m,ox,oy,c=ctr,tz=TZ){const a=io(t/tz);const dist=S*m*(1.75-.45*a);const pitch=(89-43*a)*Math.PI/180;const yaw=D.yaw+(t-DUR/2)*1.2*Math.PI/180;
 sc.fog.near=dist*1.15;sc.fog.far=dist*2.8;cam.far=dist*4;cam.clearViewOffset();if(ox||oy)cam.setViewOffset(W,H,ox*a,oy*a,W,H);cam.updateProjectionMatrix();
 cam.position.set(c.x+dist*Math.cos(pitch)*Math.sin(yaw),c.y+dist*Math.sin(pitch),c.z+dist*Math.cos(pitch)*Math.cos(yaw));cam.lookAt(c);cam.updateMatrixWorld();return a}
function bb(t,m,c=ctr,PP=FP,tz=TZ){setCam(t,m,0,0,c,tz);let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const v of PP){const p=v.clone().project(cam);const x=(p.x+1)/2*W,y=(1-p.y)/2*H;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}return[x0,y0,x1,y1]}
if(FP.length){const ts=D.rise?[D.rise[1],(D.rise[1]+DUR)/2,DUR-.1]:[Math.max(TZ,DUR*.35),Math.max(TZ,DUR*.65),Math.max(TZ,DUR-.1)];const big=m=>{let w=0,h=0;for(const t of ts){const q=bb(t,m);w=Math.max(w,q[2]-q[0]);h=Math.max(h,q[3]-q[1])}return Math.max(w/570,h/470)};
 for(let it=0;it<40;it++){const k=big(FM);if(Math.abs(k-1)<.015)break;FM*=Math.pow(k,.85)}
 let cx=0,cy=0;for(const t of ts){const q=bb(t,FM);cx+=(q[0]+q[2])/6;cy+=(q[1]+q[3])/6}OX=cx-330;OY=cy-420}
const TZf=Math.max(1.,Math.min(2.2,(D.tf||0)+.4));const ctrF=new THREE.Vector3((D.fctr[0]-.5)*S,hAt(D.fctr[0],D.fctr[1]),(D.fctr[1]-.5)*S);let FMf=1,OXf=0,OYf=0;
if(D.rise&&FL.length){const FPf=[];for(const o of FL)for(let k=0;k<o.pts.length;k+=3)FPf.push(new THREE.Vector3(o.pts[k],o.pts[k+1],o.pts[k+2]));const ts=[TZf,(TZf+D.rise[0])/2,D.rise[0]];
 const big=m=>{let w=0,h=0;for(const t of ts){const q=bb(t,m,ctrF,FPf,TZf);w=Math.max(w,q[2]-q[0]);h=Math.max(h,q[3]-q[1])}return Math.max(w/520,h/430)};
 for(let it=0;it<40;it++){const k=big(FMf);if(Math.abs(k-1)<.015)break;FMf*=Math.pow(k,.85)}
 let cx=0,cy=0;for(const t of ts){const q=bb(t,FMf,ctrF,FPf,TZf);cx+=(q[0]+q[2])/6;cy+=(q[1]+q[3])/6}OXf=cx-330;OYf=cy-420}
const SS5=x=>{x=x<0?0:x>1?1:x;return x*x*x*(x*(6*x-15)+10)};
function camAt(t){if(!D.rise)return setCam(t,FM,OX,OY);const[R0,R1]=D.rise;if(t<=R0)return setCam(t,FMf,OXf,OYf,ctrF,TZf);const k=SS5((t-R0)/(R1-R0));if(k>=1)return setCam(t,FM,OX,OY);
 setCam(R0,FMf,OXf,OYf,ctrF,TZf);const p1=cam.position.clone(),c1=ctrF.clone();setCam(t,FM,OX,OY);const p2=cam.position.clone(),c2=ctr.clone();
 const d1=p1.clone().sub(c1),d2=p2.clone().sub(c2);const L1=d1.length(),L2=d2.length();const Lk=L1*Math.pow(L2/L1,k);const dir=d1.normalize().lerp(d2.normalize(),k).normalize();const c=c1.lerp(c2,k);
 const ox=OXf+(OX-OXf)*k,oy=OYf+(OY-OYf)*k;sc.fog.near=Lk*1.15;sc.fog.far=Lk*2.8;cam.far=Lk*4;cam.clearViewOffset();cam.setViewOffset(W,H,ox,oy,W,H);cam.updateProjectionMatrix();
 cam.position.copy(c.clone().add(dir.multiplyScalar(Lk)));cam.lookAt(c);cam.updateMatrixWorld();return 1}
const FLB=document.createElement('div');FLB.style.cssText='position:absolute;left:0;top:0;opacity:0;white-space:nowrap;text-align:center';
FLB.innerHTML=D.fname?`<div class="foil" style="font-size:58px">${D.fname}</div>`+(D.fsub?`<div class="foil" style="font-size:20px;letter-spacing:2px;margin-top:4px">${D.fsub}</div>`:''):'';document.body.appendChild(FLB);
// anh 26/11: tên + chú thích nằm GỌN trong ranh giới, đặt ở tâm thị giác vùng, cỡ chữ tự vừa
const KK=document.getElementById('kk'),SS=document.getElementById('ss');
function setFS(f){nm.style.fontSize=f+'px';KK.style.fontSize=Math.max(11,f*.3)+'px';SS.style.fontSize=Math.max(12,f*.4)+'px'}
function inPoly(x,y,P){let c=false;for(const R of P)for(let i=0,j=R.length-1;i<R.length;j=i++){const[xi,yi]=R[i],[xj,yj]=R[j];if((yi>y)!=(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)c=!c}return c}
function dEdge(x,y,P){let m=1e9;for(const R of P)for(let i=0,j=R.length-1;i<R.length;j=i++){const[ax,ay]=R[j],[bx,by]=R[i];const dx=bx-ax,dy=by-ay;const u=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));m=Math.min(m,Math.hypot(x-ax-u*dx,y-ay-u*dy))}return m}
let LP=null;await document.fonts.ready;
if(D.rings.length){const tr=Math.min(DUR-.2,TD+1.4);setCam(tr,FM,OX,OY);
 const P=lines.map(o=>{const q=[];for(let k=0;k<o.pts.length;k+=3){const p=new THREE.Vector3(o.pts[k],o.pts[k+1],o.pts[k+2]).project(cam);q.push([(p.x+1)/2*W,(1-p.y)/2*H])}return q});
 const F=P.flat(),X0=Math.max(40,Math.min(...F.map(p=>p[0]))),X1=Math.min(620,Math.max(...F.map(p=>p[0]))),Y0=Math.max(170,Math.min(...F.map(p=>p[1]))),Y1=Math.min(640,Math.max(...F.map(p=>p[1])));
 let best=null;
 for(let fs=64;fs>=16&&!best;fs-=2){setFS(fs);const w=lab.offsetWidth+18,h=lab.offsetHeight+10;let bd=-1;
  for(let y=Y0+h/2;y<=Y1-h/2;y+=5)for(let x=X0+w/2;x<=X1-w/2;x+=5){let ok=true;
   for(let q=0;q<=10&&ok;q++){const f=q/10;for(const[px,py]of[[x-w/2+w*f,y-h/2],[x-w/2+w*f,y+h/2],[x-w/2,y-h/2+h*f],[x+w/2,y-h/2+h*f]])if(!inPoly(px,py,P)){ok=false;break}}
   if(!ok)continue;const d=dEdge(x,y,P);if(d>bd){bd=d;best={x,y,fs}}}}
 if(!best){setFS(16);let bd=-1;for(let y=Y0;y<=Y1;y+=5)for(let x=X0;x<=X1;x+=5)if(inPoly(x,y,P)){const d=dEdge(x,y,P);if(d>bd){bd=d;best={x,y,fs:16}}}}
 if(best){setFS(best.fs);const rc=new THREE.Raycaster();rc.setFromCamera(new THREE.Vector2(best.x/W*2-1,1-best.y/H*2),cam);const hit=rc.intersectObject(md);LP=hit.length?hit[0].point:null}}
window.renderAt=t=>{const a=camAt(t);const dist=S*FM*(1.75-.45*a);
 if(FL.length){U.dim.value=UW.dim.value=E((t-D.tf+.1)/.9);U.sw.value=E((t-TD+.1)/.9)}else U.dim.value=UW.dim.value=D.rings.length?E((t-TD+.1)/.9):E((t-TD+.1)/.9)*.25;
 for(const o of RTS){const d2=io((t-o.td)/1.1);const ns=Math.floor(d2*o.n);o.core.geometry.instanceCount=ns;o.glow.geometry.instanceCount=ns;o.hot.geometry.instanceCount=ns;o.glow.material.opacity=.5+.15*Math.sin(t*5)}const d=io((t-TD)/1.0);
 for(const o of lines){const ns=Math.floor(d*o.n);o.core.geometry.instanceCount=ns;o.glow.geometry.instanceCount=ns;let hs,he;
  if(d<1){he=ns;hs=Math.max(0,ns-6)}else{hs=Math.floor(((t-TD-1)/2.2%1)*o.n);he=hs+10}
  const seg=[];for(let k=Math.min(hs,o.n);k<=Math.min(he,o.n);k++)seg.push(o.pts[3*k],o.pts[3*k+1],o.pts[3*k+2]);
  if(seg.length>=6){o.hot.visible=true;o.hot.geometry.dispose();o.hot.geometry=new LineGeometry();o.hot.geometry.setPositions(seg)}else o.hot.visible=false;o.glow.material.opacity=.28+.12*Math.sin(t*5)}
 {const df=io((t-D.tf)/1.0);for(const o of FL){const ns=Math.floor(df*o.n);o.core.geometry.instanceCount=ns;o.glow.geometry.instanceCount=ns;let hs,he;if(df<1){he=ns;hs=Math.max(0,ns-6)}else{hs=Math.floor(((t-D.tf-1)/2.2%1)*o.n);he=hs+10}
  const seg=[];for(let k=Math.min(hs,o.n);k<=Math.min(he,o.n);k++)seg.push(o.pts[3*k],o.pts[3*k+1],o.pts[3*k+2]);if(seg.length>=6){o.hot.visible=true;o.hot.geometry.dispose();o.hot.geometry=new LineGeometry();o.hot.geometry.setPositions(seg)}else o.hot.visible=false;o.glow.material.opacity=.28+.12*Math.sin(t*5)}}
 r.render(sc,cam);for(const o of RTS)if(o.el)place(o.el,o.mid,E((t-o.td-.6)/.3));for(const o of PNS)place(o.el,o.v,E((t-o.td)/.25),true);for(const o of ARS){const p=o.v.clone().project(cam);const x=Math.min(560,Math.max(160,(p.x+1)/2*W)),y=Math.min(620,Math.max(230,(1-p.y)/2*H));o.el.style.opacity=E((t-TD+.2)/.5)*.92;o.el.style.transform=`translate(${x}px,${y}px) translate(-50%,-50%)`}const sp=ctr.clone().add(new THREE.Vector3(0,S*.016,0)).project(cam);
 if(LP){const q=LP.clone().project(cam);lab.style.left=((q.x+1)/2*W)+'px';lab.style.top=((1-q.y)/2*H)+'px'}else if(D.rings.length){lab.style.left=Math.min(560,Math.max(160,(sp.x+1)/2*W))+'px';lab.style.top=Math.min(560,Math.max(280,(1-sp.y)/2*H))+'px'}else{lab.style.left='360px';lab.style.top='168px'}
 const la=E((t-TD-.8)/.5);lab.style.opacity=la;{const bp=(100-100*E((t-TD-.6)/1.8))+'% 0';for(const el of [nm,KK,SS])el.style.backgroundPosition=bp;for(const o of ARS)o.el.style.backgroundPosition=bp}lab.style.transform=`translate(-50%,-50%) translateY(${(1-la)*20}px) scale(${.92+.08*la})`;
 if(D.fname){const q=ctrF.clone().project(cam);FLB.style.opacity=E((t-D.tf-.8)/.5)*(D.rise?1-E((t-D.rise[0])/.5):1);FLB.style.transform=`translate(${Math.min(560,Math.max(160,(q.x+1)/2*W))}px,${Math.min(600,Math.max(240,(1-q.y)/2*H))}px) translate(-50%,-50%)`;const bp=(100-100*E((t-D.tf-.6)/1.8))+'% 0';for(const el of FLB.children)el.style.backgroundPosition=bp}};
window.ready=true;
</script></body></html>"""
S3D_MJS = r"""import { createRequire } from 'module'; import fs from 'fs'; import path from 'path'; import os from 'os'; import http from 'http'; import { execSync } from 'child_process';
function loadPlaywright() { const bases = [path.join(os.homedir(), '.vucut', 'node') + '/', import.meta.url, process.cwd() + '/'];
  try { bases.push(path.dirname(execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()) + '/'); } catch {}
  for (const b of bases) { try { return createRequire(b)('playwright'); } catch {} } console.error('✖ thiếu playwright'); process.exit(2); }
const { chromium } = loadPlaywright(); const [dir, nS] = process.argv.slice(2); const N = +nS;
const MT = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.ttf': 'font/ttf' };
const srv = http.createServer((q, s) => { const f = path.join(dir, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, { 'Content-Type': MT[path.extname(f)] || 'application/octet-stream' }); s.end(d); } }); });
await new Promise(r => srv.listen(0, r)); const port = srv.address().port;
const args = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--use-gl=angle'];
let b; try { b = await chromium.launch({ args }); } catch { b = await chromium.launch({ args, executablePath: '/usr/bin/google-chrome' }); }
const pg = await b.newPage({ viewport: { width: 720, height: 1280 } }); pg.on('pageerror', e => console.error('✖ 3D:', String(e)));
await pg.goto(`http://localhost:${port}/index.html`); await pg.waitForFunction('window.ready===true', null, { timeout: 180000 }); await pg.waitForTimeout(400);
for (let k = 0; k < N; k++) { await pg.evaluate(t => renderAt(t), k / 30); await pg.screenshot({ path: path.join(dir, String(k).padStart(4, '0') + '.jpg'), type: 'jpeg', quality: 90 }); }
await b.close(); srv.close(); fs.writeFileSync(path.join(dir, 'done'), String(N)); console.log('✓ 3D', N, 'khung');"""
PREVIEW_PATCH = ("    window.__timelines.master.seek(t, false);\n  }, [frameFile",
                 "    window.__timelines.master.seek(t, false);\n"
                 "    for (const el of document.querySelectorAll('img[data-seq]')) {   // vucut-tools: chuỗi khung dựng sẵn (bản đồ 3D)\n"
                 "      const src = el.dataset.seq.replace('%04d', String(+el.dataset.f || 0).padStart(4, '0'));\n"
                 "      if (el.getAttribute('src') !== src) { el.setAttribute('src', src); await el.decode().catch(() => {}); } }\n"
                 "  }, [frameFile")
def _skill_copy(vc):   # chép skill sang ~/.vucut/skill + vá preview.mjs (lắp chuỗi khung 3D) — skill gốc chỉ đọc
    dst = os.path.join(HOME, 'skill')
    if os.path.abspath(vc) != dst: subprocess.run(['rm', '-rf', dst]); shutil.copytree(vc, dst)
    pm = os.path.join(dst, 'scripts', 'preview.mjs'); s = open(pm, encoding='utf-8').read()
    if PREVIEW_PATCH[0] in s: open(pm, 'w', encoding='utf-8').write(s.replace(PREVIEW_PATCH[0], PREVIEW_PATCH[1], 1))
    else: print('  ⚠ không vá được preview.mjs — bản đồ 3D sẽ đứng hình'); 
    return dst
def _three():
    d = os.path.join(HOME, 'three')
    if not os.path.exists(os.path.join(d, 'node_modules', 'three', 'build', 'three.module.js')):
        os.makedirs(d, exist_ok=True); subprocess.run('npm i -s three@0.160.0', shell=True, cwd=d, capture_output=True)
    return os.path.join(d, 'node_modules')
def _zfor(span14, target):   # zoom sao cho bề ngang vùng ≈ target px
    return int(max(6, min(18, 14 + math.floor(math.log2(target / max(1, span14))))))
def _elev(z, x0, y0, x1, y1):   # độ cao AWS Terrain (terrarium) → mảng mét
    import numpy as np; from PIL import Image
    cd = os.path.join(HOME, 'dem'); os.makedirs(cd, exist_ok=True); tx = range(int(x0 // 256), int(x1 // 256) + 1); ty = range(int(y0 // 256), int(y1 // 256) + 1)
    from concurrent.futures import ThreadPoolExecutor
    def get(xy):
        f = os.path.join(cd, f'{z}_{xy[0]}_{xy[1]}.png')
        if not os.path.exists(f) or os.path.getsize(f) < 100: subprocess.run(['curl', '-s', '--max-time', '20', '-o', f, f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{xy[0]}/{xy[1]}.png'])
        return xy, f
    with ThreadPoolExecutor(12) as ex: fs = list(ex.map(get, [(x, y) for x in tx for y in ty]))
    A = np.zeros((len(ty) * 256, len(tx) * 256))
    for (x, y), f in fs:
        try: a = np.asarray(Image.open(f).convert('RGB')).astype(float); A[(y - ty[0]) * 256:(y - ty[0] + 1) * 256, (x - tx[0]) * 256:(x - tx[0] + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        except Exception: pass
    return A[int(y0 - ty[0] * 256):int(y1 - ty[0] * 256), int(x0 - tx[0] * 256):int(x1 - tx[0] * 256)]
def _sat3d(i, a, b, D, ks, t_draw, label, sub, RT=(), PN=(), center=None, km=6, AR=(), BK=(), FK=None, TF=None, RISE=None, FSUB=''):   # FK: xã mở đầu cận cảnh, TF giây vẽ viền xã, RISE=(t0,t1) camera bay lên toàn cảnh rồi vẽ viền chính ở t_draw (anh 27/11)
    import numpy as np, hashlib; from PIL import Image, ImageDraw, ImageFilter
    Image.MAX_IMAGE_PIXELS = None
    R = [r for k in ks for r in D[k]['r']]; P = [p for r in R for p in r] + [p for _, ln, _ in RT for p in ln] + [p for _, p, _ in PN]
    if center is not None or not P:
        cx_, cy_ = _pt(center) if center is not None else (108.038, 12.667); dl = km / 111; P = P + [(cx_ - dl, cy_ - dl), (cx_ + dl, cy_ + dl)]
    xs = [p[0] for p in P]; ys = [p[1] for p in P]; lat = (min(ys) + max(ys)) / 2
    one = len(ks) == 1; full = D[ks[0]]['full'] if one else ''
    kick = '' if not one or ks[0] == '__tinh' else (full.split()[0].upper() if full and _plain(full) != _plain(D[ks[0]]['ten']) else '')
    if ks: name = label or (('TỈNH ' if ks[0] == '__tinh' else '') + D[ks[0]]['ten'].upper() if one else ' · '.join(D[k]['ten'].upper() for k in ks))
    else: name, sub = (label or sub or ''), ''
    dur = b - a; td = t_draw - a; N = int(math.ceil(dur * 30)) + 1
    key = hashlib.md5(json.dumps([ks, round(dur, 2), round(td, 2), name, kick, sub, [(lb, ln, round(t - a, 2)) for lb, ln, t in RT], [(lb, p, round(t - a, 2)) for lb, p, t in PN], AR, BK, 'v10' + MAU['k'] + json.dumps(PAL[MAU['k']], sort_keys=True), FK, TF and round(TF - a, 2), RISE and [round(x - a, 2) for x in RISE], FSUB]).encode()).hexdigest()[:10]
    root = DA_ or HOME; jd = os.path.join(root, 's3d', key)
    if not os.path.exists(os.path.join(jd, 'done')):
        os.makedirs(jd, exist_ok=True); print(f'  · dựng bản đồ 3D {name} ({N} khung, ~{N * .45:.0f} s)…')
        ax, ay = _wm(min(xs), max(ys), 14); bx, by = _wm(max(xs), min(ys), 14); cx, cy = (ax + bx) / 2, (ay + by) / 2; half = max(bx - ax, by - ay) * 1.25
        mpp = 156543.03 * math.cos(math.radians(lat)) / 2 ** 14; size = 2 * half * mpp
        def layer(K, target, N_):
            z = _zfor(2 * half * K, target); f = 2 ** (14 - z); h = half * K / f
            im = _tiles(z, cx / f - h, cy / f - h, cx / f + h, cy / f + h).resize((N_, N_), Image.LANCZOS)
            ze = min(13, _zfor(2 * half * K, 900)); fe = 2 ** (14 - ze); he = half * K / fe
            E = _elev(ze, cx / fe - he, cy / fe - he, cx / fe + he, cy / fe + he)
            return np.asarray(im).astype(float) / 255, np.clip(np.array(Image.fromarray(E.astype(np.float32)).resize((256, 256), Image.BILINEAR)), 0, None)   # biển phẳng
        def shade(s, Eg, sz):
            gy, gx = np.gradient(Eg, sz / 256); az, al = math.radians(315), math.radians(40); sl = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
            hs = np.clip(np.sin(al) * np.cos(sl) + np.cos(al) * np.sin(sl) * np.cos(az - asp), 0, 1)
            h = np.asarray(Image.fromarray((hs * 255).astype(np.uint8)).resize(s.shape[:2][::-1], Image.BILINEAR)).astype(float)[..., None] / 255
            return Image.fromarray((np.clip(((s * (.55 + .65 * h)) * 1.08 - .5) * 1.12 + .5, 0, 1) * 255).astype(np.uint8))
        s1, E1 = layer(1, 8000, 6144) if FK else layer(1, 5000, 4096); s2, E2 = layer(4, 4000, 4096)
        shade(s1, E1, size).save(os.path.join(jd, 'sat.jpg'), quality=90); shade(s2, E2, size * 4).save(os.path.join(jd, 'satw.jpg'), quality=88)
        def tp(lon, la): px, py = _wm(lon, la, 14); return ((px - cx + half) / (2 * half), (py - cy + half) / (2 * half))
        m = Image.new('L', (4096, 4096), 0); dr = ImageDraw.Draw(m)
        for r in R: dr.polygon([(u * 4096, v * 4096) for u, v in (tp(*p) for p in r)], fill=255)
        m.filter(ImageFilter.GaussianBlur(6)).save(os.path.join(jd, 'mask.png'))
        frings, fctr, fname = [], [0, 0], ''
        if FK:
            frings = [[tp(*p) for p in r] for r in D[FK]['r'] if len(r) > 8]; fq = [q for r in frings for q in r]
            fctr = [sum(q[0] for q in fq) / len(fq), sum(q[1] for q in fq) / len(fq)]; fname = D[FK]['ten'].upper()
            m2 = Image.new('L', (4096, 4096), 0); dr2 = ImageDraw.Draw(m2)
            for r in D[FK]['r']: dr2.polygon([(u * 4096, v * 4096) for u, v in (tp(*p) for p in r)], fill=255)
            m2.filter(ImageFilter.GaussianBlur(4)).save(os.path.join(jd, 'mask2.png'))
        rings = [[tp(*p) for p in r] for r in R if len(r) > 8]
        rts = [{'pts': [tp(*p) for p in ln], 'td': t - a, 'lab': lb} for lb, ln, t in RT]
        ars = [{'p': tp(*p), 'lab': lb} for lb, p in AR]
        bds = []   # ranh giới tỉnh mảnh (bối cảnh), chỉ phần nằm trong mặt bản đồ
        for k in BK:
            for r in D[k]['r']:
                cur = []
                for q in [tp(*p) for p in r] + [tp(*r[0])]:
                    if .01 < q[0] < .99 and .01 < q[1] < .99: cur.append(q)
                    elif len(cur) > 1: bds.append(cur); cur = []
                    else: cur = []
                if len(cur) > 1: bds.append(cur)
        pns = [{'p': tp(*p), 'td': t - a, 'lab': lb} for lb, p, t in PN]
        uv = [q for r in rings for q in r] or ([q for r_ in rts for q in r_['pts']] + [q['p'] for q in pns]) or [tp(*p) for p in P]
        u0 = sum(q[0] for q in uv) / len(uv); v0 = sum(q[1] for q in uv) / len(uv)
        C = np.cov(np.array([[q[0] - u0, q[1] - v0] for q in uv]).T); w_, V_ = np.linalg.eigh(C); ax_ = V_[:, -1]
        yaw = math.atan2(ax_[0], ax_[1]); yaw = yaw if math.cos(yaw) >= 0 else yaw + math.pi   # nhìn dọc chiều dài vùng, camera phía nam
        emin = float(max(0, np.percentile(E1, 1)))
        json.dump({'G': 256, 'size': size, 'elev': E1.round(1).flatten().tolist(), 'G2': 256, 'size2': size * 4, 'elev2': E2.round(1).flatten().tolist(),
                   'rings': rings, 'routes': rts, 'pins': pns, 'areas': ars, 'borders': bds, 'dur': dur, 'ctr': [u0, v0], 'name': name, 'kicker': kick, 'sub': sub or '', 'emin': emin, 'yaw': yaw, 'td': td, 'frings': frings, 'fctr': fctr, 'fname': fname, 'fsub': FSUB or '', 'tf': (TF - a) if FK else 0, 'rise': [x - a for x in RISE] if (FK and RISE) else None}, open(os.path.join(jd, 'data.json'), 'w'))
        open(os.path.join(jd, 'index.html'), 'w', encoding='utf-8').write(_pal(S3D_HTML)); open(os.path.join(T_DIR, 's3d.mjs'), 'w').write(S3D_MJS)
        nm = os.path.join(jd, 'node_modules'); os.path.exists(nm) or os.symlink(_three(), nm)
        fp = os.path.join(T_DIR, 'LPVDisplay-Black.ttf')
        if not os.path.exists(fp): lpv_css()
        if os.path.exists(fp): shutil.copy(fp, os.path.join(jd, 'LPV.ttf'))
        r_ = subprocess.run(['node', os.path.join(T_DIR, 's3d.mjs'), jd, str(N)], capture_output=True, text=True)
        if not os.path.exists(os.path.join(jd, 'done')): sys.exit('✖ dựng bản đồ 3D lỗi: ' + (r_.stderr or r_.stdout)[-600:])
    rel = os.path.relpath(jd, os.path.join(root, 'build')) if DA_ else jd
    html = (f'<div class="vc" data-mg="ranh3d" id="{i}" style="left:0;top:0;width:720px;height:1280px;z-index:7;overflow:hidden;background:#0b1016">'
            f'<img class="s3" data-seq="{rel}/%04d.jpg" data-f="0" src="{rel}/0000.jpg" style="position:absolute;left:0;top:0;width:720px;height:1280px"/>'
            f'<svg viewBox="0 0 720 1280" width="720" height="1280" style="position:absolute;left:0;top:0"><text x="40" y="985" font-family="VCB6,sans-serif" font-weight="600" font-size="14" fill="rgba(255,255,255,.55)">'
            + (f'Google · AWS Terrain' + (' · Bộ NN&amp;MT' if ks else '') + ' · OSM' if RT else f'Ảnh vệ tinh: Google · Độ cao: AWS Terrain' + (' · Ranh giới 2025: Bộ NN&amp;MT' if ks else '')) + '</text></svg></div>')
    js = [f"tl.set('#{i}',{{autoAlpha:0}},0);", f"tl.set('#{i}',{{autoAlpha:1}},{a});",
          f"(function(){{var o={{f:0}},el=document.querySelector('#{i} .s3');tl.fromTo(o,{{f:0}},{{f:{N - 1},duration:{(N - 1) / 30:.3f},ease:'none',onUpdate:function(){{el.dataset.f=Math.round(o.f)}}}},{a});}})();",
          f"tl.set('#{i}',{{autoAlpha:0}},{b});"]
    if DA_:
        import cine; os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_ranh(os.path.join(DA_, 'sfx', 'ranh.wav'), 1.0)
        if ks: cine.sfx(t_draw - .05, 'ranh')
        if FK: cine.sfx(TF - .05, 'ranh')
        for _, _, t in RT: cine.sfx(t - .05, 'ranh')
    return html, js, [(a, 'whoosh')] + [(t, 'pop') for _, _, t in PN]

# ---------- STORYBOARD trước khi dựng (anh yêu cầu 26/11/2026, giống realcut) ----------
#   vc.py sb DA              → DA/storyboard.xlsx (mỗi cảnh 1 dòng + ảnh) + DA/storyboard.jpg (xem nhanh) — đọc scenes.py + subs.py, KHÔNG dựng
#   vc.py sb DA --read FILE  → so bản anh sửa với bản gốc, in ô đã đổi + cột ANH SỬA → sửa scenes.py/subs.py rồi mới build
SB_COLS = ['CẢNH', 'GIÂY', 'LỜI ANH NÓI', 'LOẠI CẢNH', 'NỘI DUNG HÌNH', 'CHỮ NHẤN (PHỤ ĐỀ)', 'HIỆU ỨNG / ÂM', 'ẢNH', 'ANH SỬA']
SB_KIND = {'mat': 'MẶT', 'vanban': 'VĂN BẢN', 'ds': 'THÔNG TIN', 'so': 'CON SỐ', 'sat': 'BẢN ĐỒ', 'cta': 'KÊU GỌI', 'hinh': 'ĐỒ HOẠ', 'full': 'ĐỒ HOẠ', 'person': 'MẶT', 'tu': 'MẶT'}
def _sb_txt(v):
    if isinstance(v, str): return v
    if isinstance(v, (int, float)): return f'{v:g}'
    if isinstance(v, (list, tuple)): return ', '.join(_sb_txt(x) for x in v if not isinstance(x, (int, float)) or isinstance(x, bool)) or ''
    return ''
def _sb_desc(n, ar, kw):
    g = lambda k, d='': kw.get(k, d)
    if n == 'mat': return 'Mặt người nói' + (f" · nhấn zoom ở {g('nhan'):g}s" if g('nhan', None) is not None else '') + (' · đẩy cận' if g('push') else '')
    if n == 'vanban': return f"Văn bản giấy: {_sb_txt(ar[2:3])} · {_sb_txt(ar[3:4])}" + (f" · dấu {g('stamp')}" if g('stamp') else '')
    if n == 'ds': return f"Bảng '{g('title', 'CẦN BIẾT')}': " + '; '.join(str(x[0]) if isinstance(x, (list, tuple)) else str(x) for x in (ar[2] if len(ar) > 2 else [])) + (f" · kết: {g('ket')}" if g('ket') else '')
    if n == 'so': return f"Số lớn {_sb_txt(ar[2:3])}{(' ' + g('unit')) if g('unit') else ''} · {_sb_txt(ar[3:4])}" + ''.join(f" · {k}: {g(k)}" for k in ('title', 'delta', 'note') if g(k))
    if n == 'sat':
        nm = ar[2] if len(ar) > 2 else kw.get('names', ''); nm = ' + '.join(nm) if isinstance(nm, (list, tuple)) else nm
        return (f"Bản đồ vệ tinh {'3D ' if g('d3') else ''}{nm or ''}" + (f" · tên hiện: {g('label')}" if g('label') else '') + (f" · dòng phụ: {g('sub')}" if g('sub') else '')
                + ''.join(f" · tuyến {r[0]}" for r in g('routes', ())) + ''.join(f" · ghim {p[0]}" for p in g('pins', ())))
    if n == 'cta': return 'Kêu gọi cuối: ' + ('bình luận + ' if g('hoi', None) is not None else '') + 'FOLLOW VŨ' + (' · chủ đề: ' + ', '.join(c[0] for c in g('chu', ())) if g('chu') else '')
    if n == 'R':
        mk = ar[0]; s = ', '.join(f'{k}={_sb_txt(v)}' for k, v in mk.kw.items() if _sb_txt(v) and k not in ('t0', 't1'))
        pos = ', '.join(_sb_txt(x) for x in mk.ar[3:] if isinstance(x, str))
        return f"Đồ hoạ {mk.n}" + (f": {pos}" if pos else '') + (f" · {s}" if s else '')
    return n
def _sb_rows(DA):
    import types
    rec = []
    class Mk:
        def __init__(s, n, ar, kw): s.n, s.ar, s.kw = n, ar, kw
    class JL(list):
        def append(s, x): rec.append(('V', 'J', (x,), {}))
    class Rec:
        def __init__(s, ns): s._ns = ns
        def __getattr__(s, n):
            if n == 'J': return JL()
            def f(*ar, **kw):
                if s._ns == 'R': return Mk(n, ar, kw)
                rec.append((s._ns, n, ar, kw))
            return f
    ns = {'V': Rec('V'), 'P': Rec('P'), 'C': Rec('C'), 'R': Rec('R'), 'N': Rec('R'), 'B': Rec('R'), 'X': Rec('R'), 'DL': Rec('R'), 'mg_v4': Rec('R'), 'MJ': Rec('R')}
    exec(open(os.path.join(DA, 'scenes.py'), encoding='utf-8').read(), ns)
    global WD, K, SUBS
    WD, K = _load(DA), 0; SUBS.clear(); PEND.clear()
    exec(open(os.path.join(DA, 'subs.py'), encoding='utf-8').read(), {'P': sys.modules[__name__]})
    T = float(json.load(open(os.path.join(DA, 'state.json')))['T'])
    sc, ev, hook = [], [], []
    for nsn, n, ar, kw in rec:
        num = len(ar) >= 2 and all(isinstance(x, (int, float)) for x in ar[:2])
        if nsn == 'P' and n in SB_KIND and num: sc.append((ar[0], ar[1], SB_KIND[n], _sb_desc(n, ar, kw)))
        elif nsn == 'V' and n == 'full' and ar and isinstance(ar[0], Mk) and len(ar[0].ar) >= 3: sc.append((ar[0].ar[1], ar[0].ar[2], 'ĐỒ HOẠ', _sb_desc('R', ar, kw)))
        elif nsn == 'V' and n == 'L_person' and num: sc.append((ar[0], ar[1], 'MẶT', 'Mặt người nói'))
        elif nsn == 'P' and n == 'hook': hook.append(f"HOOK: {ar[0] if ar else ''}")
        elif nsn == 'V' and n == 'TR' and len(ar) > 1: ev.append((ar[1], f'chuyển {ar[0]}'))
        elif nsn == 'C' and ar and isinstance(ar[0], (int, float)): ev.append((ar[0], {'dip': 'tối chuyển chương', 'leak': 'loé sáng câu đắt', 'focus': 'lấy nét về mặt', 'lens': 'ống kính vào bản đồ', 'letterbox': 'viền điện ảnh (cao trào)'}.get(n, n)))
        elif nsn == 'V' and n == 'J':
            for m in re.finditer(r'VC\.(punch|push|reset)\(([\d.]+)', str(ar[0])): ev.append((float(m[2]), {'punch': 'zoom nhấn', 'push': 'đẩy cận', 'reset': 'về khung'}[m[1]]))
        elif nsn == 'V' and n == 'audio':
            for t in kw.get('impacts', []) or []: ev.append((t, 'tiếng nhấn'))
            for t in kw.get('duck', []) or []: ev.append((t, 'nhạc lặng trước câu đắt'))
        elif nsn == 'P' and n == 'nhac': hook.append(f"NHẠC: {ar[0] if ar else 'tin'}")
        elif nsn == 'P' and n == 'nen': hook.append(f"NỀN: {ar[0] if ar else 'do'}")
    sc.sort(key=lambda x: x[0]); full = []; t = 0.0
    for a, b, k, d in sc:
        if a - t > .3: full.append((t, a, 'MẶT', 'Mặt người nói (giữa các cảnh)'))
        full.append((a, b, k, d)); t = max(t, b)
    if T - t > .3: full.append((t, T, 'MẶT', 'Mặt người nói (giữa các cảnh)'))
    kws = [(p[2], f"[{({'s': 'ĐỎ', 'l': 'XANH', 'g': 'VÀNG', 'x': 'VÀNG'}).get(p[0][:1], p[0].upper())}{' TO' if 'xl' in p[0] else ''}] {p[1]}") for parts, _ in SUBS for p in parts if p != 'br' and p[0] != 'w']
    rows = []
    for n, (a, b, k, d) in enumerate(full):
        loi = ' '.join(w['word'] for w in WD if a - .01 <= w['start'] < b - .01)
        ch = '\n'.join(x for tt, x in kws if a - .01 <= tt < b - .01)
        hi = '\n'.join(f'{tt:.1f}s {x}' for tt, x in sorted(ev) if a - .01 <= tt < b - .01)
        if n == 0 and hook: ch = '\n'.join(hook) + ('\n' + ch if ch else '')
        rows.append([str(n + 1), f'{a:.1f} – {b:.1f}', loi, k, d, ch, hi, '', ''])
    return rows, full
def _sb_font(sz, bold=False):
    from PIL import ImageFont
    for f in ([os.path.join(T_DIR, 'LPVDisplay-Black.ttf')] if bold else []) + ['/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']:
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()
def _sb_thumb(DA, a, b, k, d, n):
    from PIL import Image, ImageDraw
    W, H = 270, 480; f = os.path.join(DA, 'qc', f'sb_{n}.jpg'); os.makedirs(os.path.dirname(f), exist_ok=True)
    if k == 'MẶT':
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(a + b) / 2:.2f}', '-i', os.path.join(DA, 'cut', 'cut.mp4'), '-frames:v', '1', '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', f])
        if os.path.exists(f): return f
    im = Image.new('RGB', (W, H), (22, 6, 8)); dr = ImageDraw.Draw(im)
    for y in range(H): dr.line([(0, y), (W, y)], fill=(int(22 + 60 * y / H), 6, 10))
    col = {'BẢN ĐỒ': (61, 242, 166), 'CON SỐ': (255, 210, 63), 'THÔNG TIN': (255, 210, 63), 'KÊU GỌI': (255, 210, 63)}.get(k, (255, 255, 255))
    dr.text((18, 28), k, font=_sb_font(34, True), fill=col)
    y = 90; words = d.split(); line = ''; fb = _sb_font(17)
    for w in words:
        if dr.textlength(line + ' ' + w, font=fb) > W - 36: dr.text((18, y), line.strip(), font=fb, fill=(235, 235, 235)); y += 24; line = ''
        line += ' ' + w
        if y > H - 60: break
    dr.text((18, y), line.strip(), font=fb, fill=(235, 235, 235)); im.save(f, quality=88); return f
def sb(DA, *a):
    DA = os.path.abspath(os.path.expanduser(DA))
    if '--read' in a: return _sb_read(DA, a[a.index('--read') + 1])
    import openpyxl; from openpyxl.drawing.image import Image as XImg; from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from PIL import Image, ImageDraw
    rows, full = _sb_rows(DA); th = [_sb_thumb(DA, *x, n) for n, x in enumerate(full)]
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Storyboard'; ws.append(SB_COLS)
    for j, w in enumerate([7, 12, 42, 12, 42, 26, 24, 20, 32]): ws.column_dimensions[chr(65 + j)].width = w
    hd = PatternFill('solid', fgColor='7A0C12'); bd = Side(style='thin', color='BBBBBB')
    for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = hd; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.freeze_panes = 'C2'
    for n, r in enumerate(rows):
        ws.append(r); R_ = n + 2; ws.row_dimensions[R_].height = 185
        for c in ws[R_]: c.alignment = Alignment(vertical='top', wrap_text=True); c.border = Border(top=bd, bottom=bd, left=bd, right=bd)
        ws.cell(R_, 9).fill = PatternFill('solid', fgColor='FFF6D6')
        if th[n]:
            tp = th[n].replace('.jpg', '_x.png'); Image.open(th[n]).resize((135, 240)).save(tp); im = XImg(tp); ws.add_image(im, f'H{R_}')
    ws.append([]); ws.append(['', '', 'Ghi chú: sửa thẳng ô (lời, hình, chữ nhấn, hiệu ứng) hoặc ghi yêu cầu ở cột ANH SỬA. Thêm cảnh: chèn dòng mới, ghi giây + nội dung. Gửi lại file cho em.'])
    xp = os.path.join(DA, 'storyboard.xlsx'); wb.save(xp)
    json.dump({'rows': rows}, open(os.path.join(DA, 'storyboard.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    cw, chh, nc = 270, 560, 6; nr = (len(rows) + nc - 1) // nc; sh_ = Image.new('RGB', (cw * nc, chh * nr), (12, 12, 12)); dr = ImageDraw.Draw(sh_)
    for n, r in enumerate(rows):
        x, y = (n % nc) * cw, (n // nc) * chh
        if th[n]: sh_.paste(Image.open(th[n]).resize((cw - 6, 474)), (x + 3, y + 3))
        dr.text((x + 8, y + 482), f'{r[0]} · {r[1]}s · {r[3]}', font=_sb_font(18), fill=(255, 210, 63))
        dr.text((x + 8, y + 508), (r[2][:34] + '…') if len(r[2]) > 34 else r[2], font=_sb_font(14), fill=(220, 220, 220))
    sh_.save(os.path.join(DA, 'storyboard.jpg'), quality=86)
    print(f'✅ {xp} ({len(rows)} cảnh) + storyboard.jpg → gửi anh sửa; anh gửi lại → vc.py sb DA --read <file>')
def _sb_read(DA, path):
    import openpyxl
    snap = json.load(open(os.path.join(DA, 'storyboard.json'), encoding='utf-8'))['rows']
    ws = openpyxl.load_workbook(path).active; n = 0; seen = set()
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        r = ['' if v is None else str(v) for v in r] + [''] * len(SB_COLS)
        if not any(x.strip() for x in r) or r[2].startswith('Ghi chú: sửa thẳng'): continue
        o = next((s for s in snap if s[0] == r[0].strip()), None)
        if o is None: print(f'+ CẢNH MỚI (dòng {i + 2}): ' + ' | '.join(f'{SB_COLS[j]}: {r[j]}' for j in range(len(SB_COLS)) if r[j].strip() and SB_COLS[j] != 'ẢNH')); n += 1; continue
        seen.add(o[0])
        for j, col in enumerate(SB_COLS):
            if col == 'ẢNH': continue
            if r[j].strip() != o[j].strip(): print(f'Cảnh {o[0]} ({o[1]}s) · {col}:\n    trước: {o[j] or "—"}\n    anh sửa: {r[j] or "(xoá)"}'); n += 1
    for s in snap:
        if s[0] not in seen: print(f'- ANH XOÁ cảnh {s[0]} ({s[1]}s): {s[4]}'); n += 1
    print(f'→ {n} chỗ anh sửa' if n else '→ anh không sửa gì → build')


# ---------- MÀU NHŨ cho tên địa danh + viền bản đồ + chữ kêu gọi cuối (anh 27/11: so vàng nhũ / sâm panh / vàng hồng) ----------
GOLD_BASE = dict(grad="linear-gradient(100deg,#7a5a24 0%,#c9a25a 14%,#f6e2a2 24%,#fff6d6 28%,#d9b468 38%,#8c6a2c 52%,#e8c983 64%,#fff1c2 70%,#b88f45 82%,#6e5020 100%)", sh="rgba(70,48,12,.95)", c0="c0=[.50,.35,.13],c1=[1,.93,.70]", glow="0xC9A25A", hot="0xFFF1C2", fcore="0xF6E2A2", f="const f=.5+.5*Math.sin(acc/(S*.025));",
                 k1="glow:mk(16,0xC9A25A,.35),core,hot:mk(8,0xFFF1C2,.85)", k2="const core=mk(5,0xffffff,1);",
                 k3="glow:mk(14,0xC9A25A,.35),core:mk(4.5,0xF6E2A2,1),hot:mk(7,0xFFF1C2,.85)", k4="o.glow.material.opacity=.28+.12*Math.sin(t*5)")
PAL = {
    'nhu': GOLD_BASE,
    'sampanh': dict(f=GOLD_BASE['f'], grad="linear-gradient(100deg,#7b6a4c 0%,#c9b58c 14%,#f1e6cb 24%,#fffbf2 28%,#ddcca6 38%,#8e7a57 52%,#e8d9b7 64%,#fff7e6 70%,#bca77d 82%,#6c5b3d 100%)",
                    sh="rgba(58,46,26,.95)", c0="c0=[.56,.48,.34],c1=[1,.97,.88]", glow="0xD8C8A0", hot="0xFFF8E6", fcore="0xF3EAD3"),
    'xuoc': dict(GOLD_BASE, c0="c0=[.50,.35,.13],c1=[.98,.85,.56]",   # chữ vàng nhũ + ranh giới VÀNG XƯỚC: dải kim loại mảnh, mép vàng sẫm, lõi sáng có vân xước mịn
                 f="const f=Math.min(1,Math.max(0,.55+.15*Math.sin(acc/(S*.02))+.3*Math.sin(acc/(S*.0009)+1.3)+.2*Math.sin(acc/(S*.00037)+.4)));",
                 k1="glow:(g=>(g.renderOrder=4,g))(mk(7.5,0x5E431A,.95)),core,hot:mk(3.5,0xFFE6B0,.9)", k2="const core=mk(3.4,0xffffff,1);",
                 k3="glow:(g=>(g.renderOrder=4,g))(mk(7,0x5E431A,.95)),core:mk(3.2,0xE2C27E,1),hot:mk(3.5,0xFFE6B0,.9)", k4="o.glow.material.opacity=.95"),
    'hong': dict(f=GOLD_BASE['f'], grad="linear-gradient(100deg,#7a4034 0%,#c47f6c 14%,#f6cfc2 24%,#fff3ee 28%,#dda08c 38%,#8f4f40 52%,#eab4a2 64%,#ffe6dc 70%,#b8725f 82%,#683629 100%)", sh="rgba(78,34,26,.95)", c0="c0=[.55,.30,.24],c1=[1,.88,.82]", glow="0xC98A78", hot="0xFFE8E0", fcore="0xF3C9BC"),
}
MAU = {'k': 'xuoc'}   # anh chốt 27/11: chữ vàng nhũ + ranh giới VÀNG XƯỚC
def _pal(txt):
    if MAU['k'] == 'nhu': return txt
    b, q = GOLD_BASE, PAL[MAU['k']]
    for k in b: txt = txt.replace(b[k], q.get(k, b[k]))
    return txt
def mau(k='nhu'):   # P.mau('nhu'|'sampanh'|'hong') đầu scenes.py — màu nhũ tên địa danh, viền bản đồ, chữ kêu gọi cuối
    global FOIL
    MAU['k'] = k; FOIL = _pal(FOIL0)
# ---------- bộ phong cách (tự xoay theo video) + cảnh mẫu 1 dòng ----------
PACKS = [
    dict(ten='vang-tram', tr=['wipe', 'zoom', 'flash'], bg=['inkpanel', 'darkpanel', 'goldglow', 'diahinh', 'betong'], punch=1.15, accent='leak', ds=['phaply', 'stairs', 'hoso']),
    dict(ten='xanh-ha-tang', tr=['zoom', 'whip', 'wipe'], bg=['diahinh', 'greenglow', 'darkpanel', 'diagpanel', 'inkpanel'], punch=1.12, accent='lens', ds=['stairs', 'hoso', 'phaply']),
    dict(ten='do-tin-nong', tr=['flash', 'wipe', 'glitch'], bg=['redglow', 'darkpanel', 'betong', 'inkpanel', 'diagpanel'], punch=1.18, accent='dip', ds=['hoso', 'phaply', 'stairs']),
    dict(ten='giay-sang', tr=['wipe', 'flash', 'zoom'], bg=['darkpanel', 'goldglow', 'inkpanel', 'diahinh', 'redglow'], punch=1.14, accent='focus', ds=['phaply', 'hoso', 'stairs']),
]
ST = {'pack': None, 'k': 0, 'bg': 0, 'tr': -9, 'n': 0, 'ds': 0}
def _pack():
    if ST['pack'] is None:
        import hashlib; h = int(hashlib.md5(os.path.basename(DA_ or 'x').encode()).hexdigest(), 16); ST['pack'] = PACKS[h % len(PACKS)]
        print(f"  · phong cách video này: {ST['pack']['ten']}")
    return ST['pack']
def _id(p): ST['n'] += 1; return f'{p}{ST["n"]}'
def _bg(a, b, kind=None):
    pk = _pack(); kind = kind or pk['bg'][ST['bg'] % len(pk['bg'])]; ST['bg'] += 1; V.panel(_id('bg'), kind, a, b, seed=ST['n']); return kind
def _tr(a):   # chuyển cảnh trang trí ≤ 1/8 s, xoay loại
    pk = _pack()
    if a - ST['tr'] >= 8: V.TR(pk['tr'][ST['k'] % len(pk['tr'])], a); ST['k'] += 1; ST['tr'] = a
def mat(a, b, nhan=None, push=False):   # cảnh mặt: tự reset zoom, nhấn ở giây `nhan`, push chậm nếu câu kể
    V.L_person(a, b); s = f"VC.reset({a});"
    if push: s += f"VC.push({a + .1:.2f},1.07,{min(4, b - a - .2):.2f});"
    if nhan is not None: s += f"VC.punch({nhan},{_pack()['punch']});"
    V.J.append(s)
NEN = {   # nền cảnh đồ hoạ (P.nen) — tối giản, sang; chữ trắng/vàng của bộ R. vẫn nổi
    'do':   'url(\'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%22.85%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3CfeColorMatrix values=%220 0 0 0 .95 0 0 0 0 .12 0 0 0 0 .14 0 0 0 9 -4.6%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23n)%22 opacity=%22.35%22/%3E%3C/svg%3E\') 0 0/300px 300px,radial-gradient(70% 18% at 50% 104%,rgba(160,14,22,.4),rgba(160,14,22,0) 70%),radial-gradient(70% 50% at 100% 60%,#8a0c12 0%,#4a060a 40%,rgba(10,2,3,0) 80%),linear-gradient(160deg,#070203 0%,#110304 60%,#170305 100%)',   # ĐỎ TRẦM hạt nhiễu — MẶC ĐỊNH (anh duyệt 23/11/2026)
    'do_ruc': 'url(\'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%22.85%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3CfeColorMatrix values=%220 0 0 0 .95 0 0 0 0 .12 0 0 0 0 .14 0 0 0 9 -4.6%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23n)%22 opacity=%22.55%22/%3E%3C/svg%3E\') 0 0/300px 300px,radial-gradient(70% 22% at 50% 104%,rgba(200,20,28,.55),rgba(200,20,28,0) 70%),radial-gradient(85% 60% at 92% 52%,#d0161d 0%,#8e0c12 30%,#3a0508 62%,rgba(10,2,3,0) 88%),linear-gradient(160deg,#060102 0%,#120204 45%,#1c0306 100%)',   # đỏ rực sát ảnh mẫu Black Friday
    'den':  '#0d0d0f',
    'than': 'radial-gradient(120% 75% at 28% 16%,#27221c 0%,#16130f 46%,#0a0907 100%)',
    'dem':  'radial-gradient(120% 75% at 28% 16%,#1a2633 0%,#0f1720 48%,#070a0e 100%)',
    'da':   'radial-gradient(85% 45% at 50% -4%,rgba(232,194,122,.13),rgba(232,194,122,0) 70%),radial-gradient(140% 90% at 50% 40%,#1c1c1f 0%,#121214 55%,#08080a 100%)',
}
def nen(ten='do'):   # P.nen('do'|'do_ruc'|'than'|'dem'|'da'|'den') đầu scenes.py — đổi nền mọi hình R.
    R().BG = NEN.get(ten, ten)
CTA_TEN, CTA_CHUC = 'Lê Phong Vũ', 'GĐDA · Tây Nguyên Investment'
FOIL = ("background:linear-gradient(100deg,#7a5a24 0%,#c9a25a 14%,#f6e2a2 24%,#fff6d6 28%,#d9b468 38%,#8c6a2c 52%,#e8c983 64%,#fff1c2 70%,#b88f45 82%,#6e5020 100%);"
        "background-size:240% 100%;background-position:100% 0;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;"
        "padding:.22em .04em .26em;margin:-.22em -.04em -.26em;filter:drop-shadow(0 1.5px 0 rgba(70,48,12,.95)) drop-shadow(0 10px 22px rgba(0,0,0,.55))")   # đệm để dấu tiếng Việt (Ị, Ũ, Ỗ) không bị cắt
FOIL0 = FOIL
FOIL = _pal(FOIL0)
def _foil_js(sel, t, d=1.6): return f"tl.fromTo('{sel}',{{backgroundPosition:'100% 0'}},{{backgroundPosition:'0% 0',duration:{d},ease:'power2.inOut'}},{t:.2f});"
def cta(a, b, follow, hoi=None, chu=(), ten=CTA_TEN, chuc=CTA_CHUC, nut='Follow', xong='Đã follow', hoi_txt=('ANH CHỊ', 'CÓ CÂU HỎI?')):
    """MẪU KÊU GỌI CUỐI VIDEO — cảnh đồ hoạ nền mặc định + khung nhân vật nhỏ, chữ NHŨ VÀNG:
    hoi=giây câu hỏi/bình luận → chữ nhũ "ANH CHỊ / CÓ CÂU HỎI?" + bong bóng bình luận 3D đang gõ + "BÌNH LUẬN BÊN DƯỚI ↓" (hoi_txt chỉ chữ có trong lời)
    follow=giây chữ "Follow" → chữ nhũ "FOLLOW VŨ" + thẻ kính (chữ ký V · tên · chức danh · nút Follow tự bấm → Đã follow)
    chu=[(CHỮ, giây)] ≤3 chủ đề nói ở câu follow → từng dòng tick vàng"""
    i = _id('cta'); R_ = R(); J = []; t1 = follow
    gl = 'background:rgba(255,248,235,.05);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:inset 0 0 0 1px rgba(232,194,122,.28),0 18px 40px rgba(0,0,0,.45)'
    H = [f'<div class="vc" id="{i}bg" style="left:0;top:0;width:720px;height:1280px;z-index:7;opacity:0;background:{R_.BG}"></div>',
         f'<div class="vc" id="{i}" style="left:0;top:0;width:720px;height:1280px;z-index:8;opacity:0">']
    if hoi is not None:
        H.append(f'<div class="pa" style="position:absolute;left:60px;top:150px;width:600px">'
                 f'<div class="k" style="display:flex;align-items:center;gap:12px;font-family:VCB,sans-serif;font-weight:800;font-size:19px;letter-spacing:4px;color:#E8C27A">'
                 f'<span style="width:28px;height:3px;background:#E8C27A;display:inline-block"></span>BÌNH LUẬN</div>'
                 + ''.join(f'<div class="h{k}" style="font-family:VCS,serif;font-weight:700;font-size:{(min(82, int(560 / (len(x) * .6))) if len(x) > 9 else 82) if k else 64}px;white-space:nowrap;line-height:1.08;letter-spacing:.01em;margin-top:{14 if not k else 0}px;{FOIL}">{x}</div>' for k, x in enumerate(hoi_txt))
                 + '</div>'
                 f'<div class="bu" style="position:absolute;left:70px;top:430px;width:300px;height:170px;transform:scale(1.25);transform-origin:0 0">'
                 f'<svg width="300" height="170" viewBox="0 0 300 170"><defs><linearGradient id="{i}b1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a332a"/><stop offset="1" stop-color="#1c1814"/></linearGradient>'
                 f'<linearGradient id="{i}b2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6e2a2"/><stop offset=".5" stop-color="#c9a25a"/><stop offset="1" stop-color="#7a5a24"/></linearGradient></defs>'
                 f'<path d="M30 14 H270 a22 22 0 0 1 22 22 V104 a22 22 0 0 1 -22 22 H96 L58 156 L64 126 H30 a22 22 0 0 1 -22 -22 V36 a22 22 0 0 1 22 -22Z" fill="url(#{i}b1)" stroke="url(#{i}b2)" stroke-width="2.5"/>'
                 f'<path d="M34 22 H262" stroke="#fff" stroke-opacity=".18" stroke-width="3" stroke-linecap="round"/>'
                 + ''.join(f'<circle class="d{k}" cx="{110 + k * 40}" cy="70" r="11" fill="url(#{i}b2)"/>' for k in range(3)) + '</svg></div>'
                 f'<div class="ar" style="position:absolute;left:470px;top:480px;font-family:VCB,sans-serif;font-weight:800;font-size:21px;letter-spacing:2.5px;color:rgba(246,241,231,.8);line-height:1.5">BÌNH LUẬN<br>BÊN DƯỚI <span class="aw" style="display:inline-block;color:#E8C27A">↓</span></div>')
        J += [_foil_js(f'#{i} .h0', hoi - .4), _foil_js(f'#{i} .h1', hoi - .25),
              f"tl.set('#{i} .k',{{opacity:0,x:-14}},0);tl.to('#{i} .k',{{opacity:1,x:0,duration:.5,ease:'expo.out'}},{a + .05:.2f});",
              f"tl.set('#{i} .h0,#{i} .h1',{{opacity:0,y:24}},0);tl.to('#{i} .h0',{{opacity:1,y:0,duration:.7,ease:'expo.out'}},{a + .12:.2f});tl.to('#{i} .h1',{{opacity:1,y:0,duration:.7,ease:'expo.out'}},{a + .22:.2f});",
              f"tl.set('#{i} .bu',{{opacity:0,scale:.7,transformOrigin:'20% 100%'}},0);tl.to('#{i} .bu',{{opacity:1,scale:1,duration:.6,ease:'back.out(2)'}},{hoi - .1:.2f});",
              f"tl.set('#{i} .ar',{{opacity:0,y:10}},0);tl.to('#{i} .ar',{{opacity:1,y:0,duration:.5}},{hoi + .2:.2f});tl.to('#{i} .aw',{{y:8,duration:.35,yoyo:true,repeat:{int(max(1, (t1 - hoi) / .35))},ease:'sine.inOut'}},{hoi + .4:.2f});"]
        J += [f"tl.to('#{i} .d{k}',{{y:-10,duration:.22,yoyo:true,repeat:{int(max(1, (t1 - hoi) / .22))},ease:'sine.inOut'}},{hoi + .2 + k * .12:.2f});" for k in range(3)]
        J.append(f"tl.to('#{i} .pa,#{i} .bu,#{i} .ar',{{opacity:0,y:-30,duration:.35,ease:'power2.in'}},{t1 - .35:.2f});")
    btn = (f'<div class="bt" style="position:relative;margin-left:auto;height:48px;min-width:138px;border-radius:999px;overflow:hidden;font-family:VCB,sans-serif;font-weight:800;font-size:19px">'
           f'<div class="b1" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,#F6E2A2,#D2A85A 55%,#B38A42);color:#1a140a;box-shadow:inset 0 1px 0 rgba(255,255,255,.6)">{nut}</div>'
           f'<div class="b2" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:6px;box-shadow:inset 0 0 0 1px rgba(232,194,122,.6);color:#F1D08E;opacity:0">'
           f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E8C27A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>{xong}</div>'
           f'<div class="rp" style="position:absolute;left:50%;top:50%;width:20px;height:20px;margin:-10px;border-radius:50%;background:rgba(255,255,255,.6);opacity:0"></div></div>')
    H.append(f'<div class="pb" style="position:absolute;left:60px;top:150px;width:600px">'
             f'<div class="k2" style="display:flex;align-items:center;gap:12px;font-family:VCB,sans-serif;font-weight:800;font-size:19px;letter-spacing:4px;color:#E8C27A">'
             f'<span style="width:28px;height:3px;background:#E8C27A;display:inline-block"></span>ĐỪNG BỎ LỠ</div>'
             f'<div class="f1" style="font-family:VCS,serif;font-weight:700;font-size:90px;line-height:1.02;letter-spacing:.01em;margin-top:10px;white-space:nowrap;{FOIL}">FOLLOW VŨ</div>'
             f'<div class="cd" style="display:flex;align-items:center;gap:16px;margin-top:22px;padding:16px 16px 16px 18px;border-radius:20px;{gl}">'
             f'<div style="width:56px;height:56px;flex:none;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1.5px #E8C27A,0 0 0 4px rgba(232,194,122,.08)">'
             f'<span style="font-family:VCS,serif;font-style:italic;font-weight:700;font-size:32px;{FOIL}">V</span></div>'
             f'<div style="line-height:1.15"><div style="font-family:VCB,sans-serif;font-weight:800;font-size:25px;color:#F6F1E7">{ten}</div>'
             f'<div style="font-family:VSUB,sans-serif;font-weight:500;font-size:16px;letter-spacing:.4px;color:rgba(246,241,231,.6);margin-top:4px">{chuc}</div></div>{btn}</div>'
             f'<div style="margin-top:22px;width:360px">'
             + ''.join(f'<div class="c{k}" style="display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid rgba(232,194,122,.22);font-family:VCB,sans-serif;font-weight:800;font-size:24px;letter-spacing:2.5px;color:#F6F1E7">'
                       f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E8C27A" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" stroke-opacity=".5"/><path d="M7.5 12.5l3 3 6-6.5"/></svg>{c}</div>' for k, (c, _) in enumerate(chu[:3]))
             + '</div></div></div>')
    tap = t1 + .75
    J += [f"tl.set('#{i}bg,#{i}',{{opacity:1}},{a:.2f});tl.set('#{i}bg,#{i}',{{opacity:0}},{b:.2f});",
          f"tl.set('#{i} .pb',{{opacity:0}},0);tl.set('#{i} .pb',{{opacity:1}},{t1 - .05:.2f});",
          f"tl.set('#{i} .k2',{{opacity:0,x:-14}},0);tl.to('#{i} .k2',{{opacity:1,x:0,duration:.5,ease:'expo.out'}},{t1:.2f});",
          f"tl.set('#{i} .f1',{{opacity:0,y:26,letterSpacing:'.05em'}},0);tl.to('#{i} .f1',{{opacity:1,y:0,letterSpacing:'.01em',duration:.9,ease:'expo.out'}},{t1 + .05:.2f});",
          _foil_js(f'#{i} .f1', t1 + .1, 1.8),
          f"tl.set('#{i} .cd',{{opacity:0,y:18}},0);tl.to('#{i} .cd',{{opacity:1,y:0,duration:.6,ease:'expo.out'}},{t1 + .3:.2f});",
          f"tl.to('#{i} .bt',{{scale:.9,duration:.1,ease:'power2.in'}},{tap:.2f});tl.to('#{i} .bt',{{scale:1,duration:.35,ease:'back.out(2.4)'}},{tap + .1:.2f});",
          f"tl.fromTo('#{i} .rp',{{opacity:.6,scale:0}},{{opacity:0,scale:9,duration:.55,ease:'power2.out'}},{tap + .05:.2f});",
          f"tl.to('#{i} .b1',{{opacity:0,duration:.2}},{tap + .12:.2f});tl.to('#{i} .b2',{{opacity:1,duration:.25}},{tap + .12:.2f});"]
    for k, (c, t) in enumerate(chu[:3]):
        J.append(f"tl.set('#{i} .c{k}',{{opacity:0,x:-16}},0);tl.to('#{i} .c{k}',{{opacity:1,x:0,duration:.45,ease:'expo.out'}},{t:.2f});")
    cues = [(t1, 'whoosh'), (tap, 'pop')] + [(t, 'tick') for _, t in chu[:3]] + ([(hoi - .1, 'pop')] if hoi is not None else [])
    V.full((''.join(H), J, cues)); V.L_full(a, b, 'CTA'); _tr(a)
    import cine; cine.sfx(t1 + .1, 'shimmer')
def vanban(a, b, title, meta='', t=None, stamp='BAN HÀNH', head='QUYẾT ĐỊNH', brand='UBND TỈNH ĐẮK LẮK'):   # văn bản / quyết định / dự thảo (bộ chân thực)
    t = a + .5 if t is None else t; V.full(R().vanban(_id('vb'), a, b, t, title, meta, stamp=stamp, head=head, brand=brand)); V.L_full(a, b, 'VB'); _tr(a)
def ds(a, b, items, title='CẦN BIẾT', ket='', t_ket=None):   # MÀN HÌNH THÔNG TIN: bảng kẹp hồ sơ, tick từng ý · items=[(chữ, t)] 3–6 · nhãn LƯU LẠI
    V.full(R().ds(_id('ds'), a, b, items, title=title, ket=ket, t_ket=t_ket)); V.L_full(a, b, 'DS'); _tr(a); luu(items[-1][1] + .3, b)
def luu(a, b):   # nhãn nhỏ LƯU LẠI góc trên
    i = _id('luu')
    V.H.append(f'<div class="vc" id="{i}" style="left:40px;top:128px;z-index:30;padding:6px 14px;border-radius:999px;background:rgba(217,181,107,.95);color:#141414;font-family:VCB,sans-serif;font-weight:900;font-size:18px;letter-spacing:2px;opacity:0">LƯU LẠI</div>')
    V.J.append(f"tl.set('#{i}',{{opacity:0}},0);tl.to('#{i}',{{opacity:1,duration:.3}},{a:.2f});tl.set('#{i}',{{opacity:0}},{b:.2f});")
def so(a, b, value, label='', t=None, unit='', title='', note='', delta=''):   # 1 con số lớn (chỉ số có trong lời)
    t = a + .3 if t is None else t; V.full(R().so(_id('so'), a, b, t, str(value), unit, kicker=label, title=title, note=note, delta=delta)); V.L_full(a, b, 'SO'); _tr(a)
    if DA_ and re.fullmatch(r'[\d.,]+', str(value).strip()):   # tiếng máy đếm số chạy theo nhịp số (expo.out 1.2 s) + tiếng chốt sáng khi dừng
        import cine; os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_count(os.path.join(DA_, 'sfx', 'countup.wav')); cine.sfx(t, 'countup')
def hinh(a, b, fn, *args, nen=None, **kw):   # bất kỳ hình nào: P.hinh(a, b, R.caotoc, t0, …) — hình bộ chân thực có nền riêng; tự chuyển cảnh + khung người nói
    if not getattr(fn, '__module__', '').startswith('mg_real'): _bg(a, b, nen)
    i = _id('h'); r = fn(i, a, b, *args, **kw)
    if isinstance(r, tuple) and len(r) == 3 and DA_ and any(c[1] == 'count' for c in r[2]):   # số đếm → tiếng máy đếm + chốt (như P.so)
        import cine; os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_count(os.path.join(DA_, 'sfx', 'countup.wav'))
        for t, n_ in r[2]:
            if n_ == 'count': cine.sfx(t, 'countup')
        r = (r[0], r[1], [c for c in r[2] if c[1] != 'count'])
    V.full(r); V.L_full(a, b, 'H'); _tr(a); return i
def sat(a, b, names=(), **kw):   # bản đồ vệ tinh: xã/phường · routes · pins
    V.full(map_ranh(_id('sat'), a, b, names, **kw)); V.L_full(a, b, 'SAT')
def R():
    import mg_real as m; return m
def mg_v4():
    import mg_v4 as m; return m
def B():
    import mg_bds as m; return m
def X():
    import mg_x as m; return m

# ---------- dùng trong build.py ----------
V = DA_ = None; WD = []; K = 0; SUBS = []; KIN = []; EXTRA = []; SPK = []
def init(v, da):
    global V, DA_, WD
    V, DA_, WD = v, da, _load(da); nen('do')   # nền mặc định: ĐỎ TRẦM hạt nhiễu (anh duyệt 23/11/2026; trước: than)
PEND = []   # phần còn lại của 1 từ gộp trong lời ('Đắk Lắk') khi subs.py viết tách ('Đắk Lắk' 2 chữ)
def _take(tok, spec):
    global K
    if PEND:
        w, part = PEND.pop(0)
        assert _norm(part) == _norm(tok), f"lệch từ ({w['start']}s): viết '{tok}' ≠ lời '{part}' (trong '{w['word']}') — {spec}"
        return dict(w, word=part)
    assert K < len(WD), f'hết lời mà còn chữ "{tok}" trong: {spec}'
    w = WD[K]; K += 1; nw, nt = _norm(w['word']), _norm(tok)
    if nw == nt: return w
    wp, tp = w['word'].split(), nt.split()
    if len(wp) > 1 and _norm(wp[0]) == nt:   # lời gộp, viết tách → nhận dần từng chữ
        PEND.extend((w, x) for x in wp[1:]); return dict(w, word=wp[0])
    if len(tp) > 1 and nw == tp[0]:          # lời tách, viết gộp ('Đắk_Lắk' hay 'Đắk Lắk' trong 1 khoá) → gom các từ lời
        ws = [w]
        while len(ws) < len(tp) and K < len(WD): ws.append(WD[K]); K += 1
        if _norm(' '.join(x['word'] for x in ws)) == nt: return dict(w, word=' '.join(x['word'] for x in ws), end=ws[-1].get('end'))
    raise AssertionError(f"lệch từ #{K - 1} ({w['start']}s): viết '{tok}' ≠ lời '{w['word']}' — {spec}")
def sub(spec, top=None):   # 'chữ | dòng 2 [g:từ khoá]' · [s:] đỏ [l:] xanh lá [g:] vàng · [sxl:] [lxl:] [gxl:] to · top None = tự theo cảnh
    spec = re.sub(r'\]([.,?!:;…]+)', r'\1]', spec)   # dấu câu viết sau ] → đưa vào trong từ khoá
    parts, toks, j = [], spec.replace('|', ' | ').split(), 0
    while j < len(toks):
        tk = toks[j]
        if tk == '|': parts.append('br')
        elif tk.startswith('['):
            kind, first = tk[1:].split(':', 1); grp = [first]
            while not grp[-1].endswith(']'): j += 1; grp.append(toks[j])
            grp[-1] = grp[-1][:-1]; ws = [_take(g, spec) for g in grp]
            parts.append(({'sxl': 'xl'}.get(kind, kind), ' '.join(w['word'] for w in ws), ws[0]['start']))
        else:
            w = _take(tk, spec); parts.append(('w', w['word'], w['start']))
        j += 1
    SUBS.append((parts, top))
def skip(spec):
    for tk in spec.split(): _take(tk, spec)
def kinetic(kid): KIN.append(kid)
def hook(text, **kw):
    if len(text) >= 8: kw.setdefault('size', min(100, int(520 / (len(text) * .62))))
    V.hook(text, **kw)
def ranh_map(i, a, b, names=(), **kw): V.full(map_ranh(i, a, b, names, **kw))
def speaker(t, j): SPK.append((t, {'trai': 0, 'trái': 0, 'phai': -1, 'phải': -1}.get(j, j)))   # ép người nói từ giây t (khung nhỏ)
def hide(css_sel): EXTRA.append(css_sel + '{display:none!important}')
MORPH_JS = ("VC.mcut=function(t){tl.to('#root',{scale:1.055,filter:'blur(2.5px)',duration:.22,ease:'power2.in',transformOrigin:'50% 45%'},t-.22);"
  "tl.set('#root',{scale:1.055,filter:'blur(2.5px)'},t);tl.to('#root',{scale:1,filter:'blur(0px)',duration:.5,ease:'power3.out'},t);"
  "tl.set('#root',{filter:'none'},t+.52);};"
  "VC.shrink=function(a,e){var f=VC._ff||[.5,.38],s=.348,L=Math.max(0,Math.min(220,f[0]*720-250)),T=Math.max(0,Math.min(740,f[1]*1280-250));"
  "var px=436-L*s,py=676-T*s,ct=Math.max(0,T-26/s),cl=Math.max(0,L-10/s),cb=Math.max(0,1280-(T+224/s)),cr=Math.max(0,720-(L+190/s)),D=.55;"
  "gsap.set('#pipImg',{left:-L*s,top:-T*s,width:720*s,height:1280*s});"
  "tl.set('#personWrap',{transformOrigin:'0px 0px',scale:1,x:0,y:0,clipPath:'inset(0px 0px 0px 0px round 0px)',filter:'contrast(1) saturate(1) brightness(1)',zIndex:9,autoAlpha:1},a);"
  "var C1=.25;tl.to('#personWrap',{clipPath:'inset('+ct+'px '+cr+'px '+cb+'px '+cl+'px round '+(18/s)+'px)',filter:'contrast(1.1) saturate(.84) brightness(.97)',duration:C1,ease:'power2.out'},a);"
  "tl.to('#personWrap',{scale:s,x:px,y:py,duration:D,ease:'expo.inOut'},a+C1);"
  "tl.set('#personWrap',{autoAlpha:0,zIndex:1},a+C1+D);tl.set('#pip',{opacity:0,scale:1},a);tl.to('#pip',{opacity:1,duration:.12},a+C1+D-.06);tl.set('#pip',{opacity:0},e);"
  "tl.set('#personWrap',{transformOrigin:VC._fo||'50% 38%',scale:1,x:0,y:0,clipPath:'none',filter:'none',zIndex:1,autoAlpha:1},e);};"
  "VC.ccut=function(t){tl.set('#root',{scale:1.04,transformOrigin:'50% 45%'},t);tl.to('#root',{scale:1,duration:.4,ease:'power2.out'},t);};"
  "VC.scut=function(t,d){tl.to('#root',{x:-90*d,filter:'blur(6px)',duration:.14,ease:'power2.in'},t-.14);tl.set('#root',{x:110*d},t);"
  "tl.to('#root',{x:0,filter:'blur(0px)',duration:.3,ease:'power3.out'},t);tl.set('#root',{filter:'none'},t+.32);};"
  "VC.fcut=function(t){tl.to('#root',{filter:'blur(12px) brightness(.8)',duration:.2,ease:'power2.in'},t-.2);tl.set('#root',{filter:'blur(12px) brightness(.8)'},t);"
  "tl.to('#root',{filter:'blur(0px) brightness(1)',duration:.32,ease:'power2.out'},t);tl.set('#root',{filter:'none'},t+.34);};")
CHUYEN = {'kieu': 'cat', 'thu': set()}   # anh chọn 27/11: B · cắt gọn
def chuyen(kieu='da'):   # P.chuyen('da'|'cat'|'truot'|'net') — kiểu chuyển cảnh: đà đẩy vào · cắt gọn · trượt ngang · lấy nét
    CHUYEN['kieu'] = kieu
def thu(t):   # P.thu(giây) — mốc mặt→đồ hoạ này: người THU MƯỢT vào khung kính nhỏ (anh 27/11, dùng ở mở đầu)
    CHUYEN['thu'].add(round(t, 2))
def _morph():   # anh 27/11 (bản 6): CHUYỂN CẢNH TỰ NHIÊN, LIỀN MẠCH — cắt theo đà chuyển động (momentum cut): cảnh cũ đẩy nhẹ vào 0,22 s → cắt gọn → cảnh mới tiếp đà và chậm lại; không tấm phủ, không chớp, không hoà trộn; mặt ẩn trong cảnh đồ hoạ
    if getattr(V, '_morph_on', False): return
    V._morph_on = True
    face = [(a, b) for n, a, b in V.LAYOUT if n == 'P']; fe = {round(b, 2) for a, b in face}; fs = {round(a, 2) for a, b in face}
    gr = sorted((a, b) for n, a, b in V.LAYOUT if n not in ('P', 'SPLIT'))
    ga = {round(a, 2) for a, b in gr}; gb = {round(b, 2) for a, b in gr}
    cuts = sorted(((fe & ga) | (gb & fs) | (gb & ga)) - {0})
    rx = re.compile(r"VC\.(wipe|whip|zoomThrough|flash|glitch)\(")
    for k, x in enumerate(V.J):
        if isinstance(x, str) and rx.match(x): V.J[k] = ''
    V.J.insert(0, MORPH_JS)
    orig = V.pip_apply
    def pa():
        orig()
        for k, x in enumerate(V.J):
            m = re.fullmatch(r"VC\.pip\(([\d.]+),([\d.]+)\);", x) if isinstance(x, str) else None
            if m and round(float(m.group(1)), 2) in CHUYEN['thu']: V.J[k] = ''
    V.pip_apply = pa
    TH = CHUYEN['thu']
    for n, t in enumerate(cuts):
        if t in TH: continue
        k = CHUYEN['kieu']
        V.J.append({'da': f"VC.mcut({t});", 'cat': f"VC.ccut({t});", 'truot': f"VC.scut({t},{1 if n % 2 == 0 else -1});", 'net': f"VC.fcut({t});"}[k])
        if k != 'cat': V.cue(t - .2, 'whoosh')
    for a_, b_ in gr:   # mặt không lẫn vào đồ hoạ
        if round(a_, 2) in TH and round(a_, 2) in fe:
            e_ = b_
            for a2, b2 in gr:
                if abs(a2 - e_) < .15: e_ = b2
            V.J.append(f"VC.shrink({a_},{e_});"); V.cue(a_, 'whoosh'); continue
        if round(a_, 2) in fe: V.J.append(f"tl.set('#personWrap',{{autoAlpha:0}},{a_ + .01:.2f});")
        if round(b_, 2) in fs: V.J.append(f"tl.set('#personWrap',{{autoAlpha:1}},{b_:.2f});")
def finish():
    _morph()
    assert K == len(WD), f"còn {len(WD) - K} từ chưa lên phụ đề, từ '{WD[K]['word']}' ({WD[K]['start']}s)"
    T = V.T; cuts = sorted({0, T} | {x for _, a, b in V.LAYOUT for x in (a, b)})
    FW = [(a, b) for n, a, b in V.LAYOUT if n not in ('P', 'SPLIT')]; SW = [(a, b) for n, a, b in V.LAYOUT if n == 'SPLIT']
    inw = lambda t, ws: any(a - .01 <= t < b for a, b in ws)
    for n, (parts, top) in enumerate(SUBS):
        ts = [p[2] for p in parts if p != 'br']; t0 = ts[0]
        for c in cuts:
            if t0 + .01 < c < min(ts[-1] - .01, T - .05): print(f'  ⚠ cụm sb{n} ({t0}s) vắt qua mốc {c} → tách cụm hoặc dời mốc')
        nxt = next((next(p[2] for p in q if p != 'br') for q, _ in SUBS[n + 1:]), T)
        cut_ = next((c for c in cuts if c > t0 + .01), T)
        if top is None: top = 478 if inw(t0, SW) else 712 if inw(t0, FW) else 780
        V.mix(f'sb{n}', parts, top, out=round(min(nxt - .1, cut_ - .2, T - .2), 2))
    sp = os.path.join(DA_, 'speakers.json'); SP = json.load(open(sp)) if os.path.exists(sp) else {}
    if len(SP.get('faces', [])) >= 2:
        W = sorted((a, b) for n, a, b in V.LAYOUT if n not in ('P', 'SPLIT'))
        seg = sorted(SP['seg'] + [[t, t, j] for t, j in SPK])
        def who(t): return ([j for a, b, j in seg if a - .05 <= t] or [seg[0][2]])[-1]
        for a, b in W:
            for t in [a] + [s[0] for s in seg if a < s[0] < b]:
                fx, fy = SP['faces'][who(t)]; L = max(0, min(220, fx * 720 - 250)) * .348; Tp = max(0, min(740, fy * 1280 - 250)) * .348
                V.J.append(f"tl.set('#pipImg',{{left:{-L:.1f},top:{-Tp:.1f}}},{max(0, t - .02):.2f});")
    json.dump([[n, a, b] for n, a, b in V.LAYOUT], open(os.path.join(DA_, 'layout.json'), 'w'))
    _wm_html()
    V.H.append('<style id="phude">' + font_css() + lpv_css() + CSS + ''.join(KCSS.replace('#K', '#' + k) for k in KIN) + ''.join(EXTRA) + '</style>')
    print(f'  ✓ phụ đề: {len(SUBS)} cụm · {len(WD)} từ')

if __name__ == '__main__':
    c, *a = sys.argv[1:]
    {'setup': setup, 'go': go, 'cut': cut, 'build': build, 'out': out, 'wait': wait, 'grid': grid, 'ranh': ranh, 'speakers': speakers, 'xem': xem, 'diadanh': diadanh, 'sb': sb}[c](*a)
