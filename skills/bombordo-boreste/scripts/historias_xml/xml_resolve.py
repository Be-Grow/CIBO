"""Projeto editável do Histórias do Porto para o DaVinci Resolve (XML do Final Cut 7, xmeml v4).

Mesmo layout do compose.py do EP 04, mas com cada camada numa trilha própria em vez de um MP4 queimado.
Sequência 1080x1920, 30 qps; o quadro 0 é a capa e a edição começa no quadro 1 (como na entrega).

  V1  Daniel: os keeps sobre o bruto, 9:16 por Movimento (escala + posição), punch-in nos destaques e
      descida de D px enquanto o painel de contexto está na tela (keyframes quadro a quadro nas rampas)
  V2  painéis de contexto (1080xP) entrando por cima
  V3  sombra da emenda (acompanha o painel)
  V4  legenda animada (ProRes 4444 com alfa), acompanha o layout
  V5  film burn azul (modo Tela) no início, nas emendas e no fim
  V6  fade final para preto (ProRes 4444 com alfa)
  V7  capa (1 quadro)
  A1  voz (WAV do bruto, dual-mono; ganho calculado para -16 LUFS)
  A2/A3  trilha já mixada, L/R (-23 dB, ducking e silêncio das piadas aplicados no arquivo)
  A4  cliques na entrada de cada contexto
  A5  whooshes (burns e entrada/saída dos painéis)
  A6  SFX das piadas (disco arranhado, grilos) e bipe nos palavrões

  python3 xml_resolve.py <historia> [saida.xml]
"""
import json, math, os, subprocess, sys
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.expanduser('~/.claude/skills/bombordo-boreste/scripts'))
import punch

HERE = Path(sys.argv[1]).resolve()            # pasta da história (ginecologista | grego)
FPS, W, H = 30, 1080, 1920
CFG = json.load(open(HERE / 'xml_cfg.json'))
E = json.load(open(HERE / 'edit.json'))
TOTAL, SEAMS, KEEPS = E['total'], E['seams'], E['keeps']
P, D, RAMP = CFG['P'], CFG['D'], CFG['RAMP']
CAP_N, CAP_S, SC = CFG['CAP_N'], P, CFG['SHADOW_C']
BURN_D, BURN_PEAK = CFG['BURN_D'], CFG['BURN_PEAK']
REFS = CFG['REFS']
OFF = 1                                # quadro da capa
BAND_H = 560                           # altura da faixa da legenda (kinetic position.band_height)


def fr(t): return int(round(t * FPS))


WIN = []
for _, a, b in REFS:
    if WIN and abs(WIN[-1][1] - a) < 0.05: WIN[-1][1] = b
    else: WIN.append([a, b])


def F(t):
    s = 0.0
    for a, b in WIN:
        u = min(1, max(0, (t - a) / RAMP)); v = min(1, max(0, (b - t) / RAMP))
        s += (u * u * (3 - 2 * u)) * (v * v * (3 - 2 * v))
    return s


PT = punch.Track(json.load(open(HERE / 'punch_events.json')))


def sub(p, tag, text=None, **at):
    e = ET.SubElement(p, tag, {k: str(v) for k, v in at.items()})
    if text is not None: e.text = str(text)
    return e


def rate(p):
    r = sub(p, 'rate'); sub(r, 'timebase', FPS); sub(r, 'ntsc', 'FALSE')


INFO = {}


def probe(path):
    if path not in INFO:
        d = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                       'format=duration:stream=codec_type,width,height,channels', '-of', 'json', path],
                                      capture_output=True, text=True).stdout)
        v = next((s for s in d['streams'] if s['codec_type'] == 'video'), None)
        a = next((s for s in d['streams'] if s['codec_type'] == 'audio'), None)
        dur = float(d['format'].get('duration', 0) or 0)
        INFO[path] = dict(duration=dur if dur > 0.05 else 3600.0, w=v and v['width'], h=v and v['height'],
                          channels=a and a.get('channels'), still=path.lower().endswith('.png'))
    return INFO[path]


FIDS = {}


def add_file(parent, path):
    path = str(Path(path).resolve())
    if path in FIDS:
        sub(parent, 'file', id=FIDS[path]); return
    fid = f'file-{len(FIDS) + 1}'; FIDS[path] = fid
    i = probe(path)
    f = sub(parent, 'file', id=fid)
    sub(f, 'name', Path(path).name)
    sub(f, 'pathurl', 'file://localhost' + quote(path))
    rate(f); sub(f, 'duration', fr(i['duration']))
    m = sub(f, 'media')
    if i['w']:
        sc = sub(sub(m, 'video'), 'samplecharacteristics'); rate(sc)
        for k, v in (('width', i['w']), ('height', i['h']), ('anamorphic', 'FALSE'),
                     ('pixelaspectratio', 'square'), ('fielddominance', 'none')):
            sub(sc, k, v)
    if i['channels']:
        au = sub(m, 'audio'); sc = sub(au, 'samplecharacteristics')
        sub(sc, 'depth', 16); sub(sc, 'samplerate', 48000); sub(au, 'channelcount', i['channels'])


