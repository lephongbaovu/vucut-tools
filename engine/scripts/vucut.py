#!/usr/bin/env python3
"""vucut.py — chạy cả dây chuyền vucut bằng vài lệnh. Claude chỉ cần viết SHOTBOOK + build.py.

  python -X utf8 vucut.py setup                               kiểm tra/cài thư viện (chạy 1 lần mỗi máy)
  python -X utf8 vucut.py prep  goc.mp4 DA [--clip 0-30] [--speed 1.1] [--model medium] [--crop-x 0.5 (bỏ trống = tự bám mặt)]
        → DA/source.mp4 (đã tăng tốc ×speed, giữ cao độ giọng), DA/words.json (phiên âm, có sẵn thì bỏ qua), in bảng autocut --dry
  python -X utf8 vucut.py cut   DA [--keep a-b,..] [--drop a-b,..] [--no-autocut] [--no-tighten] [--frames-h 1920]
        → cut/ (autocut) → cut2/ (rút lặng) → frames/ → build/lib/ ; in T và lệnh V.init cho build.py
  python -X utf8 vucut.py beats DA                            BẢNG NHỊP: năng lượng thể hiện + vai từng câu → gợi ý mặt/hình (DA/beats.json)
  (Claude viết DA/build.py từ SHOTBOOK → python -X utf8 DA/build.py → build/master.html + cues.json [+ audio.json])
  python -X utf8 vucut.py split DA "a-b,a-b"                  tách nền đầu nổi cho cảnh SPLIT (giây video cuối)
  python -X utf8 vucut.py audio DA [--no-music] [--denoise 12] [--lufs -14]   giọng (lọc ồn) + SFX thưa + nhạc → chuẩn hoá độ to → final_audio.m4a
  python -X utf8 vucut.py probe DA 0.5,3,8 [--cuts]           chụp khung + ghép 1 tấm qc/sheet.jpg để tự xem
  python -X utf8 vucut.py render DA [--draft] [--jobs 4] [--scale 1.5]
        → out_vN.mp4 (draft: 720×1280, nhanh; mặc định: 1080×1920 bản cuối)
Mọi bước ghi DA/state.json để bước sau tự biết file nào dùng. Có thể chạy lại từng bước."""
import argparse, glob, json, math, os, re, shutil, subprocess, sys

# Windows/console không phải UTF-8 → tự chạy lại với -X utf8 (tiếng Việt, ✓ ❌ không làm vỡ chương trình);
# PYTHONUTF8=1 để mọi script con cũng UTF-8.
os.environ.setdefault('PYTHONUTF8', '1')
if not sys.flags.utf8_mode and not os.environ.get('_VC_REEXEC'):
    os.environ['_VC_REEXEC'] = '1'
    sys.exit(subprocess.call([sys.executable, '-X', 'utf8', os.path.abspath(__file__), *sys.argv[1:]]))

VC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(VC, 'scripts')
PY = [sys.executable, '-X', 'utf8']
NODE_DIR = os.path.join(os.path.expanduser('~'), '.vucut', 'node')   # thư viện bản đồ (setup --maps)


def run(cmd, **k):
    print('»', ' '.join(map(str, cmd))[:300], flush=True)
    return subprocess.run(list(map(str, cmd)), check=True, **k)


def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def state(da, **upd):
    p = os.path.join(da, 'state.json')
    s = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    if upd:
        s.update(upd); json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return s


# ---------------------------------------------------------------- setup
PW_VER = '1.55.0'   # phiên bản playwright đã kiểm thử; cài riêng vào ~/.vucut/node, không đụng cài global


def _ver(cmd, rx):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        m = re.search(rx, out); return tuple(int(x) for x in m.groups()) if m else None
    except Exception: return None


