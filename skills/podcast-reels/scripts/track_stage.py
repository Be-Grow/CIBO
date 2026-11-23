"""Rastreia o João num mezanino e gera cropx_timeline para o podcast-reels (cropx_interp).

Uso: track.py SRC.mov OUT.json
- YuNet a cada 3 quadros; corte de câmera por diferença de quadro (o recorte salta só ali).
- Dentro de um plano: zona morta de 110 px; fora dela o centro anda suave até o rosto.
- Pontos a cada 0,5 s e um par de pontos colado em cada corte de câmera (degrau).
"""
import json, os, sys
from pathlib import Path
import cv2, numpy as np

# modelo de detecção genérico (YuNet), não é asset de cliente
MODEL = os.environ.get('YUNET', str(Path(__file__).resolve().parents[2] / 'content-hub' / 'assets' / 'yunet.onnx'))
src, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
W, H = 1920, 1080; CW = 608; DZ = 60   # zona morta em px (110 deixava o rosto encostado na borda)
det = cv2.FaceDetectorYN.create(MODEL, '', (960, 540), 0.6)
det.setInputSize((960, 540))
ring = []; t = 0; i = 0
cuts = [0.0]; obs = []          # (t, face_x, face_w)
track = None
while True:
    ok, fr = cap.read()
    if not ok: break
    t = i / fps
    small = cv2.cvtColor(cv2.resize(fr, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    # corte seco ou dissolve curto: compara com 4 quadros atrás
    ring.append(small); ring = ring[-5:]
    if len(ring) == 5 and float(cv2.absdiff(ring[0], ring[-1]).mean()) > 22 and t - cuts[-1] > 0.8:
        cuts.append(round(t - 2 / fps, 3)); track = None
    if i % 3 == 0:
        _, faces = det.detect(cv2.resize(fr, (960, 540), interpolation=cv2.INTER_AREA))
        cand = []
        for f in (faces if faces is not None else []):
            x, y, w, h = [float(v) * 2 for v in f[:4]]
            if w < 40: continue
            cand.append((x + w / 2, y + h / 2, w))
        if cand:
            if track is None:
                c = max(cand, key=lambda z: z[2])
            else:
                c = min(cand, key=lambda z: abs(z[0] - track))
                if abs(c[0] - track) > 260: c = None
            if c:
                track = c[0]; obs.append((t, c[0], c[2]))
    i += 1
dur = t
cuts.append(dur + 1 / fps)
pts = []; shots = []
for a, b in zip(cuts, cuts[1:]):
    o = [(tt, x) for tt, x, _ in obs if a <= tt < b]
    if not o:
        shots.append(dict(start=a, end=b, n=0)); continue
    ts = np.array([p[0] for p in o]); xs = np.array([p[1] for p in o])
    # mediana móvel de 1 s contra detecções erradas
    sm = np.array([np.median(xs[(ts >= tt - 0.5) & (ts <= tt + 0.5)]) for tt in ts])
    center = sm[0]; cur = []
    for tt in np.arange(a, b, 1 / fps):
        fx = np.interp(tt, ts, sm)
        d = fx - center
        if abs(d) > DZ: center += (d - np.sign(d) * DZ) * 0.14   # persegue só fora da zona morta
        cur.append((tt, center))
    # amostra a cada 0,5 s
    step = int(0.5 * fps)
    sel = cur[::step] + [cur[-1]]
    for tt, cx in sel:
        cropx = min(1, max(0, (cx - CW / 2) / (W - CW)))
        pts.append([round(float(tt), 3), round(float(cropx), 4)])
    shots.append(dict(start=round(a, 3), end=round(b, 3), n=len(o),
                      xmin=float(xs.min()), xmax=float(xs.max())))
json.dump(dict(cuts=cuts, shots=shots, timeline=pts), open(out, 'w'), indent=1)
print(f'{src}: {len(cuts)-2} cortes de câmera, {len(obs)} detecções, {len(pts)} pontos')
for s in shots: print(' ', s)
