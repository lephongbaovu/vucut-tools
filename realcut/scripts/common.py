"""realcut · tiện ích dùng chung (đường dẫn, ffprobe, ffmpeg đọc/ghi khung, bảng màu, font)."""
import json, os, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ASSETS = os.path.join(SKILL, 'assets')
FONTS = os.path.join(ASSETS, 'fonts')
MODELS = os.path.join(ASSETS, 'models')
REF = os.path.join(SKILL, 'reference')

# ── Bảng màu "sáng ấm + vàng đồng" (đổi tông: sửa ở đây hoặc khoá "palette" trong edit.json) ──
PALETTE = {
    'gold':      (201, 162, 106),   # vàng đồng chính  #C9A26A
    'gold_hi':   (236, 214, 170),   # vàng sáng (đỉnh gradient) #ECD6AA
    'gold_lo':   (150, 112, 62),    # vàng tối (đáy gradient)   #96703E
    'cream':     (247, 241, 231),   # chữ kem  #F7F1E7
    'ink':       (38, 31, 26),      # nâu đen  #261F1A
    'wood':      (92, 66, 45),      # nâu gỗ   #5C422D
    'white':     (255, 255, 255),
}

FONT_FILES = {
    'serif':        'PlayfairDisplay-Regular.ttf',
    'serif_bold':   'PlayfairDisplay-Bold.ttf',
    'serif_italic': 'PlayfairDisplay-Italic.ttf',
    'thin':         'BeVietnamPro-ExtraLight.ttf',
    'light':        'BeVietnamPro-Light.ttf',
    'medium':       'BeVietnamPro-Medium.ttf',
    'bold':         'BeVietnamPro-Bold.ttf',
    'black':        'BeVietnamPro-ExtraBold.ttf',
    'serif_black':  'PlayfairDisplay_900Black.ttf',
    'serif_xb':     'PlayfairDisplay_800ExtraBold.ttf',
    'serif_xbi':    'PlayfairDisplay_800ExtraBold_Italic.ttf',
    'semibold':     'BeVietnamPro_600SemiBold.ttf',
    'medium_italic': 'BeVietnamPro_500Medium_Italic.ttf',
    'light_italic': 'BeVietnamPro_300Light_Italic.ttf',
}

def font_path(key):
    return os.path.join(FONTS, FONT_FILES.get(key, key))

def die(msg):
    print('✖ ' + msg, file=sys.stderr); sys.exit(1)

def need(binary):
    if not shutil.which(binary):
        die(f'Thiếu {binary}. Cài ffmpeg (có ffprobe) rồi chạy lại.')

def run(cmd, **kw):
    kw.setdefault('check', True)
    return subprocess.run(cmd, **kw)

def probe(path):
    """→ dict(w, h, fps, dur, has_audio, rotation)"""
    need('ffprobe')
    out = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next((s for s in j['streams'] if s['codec_type'] == 'video'), None)
    a = any(s['codec_type'] == 'audio' for s in j['streams'])
    if v is None:
        die(f'{path}: không có hình')
    num, den = (v.get('avg_frame_rate') or v.get('r_frame_rate') or '30/1').split('/')
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    rot = 0
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd:
            rot = int(sd['rotation'])
    rot = int(v.get('tags', {}).get('rotate', rot))
    w, h = int(v['width']), int(v['height'])
    if abs(rot) in (90, 270):
        w, h = h, w
    dur = float(j['format'].get('duration') or v.get('duration') or 0)
    return dict(w=w, h=h, fps=fps, dur=dur, has_audio=a, rotation=rot)

def out_size(ratio, draft=False):
    W, H = (1080, 1920) if ratio == '9:16' else (1920, 1080)
    if draft:
        W, H = W // 2, H // 2
    return W, H

class Reader:
    """Đọc khung tuần tự qua ffmpeg (rgb24) — vf tuỳ chọn, ss = giây bắt đầu."""
    def __init__(self, path, w, h, ss=0.0, vf=None, fps=None, gray=False):
        self.w, self.h, self.gray = w, h, gray
        self.ch = 1 if gray else 3
        filt = []
        if fps:
            filt.append(f'fps={fps}')
        if vf:
            filt.append(vf)
        filt.append(f'scale={w}:{h}:flags=bicubic')
        cmd = ['ffmpeg', '-nostdin', '-v', 'error']
        if ss > 0:
            cmd += ['-ss', f'{ss:.3f}']
        cmd += ['-i', path, '-an', '-vf', ','.join(filt), '-f', 'rawvideo',
                '-pix_fmt', 'gray' if gray else 'rgb24', '-']
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.n = w * h * self.ch
        self.last = None
        self.eof = False

    def read(self):
        import numpy as np
        buf = self.p.stdout.read(self.n) if self.p else b''
        if len(buf) < self.n:
            self.eof = True
            return self.last  # hết clip → giữ khung cuối
        a = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, self.ch)
        if self.gray:
            a = a[:, :, 0]
        self.last = a
        return a

    def close(self):
        if self.p:
            try:
                self.p.stdout.close(); self.p.kill(); self.p.wait()
            except Exception:
                pass
            self.p = None

class Writer:
    def __init__(self, path, w, h, fps, crf=18, preset='medium', audio=None):
        cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{w}x{h}', '-r', str(fps), '-i', '-']
        if audio:
            cmd += ['-i', audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest']
        cmd += ['-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame):
        self.p.stdin.write(frame.tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()

def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def save_json(p, obj):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
