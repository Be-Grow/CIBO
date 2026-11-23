#!/usr/bin/env python3
"""Caixa de entrada de aprendizado (23/11/2026): o editor joga material solto numa pasta do cliente e a CIBO estuda.

Pasta de entrada: Meu Drive/CIBO/aprender/<cliente>/ (qualquer um joga lá: fonte, logo, manual em PDF, prints, vídeo de
referência, links.txt com perfis/posts, notas .txt/.md). Trabalho pesado (downloads, análises) fica no SSD, em
/Volumes/SSD/CIBO/aprender/<cliente>/<data>/. Nada entra no motor sem aprovação: sai uma FICHA + proposta.json.

  aprende.py CLIENTE [--novo] [--alias "a,b"] [--base andreia] [--rapido] [--posts 6] [--nao-move]
        lê o que chegou na pasta, analisa e escreve ficha.md + proposta.json (cópia da ficha vai para a pasta do Drive)
        --novo   cliente que ainda não existe: cadastra no client-registry (motor reel-motion), cria o tema a partir de
                 --base, a rubrica e o licoes.md em reel-motion/references/clientes/<cliente>/ e a pasta no Drive
        --rapido vídeos sem separar voz/música, transcrever e OCR de legenda (bem mais rápido, mede menos)
  aprende.py CLIENTE --aplica [proposta.json]
        aplica a proposta APROVADA (apague antes do proposta.json o que o editor recusou): backup do tema e grava
  aprende.py CLIENTE --pasta
        só mostra/cria a pasta de entrada no Drive

O que vai para onde: fonte -> acervo (tipo fonte) + theme.fonts; logo/manual/prints -> paleta -> theme.colors;
vídeo -> briefing-criativo/analisa_referencia.py -> receita (theme.mediaFilter, legenda, montagem); links -> yt-dlp baixa os
últimos posts públicos e analisa em lote; notas -> lista de pedidos para virar lição (`licao.py add`).
Instagram que barrar sem login: CIBO_COOKIES="chrome" (ou "chromium:/caminho/do/perfil") usa o login do navegador;
nunca peça nem digite senha. Se ainda falhar, peça os vídeos baixados.
"""
import argparse, colorsys, copy, glob, json, os, re, shutil, subprocess, sys, time, unicodedata, zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SK = AQUI.parents[1]
REG = SK / 'client-router/references/client-registry.json'
TEMAS = SK / 'reel-motion/temas'
CLIENTES = SK / 'reel-motion/references/clientes'
ANALISA = SK / 'briefing-criativo/scripts/analisa_referencia.py'
ACERVO = SK / 'acervo/scripts/acervo.py'
WORK_RAIZ = Path(os.environ.get('CIBO_APRENDER_WORK', '/Volumes/SSD/CIBO/aprender'))
FONTE = {'.ttf', '.otf', '.woff', '.woff2'}
IMG = {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.gif', '.bmp', '.tif', '.tiff'}
VID = {'.mp4', '.mov', '.m4v', '.webm', '.mkv'}
TXT = {'.txt', '.md'}
HOJE = time.strftime('%Y-%m-%d')
RODADA = time.strftime('%Y-%m-%d_%H%M')   # uma pasta por rodada: rodar de novo não apaga proposta ainda não aplicada


def slug(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.split('(')[0].strip().lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def drive():
    if os.environ.get('CIBO_APRENDER'):
        return Path(os.environ['CIBO_APRENDER'])
    m = sorted(glob.glob(str(Path.home() / 'Library/CloudStorage/GoogleDrive-*/Meu Drive'))) + \
        sorted(glob.glob(str(Path.home() / 'Library/CloudStorage/GoogleDrive-*/My Drive')))
    if not m:
        sys.exit('Google Drive desktop não está montado (Library/CloudStorage). Abra o Drive ou use CIBO_APRENDER=PASTA.')
    return Path(m[0]) / 'CIBO' / 'aprender'


def registro():
    return json.loads(REG.read_text())


def acha_cliente(nome):
    """slug do client-registry pelo nome ou alias (mesma regra do feedback.py)"""
    base, reg = slug(nome), registro()
    for k, v in reg.items():
        if base == k or base in {slug(x) for x in v.get('aliases') or []}:
            return k
    return None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- cliente novo
def cria_cliente(nome, aliases, base):
    k = slug(nome)
    reg = registro()
    if k in reg:
        sys.exit(f'"{k}" já existe no client-registry: rode sem --novo')
    if not (TEMAS / f'{base}.json').exists():
        sys.exit(f'tema base "{base}" não existe em reel-motion/temas')
    if 'colors' not in json.loads((TEMAS / f'{base}.json').read_text()).get('theme', {}):
        sys.exit(f'tema "{base}" não tem theme.colors (o priscilla é o padrão interno do motor): escolha outro --base')
    reg[k] = {'aliases': sorted({nome.lower(), k, *[a.strip().lower() for a in aliases if a.strip()]}),
              'skill': 'reel-motion', 'tema': k}
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + '\n')
    t = json.loads((TEMAS / f'{base}.json').read_text())
    t['cliente'] = nome
    t['origem'] = f'criado por aprende.py em {HOJE} a partir do tema "{base}": cores, fontes e regras ainda são do base até ' \
                  f'aplicar a ficha (aprende.py {k} --aplica)'
    t['_base'] = base
    (TEMAS / f'{k}.json').write_text(json.dumps(t, ensure_ascii=False, indent=1) + '\n')
    d = CLIENTES / k
    d.mkdir(parents=True, exist_ok=True)
    if not (d / 'rubrica.md').exists():
        (d / 'rubrica.md').write_text(
            f'# Rubrica — {nome} (tema `{k}`)\n\nBase: ainda nenhum lote aprovado; preencha depois do 1º job (o que passou e o '
            'que reprovou).\n\n| Dimensão | Aprovado assim | Reprova se |\n|---|---|---|\n| Gancho | | |\n| Ritmo | | |\n'
            '| Legibilidade | | |\n| Identidade | | |\n')
    if not (d / 'licoes.md').exists():
        (d / 'licoes.md').write_text(f'# Lições — {nome}\n\nGostos e proibições do cliente, mais novas em cima (`licao.py add {k} "…"`).\n')
    print(f'cliente novo: {k} (registro + tema {k}.json a partir de {base} + rubrica/licoes em reel-motion/references/clientes/{k}/)')
    return k


# ---------------------------------------------------------------- fontes
def fontes(arqs, k, w):
    saida = []
    for z in [a for a in arqs if a.suffix.lower() == '.zip']:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                p = Path(n)
                if p.suffix.lower() in FONTE and not p.name.startswith('.') and '__MACOSX' not in n and '..' not in p.parts:
                    dst = w / 'fontes' / p.name; dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(zf.read(n)); arqs.append(dst)
    for f in [a for a in arqs if a.suffix.lower() in FONTE]:
        r = run(['fc-scan', '--format', '%{family[0]}|%{style[0]}|%{weight}|%{slant}\n', str(f)])
        fam, est, peso, incl = (r.stdout.splitlines() or ['?|?|80|0'])[0].split('|')[:4]
        r = run([sys.executable, str(ACERVO), 'add', str(f), '--type', 'fonte', '--client', k,
                 '--note', f'aprende.py {HOJE}', '--license', 'conferir licença com o cliente'])
        if r.returncode == 0:
            caminho = r.stdout.strip().split('  ')[-1]
        else:   # sem acervo: guarda no SSD (o original do Drive vai para lido/ e o tema não pode apontar para ele)
            dst = w / 'fontes' / f.name; dst.parent.mkdir(parents=True, exist_ok=True)
            if dst != f: shutil.copy2(f, dst)
            caminho = str(dst)
        saida.append({'familia': fam, 'estilo': est, 'peso_fc': int(float(peso or 80)), 'italico': incl not in ('0', ''),
                      'arquivo': caminho, 'acervo': r.returncode == 0})
    return saida


def propoe_fontes(fs):
    """theme.fonts no formato do motor; título = família mais pesada, legenda = a outra (conferir na folha)"""
    if not fs:
        return {}, []
    fams = {}
    for f in fs:
        fams.setdefault(f['familia'], []).append(f)
    entradas = []
    for fam, lst in fams.items():
        for f in lst:
            entradas.append({'family': fam, 'file': f['arquivo'], 'weight': '100 900' if 'variable' in f['arquivo'].lower()
                             or '-vf' in f['arquivo'].lower() else str(fc_peso(f['peso_fc'])),
                             'style': 'italic' if f['italico'] else 'normal'})
    ordem = sorted(fams, key=lambda n: -max(x['peso_fc'] for x in fams[n]))
    tit, leg = ordem[0], (ordem[1] if len(ordem) > 1 else ordem[0])
    prop = {'theme.fonts': entradas, 'theme.title.family': tit, 'theme.caption.family': leg, 'theme.label.family': leg}
    return prop, [f'título: {tit}; legenda e rótulos: {leg} (pela espessura; troque se for o contrário)']


def fc_peso(w):
    """peso do fontconfig -> CSS"""
    tab = [(0, 100), (40, 200), (50, 300), (80, 400), (100, 500), (180, 600), (200, 700), (205, 800), (210, 900)]
    return min(tab, key=lambda t: abs(t[0] - w))[1]


# ---------------------------------------------------------------- cores
def pixels(img):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(img), '-frames:v', '1', '-vf', 'scale=64:64:flags=area',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    b = r.stdout
    return [tuple(b[i:i + 3]) for i in range(0, len(b) - 2, 3)]


def hexa(c):
    return '#%02X%02X%02X' % tuple(int(x) for x in c)


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contraste(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paleta(imgs, hex_pdf):
    """cores dominantes (baldes de 16 níveis, juntando as próximas) + hex escritos no manual"""
    cont, soma = {}, {}
    for im in imgs:
        for p in pixels(im):
            q = tuple(v // 16 for v in p)
            cont[q] = cont.get(q, 0) + 1
            s = soma.setdefault(q, [0, 0, 0])
            for i in range(3): s[i] += p[i]
    cores = []   # cor = média real dos pixels do balde (não o centro do balde)
    for q, n in sorted(cont.items(), key=lambda x: -x[1]):
        c = tuple(round(v / n) for v in soma[q])
        if all(sum((a - b) ** 2 for a, b in zip(c, d['rgb'])) > 55 ** 2 for d in cores):
            cores.append({'rgb': c, 'n': n})
        if len(cores) >= 8:
            break
    tot = sum(cont.values()) or 1
    lst = [{'hex': h.upper(), 'rgb': rgb(h), 'fonte': 'manual', 'pct': None} for h in dict.fromkeys(hex_pdf)][:8]
    lst += [{'hex': hexa(c['rgb']), 'rgb': c['rgb'], 'fonte': 'imagem', 'pct': round(100 * c['n'] / tot)} for c in cores]
    return lst


def propoe_cores(lst):
    if len(lst) < 2:
        return {}, []
    sat = lambda c: colorsys.rgb_to_hsv(*[v / 255 for v in c['rgb']])[1]
    fundo = min(lst, key=lambda c: lum(c['rgb'])) if sum(lum(c['rgb']) < 0.2 for c in lst) >= len(lst) / 2 \
        else max(lst, key=lambda c: lum(c['rgb']))
    texto = max(lst, key=lambda c: contraste(c['rgb'], fundo['rgb']))
    resto = [c for c in lst if c is not fundo and c is not texto]
    destaque = max(resto, key=sat) if resto else texto
    claro = lum(fundo['rgb']) > 0.5
    ct = contraste(texto['rgb'], fundo['rgb']); cd = contraste(destaque['rgb'], fundo['rgb'])
    prop = {'theme.colors.paper': fundo['hex'], 'theme.colors.ink': texto['hex'], 'theme.colors.video': texto['hex'],
            'theme.colors.terra': destaque['hex'], 'theme.colors.peach': destaque['hex'], 'theme.colors.gold': destaque['hex'],
            'theme.colors.onAccent': fundo['hex'] if contraste(fundo['rgb'], destaque['rgb']) >= 3 else texto['hex']}
    notas = [f'fundo {fundo["hex"]} ({"claro" if claro else "escuro"}), texto {texto["hex"]} (contraste {ct:.1f}:1'
             + ('' if ct >= 4.5 else ' — BAIXO, legenda vai sofrer') + f'), destaque {destaque["hex"]} ({cd:.1f}:1 no fundo'
             + (')' if cd >= 3 else ' — fraco como texto: use em fundo de pílula/caixa, não em letra sobre o fundo)'),
             'as outras cores do tema (paper2, ink2, pill, bg, terraDark…) continuam do tema base: ajuste na folha de contato']
    return prop, notas


# ---------------------------------------------------------------- vídeos e redes
def analisa(v, out, rapido):
    if (out / 'estilo.json').exists():
        return json.loads((out / 'estilo.json').read_text())
    cmd = [sys.executable, str(ANALISA), str(v), '--out', str(out)] + (['--rapido'] if rapido else [])
    r = run(cmd, env={**os.environ, 'TMPDIR': str(out.parent.parent / 'tmp')})
    if r.returncode != 0 or not (out / 'estilo.json').exists():
        fim = ((r.stderr or r.stdout).strip().splitlines() or ['sem saída'])[-1]
        print(f'  !! análise falhou em {v.name}: {fim[:200]}')
        return None
    return json.loads((out / 'estilo.json').read_text())


def baixa(url, dst, n):
    dst.mkdir(parents=True, exist_ok=True)
    base = ['yt-dlp', '--no-progress', '--playlist-end', str(n), '-f', 'mp4/bestvideo*+bestaudio/best',
            '--merge-output-format', 'mp4', '--no-overwrites', '-o', str(dst / '%(uploader_id)s_%(id)s.%(ext)s')]
    antes = set(dst.glob('*.mp4'))
    r = run(base + [url], timeout=900)
    if r.returncode != 0 and os.environ.get('CIBO_COOKIES'):
        r = run(base + ['--cookies-from-browser', os.environ['CIBO_COOKIES'], url], timeout=900)
    novos = sorted(set(dst.glob('*.mp4')) - antes) or sorted(dst.glob('*.mp4'))
    erro = '' if novos else ((r.stderr or '').strip().splitlines() or ['sem vídeo'])[-1][:200]
    return novos, erro


def med(xs):
    xs = sorted(x for x in xs if x is not None)
    return None if not xs else (xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2)


def resumo_estilo(ests):
    ests = [e for e in ests if e]
    if not ests:
        return {}
    lg = [e.get('legenda') or {} for e in ests]
    lg = [x for x in lg if x.get('achou')]
    r = {'videos': len(ests), 'duracao_s': med([e['duracao_s'] for e in ests]),
         'plano_mediano_s': med([e['ritmo']['plano_mediano_s'] for e in ests]),
         'cortes_por_10s': med([e['ritmo']['cortes_por_10s'] for e in ests]),
         'rosto_altura_pct': med([e['rosto'].get('altura_mediana_pct_do_quadro') for e in ests]),
         'saturacao': med([e['cor']['saturacao'] for e in ests]), 'contraste': med([e['cor']['contraste'] for e in ests]),
         'formato': max({e['formato'] for e in ests}, key=[e['formato'] for e in ests].count)}
    if lg:
        r['legenda'] = {'y_pct': med([x['y_centro_pct'] for x in lg]), 'altura_letra_pct': med([x['altura_letra_pct'] for x in lg]),
                        'palavras_por_bloco': med([x['palavras_por_bloco'] for x in lg]),
                        'minusculas_pct': med([x['minusculas_pct'] for x in lg]), 'de': len(lg)}
    r['montagem'] = sorted({m.split(':')[0].split(' ')[0] for e in ests for m in e.get('receita', {}).get('montagem_davinci', [])})
    return r


def propoe_estilo(r):
    if not r:
        return {}, []
    s, c = r['saturacao'], r['contraste']
    prop = {'theme.mediaFilter': f'saturate({min(1.3, max(0.4, s / 0.45)):.2f}) contrast({min(1.4, max(0.8, c / 0.62)):.2f})'}
    notas = [f'{r["videos"]} vídeo(s), {r["formato"]}, ~{r["duracao_s"]:.0f} s; plano mediano {r["plano_mediano_s"]} s, '
             f'{r["cortes_por_10s"]} cortes/10 s' + (f'; rosto ocupa ~{r["rosto_altura_pct"]:.0f}% da altura' if r.get('rosto_altura_pct') else '')]
    if r.get('legenda'):
        L = r['legenda']
        caixa = 'minúscula' if L['minusculas_pct'] > 85 else 'mista' if L['minusculas_pct'] > 30 else 'MAIÚSCULA'
        notas.append(f'legenda em {L["de"]} deles: centro a {L["y_pct"]:.0f}% da altura, letra {L["altura_letra_pct"]:.1f}% do quadro, '
                     f'{L["palavras_por_bloco"]} palavras por bloco, {caixa}')
        prop['theme.caption.upper'] = caixa == 'MAIÚSCULA'
    if r.get('montagem'):
        notas.append('efeitos de montagem vistos (sem chave no tema, entram como regra/DaVinci): ' + ', '.join(r['montagem']))
    return prop, notas


# ---------------------------------------------------------------- ficha
def ficha(k, w, achados, prop, notas_cli, avisos):
    L = [f'# Ficha de aprendizado — {k} ({HOJE})', '',
         f'Proposta para aplicar: `{w / "proposta.json"}`. Apague dela o que o editor recusar e rode '
         f'`aprende.py {k} --aplica`. Nada foi aplicado ainda.', '']
    for titulo, linhas in achados:
        if linhas:
            L += [f'## {titulo}', ''] + [f'- {x}' for x in linhas] + ['']
    if notas_cli:
        L += ['## Pedidos do cliente (vire lição: `licao.py add ' + k + ' "…"`)', ''] + [f'- {x}' for x in notas_cli] + ['']
    if avisos:
        L += ['## Atenção', ''] + [f'- {x}' for x in avisos] + ['']
    L += ['## Mudanças propostas no tema', '', '| chave | valor |', '|---|---|']
    L += [f'| `{a}` | {json.dumps(b, ensure_ascii=False)[:90]} |' for a, b in prop.items() if a != 'theme.fonts']
    if 'theme.fonts' in prop:
        L.append(f'| `theme.fonts` | {len(prop["theme.fonts"])} arquivo(s): ' + ', '.join(sorted({f["family"] for f in prop["theme.fonts"]})) + ' |')
    return '\n'.join(L) + '\n'


def aprende(k, a):
    pasta = drive() / k
    pasta.mkdir(parents=True, exist_ok=True)
    w = WORK_RAIZ / k / RODADA
    (w / 'tmp').mkdir(parents=True, exist_ok=True)
    os.environ['TMPDIR'] = str(w / 'tmp')
    arqs = [p for p in pasta.rglob('*') if p.is_file() and not p.name.startswith(('.', 'FICHA_'))
            and 'lido' not in p.relative_to(pasta).parts and p.name != 'Icon\r']
    if not arqs:
        print(f'pasta vazia: {pasta}\njogue lá fontes, logo/manual, prints, vídeos de referência, links.txt e notas, e rode de novo')
        return
    print(f'{len(arqs)} arquivo(s) em {pasta}')
    achados, prop, avisos, notas_cli, hex_pdf, imgs, links = [], {}, [], [], [], [], []

    for p in arqs:
        s = p.suffix.lower()
        if s == '.pdf':
            (w / 'pdf').mkdir(exist_ok=True)
            run(['pdftoppm', '-r', '30', '-png', '-l', '6', str(p), str(w / 'pdf' / p.stem)])
            imgs += sorted((w / 'pdf').glob(p.stem + '*.png'))
            t = run(['pdftotext', '-l', '30', str(p), '-']).stdout
            hex_pdf += re.findall(r'#[0-9A-Fa-f]{6}\b', t)
            fam = sorted(set(re.findall(r'\b(?:fonte|tipografia|font|typeface)\s*[:\-–]?\s*([A-Z][\w ]{2,30})', t, re.I)))
            if fam: achados.append(('Manual: fontes citadas', fam[:6]))
        elif s in IMG:
            imgs.append(p)
        elif s in TXT:
            for l in p.read_text(errors='replace').splitlines():
                l = l.strip().lstrip('-*• ').strip()
                if not l: continue
                (links if re.match(r'https?://', l) else notas_cli).append(l)

    fs = fontes(arqs, k, w)
    if fs:
        pf, nf = propoe_fontes(fs); prop.update(pf)
        achados.append(('Fontes', [f'{f["familia"]} {f["estilo"]}' + ('' if f['acervo'] else ' (NÃO entrou no acervo)') for f in fs] + nf))
        avisos.append('fonte paga só entra no tema com licença do cliente (o acervo marcou "conferir licença")')
    if imgs or hex_pdf:
        pal = paleta(imgs, hex_pdf)
        pc, nc = propoe_cores(pal); prop.update(pc)
        achados.append(('Cores', [f'{c["hex"]} ({c["fonte"]}' + (f', {c["pct"]}%' if c['pct'] is not None else '') + ')' for c in pal] + nc))

    vids = [p for p in arqs if p.suffix.lower() in VID]
    ests = []
    for v in vids:
        print(f'  analisando {v.name}…', flush=True)
        ests.append(analisa(v, w / 'ref' / slug(v.stem), a.rapido))
    if vids:
        pe, ne = propoe_estilo(resumo_estilo(ests))
        prop.update(pe); achados.append(('Vídeos de referência', ne + [f'receitas completas: {w / "ref"}/*/relatorio.md']))

    rede = []
    for u in dict.fromkeys(links):
        print(f'  baixando {u[:70]}…', flush=True)
        try:
            novos, erro = baixa(u, w / 'rede' / slug(re.sub(r'https?://(www\.)?', '', u))[:60], a.posts)
        except subprocess.TimeoutExpired:
            novos, erro = [], 'demorou demais (15 min)'
        if erro:
            avisos.append(f'não baixou {u}: {erro}. Login: CIBO_COOKIES="chrome"; senão peça os vídeos e jogue na pasta')
        for v in novos[:a.posts]:
            rede.append(analisa(v, w / 'rede_ref' / slug(v.stem), True))
    if rede:
        rr = resumo_estilo(rede)
        _, nr = propoe_estilo(rr)
        achados.append(('Padrão do perfil (posts baixados, análise rápida)', nr))
        if not vids:
            prop.update(propoe_estilo(rr)[0])

    (w / 'proposta.json').write_text(json.dumps({'cliente': k, 'data': HOJE, 'aplicar': prop}, ensure_ascii=False, indent=1) + '\n')
    txt = ficha(k, w, achados, prop, notas_cli, avisos)
    (w / 'ficha.md').write_text(txt)
    shutil.copy2(w / 'ficha.md', pasta / f'FICHA_{RODADA}.md')
    if not a.nao_move:
        lido = pasta / 'lido' / RODADA
        for p in arqs:
            if p.exists() and pasta in p.parents:
                dst = lido / p.relative_to(pasta); dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(p), dst)
    print(f'ficha: {w / "ficha.md"} (cópia no Drive: FICHA_{RODADA}.md)')
    print(f'{len(prop)} mudança(s) propostas; {len(avisos)} aviso(s). Mostre a ficha ao editor; aprovado -> aprende.py {k} --aplica')


# ---------------------------------------------------------------- aplicar
def aplica(k, arq):
    if not arq:
        cand = sorted((WORK_RAIZ / k).glob('*/proposta.json'))
        if not cand: sys.exit(f'nenhuma proposta em {WORK_RAIZ / k}: rode aprende.py {k} antes')
        arq = cand[-1]
    P = json.loads(Path(arq).read_text())
    tema_nome = registro().get(k, {}).get('tema') or k
    tp = TEMAS / f'{tema_nome}.json'
    if not tp.exists(): sys.exit(f'tema {tp.name} não existe (cliente novo: aprende.py "{k}" --novo)')
    t = json.loads(tp.read_text()); antes = copy.deepcopy(t)
    for chave, val in P['aplicar'].items():
        partes = chave.split('.'); d = t
        for p in partes[:-1]:
            d = d.setdefault(p, {})
        d[partes[-1]] = val
    if t == antes:
        print('nada muda no tema'); return
    bak = tp.with_name(f'{tp.name}.bak-{time.strftime("%Y%m%d-%H%M")}')
    shutil.copy2(tp, bak)
    t['origem'] = (t.get('origem', '') + f' | aprende.py {P["data"]} aplicado em {HOJE}').strip(' |')
    tp.write_text(json.dumps(t, ensure_ascii=False, indent=1) + '\n')
    for chave, val in P['aplicar'].items():
        d = antes
        for p in chave.split('.'):
            d = d.get(p) if isinstance(d, dict) else None
        if d != val and chave != 'theme.fonts':
            print(f'  {chave}: {json.dumps(d, ensure_ascii=False)[:40]} -> {json.dumps(val, ensure_ascii=False)[:40]}')
    print(f'tema {tp.name} atualizado (backup {bak.name}). Confira numa folha de contato antes do próximo job.')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cliente'); ap.add_argument('--novo', action='store_true'); ap.add_argument('--alias', default='')
    ap.add_argument('--base', default='andreia'); ap.add_argument('--rapido', action='store_true')
    ap.add_argument('--posts', type=int, default=6); ap.add_argument('--nao-move', action='store_true')
    ap.add_argument('--aplica', nargs='?', const='', default=None); ap.add_argument('--pasta', action='store_true')
    a = ap.parse_args()
    k = acha_cliente(a.cliente)
    if a.novo:
        k = k and sys.exit(f'"{a.cliente}" já é o cliente "{k}": rode sem --novo') or cria_cliente(a.cliente, a.alias.split(','), a.base)
    elif not k:
        sys.exit(f'cliente "{a.cliente}" não está no client-registry. É novo? aprende.py "{a.cliente}" --novo [--alias "x,y"]')
    if a.pasta:
        p = drive() / k; p.mkdir(parents=True, exist_ok=True); print(p); return
    if a.aplica is not None:
        aplica(k, a.aplica); return
    aprende(k, a)


if __name__ == '__main__':
    main()
