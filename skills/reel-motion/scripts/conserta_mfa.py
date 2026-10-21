#!/usr/bin/env python3
"""Conserta o edit_mfa.json onde o MFA colapsou (Andreia, 19/10/2026): palavra a > 0,6 s do Whisper, ou < 0,06 s numa
sequência colapsada, recebe o tempo do Whisper (edit_w.json). Rode depois da etapa legenda, antes das props. uso: conserta_mfa.py rNN/"""
import json, sys, re, difflib
W = sys.argv[1]
d = json.load(open(f'{W}/edit_mfa.json')); m = d['segments'][0]['words']
w = [x for s in json.load(open(f'{W}/edit_w.json'))['segments'] for x in s['words']]
N = lambda s: re.sub(r'[^a-zà-ÿ0-9]', '', s.lower())
sm = difflib.SequenceMatcher(a=[N(x['word']) for x in m], b=[N(x['word']) for x in w], autojunk=False)
n = 0
for a, b, k in sm.get_matching_blocks():
    for i in range(k):
        x, y = m[a + i], w[b + i]
        if abs(x['start'] - y['start']) > 0.6 or (x['end'] - x['start'] < 0.06 and abs(x['start'] - y['start']) > 0.3):
            x['start'], x['end'] = round(y['start'] + 0.08, 3), round(y['end'], 3); n += 1
if m[0]['start'] > 0.5 and w[0]['start'] < 0.3:
    m[0]['start'] = 0.12; n += 1
for i in range(1, len(m)):              # mantém a ordem
    if m[i]['start'] < m[i - 1]['start']:
        m[i]['start'] = m[i - 1]['start'] + 0.02
json.dump(d, open(f'{W}/edit_mfa.json', 'w'), ensure_ascii=False, indent=1)
print('palavras com tempo do Whisper:', n)
