#!/usr/bin/env python3
"""B-roll com speed ramp para inserts (drone, ambiente), já em 1080×1920 e no fps do reel.

uso: broll_ramp.py FONTE SAIDA.mov --from 25.0 --dur 3.2 [--speed "4@0,1@0.45"] [--fps 30] [--cx 0.5] [--blend 1]

--speed  curva de velocidade em quadros-chave velocidade@posição (0–1 da duração de saída), interpolada com
         suavização (smoothstep). "4@0,1@0.45" = entra a 4× e assenta em 1× (speed in, para entrar no
         corte com energia); "1@0,1@0.6,5@1" = sai acelerando (speed out). Sem --speed: 1×.
--blend  nos trechos acima de 1,5× mistura os quadros de fonte pulados (motion blur de verdade, sem flicker).
--cx     centro do recorte 9:16 em fonte horizontal (0–1). Fonte vertical (drone com rotação 90) usa o quadro todo.
A fonte é lida já rodada pelo ffmpeg (autorotate) e escalada para 1080 de largura uma vez; nunca upscale de fonte < 1080.
Pedido do brief Growth Leaders (18/10/2026): drone intercalado com speed ramp, tom cinematográfico.
"""
import argparse, json, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--from', dest='t0', type=float, default=0.0)
ap.add_argument('--dur', type=float, required=True)
ap.add_argument('--speed', default='1@0')
ap.add_argument('--fps', type=float, default=30)
ap.add_argument('--cx', type=float, default=0.5)
ap.add_argument('--blend', type=int, default=1)
a = ap.parse_args()

pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                'stream=width,height,r_frame_rate:stream_side_data=rotation:format=duration', '-of', 'json', a.src],
                               capture_output=True, text=True).stdout)
st = pr['streams'][0]; w, h = st['width'], st['height']
rot = abs(int(next((d.get('rotation', 0) for d in st.get('side_data_list', []) if 'rotation' in d), 0)))
if rot in (90, 270):
    w, h = h, w
num, den = map(int, st['r_frame_rate'].split('/')); sfps = num / den
fdur = float(pr['format']['duration'])

# curva de velocidade → tempo de fonte por quadro de saída
keys = sorted((float(p.split('@')[1]), float(p.split('@')[0])) for p in a.speed.split(','))
N = int(round(a.dur * a.fps))
u = (np.arange(N) + 0.5) / N
ku, ks = zip(*keys)
if len(keys) == 1:
    sp = np.full(N, ks[0])
else:
    seg = np.clip(np.searchsorted(ku, u) - 1, 0, len(ku) - 2)
    x = np.clip((u - np.array(ku)[seg]) / (np.array(ku)[seg + 1] - np.array(ku)[seg]), 0, 1)
    x = x * x * (3 - 2 * x)
    sp = np.array(ks)[seg] + (np.array(ks)[seg + 1] - np.array(ks)[seg]) * x
tau = np.concatenate([[0], np.cumsum(sp / a.fps)])            # tempo de fonte no início de cada quadro de saída
need = tau[-1] + 2 / sfps
assert a.t0 + need <= fdur + 1e-3, f'trecho passa do fim da fonte: {a.t0 + need:.2f}s > {fdur:.2f}s'

# recorte 9:16 na fonte (altura inteira) e escala para 1080×1920
if w / h > 9 / 16 + 1e-3:
    cw = round(h * 9 / 16 / 2) * 2; x0 = int(min(max(a.cx * w - cw / 2, 0), w - cw)); crop = f'crop={cw}:{h}:{x0}:0,'
else:
    ch = round(w * 16 / 9 / 2) * 2; crop = f'crop={w}:{ch}:0:{(h - ch) // 2},'
OW, OH = 1080, 1920
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{a.t0:.4f}', '-t', f'{need:.4f}', '-i', a.src,
                        '-vf', f'{crop}scale={OW}:{OH}:flags=lanczos', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(a.fps),
                        '-i', '-', '-c:v', 'prores_ks', '-profile:v', '2', '-pix_fmt', 'yuv422p10le', a.out], stdin=subprocess.PIPE)
FS = OW * OH * 3
buf, base = [], 0                                             # quadros de fonte em memória a partir do índice base


def frame(i):
    global base
    while base + len(buf) <= i:
        b = dec.stdout.read(FS)
        if len(b) < FS:
            break
        buf.append(np.frombuffer(b, np.uint8).reshape(OH, OW, 3))
    i = min(i, base + len(buf) - 1)
    return buf[i - base]


for k in range(N):
    i0 = int(tau[k] * sfps); i1 = max(i0 + 1, int(tau[k + 1] * sfps))
    if a.blend and sp[k] > 1.5 and i1 - i0 > 1:
        acc = np.zeros((OH, OW, 3), np.float32)
        for i in range(i0, i1):
            acc += frame(i)
        out = (acc / (i1 - i0)).astype(np.uint8)
    else:
        out = frame(i0)
    enc.stdin.write(out.tobytes())
    drop = i0 - base - 2                                       # libera o que ficou para trás
    if drop > 0:
        del buf[:drop]; base += drop
enc.stdin.close(); enc.wait(); dec.kill()
print(f'{a.out}: {N} quadros, fonte {a.t0:.2f}–{a.t0 + tau[-1]:.2f}s, velocidade {sp.min():.1f}–{sp.max():.1f}×')
