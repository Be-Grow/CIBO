#!/usr/bin/env python3
"""Biblioteca de aprendizado GERAL da CIBO (sem nome de cliente), para ficar no Drive compartilhado.

  biblioteca.py envia                   fim do job: regera e copia ao Drive (só se nenhum nome de cliente sobrar)
  biblioteca.py exporta [--saida DIR]   gera a biblioteca (rascunho local; NÃO envia ao Drive)
  biblioteca.py consulta TERMO... [-n 6] busca lições, regras e scripts antes de editar
  biblioteca.py nomes                   mostra os nomes que serão trocados por "cliente"

A biblioteca tem: regras/ (md), licoes.jsonl (travas, melhorias, candidatas), erros.jsonl (correções por padrão),
padroes.json, scripts.md (índice dos scripts das skills) e INDICE.json (usado pela consulta).
No Drive: aprendizado/universal/ (isto, sem nome de cliente) e aprendizado/clientes/<pasta>/ (lições, rubrica, briefing e
tema de cada cliente da GBrand, marcado com "drive": "<pasta>" no client-registry.json). Clientes sem "drive" não sobem.
Saída curta."""
import argparse, json, os, re, sys, unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REF = AQUI.parent / 'references'
REPO = AQUI.parents[2]
SKILLS = REPO / 'skills'
BASE_PADRAO = Path.home() / 'Library/CloudStorage/GoogleDrive-assessoriagbrand@gmail.com/Meu Drive/CLIENTES/AGENTE_DE_EDIÇÃO/aprendizado'
BASE = Path(os.environ['CIBO_BIBLIOTECA']) if os.environ.get('CIBO_BIBLIOTECA') else BASE_PADRAO
DRIVE = BASE / 'universal'       # vale para todo cliente, sem nome de cliente
CLIENTES_DRIVE = BASE / 'clientes'  # preferências de cada cliente da GBrand (registro com "drive": "<pasta>")
ARQS_CLIENTE = ['licoes.md', 'rubrica.md', 'briefing.md']
SAIDA = Path('/Volumes/SSD/CIBO/biblioteca_staging')
LOCAL = SAIDA
DESTINOS_GERAIS = {'trava', 'melhoria', 'candidata', 'skill-nova', 'formato'}
EXTRAS = ['francomano', 'daher', 'jansen', 'gbrand', 'be grow', 'begrow', 'growth leaders', 'growth-leaders', 'lpa',
          'angelica', 'autismo-cast', 'autismo cast', 'confea', 'sebrae', 'histórias do porto', 'historias do porto', 'podacontecer', 'insight', 'daniel', 'dannyel', 'marcos barros', 'barros', 'lula filho', 'inge weiser', 'weiser', 'fiema', 'shein', 'hotmart', 'zeo', 'turi', 'ita']
COMUNS = {'ita', 'lpa'}  # curtos demais: só casam como palavra inteira


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def nomes():
    ns = set(EXTRAS)
    reg = json.loads((REF / 'client-registry.json').read_text())
    for k, v in reg.items():
        ns.add(k)
        ns.update(k.split('-'))
        ns.update(v.get('aliases', []))
    for f in ('aprendizado.jsonl', 'feedback.jsonl'):
        for l in (REF / f).read_text().splitlines():
            try:
                c = json.loads(l).get('cliente')
            except Exception:
                continue
            if c and c != 'cibo':
                ns.add(c)
                ns.update(c.split('-'))
    ns = {n.strip() for n in ns if n and len(n.strip()) >= 3}
    ns -= {'cibo', 'dr', 'de', 'cast', 'hub', 'content', 'produto', 'cortes'}
    return sorted(ns, key=len, reverse=True)


def regex_nomes():
    partes = [re.escape(n) for n in nomes()]
    return re.compile(r'(?<![\w])(' + '|'.join(partes) + r')(?![\w])', re.I)


RX = None


def limpa(t):
    """troca nome de cliente por 'cliente' (sem acento, igual ao texto original) e esconde caminhos de projeto"""
    global RX
    if t is None:
        return t
    if RX is None:
        RX = regex_nomes()
    t = re.sub(r'/(?:Volumes|Users)/[^\s"\']+', '<caminho>', t)
    # compara sem acento: aplica no texto original e no normalizado
    t = RX.sub('cliente', t)
    n = norm(t)
    if n != t.lower() and RX.search(n):
        # nome com acento no original (ex.: João): troca por posição
        for m in reversed(list(RX.finditer(n))):
            t = t[:m.start()] + 'cliente' + t[m.end():]
    t = re.sub(r'\bEP\.? ?\d+\b', 'episódio', t)
    t = re.sub(r'(cliente[\s,/&e-]+){2,}cliente', 'cliente', t)
    return t