N = [0]


def clipitem(track, path, start, end, src_in, name, audio_ch=None):
    N[0] += 1
    ci = sub(track, 'clipitem', id=f'clipitem-{N[0]}')
    sub(ci, 'name', name)
    sub(ci, 'duration', fr(probe(str(Path(path).resolve()))['duration']))
    rate(ci)
    sub(ci, 'start', start); sub(ci, 'end', end); sub(ci, 'enabled', 'TRUE')
    sub(ci, 'in', src_in); sub(ci, 'out', src_in + end - start)
    add_file(ci, path)
    if audio_ch:
        st = sub(ci, 'sourcetrack'); sub(st, 'mediatype', 'audio'); sub(st, 'trackindex', audio_ch)
    return ci


def keys_compact(samples, eps=1e-5):
    """[(quadro, valor...)] -> só os quadros onde a curva muda (mantém o início e o fim de cada patamar)."""
    out = []
    for k, s in enumerate(samples):
        prv = samples[k - 1] if k else None; nxt = samples[k + 1] if k + 1 < len(samples) else None
        same_prev = prv is not None and all(abs(a - b) < eps for a, b in zip(s[1:], prv[1:]))
        same_next = nxt is not None and all(abs(a - b) < eps for a, b in zip(s[1:], nxt[1:]))
        if not (same_prev and same_next): out.append(s)
    return out


def motion(ci, samples):
    # <when> conta do início da MÍDIA (inclui o <in> do clipe), não do início do clipe na timeline
    src_in = int(ci.find('in').text)
    ks = keys_compact(samples)
    e = sub(sub(ci, 'filter'), 'effect')
    for k, v in (('name', 'Basic Motion'), ('effectid', 'basic'), ('effectcategory', 'motion'),
                 ('effecttype', 'motion'), ('mediatype', 'video')):
        sub(e, k, v)
    p = sub(e, 'parameter', authoringApp='PremierePro')
    sub(p, 'parameterid', 'scale'); sub(p, 'name', 'Scale'); sub(p, 'valuemin', 0); sub(p, 'valuemax', 1000)
    sub(p, 'value', f'{ks[0][1]:.4f}')
    if len(ks) > 1 and any(abs(k[1] - ks[0][1]) > 1e-4 for k in ks):
        for k in ks:
            kf = sub(p, 'keyframe'); sub(kf, 'when', src_in + k[0]); sub(kf, 'value', f'{k[1]:.4f}')
    p = sub(e, 'parameter', authoringApp='PremierePro')
    sub(p, 'parameterid', 'center'); sub(p, 'name', 'Center')
    v = sub(p, 'value'); sub(v, 'horiz', f'{ks[0][2]:.6f}'); sub(v, 'vert', f'{ks[0][3]:.6f}')
    if len(ks) > 1 and any(abs(k[2] - ks[0][2]) > 1e-6 or abs(k[3] - ks[0][3]) > 1e-6 for k in ks):
        for k in ks:
            kf = sub(p, 'keyframe'); sub(kf, 'when', src_in + k[0])
            val = sub(kf, 'value'); sub(val, 'horiz', f'{k[2]:.6f}'); sub(val, 'vert', f'{k[3]:.6f}')


def screen(ci): sub(ci, 'compositemode', 'screen')


def level(ci, db):
    e = sub(sub(ci, 'filter'), 'effect')
    for k, v in (('name', 'Audio Levels'), ('effectid', 'audiolevels'), ('effectcategory', 'audiolevels'),
                 ('effecttype', 'audiolevels'), ('mediatype', 'audio')):
        sub(e, k, v)
    p = sub(e, 'parameter', authoringApp='PremierePro')
    sub(p, 'parameterid', 'level'); sub(p, 'name', 'Level'); sub(p, 'valuemin', 0); sub(p, 'valuemax', 3.98109)
    sub(p, 'value', f'{10 ** (db / 20):.5f}')


def pan(ci, v):
    e = sub(sub(ci, 'filter'), 'effect')
    for k, val in (('name', 'Audio Pan'), ('effectid', 'audiopan'), ('effectcategory', 'audiopan'),
                   ('effecttype', 'audiopan'), ('mediatype', 'audio')):
        sub(e, k, val)
    p = sub(e, 'parameter', authoringApp='PremierePro')
    sub(p, 'parameterid', 'pan'); sub(p, 'name', 'Pan'); sub(p, 'valuemin', -1); sub(p, 'valuemax', 1)
    sub(p, 'value', v)


