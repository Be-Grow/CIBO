"""sfx.json a partir do props.json: whoosh nas trocas de layout e burns, pop baixo nas entradas, cliques do João
(2 sons alternados, ~-20 dBFS, ≥2,5 s, nunca na 1ª palavra) nas palavras de destaque em tela cheia.
uso: sfx_auto.py rNN/ public/rNN/props.json [cliques_max]"""
import json, sys
W, PJ = sys.argv[1], sys.argv[2]; NMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 3
P = json.load(open(PJ))
CK = ['/Volumes/SSD/CIBO Acervo/sfx/joao-campos/camera_click_1.wav', '/Volumes/SSD/Music/Sound/Músicas edicao/click lens.wav',
      '/Volumes/SSD/CIBO Acervo/sfx/joao-campos/camera_click_3.wav']
CKDB = [-19, 4, -19]
ev = []
for g in P['split']:
    ev.append({'t': g['s'], 'f': 'whoosh-soft', 'db': -14})
    ev.append({'t': g['e'], 'f': 'whoosh-reverse-1s', 'db': -16 if g['e'] < P['duration'] - 1.0 else -22})   # no fim, baixo (entra no fade)
for b in P.get('burns', []):
    ev.append({'t': b['t'], 'f': 'whoosh-medium-1s', 'db': -15})
pops = []
for p in P['panels']:
    for k in ('items', 'cards', 'steps', 'events', 'roles'):
        for it in p.get(k, []) if isinstance(p.get(k), list) else []:
            if 'at' in it: pops.append(it['at'])
    for k in ('strikeAt',):
        if k in p: ev.append({'t': p[k] + 0.1, 'f': 'pencil-write', 'db': -19})
pops.sort()
last = -9
for i, t in enumerate(pops):
    if t - last >= 0.6:
        ev.append({'t': t + 0.05, 'f': 'pop-1' if i % 2 == 0 else 'pop-2', 'db': -21}); last = t
# cliques: palavras destacadas fora da tela dividida
def split_at(t):
    return any(g['s'] - 0.3 <= t <= g['e'] + 0.3 for g in P['split'])
words = [w for b in P['captions'] for w in b['words'] if w.get('hl')]
first = P['captions'][0]['words'][0]['s']
ck, lastc = [], -9
for w in words:
    if len(ck) >= NMAX: break
    if w['s'] > first + 0.3 and not split_at(w['s']) and w['s'] - lastc >= 2.5:
        ck.append(w['s']); lastc = w['s']
for i, t in enumerate(ck):
    ev.append({'t': t, 'f': CK[i % 3], 'db': CKDB[i % 3]})
ev.sort(key=lambda e: e['t'])
json.dump(ev, open(f'{W}/sfx.json', 'w'), ensure_ascii=False, indent=1)
print(f'{len(ev)} SFX, cliques em', [round(t, 2) for t in ck])
