#!/usr/bin/env python3
"""QA de posição do rosto na entrega (reprovação da Andreia, 19/10/2026: "ela não tá no terço direito centralizada").
uso: qa_rosto.py VIDEO.mp4 [--passo 0.25] [--json saida.json] [--alvo-split 1600] [--split s-e,s-e] [--pacote 07_davinci/<nome>]
Mede o centro do rosto (YuNet) a cada passo e lista os trechos em que ele foge do alvo:
  tela dividida (trechos --split): centro x no alvo ± 40 px e o rosto inteiro à direita do painel.
  texto × rosto (--pacote): o alfa de cada camada de texto do pacote DaVinci (legenda/, _camadas/el/, tempos do
  timeline.fcpxml) não pode entrar na caixa do rosto (margem --margem px). Reprovação de 19/10/2026: "o texto cobre o rosto".
Saída: uma linha por trecho com defeito + resumo; o JSON guarda t, x, y, w, h de cada medida.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, cv2
ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--passo', type=float, default=0.25)
ap.add_argument('--json'); ap.add_argument('--alvo-split', type=float, default=1600); ap.add_argument('--painel', type=float, default=1280)
ap.add_argument('--split', default=''); ap.add_argument('--tol', type=float, default=40)
ap.add_argument('--pacote'); ap.add_argument('--margem', type=float, default=20)
a = ap.parse_args()
MODEL = str(Path.home() / '.cache/yunet/face_detection_yunet_2023mar.onnx')
cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 30; N = int(cap.get(7))
W, H = int(cap.get(3)), int(cap.get(4)); S = 0.5
det = cv2.FaceDetectorYN.create(MODEL, '', (int(W * S), int(H * S)), 0.6, 0.3, 5000)
SP = [tuple(map(float, p.split('-'))) for p in a.split.split(',') if p]
out = []; step = max(1, round(a.passo * fps)); f = 0
while f < N:
    cap.set(cv2.CAP_PROP_POS_FRAMES, f); ok, im = cap.read()
    if not ok: break
    _, fs = det.detect(cv2.resize(im, (int(W * S), int(H * S))))
    t = f / fps
    if fs is not None and len(fs):
        b = max(fs, key=lambda r: r[2] * r[3])[:4] / S
        out.append([round(t, 2), round(b[0] + b[2] / 2), round(b[1] + b[3] / 2), round(b[2]), round(b[3])])
    else:
        out.append([round(t, 2), None, None, None, None])
    f += step
if a.json: json.dump(out, open(a.json, 'w'))

def camadas(pac):
    """[(nome, t0, fps, [bbox|None por quadro a 1/passo])] das camadas de texto do pacote, no tamanho do vídeo."""
    import re, subprocess, urllib.parse
    from fractions import Fraction
    pac = Path(pac); X = (pac / 'timeline.fcpxml').read_text()
    fr = lambda v: float(Fraction(v.rstrip('s'))) if v else 0.0
    src = {}
    for m in re.finditer(r'<asset id="([^"]+)"[^>]*>\s*<media-rep[^>]*src="([^"]+)"', X):
        src[m.group(1)] = Path(urllib.parse.unquote(m.group(2).replace('file://', '')))
    res = []; SW, SH = 480, 270; fp = 1 / a.passo
    for m in re.finditer(r'<asset-clip ([^>]*)>', X):
        at = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))); f = src.get(at.get('ref'))
        if not f or not ('/legenda/' in str(f) or '/_camadas/el/' in str(f)) or 'bg' in f.stem: continue
        t0, st, du = fr(at.get('offset')), fr(at.get('start')), fr(at.get('duration'))
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{st:.3f}', '-t', f'{du:.3f}', '-i', str(f), '-vf',
              f'fps={fp},alphaextract,scale={SW}:{SH}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
        fr_ = np.frombuffer(raw, np.uint8).reshape(-1, SH, SW); bx = []
        for q in fr_:
            q = q.astype(np.int16) - np.median(q, axis=1, keepdims=True)  # véu em gradiente (uniforme na linha) não é texto
            ys, xs = np.nonzero(q > 80)
            bx.append(None if not len(xs) else (xs.min() * W / SW, ys.min() * H / SH, (xs.max() + 1) * W / SW, (ys.max() + 1) * H / SH))
        res.append((f.stem, t0, bx))
    return res

if a.pacote:
    CAM = camadas(a.pacote); txt = []
    for t, x, y, w, h in out:
        if x is None: continue
        r = (x - w / 2 - a.margem, y - h / 2 - a.margem, x + w / 2 + a.margem, y + h / 2 + a.margem)
        for nome, t0, bx in CAM:
            i = int(round((t - t0) / a.passo))
            if 0 <= i < len(bx) and bx[i]:
                b = bx[i]
                if b[0] < r[2] and b[2] > r[0] and b[1] < r[3] and b[3] > r[1]:
                    txt.append((t, f'TEXTO SOBRE O ROSTO: {nome} caixa {tuple(int(v) for v in b)}'))
    print(f'camadas de texto lidas: {len(CAM)}')
ruins = []
for t, x, y, w, h in out:
    insp = any(s <= t <= e for s, e in SP)
    if x is None: ruins.append((t, 'sem rosto')); continue
    if insp and (abs(x - a.alvo_split) > a.tol or x - w / 2 < a.painel):
        ruins.append((t, f'split x={x} (alvo {a.alvo_split:.0f}), borda esq {x - w/2:.0f}'))
# agrupa
g = []
for t, m in sorted(ruins + (txt if a.pacote else [])):
    if g and t - g[-1][1] <= a.passo * 1.5: g[-1][1] = t; g[-1][2].append(m)
    else: g.append([t, t, [m]])
for s, e, ms in g: print(f'{s:6.2f}-{e:6.2f}  {ms[len(ms)//2]}')
xs = [r[1] for r in out if r[1] is not None and any(s <= r[0] <= e for s, e in SP)]
print(f'medidas {len(out)}, trechos ruins {len(g)}; split x min/med/máx', (min(xs), int(np.median(xs)), max(xs)) if xs else '-')
