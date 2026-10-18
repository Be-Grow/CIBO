#!/usr/bin/env python3
"""Projeto editável de cada corte para Premiere Pro e DaVinci Resolve (XML do Final Cut 7).

uso: JOB=job.json projeto_nle.py [corte01 ...] [--master ARQ] [--out PASTA] [--clicks 'reaudio_clicks_{k}.wav']

Para cada corte grava `PROJETO - <filename>.xml`, `<filename>.srt` e um LEIAME na pasta
`<outdir>/Projetos editáveis` (ou --out). Sequência 1080×1920, 30 qps:
  V1  os trechos mantidos (keeps já ajustados ao silêncio, de `work/plan.json`) sobre o vídeo de
      origem — o mezanino `src` do job ou, com --master (ou `master` no clipe/job), o arquivo
      original com o deslocamento `master_in` — reenquadrados como Movimento (escala + posição),
      com keyframes quando há `cropx_timeline`
  V2  film burn da entrada e da saída (modo de mesclagem Tela/Screen)
  V3  grafismos de `overlays` (título de gancho, cartão Seguir), no tempo da entrega
  A1/A2  a voz dos mesmos trechos (canais 1 e 2)
  A3/A4  a trilha (`music`, a partir de `music_offset`, no nível `music_db`)
  A5  os cliques (`work/clicks_<clip>.wav` ou --clicks)
O tempo do projeto não tem o quadro da capa: é a edição. Adaptado de `kvrancic/oneshot-video`
premiere.py (MIT), 12/10/2026.
ATENÇÃO (18/10/2026): no DaVinci Resolve 20 este XML sai errado (Daniel pequeno, keyframes fora do clipe,
voz do MP4 recusada). As regras medidas e um gerador validado estão em bombordo-boreste SKILL.md,
seção "Histórias do Porto → XML para o DaVinci".
"""
import json, os, subprocess, sys
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

FPS = 30
W_SEQ, H_SEQ = 1080, 1920
CD = 1 / 30   # quadro da capa na entrega


def fr(t):
    return int(round(t * FPS))


def sub(p, tag, text=None, **at):
    e = ET.SubElement(p, tag, {k: str(v) for k, v in at.items()})
    if text is not None:
        e.text = str(text)
    return e


def rate(p):
    r = sub(p, "rate")
    sub(r, "timebase", FPS)
    sub(r, "ntsc", "FALSE")


def probe(path):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration:stream=codec_type,width,height,channels", "-of", "json", path],
                                  capture_output=True, text=True).stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    return {"duration": float(d["format"]["duration"]), "w": v and v["width"], "h": v and v["height"],
            "channels": a and a.get("channels")}


class Files:
    def __init__(self):
        self.ids, self.info = {}, {}

    def get(self, path):
        path = str(Path(path).resolve())
        if path not in self.info:
            self.info[path] = probe(path)
        return self.info[path]

    def add(self, parent, path):
        path = str(Path(path).resolve())
        if path in self.ids:
            sub(parent, "file", id=self.ids[path])
            return
        fid = f"file-{len(self.ids) + 1}"
        self.ids[path] = fid
        info = self.get(path)
        f = sub(parent, "file", id=fid)
        sub(f, "name", Path(path).name)
        sub(f, "pathurl", "file://localhost" + quote(path))
        rate(f)
        sub(f, "duration", fr(info["duration"]))
        m = sub(f, "media")
        if info["w"]:
            sc = sub(sub(m, "video"), "samplecharacteristics")
            rate(sc)
            for k, v in (("width", info["w"]), ("height", info["h"]), ("anamorphic", "FALSE"),
                         ("pixelaspectratio", "square"), ("fielddominance", "none")):
                sub(sc, k, v)
        if info["channels"]:
            au = sub(m, "audio")
            sc = sub(au, "samplecharacteristics")
            sub(sc, "depth", 16)
            sub(sc, "samplerate", 48000)
            sub(au, "channelcount", info["channels"])


