#!/usr/bin/env python3
"""Arena (editor, 23/11/2026): SÓ a porta de entrada. O editor sobe o material de cada demanda numa pasta que ELE aponta (Drive, SSD,
onde for); a CIBO guarda essa pasta, uma vez por computador, em ~/.cibo/arena.json. Ao receber, a CIBO traz o material para a
organização DELA (projeto do cliente com a estrutura padrão) e a arena fica intocada. Quem roda é a CIBO; o editor só fala
("a minha arena é a pasta X", "tem demanda nova na arena", "pega a demanda da Fulana").

  arena.py define PASTA         guarda a arena deste computador (a pasta tem que existir; nada é criado)
  arena.py onde                 mostra a arena guardada
  arena.py projetos [PASTA]     onde a CIBO organiza os projetos (padrão no Mac: /Volumes/SSD/Movies/Edição/Mídia)
  arena.py lista [--todas]      demandas da arena (cada subpasta, ou <cliente>/<demanda>): cliente provável, arquivos, tamanho e
                                estado (nova / recebida → projeto); sem --todas, esconde as recebidas
  arena.py recebe DEMANDA [--cliente C] [--nome NOME]
                                cria o projeto em PROJETOS/<pasta do cliente>/<demanda> (estrutura do video-project-structure),
                                COPIA o material para 01_sources (vídeo/áudio), 02_transcripts (srt/vtt/txt), 07_manifests (pdf/docx
                                de briefing) e 03_assets (imagens, fontes, zip) e grava 07_manifests/origem_arena.json
Nunca move, apaga ou renomeia nada na arena: ela é do editor."""
import json, os, re, shutil, subprocess, sys, time, unicodedata
from pathlib import Path

CONF = Path(os.environ.get('CIBO_ARENA_CONF', Path.home() / '.cibo' / 'arena.json'))
AQUI = Path(__file__).resolve().parent
MIDIA = {'.mp4', '.mov', '.mxf', '.mkv', '.m4v', '.wav', '.mp3', '.m4a', '.aif', '.aiff', '.srt', '.vtt', '.jpg', '.jpeg', '.png',
         '.psd', '.pdf', '.txt', '.docx', '.ttf', '.otf', '.zip'}


