#!/usr/bin/env python3
"""Nota criativa de um reel (0–10 por critério, com justificativa): gancho dos 3 s, tempo morto, densidade de cortes,
variação de ritmo, ênfase de legenda e final. Lê o que o motor já gerou, sem render nem modelo: é uma pré-seleção que o
editor pode derrubar, não um juiz. Ideias (não código) de Shorts-Generator, supoclip (AGPL, só ideia), openshorts,
video-use e OpenCut: ver client-router/references/fontes-externas.md.
Entradas:
  reel-motion   gancho_ritmo.py --props public/rNN/props.json [--segs rNN/segs.json] [--sfx rNN/sfx.json]
                               [--reel rNN/reel.json] [--tema temas/<c>.json] [--json saida.json]
  qualquer SRT  gancho_ritmo.py --srt corte.srt [--dur 62.4] [--tema …]   (sem painéis: só fala, legenda e final)
Limiar e alvos por cliente no tema: "qualidade": {"limiar": 6, "alvo_eventos_10s": [1.5, 4], "max_parado": 6,
"enfase": [0.08, 0.28], "pesos": {...}}. Sai com código 2 se a média ponderada ficar abaixo do limiar."""
import argparse, json, re, statistics as st, sys
from pathlib import Path

a = argparse.ArgumentParser()
for k in ('props', 'segs', 'sfx', 'reel', 'tema', 'srt', 'json'):
    a.add_argument('--' + k)
a.add_argument('--dur', type=float)
A = a.parse_args()
J = lambda f: json.load(open(f)) if f and Path(f).exists() else None

Q = {'limiar': 6, 'alvo_eventos_10s': [1.5, 4.0], 'max_parado': 6.0, 'enfase': [0.08, 0.28], 'pesos': {}}
Q.update((J(A.tema) or {}).get('qualidade', {}))
PESO = {'gancho': 2, 'tempo_morto': 1.5, 'densidade': 1, 'variacao': 1, 'enfase': 1, 'final': 1.5, **Q['pesos']}

# ---------- palavras na linha do tempo da edição
P = J(A.props) or {}
if A.srt:
    def tc(s):
        h, m, r = s.replace(',', '.').split(':'); return int(h) * 3600 + int(m) * 60 + float(r)
    caps = []
    for b in re.split(r'\n\s*\n', open(A.srt, encoding='utf-8-sig').read().strip()):
        L = b.strip().splitlines()
        if len(L) < 3 or '-->' not in L[1]:
            continue
        s, e = (tc(x.strip()) for x in L[1].split('-->')); ws = ' '.join(L[2:]).split()
        d = (e - s) / max(len(ws), 1)
        caps.append({'s': s, 'e': e, 'words': [{'t': w, 'hl': False, 's': s + i * d, 'e': s + (i + 1) * d} for i, w in enumerate(ws)]})
    P = {'captions': caps, 'duration': A.dur or (caps[-1]['e'] + 0.5 if caps else 0)}
W = [w for c in P.get('captions', []) for w in c['words']]
DUR = P.get('duration') or (W[-1]['e'] if W else 0)
if not W:
    sys.exit('sem palavras: passe --props com captions ou --srt')
TXT = lambda ws: ' '.join(w['t'] for w in ws)
limpa = lambda t: re.sub(r'[^\wÀ-ú]', '', t.lower())

# ---------- eventos visuais (o que muda na tela)
ev = set()
segs = J(A.segs) or []
acc = 0
for s0, s1 in segs[:-1]:
    acc += s1 - s0; ev.add(round(acc, 2))                       # emenda da fala
for g in P.get('split', []):
    ev |= {round(g['s'], 2), round(g['e'], 2)}
ev |= {round(b['t'], 2) for b in P.get('burns', [])}
for p in P.get('panels', []):
    ev.add(round(p['s'], 2))
    for key in ('items', 'cards', 'steps', 'events', 'roles'):
        ev |= {round(it['at'], 2) for it in (p.get(key) or []) if isinstance(it, dict) and 'at' in it}
    for key in ('aAt', 'bAt', 'leftAt', 'rightAt', 'topAt', 'fromAt', 'toAt', 'strikeAt'):
        if key in p:
            ev.add(round(p[key], 2))
for k in (P.get('keywords') or []) + (P.get('titles') or []):
    ev.add(round(k['s'], 2))
