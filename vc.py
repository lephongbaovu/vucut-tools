"""vc.py · vucut gọn: setup | go VIDEO DA [thu] | cut DA ["sai=>đúng"…] [--keep a-b] [--drop a-b] | build DA | out DA | wait DA | grid DA [video.mp4] [giây…] | ranh [tên…] | speakers DA
Trong build.py (tự sinh): import vc as P → P.sub / P.skip / P.kinetic / P.hook / P.hide / P.speaker · cảnh mẫu P.mat / P.vanban / P.ds / P.so / P.hinh / P.sat"""
import base64, glob, json, os, re, subprocess, sys, tarfile, tempfile, time
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

CSS = r"""#pip{border:0!important;border-radius:16px!important;box-shadow:0 0 0 1px rgba(255,255,255,.18),0 10px 28px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.35)!important}
#pip:after{content:"";position:absolute;left:14px;bottom:12px;width:26px;height:2px;border-radius:2px;background:#E8C27A;opacity:.9;z-index:2}
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
    os.makedirs(T_DIR, exist_ok=True); open(VCP, 'w').write(os.path.abspath(vc))
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
MOODS = {   # hợp âm (MIDI) · gốc bass · BPM · độ sáng · mô tả
    'sang': dict(ch=[[55, 59, 62, 67], [50, 54, 57, 62], [52, 55, 59, 64], [48, 52, 55, 60]], root=[43, 38, 40, 36], bpm=100,
                 desc='ấm áp – hy vọng (Sol trưởng G–D–Em–C): an cư, an sinh, cơ hội, tin tích cực'),
    'hung': dict(ch=[[50, 53, 57, 62], [46, 50, 53, 58], [48, 52, 55, 60], [45, 49, 52, 57]], root=[38, 34, 36, 33], bpm=112,
                 desc='hùng tráng – đà phát triển (Rê thứ Dm–Bb–C–A): hạ tầng lớn, cao tốc, sân bay, vốn đầu tư'),
    'toi':  dict(desc='điện ảnh tối, nhịp đều (mặc định cũ): rủi ro, cảnh báo, pháp lý'),
}
def nhac(mood='sang'):   # P.nhac('sang'|'hung'|'toi') trong scenes.py — chọn mood nhạc nền theo nội dung
    assert mood in MOODS, f'mood: {list(MOODS)}'; json.dump({'mood': mood}, open(os.path.join(DA_, 'nhac.json'), 'w'))
def _music(dur, impacts, mood, path):
    import numpy as np, wave
    from scipy.signal import butter, sosfilt
    M = MOODS[mood]; sr = 48000; N = int(sr * dur); L = np.zeros(N); Rr = np.zeros(N); rng = np.random.default_rng(11)
    BEAT = 60 / M['bpm']; BAR = 4 * BEAT; nb = int(dur / BAR) + 1; hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    lpf = lambda x, f: sosfilt(butter(2, f, 'low', fs=sr, output='sos'), x); hpf = lambda x, f: sosfilt(butter(2, f, 'high', fs=sr, output='sos'), x)
    def add(x, t, gl, gr=None):
        a = int(t * sr)
        if a >= N or a < 0: return
        x = x[:N - a]; L[a:a + len(x)] += gl * x; Rr[a:a + len(x)] += (gl if gr is None else gr) * x
    imp = sorted(impacts); peak = max([t for t in imp if t > dur * .6] or [dur * .8])
    def energy(t):   # 0.35 mở → 0.7 thân → 1.0 quanh cao trào → 0.6 kết
        return .35 + .35 * min(1, t / 8) + .3 * math.exp(-((t - peak) / 9) ** 2)
    for b in range(nb):   # PAD ấm (2 saw tách âm lọc thấp + sine)
        t0 = b * BAR; d = BAR + .8; n = int(sr * d); m = np.arange(n) / sr
        e = np.minimum(1, m / .6) * np.minimum(1, (d - m) / .8)
        for k, q in enumerate(M['ch'][b % 4]):
            f = hz(q); x = (2 * ((f * 1.004 * m) % 1) - 1 + 2 * ((f * .996 * m) % 1) - 1) * .5
            x = lpf(x, 1100 if mood == 'sang' else 800) * .05 + np.sin(2 * np.pi * f * m) * .03
            add(x * e, t0, .8 if k % 2 else .6, .6 if k % 2 else .8)
    pat = [0, 1, 2, 3, 2, 1, 3, 2] if mood == 'sang' else [0, 2, 1, 3, 0, 2, 1, 3]
    for b in range(nb):   # PIANO/PLUCK rải hợp âm móc 8 (vào ngay — giữ nhịp từ giây đầu)
        for st in range(8):
            t0 = b * BAR + st * BEAT / 2; q = M['ch'][b % 4][pat[st]] + 12; m = np.arange(int(sr * .9)) / sr; f = hz(q)
            x = (np.sin(2 * np.pi * f * m) + .45 * np.sin(4 * np.pi * f * m) * np.exp(-m * 6) + .2 * np.sin(6 * np.pi * f * m) * np.exp(-m * 9)) * np.exp(-m * 4.5)
            g = .07 * energy(t0) / .7; pn = .35 + .3 * (st % 2); add(x, t0, g * (1 - pn), g * pn)
    for b in range(1, nb):   # BASS gốc: phách 1 + móc trước phách 3
        for off, g in ((0, .26), (BEAT * 1.5, .14), (BEAT * 2, .2)):
            t0 = b * BAR + off; m = np.arange(int(sr * BEAT * 1.2)) / sr; f = hz(M['root'][b % 4])
            x = np.tanh(1.5 * np.sin(2 * np.pi * f * m)) * np.exp(-m * 3.5); add(x, t0, g * min(1, energy(t0) / .6))
    def kick():
        m = np.arange(int(sr * .35)) / sr; return np.sin(2 * np.pi * np.cumsum(48 + 75 * np.exp(-m * 32)) / sr) * np.exp(-m * 10)
    def noise(d, hp, dec): m = np.arange(int(sr * d)) / sr; return hpf(rng.standard_normal(len(m)), hp) * np.exp(-m * dec)
    K = kick(); SH = noise(.05, 6000, 90); SN = lpf(noise(.22, 1500, 20), 6000)
    for b in range(2, nb):   # TRỐNG mềm, dày dần theo năng lượng
        for qd in range(4):
            t0 = b * BAR + qd * BEAT; e = energy(t0)
            if qd in (0, 2) or (mood == 'hung' and e > .75): add(K, t0, .3)
            if b >= 4:
                for s16 in range(2): add(SH, t0 + s16 * BEAT / 2, .03 * e, .045 * e)
            if b >= 6 and qd in (1, 3): add(SN, t0, .06 * e)
            if mood == 'hung' and e > .8 and qd == 3: add(lpf(noise(.3, 80, 9), 300), t0 + BEAT * .5, .2)   # tom trầm
    for t in imp:   # tại mốc lớn: riser 1.2 s trước + "bừng sáng" (cymbal + sub mềm)
        m = np.arange(int(sr * 1.2)) / sr; rs = hpf(rng.standard_normal(len(m)), 2500) * (m / 1.2) ** 2.5; add(rs, t - 1.2, .05)
        m = np.arange(int(sr * 2.4)) / sr; cy = hpf(rng.standard_normal(len(m)), 5000) * np.exp(-m * 2.2)
        sb = np.sin(2 * np.pi * np.cumsum(55 + 30 * np.exp(-m * 8)) / sr) * np.exp(-m * 2.5); add(cy * .06 + sb * .22, t, 1.0)
    x = np.stack([L, Rr], 1); fi = np.minimum(1, np.arange(N) / (sr * 1.0)); fo = np.minimum(1, (N - np.arange(N)) / (sr * 1.2))
    x *= (fi * fo)[:, None]; x = hpf(x.T, 30).T; x = x / (np.abs(x).max() + 1e-9) * 10 ** (-1 / 20)
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
def _remix(DA):   # thay nhạc mặc định bằng nhạc theo mood (P.nhac), trộn lại đúng như vucut.py audio (nghẹt · tắt trước câu đắt · nhường giọng)
    nf = os.path.join(DA, 'nhac.json'); mood = json.load(open(nf))['mood'] if os.path.exists(nf) else 'toi'
    if mood == 'toi': return
    j = lambda *x: os.path.join(DA, *x); plan = json.load(open(j('audio.json'), encoding='utf-8')) if os.path.exists(j('audio.json')) else {}
    T = json.load(open(j('state.json')))['T']; _music(T, plan.get('impacts', []), mood, j('music.wav'))
    btw = lambda W: '+'.join(f'between(t,{x},{y})' for x, y in W) or '0'; Wm, Dk = btw(plan.get('muffle', [])), btw(plan.get('duck', []))
    fc = (f"[1:a]aresample=48000,volume=-12dB,asplit=2[mA][mB];[mA]volume='if({Wm},0,1)':eval=frame[full];"
          f"[mB]lowpass=f=520,lowpass=f=520,volume=2dB,volume='if({Wm},1,0)':eval=frame[muff];"
          f"[full][muff]amix=inputs=2:normalize=0,volume='if({Dk},0.03,1)':eval=frame[m];"
          f"[2:a]pan=stereo|c0=c0|c1=c0[key];[m][key]sidechaincompress=threshold=0.15:ratio=3:attack=80:release=650:knee=6[md];"
          f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0[v];[v][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', j('voice_sfx.m4a'), '-i', j('music.wav'), '-i', j('voice.wav'), '-filter_complex', fc,
                    '-map', '[out]', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', j('final_audio.m4a')], check=True)
    print(f'xong → nhạc nền mood "{mood}": {MOODS[mood]["desc"]}')

def out(DA):
    DA = os.path.abspath(os.path.expanduser(DA))
    for f in ('final_audio_base.m4a', 'final_audio.m4a'):
        if os.path.exists(os.path.join(DA, f)): os.remove(os.path.join(DA, f))
    sh(f'python3 {T_DIR}/cine_sfx.py sfx', cwd=DA, tail=1)
    sh(f'{PY()} audio {DA}', keep='LUFS|✖')
    _remix(DA)
    sh(f'python3 {T_DIR}/cine_sfx.py --layer {DA}', tail=1)
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
def _tiles(z, x0, y0, x1, y1):   # ảnh vệ tinh Bing (cache ~/.vucut/tiles) → PIL mosaic từ pixel (x0,y0) tới (x1,y1) ở zoom z
    from PIL import Image; from concurrent.futures import ThreadPoolExecutor
    cd = os.path.join(HOME, 'tiles'); os.makedirs(cd, exist_ok=True); tx = range(int(x0 // 256), int(x1 // 256) + 1); ty = range(int(y0 // 256), int(y1 // 256) + 1)
    def qk(x, y): return ''.join(str((((x >> i) & 1) | (((y >> i) & 1) << 1))) for i in range(z - 1, -1, -1))
    def get(xy):
        x, y = xy; f = os.path.join(cd, f'{z}_{x}_{y}.jpg')
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
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
def _road(wps):   # tuyến theo đường thật qua các điểm
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

def map_ranh(i, a, b, names=(), t_draw=None, label='', sub='', km2=False, routes=(), pins=(), center=None, km=6):
    """bản đồ vệ tinh: zoom từ xa vào · xã/phường (names) viền vàng tự vẽ + vệt trắng chạy · tuyến đường (routes) xanh sáng tự vẽ · ghim (pins)
    routes=[('QUỐC LỘ 14', ['buonmathuot', 'Ea Kao'], t)] · pins=[('SÂN BAY', 'sanbaybmt', t)] · center=(điểm) km= bán kính khi không có xã"""
    D = _dtinh(); names = [names] if isinstance(names, str) else list(names); ks = [_pick(D, s) for s in names]
    t_draw = max(a + 1.2, a + .35 if t_draw is None else t_draw); DR = 1.0
    RT = [(lb, _road(w), (t if t is not None else t_draw + .3 + .4 * n)) for n, (lb, w, *t_) in enumerate(routes) for t in [t_[0] if t_ else None]]
    PN = [(lb, _pt(p), (t_[0] if t_ else t_draw + .5 + .3 * n)) for n, (lb, p, *t_) in enumerate(pins)]
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
    js = [f"tl.set('#{i}',{{autoAlpha:0}},0);", f"tl.to('#{i}',{{autoAlpha:1,duration:.25}},{a});"]
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
        svg += (f'<path class="rg{n}" d="{d}" fill="none" stroke="#3DF2A6" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" filter="url(#{i}g)" opacity=".8" stroke-dasharray="{L2:.0f} {L2:.0f}" stroke-dashoffset="{L2:.0f}"/>'
                f'<path class="rl{n}" d="{d}" fill="none" stroke="#9BFFD6" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L2:.0f} {L2:.0f}" stroke-dashoffset="{L2:.0f}"/>')
        js += [f"tl.to('#{i} .rg{n},#{i} .rl{n}',{{strokeDashoffset:0,duration:1.1,ease:'power1.inOut'}},{t:.2f});"]
        if lb: svg += chip(mid[0], mid[1] - 30, lb, '#9BFFD6', f'rc{n}', t + .6)
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
            f'{svg}{tt}<text class="cr" x="40" y="985" font-family="VCB6,sans-serif" font-weight="600" font-size="14" fill="rgba(255,255,255,.55)">Ảnh vệ tinh: Bing Maps · '
            + ('Ranh giới 2025: Bộ NN&amp;MT' if ks else '') + (' · ' if ks and RT else '') + ('Tuyến: OpenStreetMap' if RT else '') + '</text></svg></div>')
    js.append(f"tl.set('#{i}',{{autoAlpha:0}},{b});")
    if DA_:
        import cine
        if ks: os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_ranh(os.path.join(DA_, 'sfx', 'ranh.wav'), DR); cine.sfx(t_draw - .05, 'ranh')
    return html, js, [(a, 'whoosh')] + [(t, 'whoosh') for _, _, t in RT] + [(t, 'pop') for _, _, t in PN]

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
    'den':  '#0d0d0f',
    'than': 'radial-gradient(120% 75% at 28% 16%,#27221c 0%,#16130f 46%,#0a0907 100%)',
    'dem':  'radial-gradient(120% 75% at 28% 16%,#1a2633 0%,#0f1720 48%,#070a0e 100%)',
    'da':   'radial-gradient(85% 45% at 50% -4%,rgba(232,194,122,.13),rgba(232,194,122,0) 70%),radial-gradient(140% 90% at 50% 40%,#1c1c1f 0%,#121214 55%,#08080a 100%)',
}
def nen(ten='than'):   # P.nen('than'|'dem'|'da'|'den') đầu scenes.py — đổi nền mọi hình R.
    R().BG = NEN.get(ten, ten)
CTA_TEN, CTA_CHUC = 'Lê Phong Vũ', 'GĐDA · Tây Nguyên Investment'
FOIL = ("background:linear-gradient(100deg,#7a5a24 0%,#c9a25a 14%,#f6e2a2 24%,#fff6d6 28%,#d9b468 38%,#8c6a2c 52%,#e8c983 64%,#fff1c2 70%,#b88f45 82%,#6e5020 100%);"
        "background-size:240% 100%;background-position:100% 0;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;"
        "padding:.22em .04em .26em;margin:-.22em -.04em -.26em;filter:drop-shadow(0 1.5px 0 rgba(70,48,12,.95)) drop-shadow(0 10px 22px rgba(0,0,0,.55))")   # đệm để dấu tiếng Việt (Ị, Ũ, Ỗ) không bị cắt
def _foil_js(sel, t, d=1.6): return f"tl.fromTo('{sel}',{{backgroundPosition:'100% 0'}},{{backgroundPosition:'0% 0',duration:{d},ease:'power2.inOut'}},{t:.2f});"
def cta(a, b, follow, hoi=None, chu=(), ten=CTA_TEN, chuc=CTA_CHUC, nut='Follow', xong='Đã follow', hoi_txt=('ANH CHỊ', 'CÓ CÂU HỎI?')):
    """MẪU KÊU GỌI CUỐI VIDEO — cảnh đồ hoạ nền than + khung nhân vật nhỏ, chữ NHŨ VÀNG:
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
                 + ''.join(f'<div class="h{k}" style="font-family:VCS,serif;font-weight:700;font-size:{82 if k else 64}px;line-height:1.08;letter-spacing:.01em;margin-top:{14 if not k else 0}px;{FOIL}">{x}</div>' for k, x in enumerate(hoi_txt))
                 + '</div>'
                 f'<div class="bu" style="position:absolute;left:70px;top:405px;width:300px;height:170px;transform:scale(1.25);transform-origin:0 0">'
                 f'<svg width="300" height="170" viewBox="0 0 300 170"><defs><linearGradient id="{i}b1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a332a"/><stop offset="1" stop-color="#1c1814"/></linearGradient>'
                 f'<linearGradient id="{i}b2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6e2a2"/><stop offset=".5" stop-color="#c9a25a"/><stop offset="1" stop-color="#7a5a24"/></linearGradient></defs>'
                 f'<path d="M30 14 H270 a22 22 0 0 1 22 22 V104 a22 22 0 0 1 -22 22 H96 L58 156 L64 126 H30 a22 22 0 0 1 -22 -22 V36 a22 22 0 0 1 22 -22Z" fill="url(#{i}b1)" stroke="url(#{i}b2)" stroke-width="2.5"/>'
                 f'<path d="M34 22 H262" stroke="#fff" stroke-opacity=".18" stroke-width="3" stroke-linecap="round"/>'
                 + ''.join(f'<circle class="d{k}" cx="{110 + k * 40}" cy="70" r="11" fill="url(#{i}b2)"/>' for k in range(3)) + '</svg></div>'
                 f'<div class="ar" style="position:absolute;left:470px;top:455px;font-family:VCB,sans-serif;font-weight:800;font-size:21px;letter-spacing:2.5px;color:rgba(246,241,231,.8);line-height:1.5">BÌNH LUẬN<br>BÊN DƯỚI <span class="aw" style="display:inline-block;color:#E8C27A">↓</span></div>')
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
    V, DA_, WD = v, da, _load(da); nen('than')   # nền mặc định: THAN ẤM (anh duyệt 19/11/2026)
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
def finish():
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
    V.H.append('<style id="phude">' + font_css() + CSS + ''.join(KCSS.replace('#K', '#' + k) for k in KIN) + ''.join(EXTRA) + '</style>')
    print(f'  ✓ phụ đề: {len(SUBS)} cụm · {len(WD)} từ')

if __name__ == '__main__':
    c, *a = sys.argv[1:]
    {'setup': setup, 'go': go, 'cut': cut, 'build': build, 'out': out, 'wait': wait, 'grid': grid, 'ranh': ranh, 'speakers': speakers, 'xem': xem, 'diadanh': diadanh}[c](*a)
