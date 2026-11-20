"""Tách người khỏi nền (Robust Video Matting, ONNX, chạy CPU) → matte.mp4 (xám, nửa độ phân giải) + head.json
Dùng cho hiệu ứng CHỮ SAU NGƯỜI (title_behind) và để biết vị trí đầu (tâm zoom, đặt chữ).
python3 matte.py cut.mp4 DA [--scale 0.5]
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MODELS, Reader, probe, save_json, die

MODEL = os.path.join(MODELS, 'rvm_mobilenetv3_fp32.onnx')

class RVM:
    def __init__(self):
        import onnxruntime as ort
        if not os.path.exists(MODEL):
            die('Thiếu assets/models/rvm_mobilenetv3_fp32.onnx — chạy realcut.py setup')
        so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 2
        self.s = ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider'])
        self.reset()

    def reset(self):
        self.rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4

    def __call__(self, rgb, ratio):
        src = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        out = self.s.run(None, {'src': src, 'r1i': self.rec[0], 'r2i': self.rec[1], 'r3i': self.rec[2],
                                'r4i': self.rec[3], 'downsample_ratio': np.array([ratio], np.float32)})
        self.rec = out[2:]
        return out[1][0, 0]

def person_center_x(path, start=0.0, end=None, n=10):
    """Ước lượng tâm ngang người nói (0..1) từ vài khung — để cắt khung 9:16 từ video ngang."""
    info = probe(path)
    end = end or info['dur']
    w = 480; h = int(round(info['h'] * w / info['w'] / 2) * 2)
    m = RVM(); xs = []
    for i in range(n):
        t = start + (end - start) * (i + 0.5) / n
        r = Reader(path, w, h, ss=t); f = r.read(); r.close()
        if f is None:
            continue
        m.reset()
        for _ in range(3):  # vài lượt cho trạng thái hồi quy ổn định
            a = m(f, 0.5)
        col = a.sum(0)
        if col.sum() > 50:
            xs.append(float((col * np.arange(w)).sum() / col.sum() / w))
    return float(np.median(xs)) if xs else 0.5

def head_point(a):
    """a: alpha (h,w) 0..1 → (x, y_top, y_head) chuẩn hoá, hoặc None."""
    h, w = a.shape
    rows = np.where(a.max(1) > 0.5)[0]
    if len(rows) < 10:
        return None
    top = rows[0]
    band = a[top: min(h, top + int(h * 0.12))]
    col = band.sum(0)
    x = (col * np.arange(w)).sum() / max(col.sum(), 1e-6)
    return (x / w, top / h, min(1.0, (top + h * 0.09) / h))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('da')
    ap.add_argument('--scale', type=float, default=0.5, help='độ phân giải chạy mô hình so với video')
    a = ap.parse_args()
    info = probe(a.src)
    w = int(info['w'] * a.scale) // 2 * 2; h = int(info['h'] * a.scale) // 2 * 2
    ratio = min(1.0, 512 / max(w, h)) if max(w, h) > 512 else 1.0
    from common import Writer
    r = Reader(a.src, w, h)
    out = os.path.join(a.da, 'matte.mp4')
    import subprocess
    wp = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray',
                           '-s', f'{w}x{h}', '-r', str(info['fps']), '-i', '-', '-c:v', 'libx264', '-crf', '14',
                           '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    m = RVM(); heads = []; n = 0
    total = int(info['dur'] * info['fps'])
    while True:
        f = r.read()
        if r.eof or f is None:
            break
        al = m(f, ratio)
        al = np.clip((al - 0.04) / 0.92, 0, 1)
        wp.stdin.write((al * 255).astype(np.uint8).tobytes())
        hp = head_point(al)
        heads.append([round(v, 4) for v in hp] if hp else None)
        n += 1
        if total and n % max(150, int(total) // 4) == 0:
            print(f'  matte {n}/{total}', flush=True)
    r.close(); wp.stdin.close(); wp.wait()
    # làm mượt vị trí đầu (trung bình trượt 0.7 s), lấp chỗ trống
    last = [0.5, 0.2, 0.3]; filled = []
    for hpt in heads:
        last = hpt or last; filled.append(last)
    arr = np.array(filled, float); k = max(1, int(info['fps'] * 0.7))
    if len(arr) > k:
        ker = np.ones(k) / k
        arr = np.stack([np.convolve(np.pad(arr[:, j], (k // 2, k - 1 - k // 2), mode='edge'), ker, 'valid') for j in range(3)], 1)
    save_json(os.path.join(a.da, 'head.json'), dict(fps=info['fps'], w=w, h=h,
              head=[[round(float(v), 4) for v in row] for row in arr]))
    med = np.median(arr, 0)
    print(f'✓ matte {n} khung → {out} · đầu người nói ở x={med[0]:.2f}, đỉnh đầu y={med[1]:.2f}')

if __name__ == '__main__':
    main()