def cmd_setup(a):
    win = sys.platform == 'win32'
    ok = True
    # 1 · Python
    if sys.version_info < (3, 10):
        print(f'❌ Python {sys.version.split()[0]} quá cũ → cài Python 3.10–3.13'); ok = False
    else: print(f'✅ Python {sys.version.split()[0]}')
    # 2 · thư viện Python (khoá phiên bản trong requirements.txt)
    req = os.path.join(VC, 'requirements.txt')
    need = {'numpy': 'numpy', 'PIL': 'Pillow', 'scipy': 'scipy', 'faster_whisper': 'faster-whisper', 'cv2': 'opencv-python-headless'}
    if a.rembg: need['rembg'] = 'rembg'
    miss = []
    for mod in need:
        try: __import__(mod)
        except ImportError: miss.append(mod)
    if miss:
        extra = ['--break-system-packages'] if sys.platform.startswith('linux') else []
        try:
            run([sys.executable, '-m', 'pip', 'install', '-q', '-r', req, *extra])
            if a.rembg: run([sys.executable, '-m', 'pip', 'install', '-q', 'rembg[cpu]>=2.0.60,<3', *extra])
        except subprocess.CalledProcessError: print('❌ pip cài lỗi — xem INSTALL.md mục Lỗi thường gặp'); ok = False
    for mod, pkg in need.items():
        try: __import__(mod); print('✅', pkg)
        except ImportError: print('❌ THIẾU', pkg); ok = False
    # 3 · ffmpeg / node
    fv = _ver(['ffmpeg', '-version'], r'version n?(\d+)\.(\d+)') if shutil.which('ffmpeg') else None
    if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
        print('❌ THIẾU ffmpeg/ffprobe trong PATH → Windows: winget install Gyan.FFmpeg · macOS: brew install ffmpeg'); ok = False
    else: print('✅ ffmpeg', '.'.join(map(str, fv)) if fv else '(bản build riêng)')
    nv = _ver(['node', '-v'], r'v(\d+)\.(\d+)') if shutil.which('node') else None
    if not nv or nv[0] < 18:
        print('❌ THIẾU Node.js ≥ 18 → https://nodejs.org (bản LTS) rồi mở lại terminal'); ok = False
    else:
        print(f'✅ Node {nv[0]}.{nv[1]}')
        # 4 · playwright + Chromium vào ~/.vucut/node (không cần npm -g, không cần NODE_PATH)
        os.makedirs(NODE_DIR, exist_ok=True)
        chk = lambda: subprocess.run(['node', os.path.join(SCR, 'preview.mjs'), '--check'], capture_output=True, text=True)
        r = chk()
        if 'ok' not in r.stdout:
            pkgs = [f'playwright@{PW_VER}'] + (['world-atlas@2.0.2', 'topojson-client@3.1.0', 'd3-geo@3.1.0'] if a.maps else [])
            try:
                run(['npm', 'i', '--no-audit', '--no-fund', '--prefix', NODE_DIR, *pkgs], shell=win)
                run(['node', os.path.join(NODE_DIR, 'node_modules', 'playwright', 'cli.js'), 'install', 'chromium'])
            except subprocess.CalledProcessError: pass
            r = chk()
        elif a.maps:
            run(['npm', 'i', '--no-audit', '--no-fund', '--prefix', NODE_DIR, 'world-atlas@2.0.2', 'topojson-client@3.1.0', 'd3-geo@3.1.0'], shell=win)
        if 'ok' in r.stdout: print('✅ playwright + Chromium (render)')
        else: print('❌ playwright/Chromium chưa chạy được:', (r.stderr or r.stdout).strip()[:200]); ok = False
    # 5 · mô hình (tải 1 lần → các lần sau chạy offline)
    if not a.no_models:
        try:
            from faster_whisper import WhisperModel
            print(f'» tải sẵn mô hình phiên âm Whisper "{a.model}" (~{ {"small": 470, "medium": 1500}.get(a.model, "?") } MB, 1 lần)…', flush=True)
            WhisperModel(a.model, device='cpu', compute_type='int8'); print(f'✅ Whisper {a.model}')
        except Exception as e: print('❌ chưa tải được Whisper (cần mạng lần đầu):', e); ok = False
        if a.rembg:
            try:
                from rembg import new_session
                print('» tải sẵn mô hình tách nền u2net_human_seg (~176 MB, 1 lần)…', flush=True)
                new_session('u2net_human_seg'); print('✅ rembg u2net_human_seg')
            except Exception as e: print('❌ chưa tải được mô hình tách nền:', e); ok = False
    print('✅ font + GSAP + mô hình dò mặt đã có sẵn trong skill (assets/).')
    hist = os.environ.get('VUCUT_HISTORY')
    print('· lịch sử chống lặp:', hist or os.path.join(os.path.expanduser('~'), '.vucut', 'history.json'),
          '' if hist else '(nhiều máy cùng kênh → đặt VUCUT_HISTORY vào thư mục dùng chung, xem INSTALL.md)')
    print('\n🎉 SẴN SÀNG — chạy được vucut.' if ok else '\n⚠ Còn mục ❌ ở trên — sửa rồi chạy lại setup.')
    if not ok: sys.exit(1)


