#!/usr/bin/env python3
"""Processo de aprendizado da CIBO (regra em references/aprendizado.md). Quem roda é a CIBO, por baixo; o editor só conversa.

  aprendizado.py registra --sinal "o que aconteceu" --destino D [--skill S] [--cliente C] [--tipo T] [--proj PASTA] [--motivo "..."]
        D = licao | tema | trava | melhoria | candidata | skill-nova | formato | nada
        (licao/tema/nada nascem feitos; trava/melhoria/skill-nova/formato/candidata nascem abertos até `feito`)
  aprendizado.py colhe PROJ        fim do job: scripts criados no projeto e o que ainda não foi classificado
  aprendizado.py revisao           pauta da semana: travas, melhorias abertas, candidatas que repetiram, skills paradas
  aprendizado.py lista [--abertos] [-n 20]
  aprendizado.py feito ID [--nota "commit abc / teste X"]
Saída curta (até ~25 linhas)."""
import argparse, collections, json, os, re, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REF = AQUI.parent / 'references'
LOG = REF / 'aprendizado.jsonl'
REPO = AQUI.parents[2]
SKILLS = REPO / 'skills'
DESTINOS = ['licao', 'tema', 'trava', 'melhoria', 'candidata', 'skill-nova', 'formato', 'nada']
ABRE = {'trava', 'melhoria', 'candidata', 'skill-nova', 'formato'}
CODIGO = {'.py', '.mjs', '.js', '.ts', '.tsx', '.sh', '.ps1', '.swift'}
PULA = {'node_modules', '.venv', 'public', '__pycache__', '.git', 'tmp', 'mfa'}
HOJE = time.strftime('%Y-%m-%d')


def load():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]


def save(rows):
    LOG.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def registra(a):
    rows = load()
    nid = max([r['id'] for r in rows] or [0]) + 1
    r = {'id': nid, 'data': HOJE, 'sinal': a.sinal, 'destino': a.destino, 'skill': a.skill, 'cliente': a.cliente,
         'tipo': a.tipo, 'proj': a.proj, 'motivo': a.motivo, 'status': 'aberto' if a.destino in ABRE else 'feito'}
    rows.append(r); save(rows)
    print(f'#{nid} {a.destino}' + (f' ({a.skill})' if a.skill else '') + (f' tipo {a.tipo}' if a.tipo else '') + f': {a.sinal[:80]}')
    if a.destino == 'candidata' and a.tipo:
        c = candidatas(rows).get(a.tipo)
        if c and c['jobs'] >= 2:
            print(f'!! "{a.tipo}" já apareceu em {c["jobs"]} jobs ({", ".join(sorted(c["clientes"])) or "?"}): confira os critérios da '
                  f'seção 3 de aprendizado.md e proponha formato do reel-motion ou skill nova na revisão')


def candidatas(rows):
    out = {}
    for r in rows:
        if r['destino'] == 'candidata' and r.get('tipo'):
            c = out.setdefault(r['tipo'], {'jobs': set(), 'clientes': set(), 'ids': [], 'aberto': False})
            c['jobs'].add(r.get('proj') or f"#{r['id']}"); c['clientes'].add(r.get('cliente') or '')
            c['ids'].append(r['id']); c['aberto'] |= r['status'] == 'aberto'
    for c in out.values():
        c['jobs'] = len(c['jobs']); c['clientes'].discard('')
    return out


def colhe(proj):
    P = Path(proj).expanduser().resolve()
    if not P.exists():
        sys.exit(f'projeto não encontrado: {P}')
    ja = {r.get('sinal', '') for r in load()} | {str(r.get('proj')) for r in load()}
    scripts = []
    for f in P.rglob('*'):
        if f.is_file() and f.suffix in CODIGO and not (set(f.relative_to(P).parts) & PULA):
            scripts.append(f)
    print(f'{P.name}: {len(scripts)} script(s) criados no job')
    for f in sorted(scripts, key=lambda x: -x.stat().st_size)[:15]:
        linhas = sum(1 for _ in open(f, errors='ignore'))
        marca = ' (já registrado)' if str(f) in ja or f.name in ' '.join(ja) else ''
        print(f'  {f.relative_to(P)}  {linhas} linhas{marca}')
    if len(scripts) > 15:
        print(f'  … e mais {len(scripts) - 15}')
    print('Para cada script e cada correção do job, siga a árvore de aprendizado.md seção 2 e registre:\n'
          '  resolve etapa que já existe → --destino melhoria --skill <skill>; trabalho que nenhuma skill cobre → --destino candidata '
          '--tipo <nome>; caso único → nada (não precisa registrar).')
    # biblioteca geral (sem cliente) no Drive da GBrand: atualiza sozinha no fim do job (editor, 27/11/2026)
    r = subprocess.run([sys.executable, str(AQUI / 'biblioteca.py'), 'envia'], capture_output=True, text=True)
    print('biblioteca: ' + ((r.stdout.strip().splitlines() or [''])[-1] or r.stderr.strip()[-200:]))


