#!/usr/bin/env python3
"""Acha hesitação que sobrou no áudio montado: "ééé"/"ahn" (voz sem palavra alinhada) e repetição
("que eu que eu", "não não"). O Whisper limpa disfluência do texto e o MFA espalha a palavra sobre ela, então
nenhum dos dois sozinho mostra; o editor pegou três assim no 03 e um "ehm" no 04 da Priscilla (13/10/2026).

uso: hesita.py voz16k.wav edit_mfa.json [--db -38] [--min 0.18]
  1) trechos com voz (janela 20 ms acima de --db) sem nenhuma palavra por perto, de pelo menos --min s
  2) palavra alongada demais (> 0,22 s por sílaba aproximada): costuma ser "que eu|que eu" engolido numa palavra só
  3) palavra ou par de palavras repetido em sequência
Confira cada ponto no áudio (perfil de nível + MFA com o texto repetido) antes de cortar.
"""
import json, re, subprocess, sys
import numpy as np

wav, mfa = sys.argv[1], sys.argv[2]
DB = float(sys.argv[sys.argv.index('--db') + 1]) if '--db' in sys.argv else -38
MIN = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 0.18
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout, np.int16) / 32768
fr = 320
lv = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + fr] ** 2)) + 1e-9) for i in range(0, len(x) - fr, fr)])
W = [w for w in json.load(open(mfa))['segments'][0]['words'] if w['word'].strip()]
cov = np.zeros(len(lv), bool)
for w in W:
    cov[max(int((w['start'] - 0.04) * 50), 0):int((w['end'] + 0.04) * 50) + 1] = True
achados = []
k = 0
while k < len(lv):
    if lv[k] > DB and not cov[k]:
        j = k
        while j + 1 < len(lv) and lv[j + 1] > DB - 4 and not cov[j + 1]:
            j += 1
        if (j - k + 1) / 50 >= MIN:
            achados.append((k / 50, f'voz sem palavra {(j - k + 1) / 50:.2f}s (ééé/ahn?)'))
        k = j + 1
    else:
        k += 1
N = lambda s: re.sub(r'[^0-9a-zà-ÿ]', '', s.lower())
sil = lambda s: max(1, len(re.findall(r'[aeiouáéíóúâêôãõà]+', N(s))))
for i, w in enumerate(W):
    d = w['end'] - w['start']
    if d / sil(w['word']) > 0.36 and not re.search(r'\d', w['word']):
        achados.append((w['start'], f'"{w["word"].strip()}" longa demais ({d:.2f}s): repetição engolida?'))
    if i and N(w['word']) and N(w['word']) == N(W[i - 1]['word']) and N(w['word']) not in ('é',):
        achados.append((W[i - 1]['start'], f'repetição "{W[i - 1]["word"].strip()} {w["word"].strip()}"'))
    if i >= 3 and N(W[i - 3]['word'] + W[i - 2]['word']) == N(W[i - 1]['word'] + w['word']):
        achados.append((W[i - 3]['start'], f'par repetido "{W[i - 3]["word"].strip()} {W[i - 2]["word"].strip()}"'))
for t, m in sorted(achados):
    print(f'{t:6.2f}s  {m}')
print(f'{len(achados)} ponto(s) para conferir' if achados else 'OK: nenhuma hesitação aparente')