# ---------------------------------------------------------------- prep
def cmd_prep(a):
    os.makedirs(a.da, exist_ok=True)
    src = os.path.join(a.da, 'source.mp4')
    sp = round(a.speed, 3)
    if os.path.exists(src) and not a.force and state(a.da).get('speed', 1.0) != sp:
        sys.exit(f"❌ source.mp4 đã làm với tốc độ ×{state(a.da).get('speed', 1.0)} ≠ ×{sp} → chạy lại prep với --force")
    fresh = not os.path.exists(src) or a.force
    if fresh:
        # TĂNG TỐC ngay từ đầu (mặc định ×1.1): mọi bước sau (phiên âm, autocut, mốc giây, âm thanh) đều theo video đã tăng tốc.
        # atempo giữ nguyên cao độ giọng; --clip tính theo giây video GỐC.
        cmd = ['ffmpeg', '-v', 'error', '-y']
        if a.clip:
            s, e = a.clip.split('-'); cmd += ['-ss', s, '-to', e]
        cmd += ['-i', a.video]
        if sp != 1: cmd += ['-vf', f'setpts=PTS/{sp}', '-af', f'atempo={sp}']
        cmd += ['-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '256k', src]
        run(cmd)
        print(f'✅ source.mp4 · tốc độ ×{sp} · dài {dur(src):.2f} s')
    words = os.path.join(a.da, 'words.json')
    if not os.path.exists(words) or fresh:
        run([*PY, os.path.join(SCR, 'transcribe.py'), src, words, '--model', a.model])
    state(a.da, source=src, words=words, crop_x=a.crop_x, speed=sp)
    run([*PY, os.path.join(SCR, 'autocut.py'), src, words, os.path.join(a.da, 'cut'), '--dry'])
    print('\n→ Sửa tay chính tả/tên riêng trong words.json nếu cần, soát bảng ĐOẠN BỎ, rồi: vucut.py cut', a.da,
          '[--keep a-b] [--drop a-b]')


# ---------------------------------------------------------------- cut
def cmd_cut(a):
    s = state(a.da); src, words = s['source'], s['words']
    base_v, base_w = src, words
    if not a.no_autocut:
        cmd = [*PY, os.path.join(SCR, 'autocut.py'), src, words, os.path.join(a.da, 'cut')]
        if a.keep: cmd += ['--keep', a.keep]
        if a.drop: cmd += ['--drop', a.drop]
        run(cmd)
        base_v, base_w = os.path.join(a.da, 'cut', 'cut.mp4'), os.path.join(a.da, 'cut', 'words_cut.json')
    fin_v, fin_w, mp = base_v, base_w, None
    if not a.no_tighten:
        run([*PY, os.path.join(SCR, 'tighten.py'), base_v, base_w, os.path.join(a.da, 'cut2')])
        fin_v, fin_w, mp = (os.path.join(a.da, 'cut2', x) for x in ('cut.mp4', 'words_cut.json', 'map.json'))
    # khung người nói (từ video CUỐI); gốc ngang → cắt dọc quanh mặt
    fr = os.path.join(a.da, 'frames'); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                    '-of', 'csv=p=0', fin_v], capture_output=True, text=True).stdout.strip().split(',')[:2])
    # khung người nói ở độ phân giải BẢN CUỐI (1080×1920) để mặt không bị phóng từ 720p khi render
    fh = a.frames_h; fw = fh * 9 // 16
    ft = os.path.join(a.da, 'facetrack.json')
    run([*PY, os.path.join(SCR, 'facetrack.py'), fin_v, ft])
    track = json.load(open(ft, encoding='utf-8')); face = track['face']
    vf = 'fps=30,'
    if w / h > 9 / 16 + .01:
        cx = s.get('crop_x')
        if cx is not None:      # người dùng ép tâm cố định
            vf += f'crop=ih*9/16:ih:max(0\\,min(iw-ih*9/16\\,iw*{cx}-ih*9/32)):0,'
        else:                   # bám mặt: đổi x của crop theo từng khung (sendcmd)
            with open(os.path.join(a.da, 'crop_cmds.txt'), 'w', encoding='utf-8') as f:
                for k, x in enumerate(track['x']): f.write(f"{k / 30:.4f} crop x {int(x)};\n")
            x0 = int(track['x'][0]) if track['x'] else 0
            vf += f"sendcmd=f=crop_cmds.txt,crop={track['crop_w']}:ih:{x0}:0,"
    run(['ffmpeg', '-v', 'error', '-y', '-i', fin_v, '-vf', vf + f'scale={fw}:{fh}:flags=lanczos', '-q:v', '2', '-qmin', '1',
         os.path.join(fr, '%05d.jpg')], cwd=a.da)
    # build/lib
    lib = os.path.join(a.da, 'build', 'lib'); os.makedirs(lib, exist_ok=True)
    for f in ('vucut.css', 'vucut.js', 'gsap.min.js'): shutil.copy(os.path.join(VC, 'assets', f), lib)
    shutil.copytree(os.path.join(VC, 'assets', 'fonts'), os.path.join(lib, 'fonts'), dirs_exist_ok=True)
    T = round(dur(base_v), 3)
    state(a.da, video=fin_v, words_final=fin_w, base=base_v, base_words=base_w, map=mp, T=T, face=face)
    cj = os.path.join(a.da, 'cut', 'cut.json')
    cuts = json.load(open(cj, encoding='utf-8'))['cuts_new'] if os.path.exists(cj) and not a.no_autocut else []
    print(f'\n✅ Sẵn sàng viết SHOTBOOK. Mốc từng từ: {base_w} (giây của {base_v}).')
    print(f'   Mối nối cần phủ (giây {os.path.basename(os.path.dirname(base_v)) or "gốc"}): {cuts}')
    print('   Đầu build.py:')
    print(f"     import sys; sys.path.insert(0, r'{SCR}')\n     import vc_build as V, cine as C, vc as P, mg_real as R   (dựng qua vc.py build)")
    print(f"     V.init(T={T}" + (f", tighten=r'{mp}'" if mp else '') + f", face=({face[0]}, {face[1]}), head=r'{ft}', kind='phantich')   # kind: 'tin' | 'phantich' | 'nhandinh' · head = đỉnh đầu (SPLIT tự né)")
    print(f"   Bước tiếp: vucut.py beats {a.da}  → BẢNG NHỊP cho SHOTBOOK")
    print(f"     ... V.audio(impacts=[...], muffle=[(a,b)], duck=[t])")
    print(f"     V.finish(r'{os.path.join(a.da, 'build', 'master.html')}', r'{os.path.join(a.da, 'cues.json')}', "
          f"shell=r'{os.path.join(VC, 'assets', 'template', 'vucut_9x16_v4.html')}')")