def dias(data):
    try:
        return int((time.time() - time.mktime(time.strptime(data, '%Y-%m-%d'))) // 86400)
    except ValueError:
        return 0


def revisao():
    rows = load()
    print(f'REVISÃO DE APRENDIZADO — {HOJE}')
    # 1. erros repetidos (feedback.py)
    r = subprocess.run([sys.executable, str(AQUI / 'feedback.py'), 'repetidos'], capture_output=True, text=True)
    linhas = [l for l in r.stdout.splitlines() if l.strip()]
    print('1. Erros que repetem (correções):')
    for l in linhas[:8]:
        print('   ' + l)
    # 2. abertos por destino
    ab = [x for x in rows if x['status'] == 'aberto' and x['destino'] != 'candidata']
    print(f'2. Melhorias e travas abertas: {len(ab)}')
    for x in sorted(ab, key=lambda x: x['data'])[:8]:
        print(f"   #{x['id']} {x['destino']} {x.get('skill') or ''} ({dias(x['data'])} dias): {x['sinal'][:70]}")
    # 3. candidatas
    cs = candidatas(rows)
    print('3. Trabalhos sem skill (candidatas):' + ('' if cs else ' nenhuma'))
    for t, c in sorted(cs.items(), key=lambda kv: -kv[1]['jobs']):
        acao = 'REPETIU: decidir formato do reel-motion ou skill nova (critérios seção 3)' if c['jobs'] >= 2 else 'esperar repetir'
        if c['aberto']:
            print(f"   {t}: {c['jobs']} job(s), clientes {', '.join(sorted(c['clientes'])) or '?'} → {acao}")
    # 4. skills paradas
    paradas = []
    for sk in sorted(p for p in SKILLS.iterdir() if (p / 'SKILL.md').exists()):
        d = subprocess.run(['git', '-C', str(REPO), 'log', '-1', '--format=%cs', '--', str(sk.relative_to(REPO))],
                           capture_output=True, text=True).stdout.strip()
        if d and dias(d) > 60:
            paradas.append((dias(d), sk.name))
    print(f'4. Skills sem mudança há mais de 60 dias: {len(paradas)}' + (' → ' + ', '.join(f'{n} ({d}d)' for d, n in sorted(paradas, reverse=True)[:6]) if paradas else ''))
    print('   (sem uso e sem cliente ativo → propor aposentar; em uso → tudo bem)')
    # 5. o que o editor ensinou na semana
    sem = [x for x in rows if dias(x['data']) <= 7]
    cont = collections.Counter(x['destino'] for x in sem)
    print('5. Aprendido nos últimos 7 dias: ' + (', '.join(f'{k} {v}' for k, v in cont.most_common()) or 'nada registrado'))
    print('Escolha até 2 itens (o que mais repete primeiro), faça fora de produção com teste e marque `aprendizado.py feito ID`.')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('registra')
    p.add_argument('--sinal', required=True); p.add_argument('--destino', required=True, choices=DESTINOS)
    for k in ('skill', 'cliente', 'tipo', 'proj', 'motivo'):
        p.add_argument('--' + k)
    p = sp.add_parser('colhe'); p.add_argument('proj')
    sp.add_parser('revisao')
    p = sp.add_parser('lista'); p.add_argument('--abertos', action='store_true'); p.add_argument('-n', type=int, default=20)
    p = sp.add_parser('feito'); p.add_argument('id', type=int); p.add_argument('--nota', default='')
    a = ap.parse_args()
    if a.cmd == 'registra':
        registra(a)
    elif a.cmd == 'colhe':
        colhe(a.proj)
    elif a.cmd == 'revisao':
        revisao()
    elif a.cmd == 'lista':
        rows = [r for r in load() if not a.abertos or r['status'] == 'aberto'][-a.n:]
        for r in rows:
            print(f"#{r['id']} {r['data']} {r['destino']:10} {r['status']:6} {r.get('skill') or r.get('tipo') or ''}: {r['sinal'][:80]}")
    elif a.cmd == 'feito':
        rows = load()
        for r in rows:
            if r['id'] == a.id:
                r['status'] = 'feito'; r['feito_em'] = HOJE; r['nota'] = a.nota
                save(rows); print(f'#{a.id} feito'); return
        sys.exit(f'#{a.id} não existe')


if __name__ == '__main__':
    main()
