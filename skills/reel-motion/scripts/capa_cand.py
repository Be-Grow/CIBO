#!/usr/bin/env python3
"""Candidatos de capa numa folha só, com o recorte de feed já calculado pelo rosto (antes: 3-5 turnos por capa, achando
o enquadramento da fonte à mão). Recorte: zoom ~1,4 sobre o quadro vertical, rosto centrado, topo da cabeça em y≈600
de 1920 (título acima da cabeça, dentro do grid 3:4). Escolha olhando: olhos abertos, boca fechada.

uso: capa_cand.py FONTE.MP4 SAIDA_FOLHA.jpg T1 T2 … [--rot clock] [--grava T rNN/capa_feed.png]
  --grava T ARQ  grava o quadro T recortado em ARQ (1080x1920) para o reel.json "capa": {"frame_file": …}
"""
import subprocess, sys
from pathlib import Path
import numpy as np, cv2

src, out = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
rot = args[args.index('--rot') + 1] if '--rot' in args else 'clock'
grava = args[args.index('--grava') + 1:args.index('--grava') + 3] if '--grava' in args else None
ts = [float(a) for a in args if a.replace('.', '', 1).isdigit() and (not grava or a != grava[0])]
tr = {'clock': 'transpose=1,', 'cclock': 'transpose=2,', 'none': ''}[rot]
det = cv2.FaceDetectorYN.create(str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx'), '', (540, 960), 0.6, 0.3, 5000)


def quadro(t, w=1080, h=1920):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-noautorotate', '-i', src, '-frames:v', '1', '-vf', f'{tr}scale={w}:{h}',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else None


def recorte(im):
    _, f = det.detect(cv2.resize(im, (540, 960)))
    if f is None or not len(f):
        return None
    x, y, w, h = max(f, key=lambda r: r[2] * r[3])[:4] * 2
    Z = 1.4; cw, ch = 1080 / Z, 1920 / Z
    topo = y - 0.45 * h                                  # topo da cabeça ~ 45% da altura do rosto acima da caixa
    y0 = topo - 600 / Z; x0 = x + w / 2 - cw / 2
    x0 = min(max(x0, 0), 1080 - cw); y0 = min(max(y0, 0), 1920 - ch)
    return int(x0), int(y0), int(cw), int(ch)


if grava:
    t = float(grava[0]); im = quadro(t, 2160, 3840)
    c = recorte(cv2.resize(im, (1080, 1920)))
    x0, y0, cw, ch = [v * 2 for v in c]
    cv2.imwrite(grava[1], cv2.resize(im[y0:y0 + ch, x0:x0 + cw], (1080, 1920), interpolation=cv2.INTER_AREA))
    print('capa gravada:', grava[1], 'recorte 4K', (x0, y0, cw, ch)); sys.exit()
tiles = []
for t in ts:
    im = quadro(t)
    if im is None:
        continue
    c = recorte(im)
    if not c:
        continue
    x0, y0, cw, ch = c
    crop = cv2.resize(im[y0:y0 + ch, x0:x0 + cw], (1080, 1920))[420:1180, 200:880]   # rosto e boca
    crop = cv2.resize(crop, (200, 224)); cv2.putText(crop, f'{t}', (5, 20), 0, 0.6, (0, 255, 255), 2)
    tiles.append(crop)
while len(tiles) % 6:
    tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]))
print('folha:', out, len(ts), 'quadros')
