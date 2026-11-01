#!/usr/bin/env python3
"""Encaixa pontas de trechos no silêncio entre palavras (transcrição do episódio com word_timestamps do mlx-whisper).

Pontas marcadas pelo SRT caem no meio da palavra (EP 10, 01/11/2026: o checa_takes acusou quase todas). Cada início vai
para logo antes da palavra mais próxima (folga até 0,12 s, nunca antes do fim da palavra anterior) e cada fim para logo
depois da palavra mais próxima (folga até 0,15 s, nunca depois do início da próxima). Mostra a palavra de cada ponta.

uso: encaixa_palavras.py ep_words.json rNN/segs.json [...]            reescreve cada segs.json (guarda .bak)
     encaixa_palavras.py ep_words.json --remocoes remocoes.json        mesmo para trechos que SAEM (fim da fala antes, início depois)
"""
import json, shutil, sys

W = [w for s in json.load(open(sys.argv[1]))['segments'] for w in s.get('words', [])]
W = sorted(({'w': w['word'].strip(), 's': w['start'], 'e': w['end']} for w in W), key=lambda w: w['s'])


def ini(t):
    i = min(range(len(W)), key=lambda k: abs(W[k]['s'] - t))
    prev = W[i - 1]['e'] if i else 0
    return round(max(W[i]['s'] - 0.12, (prev + W[i]['s']) / 2), 2), W[i]['w']


def fim(t):
    i = min(range(len(W)), key=lambda k: abs(W[k]['e'] - t))
    nxt = W[i + 1]['s'] if i + 1 < len(W) else W[i]['e'] + 1
    return round(min(W[i]['e'] + 0.15, (W[i]['e'] + nxt) / 2), 2), W[i]['w']


if sys.argv[2] == '--remocoes':
    p = sys.argv[3]; R = json.load(open(p)); shutil.copy2(p, p + '.bak')
    for k, (a, b) in R.items():
        # trecho que sai: a fala mantida termina antes de a (fim de palavra) e recomeça depois de b (início de palavra)
        A, wa = fim(a) if a > 0 else (0, '—'); B, wb = ini(b) if b < W[-1]['e'] else (b, '—')
        R[k] = [A, B]; print(f'{k}: {a:.2f}->{A:.2f} (depois de "{wa}")  {b:.2f}->{B:.2f} (antes de "{wb}")')
    json.dump(R, open(p, 'w'), indent=1)
    sys.exit()

for p in sys.argv[2:]:
    S = json.load(open(p)); shutil.copy2(p, p + '.bak'); out = []
    for a, b in S:
        A, wa = ini(a); B, wb = fim(b)
        out.append([A, B]); print(f'{p.split("/")[-2]}: {a:.2f}-{b:.2f} -> {A:.2f}-{B:.2f}  "{wa}" … "{wb}"')
    json.dump(out, open(p, 'w'))
