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
import json, os, re, shutil, subprocess, sys
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


def fontes_tema():
    """copia as fontes do tema para PUB/fonts e devolve o tema com caminhos relativos à pasta pública"""
    import shutil
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
    e_takes()
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
                                     capture_output=True, text=True).stdout.strip().split(','))
    S = segs(); base = max(min(a for a, _ in S) - 1, 0)   # trechos podem vir fora de ordem (cold open)
    pieces = []
    for a, b in S:
        cuts = [a] + [c['at'] for c in cr if a < c['at'] < b] + [b]
        for x, y in zip(cuts, cuts[1:]):
            c = [k for k in cr if k['at'] <= x + 1e-3][-1]
            # escala nativa: altura inteira da fonte (608×1080 em 1080p), nunca close ampliado (regra transversal; João, 09/10/2026)
            h = ih; w = round(h * 9 / 16)
            x0 = min(max(round(c['cx'] - w / 2), 0), iw - w); y0 = 0
            pieces.append((x - base, y - base, w, h, x0, y0))
    (PUB / R).mkdir(parents=True, exist_ok=True)
    f = ''.join(f'[0:v]trim={x:.4f}:{y:.4f},setpts=PTS-STARTPTS,crop={w}:{h}:{x0}:{y0},scale=1080:1920:flags=lanczos,'
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
    pr = json.load(open(out)); pr['theme'] = fontes_tema(); json.dump(pr, open(out, 'w'), ensure_ascii=False, indent=1)
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


def remotion(out, extra):
    """render com limite de tempo e uma nova tentativa: a prévia do 05 travou 25 min sem dar erro (13/10/2026).
    Limite = 12 s por segundo de vídeo (render real: ~3-5 s/s com 2 abas), mínimo 6 min; trecho usa o tamanho dos quadros."""
    pr = json.load(open(PUB / R / 'props.json'))
    fr = [a for a in extra if a.startswith('--frames=')]
    dur = (lambda a, b: (int(b) - int(a)) / 29.97)(*fr[0][9:].split('-')) if fr else pr['duration']
    lim = max(360, int(dur * 12))
    cmd = ['npx', 'remotion', 'render', 'src/index.ts', 'Reel', str(out), f'--props={PUB / R / "props.json"}', f'--public-dir={PUB}', '--codec=h264',
           '--muted', '--log=error', '--timeout=180000', '--concurrency=2'] + extra   # 2 abas (RAM do Mac de 16 GB); 180 s por quadro com a máquina ocupada
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
        "[1:v]scale=1080:1920,format=yuv420p[c];[0:v][c]overlay=0:0:enable='eq(n,0)':shortest=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p[v]",
        '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-crf', '17', '-maxrate', '10M', '-bufsize', '20M', '-preset', 'slow', '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709',
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', '-c:a', 'aac', '-b:a', '320k', '-shortest', '-movflags', '+faststart', str(W / 'final_tmp.mp4')])
    os.replace(W / 'final_tmp.mp4', ENTREGA)
    v = P / '05_qa' / f'{R}_verify.json'
    subprocess.run([sys.executable, str(SK / 'video-delivery-safety-check/scripts/verify_video.py'), '--video', str(ENTREGA), '--cover', str(CAPA), '--width', '1080', '--height', '1920',
                    '--fps', str(FPS), '--output-json', str(v), '--min-shot', '0'], capture_output=True)
    d = json.load(open(v)); print('checagem técnica:', d['automated_status'], d['errors'])


def faz_capa(cp):
    # capa pensada para o feed: "frame_file" = quadro já recortado da fonte aberta (pessoa mais baixa, título acima da cabeça
    # dentro da área do grid 3:4); senão o quadro "frame_t" da câmera do reel. Escolha OLHANDO a imagem (olhos abertos).
    if cp.get('frame_file'):
        import shutil; shutil.copy2(W / cp['frame_file'], PUB / R / 'capa_frame.png')
    else:
        sh(['ffmpeg', '-v', 'error', '-y', '-ss', str(cp['frame_t']), '-i', str(PUB / R / 'camera.mov'), '-frames:v', '1', str(PUB / R / 'capa_frame.png')])
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

def e_final():
    e_revisa()
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
    subprocess.run([sys.executable, str(SK / 'video-delivery-safety-check/scripts/verify_video.py'), '--video', str(ENTREGA), '--cover', str(CAPA), '--width', '1080', '--height', '1920',
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


PESADAS = ('voz', 'camera', 'previa', 'final', 'trecho', 'entrega', 'capa')
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
 'previa': e_previa, 'final': e_final, 'capa': e_capa, 'revisa': e_revisa, 'entrega': lambda: entrega(W / 'video2.mp4'), 'audio': e_audio, 'trecho': lambda: e_trecho(*ARGS[:2])}[ETAPA]()
