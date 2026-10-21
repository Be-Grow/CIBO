#!/usr/bin/env python3
"""sfx.json a partir do props.json e do bloco "sfx" do tema do cliente (nasceu do sfx_andreia.py do projeto da Andreia,
19–20/10/2026). Dois modos, escolhidos no tema:
  "so_trocas"  um som (ou poucos, girando) só nas trocas de painel/burns e na abertura; nada em frase, legenda ou item.
               Nível pela loudness: `lufs_abaixo_voz` LUFS abaixo da voz.wav do reel. Final aprovado da Andreia
               (tigela tibetana grave, 16 LUFS abaixo; a aguda soou "feliz demais", 20/10/2026).
  "variado"    grupos por tipo de evento girando sem repetir o anterior (whoosh de troca, whoosh de burn, brilho nos itens,
               marca nos títulos/palavras-chave), níveis em dB por grupo. Primeira versão da Andreia ("faltou variação nos
               whooshes… SFX não combinaram com o assunto", 19/10/2026).
Os níveis em dB são medidos contra a voz: os do kit global ficavam 8–10 dB abaixo e sumiam. Mostre prévia de 10 s no
trecho real (voz + trilha) antes do render — o desenho de som é do editor, não da IA.
Bloco no tema (temas/<tema>.json):
  "sfx": {"kit": "/Volumes/SSD/CIBO Acervo/sfx/<cliente>/wav/", "modo": "so_trocas", "trocas": ["tibetan-singing-bowl"],
          "lufs_abaixo_voz": 16, "abertura": true}
  "sfx": {"kit": "…", "modo": "variado", "grupos": {"layout": […], "burn": […], "brilho": […], "marca": […]},
          "db": {"layout": -10, "burn": -10, "brilho": -16, "marca": -12}}
uso: sfx_tema.py rNN/ public/rNN/props.json temas/<tema>.json"""
import itertools, json, subprocess, sys
from pathlib import Path

W, PJ, TJ = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
P = json.load(open(PJ)); S = json.load(open(TJ)).get('sfx')
if not S:
    sys.exit(f'{TJ} sem bloco "sfx": use sfx_auto.py ou defina o desenho de som do cliente no briefing')
K = S['kit'].rstrip('/') + '/'; G = '/Volumes/SSD/CIBO Acervo/sfx/_global/'


def lufs(f):
    r = subprocess.run(['ffmpeg', '-i', str(f), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(r[r.rfind('I:'):].split()[1])


def roda(nomes):
    c = itertools.cycle(nomes)
    return lambda: K + next(c) + '.wav'


ev = []
add = lambda t, f, db: ev.append({'t': round(t, 3), 'f': f, 'db': round(db, 1)})
trocas = sorted({round(g['s'], 2) for g in P.get('split', [])} | {round(g['e'], 2) for g in P.get('split', []) if g['e'] < P['duration'] - 1}
                | {round(b['t'], 2) for b in P.get('burns', [])})

if S.get('modo', 'so_trocas') == 'so_trocas':
    som = roda(S['trocas']); voz = lufs(W / 'voz.wav'); nivel = {}
    def db(f):
        if f not in nivel:
            nivel[f] = voz - S.get('lufs_abaixo_voz', 16) - lufs(f)
        return nivel[f]
    ts = ([P['hook']['s']] if S.get('abertura', True) and P.get('hook') else []) + trocas
    for t in ts:
        if not ev or t - ev[-1]['t'] >= S.get('min_intervalo', 1.5):   # troca de layout + burn no mesmo ponto = um som só
            f = som(); add(t, f, db(f))
else:
    gr, D = S['grupos'], {'layout': -10, 'burn': -10, 'brilho': -16, 'marca': -12, **S.get('db', {})}
    LAY, BUR, BRI, MAR = (roda(gr[k]) for k in ('layout', 'burn', 'brilho', 'marca'))
    if P.get('hook'):
        add(P['hook']['s'], MAR(), D['marca'] - 1)
    for g in P.get('split', []):
        add(g['s'], LAY(), D['layout'])
        if g['e'] < P['duration'] - 1:
            add(g['e'], LAY(), D['layout'] - 1)
    for b in P.get('burns', []):
        add(b['t'], BUR(), D['burn'])
    for h in P.get('titles') or []:
        add(h.get('l2At', h['s'] + 0.5), BRI(), D['brilho'] + 1)
    for k in P.get('keywords') or []:
        add(k['s'], MAR(), D['marca'])
    ult = -9
    for p in P.get('panels', []):
        ats = []
        for key in ('items', 'cards', 'steps', 'events', 'roles'):
            ats += [it['at'] for it in (p.get(key) or []) if isinstance(it, dict) and 'at' in it]
        for key in ('aAt', 'bAt', 'leftAt', 'rightAt', 'topAt', 'fromAt', 'toAt'):
            if key in p:
                ats.append(p[key])
        for t in sorted(ats):
            if p['s'] - 0.05 <= t <= p['e'] and t - ult >= 0.7:
                add(t + 0.05, BRI(), D['brilho']); ult = t
        if 'strikeAt' in p:
            add(p['strikeAt'] + 0.1, G + 'pencil-write.wav', D['brilho'] + 2)
        if p.get('type') == 'stack':
            for c in p['cards']:
                add(c['at'] + 0.35, G + 'dry-thud.wav', D['brilho'] + 1)
    ev.sort(key=lambda e: e['t'])
    out = []
    for e in ev:                                       # brilho colado num whoosh some (o whoosh já marca a troca)
        if out and e['t'] - out[-1]['t'] < 0.3 and any(x in e['f'] for x in gr['brilho']):
            continue
        out.append(e)
    ev = out

ev.sort(key=lambda e: e['t'])
json.dump(ev, open(W / 'sfx.json', 'w'), indent=1, ensure_ascii=False)
print(len(ev), 'SFX;', len({e['f'] for e in ev}), 'sons diferentes;', S.get('modo', 'so_trocas'))