def motion(ci, scale, keys):
    """Movimento básico: escala fixa e posição (centro) com keyframes [(quadro_no_clipe, h, v)]."""
    e = sub(sub(ci, "filter"), "effect")
    for k, v in (("name", "Basic Motion"), ("effectid", "basic"), ("effectcategory", "motion"),
                 ("effecttype", "motion"), ("mediatype", "video")):
        sub(e, k, v)
    p = sub(e, "parameter", authoringApp="PremierePro")
    sub(p, "parameterid", "scale"); sub(p, "name", "Scale")
    sub(p, "valuemin", 0); sub(p, "valuemax", 1000); sub(p, "value", f"{scale:.3f}")
    p = sub(e, "parameter", authoringApp="PremierePro")
    sub(p, "parameterid", "center"); sub(p, "name", "Center")
    v = sub(p, "value")
    sub(v, "horiz", f"{keys[0][1]:.6f}"); sub(v, "vert", f"{keys[0][2]:.6f}")
    if len(keys) > 1:
        for when, h, vv in keys:
            kf = sub(p, "keyframe")
            sub(kf, "when", when)
            val = sub(kf, "value")
            sub(val, "horiz", f"{h:.6f}"); sub(val, "vert", f"{vv:.6f}")


def composite_screen(ci):
    """Modo de mesclagem Tela (o film burn é preto com luz: Tela tira o preto)."""
    sub(ci, "compositemode", "screen")


def audio_level(ci, db):
    e = sub(sub(ci, "filter"), "effect")
    for k, v in (("name", "Audio Levels"), ("effectid", "audiolevels"), ("effectcategory", "audiolevels"),
                 ("effecttype", "audiolevels"), ("mediatype", "audio")):
        sub(e, k, v)
    p = sub(e, "parameter", authoringApp="PremierePro")
    sub(p, "parameterid", "level"); sub(p, "name", "Level")
    sub(p, "valuemin", 0); sub(p, "valuemax", 3.98109)
    sub(p, "value", f"{10 ** (db / 20):.5f}")


def clipitem(track, files, n, path, start, end, src_in, name, audio_ch=None, enabled=True):
    ci = sub(track, "clipitem", id=f"clipitem-{n}")
    sub(ci, "name", name)
    sub(ci, "duration", fr(files.get(path)["duration"]))
    rate(ci)
    sub(ci, "start", start); sub(ci, "end", end)
    sub(ci, "enabled", "TRUE" if enabled else "FALSE")
    sub(ci, "in", src_in); sub(ci, "out", src_in + end - start)
    files.add(ci, path)
    if audio_ch:
        st = sub(ci, "sourcetrack")
        sub(st, "mediatype", "audio")
        sub(st, "trackindex", audio_ch)
    return ci


def crop_at(c, t):
    """cropx no tempo t (segundos do `src`), como o render: degrau ou interpolação."""
    tl = sorted((float(a), float(b)) for a, b in c.get("cropx_timeline", []))
    if not tl:
        return float(c["cropx"])
    if c.get("cropx_interp"):
        if t <= tl[0][0]:
            return tl[0][1]
        for (t0, v0), (t1, v1) in zip(tl, tl[1:]):
            if t0 <= t <= t1:
                return v0 + (v1 - v0) * (t - t0) / max(t1 - t0, 1e-3)
        return tl[-1][1]
    cur = float(c["cropx"])
    for a, b in tl:
        if a <= t + 1e-6:
            cur = b
    return cur