def jl(p):
    out = []
    for l in p.read_text().splitlines():
        if l.strip().startswith('{'):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def indice_scripts():
    linhas = ['# Scripts das skills (quando usar)\n']
    itens = []
    clientes = set(json.loads((REF / 'client-registry.json').read_text()))
    for sk in sorted(SKILLS.iterdir()):
        sc = sk / 'scripts'
        if not sc.is_dir() or sk.name in clientes:  # skill de cliente não entra na biblioteca geral
            continue
        for f in sorted(sc.glob('*.py')):
            doc = ''
            try:
                m = re.search(r'^(?:#!.*\n)?\s*(?:"""|\'\'\')(.+?)(?:"""|\'\'\')', f.read_text(errors='ignore'), re.S)
                doc = (m.group(1).strip().splitlines()[0] if m else '')
            except Exception:
                pass
            doc = limpa(doc)
            if doc:
                linhas.append(f'- `{sk.name}/scripts/{f.name}` — {doc}')
                itens.append({'tipo': 'script', 'onde': f'{sk.name}/scripts/{f.name}', 'texto': doc})
    return '\n'.join(linhas) + '\n', itens


def exporta(saida):
    saida = Path(saida)
    (saida / 'regras').mkdir(parents=True, exist_ok=True)
    indice, trocas = [], 0
    # regras (md)
    for f in sorted((REF / 'regras').glob('*.md')) + [REF / 'regras-transversais.md', REF / 'aprendizado.md', REF / 'eficiencia.md']:
        txt = f.read_text()
        novo = limpa(txt)
        trocas += len(RX.findall(txt)) if RX else 0
        (saida / 'regras' / f.name).write_text(novo)
        # um item de índice por título de seção
        for sec in re.split(r'\n(?=#{1,3} )', novo):
            tit = sec.strip().splitlines()[0][:100] if sec.strip() else ''
            if tit.startswith('#'):
                indice.append({'tipo': 'regra', 'onde': f'regras/{f.name}', 'titulo': tit.lstrip('# '), 'texto': sec[:600]})
    # lições gerais
    ap = [d for d in jl(REF / 'aprendizado.jsonl') if d.get('destino') in DESTINOS_GERAIS]
    with open(saida / 'licoes.jsonl', 'w') as o:
        for d in ap:
            sk = d.get('skill')
            sk = 'cliente' if sk in json.loads((REF / 'client-registry.json').read_text()) else sk
            n = {'data': d.get('data'), 'destino': d.get('destino'), 'skill': sk, 'tipo': d.get('tipo'),
                 'sinal': limpa(d.get('sinal')), 'motivo': limpa(d.get('motivo')), 'status': d.get('status')}
            o.write(json.dumps(n, ensure_ascii=False) + '\n')
            indice.append({'tipo': 'licao', 'onde': 'licoes.jsonl', 'skill': n['skill'], 'texto': f"{n['sinal']} {n['motivo'] or ''}"})
    # erros por padrão (sem cliente, sem repetição)
    vistos, erros = set(), []
    for d in jl(REF / 'feedback.jsonl'):
        if not d.get('padrao'):
            continue
        t = limpa(d.get('texto'))
        ch = (d['padrao'], t)
        if ch in vistos:
            continue
        vistos.add(ch)
        erros.append({'categoria': d.get('categoria'), 'padrao': d['padrao'], 'skill': 'cliente' if d.get('skill') in json.loads((REF / 'client-registry.json').read_text()) else d.get('skill'), 'texto': t, 'acao': limpa(d.get('acao'))})
    with open(saida / 'erros.jsonl', 'w') as o:
        for e in erros:
            o.write(json.dumps(e, ensure_ascii=False) + '\n')
    pad = json.loads((REF / 'padroes.json').read_text())
    pad = json.loads(limpa(json.dumps(pad, ensure_ascii=False)))
    (saida / 'padroes.json').write_text(json.dumps(pad, ensure_ascii=False, indent=1))
    for k, v in pad.items():
        if isinstance(v, dict):
            indice.append({'tipo': 'padrao', 'onde': 'padroes.json', 'titulo': k, 'texto': f"{v.get('descricao', '')} | trava: {v.get('trava', '')}"})
    # scripts
    md, itens = indice_scripts()
    (saida / 'scripts.md').write_text(md)
    indice += itens
    (saida / 'INDICE.json').write_text(json.dumps(indice, ensure_ascii=False))
    print(f'biblioteca em {saida}: {len(ap)} lições, {len(erros)} erros, {len(itens)} scripts, {len(indice)} itens no índice')
    sobra = confere(saida)
    print('conferência de nomes:', 'nenhum nome de cliente sobrou' if not sobra else f'{len(sobra)} possíveis sobras (veja abaixo)')
    for s in sobra[:15]:
        print('  ', s)


