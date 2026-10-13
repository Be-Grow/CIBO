#!/usr/bin/env python3
"""Mede uma trilha antes de editar em cima dela: BPM, perfil de volume, pausas (respiros/breaks),
o impacto que vem depois de cada pausa e os acentos fortes. Sugere o offset para o impacto cair
no momento-chave do vídeo (revelação da logo, virada do reel, CTA).

Uso: analisa_trilha.py TRILHA [--ate 150] [--alvo 11.75] [--perfil]
  --alvo   segundo do VÍDEO onde o impacto grande deve cair (ex.: logo da vinheta em 11,75 s)
  --perfil imprime o RMS a cada 0,5 s (texto curto; só quando precisar olhar a forma da música)
Sem librosa: numpy + ffmpeg.
"""
import argparse, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('trilha'); ap.add_argument('--ate', type=float, default=150)
ap.add_argument('--alvo', type=float); ap.add_argument('--perfil', action='store_true')
a = ap.parse_args()

SR = 11025
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-t', str(a.ate), '-i', a.trilha, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True).stdout, np.float32)
dur = len(x) / SR


def rms(win):
    w = int(SR * win)
    n = len(x) // w
    v = x[:n * w].reshape(n, w)
    return 20 * np.log10(np.sqrt((v ** 2).mean(1)) + 1e-9)


r50 = rms(0.05)
r250 = rms(0.25)
med = float(np.median(r250))

# BPM: autocorrelação do fluxo espectral
hop = 256
fr = np.lib.stride_tricks.sliding_window_view(x, 1024)[::hop]
E = np.log(np.abs(np.fft.rfft(fr * np.hanning(1024), axis=1)) + 1e-6)
on = np.log1p(np.maximum(np.diff(E, axis=0), 0).sum(1))
k1 = int(SR / hop)  # tira a tendência de ~1 s (pausas e impactos enganam a autocorrelação)
on = np.maximum(on - np.convolve(on, np.ones(k1) / k1, 'same'), 0)
seg = on[:min(len(on), 6000)]; seg = seg - seg.mean()
ac = np.correlate(seg, seg, 'full')[len(seg) - 1:] / (len(seg) - np.arange(len(seg)))
lags = np.arange(len(ac)) * hop / SR
pk = [i for i in range(1, len(ac) - 1) if 0.3 < lags[i] < 1.0 and ac[i] >= ac[i - 1] and ac[i] >= ac[i + 1]]
beat = float(lags[max(pk, key=lambda i: ac[i])])
print(f'duração analisada {dur:.1f}s | batida {beat:.3f}s ({60 / beat:.0f} BPM; metade/dobro também valem: {120 / beat:.0f}/{30 / beat:.0f}) | mediana {med:.0f} dB')

# pausas: >= 0,75 s abaixo de mediana-10 dB; impacto = 1ª janela de 50 ms que volta acima de mediana-2 dB
quiet = r250 < med - 10
pausas = []
i = 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        if (j - i) * 0.25 >= 0.75:
            t0, t1 = i * 0.25, j * 0.25
            k = int(t1 / 0.05) - 10
            while k < len(r50) and r50[k] < med - 2: k += 1
            hit = k * 0.05 if k < len(r50) else None
            pausas.append((t0, t1, hit, float(r50[k]) if hit else None))
        i = j
    else:
        i += 1
print('\nPAUSAS (início-fim -> impacto):')
for t0, t1, hit, lv in pausas:
    print(f'  {t0:6.2f}-{t1:6.2f}s ({t1 - t0:.1f}s)  ->  impacto {hit:.2f}s ({lv:.0f} dB)' if hit else f'  {t0:6.2f}-{t1:6.2f}s  (sem retorno)')

# acentos: pico de 50 ms >= 6 dB acima da mediana móvel de 2 s, espaçados >= 1 s
k = 40
mv = np.array([np.median(r50[max(0, i - k):i + k]) for i in range(len(r50))])
cand = [(r50[i] - mv[i], i * 0.05) for i in range(1, len(r50) - 1) if r50[i] >= r50[i - 1] and r50[i] >= r50[i + 1] and r50[i] - mv[i] >= 6]
cand.sort(reverse=True)
acentos = []
for s, t in cand:
    if all(abs(t - u) >= 1.0 for _, u in acentos): acentos.append((s, t))
acentos = sorted(acentos[:20], key=lambda z: z[1])
print('\nACENTOS FORTES (s, +dB sobre o entorno):', '  '.join(f'{t:.2f}(+{s:.0f})' for s, t in acentos))

if a.alvo is not None and pausas:
    print(f'\nSUGESTÃO para o impacto cair em {a.alvo:.2f}s do vídeo:')
    for t0, t1, hit, _ in sorted(pausas, key=lambda z: z[0] - z[1]):  # pausa mais longa primeiro = mais drama
        if hit is None or hit - a.alvo < 0: continue
        off = hit - a.alvo
        prev = [t for _, t in acentos if off + 0.8 <= t <= off + 3.0]
        first = f'1º acento no vídeo em {prev[0] - off:.2f}s (trilha {prev[0]:.2f})' if prev else 'sem acento forte no começo: use reverse cymbal até o 1º corte'
        print(f'  offset {off:.2f}s -> pausa no vídeo {t0 - off:.2f}-{t1 - off:.2f}s | {first}')

if a.perfil:
    r = rms(0.5)
    print('\nPERFIL (dB a cada 0,5 s):')
    for i in range(0, len(r), 20):
        print(f'  {i * 0.5:6.1f} ' + ' '.join(f'{v:3.0f}' for v in r[i:i + 20]))