def center_for(c, cropx, sw, sh):
    ch = int(c.get("crop_h", 1080)) if sh == 1080 else int(round(int(c.get("crop_h", 1080)) * sh / 1080))
    cw = (608 if int(c.get("crop_h", 1080)) == 1080 else int(round(int(c.get("crop_h", 1080)) * 9 / 16)) // 2 * 2) * sw / 1920
    s = H_SEQ / ch
    x = (sw - cw) * cropx
    dx, dy = x + cw / 2 - sw / 2, ch / 2 - sh / 2
    return 100.0 * s, -s * dx / W_SEQ, -s * dy / H_SEQ


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(k, c, job, work, out, master, clicks_pat, filmburn):
    files = Files()
    use_master = master or c.get("master") or job.get("master")
    src = use_master or os.path.join(job["srcdir"], c["src"])
    off = float(c.get("master_in", 0)) if use_master else 0.0
    info = files.get(src)
    name = c.get("filename") or k
    root = ET.Element("xmeml", version="4")
    seq = sub(root, "sequence", id="sequence-1")
    sub(seq, "name", name)
    total = sum(fr(b) - fr(a) for a, b in c["keeps"])
    sub(seq, "duration", total)
    rate(seq)
    tc = sub(seq, "timecode"); rate(tc)
    sub(tc, "string", "00:00:00:00"); sub(tc, "frame", 0); sub(tc, "displayformat", "NDF")
    m = sub(seq, "media")
    video = sub(m, "video")
    sc = sub(sub(video, "format"), "samplecharacteristics"); rate(sc)
    for kk, v in (("width", W_SEQ), ("height", H_SEQ), ("anamorphic", "FALSE"), ("pixelaspectratio", "square"),
                  ("fielddominance", "none")):
        sub(sc, kk, v)
    n = 0
    v1 = sub(video, "track")
    pos, segs = 0, []
    for a, b in c["keeps"]:
        f0, f1 = pos, pos + fr(b) - fr(a)
        n += 1
        ci = clipitem(v1, files, n, src, f0, f1, fr(a + off), f"{name[:2]} trecho {len(segs) + 1}")
        # keyframes da posição: a cada ponto da timeline dentro do trecho (quadros relativos ao clipe)
        ts = [a] + [float(t) for t, _ in c.get("cropx_timeline", []) if a < float(t) < b] + [b]
        keys = []
        for t in ts:
            sc_, h, vv = center_for(c, crop_at(c, t), info["w"], info["h"])
            if not keys or abs(h - keys[-1][1]) > 1e-5 or t == b:
                keys.append((fr(t) - fr(a), h, vv))
        if len(keys) == 2 and abs(keys[0][1] - keys[1][1]) < 1e-5:
            keys = keys[:1]
        motion(ci, sc_, keys)
        segs.append((f0, f1, a, b))
        pos = f1
    # V2: film burn da entrada e da saída (pico 0,53 s do asset no último quadro)
    v2 = sub(video, "track")
    if filmburn and os.path.exists(filmburn):
        fbd = fr(files.get(filmburn)["duration"])
        n += 1
        ci = clipitem(v2, files, n, filmburn, 0, min(fbd, total), 0, "film burn (entrada) — modo Tela")
        composite_screen(ci)
        st = max(0, total - fr(0.53))
        n += 1
        ci = clipitem(v2, files, n, filmburn, st, min(st + fbd, total + fbd), 0, "film burn (saída) — modo Tela")
        composite_screen(ci)
    # V3: grafismos (overlays) no tempo da entrega menos o quadro da capa
    v3 = sub(video, "track")
    for o in c.get("overlays", []):
        if os.path.exists(o["file"]):
            f0 = fr(float(o["t"]) - CD)
            nf = fr(files.get(o["file"])["duration"])
            n += 1
            clipitem(v3, files, n, o["file"], f0, f0 + nf, 0, Path(o["file"]).stem)
    audio = sub(m, "audio")
    sub(audio, "numOutputChannels", 2)
    af = sub(sub(audio, "format"), "samplecharacteristics")
    sub(af, "depth", 16); sub(af, "samplerate", 48000)
    # A1/A2: voz
    chs = info["channels"] or 1
    for ch in (1, 2) if chs >= 2 else (1,):
        tr = sub(audio, "track")
        for f0, f1, a, b in segs:
            n += 1
            clipitem(tr, files, n, src, f0, f1, fr(a + off), f"voz {ch}", audio_ch=ch)
    # A3/A4: trilha
    mus = c.get("music")
    if mus and os.path.exists(mus):
        mix = c.get("mix", {})
        mo, mdb = float(mix.get("music_offset", 0)), float(mix.get("music_db", -26))
        mi = files.get(mus)
        for ch in (1, 2) if (mi["channels"] or 1) >= 2 else (1,):
            tr = sub(audio, "track")
            n += 1
            ci = clipitem(tr, files, n, mus, 0, min(total, fr(mi["duration"] - mo)), fr(mo),
                          f"trilha {Path(mus).stem} ({mdb:g} dB; ducking no render)", audio_ch=ch)
            audio_level(ci, mdb)
    # A5: cliques
    cp = (clicks_pat.format(k=k) if clicks_pat else os.path.join(work, f"clicks_{k}.wav"))
    if cp and os.path.exists(cp):
        tr = sub(audio, "track")
        n += 1
        shift = fr(CD) if clicks_pat else 0     # cliques do reaudio já incluem a capa
        dur = fr(files.get(cp)["duration"])
        clipitem(tr, files, n, cp, 0, min(total, dur - shift), shift, "cliques", audio_ch=1)
    # marcadores nas emendas
    for i, (f0, *_r) in enumerate(segs[1:], 2):
        mk = sub(seq, "marker")
        sub(mk, "name", f"emenda {i}"); sub(mk, "in", f0); sub(mk, "out", -1)
    ET.indent(root)
    out.mkdir(parents=True, exist_ok=True)
    xml = out / f"PROJETO - {name}.xml"
    xml.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(root, encoding="unicode") + "\n")
    # legenda editável (tempo do projeto = tempo do corte, sem a capa)
    caps = os.path.join(work, f"captions_{k}.json")
    if os.path.exists(caps):
        cc = json.load(open(caps))["caps"]
        (out / f"{name}.srt").write_text("\n\n".join(
            f"{i}\n{srt_time(x['s'])} --> {srt_time(x['e'])}\n{x['t']}" for i, x in enumerate(cc, 1)) + "\n")
    return xml, total, n


