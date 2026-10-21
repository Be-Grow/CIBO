#!/usr/bin/env python3
"""Biblioteca compartilhada de movimento de câmera e orçamento de variação (20/10/2026).
Os três tipos já existiam espalhados: `punch` (reel-motion camera_moves, davinci.py/Fusion), `impact_pulses` e `long_moves`
(render.py/punch.py de bombordo-boreste, autismo-cast, content-hub). Os renders continuam onde estão (não reescrever o que
funciona); esta biblioteca GERA e CONFERE os eventos no mesmo formato que cada motor já lê, com parâmetros por tema.
Ideias (não código): openshorts (push ≤12 %, intervalo mínimo entre pushes, "crop parado longo = vídeo não editado"),
video-use (anti-padrão: o mesmo efeito em toda transição). Ver client-router/references/fontes-externas.md.

  movimento.py planeja --tema temas/<c>.json --tempos 3.2,9.8,15.1 --dur 62 [--formato reel|podcast] [--json saida.json]
      tempos = ênfases candidatas (palavra-chave, virada); devolve camera_moves (reel) ou impact_pulses/long_moves (podcast)
  movimento.py confere --tema temas/<c>.json [--sfx sfx.json] [--props props.json] [--reel reel.json] [--clip clip.json]
      orçamento: no máximo N iguais seguidos por categoria (sfx, burn, movimento, painel); código 2 se estourar

No reel tudo sai como `punch` (amount/in diferentes por tipo). Tema: "movimento": {"preset": "editorial", "punch": {...}, "pulse": {...}, "long": {...}}
      "variacao":  {"sfx": 3, "burn": 2, "movimento": 2, "painel": 1}   (0 = sem limite; ex.: Andreia usa um som só, aprovado)"""
import argparse, itertools, json, os, sys
from pathlib import Path

# presets: valores que cada motor já usa hoje (não mudam o que está aprovado)
PRESETS = {
    'editorial': {'punch': {'amount': 0.08, 'in': 0.35, 'hold': 3.5, 'min_gap': 12},         # Andreia r01 (aprovado)
                  'pulse': {'amount': 0.035, 'duration': 1.2, 'min_gap': 6},
                  'long': {'amount': 0.03, 'duration': 2.8, 'min_gap': 15}},
    'podcast':   {'punch': {'amount': 0.06, 'in': 0.3, 'hold': 2.5, 'min_gap': 10},
                  'pulse': {'amount': 0.045, 'duration': 1.1, 'min_gap': 4},                 # bombordo asr_polish
                  'long': {'amount': 0.03, 'duration': 2.8, 'min_gap': 12}},
    'energetico': {'punch': {'amount': 0.10, 'in': 0.25, 'hold': 2.0, 'min_gap': 8},
                   'pulse': {'amount': 0.05, 'duration': 1.0, 'min_gap': 3},
                   'long': {'amount': 0.035, 'duration': 2.4, 'min_gap': 10}},
}
ORC = {'sfx': 3, 'burn': 2, 'movimento': 2, 'painel': 1}
J = lambda f: json.load(open(f)) if f and Path(f).exists() else None


def params(tema, formato='reel'):
    m = (tema or {}).get('movimento', {})
    p = json.loads(json.dumps(PRESETS[m.get('preset', 'podcast' if formato == 'podcast' else 'editorial')]))
    for k in ('punch', 'pulse', 'long'):
        p[k].update(m.get(k, {}))
    return p