h = P.get('hook') or {}
ev |= {round(h[k], 2) for k in ('s', 'l2At', 'asideAt') if k in h}
for m in (J(A.reel) or {}).get('camera_moves', []):
    ev.add(round(m['t'], 2))
ev = sorted(t for t in ev if 0 <= t <= DUR)
TEM_VISUAL = len(ev) > 0

nota, por = {}, {}
def da(k, n, txt):
    nota[k] = max(0, min(10, round(n, 1))); por[k] = txt


# ---------- 1. gancho dos 3 s
w3 = [w for w in W if w['s'] < 3]
ini = W[0]['s']
t3 = TXT(w3)
tipo = ('pergunta' if '?' in t3 else 'número' if re.search(r'\d|\b(dois|três|cem|mil|metade|dobro|triplo)\b', t3.lower())
        else 'contraste' if re.search(r'\b(não|nem|mas|nunca|errado|mito|parar?)\b', t3.lower())
        else 'história' if re.search(r'\b(quando|eu|fui|era|aconteceu)\b', t3.lower()) else 'afirmação')
n = 10
mot = [f'tipo {tipo}']
if ini > 0.4:
    n -= min(4, (ini - 0.4) * 5); mot.append(f'primeira palavra em {ini:.2f} s')
if len(w3) < 5:
    n -= 2; mot.append(f'só {len(w3)} palavras nos 3 s')
if TEM_VISUAL and not any(t < 3 for t in ev):
    n -= 2; mot.append('nada muda na tela nos 3 s')
if not h and TEM_VISUAL:
    n -= 1.5; mot.append('sem título de gancho')
if re.match(r'^\s*(então|é|bom|olha|tipo|né|assim|e)\b', t3.lower()):
    n -= 2; mot.append(f'abre com muleta "{t3.split()[0]}"')
if not re.search(r'[.!?…]', TXT([w for w in W if w['s'] < 6])):
    n -= 1; mot.append('nenhuma frase fecha em 6 s')
da('gancho', n, f'"{t3[:60]}" — ' + '; '.join(mot))

# ---------- 2. tempo morto (fala e tela)
gaps = [(W[i]['e'], W[i + 1]['s']) for i in range(len(W) - 1) if W[i + 1]['s'] - W[i]['e'] > 0.6]
morto = sum(b - a for a, b in gaps)
pior_fala = max(gaps, key=lambda g: g[1] - g[0]) if gaps else None
n = 10 - morto / DUR * 30 - sum(max(0, b - a - 1.0) * 1.5 for a, b in gaps)
mot = [f'{len(gaps)} pausa(s) >0,6 s somando {morto:.1f} s'] + ([f'maior {pior_fala[0]:.1f}–{pior_fala[1]:.1f} s'] if pior_fala else [])
if TEM_VISUAL:
    marcos = [0] + ev + [DUR]
    par = max(zip(marcos, marcos[1:]), key=lambda x: x[1] - x[0])
    if par[1] - par[0] > Q['max_parado']:
        n -= min(3, (par[1] - par[0] - Q['max_parado']) * 0.5)
    mot.append(f'tela parada mais longa {par[0]:.1f}–{par[1]:.1f} s ({par[1] - par[0]:.1f} s, limite {Q["max_parado"]})')
da('tempo_morto', n, '; '.join(mot))

# ---------- 3. densidade de cortes / eventos visuais
if TEM_VISUAL:
    d = len(ev) / DUR * 10; lo, hi = Q['alvo_eventos_10s']
    n = 10 if lo <= d <= hi else 10 - (lo - d) / lo * 10 if d < lo else 10 - (d - hi) / hi * 8
    da('densidade', n, f'{len(ev)} mudanças de tela em {DUR:.0f} s = {d:.1f}/10 s (alvo {lo}–{hi})')
else:
    cps = len(P['captions']) / DUR * 10
    da('densidade', 10 if 2 <= cps <= 6 else 6, f'só legenda: {cps:.1f} blocos/10 s (sem dados de tela: passe --props)')

# ---------- 4. variação de ritmo (intervalos entre mudanças + fala/s por bloco)
mot = []; n = 10
if TEM_VISUAL and len(ev) >= 4:
    iv = [b - a for a, b in zip(ev, ev[1:]) if b - a > 0.2]
    cv = st.pstdev(iv) / st.mean(iv) if iv else 0
    if cv < 0.3:
        n -= (0.3 - cv) * 20; mot.append(f'mudanças em intervalos quase iguais (CV {cv:.2f}): soa mecânico')
    else:
        mot.append(f'intervalos variados (CV {cv:.2f})')