LEIAME = """Projetos editáveis dos cortes (gerados pelo CIBO)

Cada corte tem um PROJETO - <nome>.xml (formato XML do Final Cut 7) e a legenda <nome>.srt.
Sequência 1080x1920, 30 qps. Trilhas: V1 trechos com reenquadramento (Movimento), V2 film burn
(modo Tela), V3 título de gancho e cartão Seguir, A1/A2 voz, A3/A4 trilha, A5 cliques.

Premiere Pro: Arquivo > Importar > escolha o .xml. A sequência aparece no painel Projeto.
  Legenda: Arquivo > Importar o .srt e arraste para a timeline (vira faixa de legenda).
DaVinci Resolve: Arquivo > Importar > Timeline > escolha o .xml; marque "Importar
  automaticamente os clipes de origem para o Media Pool". Legenda: Arquivo > Importar >
  Legendas e arraste o .srt para a timeline.
Se o film burn aparecer com fundo preto, mude o modo de mesclagem do clipe para Tela/Screen.
O ducking da trilha sob a voz é feito no render; no projeto a trilha entra no nível médio.
Se algum arquivo aparecer offline, use "Vincular mídia" / "Relink" apontando para a pasta do projeto.
"""


def main():
    args = sys.argv[1:]
    opt = {}
    for o in ("--master", "--out", "--clicks"):
        if o in args:
            i = args.index(o); opt[o] = args[i + 1]; del args[i:i + 2]
    job = json.load(open(os.environ["JOB"]))
    work = os.environ.get("WORK", job.get("work", "./work"))
    plan = json.load(open(os.path.join(work, "plan.json")))
    out = Path(opt.get("--out") or os.path.join(job.get("outdir", work), "Projetos editáveis"))
    fb = job.get("filmburn") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "filmburn_blue.mp4")
    for k in args or list(plan):
        c = {**plan[k], **{kk: v for kk, v in job["clips"].get(k, {}).items() if kk not in plan[k]}}
        xml, total, n = build(k, c, job, work, out, opt.get("--master"), opt.get("--clicks"), fb)
        ET.parse(xml)   # XML bem formado
        print(f"{k}: {xml.name} ({total / FPS:.1f}s, {n} clipes)")
    (out / "LEIAME.txt").write_text(LEIAME)


if __name__ == "__main__":
    main()
