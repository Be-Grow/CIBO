#!/usr/bin/env python3
"""Ciclo de aprendizado por cliente (20/10/2026). Depois de cada entrega, UMA pergunta ao editor: "o que você mudaria?".
A resposta entra em `references/licoes.md` do cliente; antes de editar, a lição é lida (junto com a rubrica).
Onde fica: `<skill do cliente>/references/` se o cliente tem skill própria; senão `reel-motion/references/clientes/<cliente>/`.
Diferença do feedback.py: feedback = correção que mudou uma skill; lição = gosto do cliente/editor para o próximo job.
  licao.py ler <cliente>                          imprime rubrica (resumo) e lições, as mais novas primeiro
  licao.py add <cliente> "<resposta>" [--projeto <pasta>] [--reel r03]
  licao.py onde <cliente>                         só o caminho"""
import json, sys, time
from pathlib import Path

SK = Path.home() / '.claude/skills'
REG = json.load(open(SK / 'client-router/references/client-registry.json'))


def slug(c):
    c = c.strip().lower()
    for k, v in REG.items():
        if c == k or c in [a.lower() for a in (v.get('aliases') or [])]:
            return k
    return c.replace(' ', '-')


def pasta(c):
    s = slug(c)
    return (SK / s / 'references') if (SK / s / 'SKILL.md').exists() else (SK / 'reel-motion/references/clientes' / s), s


a = sys.argv[1:]
if len(a) < 2 or a[0] not in ('ler', 'add', 'onde'):
    sys.exit(__doc__)
D, S = pasta(a[1]); L = D / 'licoes.md'
if a[0] == 'onde':
    print(L)
elif a[0] == 'add':
    txt = a[2].strip().replace('\n', ' ')
    ex = dict(zip(a[3::2], a[4::2]))
    D.mkdir(parents=True, exist_ok=True)
    if not L.exists():
        L.write_text(f'# Lições — {S}\n\nResposta do editor a "o que você mudaria?" depois de cada entrega. Mais nova em cima.\n'
                     'Leia antes de editar (client-router). Lição que vira regra fixa sobe para a rubrica ou para a skill.\n\n')
    cab, corpo = L.read_text().split('\n\n', 2)[:2], L.read_text().split('\n\n', 2)[2:]
    onde = ' '.join(x for x in (ex.get('--projeto', ''), ex.get('--reel', '')) if x)
    linha = f"- {time.strftime('%Y-%m-%d')}{f' ({onde})' if onde else ''}: {txt}\n"
    L.write_text('\n\n'.join(cab) + '\n\n' + linha + (corpo[0] if corpo else ''))
    print('gravado em', L, '— leve ao ~/CIBO (commit e push) no mesmo turno')
else:
    R = D / 'rubrica.md'
    if R.exists():
        print('rubrica:', R)
    print(L.read_text() if L.exists() else f'sem lições ainda ({L})')