# ---------------------------------------------------------------- beats
def cmd_beats(a):
    s = state(a.da)
    if 'base' not in s: sys.exit('❌ chưa chạy cut')
    run([*PY, os.path.join(SCR, 'beats.py'), s['base'], s['base_words'], os.path.join(a.da, 'beats.json')])


# ---------------------------------------------------------------- split
def cmd_split(a):
    rg = a.ranges or ','.join(f'{x}-{y}' for x, y in json.load(open(os.path.join(a.da, 'splits.json'))))   # bỏ trống = đọc splits.json do build ghi
    run([*PY, os.path.join(SCR, 'matte_split.py'), os.path.join(a.da, 'frames'), os.path.join(a.da, 'build', 'cut'), 30,
         rg, '--jobs', a.jobs])


# ---------------------------------------------------------------- audio
def cmd_audio(a):
    s = state(a.da); v = s['video']; d = a.da
    j = lambda *x: os.path.join(d, *x)
    sfx = j('sfx')
    if not os.path.exists(os.path.join(sfx, 'wash.wav')): run([*PY, os.path.join(SCR, 'make_sfx.py'), sfx])
    dn = f'afftdn=nr={a.denoise}:nf=-38:tn=1,' if a.denoise > 0 else ''      # lọc ồn nền (quạt, điều hoà, xì) — theo dõi nhiễu
    run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-vn', '-af',
         f'highpass=f=80,{dn}lowpass=f=15000,equalizer=f=250:t=q:w=1.2:g=-2,'      # bớt ù phòng
         'acompressor=threshold=0.1:ratio=2.5:attack=15:release=220,aresample=48000', '-ac', '1', j('voice.wav')])
    run([*PY, os.path.join(SCR, 'sfx_thin.py'), j('cues.json'), j('cues_lite.json')])
    run([*PY, os.path.join(SCR, 'sfx_mix.py'), j('voice.wav'), j('cues_lite.json'), sfx, j('voice_sfx.m4a'), '--sfx-db', '0'])
    # 27/11/2026: nhạc nền do vc.py (_remix) trộn — bản 'tin' duy nhất; ở đây chỉ chuẩn hoá giọng + SFX
    loudnorm(j('voice_sfx.m4a'), j('final_audio.m4a'), a.lufs)


