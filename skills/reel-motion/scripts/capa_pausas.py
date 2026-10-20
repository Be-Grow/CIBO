#!/usr/bin/env python3
"""Candidatos de capa nas pausas da fala (boca fechada): quadros da câmera do reel no meio de cada silêncio entre
palavras (edit_mfa.json), pontuados por rosto de frente, olhos alinhados e nitidez; folha com os N melhores, rotulados.
Escolha olhando (olhos abertos, boca fechada, olhando para a câmera). Andreia, 19/10/2026.
uso: capa_pausas.py rNN_dir camera.mov folha.jpg [N]"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
W, CAM, OUT = Path(sys.argv[1]), sys.argv[2], sys.argv[3]; N = int(sys.argv[4]) if len(sys.argv) > 4 else 8
ws = json.load(open(W / 'edit_mfa.json'))['segments'][0]['words']
ts = [round((a['end'] + b['start']) / 2, 2) for a, b in zip(ws, ws[1:]) if b['start'] - a['end'] > 0.12]
det = cv2.FaceDetectorYN.create(str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx'), '', (480, 480), 0.6, 0.3, 5000)
cand = []
for t in ts:
    im = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', CAM, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    fr = cv2.imdecode(np.frombuffer(im, np.uint8), 1)
    if fr is None: continue
    h0, w0 = fr.shape[:2]; s = 480 / max(h0, w0); sm = cv2.resize(fr, (round(w0 * s), round(h0 * s)))
    det.setInputSize((sm.shape[1], sm.shape[0])); _, f = det.detect(sm)
    if f is None: continue
    f = max(f, key=lambda z: z[2]); re, le, no = f[4:6], f[6:8], f[8:10]
    front = 1 - abs((no[0] - re[0]) / (le[0] - re[0] + 1e-6) - 0.5) * 2
    tilt = abs(le[1] - re[1]) / (abs(le[0] - re[0]) + 1e-6)
    x, y, w, h = (f[:4] / s).astype(int); face = fr[max(y, 0):y + h, max(x, 0):x + w]
    sharp = cv2.Laplacian(cv2.cvtColor(face, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var() if face.size else 0
    cand.append((front - tilt + min(sharp, 400) / 400 * 0.5, t, fr))
cand.sort(key=lambda c: -c[0]); top = cand[:N]
tiles = []
for sc, t, fr in sorted(top, key=lambda c: c[1]):
    th = cv2.resize(fr, (270, round(270 * fr.shape[0] / fr.shape[1])))
    cv2.putText(th, f'{t:.2f}', (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2); tiles.append(th)
rows = [np.hstack(tiles[i:i + 4] + [np.zeros_like(tiles[0])] * (4 - len(tiles[i:i + 4]))) for i in range(0, len(tiles), 4)]
cv2.imwrite(OUT, np.vstack(rows)); print(len(ts), 'pausas;', 'melhores:', ' '.join(f'{t:.2f}' for _, t, _ in top))
