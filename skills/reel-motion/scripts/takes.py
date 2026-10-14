#!/usr/bin/env python3
"""Lista compacta de takes para escolher os trechos de um reel: só a fala da apresentadora, sem as tentativas que ela
refez logo depois resumidas (a última versão inteira, a regra que o editor aprovou) e sem a voz da equipe soprando o roteiro.
Antes eu lia o bruto inteiro (~200 linhas por reel, metade equipe e retakes); a escolha continua sendo do agente.

uso: takes.py src_large.json src_16k.wav [--min -25] [--todas]
  --min    p90 mínimo (dB) para contar como a voz dela (equipe sopra a −30/−50, ela fala a −13/−20)
  --todas  mostra as tentativas superadas por inteiro (por padrão saem resumidas, com ~)
"""
import json, re, subprocess, sys
from difflib import SequenceMatcher
import numpy as np

src, wav = sys.argv[1], sys.argv[2]
MIN = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else -25
TODAS = '--todas' in sys.argv
d = json.load(open(src))
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout, np.int16) / 32768


def p90(a, b):
    s = x[int(a * 16000):int(b * 16000)]
    f = [np.sqrt(np.mean(s[i:i + 1600] ** 2)) for i in range(0, len(s) - 1600, 1600)]
    f = [20 * np.log10(v + 1e-9) for v in f if v > 10 ** (-60 / 20)]
    return np.percentile(f, 90) if f else -99


norm = lambda t: re.sub(r'[^0-9a-zà-ÿ ]', '', t.lower()).strip()
L = [(s['start'], s['end'], s['text'].strip()) for s in d['segments'] if p90(s['start'], s['end']) >= MIN and len(norm(s['text'])) > 2]
# tentativa superada: uma das próximas 12 falas (até 150 s depois) repete o mesmo começo ou é parecida com ela
sup = set()
for i, (a, b, t) in enumerate(L):
    for j in range(i + 1, min(i + 13, len(L))):
        a2, b2, t2 = L[j]
        if a2 - b > 150:
            break
        n1, n2 = norm(t), norm(t2)
        w1, w2 = n1.split()[:3], n2.split()[:3]
        if (len(w1) >= 2 and w1 == w2) or SequenceMatcher(None, n1, n2).ratio() > 0.72:
            sup.add(i); break
n = 0
for i, (a, b, t) in enumerate(L):
    if i in sup and not TODAS:   # superada: aparece resumida (pode ser a melhor se a última tiver equipe ou palavra pior — 05: 608,7 e 761,8)
        print(f"~{a:7.1f}-{b:6.1f} {' '.join(t.split()[:6])}…"); n += 1
        continue
    corte = '…' if t.endswith(('...', '…')) or len(norm(t).split()) <= 2 else ''
    print(f"{'~' if i in sup else ' '}{a:7.1f}-{b:6.1f} {t[:110]}{corte}")
    n += 1
print(f'{n} falas ({len(sup)} tentativas superadas resumidas com ~, {len(d["segments"]) - len(L)} da equipe/ruído fora)')
