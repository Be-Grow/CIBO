#!/usr/bin/env python3
"""Motor genérico de reel com tela dividida (painel de motion + pessoa), etapa por etapa,
a partir de PROJ/04_work/rNN/reel.json + segs.json. Estilo do cliente em temas/<tema>.json.

uso: reel.py PROJ rNN ETAPA [args]
  fix       reaplica o edit_fix do reel.json no edit_mfa.json (sem retranscrever)
  fonte     extrai src_48k.wav e src_16k.wav da fonte (reel.json "src", relativo a PROJ/01_sources)
  takes     checa se algum trecho é a voz da equipe soprando (−30/−50 dB)
  voz       monta a voz, transcreve, alinha no MFA com números por extenso → edit_mfa.json
  legenda   blocos_manual.txt → blocos.json + SRT em 05_qa/legendas
  camera    "camera": "face" (padrão: rastreio de rosto + camera.py da malu, base em camera_base)
            ou "crop" (recorte fixo por plano: reel.json "crops" = [{"at": t_fonte, "cx": px}], altura inteira)
  props     rNN/props.py → mg/public/rNN/props.json + checador de animação
  mix       voz + trilha do reel.json + SFX → mix.wav (−14 LUFS)
  previa    render rápido em 540p com som → 05_qa/previas (para o editor aprovar)
  revisa    todos os checadores num relatório (rode antes do final; o final também roda)
  davinci   pacote editável para o DaVinci em 07_davinci/ (camadas + timeline.fcpxml); o editor exporta por lá
  final     render final, capa, entrega, checagem técnica e legenda cruzada
  trecho A B  refaz só os quadros A–B e encaixa na entrega (ajuste pontual)
  audio     troca só o som do arquivo entregue (vídeo copiado, sem recodificar)
  capa      troca só a capa (rNN/reel.json "capa") e recoloca no quadro 0, sem renderizar o vídeo
  entrega   refaz só o arquivo entregue (capa nova no quadro 0, mix novo) a partir do video2.mp4

reel.json: {"name": "03 - …", "src": "C0008-004.MP4", "tema": "priscilla", "music": "music-…mp3", "prompt": "Alva, Dove…",
            "fix_words": {"Isotone.": "Isotônico."}, "shot_levels": […], "camera_moves": […],
            "capa": {"frame_t": 12.3, "l1": "…", "l2": "…", "accent": "…", "y": 290}}
Temporários sempre no SSD (TMPDIR) e mantidos (o editor pediu para guardar).
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ENG = Path(__file__).resolve().parent.parent           # skill reel-motion
P = Path(sys.argv[1]).resolve()
WK = P / '04_work'; MG = ENG / 'mg'; SK = Path.home() / '.claude/skills'
TMP = '/Volumes/SSD/CIBO/tmp'
os.environ['TMPDIR'] = TMP
AUDIOPY = str(Path.home() / '.venvs/audiotools/bin/python')
R = sys.argv[2]; ETAPA = sys.argv[3]; ARGS = sys.argv[4:]; W = WK / R
C = json.load(open(W / 'reel.json'))
NAME = C['name']; ENTREGA = P / '06_deliverables' / f'{NAME}.mp4'; CAPA = P / '06_deliverables' / f'CAPA - {NAME}.jpg'
# pasta pública do Remotion é do projeto (mídia do reel, fontes do tema); o código é o do motor
PUB = Path(os.environ.get('REEL_PUBLIC', WK / 'public')); PUB.mkdir(parents=True, exist_ok=True)
TEMA = json.load(open(ENG / 'temas' / f"{C.get('tema', 'priscilla')}.json"))
TH = TEMA.get('theme', {})
os.environ['PUBLIC_DIR'] = str(PUB)
FPS = C.get('fps', 29.97)
# "orient": "h" = versão horizontal 16:9 do reel (composição ReelH, painel à esquerda; Andreia 19/10/2026)
HZ = C.get('orient') == 'h'; VW, VH = (1920, 1080) if HZ else (1080, 1920)


def fontes_tema():
    """copia as fontes do tema para PUB/fonts e devolve o tema com caminhos relativos à pasta pública"""
    import shutil, time
    (PUB / 'fonts').mkdir(exist_ok=True)
    th = json.loads(json.dumps(TH))
    for f in th.get('fonts', []):
        src = Path(os.path.expanduser(f['file']))
        if not (PUB / 'fonts' / src.name).exists():
            shutil.copy2(src, PUB / 'fonts' / src.name)
        f['file'] = f'fonts/{src.name}'
    return th


def capa_tema():
    """capa do tema com o logo copiado para PUB/brand (o Remotion só lê da pasta pública)"""
    import shutil
    cp = dict(TEMA.get('capa', {}))
    if cp.get('logo') and os.path.isabs(cp['logo']):
        (PUB / 'brand').mkdir(exist_ok=True); src = Path(cp['logo'])
        shutil.copy2(src, PUB / 'brand' / src.name); cp['logo'] = f'brand/{src.name}'
    return cp


def fonte_path():
    return Path(C['src']) if os.path.isabs(C['src']) else P / '01_sources' / C['src']


def sh(cmd, **kw):
    print('$', cmd if isinstance(cmd, str) else ' '.join(map(str, cmd))[:160], flush=True)
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kw)


def segs():
    return json.load(open(W / 'segs.json'))


def whisper(audio, out, prompt=None):
    cmd = ['uv', 'run', '--quiet', '--with', 'mlx-whisper', 'python', str(ENG / 'scripts/wt.py'), str(audio), str(out), 'mlx-community/whisper-large-v3-mlx']
    sh(cmd + ([prompt] if prompt else []), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- números por extenso para o MFA (ele erra "75%", "R$ 82", "1,3") ----------
def extenso(tok):
    """'75%' → ['setenta','e','cinco','por','cento']; devolve None se não é número."""
    t = tok.strip().strip('.,;:!?')
    t = re.sub(r',00$', '', t)                                  # "R$4,00" → "R$4"
    if re.fullmatch(r'\d{1,3}(\.\d{3})+', t):                   # "3.900.000" é milhar, não decimal
        t = t.replace('.', '')
    m = re.fullmatch(r'(R\$)?\s*(\d+(?:[.,]\d+)?)\s*(%|mil|mi|milhões|milhão|reais)?', t)
    if not m:
        return None
    out = subprocess.run(['uv', 'run', '--quiet', '--with', 'num2words', 'python', '-c',
                          'import sys;from num2words import num2words as n;v=sys.argv[1].replace(".","").replace(",",".") if "," in sys.argv[1] else sys.argv[1];'
                          'print(n(float(v) if "." in v else int(v),lang="pt_BR"))', m.group(2)], capture_output=True, text=True).stdout.split()
    suf = {'%': ['por', 'cento'], 'mi': ['milhões'], None: []}.get(m.group(3), [m.group(3)] if m.group(3) else [])
    return out + suf + (['reais'] if m.group(1) else [])


def alinha(audio, wjson, a, b, out):
    """MFA com números expandidos; volta ao token original (início da 1ª palavra, fim da última)."""
    d = json.load(open(wjson))
    toks = [w for s in d['segments'] for w in s.get('words', []) if a - 0.5 <= w['start'] < b + 0.5]
    for k, v in C.get('fix_words', {}).items():
        for w in toks:
            if w['word'].strip() == k:
                w['word'] = ' ' + v
    # o Whisper quebra "R$ 4,00" em R / $ / 4 / ,00 e "75%" em 75 / %: junta antes de expandir
    m = []
    for w in toks:
        t = w['word'].strip()
        prev = m[-1]['word'].strip() if m else ''
        if m and (t in ('$', '%') or re.fullmatch(r'[.,]\d+[.,]?', t) or (re.fullmatch(r'\d+[.,]?%?', t) and prev in ('R', 'R$')) or (t.startswith('$') and prev == 'R')):   # "R" + "$40" (Priscilla 05)
            m[-1] = dict(m[-1], word=m[-1]['word'] + t, end=w['end'])
        else:
            m.append(dict(w))
    toks = m
    for k, v in C.get('fix_words', {}).items():
        for w in toks:
            if w['word'].strip() == k:
                w['word'] = ' ' + v
    exp, grp = [], []
    for i, w in enumerate(toks):
        if w['word'].strip() in ('%', 'R$') and grp:          # "%" solto do Whisper junta no número anterior
            e = extenso(toks[i - 1]['word'].strip() + w['word'].strip()) if w['word'].strip() == '%' else None
            if e and grp[-1][0] == i - 1:
                n = len(grp[-1][1]); del exp[-n:]
                span = (w['start'] - toks[i - 1]['start']) / len(e)
                exp += [{'word': x, 'start': toks[i - 1]['start'] + k * span, 'end': toks[i - 1]['start'] + (k + 1) * span} for k, x in enumerate(e)]
                grp[-1] = (i - 1, list(range(len(exp) - len(e), len(exp))), [i - 1, i])
                continue
        e = extenso(w['word'])
        if e:
            span = (w['end'] - w['start']) / len(e)
            exp += [{'word': x, 'start': w['start'] + k * span, 'end': w['start'] + (k + 1) * span} for k, x in enumerate(e)]
            grp.append((i, list(range(len(exp) - len(e), len(exp))), [i]))
        else:
            exp.append(dict(w)); grp.append((i, [len(exp) - 1], [i]))
    tmpw = W / 'mfa' / 'expandido.json'; tmpw.parent.mkdir(exist_ok=True)
    json.dump({'segments': [{'words': exp}]}, open(tmpw, 'w'), ensure_ascii=False)
    tmpo = W / 'mfa' / 'expandido_out.json'
    try:
        sh([sys.executable, str(SK / 'fala-limpa/scripts/alinha_mfa.py'), '--audio', str(audio), '--words', str(tmpw), '--range', str(a), str(b),
            '--margem', '0.5', '--out', str(tmpo)])
        al = json.load(open(tmpo))['segments'][0]['words']
    except subprocess.CalledProcessError:
        # o MFA às vezes não alinha um trecho longo inteiro (sigla, número): alinha em pedaços de ~12 s cortados em pausas
        print('MFA falhou no trecho inteiro: alinhando em pedaços')
        al, cur, chunk = [], a, []
        cuts = [a] + [exp[i]['end'] for i in range(len(exp) - 1) if exp[i + 1]['start'] - exp[i]['end'] > 0.15 and exp[i]['end'] - a > 0] + [b]
        bounds, last = [a], a
        for c in cuts[1:]:
            if c - last >= 12 or c == b:
                bounds.append(c); last = c
        for x, y in zip(bounds, bounds[1:]):
            part = [w for w in exp if x - 0.01 <= w['start'] < y]
            if not part:
                continue
            json.dump({'segments': [{'words': part}]}, open(tmpw, 'w'), ensure_ascii=False)
            try:
                sh([sys.executable, str(SK / 'fala-limpa/scripts/alinha_mfa.py'), '--audio', str(audio), '--words', str(tmpw), '--range', f'{x:.3f}', f'{y:.3f}',
                    '--margem', '0.3', '--out', str(tmpo)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                al += json.load(open(tmpo))['segments'][0]['words']
            except subprocess.CalledProcessError:
                print(f'  pedaço {x:.1f}-{y:.1f}s sem MFA: tempo do Whisper'); al += [dict(w, mfa=False) for w in part]
    outw = []
    for i, ix, orig in grp:
        if ix[0] >= len(al):
            break
        txt = ''.join(toks[o]['word'] for o in orig)
        txt = re.sub(r',00(?=\W*$)', '', txt)                   # "R$82,00," → "R$82,"
        outw.append({'word': txt, 'start': al[ix[0]]['start'], 'end': al[ix[-1]]['end'], 'mfa': all(al[x].get('mfa') for x in ix)})
    json.dump({'segments': [{'start': a, 'end': b, 'words': outw}]}, open(out, 'w'), ensure_ascii=False, indent=1)
    return outw


# ---------- etapas ----------
def e_takes():
    sh([sys.executable, str(ENG / 'scripts/checa_takes.py'), str(W / 'segs.json'), str(W / 'src_16k.wav'), '--min', str(C.get('takes_min', -25))])   # conversa livre: voz dela -17/-30, equipe -38/-42 → takes_min -32


def e_voz():
    try:   # o checador lista trechos para OUVIR; no voz é aviso (no revisa/final continua cobrando)
        e_takes()
    except subprocess.CalledProcessError:
        print('AVISO: checa_takes acusou emenda para ouvir (ver acima); seguindo')
    S = segs()
    f = ''.join(f'[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,afade=t=out:st={b - a - 0.006:.3f}:d=0.006[a{i}];' for i, (a, b) in enumerate(S))
    f += ''.join(f'[a{i}]' for i in range(len(S))) + f'concat=n={len(S)}:v=0:a=1[o]'
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(W / 'src_48k.wav'), '-filter_complex', f, '-map', '[o]', '-ar', '16000', '-ac', '1', str(W / 'voz16k.wav')])
    whisper(W / 'voz16k.wav', W / 'edit_w.json', C.get('prompt'))
    dur = sum(b - a for a, b in S)
    ws = alinha(W / 'voz16k.wav', W / 'edit_w.json', 0, dur + 0.05, W / 'edit_mfa.json')
    ws = edit_fix(ws)
    print(f'duração {dur:.2f}s')
    print(' '.join(f"{w['word'].strip()}@{w['start']:.2f}" for w in ws))


def edit_fix(ws):
    """Correções do texto montado por contexto (sobrevive a mudança de tempo): reel.json "edit_fix" =
    [{"w": "porque", "prev": "27,", "op": "drop"}, {"w": "de", "prev": "equipe", "to": "com"}].
    Uso: palavra que o Whisper inventa para ligar uma emenda, ou que ele ouve diferente da fonte."""
    fx = C.get('edit_fix', [])
    if not fx:
        return ws
    out, used = [], set()
    for i, w in enumerate(ws):
        t = w['word'].strip(); prev = out[-1]['word'].strip() if out else ''
        nxt = ws[i + 1]['word'].strip() if i + 1 < len(ws) else ''
        # prev/next = contexto; once = só a primeira ocorrência (default)
        f = next((f for k, f in enumerate(fx) if f['w'] == t and f.get('prev', prev) == prev and f.get('next', nxt) == nxt
                  and not (f.get('once', True) and k in used)), None)
        if f:
            used.add(fx.index(f))
        if f and f.get('op') == 'drop':
            print('edit_fix: tirou', t, 'depois de', prev); continue
        if f and 'to' in f:
            w = dict(w, word=' ' + f['to']); print('edit_fix:', t, '->', f['to'])
        out.append(w)
    d = json.load(open(W / 'edit_mfa.json')); d['segments'][0]['words'] = out
    json.dump(d, open(W / 'edit_mfa.json', 'w'), ensure_ascii=False, indent=1)
    return out


def e_legenda():
    sh([sys.executable, str(ENG / 'scripts/blocos.py'), str(W)])
    b = json.load(open(W / 'blocos.json'))
    f = lambda t: f"{int(t // 3600):02d}:{int(t // 60 % 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}"
    (P / '05_qa/legendas').mkdir(parents=True, exist_ok=True)
    (P / '05_qa/legendas' / f'{NAME}.srt').write_text('\n'.join(f"{i}\n{f(x['s'])} --> {f(x['e'])}\n{' '.join(w['t'] for w in x['words'])}\n" for i, x in enumerate(b, 1)))


def e_fonte():
    for sr, out in ((48000, 'src_48k.wav'), (16000, 'src_16k.wav')):
        sh(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', str(fonte_path()), '-vn', '-ac', '1', '-ar', str(sr), str(W / out)])


def e_camera_raw():
    """Imagem do bruto multicâmera (reel.json video_map: [{src, off, cx?}] um por trecho de segs; t_bruto = t_ep + off),
    áudio continua o do episódio. Recorte 9:16 na altura inteira em cx (padrão raw_cx). Um input por trecho (seek exato)."""
    S, VM = segs(), C['video_map']
    assert len(VM) == len(S), 'video_map precisa de um item por trecho'
    args, f = [], ''
    for i, ((a, b), v) in enumerate(zip(S, VM)):
        src = v['src']
        iw, ih = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src],
                                         capture_output=True, text=True).stdout.strip().split(','))
        h = ih; w = round(h * 9 / 16); cx = v.get('cx', C.get('raw_cx', iw / 2)); x0 = min(max(round(cx - w / 2), 0), iw - w)
        args += ['-ss', f'{a + v["off"]:.4f}', '-t', f'{b - a:.4f}', '-i', src]
        f += f'[{i}:v]setpts=PTS-STARTPTS,fps={FPS},crop={w}:{h}:{x0}:0,scale=1080:1920:flags=lanczos,unsharp=5:5:{C.get("sharpen", 0.5)},setsar=1,trim=duration={b - a:.4f}[v{i}];'
    f += ''.join(f'[v{i}]' for i in range(len(S))) + f'concat=n={len(S)}:v=1:a=0[o]'
    (PUB / R).mkdir(parents=True, exist_ok=True)
    sh(['ffmpeg', '-v', 'error', '-y', '-threads', '4'] + args + ['-filter_complex', f, '-map', '[o]', '-c:v', 'prores_ks', '-profile:v', '2', '-an', str(PUB / R / 'camera.mov')])
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(PUB / R / 'camera.mov')], capture_output=True, text=True).stdout)
    print(f'{len(S)} trechos do bruto, câmera {d:.2f}s (voz {sum(b - a for a, b in S):.2f}s)')


def e_camera_crop():
    """Fonte já editada (podcast multicâmera): recorte 9:16 na altura inteira por plano. crops = [{at, cx}] em tempo da fonte;
    cada um vale do 'at' até o próximo e cada trecho de segs é quebrado nas trocas."""
    src = fonte_path()
    cr = sorted(C['crops'], key=lambda c: c['at'])
    iw, ih = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(src)],
                                     capture_output=True, text=True).stdout.strip().split(',')[:2])   # HEVC do iPhone imprime vírgula a mais
    # "rotate": "cclock"/"clock" = gravação deitada no arquivo (Andreia: 16:9 salvo como 1080×1920); cx/cy valem no quadro já girado
    rot = {'cclock': 'transpose=2,', 'clock': 'transpose=1,'}.get(C.get('rotate'), '')
    if rot:
        iw, ih = ih, iw
    S = segs(); base = max(min(a for a, _ in S) - 1, 0)   # trechos podem vir fora de ordem (cold open)
    pieces = []
    for a, b in S:
        cuts = [a] + [c['at'] for c in cr if a < c['at'] < b] + [b]
        for x, y in zip(cuts, cuts[1:]):
            c = [k for k in cr if k['at'] <= x + 1e-3][-1]
            # escala nativa: altura inteira da fonte (608×1080 em 1080p), nunca close ampliado (regra transversal; João, 09/10/2026)
            # "z" (punch-in no corte seco) só enquanto o recorte continua ≥ 1080 de largura: fonte vertical 1440×2560 aceita até 1,33
            h = ih; w = round(h * 9 / 16) if not HZ else min(iw, round(h * 16 / 9))
            zz = min(c.get('z', 1.0), w / VW)
            if zz > 1.001:
                h = round(h / zz / 2) * 2; w = round(h * VW / VH / 2) * 2
            x0 = min(max(round(c['cx'] - w / 2), 0), iw - w)
            y0 = min(max(round(c.get('cy', ih * 0.42) - h * 0.42), 0), ih - h) if zz > 1.001 else 0
            pieces.append((x - base, y - base, w, h, x0, y0))
    (PUB / R).mkdir(parents=True, exist_ok=True)
    # "tonemap": "hlg" — selfie de iPhone em HDR HLG (arib-std-b67) vira SDR Rec.709; sem isso céu estoura e pele lava (GL, 18/10/2026)
    pre = {'hlg': 'zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,'
                  'tonemap=mobius:desat=0:param=0.35,zscale=t=bt709:m=bt709:r=tv,format=yuv422p10le,'}.get(C.get('tonemap'), '')
    # range: HEVC do iPhone vem yuvj420p (full); sai em tv para o ProRes não lavar/estourar
    rng = ':in_range=pc:out_range=tv' if C.get('full_range') else ''
    # "track": rastreio do rosto (rastreio.py, [[t_fonte, cx, cy]]): o recorte 9:16 acompanha o rosto quadro a quadro
    # por sendcmd no crop (câmera de mão / pessoa que se mexe; Andreia 01, 19/10/2026). No 16:9 o quadro é inteiro e o
    # rastreio vai para o props (camX) na tela dividida.
    import bisect
    def interp(v, xs, ys):
        k = bisect.bisect_left(xs, v)
        if k <= 0: return ys[0]
        if k >= len(xs): return ys[-1]
        return ys[k - 1] + (ys[k] - ys[k - 1]) * (v - xs[k - 1]) / (xs[k] - xs[k - 1])
    TR_ = json.load(open(WK / C['track'])) if C.get('track') and not HZ else None
    cmds = []
    for i, (x, y, w, h, x0, y0) in enumerate(pieces):
        if TR_ is None:
            cmds.append(''); continue
        tt_ = [k / FPS for k in range(int((y - x) * FPS) + 1)]
        cx = [interp(t + x + base, [r[0] for r in TR_], [r[1] for r in TR_]) for t in tt_]
        f_ = W / 'work' / f'crop_{i}.cmd'; f_.parent.mkdir(exist_ok=True)
        f_.write_text(''.join(f'{t:.4f} crop@c{i} x {min(max(round(c - w / 2), 0), iw - w)};\n' for t, c in zip(tt_, cx)))
        cmds.append(f"sendcmd=f='{f_}',")
    f = ''.join(f'[0:v]trim={x:.4f}:{y:.4f},setpts=PTS-STARTPTS,{pre}{rot}{cmds[i]}crop@c{i}={w}:{h}:{x0}:{y0},scale={VW}:{VH}:flags=lanczos{rng},'
                f'unsharp=5:5:{C.get("sharpen", 0.5)},setsar=1[v{i}];' for i, (x, y, w, h, x0, y0) in enumerate(pieces))
    f += ''.join(f'[v{i}]' for i in range(len(pieces))) + f'concat=n={len(pieces)}:v=1:a=0,fps={FPS}[o]'
    sh(['ffmpeg', '-v', 'error', '-y', '-threads', '4', '-ss', f'{base:.3f}', '-to', f'{max(b for _, b in S) + 1:.3f}', '-i', str(src),
        '-filter_complex', f, '-map', '[o]', '-c:v', 'prores_ks', '-profile:v', '2', '-an', str(PUB / R / 'camera.mov')])
    print(f'{len(pieces)} planos, {sum(p[1] - p[0] for p in pieces):.2f}s')


def e_camera():
    if C.get('video_map'):
        return e_camera_raw()
    if C.get('camera', 'face') == 'crop':
        return e_camera_crop()
    S = segs()
    j = json.load(open(WK / C.get('camera_base', 'r02/job.json')))       # base: rotação, grade, âncora, motor
    j.update(name=NAME, src=str(P / '01_sources' / C['src']), work=str(W / 'work'), **{'in': S[0][0], 'out': S[-1][1]},
             cuts=[[S[i][1], S[i + 1][0]] for i in range(len(S) - 1)], shots=[[a, b, k] for k, (a, b) in enumerate(S)],
             shot_levels=C['shot_levels'], face_pos=[[0.5, 0.33]] * len(S), camera_moves=C['camera_moves'],
             out_size=[1080, 1920])   # warp em 4K, saída já em 1080: −86% de disco e −12% de tempo, PSNR 47 dB contra o proxy antigo (auditoria 14/10/2026)
    assert len(C['shot_levels']) == len(S), 'shot_levels precisa de um nível por trecho'
    # rastreio de rosto é caro (~2-4 min, decodifica todos os planos em 4K): se fonte e planos são os mesmos do job anterior,
    # reaproveita os enquadramentos (já centralizados) e pula face_track + centraliza (auditoria 14/10/2026)
    ant = json.load(open(W / 'job.json')) if (W / 'job.json').exists() else {}
    reusa = ant.get('framings') and ant.get('src') == j['src'] and [s[:2] for s in ant.get('shots', [])] == [s[:2] for s in j['shots']] \
        and ant.get('centralizado') == bool(C.get('centraliza'))
    j.pop('framings', None)
    if reusa:
        j['framings'] = ant['framings']; j['centralizado'] = ant.get('centralizado'); print('planos iguais: enquadramentos reaproveitados')
    (W / 'work').mkdir(exist_ok=True)
    json.dump(j, open(W / 'job.json', 'w'), ensure_ascii=False, indent=1)
    # o face_track só grava os enquadramentos com --debug (sem ele sai sem erro e sem framings)
    if not reusa:
        sh([AUDIOPY, str(SK / 'fernanda-produto/scripts/face_track.py'), str(W / 'job.json'), '--apply', '--debug', str(P / '05_qa' / f'{R}_face_track.mp4')],
           cwd=W, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert 'framings' in json.load(open(W / 'job.json')), 'face_track não gravou framings'
    if C.get('centraliza') and not reusa:   # recorte de cada plano centrado no meio dos olhos (planos tortos pulam na emenda)
        sh([AUDIOPY, str(ENG / 'scripts/centraliza.py'), str(W / 'job.json')])
        jj = json.load(open(W / 'job.json')); jj['centralizado'] = True; json.dump(jj, open(W / 'job.json', 'w'), ensure_ascii=False, indent=1)
    sh([sys.executable, str(SK / 'malu-cortes/scripts/camera.py'), str(W / 'job.json')], cwd=W, stdout=open(W / 'work/camera.log', 'w'), stderr=subprocess.STDOUT)
    (PUB / R).mkdir(parents=True, exist_ok=True)
    dst = PUB / R / 'camera.mov'; dst.unlink(missing_ok=True)
    try:
        os.link(W / 'work/camera.mov', dst)   # já sai em 1080: link no mesmo disco, sem copiar nem reconverter
    except OSError:
        shutil.copy2(W / 'work/camera.mov', dst)


def e_props():
    out = PUB / R / 'props.json'; out.parent.mkdir(parents=True, exist_ok=True)
    sh([sys.executable, str(W / 'props.py'), str(W), str(out)])
    pr = json.load(open(out)); pr['theme'] = fontes_tema()
    # reel.json "layout"/"layoutH": ajuste do layout só deste reel (ex.: camShift pela altura do rosto na fonte; Andreia 19/10/2026)
    for k in ('layout', 'layoutH'):
        if C.get(k):
            pr['theme'][k] = {**pr['theme'].get(k, {}), **C[k]}
    # saída por cliente (editor 20/10/2026): tema "saida" {"tipo": "seco"|"fade", "dur": 0.9}; sem o bloco = seco (regra
    # transversal). reel.json "saida" sobrepõe só neste reel.
    sd = {'tipo': 'seco', **TEMA.get('saida', {}), **C.get('saida', {})}
    pr['endFade'] = float(sd.get('dur', 0.9)) if sd['tipo'] == 'fade' else 0
    if C.get('formato') == 'so_legenda':
        # formato "só legenda" (crítica do 06 da Priscilla, 14/10/2026: nem tudo igual): ela em tela cheia com gancho, títulos
        # e legenda; sem painéis, tela dividida e burns. SFX ficam só nos textos (gancho e títulos); os dos painéis saem.
        pr['panels'], pr['split'], pr['burns'] = [], [], []
        orig = W / 'sfx_com_paineis.json'
        if not orig.exists():
            shutil.copy(W / 'sfx.json', orig)
        marcas = [0.0] + [x for h in pr.get('titles') or [] for x in (h['s'], h.get('l2At', h['s']))]
        json.dump([e for e in json.load(open(orig)) if any(abs(e['t'] - m) < 0.45 for m in marcas)], open(W / 'sfx.json', 'w'), indent=1)
    json.dump(pr, open(out, 'w'), ensure_ascii=False, indent=1)
    sh([sys.executable, str(ENG / 'scripts/checa_props.py'), str(out), str(W / 'edit_mfa.json'), str(W / 'sfx.json')])


def e_mix():
    # calibra a trilha até a meta voz × trilha (reel.json "music_gap", padrão 18,5 dB; editor do João: trilha alta demais, 13/10/2026)
    gap = C.get('music_gap', 18.5)   # null = não calibra (ganho travado, ex.: ajuste pontual com music_env)
    for _ in range(3 if gap is not None else 1):
        out = subprocess.run([AUDIOPY, str(ENG / 'scripts/mix.py'), str(W)], capture_output=True, text=True, check=True).stdout
        m = re.search(r'diferença (-?[\d.]+) dB', out)
        if gap is None or not m or abs(float(m.group(1)) - gap) <= 1.0:
            break
        c = json.load(open(W / 'reel.json')); c['music_db'] = round(c.get('music_db', -6.5) + float(m.group(1)) - gap, 1)
        json.dump(c, open(W / 'reel.json', 'w'), ensure_ascii=False, indent=1); print(f"trilha ajustada para {c['music_db']} dB")
    print(out.strip().splitlines()[-1])
    r = subprocess.run(['ffmpeg', '-i', str(W / 'mix.wav'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    print(' '.join(l.strip() for l in r.splitlines()[-12:] if l.strip().startswith(('I:', 'Peak:'))))


def limpa_bundles():
    """o render do Remotion deixa uma cópia da pasta pública em TMP/remotion-webpack-bundle-*: é cópia, apaga (SSD lotou, 13/10/2026)"""
    import glob, shutil
    for d in glob.glob(f'{TMP}/remotion-webpack-bundle-*'):
        shutil.rmtree(d, ignore_errors=True)


def mata_orfaos():
    """esbuild/Chrome do motor que ficaram órfãos (pai = 1) de render encerrado: dois esbuild ficaram 4 h a ~280% de CPU (auditoria 14/10/2026)"""
    for l in subprocess.run(['ps', '-eo', 'pid=,ppid=,command='], capture_output=True, text=True).stdout.splitlines():
        p = l.split(None, 2)
        if len(p) == 3 and p[1] == '1' and 'reel-motion/node_modules' in p[2]:
            try:
                os.kill(int(p[0]), 9); print('órfão encerrado:', p[2][:70])
            except ProcessLookupError:
                pass


def pub_enxuta():
    """pasta pública só deste reel (hard links, sem ocupar disco): o bundle do Remotion COPIA a pasta pública inteira a cada
    render; com a câmera de todos os reels eram 12 GB por render e o SSD lotou (Andreia, 19/10/2026)"""
    dst = WK / '_pub' / R
    for sub in [R] + [d.name for d in PUB.iterdir() if d.is_dir() and not re.fullmatch(r'r\d+h?', d.name)]:
        src = PUB / sub
        if not src.is_dir():
            continue
        for f in src.rglob('*'):
            if f.is_file():
                g = dst / f.relative_to(PUB); g.parent.mkdir(parents=True, exist_ok=True)
                if g.exists() and g.stat().st_ino == f.stat().st_ino:
                    continue
                g.unlink(missing_ok=True)
                try:
                    os.link(f, g)
                except OSError:
                    shutil.copy2(f, g)
    return dst


_BUNDLE = None


def bundle_unico():
    """empacota UMA vez por processo (pasta pública enxuta dentro) e reusa em todos os renders da etapa: no pacote DaVinci
    são ~35 renders por reel e cada um reempacotava do zero (13 s cada; Andreia, 19/10/2026). Apagado ao sair."""
    global _BUNDLE
    if _BUNDLE is None:
        import atexit
        dst = WK / '_bundle' / R; shutil.rmtree(dst, ignore_errors=True)
        sh(['npx', 'remotion', 'bundle', 'src/index.ts', f'--public-dir={pub_enxuta()}', f'--out-dir={dst}', '--log=error'], cwd=MG)
        _BUNDLE = dst; atexit.register(lambda: shutil.rmtree(dst, ignore_errors=True))
    return _BUNDLE


def remotion(out, extra, props=None, codec=('--codec=h264',)):
    """render com limite de tempo e uma nova tentativa: a prévia do 05 travou 25 min sem dar erro (13/10/2026).
    Limite = 12 s por segundo de vídeo (render real: ~3-5 s/s com 2 abas), mínimo 6 min; trecho usa o tamanho dos quadros."""
    props = props or PUB / R / 'props.json'
    pr = json.load(open(props))
    ent = bundle_unico()
    fr = [a for a in extra if a.startswith('--frames=')]
    dur = (lambda a, b: (int(b) - int(a)) / 29.97)(*fr[0][9:].split('-')) if fr else pr['duration']
    lim = max(360, int(dur * 12))
    cmd = ['npx', 'remotion', 'render', str(ent), 'ReelH' if HZ else 'Reel', str(out), f'--props={props}', *codec,
           '--muted', '--overwrite', '--log=error', '--timeout=180000', '--concurrency=2'] + extra   # 2 abas (RAM do Mac de 16 GB); 180 s por quadro com a máquina ocupada
    mata_orfaos()
    for tentativa in (1, 2):
        print('$', ' '.join(map(str, cmd))[:160], f'(limite {lim}s)', flush=True)
        p = subprocess.Popen(cmd, cwd=MG, start_new_session=True)
        import signal
        def _fim(sig, frm, p=p):   # reel.py encerrado: leva o render junto (grupo próprio não recebe o sinal do pai)
            try:
                os.killpg(p.pid, 15)
            except ProcessLookupError:
                pass
            sys.exit(1)
        signal.signal(signal.SIGTERM, _fim); signal.signal(signal.SIGINT, _fim)
        try:
            if p.wait(timeout=lim) == 0:
                break
            raise subprocess.CalledProcessError(p.returncode, cmd)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 15); p.wait()
            print(f'render passou de {lim}s (travado?): encerrado' + ('; nova tentativa' if tentativa == 1 else ''), flush=True)
            if tentativa == 2:
                raise
    limpa_bundles()


def e_previa():
    (P / '05_qa/previas').mkdir(parents=True, exist_ok=True)
    remotion(W / 'previa.mp4', ['--scale=0.5', '--crf=26', '--x264-preset=veryfast'])
    out = P / '05_qa/previas' / f'{NAME} (prévia).mp4'
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(W / 'previa.mp4'), '-i', str(W / 'mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart', str(out)])
    print('prévia:', out)


def entrega(video):
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-loop', '1', '-i', str(CAPA), '-i', str(W / 'mix.wav'), '-filter_complex',
        f"[1:v]scale={VW}:{VH},format=yuv420p[c];[0:v][c]overlay=0:0:enable='eq(n,0)':shortest=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p[v]",
        '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-crf', '17', '-maxrate', '10M', '-bufsize', '20M', '-preset', 'slow', '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709',
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', '-c:a', 'aac', '-b:a', '320k', '-shortest', '-movflags', '+faststart', str(W / 'final_tmp.mp4')])
    os.replace(W / 'final_tmp.mp4', ENTREGA)
    v = P / '05_qa' / f'{R}_verify.json'
    subprocess.run([sys.executable, str(SK / 'video-delivery-safety-check/scripts/verify_video.py'), '--video', str(ENTREGA), '--cover', str(CAPA), '--width', str(VW), '--height', str(VH),
                    '--fps', str(FPS), '--output-json', str(v), '--min-shot', '0'], capture_output=True)
    d = json.load(open(v)); print('checagem técnica:', d['automated_status'], d['errors'])


def faz_capa(cp):
    # capa pensada para o feed: "frame_file" = quadro já recortado da fonte aberta (pessoa mais baixa, título acima da cabeça
    # dentro da área do grid 3:4); senão o quadro "frame_t" da câmera do reel. Escolha OLHANDO a imagem (olhos abertos).
    if cp.get('frame_file'):
        import shutil; shutil.copy2(W / cp['frame_file'], PUB / R / 'capa_frame.png')
    else:
        sh(['ffmpeg', '-v', 'error', '-y', '-ss', str(cp['frame_t']), '-i', str(PUB / R / 'camera.mov'), '-frames:v', '1', str(PUB / R / 'capa_frame.png')])
    os.environ['COMP'] = 'CapaH' if HZ else 'Capa'; os.environ['PUBLIC_DIR'] = str(pub_enxuta())
    sh(['node', 'capa.mjs', str(CAPA), json.dumps({'frame': f'{R}/capa_frame.png', 'theme': fontes_tema(), **capa_tema(), **{k: v for k, v in cp.items() if k not in ('frame_t', 'frame_file')}}, ensure_ascii=False)], cwd=MG)


def e_capa():
    """troca só a capa (quadro escolhido olhando a imagem) e recoloca no quadro 0 da entrega, sem renderizar o vídeo"""
    faz_capa(C['capa']); entrega(W / 'video2.mp4')



def e_revisa():
    """todos os checadores num relatório só, antes do final (auditoria 14/10/2026: 5 erros do 05 passaram pela revisão visual).
    takes (equipe + cortes no meio da fala/palavra), hesitação, painéis/etiquetas, olhar nas pontas dos cortes."""
    print('== cortes e vozes', flush=True); subprocess.run([sys.executable, str(ENG / 'scripts/checa_takes.py'), str(W / 'segs.json'), str(W / 'src_16k.wav'), '--min', str(C.get('takes_min', -25))])
    if (W / 'voz16k.wav').exists():
        print('== hesitação', flush=True)
        r = subprocess.run([sys.executable, str(ENG / 'scripts/hesita.py'), str(W / 'voz16k.wav'), str(W / 'edit_mfa.json')], capture_output=True, text=True).stdout
        print('\n'.join(l for l in r.splitlines() if 'longa demais' not in l))
    if (PUB / R / 'props.json').exists():
        print('== painéis', flush=True); subprocess.run([sys.executable, str(ENG / 'scripts/checa_props.py'), str(PUB / R / 'props.json'), str(W / 'edit_mfa.json'), str(W / 'sfx.json')])
    cam = PUB / R / 'camera.mov'
    if cam.exists():
        print('== olhar nas pontas dos cortes (até 0,5 s antes de cada emenda)', flush=True)
        S = segs(); st = [0.0]
        for a, b in S:
            st.append(st[-1] + b - a)
        js = W / 'work' / 'olhar.json'
        subprocess.run([AUDIOPY, str(ENG / 'scripts/olhar.py'), str(cam), '--json', str(js)], capture_output=True)
        tr = json.load(open(js)) if js.exists() else []
        achou = [t for t in tr for c in st[1:] if c - 0.5 <= t['fim'] <= c + 0.15 and t['fim'] - t['ini'] >= 0.2]
        for t in achou:
            print(f"  {t['ini']:.2f}-{t['fim']:.2f} olha para {t['lado']} colado no corte: corte antes ou segure o quadro")
        print('  OK' if not achou else f'  {len(achou)} ponto(s)')
    print('== variação (movimento.py: mesmo SFX/burn/movimento/painel seguidos além do limite do tema)', flush=True)
    subprocess.run([sys.executable, str(ENG / 'scripts/movimento.py'), 'confere', '--tema', str(ENG / 'temas' / f"{C.get('tema', 'priscilla')}.json"),
                    '--sfx', str(W / 'sfx.json'), '--props', str(PUB / R / 'props.json'), '--reel', str(W / 'reel.json')])
    print('== gancho e ritmo (gancho-e-ritmo: nota 0–10, limiar no tema "qualidade")', flush=True)
    (W / 'work').mkdir(exist_ok=True)
    return subprocess.run([sys.executable, str(SK / 'gancho-e-ritmo/scripts/gancho_ritmo.py'), '--props', str(PUB / R / 'props.json'),
                           '--segs', str(W / 'segs.json'), '--sfx', str(W / 'sfx.json'), '--reel', str(W / 'reel.json'),
                           '--tema', str(ENG / 'temas' / f"{C.get('tema', 'priscilla')}.json"), '--json', str(W / 'work' / 'gancho_ritmo.json')]).returncode


# partes isoladas por tipo de painel (as chaves batem com <Pt k=…> no panels.tsx)
PARTES = {
    'checklist': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}")]
        + [(f'item{k}', f"item {it['text']}") for k, it in enumerate(p.get('items', []))]
        + ([('risco', f"risco {p['strike']['text']}")] if p.get('strike') else []),
    'timeline': lambda p: ([('titulo', f"título {p['title']}")] if p.get('title') else []) + [('linha', 'linha do tempo')]
        + [(f'item{k}', f"marco {e['text']}") for k, e in enumerate(p.get('events', []))],
    'waves': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}"), ('linha', 'divisória'),
                        ('item0', f"lê {p.get('a', '')}"), ('item1', f"emite {p.get('b', '')}")],
    'balance': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}"), ('linha', 'balança'),
                          ('item0', f"prato {p.get('left', '')}"), ('item1', f"prato {p.get('right', '')}")],
    'root': lambda p: ([('titulo', f"título {p.get('title', '')} {p.get('accent', '')}")] if p.get('title') else []) + [('linha', 'chão e raízes')]
        + ([('item0', f"superfície {p['top']}")] if p.get('top') else []) + [(f'item{k + 1}', f"no caminho {it['text']}") for k, it in enumerate(p.get('items', []))]
        + ([('raiz', f"raiz {p['root']}")] if p.get('root') else []),
    'curve': lambda p: ([('titulo', f"título {p.get('title', '')} {p.get('accent', '')}")] if p.get('title') else []) + [('linha', 'curva')]
        + [(f'item{k}', f"ponto {q['label']}") for k, q in enumerate(p.get('points', [])) if q.get('label')],
    'pillars': lambda p: ([('titulo', f"título {p.get('title', '')} {p.get('accent', '')}")] if p.get('title') else []) + [('linha', 'base')]
        + [(f'item{k}', f"pilar {c['text']}") for k, c in enumerate(p.get('items', []))] + ([('teto', f"teto {p['roof']}")] if p.get('roof') else []),
    'strike': lambda p: [('titulo', f"tese {p.get('a', '')}"), ('risco', 'risco'), ('item0', f"correção {p.get('b', '')} {p.get('accent', '')}")],
    'cards': lambda p: [(f'item{k}', f"card {c['text']}") for k, c in enumerate(p.get('cards', []))],
    'sides': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}"), ('linha', 'divisória'), ('item0', f"lado {p.get('left', '')}"), ('item1', f"lado {p.get('right', '')}")],
    'route': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}"), ('linha', 'rota'), ('item0', f"de {p.get('from', '')}"), ('item1', f"para {p.get('to', '')}")],
    'hub': lambda p: ([('titulo', f"título {p['title']} {p.get('titleAccent', '')}")] if p.get('title') else []) + [('linha', 'raios'), ('centro', f"centro {p['center']}")]
        + [(f'item{k}', f"saída {it['text']}") for k, it in enumerate(p.get('items', []))],
    'stack': lambda p: ([('titulo', f"título {p['title']}")] if p.get('title') else []) + [(f'item{k}', f"card {c['text']}") for k, c in enumerate(p.get('cards', []))],
    'roles': lambda p: [('titulo', f"título {p.get('title', '')} {p.get('accent', '')}")] + [(f'item{k}', f"papel {r['text']}") for k, r in enumerate(p.get('roles', []))]
        + ([('centro', f"centro {p['center']['text']}")] if p.get('center') else []),
    'ladder': lambda p: ([('titulo', f"título {p['title']}")] if p.get('title') else []) + [(f'item{k}', f"degrau {st['text']}") for k, st in enumerate(p.get('steps', []))] + [('linha', 'base')],
}


def _at_parte(p, k):
    ty = p['type']
    if ty == 'strike':
        return p.get('strikeAt', p['s']) if k == 'risco' else p.get('line2At', p['s'])
    if ty in ('sides', 'route'):
        return p.get({'sides': ('leftAt', 'rightAt'), 'route': ('fromAt', 'toAt')}[ty][k == 'item1'], p['s'])
    if ty == 'hub':
        return p['items'][int(k[4:])]['at']
    if ty in ('cards', 'stack', 'roles', 'ladder'):
        if k == 'centro':
            return p['center'].get('at', p['s'])
        return {'cards': p.get('cards'), 'stack': p.get('cards'), 'roles': p.get('roles'), 'ladder': p.get('steps')}[ty][int(k[4:])].get('at', p['s'])
    if k == 'risco':
        return p['strike']['at']
    if p['type'] == 'curve':
        return p['points'][int(k[4:])]['at']
    if p['type'] == 'pillars':
        return p['roofAt'] if k == 'teto' else p['items'][int(k[4:])]['at']
    if p['type'] == 'root':
        return p['rootAt'] if k == 'raiz' else p['topAt'] if k == 'item0' else p['items'][int(k[4:]) - 1]['at']
    if p['type'] in ('waves', 'balance'):
        return p[{'waves': ('aAt', 'bAt'), 'balance': ('leftAt', 'rightAt')}[p['type']][k == 'item1']]
    return (p.get('items') or p.get('events'))[int(k[4:])]['at']


def camera_ffmpeg(pr, out):
    """camada 'camera' do pacote DaVinci sem Remotion: camera.mov sobre o fundo do tema, deslocada pela tela dividida
    (mesma curva do Reel.tsx: TR 0,42, Easy Ease) e escurecida no endFade"""
    import math
    TRv = 0.42
    def ease(u):
        u = min(1.0, max(0.0, u)); lo, hi = 0.0, 1.0
        for _ in range(30):
            m = (lo + hi) / 2; bx = 3 * (1 - m) ** 2 * m * 0.33 + 3 * (1 - m) * m * m * 0.67 + m ** 3
            lo, hi = (m, hi) if bx < u else (lo, m)
        m = (lo + hi) / 2
        return 3 * (1 - m) * m * m + m ** 3
    def sp(t):
        v = 0.0
        for g in pr['split']:
            a_, b_ = g['s'] - TRv * 0.35, g['e'] - TRv * 0.35
            v = max(v, min(ease((t - a_) / TRv), 1 - ease((t - b_) / TRv)))
        return v
    th = pr.get('theme') or {}; L = th.get('layout') or {}; LH = th.get('layoutH') or {}
    bg = (th.get('colors') or {}).get('bg', '#0f0d0c').lstrip('#')
    dur = pr['duration']; N = int(round(dur * 29.97))
    cX = pr.get('camX', VW / 2)
    def camx(t):
        if not isinstance(cX, list): return cX
        xs = [r[0] for r in cX]; ys = [r[1] for r in cX]
        if t <= xs[0]: return ys[0]
        if t >= xs[-1]: return ys[-1]
        k = next(i for i in range(len(xs)) if xs[i] >= t); return ys[k - 1] + (ys[k] - ys[k - 1]) * (t - xs[k - 1]) / (xs[k] - xs[k - 1])
    PW = LH.get('panelW', 1040)
    cmd = W / 'work' / 'camera_ff.cmd'; cmd.parent.mkdir(exist_ok=True)
    with open(cmd, 'w') as f:
        for n in range(N):
            t = n / 29.97; s_ = sp(t)
            if HZ:
                f.write(f"{t:.4f} overlay x {round((PW + (VW - PW) / 2 - camx(t)) * s_)};\n")
            else:
                f.write(f"{t:.4f} overlay y {round(L.get('camShift', 600) * s_)};\n")
    ef = pr.get('endFade') or 0
    fade = f",fade=t=out:st={dur - ef:.3f}:d={ef:.3f}:color=0x{bg}" if ef else ''
    sh(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=0x{bg}:s={VW}x{VH}:r=30000/1001:d={dur:.3f}', '-i', str(PUB / R / 'camera.mov'),
        '-filter_complex', f"[1:v]setpts=PTS-STARTPTS[c];[0:v]sendcmd=f='{cmd}'[b];[b][c]overlay@ov=x=0:y=0:eof_action=repeat{fade},trim=duration={dur:.3f},format=yuv422p10le[o]",
        '-map', '[o]', '-c:v', 'prores_ks', '-profile:v', '2', '-r', '30000/1001', str(out)])


def e_davinci():
    """pacote editável e fragmentado para o DaVinci (07_davinci/<nome>/), pedido do editor em 14/10/2026.
    Camadas inteiras: câmera renderizada (referência), mídia, fundo dos painéis, legenda. Elementos isolados, cada um no seu
    trecho de tempo: gráfico de cada painel, cada etiqueta, número da etapa, gancho, fundo do gancho, cada título.
    O davinci.py monta a timeline (bruto em takes com alça, voz por take, SFX, burns, capa).
    `davinci X…` re-renderiza só as camadas/elementos cujo nome contém X (ex.: davinci painel_2 tag_2)."""
    out = P / '07_davinci' / C['name']; cam = out / '_camadas'; (cam / 'el').mkdir(parents=True, exist_ok=True)
    if not (W / 'mix_pre.wav').exists() or not (W / 'musica.wav').exists():
        e_mix()
    pr = json.load(open(PUB / R / 'props.json'))
    alfa = ('--codec=prores', '--prores-profile=4444', '--pixel-format=yuva444p10le', '--image-format=png')
    CF = 29.97                                                  # quadros da composição Reel (Root.tsx), não o fps da câmera
    N = int(round(pr['duration'] * CF)); q = lambda t: min(N - 1, max(0, int(round(t * CF))))
    jobs = [('camera', 'camera', None, None, None, ('--codec=prores', '--prores-profile=standard')),
            ('legenda', 'legenda', None, None, None, alfa)] + ([('painel_fundo', 'painel_fundo', None, None, None, alfa)] if pr.get('panels') else [])
    if pr.get('inserts'):
        jobs.append(('midia', 'midia', None, None, None, alfa))
    man = []
    for i, p in enumerate(pr.get('panels', [])):
        a, b = q(p['s'] - 0.6), q(p['e'] + 0.7)
        # painel com partes marcadas (<Pt> no panels.tsx): um arquivo por título, item, linha e risco (17/10/2026)
        partes = PARTES.get(p['type'], lambda p: [])(p)
        for k, nm in partes or [(None, f"{p['type']} {p.get('title', '')} {p.get('accent', '')}")]:
            a2 = a if k in (None, 'titulo', 'linha') or (k == 'centro' and p['type'] != 'roles') else q(_at_parte(p, k) - 0.2)
            nome = f'painel_{i}' + (f'_{k}' if k else '')
            jobs.append((nome, 'painel', str(i), a2, b, alfa, k)); man.append(dict(arq=f'el/{nome}.mov', a=a2, grupo='painel', nome=nm))
        if p.get('step'):
            jobs.append((f'step_{i}', 'step', str(i), a, b, alfa)); man.append(dict(arq=f'el/step_{i}.mov', a=a, grupo='step', nome=f"etapa {p['step'].get('n', '')}"))
        for k, g in enumerate(p.get('tags') or []):
            a2 = q(g.get('at', p['s']) - 0.1)
            jobs.append((f'tag_{i}_{k}', 'tag', f'{i}:{k}', a2, b, alfa)); man.append(dict(arq=f'el/tag_{i}_{k}.mov', a=a2, grupo='tag', nome=f"etiqueta {g.get('text', '')}"))
    if pr.get('hook'):
        h = pr['hook']; b = q(h['e'] + 0.6)
        for el in ('hookbg', 'hook'):
            jobs.append((f'titulo_{el}', 'titulo', el, 0, b, alfa))
            man.append(dict(arq=f'el/titulo_{el}.mov', a=0, grupo='titulo', nome='fundo escuro do gancho' if el == 'hookbg' else f"gancho {h.get('l1', '')} {h.get('l2', '')} {h.get('accent', '')}"))
    for k, h in enumerate(pr.get('titles') or []):
        a, b = q(h['s'] - 0.2), q(h['e'] + 0.6)
        jobs.append((f'titulo_t{k}', 'titulo', f't{k}', a, b, alfa)); man.append(dict(arq=f'el/titulo_t{k}.mov', a=a, grupo='titulo', nome=f"título {h.get('l1', '')} {h.get('l2', '')} {h.get('accent', '')}"))
    if pr.get('lower'):
        lw = pr['lower']; a, b = q(lw.get('s', 0) - 0.2), q(lw.get('e', pr['duration']) + 0.6)
        jobs.append(('titulo_lower', 'titulo', 'lower', a, b, alfa)); man.append(dict(arq='el/titulo_lower.mov', a=a, grupo='titulo', nome='tarja'))
    # palavras-chave (tela cheia + B-roll, Growth Leaders 18/10/2026) e cartão final: um arquivo cada, véu junto da palavra
    for k, kw in enumerate(pr.get('keywords') or []):
        a, b = q(kw['s'] - 0.2), q(kw['e'] + 0.6)
        jobs.append((f'titulo_k{k}', 'titulo', f'k{k}', a, b, alfa))
        man.append(dict(arq=f'el/titulo_k{k}.mov', a=a, grupo='titulo', nome=f"palavra-chave {kw.get('sub', '')} {kw.get('text', '')} {kw.get('accent', '')}".strip()))
    if pr.get('endCard'):
        ec = pr['endCard']; a = q(ec['s'] - 0.1)
        jobs.append(('titulo_end', 'titulo', 'end', a, N - 1, alfa)); man.append(dict(arq='el/titulo_end.mov', a=a, grupo='titulo', nome=f"cartão final {ec.get('l1', '')}"))
    # nome único por pacote (o Resolve junta arquivos de mesmo nome entre pacotes; ver davinci.py): el/painel_0__r01.mov.
    # Pacote antigo sem sufixo: renomeia em vez de renderizar de novo
    U = lambda rel: str(Path(rel).with_name(f'{Path(rel).stem}__{R}{Path(rel).suffix}'))
    for m in man:
        m['arq'] = U(m['arq'])
    for nome in [j[0] for j in jobs] + ['fundo_desfocado']:
        rel = f'el/{nome}.mov' if (cam / f'el/{nome}.mov').exists() else f'{nome}.mov'
        if (cam / rel).exists() and not (cam / U(rel)).exists():
            (cam / rel).rename(cam / U(rel))
    json.dump(man, open(cam / 'elementos.json', 'w'), ensure_ascii=False, indent=1)
    # câmera da referência pelo ffmpeg (deslocamento da tela dividida por quadro + escurecimento final): no Remotion levava
    # ~5,5 min por reel de 85 s abrindo o ProRes quadro a quadro; aqui ~1 min (Andreia, 19/10/2026). Sem o motion blur da troca.
    if C.get('camera_davinci'):                                 # câmera montada pelo DaVinci a partir do bruto: não renderiza
        jobs = [j for j in jobs if j[0] != 'camera']
    elif C.get('camera_ffmpeg', True) and not (cam / U('camera.mov')).exists():
        camera_ffmpeg(pr, cam / U('camera.mov')); jobs = [j for j in jobs if j[0] != 'camera']
    for nome, lay, el, a, b, codec, *pt in jobs:
        f = cam / U(f'el/{nome}.mov' if el is not None else f'{nome}.mov')
        if f.exists() and (not ARGS or not any(x in nome for x in ARGS)) and (ARGS or f.stat().st_mtime > (PUB / R / 'props.json').stat().st_mtime):
            continue                                            # já renderizado e props sem mudança
        pf = PUB / R / f'props_{nome}.json'; json.dump({**pr, 'layer': lay, **({'el': el} if el is not None else {}), **({'part': pt[0]} if pt and pt[0] else {})}, open(pf, 'w'), ensure_ascii=False)
        t0 = time.time(); remotion(f, [f'--frames={a}-{b}'] if a is not None else [], pf, codec)
        print(f'{nome}: {time.time() - t0:.0f}s', flush=True)
    if '--so-el' not in ARGS:                                   # --so-el: só os elementos; não remonta o pacote (áudio já mexido no Resolve)
        sh([AUDIOPY, str(ENG / 'scripts/davinci.py'), str(P), R, str(out)])


def e_final():
    if e_revisa() == 2 and os.environ.get('GANCHO_OK') != '1':
        sys.exit('gancho-e-ritmo abaixo do limiar do cliente: ajuste o que o relatório aponta ou libere com GANCHO_OK=1 (decisão do editor)')
    remotion(W / 'video.mp4', ['--crf=16', '--x264-preset=slow'])
    cp = C['capa']
    faz_capa(cp)
    os.replace(W / 'video.mp4', W / 'video2.mp4')          # base sem som para ajustes pontuais
    entrega(W / 'video2.mp4')
    e_legenda()
    # a legenda cruzada reaproveita a transcrição em cache: arquiva a da versão anterior (sem apagar)
    import time
    for d in ('legenda_cruzada_transcricao', 'legenda_cruzada_audio'):
        for f in (P / '05_qa/legenda_cruzada' / d).glob(f'corte{R[1:]}.*'):
            f.rename(f.with_name(f'{f.stem}_{time.strftime("%Y%m%d%H%M%S")}{f.suffix}'))
    subprocess.run([sys.executable, str(SK / 'legenda-cruzada/scripts/cross_check.py'), '--videos', str(P / '06_deliverables'), '--captions', str(P / '05_qa/legendas'),
                    '--out', str(P / '05_qa/legenda_cruzada')], cwd=TMP)


def e_audio():
    """só o som mudou: troca a faixa de áudio do arquivo entregue, vídeo copiado sem recodificar"""
    tmp = W / 'audio_tmp.mp4'
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(ENTREGA), '-i', str(W / 'mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
        '-shortest', '-movflags', '+faststart', str(tmp)])
    os.replace(tmp, ENTREGA)
    v = P / '05_qa' / f'{R}_verify.json'
    subprocess.run([sys.executable, str(SK / 'video-delivery-safety-check/scripts/verify_video.py'), '--video', str(ENTREGA), '--cover', str(CAPA), '--width', str(VW), '--height', str(VH),
                    '--fps', str(FPS), '--output-json', str(v), '--min-shot', '0'], capture_output=True)
    d = json.load(open(v)); print('checagem técnica:', d['automated_status'], d['errors'])


def e_trecho(A, B):
    fa, fb = round(float(A) * FPS), round(float(B) * FPS)
    remotion(W / 'trecho.mp4', [f'--frames={fa}-{fb}', '--crf=16'])
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(W / 'video2.mp4'), '-i', str(W / 'trecho.mp4'), '-filter_complex',
        f'[0:v]trim=end_frame={fa},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[0:v]trim=start_frame={fb + 1},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]',
        '-map', '[v]', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', str(W / 'video3.mp4')])
    os.replace(W / 'video3.mp4', W / 'video2.mp4')
    entrega(W / 'video2.mp4')


PESADAS = ('davinci', 'voz', 'camera', 'previa', 'final', 'trecho', 'entrega', 'capa')
if ETAPA in PESADAS:   # trava: a mesma etapa nunca roda duas vezes no mesmo reel (duas câmeras do 02 corromperam o arquivo, 13/10/2026)
    LK = W / 'work' / f'.trava_{ETAPA}'; LK.parent.mkdir(exist_ok=True)
    if LK.exists():
        try:
            os.kill(int(LK.read_text()), 0); sys.exit(f'{R} {ETAPA} já está rodando (pid {LK.read_text()}); não rodo duas vezes')
        except (ProcessLookupError, ValueError):
            pass   # trava velha (processo morreu ou a sessão caiu)
    LK.write_text(str(os.getpid()))
    import atexit; atexit.register(lambda: LK.unlink(missing_ok=True))
{'fix': lambda: edit_fix(json.load(open(W / 'edit_mfa.json'))['segments'][0]['words']), 'fonte': e_fonte, 'takes': e_takes, 'voz': e_voz, 'legenda': e_legenda, 'camera': e_camera, 'props': e_props, 'mix': e_mix,
 'previa': e_previa, 'final': e_final, 'capa': e_capa, 'so_capa': lambda: faz_capa(C['capa']), 'pub': lambda: print(pub_enxuta()), 'camff': lambda: camera_ffmpeg(json.load(open(PUB / R / 'props.json')), Path(ARGS[0])), 'revisa': e_revisa, 'davinci': e_davinci, 'entrega': lambda: entrega(W / 'video2.mp4'), 'audio': e_audio, 'trecho': lambda: e_trecho(*ARGS[:2])}[ETAPA]()