def planeja(tempos, dur, tema=None, formato='reel'):
    """ênfases candidatas → movimentos alternando tipo, com intervalo mínimo por tipo e nunca 3 iguais seguidos"""
    p = params(tema, formato); ult = {k: -99 for k in p}; seq = []; out = []
    for t in sorted(tempos):
        if t > dur - 1.5:
            continue
        ordem = ['punch', 'pulse', 'long'] if formato == 'reel' else ['pulse', 'long', 'punch']
        if len(seq) >= 2 and seq[-1] == seq[-2]:
            ordem.remove(seq[-1]); ordem.append(seq[-1])                # orçamento: troca o tipo
        for k in ordem:
            if t - ult[k] >= p[k]['min_gap'] and (not out or t - out[-1][0] >= 1.5):
                out.append((t, k)); ult[k] = t; seq.append(k); break
    if formato == 'reel':
        cm = []
        for t, k in out:
            if k == 'punch':
                cm.append({'t': round(t, 2), 'kind': 'punch', 'amount': p['punch']['amount'], 'in': p['punch']['in'],
                           'until': round(min(dur, t + p['punch']['hold']), 2)})
            else:   # no davinci.py só o punch entra e sai com ease ('zoom' volta seco no hold_until): pulse/long viram punch
                d = p[k]['duration']
                cm.append({'t': round(t, 2), 'kind': 'punch', 'amount': p[k]['amount'], 'in': round(d * (0.5 if k == 'long' else 0.3), 2),
                           'until': round(min(dur, t + d), 2)})
        return {'camera_moves': cm}
    r = {'impact_pulses': [], 'long_moves': []}
    for t, k in out:
        q = p['punch' if k == 'punch' else k]
        if k == 'long':
            r['long_moves'].append({'t': round(t, 2), 'amount': q['amount'], 'duration': q['duration']})
        else:
            r['impact_pulses'].append({'t': round(t, 2), 'amount': q['amount'],
                                       'duration': q.get('duration', q.get('hold', 1.1))})
    return r


def repeticoes(seq, n):
    """trechos com mais de n iguais seguidos: [(chave, quantos, t_inicio)]"""
    if not n:
        return []
    ruins = []
    for k, g in itertools.groupby(seq, key=lambda x: x[1]):
        g = list(g)
        if len(g) > n:
            ruins.append((k, len(g), g[0][0]))
    return ruins


def confere(tema=None, sfx=None, props=None, reel=None, clip=None):
    o = {**ORC, **(tema or {}).get('variacao', {})}
    cat = {}
    if sfx:
        cat['sfx'] = [(e['t'], os.path.basename(e['f'])) for e in sfx]
    if props:
        cat['burn'] = [(b['t'], os.path.basename(b.get('src', '?'))) for b in props.get('burns', [])]
        cat['painel'] = [(p['s'], p.get('type', '?')) for p in props.get('panels', [])]
    mv = [(m['t'], f"{m['kind']} {m['amount']}") for m in (reel or {}).get('camera_moves', [])]
    mv += [(e['t'], f"pulse {e.get('amount', '')}") if isinstance(e, dict) else (e, 'pulse') for e in (clip or {}).get('impact_pulses', [])]
    mv += [(e['t'], 'long') for e in (clip or {}).get('long_moves', [])]
    if mv:
        cat['movimento'] = sorted(mv)
    falhas = []
    for c, seq in cat.items():
        for k, n, t in repeticoes(sorted(seq), o.get(c, 0)):
            falhas.append(f'  {c}: "{k}" {n}x seguidas a partir de {t:.1f} s (limite {o[c]}): troque uma do meio')
    resumo = ', '.join(f'{c} {len(s)} ({len({k for _, k in s})} diferentes)' for c, s in cat.items())
    return falhas, resumo


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('modo', choices=['planeja', 'confere'])
    for k in ('tema', 'sfx', 'props', 'reel', 'clip', 'json', 'tempos'):
        a.add_argument('--' + k)
    a.add_argument('--dur', type=float); a.add_argument('--formato', default='reel')
    A = a.parse_args(); T = J(A.tema)
    if A.modo == 'planeja':
        r = planeja([float(x) for x in A.tempos.split(',')], A.dur, T, A.formato)
        s = json.dumps(r, indent=1, ensure_ascii=False)
        open(A.json, 'w').write(s) if A.json else print(s)
    else:
        f, r = confere(T, J(A.sfx), J(A.props), J(A.reel), J(A.clip))
        print('  ' + (r or 'nada para conferir')); print('\n'.join(f) if f else '  variação OK')
        sys.exit(2 if f else 0)
