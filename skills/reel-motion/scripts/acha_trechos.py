"""Para cada trecho (tempo do episódio) de um ou mais reels, acha em qual câmera/arquivo bruto e em que tempo ele está.
Casa o áudio do trecho do episódio (envelope 10 ms, depois forma de onda) contra o áudio de cada arquivo bruto.
uso: acha_trechos.py EP_16k.wav saida.json segs1.json [segs2.json ...] -- BRUTO1 [BRUTO2 ...]"""
import json, subprocess, sys
import numpy as np
SR = 16000
def pcm(f):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-threads', '2', '-i', f, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                                        capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
def env(x, hop=160):
    n = len(x) // hop; e = np.log(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-9)); return e
i = sys.argv.index('--'); ep, out, segfiles, brutos = sys.argv[1], sys.argv[2], sys.argv[3:i], sys.argv[i + 1:]
x = pcm(ep)
B = {}
for b in brutos:
    y = pcm(b); B[b] = (y, env(y))
res = json.load(open(out)) if __import__('os').path.exists(out) else {}
for sf in segfiles:
    for a, e in json.load(open(sf)):
        key = f'{a:.2f}-{e:.2f}'
        q = x[int((a - 0.3) * SR):int((e + 0.3) * SR)]; eq = env(q); eq = (eq - eq.mean()) / (eq.std() + 1e-9)
        best = None
        for b, (y, ey) in B.items():
            if len(ey) < len(eq): continue
            # correlação normalizada deslizante do envelope
            n = len(eq); c = np.convolve(ey, np.ones(n), 'valid'); c2 = np.convolve(ey ** 2, np.ones(n), 'valid')
            mu = c / n; sd = np.sqrt(np.maximum(c2 / n - mu ** 2, 1e-9))
            r = np.correlate(ey, eq, 'valid') / n / sd
            k = int(np.argmax(r)); sc = float(r[k])
            if best is None or sc > best[0]:
                t0 = k * 0.01; base = int((t0 - 0.05) * SR)
                seg = y[max(base, 0):base + len(q) + int(0.1 * SR)]
                cc = np.correlate(seg, q, 'valid'); fine = (np.argmax(cc) - int(0.05 * SR)) / SR if len(cc) else 0
                best = (sc, b, t0 + fine)
        sc, b, t = best
        res[key] = {'bruto': b, 'offset': round(t + 0.3 - a, 3), 'score': round(sc, 3)}   # t_bruto = t_ep + offset
        print(f'{key}  {b.split("/")[-1]}  t_bruto={a + t + 0.3 - a:.2f}  score {sc:.2f}')
json.dump(res, open(out, 'w'), indent=1)
