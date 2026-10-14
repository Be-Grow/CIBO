#!/usr/bin/env python3
"""Cartão off-white com logo de marca (sombra, cantos arredondados), entra com pop e sai: ProRes 4444 com alfa + PNG.
Mesmo cartão da Growth no gancho do 06 da Priscilla (14/10/2026). Logo sem alfa (JPG): o fundo quase branco vira transparente.
uso: cartao_logo.py LOGO SAIDA.mov [--dur 6.3] [--x 540 --y 1080] [--larg 380] [--escuro|--claro|--cor-do-logo]
Logo claro → cartão grafite automaticamente."""
import sys, subprocess, cv2, numpy as np
a = sys.argv; arg = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
LOGO, OUT = a[1], a[2]; DUR, X0, Y0, LW = arg('--dur', 6.3), arg('--x', 540), arg('--y', 1080), int(arg('--larg', 380))
lg = cv2.imread(LOGO, cv2.IMREAD_UNCHANGED)
if lg.ndim == 2: lg = cv2.cvtColor(lg, cv2.COLOR_GRAY2BGR)
lg = lg.astype(np.float32) / (65535 if lg.dtype == np.uint16 else 255)   # PNG de 16 bits (SVG convertido pelo ImageMagick)
if lg.shape[2] == 3:
    al = np.clip((1 - lg.min(2)) / 0.12, 0, 1)                 # branco → transparente
    if '--cor-do-logo' in a:                                   # bloco de cor: só a moldura branca de fora sai; o branco de dentro fica
        ys, xs = np.where(al > 0.5); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; al = np.ones(lg.shape[:2], np.float32)
    lg = np.dstack([lg, al])
ys, xs = np.where(lg[..., 3] > 0.05); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]   # apara a borda vazia
if '--cor-do-logo' in a:                                       # apara a margem da cor de fundo (foto de produto em fundo branco)
    bd0 = np.median(np.concatenate([lg[:2, :, :3].reshape(-1, 3), lg[-2:, :, :3].reshape(-1, 3)]), 0)
    ys, xs = np.where(np.abs(lg[..., :3] - bd0).max(2) > 0.08)
    if len(ys):
        mg = int(0.06 * max(np.ptp(ys), np.ptp(xs)))
        lg = lg[max(0, ys.min() - mg):ys.max() + mg + 1, max(0, xs.min() - mg):xs.max() + mg + 1]
lh = int(lg.shape[0] * LW / lg.shape[1])
if lh > LW * 0.6: lh = int(LW * 0.6); LW2 = int(lg.shape[1] * lh / lg.shape[0])
else: LW2 = LW
lg = cv2.resize(lg, (LW2, lh), interpolation=cv2.INTER_AREA)
PX, PY, R = 34, 28, 30; CW, CH = LW2 + 2 * PX, lh + 2 * PY
card = np.zeros((CH + 120, CW + 120, 4), np.float32); ox, oy = 60, 50
m = np.zeros((CH, CW), np.uint8); cv2.rectangle(m, (R, 0), (CW - R, CH), 255, -1); cv2.rectangle(m, (0, R), (CW, CH - R), 255, -1)
for cx, cy in ((R, R), (CW - R, R), (R, CH - R), (CW - R, CH - R)): cv2.circle(m, (cx, cy), R, 255, -1, cv2.LINE_AA)
m = m.astype(np.float32) / 255
sh = np.zeros(card.shape[:2], np.float32); sh[oy + 14:oy + 14 + CH, ox:ox + CW] = m * 0.35; card[..., 3] = cv2.GaussianBlur(sh, (0, 0), 18)
# logo claro (ex.: Dark Lab branco) some no off-white: cartão grafite do tema
lum = float((lg[..., :3].mean(2) * lg[..., 3]).sum() / max(1e-3, lg[..., 3].sum()))
cor = (0.110, 0.114, 0.122) if ('--escuro' in a or lum > 0.7) and '--claro' not in a else (0.937, 0.953, 0.965)
if '--cor-do-logo' in a:   # logo que já é um bloco de cor (ex.: Max Titanium preto): cartão na cor da borda dele, sem moldura
    bd = np.concatenate([lg[:3, :, :3].reshape(-1, 3), lg[-3:, :, :3].reshape(-1, 3), lg[:, :3, :3].reshape(-1, 3), lg[:, -3:, :3].reshape(-1, 3)])
    cor = tuple(float(v) for v in np.median(bd, 0))
body = np.dstack([np.full((CH, CW), v) for v in cor] + [m])
reg = card[oy:oy + CH, ox:ox + CW]; b = body[..., 3:]; reg[..., :3] = body[..., :3] * b + reg[..., :3] * (1 - b); reg[..., 3:] = b + reg[..., 3:] * (1 - b)
l = reg[PY:PY + lh, PX:PX + LW2]; la = lg[..., 3:]; l[..., :3] = lg[..., :3] * la + l[..., :3] * (1 - la)
cv2.imwrite(OUT.rsplit('.', 1)[0] + '.png', (card * 255).astype(np.uint8))
FPS = 30000 / 1001; N = int(DUR * FPS); H, Wd = card.shape[:2]; ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1080x1920', '-r', '30000/1001', '-i', '-',
                      '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', OUT], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; ent = ease((t - 0.4) / 0.35); al = min(ent, 1 - ease((t - (DUR - 0.6)) / 0.3))
    fr = np.zeros((1920, 1080, 4), np.float32)
    if al > 0:
        M = cv2.getRotationMatrix2D((Wd / 2, H / 2), (1 - ent) * -6, 0.82 + 0.18 * ent); M[0, 2] += X0 - Wd / 2; M[1, 2] += Y0 - H / 2
        fr = cv2.warpAffine(card, M, (1080, 1920)); fr[..., 3] *= al
    p.stdin.write((np.clip(np.dstack([fr[..., 2], fr[..., 1], fr[..., 0], fr[..., 3]]), 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print(OUT, N, 'quadros')
