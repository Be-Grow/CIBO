"""Acha onde um arquivo de câmera cai no episódio editado, pelo envelope de áudio (10 ms) e refino na forma de onda.
uso: acha_offset.py CAMERA.mp4 EP_16k.wav [EP2_16k.wav ...]  → imprime episódio, offset (t_ep = t_cam + offset) e confiança"""
import subprocess, sys
import numpy as np
SR = 16000
def pcm(f, ss=None, t=None):
    cmd = ['ffmpeg', '-v', 'error', '-threads', '2'] + (['-ss', str(ss)] if ss is not None else []) + ['-i', f] + (['-t', str(t)] if t else []) + ['-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
def env(x, hop=160):
    n = len(x) // hop; e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-9)
    e = np.log(e); return (e - e.mean()) / (e.std() + 1e-9)
cam = sys.argv[1]; c = pcm(cam); ec = env(c)
best = []
for ep in sys.argv[2:]:
    x = pcm(ep); ee = env(x)
    n = 1 << int(np.ceil(np.log2(len(ee) + len(ec))))
    r = np.fft.irfft(np.fft.rfft(ee, n) * np.conj(np.fft.rfft(ec, n)), n)[:len(ee)]
    k = int(np.argmax(r)); conf = r[k] / (np.sqrt((ec ** 2).sum() * (ee[k:k + len(ec)] ** 2).sum()) + 1e-9)
    # refino na forma de onda (±50 ms) num trecho de 20 s
    off = k * 0.01; a = min(60.0, len(c) / SR / 2)
    seg_c = c[int(a * SR):int((a + 20) * SR)]; base = int((a + off - 0.05) * SR)
    seg_e = x[base:base + len(seg_c) + int(0.1 * SR)]
    cc = np.correlate(seg_e, seg_c, 'valid'); fine = (np.argmax(cc) - int(0.05 * SR)) / SR
    best.append((conf, ep, off + fine))
    print(f'{ep.split("/")[-2]}: offset {off + fine:.3f}s  confiança {conf:.2f}')
conf, ep, off = max(best)
print(f'RESULTADO {cam.split("/")[-1]} -> {ep} offset {off:.3f} conf {conf:.2f} dur_cam {len(c)/SR:.1f}')
