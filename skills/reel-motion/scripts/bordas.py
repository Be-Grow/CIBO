#!/usr/bin/env python3
"""Borda de corte pelo SOM, não pelo tempo do Whisper. A correção mais repetida do CIBO (10 vezes entre 14/10 e 14/11/2026:
"corte comendo metade da palavra", "'errada' engolida", "a CIBO faz isso com frequência"): o Whisper marca o fim da palavra
antes de a voz acabar (r06 podcastCast06: fim em 46,62 s, a voz ia até 46,9 s). Nasceu do `refina_bordas.py` daquele job.

Para cada trecho do segs.json: se há voz soando na borda, anda até o primeiro silêncio (nível abaixo do piso por 40 ms) —
o fim anda para a frente (até +0,6 s), o começo para trás (até −0,3 s) — e deixa uma folga. Sem silêncio no alcance = corte
no meio de fala corrida: avisa para ouvir.

uso: bordas.py W                 só confere (sai 1 se houver borda com voz); W = PROJ/04_work/rNN
     bordas.py W --aplica        corrige o segs.json (guarda segs.json.bak-bordas) — rode ANTES de `legenda`
     opções: --folga 0.08  --fim 0.6  --inicio 0.3  --piso DB (padrão: medido no arquivo)"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

a = sys.argv[1:]
if not a or a[0] in ('-h', '--help'): sys.exit(__doc__)
def opt(n, d):
    return float(a[a.index(n) + 1]) if n in a else d
W = Path(a[0]); APLICA = '--aplica' in a
FOLGA, MAXF, MAXI = opt('--folga', 0.08), opt('--fim', 0.6), opt('--inicio', 0.3)
S = json.load(open(W / 'segs.json'))
SR, P = 16000, 160                                                # passo de 10 ms
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(W / 'src_16k.wav'), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                                 capture_output=True).stdout, np.int16).astype(np.float32) / 32768
n = len(x) // P
L = 20 * np.log10(np.sqrt((x[:n * P].reshape(n, P) ** 2).mean(1)) + 1e-9)            # nível a cada 10 ms
com_som = L[L > -70]
if not len(com_som): sys.exit(f'{W}/src_16k.wav sem áudio: rode `reel.py PROJ rNN fonte`')
ruido, voz = np.percentile(com_som, 10), np.percentile(com_som, 90)
PISO = opt('--piso', min(max(ruido + 8, voz - 30), voz - 12))    # silêncio = perto do ruído de fundo, bem abaixo da voz
q = lambda t: min(max(int(round(t * 100)), 0), n - 1)


def calado(i, j):
    return j > i and bool((L[i:j] < PISO).all())


def fim_da_voz(b):
    """primeiro ponto com 40 ms de silêncio a partir de b; None se a fala segue sem pausa"""
    for i in range(q(b) - 2, q(b + MAXF)):
        if calado(i, i + 4): return i / 100
    return None


def inicio_da_voz(t):
    """último ponto com 40 ms de silêncio antes de t; None se já vinha fala"""
    for i in range(q(t) + 2, q(t - MAXI), -1):
        if calado(i - 4, i): return i / 100
    return None


out, mexe, ouvir = [], 0, 0
for k, seg in enumerate(S):
    s, e = float(seg[0]), float(seg[1]); ns, ne = s, e; nota = []
    ant = float(S[k - 1][1]) if k else -1e9; prox = float(S[k + 1][0]) if k + 1 < len(S) else 1e9
    if not calado(q(s), q(s) + 3):                                # voz soando no primeiro quadro do trecho
        v = inicio_da_voz(s)
        if v is None: nota.append(f'começo em fala corrida ({L[q(s)]:.0f} dB): ouvir'); ouvir += 1
        else: ns = round(max(v - FOLGA, ant, 0), 2)
    if not calado(q(e) - 3, q(e)):                                # voz soando no último quadro do trecho
        v = fim_da_voz(e)
        if v is None: nota.append(f'fim em fala corrida ({L[q(e) - 1]:.0f} dB): ouvir'); ouvir += 1
        else: ne = round(min(v + FOLGA, prox, n / 100), 2)
    if abs(ns - s) >= 0.02: nota.append(f'começo {s:.2f}→{ns:.2f} ({ns - s:+.2f} s)')
    if abs(ne - e) >= 0.02: nota.append(f'fim {e:.2f}→{ne:.2f} ({ne - e:+.2f} s)')
    mexe += abs(ns - s) >= 0.02 or abs(ne - e) >= 0.02
    out.append([ns, ne] + list(seg[2:]))
    if nota: print(f'{s:.2f}-{e:.2f} corte no som: ' + '; '.join(nota))
print(f'piso {PISO:.0f} dB (voz {voz:.0f}, fundo {ruido:.0f}) | {len(S)} trechos, {mexe} com borda em cima da voz, {ouvir} em fala corrida')
if APLICA and mexe:
    bak = W / 'segs.json.bak-bordas'
    if not bak.exists(): bak.write_text((W / 'segs.json').read_text())
    json.dump(out, open(W / 'segs.json', 'w')); print(f'segs.json corrigido ({mexe} trechos); original em {bak.name}. Refaça voz/legenda.')
sys.exit(0 if APLICA or not (mexe or ouvir) else 1)
