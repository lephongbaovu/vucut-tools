"""vc.py · vucut gọn: setup | go VIDEO DA [thu] | cut DA ["sai=>đúng"…] [--keep a-b] [--drop a-b] | build DA | out DA | wait DA | grid DA [video.mp4] [giây…] | ranh [tên…] | speakers DA
Trong build.py (tự sinh): import vc as P → P.sub / P.skip / P.kinetic / P.hook / P.hide / P.ranh_map / P.speaker"""
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

CSS = r""".mix{row-gap:2px!important;column-gap:9px!important}.mix:not(.cardmix){width:600px!important}
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

def go(video, DA, *a):
    DA = os.path.abspath(os.path.expanduser(DA))
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

def _assemble(DA):
    st = json.load(open(os.path.join(DA, 'state.json'))); sc = open(os.path.join(DA, 'scenes.py'), encoding='utf-8').read()
    kind = (re.search(r"KIND\s*=\s*'(\w+)'", sc) or [0, 'phantich'])[1]; vc = VC()
    head = os.path.join(DA, 'facetrack.json'); face = tuple(st.get('face') or (.5, .38))
    src = (f"import sys, os; sys.path[:0] = [r'{vc}/scripts', r'{T_DIR}']\n"
           "import vc_build as V, mg_nganh as N, cine as C, vc as P\n"
           "import mg_x as X, mg_bds as B, mg_dl as DL, mg_v4, mg_journey as MJ, mg\n"
           f"V.init(T={st['T']}, face={face}, head=r'{head}', kind='{kind}')\n"
           f"C.init(r'{DA}'); P.init(V, r'{DA}')\n# ---- scenes.py ----\n{sc}\n# ---- hết scenes ----\n"
           f"exec(open(r'{DA}/subs.py', encoding='utf-8').read())\nP.finish()\n"
           f"V.finish(r'{DA}/build/master.html', r'{DA}/cues.json', shell=r'{vc}/assets/template/vucut_9x16_v4.html')\n")
    open(os.path.join(DA, 'build.py'), 'w', encoding='utf-8').write(src)

def build(DA):
    DA = os.path.abspath(os.path.expanduser(DA)); _assemble(DA)
    sh(f'python3 -X utf8 {DA}/build.py', keep=r'⚠|✖|MẶT HIỆU|phụ đề|Error|Traceback|line \d+|^\w+Error', tail=30)
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

def out(DA):
    DA = os.path.abspath(os.path.expanduser(DA))
    for f in ('final_audio_base.m4a', 'final_audio.m4a'):
        if os.path.exists(os.path.join(DA, f)): os.remove(os.path.join(DA, f))
    sh(f'python3 {T_DIR}/cine_sfx.py sfx', cwd=DA, tail=1)
    sh(f'{PY()} audio {DA}', keep='LUFS|✖')
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
def _pick(D, s):
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

def map_ranh(i, a, b, names, t_draw=None, label='', sub='', km2=False):
    """bản đồ vệ tinh: zoom từ xa vào xã/phường · ngoài vùng tối đi · viền vàng tự vẽ (kèm tiếng vút + lấp lánh) · vệt trắng chạy quanh · tên vàng giữa vùng"""
    D = _ranh_data()['xa']; ks = [_pick(D, s) for s in (names if isinstance(names, (list, tuple)) else [names])]
    t_draw = max(a + 1.2, a + .35 if t_draw is None else t_draw); DR = 1.0
    pts = [p for k in ks for r in D[k]['r'] for p in r]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    BX = (70, 170, 650, 640)   # khung đặt vùng (trên phụ đề + khung người nói)
    z = 18
    while z > 8:
        ax, ay = _wm(x0, y1, z); bx, by = _wm(x1, y0, z)
        if (bx - ax) <= (BX[2] - BX[0]) * 1.5 and (by - ay) <= (BX[3] - BX[1]) * 1.5: break
        z -= 1
    ax, ay = _wm(x0, y1, z); bx, by = _wm(x1, y0, z); k_ = min((BX[2] - BX[0]) / (bx - ax), (BX[3] - BX[1]) / (by - ay))   # css px / tile px
    cxp, cyp = (ax + bx) / 2, (ay + by) / 2; ox, oy = (BX[0] + BX[2]) / 2, (BX[1] + BX[3]) / 2
    def S(lon, lat): px, py = _wm(lon, lat, z); return ox + (px - cxp) * k_, oy + (py - cyp) * k_
    # ảnh chi tiết phủ khung 720×1280 (+8 %) và ảnh xa ở zoom z-2 phủ gấp 4 lần
    def box(zz, f):
        s = k_ * 2 ** (z - zz); c = (cxp / 2 ** (z - zz), cyp / 2 ** (z - zz))
        X0, Y0 = c[0] - (ox + 720 * (f - 1) / 2) / s, c[1] - (oy + 1280 * (f - 1) / 2) / s
        return _tiles(zz, X0, Y0, X0 + 720 * f / s, Y0 + 1280 * f / s), f
    det, fd = box(z, 1.08); wid, fw = box(max(1, z - 2), 4.0)
    def path(rs): return ''.join('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in (S(*p) for p in r)) + 'Z' for r in rs)
    def plen(r): q = [S(*p) for p in r] + [S(*r[0])]; return sum(math.dist(q[n], q[n + 1]) for n in range(len(q) - 1))
    allp = ''.join(path(D[k]['r']) for k in ks); L = sum(plen(r) for k in ks for r in D[k]['r'])
    big = max((r for k in ks for r in D[k]['r']), key=len); cc = [S(*p) for p in big]; ccx = sum(x for x, _ in cc) / len(cc); ccy = sum(y for _, y in cc) / len(cc)
    ttl = label or (D[ks[0]]['full'].upper() if len(ks) == 1 else ' · '.join(D[k]['ten'].upper() for k in ks))
    if km2 and len(ks) == 1 and D[ks[0]].get('km2'): sub = sub or f"{D[ks[0]]['km2']:g} km²"
    fs_ = min(40, int(560 / (len(ttl) * .64))); ccx = min(max(ccx, 60 + len(ttl) * fs_ * .32), 660 - len(ttl) * fs_ * .32); ccy = min(max(ccy, 200), 600)
    html = (f'<div class="vc" data-mg="ranh" id="{i}" style="left:0;top:0;width:720px;height:1280px;z-index:7;overflow:hidden;background:#0b0c0a">'
            f'<div class="cam" style="position:absolute;left:0;top:0;width:720px;height:1280px">'
            f'<img class="wd" src="data:image/jpeg;base64,{_b64(wid.resize((1440, 2560)), 72)}" style="position:absolute;left:{-720 * (fw - 1) / 2:.0f}px;top:{-1280 * (fw - 1) / 2:.0f}px;width:{720 * fw:.0f}px;height:{1280 * fw:.0f}px"/>'
            f'<img class="dt" src="data:image/jpeg;base64,{_b64(det, 82)}" style="position:absolute;left:{-720 * (fd - 1) / 2:.0f}px;top:{-1280 * (fd - 1) / 2:.0f}px;width:{720 * fd:.0f}px;height:{1280 * fd:.0f}px;opacity:0"/></div>'
            f'<svg viewBox="0 0 720 1280" width="720" height="1280" style="position:absolute;left:0;top:0"><defs>'
            f'<filter id="{i}g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9"/></filter>'
            f'<filter id="{i}g2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.5"/></filter></defs>'
            f'<path class="dim" d="M0 0H720V1280H0Z{allp}" fill="#000" fill-rule="evenodd" opacity="0"/>'
            f'<path class="gl" d="{allp}" fill="none" stroke="#F0C460" stroke-width="16" stroke-linejoin="round" stroke-linecap="round" filter="url(#{i}g)" opacity=".85" stroke-dasharray="{L:.0f} {L:.0f}" stroke-dashoffset="{L:.0f}"/>'
            f'<path class="ln" d="{allp}" fill="none" stroke="#F6D37E" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{L:.0f} {L:.0f}" stroke-dashoffset="{L:.0f}"/>'
            f'<path class="cm" d="{allp}" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-dasharray="{L * .1:.0f} {L * .9:.0f}" filter="url(#{i}g2)" opacity="0"/>'
            f'<g class="tt"><text x="{ccx:.0f}" y="{ccy:.0f}" text-anchor="middle" font-family="VCB,sans-serif" font-weight="800" font-size="{fs_}" letter-spacing="1" fill="#F2CC74" '
            f'style="paint-order:stroke;stroke:rgba(0,0,0,.55);stroke-width:5px;filter:drop-shadow(0 2px 8px rgba(0,0,0,.8))">{ttl}</text>'
            + (f'<text x="{ccx:.0f}" y="{ccy + fs_ * .9:.0f}" text-anchor="middle" font-family="VCB,sans-serif" font-weight="800" font-size="{int(fs_ * .55)}" fill="#fff" '
               f'style="paint-order:stroke;stroke:rgba(0,0,0,.6);stroke-width:4px">{sub}</text>' if sub else '') + '</g>'
            f'<text class="cr" x="40" y="985" font-family="VCB6,sans-serif" font-weight="600" font-size="14" fill="rgba(255,255,255,.55)">Ảnh vệ tinh: Bing Maps · Ranh giới 2025: Bộ NN&amp;MT</text></svg></div>')
    tz = t_draw - .15; lap = 2.2; nlap = max(0, int((b - t_draw - DR) / lap))
    js = [f"tl.set('#{i}',{{autoAlpha:0}},0);", f"tl.to('#{i}',{{autoAlpha:1,duration:.25}},{a});",
          f"tl.fromTo('#{i} .cam',{{scale:{1 / 2.8:.4f},transformOrigin:'{ox:.0f}px {oy:.0f}px'}},{{scale:1,duration:{tz - a:.2f},ease:'power2.inOut'}},{a});",
          f"tl.to('#{i} .dt',{{opacity:1,duration:{min(.8, (tz - a) * .5):.2f}}},{tz - min(.8, (tz - a) * .5):.2f});",
          f"tl.fromTo('#{i} .cam',{{scale:1}},{{scale:1.04,duration:{max(.5, b - tz):.2f},ease:'none'}},{tz:.2f});",
          f"tl.to('#{i} .dim',{{opacity:.5,duration:.5}},{tz:.2f});",
          f"tl.to('#{i} .ln',{{strokeDashoffset:0,duration:{DR},ease:'none'}},{t_draw:.2f});",
          f"tl.to('#{i} .gl',{{strokeDashoffset:0,duration:{DR},ease:'none'}},{t_draw:.2f});",
          f"tl.set('#{i} .tt',{{opacity:0,y:8}},0);", f"tl.to('#{i} .tt',{{opacity:1,y:0,duration:.4,ease:'power2.out'}},{t_draw + DR * .7:.2f});",
          f"tl.set('#{i} .cm',{{opacity:1}},{t_draw + DR:.2f});",
          f"tl.fromTo('#{i} .cm',{{strokeDashoffset:0}},{{strokeDashoffset:{-L:.0f},duration:{lap},repeat:{nlap},ease:'none'}},{t_draw + DR:.2f});",
          f"tl.set('#{i}',{{autoAlpha:0}},{b});"]
    if DA_:
        os.makedirs(os.path.join(DA_, 'sfx'), exist_ok=True); _sfx_ranh(os.path.join(DA_, 'sfx', 'ranh.wav'), DR)
        import cine; cine.sfx(t_draw - .05, 'ranh')
    return html, js, [(a, 'whoosh')]

# ---------- dùng trong build.py ----------
V = DA_ = None; WD = []; K = 0; SUBS = []; KIN = []; EXTRA = []; SPK = []
def init(v, da):
    global V, DA_, WD
    V, DA_, WD = v, da, _load(da)
def _take(tok, spec):
    global K
    assert K < len(WD), f'hết lời mà còn chữ "{tok}" trong: {spec}'
    w = WD[K]; K += 1
    assert _norm(w['word']) == _norm(tok), f"lệch từ #{K - 1} ({w['start']}s): viết '{tok}' ≠ lời '{w['word']}' — {spec}"
    return w
def sub(spec, top=None):   # 'chữ | dòng 2 [g:từ khoá]' · [s:] đỏ [l:] xanh lá [g:] vàng · [sxl:] [lxl:] [gxl:] to · top None = tự theo cảnh
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
def ranh_map(i, a, b, names, t_draw=None, label='', sub='', km2=False): V.full(map_ranh(i, a, b, names, t_draw, label, sub, km2))
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
    V.H.append('<style id="phude">' + font_css() + CSS + ''.join(KCSS.replace('#K', '#' + k) for k in KIN) + ''.join(EXTRA) + '</style>')
    print(f'  ✓ phụ đề: {len(SUBS)} cụm · {len(WD)} từ')

if __name__ == '__main__':
    c, *a = sys.argv[1:]
    {'setup': setup, 'go': go, 'cut': cut, 'build': build, 'out': out, 'wait': wait, 'grid': grid, 'ranh': ranh, 'speakers': speakers}[c](*a)