def confere(saida):
    rx = regex_nomes()
    sobra = []
    for f in Path(saida).rglob('*'):
        if f.is_file() and f.suffix in {'.md', '.json', '.jsonl'}:
            for i, l in enumerate(f.read_text().splitlines(), 1):
                m = rx.search(l) or rx.search(norm(l))
                if m:
                    sobra.append(f'{f.relative_to(saida)}:{i}: …{l[max(0, m.start() - 30):m.end() + 30]}…')
    return sobra


def consulta(termos, n):
    base = DRIVE if DRIVE and (DRIVE / 'INDICE.json').exists() else LOCAL
    p = base / 'INDICE.json'
    if not p.exists():
        print('biblioteca ainda não gerada (rode `biblioteca.py exporta`)'); return
    idx = json.loads(p.read_text())
    ts = [norm(t) for t in termos if len(t) >= 3]
    pontos = []
    for it in idx:
        alvo = norm(' '.join(str(it.get(k, '')) for k in ('titulo', 'skill', 'texto', 'onde')))
        s = sum(alvo.count(t) + (3 if t in norm(str(it.get('titulo', ''))) else 0) for t in ts)
        if s:
            pontos.append((s, it))
    pontos.sort(key=lambda x: -x[0])
    if not pontos:
        print('nada na biblioteca para:', ' '.join(termos)); return
    print(f'da biblioteca ({base}):')
    for s, it in pontos[:n]:
        t = (it.get('titulo') or '') + (' — ' if it.get('titulo') else '') + re.sub(r'\s+', ' ', it.get('texto', ''))[:200]
        print(f"- [{it['tipo']}] {it['onde']}: {t}")


def envia():
    """fim do job: regera o rascunho e copia ao Drive. Autorização permanente do editor (27/11/2026, "Sim, liga") vale SÓ
    para esta biblioteca geral; recusa se sobrar nome de cliente. Não apaga nada no Drive."""
    if not BASE.parent.exists():
        print(f'Drive não montado ({BASE.parent}); biblioteca fica só no rascunho local'); return 1
    exporta(SAIDA)
    sobra = confere(SAIDA)
    if sobra:
        print(f'ENVIO RECUSADO: {len(sobra)} possível(is) nome(s) de cliente; acrescente em EXTRAS e rode de novo'); return 2
    pares = [(f, DRIVE / f.relative_to(SAIDA)) for f in sorted(SAIDA.rglob('*')) if f.is_file() and f.name != '.DS_Store']
    pares += pares_clientes()
    novos, mudou = copia(pares)
    if not novos and not mudou:
        print('Drive já estava em dia')
    else:
        print(f'enviado ao Drive: {len(novos)} novo(s), {len(mudou)} atualizado(s): ' + ', '.join(novos + mudou)[:300])
    return 0


def pasta_cliente(chave, reg):
    sk = reg.get('skill') or 'reel-motion'
    return SKILLS / 'reel-motion/references/clientes' / chave if sk == 'reel-motion' else SKILLS / sk / 'references'


def pares_clientes():
    """só clientes da GBrand: os que têm "drive" no registro. Preferência de cliente, com nome, na pasta dele."""
    reg = json.loads((REF / 'client-registry.json').read_text())
    pares = []
    for chave, r in reg.items():
        nome = r.get('drive')
        if not nome:
            continue
        src = pasta_cliente(chave, r)
        for a in ARQS_CLIENTE:
            if (src / a).exists():
                pares.append((src / a, CLIENTES_DRIVE / nome / a))
        tema = SKILLS / 'reel-motion/temas' / f'{chave}.json'
        if tema.exists():
            pares.append((tema, CLIENTES_DRIVE / nome / 'tema.json'))
    return pares


def copia(pares):
    import shutil
    novos, mudou = [], []
    for f, alvo in pares:
        rel = str(alvo.relative_to(BASE))
        if not alvo.exists():
            novos.append(rel)
        elif alvo.read_bytes() != f.read_bytes():
            mudou.append(rel)
        else:
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, alvo)
    return novos, mudou


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='c', required=True)
    sp.add_parser('envia')
    p = sp.add_parser('exporta'); p.add_argument('--saida', default=str(SAIDA))
    p = sp.add_parser('consulta'); p.add_argument('termos', nargs='+'); p.add_argument('-n', type=int, default=6)
    sp.add_parser('nomes')
    a = ap.parse_args()
    global RX
    if a.c == 'envia':
        RX = regex_nomes(); sys.exit(envia())
    if a.c == 'exporta':
        RX = regex_nomes(); exporta(a.saida)
    elif a.c == 'consulta':
        consulta(a.termos, a.n)
    else:
        print(', '.join(nomes()))


if __name__ == '__main__':
    main()