def le():
    try:
        return json.loads(CONF.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def grava(d):
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')


def arena():
    a = le().get('arena')
    if not a:
        sys.exit('ARENA_NAO_DEFINIDA: pergunte ao editor qual pasta é a arena dele e rode `arena.py define PASTA`.')
    p = Path(a)
    if not p.is_dir():
        sys.exit(f'arena não encontrada: {p} (Drive desmontado, SSD fora ou pasta mudou?). Confirme com o editor.')
    return p


PROJ_PADRAO = '/Volumes/SSD/Movies/Edição/Mídia' if sys.platform == 'darwin' else ''
GAVETA = {**{e: '01_sources/masters' for e in ('.mp4', '.mov', '.mxf', '.mkv', '.m4v')},
          **{e: '01_sources/audio' for e in ('.wav', '.mp3', '.m4a', '.aif', '.aiff')},
          **{e: '02_transcripts' for e in ('.srt', '.vtt', '.txt')}, **{e: '07_manifests' for e in ('.pdf', '.docx')},
          **{e: '03_assets/brand' for e in ('.jpg', '.jpeg', '.png', '.psd', '.zip')}, **{e: '03_assets/fonts' for e in ('.ttf', '.otf')}}


def slug(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def cliente_provavel(nome):
    r = subprocess.run([sys.executable, str(AQUI / 'detect_client.py'), nome], capture_output=True, text=True)
    m = re.search(r'Cliente identificado:\s*(\S+)', r.stdout)
    return m.group(1) if m else None


def projetos():
    p = le().get('projetos') or os.environ.get('CIBO_PROJETOS') or PROJ_PADRAO
    if not p or not Path(p).is_dir():
        sys.exit(f'pasta de projetos da CIBO não definida ou fora ({p or "—"}): `arena.py projetos PASTA` (SSD conectado?)')
    return Path(p)


def pasta_cliente(base, k):
    """reaproveita a pasta que já existe para o cliente (nome ou apelido do client-registry); senão cria com o nome do cadastro"""
    try:
        reg = json.loads((AQUI.parent / 'references' / 'client-registry.json').read_text())
    except (OSError, ValueError):
        reg = {}
    nomes = {slug(k)} | {slug(x) for x in (reg.get(k, {}).get('aliases') or [])}
    for d in base.iterdir():
        if d.is_dir() and slug(d.name) in nomes:
            return d
    return base / k


def demandas(base):
    """subpasta com arquivos de mídia = demanda; se só tem subpastas, desce um nível (<cliente>/<demanda>)"""
    out = []
    for d in sorted(x for x in base.iterdir() if x.is_dir() and not x.name.startswith('.')):
        arqs = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in MIDIA]
        subs = [x for x in d.iterdir() if x.is_dir() and not x.name.startswith('.')]
        if arqs or not subs:
            out.append(d)
        else:
            out += sorted(subs)
    return out


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('define', 'onde', 'lista', 'recebe', 'projetos'):
        sys.exit(__doc__)
    d = le()
    if a[0] == 'define':
        p = Path(' '.join(a[1:])).expanduser()
        if not p.is_dir():
            sys.exit(f'pasta não existe: {p}. Não crio pasta na arena: peça ao editor o caminho certo.')
        d['arena'] = str(p.resolve()); d['definida_em'] = time.strftime('%Y-%m-%d'); grava(d)
        print(f'arena deste computador: {d["arena"]}')
    elif a[0] == 'onde':
        print(d.get('arena') or 'arena ainda não definida')
    elif a[0] == 'projetos':
        if len(a) > 1:
            p = Path(' '.join(a[1:])).expanduser()
            if not p.is_dir(): sys.exit(f'pasta não existe: {p}')
            d['projetos'] = str(p.resolve()); grava(d)
        print(f'projetos da CIBO: {projetos()}')
    elif a[0] == 'lista':
        base = arena(); rec = d.get('recebidas', {}); n = 0
        for dem in demandas(base):
            rel = str(dem.relative_to(base))
            if rel in rec and '--todas' not in a:
                continue
            fs = [f for f in dem.rglob('*') if f.is_file() and not f.name.startswith('.')]
            gb = sum(f.stat().st_size for f in fs) / 2**30
            e = f'recebida → {rec[rel]}' if rel in rec else 'nova'
            print(f'{rel} | {e} | {len(fs)} arquivo(s), {gb:.1f} GB | cliente: {cliente_provavel(rel) or "? (pergunte)"}')
            n += 1
        print(f'{n} demanda(s) na arena' + ('' if '--todas' in a else ' (recebidas escondidas)'))
    elif a[0] == 'recebe':
        base = arena(); args = a[1:]
        op = lambda k: args[args.index(k) + 1] if k in args else None
        cli, nome = op('--cliente'), op('--nome')
        rel = ' '.join(x for i, x in enumerate(args) if not x.startswith('--') and (i == 0 or not args[i - 1].startswith('--')))
        dem = base / rel
        if not dem.is_dir():
            sys.exit(f'demanda não encontrada na arena: {rel}')
        cli = cli or cliente_provavel(rel)
        if not cli:
            sys.exit(f'não reconheci o cliente de "{rel}": pergunte ao editor e rode com --cliente')
        proj = pasta_cliente(projetos(), cli) / (nome or Path(rel).name)
        if (proj / '07_manifests' / 'origem_arena.json').exists():
            sys.exit(f'essa demanda já foi recebida em {proj}')
        subprocess.run([sys.executable, str(AQUI.parents[1] / 'video-project-structure/scripts/audit_structure.py'), '--root', str(proj),
                        '--init'], capture_output=True)
        copiados, pulados = [], []
        for f in sorted(dem.rglob('*')):
            if not f.is_file() or f.name.startswith('.'):
                continue
            g = GAVETA.get(f.suffix.lower())
            if not g:
                pulados.append(f.name); continue
            dst = proj / g / f.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not (dst.exists() and dst.stat().st_size == f.stat().st_size):
                shutil.copy2(f, dst)
            copiados.append(f'{g}/{f.name}')
        (proj / '07_manifests').mkdir(parents=True, exist_ok=True)
        (proj / '07_manifests' / 'origem_arena.json').write_text(json.dumps(
            {'arena': str(base), 'demanda': rel, 'cliente': cli, 'recebida_em': time.strftime('%Y-%m-%d %H:%M'),
             'arquivos': copiados, 'nao_copiados': pulados}, ensure_ascii=False, indent=1), encoding='utf-8')
        d.setdefault('recebidas', {})[rel] = str(proj); grava(d)
        print(f'projeto: {proj}\n{len(copiados)} arquivo(s) copiados' + (f'; não copiados (tipo desconhecido): {", ".join(pulados[:5])}' if pulados else ''))


if __name__ == '__main__':
    main()