taxa = [len(c['words']) / max(c['e'] - c['s'], 0.3) for c in P['captions'] if len(c['words']) >= 2]
if len(taxa) >= 4:
    med = st.median(taxa); fora = sum(1 for t in taxa if abs(t - med) / med > 0.35)
    mot.append(f'fala {med:.1f} palavras/s, {fora} bloco(s) fora de ±35 %')
    if fora / len(taxa) > 0.4:
        n -= 2; mot.append('ritmo de fala irregular demais')
mvs = [m.get('kind') for m in (J(A.reel) or {}).get('camera_moves', [])]
seg_ = max((sum(1 for _ in g) for _, g in __import__('itertools').groupby(mvs)), default=0)
if seg_ > 3:
    n -= 1.5; mot.append(f'{seg_} movimentos de câmera iguais seguidos')
if mot:                                   # sem dados não vale nota
    da('variacao', n, '; '.join(mot))

# ---------- 5. ênfase de legenda
hl = [w for w in W if w.get('hl')]
fr = len(hl) / len(W); lo, hi = Q['enfase']
VAZIA = {'a', 'o', 'e', 'de', 'do', 'da', 'que', 'é', 'um', 'uma', 'em', 'no', 'na', 'com', 'pra', 'para', 'se', 'os', 'as', 'dos', 'das'}
vaz = [w['t'] for i, w in enumerate(W) if w.get('hl') and limpa(w['t']) in VAZIA   # sozinha; dentro de expressão vale
       and not (i and W[i - 1].get('hl')) and not (i + 1 < len(W) and W[i + 1].get('hl'))]
cheio = sum(1 for c in P['captions'] if c['words'] and all(w.get('hl') for w in c['words']) and len(c['words']) > 2)
n = 10 if lo <= fr <= hi else 10 - abs(fr - (lo if fr < lo else hi)) * 40
n -= min(3, len(vaz) * 0.5) + cheio
da('enfase', n, f'{len(hl)}/{len(W)} palavras em destaque ({fr:.0%}, alvo {lo:.0%}–{hi:.0%})'
   + (f'; destaque em palavra vazia: {", ".join(vaz[:5])}' if vaz else '') + (f'; {cheio} bloco(s) inteiro(s) em destaque' if cheio else ''))

# ---------- 6. final
ult = W[-1]; cauda = DUR - ult['e']; fim = TXT(W[-6:])
n = 10; mot = [f'"…{fim[-50:]}"']
if not re.search(r'[.!?…]["”]?$', ult['t']) and not A.srt:
    n -= 3; mot.append('última palavra sem ponto: frase pode estar cortada')
if limpa(ult['t']) in VAZIA | {'mas', 'porque', 'então', 'tipo', 'né'}:
    n -= 3; mot.append(f'termina em "{ult["t"]}"')
if cauda < 0.25:
    n -= 2; mot.append(f'só {cauda:.2f} s depois da última palavra (palavra engolida?)')
elif cauda > 2.5:
    n -= min(3, cauda - 2.5); mot.append(f'{cauda:.1f} s de cauda depois da fala')
else:
    mot.append(f'cauda {cauda:.1f} s')
da('final', n, '; '.join(mot))

# ---------- relatório
tot = round(sum(nota[k] * PESO[k] for k in nota) / sum(PESO[k] for k in nota), 1)
NOME = {'gancho': 'gancho 3 s', 'tempo_morto': 'tempo morto', 'densidade': 'densidade', 'variacao': 'variação', 'enfase': 'ênfase', 'final': 'final'}
for k in nota:
    print(f'  {NOME[k]:<12} {nota[k]:>4}  {por[k]}')
fracos = sorted(nota, key=nota.get)[:2]
ok = tot >= Q['limiar']
print(f'  {"NOTA":<12} {tot:>4}  limiar {Q["limiar"]} → {"OK" if ok else "BLOQUEIA"}; mexer primeiro em: {", ".join(NOME[k] for k in fracos)}')
if A.json:
    json.dump({'nota': tot, 'limiar': Q['limiar'], 'ok': ok, 'criterios': {k: {'nota': nota[k], 'por': por[k]} for k in nota}},
              open(A.json, 'w'), indent=1, ensure_ascii=False)
sys.exit(0 if ok else 2)
