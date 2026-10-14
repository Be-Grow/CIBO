#!/usr/bin/env python3
"""Take do bruto com folga para o editor colar no DaVinci quando o corte comeu palavra (pacote 07_davinci, 14/10/2026).
Sai em 07_davinci/<nome>/correcoes/: imagem (enquadramento do take + deslocamento da tela dividida, como a câmera do
reel), voz (mesmo tratamento do mix.py e ganho do master do pacote) e as duas juntas. Começa no início do take, a menos
que --de diga outro ponto da fonte.
uso: trecho_bruto.py PROJ rNN TAKE [--mais 3] [--de S_FONTE] [--nome x]     (TAKE = índice em segs.json, 0 = primeiro)"""
import json, re, subprocess, sys
from fractions import Fraction
from pathlib import Path
import numpy as np

a = sys.argv; P, R, K = Path(a[1]), a[2], int(a[3])
arg = lambda k, d: a[a.index(k) + 1] if k in a else d
W = P / '04_work' / R; PR = json.load(open(P / '04_work' / 'public' / R / 'props.json')); C = json.load(open(W / 'reel.json'))
src = open(Path(__file__).with_name('davinci.py')).read()
g = dict(json=json, re=re, subprocess=subprocess, PR=PR, W=W, FD=Fraction(1001, 30000), Path=Path, np=np)
exec(src[src.index('def bezier'):src.index('SRC = Path(JOB')], g)          # mesmo cálculo de enquadramento do pacote
S = json.load(open(W / 'segs.json')); S = S.get('segs', S) if isinstance(S, dict) else S
TK0, acc = [], 0.0
for s0, s1 in S:
    TK0.append(acc); acc += s1 - s0
g['TK0'] = TK0
A = float(arg('--de', S[K][0])); B = S[K][1] + float(arg('--mais', 3))
px, py, sc = g['transf'](K, TK0[K] + (A - S[K][0]) + 0.3)
w, h = 1080 / sc, 1920 / sc; cx, cy = 1080 - px * 19.2 / sc, 1920 + py * 19.2 / sc; x0, y0 = cx - w / 2, cy - h / 2; PADV = 2000
rot = {'clock': 'transpose=1,', 'cclock': 'transpose=2,'}.get(g['JOB'].get('rotate'), '')
SW, SH = (2160, 3840) if rot else (3840, 2160)
O = P / '07_davinci' / C['name'] / 'correcoes'; O.mkdir(parents=True, exist_ok=True)
nome = arg('--nome', f'take{K:02d}_{A:.2f}')
log = (P / '07_davinci' / C['name'] / 'timeline.fcpxml')
G = 0.0
if (W / 'mix_pre.wav').exists():                                            # ganho do master usado no pacote
    def lufs(f):
        r = subprocess.run(['ffmpeg', '-i', str(f), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        return float(r[r.rfind('I:'):].split()[1])
    G = lufs(W / 'mix.wav') - lufs(W / 'mix_pre.wav')
vf = (f"{rot}pad={SW + 2 * PADV}:{SH + 2 * PADV}:{PADV}:{PADV}:black,crop={w:.0f}:{h:.0f}:{x0 + PADV:.0f}:{y0 + PADV:.0f},"
      "scale=1080:1920:flags=lanczos,format=yuv422p10le")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{A}', '-t', f'{B - A:.2f}', '-noautorotate', '-i', g['JOB']['src'], '-vf', vf,
                '-r', '30000/1001', '-c:v', 'prores_ks', '-profile:v', '2', '-an', str(O / f'{nome}_imagem.mov')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{A}', '-t', f'{B - A:.2f}', '-i', str(W / 'src_48k.wav'), '-af',
                f'afade=t=in:d=0.006,highpass=f=80,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=140:makeup=2,volume={G:.2f}dB',
                '-ac', '1', '-ar', '48000', '-c:a', 'pcm_f32le', str(O / f'{nome}_audio.wav')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(O / f'{nome}_imagem.mov'), '-i', str(O / f'{nome}_audio.wav'), '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'pcm_f32le', str(O / f'{nome}_imagem_e_audio.mov')], check=True)
t = TK0[K] + (A - S[K][0]); print(f'{nome}: fonte {A:.2f}-{B:.2f}, no vídeo a partir de {int(t // 60)}:{t % 60:05.2f}')
