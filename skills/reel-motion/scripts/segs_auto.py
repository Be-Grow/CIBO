#!/usr/bin/env python3
"""Trechos mantidos (segs.json) de um vídeo de roteiro fechado inteiro (Andreia, 19/10/2026): fala contínua; pausa > 0,45 s vira
emenda com ~0,27 s de sobra. Depois FECHE cada trecho pela energia da voz (o fim do Whisper come o fim da palavra:
"espiritu|al", "proble|ma") e rode fala-limpa/hesita.py para gaguejadas. uso: segs_auto.py vNN_large.json DURAÇÃO > rNN/segs.json"""
import json, sys
r = json.load(open(sys.argv[1])); D = float(sys.argv[2])
ws = [w for s in r['segments'] for w in s['words']]
S = [[max(0.0, ws[0]['start'] - 0.12), None]]; prev = ws[0]['end']
for w in ws[1:]:
    if w['start'] - prev > 0.45:
        S[-1][1] = round(prev + 0.15, 2); S.append([round(w['start'] - 0.12, 2), None])
    prev = w['end']
S[-1][1] = round(min(D, prev + 0.3), 2); S[0][0] = round(S[0][0], 2)
print(json.dumps(S))
