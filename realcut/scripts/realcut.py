"""realcut · video review BĐS (dự án · đất nền · nhà phố) — điều phối 3 tầng: NỀN (base) → CHỮ & HIỆU ỨNG (fx) → ÂM THANH (mix).
Lệnh (DA = thư mục dự án):
  setup [--model medium]                  kiểm tra + cài thư viện, mô hình
  aroll OUT.mp4 clip1 clip2[@a-b] … [--speed 1.1]   ghép nhiều clip người nói + tăng tốc (không lệch tiếng)
  prep  AROLL.mp4 DA [--model medium] [--clip a-b]  phiên âm → cắt lặng → cắt khung 9:16 bám người → matte
  broll THU_MUC DA [--mode auto|crop|blur]          chuẩn hoá B-roll 9:16 (DA/broll_916) + bảng ảnh chỉ mục
  fix   DA "sai=>đúng" …                  sửa chữ nghe sai (giữ mốc)
  cut   AROLL.mp4 DA [--keep a-b] [--drop a-b]      cắt lại (giây GỐC) khi cắt nhầm/sót
  phrases DA                              lời theo cụm + giây cut → viết edit.json + ads.json
  base  DA [--draft] [--sheet 1.0]        tầng A: nền A-roll + B-roll → DA/base.mp4
  fx    DA [--frames a,b] [--sheet .5] [--guides]   tầng B: chữ/hiệu ứng → DA/fx.mp4 (hoặc ảnh thử)
  qc    DA                                tự soát: vùng an toàn, đè đầu, thời gian đọc, nhịp, mở đầu
  mix   DA                                tầng C: âm thanh → DA/final.mp4
  all   DA                                base → fx → qc → mix
"""
import os, re, subprocess, sys

os.environ.setdefault('PYTHONUTF8', '1')
if not sys.flags.utf8_mode and not os.environ.get('_VC_REEXEC'):
    os.environ['_VC_REEXEC'] = '1'
    sys.exit(subprocess.call([sys.executable, '-X', 'utf8', os.path.abspath(__file__), *sys.argv[1:]]))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import load_json, save_json, probe, MODELS, die

PY = sys.executable

def sh(script, *args):
    r = subprocess.run([PY, os.path.join(HERE, script)] + list(args))
    if r.returncode:
        sys.exit(r.returncode)

def take(args, flag, default=None, is_bool=False):
    if flag in args:
        i = args.index(flag)
        if is_bool:
            args.pop(i); return True
        v = args[i + 1]; del args[i:i + 2]; return v
    return default

STAMP = os.path.join(os.path.expanduser('~'), '.realcut_ready')

def setup():
    import shutil, importlib, importlib.util
    if os.path.exists(STAMP) and '--force' not in sys.argv:
        print('✓ realcut đã sẵn sàng (chạy lại kiểm tra: setup --force)'); return
    ok = True
    if sys.version_info < (3, 10):
        print(f'✖ Python {sys.version.split()[0]} quá cũ → cài Python 3.10–3.13'); ok = False
    else: print(f'✓ Python {sys.version.split()[0]}')
    for b in ('ffmpeg', 'ffprobe'):
        print(('✓ ' if shutil.which(b) else '✖ ') + b); ok &= bool(shutil.which(b))
    if not shutil.which('ffmpeg'):
        print('  → Windows: winget install Gyan.FFmpeg · macOS: brew install ffmpeg · rồi mở lại terminal')
    pk = [('numpy', 'numpy'), ('cv2', 'opencv-python-headless'), ('PIL', 'Pillow'), ('onnxruntime', 'onnxruntime'),
          ('faster_whisper', 'faster-whisper'), ('scipy', 'scipy')]
    miss = [p for m, p in pk if importlib.util.find_spec(m) is None]
    if miss:
        print('· cài', ' '.join(miss))
        req = os.path.join(os.path.dirname(HERE), 'requirements.txt')
        r = subprocess.run([PY, '-m', 'pip', 'install', '-q', '--disable-pip-version-check', '-r', req]
                           + (['--break-system-packages', '--root-user-action=ignore'] if sys.platform.startswith('linux') else []),
                           capture_output=True, text=True)
        if r.returncode: print((r.stderr or r.stdout)[-800:])
        importlib.invalidate_caches()
    for m, p in pk:
        f = importlib.util.find_spec(m) is not None
        print(('✓ ' if f else '✖ ') + p)
        ok &= f
    mp = os.path.join(MODELS, 'rvm_mobilenetv3_fp32.onnx')
    if not os.path.exists(mp):
        url = 'https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx'
        print('· tải mô hình tách người …')
        try:
            import urllib.request; os.makedirs(MODELS, exist_ok=True); urllib.request.urlretrieve(url, mp + '.part'); os.replace(mp + '.part', mp)
        except Exception as e: print('  lỗi tải:', e)
    print(('✓ ' if os.path.exists(mp) else '✖ ') + 'mô hình tách người RVM'); ok &= os.path.exists(mp)
    model = take(sys.argv, '--model', None)
    if model and '--no-models' not in sys.argv:
        try:
            from faster_whisper import WhisperModel
            print(f'» tải sẵn mô hình phiên âm Whisper "{model}" (1 lần)…', flush=True)
            WhisperModel(model, device='cpu', compute_type='int8'); print(f'✓ Whisper {model}')
        except Exception as e: print('✖ chưa tải được Whisper (cần mạng lần đầu):', e); ok = False
    else:
        print('· Whisper tự tải lần phiên âm đầu (medium ~1.5 GB, small ~0.5 GB) — tải trước: realcut.py setup --model medium')
    print('\n🎉 SẴN SÀNG — chạy được realcut.' if ok else '\n⚠ Còn mục ✖ ở trên — sửa rồi chạy lại setup.')
    if not ok: sys.exit(1)
    open(STAMP, 'w').write('ok\n')