def vtrack(seq_video):
    t = sub(seq_video, 'track'); return t


def build(out):
    master = CFG['master']; mi = probe(master)
    sw, sh = mi['w'], mi['h']
    cw = sh * 9 / 16
    s0 = H / sh                                         # 1080 de altura -> 1920
    cx = CFG['crop_x'] + cw / 2                          # centro do recorte no bruto
    # O Resolve (Mismatched resolution = Scale entire image to fit, o padrão) encaixa o clipe na timeline
    # ANTES de aplicar o Movimento do XML, e lê o centro como fração do clipe já encaixado. Validado
    # importando e renderizando no Resolve 20.2.3 (18/10/2026).
    fit = min(W / sw, H / sh)
    h0 = -s0 * (cx - sw / 2) / (sw * fit)

    root = ET.Element('xmeml', version='4')
    seq = sub(root, 'sequence', id='sequence-1')
    sub(seq, 'name', CFG['name'])
    end_all = OFF + fr(TOTAL + CFG['TAIL'])
    sub(seq, 'duration', end_all); rate(seq)
    tc = sub(seq, 'timecode'); rate(tc); sub(tc, 'string', '00:00:00:00'); sub(tc, 'frame', 0)
    sub(tc, 'displayformat', 'NDF')
    media = sub(seq, 'media')
    video = sub(media, 'video')
    fmt = sub(video, 'format'); sc = sub(fmt, 'samplecharacteristics'); rate(sc)
    for k, v in (('width', W), ('height', H), ('anamorphic', 'FALSE'), ('pixelaspectratio', 'square'),
                 ('fielddominance', 'none')):
        sub(sc, k, v)
    audio = sub(media, 'audio')

    # V1 Daniel
    t1 = vtrack(video); pos = 0.0
    for n, (a, b) in enumerate(KEEPS):
        st, en = OFF + fr(pos), OFF + fr(pos + b - a)
        ci = clipitem(t1, master, st, en, fr(a), f'Daniel {n + 1:02d}')
        smp = []
        for q in range(en - st + 1):
            t = pos + q / FPS
            k = PT.scale(t); f = F(t)
            smp.append((q, 100 * s0 * k / fit, h0 * k, D * f / (sh * fit)))
        motion(ci, smp)
        pos += b - a
    # V2 painéis
    t2 = vtrack(video)
    for name, a, b in REFS:
        path = str(HERE / f'ref_{name}.mov')
        st, en = OFF + fr(a - RAMP), OFF + fr(b + RAMP)
        dur = probe(path)['duration']
        en = min(en, st + fr(dur))
        ci = clipitem(t2, path, st, en, 0, f'Contexto - {name}')
        smp = [(q, 100.0, 0.0, ((P / 2 - P) + P * F(a - RAMP + q / FPS) - H / 2) / P) for q in range(en - st + 1)]
        motion(ci, smp)
    # V3 sombra
    t3 = vtrack(video); shd = str(HERE / 'seam_shadow.png'); sh_h = 320
    for a, b in WIN:
        st, en = OFF + fr(a - RAMP), OFF + fr(b + RAMP)
        ci = clipitem(t3, shd, st, en, 0, 'Sombra da emenda')
        smp = [(q, 100.0, 0.0, (P * F(a - RAMP + q / FPS) - SC + sh_h / 2 - H / 2) / sh_h) for q in range(en - st + 1)]
        motion(ci, smp)
    # V4 legenda
    t4 = vtrack(video); cap = str(HERE / 'legenda_animada.mov')
    ci = clipitem(t4, cap, OFF, OFF + fr(TOTAL), 0, 'Legenda animada')
    smp = [(q, 100.0, 0.0, (CAP_N + (CAP_S - CAP_N) * F(q / FPS) - H / 2) / BAND_H) for q in range(fr(TOTAL) + 1)]
    motion(ci, smp)
    # V5 burns
    t5 = vtrack(video); burn = CFG['burn']
    starts = [0.0] + [round(x - BURN_PEAK, 3) for x in SEAMS] + [round(TOTAL - BURN_D, 3)]
    for j, s in enumerate(starts):
        st = OFF + fr(max(0, s)); en = st + fr(BURN_D)
        ci = clipitem(t5, burn, st, en, 0, 'Film burn azul'); screen(ci)
    # V6 fade final
    t6 = vtrack(video); fade = str(HERE / 'fade_preto.mov')
    st = OFF + fr(TOTAL - 0.42); clipitem(t6, fade, st, end_all, 0, 'Fade para preto')
    # V7 capa
    t7 = vtrack(video); clipitem(t7, str(HERE / 'capa.png'), 0, 1, 0, 'Capa')

    # O Resolve cria cada trilha do XML como mono centralizada: a voz (dual-mono) vai numa trilha só,
    # senão L e R somam; a trilha estéreo vai em duas, com pan L/R.
    # A1 voz: WAV extraído do bruto, mesmo tempo (o Resolve recusa a importação com o áudio do MP4)
    voz = str(HERE.parent / 'voz_bruto.wav')
    bl = [(fr(x), fr(y)) for x, y in CFG.get('bleeps', [])]     # palavrão: a voz sai, o bipe (A6) entra
    ta = sub(audio, 'track'); pos = 0.0
    for n, (a, b) in enumerate(KEEPS):
        st, en = OFF + fr(pos), OFF + fr(pos + b - a)
        segs = [[st, en]]
        for x, y in bl:
            x, y = OFF + x, OFF + y
            segs = [part for s0_, e0 in segs for part in ([[s0_, e0]] if y <= s0_ or x >= e0 else
                                                          [[s0_, x]] * (x > s0_) + [[y, e0]] * (e0 > y))]
        for s0_, e0 in segs:
            ci = clipitem(ta, voz, s0_, e0, fr(a) + s0_ - st, f'Voz {n + 1:02d}', audio_ch=1); level(ci, CFG['voice_db'])
        pos += b - a
    # A2/A3 trilha (L/R)
    mus = str(HERE / 'trilha_mix.wav')
    for ch, pn in ((1, -1), (2, 1)):
        ta = sub(audio, 'track')
        ci = clipitem(ta, mus, OFF, end_all, 0, 'Trilha (mixada)', audio_ch=ch); pan(ci, pn)
    # A4 cliques na entrada de cada contexto
    ta = sub(audio, 'track'); clk = CFG['click']
    # os dois cliques do usuário, alternados (regra transversal); o camera_click tem 4 batidas: usa a 1ª
    cam = '/Volumes/SSD/CIBO Acervo/sfx/_global/camera_click.mp3'
    for n, (name, a, b) in enumerate(REFS):
        if n % 2 == 0:
            st = OFF + fr(a); en = st + fr(min(probe(clk)['duration'], 1.0))
            ci = clipitem(ta, clk, st, en, 0, f'Clique - {name}', audio_ch=1); level(ci, CFG['click_db'])
        else:
            st = OFF + fr(a - 0.165); ci = clipitem(ta, cam, st, st + fr(0.33), fr(0.0), f'Clique câmera - {name}', audio_ch=1)
            level(ci, CFG['click_db'] + 4)
    # A5 whooshes: pico no pico de cada burn; whoosh curto quando o painel entra e quando sai
    ta = sub(audio, 'track'); sd = Path(CFG['sfx_dir'])
    wb, wb_pk, wb_db = CFG['whoosh_burn']; wp, wp_pk, wp_db = CFG['whoosh_panel']
    # só nas emendas: nunca no burn de abertura nem no de fechamento (regra transversal)
    ev = [(s + BURN_PEAK - wb_pk, wb, wb_db, 'Whoosh - emenda') for s in starts[1:-1]]
    for a, b in WIN:
        ev += [(a - RAMP / 2 - wp_pk, wp, wp_db, 'Whoosh - painel entra'), (b + RAMP / 2 - wp_pk, wp, wp_db, 'Whoosh - painel sai')]
    for t, f, db, nm in sorted(ev):
        path = str(sd / f); d = probe(path)['duration']
        st = OFF + fr(max(0.0, t)); src_in = fr(max(0.0, -t))
        ci = clipitem(ta, path, st, st + fr(d) - src_in, src_in, nm, audio_ch=1); level(ci, db)
    # A6 SFX das piadas
    ta = sub(audio, 'track')
    for f, t, s0_, d, db in CFG['sfx']:
        st = OFF + fr(t)
        ci = clipitem(ta, str(sd / f), st, st + fr(d), fr(s0_), f'SFX - {Path(f).stem}', audio_ch=1); level(ci, db)
    bf, bdb = CFG.get('bleep', [None, 0])
    for x, y in bl:
        ci = clipitem(ta, str(sd / bf), OFF + x, OFF + y, 0, 'SFX - bipe', audio_ch=1); level(ci, bdb)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(root, encoding='unicode') + '\n'
    Path(out).write_text(xml, encoding='utf-8')
    print(out)


if __name__ == '__main__':
    build(sys.argv[2] if len(sys.argv) > 2 else str(HERE / f"PROJETO - {CFG['name']}.xml"))