def loudnorm(src, dst, I=-14.0, TP=-1.5, LRA=11):
    """chuẩn hoá độ to 2 lượt (EBU R128): đo → áp tuyến tính → mọi video cùng độ to (TikTok/Reels ≈ −14 LUFS)"""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-af', f'loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-c:a', 'aac', '-b:a', '256k', dst])
    print(f"→ {dst} · độ to {m['input_i']} → {I} LUFS")


# ---------------------------------------------------------------- probe
def master_T(da):
    html = open(os.path.join(da, 'build', 'master.html'), encoding='utf-8').read()
    return float(re.search(r'data-duration="([\d.]+)"', html).group(1))


def cmd_probe(a):
    s = state(a.da); ts = [float(x) for x in a.times.split(',') if x] if a.times else []
    if a.scan: ts += [k / 2 + .25 for k in range(int(master_T(a.da) * 2))]   # quét mỗi 0.5 s: soát chữ tràn / xuống dòng
    if a.cuts:   # mối nối autocut ± 0.1 s, dời sang giây video cuối
        cj = os.path.join(a.da, 'cut', 'cut.json')
        if s.get('base', '').endswith(os.path.join('cut', 'cut.mp4')) and os.path.exists(cj):
            rm = json.load(open(s['map'], encoding='utf-8'))['removed'] if s.get('map') else []
            M = lambda t: t - sum((e - b) if t >= e else max(0, t - b) for b, e in rm)
            for c in json.load(open(cj, encoding='utf-8')).get('cuts_new', []): ts += [round(M(c) - .1, 2), round(M(c) + .1, 2)]
        else:
            print('ℹ --cuts: không có mối nối autocut (đã chạy cut --no-autocut) → bỏ qua')
    ts = sorted(set(round(t, 2) for t in ts if 0 <= t < master_T(a.da)))
    if not ts: sys.exit('❌ probe: không có mốc nào — truyền danh sách giây, vd 0.5,3,8')
    q = os.path.join(a.da, 'qc'); shutil.rmtree(q, ignore_errors=True)
    run(['node', os.path.join(SCR, 'preview.mjs'), os.path.join(a.da, 'build'), os.path.join(a.da, 'frames'), 30, 'probe',
         ','.join(map(str, ts)), q])
    from PIL import Image, ImageDraw
    ims = sorted(glob.glob(os.path.join(q, 't_*.png')), key=lambda p: float(p.split('t_')[1][:-4]))
    cols = min(6, len(ims)); rows = math.ceil(len(ims) / cols); W, H = 240, 427
    sh = Image.new('RGB', (cols * W, rows * (H + 22)), '#222'); dr = ImageDraw.Draw(sh)
    for k, p in enumerate(ims):
        x, y = (k % cols) * W, (k // cols) * (H + 22)
        sh.paste(Image.open(p).convert('RGB').resize((W, H)), (x, y + 22)); dr.text((x + 6, y + 5), p.split('t_')[1][:-4] + ' s', fill='#fff')
    sh.save(os.path.join(q, 'sheet.jpg'), quality=85)
    empty_bands(ims)
    print('→ tự xem:', os.path.join(q, 'sheet.jpg'))


def empty_bands(ims, lim=.30):
    """⚠ khung TRỐNG: dải ngang liền ≥ 30 % chiều cao gần như một màu (vd bản đồ toàn khung để trống nửa dưới).
    Chỉ báo khi ≥ 2 mốc liền nhau cùng trống (bỏ qua khung chuyển cảnh)."""
    import numpy as np
    from PIL import Image, ImageFilter
    hits = []
    for p in ims:
        a = np.asarray(Image.open(p).convert('L').resize((180, 320)).filter(ImageFilter.BoxBlur(2)), float)
        best = cur = st = 0
        for k, flat in enumerate(a.std(1) < 5):
            cur = cur + 1 if flat else 0
            if cur > best: best, st = cur, k - cur + 1
        hits.append((float(p.split('t_')[1][:-4]), best / 320, st / 320))
    runs, run = [], []
    for h in hits:
        if h[1] >= lim: run.append(h)
        else:
            if len(run) >= 2: runs.append(run)
            run = []
    if len(run) >= 2: runs.append(run)
    for r in runs:
        b = max(r, key=lambda h: h[1]); where = 'nửa dưới' if b[2] > .4 else ('nửa trên' if b[2] + b[1] < .6 else 'giữa khung')
        print(f'⚠ KHUNG TRỐNG {r[0][0]:.2f}–{r[-1][0]:.2f} s: {where} trống {b[1]:.0%} chiều cao → thêm nội dung '
              f'(dlmap facts=…, V.mix, ô số) hoặc đổi sang half=True + V.L_split')
    if not runs: print('✅ không có khung trống nửa khung')


# ---------------------------------------------------------------- render
def cmd_render(a):
    s = state(a.da); T = master_T(a.da); total = math.floor(T * 30)
    mh = open(os.path.join(a.da, 'build', 'master.html'), encoding='utf-8').read()
    cutd = os.path.join(a.da, 'build', 'cut')
    sj = os.path.join(a.da, 'splits.json'); rg = json.load(open(sj)) if os.path.exists(sj) else []
    if rg and not (os.path.isdir(cutd) and os.listdir(cutd)):   # ĐẦU NỔI cần tách nền → tự chạy
        try:
            import rembg  # noqa
        except ImportError:
            sys.exit('❌ cảnh SPLIT đầu nổi cần tách nền nhưng chưa có rembg → chạy `vucut.py setup --rembg` rồi render lại '
                     '(hoặc V.L_split(..., float_=False) để không nổi).')
        print('… tách nền đầu nổi cho', len(rg), 'cảnh SPLIT')
        run([*PY, os.path.join(SCR, 'matte_split.py'), os.path.join(a.da, 'frames'), cutd, '30', ','.join(f'{x}-{y}' for x, y in rg), '--jobs', '2'])
    scale = 1 if a.draft else a.scale
    out = os.path.join(a.da, 'out_frames'); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    n = max(1, a.jobs); step = math.ceil(total / n); ps = []
    for k in range(n):
        i0, i1 = k * step, min(total, (k + 1) * step)
        if i0 >= i1: break
        ps.append(subprocess.Popen(['node', os.path.join(SCR, 'preview.mjs'), os.path.join(a.da, 'build'), os.path.join(a.da, 'frames'),
                                    '30', 'full', out, str(scale), str(i0), str(i1)]))
    if any(p.wait() for p in ps): sys.exit('❌ render lỗi')
    aud = os.path.join(a.da, 'final_audio.m4a')
    if not os.path.exists(aud): aud = s['video']; print('⚠ chưa có final_audio.m4a → dùng tiếng gốc')
    k = 1
    while os.path.exists(os.path.join(a.da, f'out_v{k}{"_draft" if a.draft else ""}.mp4')): k += 1
    mp4 = os.path.join(a.da, f'out_v{k}{"_draft" if a.draft else ""}.mp4')
    q = ['-crf', '23', '-preset', 'veryfast'] if a.draft else ['-crf', '17', '-preset', 'slow']
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(out, '%05d.png'), '-i', aud, '-map', '0:v', '-map', '1:a',
         '-c:v', 'libx264', *q, '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', mp4])
    if not a.keep_frames: shutil.rmtree(out, ignore_errors=True)
    print('✅', mp4)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('setup'); p.add_argument('--rembg', action='store_true'); p.add_argument('--maps', action='store_true')
    p.add_argument('--model', default='medium', help='mô hình Whisper tải sẵn (trùng với prep --model)'); p.add_argument('--no-models', action='store_true')
    p = sp.add_parser('prep'); p.add_argument('video'); p.add_argument('da'); p.add_argument('--clip'); p.add_argument('--model', default='medium')
    p.add_argument('--speed', type=float, default=1.1, help='tốc độ so với video gốc (mặc định 1.1 · 1 = giữ nguyên)')
    p.add_argument('--crop-x', type=float, default=None, help='gốc ngang: ép tâm khung cố định (0–1); bỏ trống = tự bám mặt'); p.add_argument('--force', action='store_true')
    p = sp.add_parser('cut'); p.add_argument('da'); p.add_argument('--keep', default=''); p.add_argument('--drop', default='')
    p.add_argument('--no-autocut', action='store_true'); p.add_argument('--no-tighten', action='store_true')
    p.add_argument('--frames-h', type=int, default=1920, help='chiều cao khung người nói (1920 = nét ở bản cuối; 1280 = nhẹ máy)')
    p = sp.add_parser('beats'); p.add_argument('da')
    p = sp.add_parser('split'); p.add_argument('da'); p.add_argument('ranges', nargs='?', default=''); p.add_argument('--jobs', type=int, default=2)
    p = sp.add_parser('audio'); p.add_argument('da'); p.add_argument('--no-music', action='store_true')
    p.add_argument('--denoise', type=float, default=12, help='mức lọc ồn dB (0 = tắt; phòng ồn 18–24)'); p.add_argument('--lufs', type=float, default=-14)
    p = sp.add_parser('probe'); p.add_argument('da'); p.add_argument('times', nargs='?', default=''); p.add_argument('--cuts', action='store_true'); p.add_argument('--scan', action='store_true', help='quét cả video mỗi 0.5 s, in ⚠ chữ tràn mép / từ to xuống dòng')
    p = sp.add_parser('render'); p.add_argument('da'); p.add_argument('--draft', action='store_true'); p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--scale', type=float, default=1.5); p.add_argument('--keep-frames', action='store_true')
    a = ap.parse_args()
    if hasattr(a, 'da'): a.da = os.path.abspath(a.da)
    globals()['cmd_' + a.cmd](a)


if __name__ == '__main__':
    main()