def fix(da, pairs):
    n = 0
    for fn in ('words.json', 'words_cut.json'):
        p = os.path.join(da, fn); j = load_json(p)
        if not j:
            continue
        ws = j['words']
        for pair in pairs:
            wrong, right = pair.split('=>')
            wt = wrong.strip().lower().split(); rt = right.strip().split(); k = len(wt)
            i = 0
            while i <= len(ws) - k:
                seg = [re.sub(r'[^\w\']', '', w['w'].lower()) for w in ws[i:i + k]]
                if seg == [re.sub(r'[^\w\']', '', x) for x in wt]:
                    trail = re.sub(r'^.*?([.,!?;:…]*)$', r'\1', ws[i + k - 1]['w'])
                    if len(rt) == k:
                        for j2 in range(k):
                            ws[i + j2]['w'] = rt[j2]
                    else:
                        ws[i]['w'] = ' '.join(rt); ws[i]['e'] = ws[i + k - 1]['e']; del ws[i + 1:i + k]; k_ = 1
                        ws[i]['w'] += trail; n += 1; i += 1; continue
                    ws[i + k - 1]['w'] += trail; n += 1
                i += 1
        save_json(p, j)
    print(f'✓ sửa {n} chỗ (words.json + words_cut.json). Lỗi hay gặp → thêm vào DA/sua_chinh_ta.tsv cho lần sau.')

def phrases(da):
    ws = load_json(os.path.join(da, 'words_cut.json'))
    if not ws: die('Chưa có words_cut.json — chạy prep')
    groups, cur = [], []
    for w in ws['words']:
        if cur and (w['s'] - cur[-1]['e'] > 0.35 or cur[-1]['w'].endswith(('.', ',', '?', '!')) or len(cur) >= 9):
            groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    print(f'Tổng {ws["dur"]:.2f}s · {len(groups)} cụm (giây cut.mp4 — dùng cho edit.json + ads.json)')
    for g in groups:
        print(f'{g[0]["s"]:6.2f}–{g[-1]["e"]:6.2f}  ' + ' '.join(f'{w["w"]}' for w in g))

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__); return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'setup': setup()
    elif cmd == 'aroll': sh('aroll.py', *args)
    elif cmd == 'prep':
        src, da = args[0], args[1]; rest = args[2:]
        os.makedirs(da, exist_ok=True)
        model = take(rest, '--model'); clip = take(rest, '--clip')
        sh('transcribe.py', src, da, *((['--model', model] if model else []) + (['--clip', clip] if clip else [])))
        sh('autocut.py', src, da, '--ratio', '9:16', *((['--clip', clip] if clip else []) + rest))
        sh('matte.py', os.path.join(da, 'cut.mp4'), da)
        print('\n→ Tiếp: `fix` chữ sai · `phrases` · `broll` · viết edit.json + ads.json (reference/schema.md)')
    elif cmd == 'cut': sh('autocut.py', args[0], args[1], '--ratio', '9:16', *args[2:]); sh('matte.py', os.path.join(args[1], 'cut.mp4'), args[1])
    elif cmd == 'broll':
        src, da = args[0], args[1]; out = os.path.join(da, 'broll_916')
        sh('prep_broll.py', src, out, *args[2:]); sh('broll_index.py', out, da)
    elif cmd == 'fix': fix(args[0], args[1:])
    elif cmd == 'phrases': phrases(args[0])
    elif cmd == 'base': sh('base.py', *args)
    elif cmd == 'fx': sh('adsfx.py', *args)
    elif cmd == 'qc': sh('qc.py', *args)
    elif cmd == 'mix': sh('mix.py', *args)
    elif cmd == 'all':
        da = args[0]
        sh('base.py', da); sh('adsfx.py', da); sh('qc.py', da, '--step', '0.5'); sh('mix.py', da)
        print(f'\n🎬 Xong: {os.path.join(da, "final.mp4")} — đọc qc/qc_report.txt trước khi giao.')
    else: die(f'Lệnh lạ: {cmd}\n' + __doc__)

if __name__ == '__main__':
    main()
