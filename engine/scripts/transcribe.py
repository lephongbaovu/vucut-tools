#!/usr/bin/env python3
"""vucut · transcribe.py — phiên âm tiếng Việt có mốc từng từ (faster-whisper) → words.json.
Dùng: python -X utf8 transcribe.py <video_hoặc_wav> words.json [--model medium]
Tự đọc âm thanh bằng ffmpeg → numpy (tránh lỗi PyAV mới: open() got an unexpected keyword 'metadata_errors').
Tắt VAD + prompt có từ đệm để Whisper GHI LẠI ờ/ừm (autocut cần). Sau đó LUÔN sửa tay chính tả/tên riêng
(Whisper hay sai: rào cả→rào cản, bao mòn→bào mòn, Tài Nguyên→Tây Nguyên, Đắc Lắc→Đắk Lắk…).
Mồi tên riêng Đắk Lắk qua reference/tu_vung_daklak.txt (+ DA/tu_vung.txt) và tự sửa lỗi quen qua reference/sua_chinh_ta.tsv (+ DA/sua_chinh_ta.tsv)."""
import argparse, json, os, re, subprocess, unicodedata
import numpy as np
VC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--model', default='medium')
ap.add_argument('--vocab', action='append', default=[], help='thêm file từ vựng (mặc định: reference/tu_vung_daklak.txt + DA/tu_vung.txt)')
ap.add_argument('--fix', action='append', default=[], help='thêm file sửa chính tả .tsv (mặc định: reference/sua_chinh_ta.tsv + DA/sua_chinh_ta.tsv)')
a = ap.parse_args()
DA = os.path.dirname(os.path.abspath(a.out))
def lines(paths):
    out = []
    for p in paths:
        if os.path.exists(p):
            out += [l.strip() for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')]
    return out
VOCAB = lines([os.path.join(VC, 'reference', 'tu_vung_daklak.txt'), os.path.join(DA, 'tu_vung.txt'), *a.vocab])
FIX = [l.split('\t') for l in lines([os.path.join(VC, 'reference', 'sua_chinh_ta.tsv'), os.path.join(DA, 'sua_chinh_ta.tsv'), *a.fix]) if '\t' in l]
PROMPT = 'Ờ, ừm, à... thì là, kiểu như. ' + ' '.join(VOCAB)[:600]     # mồi tên riêng + giữ từ đệm cho autocut
from faster_whisper import WhisperModel
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.src, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
A = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
m = WhisperModel(a.model, device='cpu', compute_type='int8')
segs, _ = m.transcribe(A, language='vi', word_timestamps=True, vad_filter=False, beam_size=5,
                       initial_prompt=PROMPT)
out = []
for s in segs:
    print(f'[{s.start:.2f}-{s.end:.2f}] {s.text}', flush=True)
    out += [{'word': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)} for w in s.words]
# sửa chính tả theo bảng (khớp chuỗi từ liên tiếp, giữ mốc thời gian)
norm = lambda w: unicodedata.normalize('NFC', re.sub(r'[^\w\s/]', '', w.lower())).strip()
nfix = 0
for wrong, right in FIX:
    W = norm(wrong).split(); n = len(W); k = 0
    while k + n <= len(out):
        if [norm(x['word']) for x in out[k:k + n]] == W:
            punct = re.sub(r'^.*?([^\w]*)$', r'\1', out[k + n - 1]['word'])
            out[k:k + n] = [{'word': right + punct, 'start': out[k]['start'], 'end': out[k + n - 1]['end']}]; nfix += 1
        k += 1
if nfix: print(f'đã tự sửa {nfix} chỗ chính tả theo sua_chinh_ta.tsv')
json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('xong →', a.out, len(out), 'từ')
