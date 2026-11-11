#!/usr/bin/env python3
"""props.json a partir de um motion.json DECLARATIVO (10/11/2026): o agente descreve o que entra e quando; posição, burns,
tela dividida e encaixe na fala são do motor. Substitui o props.py escrito à mão (cada job com suas funções e coordenadas).
uso (pelo reel.py props): monta_props.py W PUB_R OUT orient

motion.json = o vocabulário do props (hook, titles, keywords, lower, endCard, panels) com estas diferenças:
  - "tags" de painel: {"text", "at", "onde": "topo" | "base" (padrão) | y numérico, "dark": bool} — sem x, sem tamanho;
    etiquetas do mesmo "onde" formam uma linha e QUEBRAM sozinhas se não couberem (layout.autoTags "quebra")
  - "split" opcional: sem ele, a tela dividida cobre cada sequência de painéis colados (vão < 0,3 s)
  - "burns" não se escreve: sai de "tr": "burn" em cada painel
  - "legenda": false = vídeo sem legenda (YouTube); sem a chave, usa blocos.json se existir
  - strike sem "line2At": entra entre o risco e o destaque
  - s/e da tela dividida encaixam no vão entre palavras mais próximo (nunca no meio de uma palavra)
Tudo o mais (tipos de painel e campos) é o do catálogo: `esquema.py` lista; `reel.py … verifica` confere o resultado."""
import json, sys
from pathlib import Path

W, PUBR, OUT, ORIENT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
M = json.load(open(W / 'motion.json')); R = W.name
MW = [w for w in json.load(open(W / 'edit_mfa.json'))['segments'][0]['words'] if w.get('word', '').strip()]
S = json.load(open(W / 'segs.json')); S = S.get('segs', S) if isinstance(S, dict) else S
DUR = M.get('duration') or round(sum(b - a for a, b in S), 3)


def vao(t):
    for i, w in enumerate(MW):
        if w['start'] - 0.02 < t < w['end'] + 0.02:
            prv = MW[i - 1]['end'] if i else 0; nxt = MW[i + 1]['start'] if i + 1 < len(MW) else w['end'] + 0.3
            return round((prv + w['start']) / 2 if t - w['start'] < w['end'] - t else (w['end'] + nxt) / 2, 3)
    return t


panels = M.get('panels') or []
leg = M.get('legenda', (W / 'blocos.json').exists())
caps = json.load(open(W / 'blocos.json')) if leg and (W / 'blocos.json').exists() else []
for b in caps:
    b.pop('audio', None)
Y = {'topo': (30, 24), 'base': (740 if caps else 800, 28)}
for p in panels:
    tags = []
    for g in p.get('tags') or []:
        if isinstance(g, list):
            g = dict(zip(('text', 'at', 'onde', 'dark'), g))
        onde = g.pop('onde', 'base'); y, sz = Y[onde] if onde in Y else (float(onde), 28)
        tags.append({**{k: v for k, v in g.items() if v not in (None, False)}, 'y': y, 'size': g.get('size', sz)})
    p['tags'] = sorted(tags, key=lambda g: g['y'])          # ordem das linhas = ordem do motor (pacote isola por índice)
    if p.get('type') == 'strike' and 'line2At' not in p and 'strikeAt' in p and 'accentAt' in p:
        p['line2At'] = round(max(p['strikeAt'] + 0.1, min(p['strikeAt'] + 0.45, p['accentAt'] - 0.35)), 2)
split = M.get('split')
if split is None:
    split = []
    for p in sorted(panels, key=lambda p: p['s']):
        if split and p['s'] - split[-1]['e'] < 0.3:
            split[-1]['e'] = max(split[-1]['e'], p['e'])
        else:
            split.append({'s': p['s'], 'e': p['e']})
mp = {}
for g in split:
    for k in ('s', 'e'):
        n = vao(g[k]); mp[g[k]] = n; g[k] = n
for p in panels:
    for k in ('s', 'e'):
        p[k] = mp.get(p[k], p[k])
props = {'camera': M.get('camera', f'{R}/camera.mov'), 'duration': round(DUR + M.get('tail', 0.8), 3), 'endFade': 0.9, 'captions': caps,
         'split': split, 'panels': panels, **{k: M[k] for k in ('hook', 'titles', 'keywords', 'lower', 'endCard', 'camX', 'inserts', 'cartoes') if M.get(k) is not None}}
bt = [p['s'] for p in panels if p.get('tr') == 'burn']
if bt:
    pasta = 'burnsH' if ORIENT == 'h' else 'burns'; lista = PUBR.parent / pasta / f'{pasta}.json'
    if not lista.exists():
        sys.exit(f'há painéis com "tr": "burn" e falta a lista de burns do projeto ({lista}): busque com a skill acervo (acervo.py find burn) e gere a pasta {pasta}/')
    B = json.load(open(lista)); K = sorted(B); pre = 'burnH_' if ORIENT == 'h' else 'burn_'
    props['burns'] = [dict(t=t, src=f'{pasta}/{pre}{K[i % len(K)][1:] if ORIENT == "h" else K[i % len(K)]}.mp4', peak=B[K[i % len(K)]]['peak'], dur=B[K[i % len(K)]]['dur']) for i, t in enumerate(bt)]
json.dump(props, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('ok', OUT, len(panels), 'painéis,', len(props.get('burns', [])), 'burns,', 'sem legenda' if not caps else f'{len(caps)} blocos de legenda')
