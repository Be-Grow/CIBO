#!/usr/bin/env python3
"""Mede o estilo de um vídeo de referência para o CIBO copiar o "jeito", não o conteúdo.

uso: analisa_referencia.py REFERENCIA.mp4 [--out PASTA] [--rapido]
     (roda com qualquer python; se faltar opencv ele se reabre sozinho no venv da CIBO que tiver)

Mede, com números e tempo exato:
- formato, ritmo de corte (planos, duração mediana, cortes por 10 s), enquadramento (rosto, YuNet), cor;
- EFEITOS de imagem quadro a quadro: flash de exposição (subida e descida de brilho), freeze (quadro
  parado e se escureceu), trechos P&B, preto, câmera inclinada por plano, provável câmera lenta/rampa;
- SOM com voz e música separadas (demucs): quanto a música fica abaixo da voz e quanto ela abaixa quando
  entra a fala, eco/reverb e compressão da voz, entradas e quedas da música, pausas dramáticas, BPM e
  quantos cortes caem na batida (comparado com o acaso), prováveis SFX (impacto e riser/whoosh);
- FALA: transcrição local (whisper-cli, modelo em ~/.whisper_models) na voz separada, sem as frases que
  o Whisper inventa ("Legendas pela comunidade…", "Obrigado por assistir"…);
- LEGENDA pela posição real do texto (OCR do Vision do macOS): altura, tamanho, caixa, palavras por bloco;
Grava em PASTA: `estilo.json`, `relatorio.md` (receita), `planos.jpg` (um quadro por plano) e
`linha_tempo.jpg` (quadros + trilhas de marcadores: cortes, flash, freeze, P&B, fala, música, SFX).
`--rapido` pula separação de áudio, transcrição e OCR. Imprime no máximo 15 linhas.
Ideia de `edenfunf/reelmimic` e `krusemediallc/video-editor-agent`.
"""
import glob, json, os, re, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SKILLS = AQUI.parents[1]


def _garante_python():
    """Item 6: se o python atual não tem opencv, reabre o script no primeiro venv da CIBO que tiver."""
    try:
        import cv2, numpy  # noqa: F401
        return
    except ImportError:
        pass
    cands = [os.environ.get("CIBO_PY"), str(SKILLS / "content-hub/.venv/bin/python")]
    cands += sorted(glob.glob(str(SKILLS / "*/.venv/bin/python"))) + sorted(glob.glob(str(SKILLS / "*/venv/bin/python")))
    for c in cands:
        if c and os.path.exists(c) and os.path.realpath(c) != os.path.realpath(sys.executable):
            if subprocess.run([c, "-c", "import cv2, numpy"], capture_output=True).returncode == 0:
                os.execv(c, [c, str(Path(__file__).resolve())] + sys.argv[1:])
    sys.exit("analisa_referencia: nenhum python com opencv+numpy achado (defina CIBO_PY).")


_garante_python()
import cv2  # noqa: E402
import numpy as np  # noqa: E402

YUNET = os.environ.get("YUNET", str(SKILLS / "content-hub/assets/yunet.onnx"))
SW, FPS = 270, 4                       # análise de rosto/cor em 270 px, 4 qps
EW = 64                                # efeitos: 64 px, todos os quadros
SR = 22050
WHISPER = os.environ.get("WHISPER_MODEL", "")
TORCH_HOME = "/Volumes/SSD/CIBO/models/torch"
OCR_BIN = Path(os.environ.get("CIBO_BIN", "/Volumes/SSD/CIBO/tmp/bin")) / "ocr_quadros"
ALUCINA = re.compile(r"legenda|transcri[cç][aã]o|obrigad[oa] por assistir|inscreva|amara\.org|"
                     r"se inscrev|ative o sininho|tradu[cç][aã]o|subt[ií]tulos|www\.|\.com", re.I)


def sh(cmd, **k):
    return subprocess.run(cmd, capture_output=True, **k)


# ---------------------------------------------------------------- vídeo
def probe(path):
    d = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                       "-of", "json", path], text=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a, b = v["r_frame_rate"].split("/")
    return v["width"], v["height"], v["r_frame_rate"], float(a) / float(b or 1), float(d["format"]["duration"])


def frames(path, w, fps=None):
    W, H, _, _, _ = probe(path)
    h = int(round(w * H / W / 2) * 2)
    vf = (f"fps={fps}," if fps else "") + f"scale={w}:{h}"
    raw = sh(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)


def cuts(path):
    e = sh(["ffmpeg", "-v", "info", "-i", path, "-vf", "scdet=threshold=12:sc_pass=0", "-an", "-f", "null", "-"], text=True).stderr
    return [float(x) for x in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", e)]


def runs(mask, minlen):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            if j - i >= minlen:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def efeitos(path, fps, cs):
    """Item 1: flash, freeze, P&B, preto, inclinação e rampa, com tempo exato (todos os quadros)."""
    E = frames(path, EW)
    n = len(E)
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in E])
    y = hsv[..., 2].reshape(n, -1).mean(1)
    sat = hsv[..., 1].reshape(n, -1).mean(1)
    g = E.mean(3)
    diff = np.r_[99.0, np.abs(np.diff(g, axis=0)).reshape(n - 1, -1).mean(1)]
    t = np.arange(n) / fps
    perto_corte = lambda s, tol=0.2: any(abs(s - c) <= tol for c in cs)  # noqa: E731
    # flash: pico de brilho que sobe e desce em poucos quadros
    fl, k = [], int(round(fps * 0.2))
    for i in range(k, n - k):
        if y[i] < 150 or y[i] < y[i - k:i + k + 1].max():
            continue
        antes, depois = y[max(0, i - 2 * k):i].min(), y[i + 1:i + 2 * k + 1].min()
        if y[i] - antes >= 35 and y[i] - depois >= 30:
            meio = (y[i] + max(antes, depois)) / 2
            a = i
            while a > 0 and y[a - 1] > meio:
                a -= 1
            b = i
            while b < n - 1 and y[b + 1] > meio:
                b += 1
            if not fl or t[i] - fl[-1]["t"] > 0.2:
                fl.append({"t": round(t[i], 2), "quadros": int(b - a + 1), "pico": int(y[i]), "no_corte": perto_corte(t[i], 0.25)})
    # freeze: quadro parado ou quase (foto/freeze com zoom lento) por >= 0,5 s; quase parado só conta se
    # escureceu >= 15% em relação ao 0,5 s anterior (assinatura do "segura" dramático), senão é plano estático
    fz = []
    for a, b in runs((diff < 2.4) & (y > 20), int(fps * 0.5)):
        pre = y[max(0, a - int(fps * 0.5)):max(1, a - 1)]
        esc = 100 * (1 - y[a:b].mean() / pre.mean()) if len(pre) and pre.mean() > 0 else 0
        if diff[a + 1:b].mean() < 0.8 or esc >= 15:
            fz.append({"de": round(t[a], 2), "ate": round(t[b - 1], 2), "dur": round((b - a) / fps, 2),
                       "escureceu_pct": round(float(esc), 0), "tipo": "parado" if diff[a + 1:b].mean() < 0.8 else "quase parado (foto/zoom lento)"})
    pb = [{"de": round(t[a], 2), "ate": round(t[b - 1], 2)} for a, b in runs((sat < 6) & (y > 20), int(fps * 0.3))]
    preto = [{"de": round(t[a], 2), "ate": round(t[b - 1], 2)} for a, b in runs(y < 12, int(fps * 0.15))]
    # rampa/câmera lenta provável: dentro de um plano com movimento, o movimento cai para < 40% por >= 0,4 s e não é freeze
    edges = [0.0] + cs + [n / fps]
    rampa = []
    for s0, s1 in zip(edges, edges[1:]):
        a, b = int(s0 * fps) + 2, int(s1 * fps) - 2
        if b - a < fps * 1.2:
            continue
        m = diff[a:b]
        ref = np.median(m[: max(3, len(m) // 3)])
        if ref < 2.0:
            continue
        for ra, rb in runs((m < 0.4 * ref) & (m > 0.6), int(fps * 0.4)):
            rampa.append({"de": round(t[a + ra], 2), "ate": round(t[a + rb - 1], 2), "obs": "provável câmera lenta/rampa"})
    return {"flashes": fl, "freezes": fz, "pb": pb, "preto": preto, "rampas": rampa}, (t, y, sat, diff)


def _angulo(f):
    e = cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 80, 200)
    L = cv2.HoughLinesP(e, 1, np.pi / 180, 40, minLineLength=f.shape[1] // 4, maxLineGap=6)
    if L is None or len(L) < 6:
        return None
    ang, pes = [], []
    for x1, y1, x2, y2 in np.asarray(L).reshape(-1, 4):
        a = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 90
        ang.append(a if a <= 45 else a - 90); pes.append(np.hypot(x2 - x1, y2 - y1))
    ang, pes = np.array(ang), np.array(pes)
    h, bins = np.histogram(ang, bins=18, range=(-45, 45), weights=pes)
    dom = (bins[h.argmax()] + bins[h.argmax() + 1]) / 2
    pico = h.max() / pes.sum()
    eixo = pes[np.abs(ang) < 4].sum() / pes.sum()
    return dom if (abs(dom) >= 12 and pico >= 0.35 and eixo < 0.12) else None


def inclinacao(F, edges):
    """Câmera inclinada (holandês) por plano: o mesmo ângulo fora do eixo em 3 quadros do plano, quase
    nenhuma linha reta no eixo. Conservador de propósito (treliça e telão em diagonal enganam)."""
    out, n = [], len(F)
    for s0, s1 in zip(edges, edges[1:]):
        if s1 - s0 < 0.4:
            continue
        a = [_angulo(F[min(n - 1, int((s0 + (s1 - s0) * k) * FPS))]) for k in (0.25, 0.5, 0.75)]
        if all(x is not None for x in a) and max(a) - min(a) <= 10 and len({np.sign(x) for x in a}) == 1:
            out.append({"de": round(s0, 2), "ate": round(s1, 2), "graus": round(float(np.median(a)), 0)})
    return out


# ---------------------------------------------------------------- áudio
def le_wav(path, ch=1):
    raw = sh(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]).stdout
    return np.frombuffer(raw, np.float32)


def env_db(x, hop):
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


def separa(path, out):
    """Item 2: voz e música separadas com demucs (venv atual). Volta (voz, musica) ou (None, None)."""
    try:
        import demucs  # noqa: F401
    except ImportError:
        return None, None, "demucs não instalado neste venv (pip install demucs)"
    wav = out / "_audio.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "2", "-ar", "44100", str(wav)])
    env = dict(os.environ)
    if os.path.isdir(TORCH_HOME):
        env.setdefault("TORCH_HOME", TORCH_HOME)
    r = sh([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(out / "sep"), str(wav)], env=env, text=True)
    d = out / "sep/htdemucs/_audio"
    if not (d / "vocals.wav").exists():
        return None, None, "demucs falhou: " + r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else "demucs falhou"
    return d / "vocals.wav", d / "no_vocals.wav", None


def onset_env(x, hop=512, nfft=2048):
    n = 1 + (len(x) - nfft) // hop
    if n < 4:
        return np.zeros(1), np.zeros((1, nfft // 2 + 1))
    idx = np.arange(nfft)[None, :] + hop * np.arange(n)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(nfft), axis=1))
    L = np.log1p(S * 10)
    flux = np.r_[0, np.maximum(0, np.diff(L, axis=0)).sum(1)]
    return flux, S


def picos(v, dist, limiar):
    p = [i for i in range(1, len(v) - 1) if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] > limiar]
    out = []
    for i in p:
        if out and i - out[-1] < dist:
            if v[i] > v[out[-1]]:
                out[-1] = i
        else:
            out.append(i)
    return out


def som(path, out, cs, rapido):
    e = sh(["ffmpeg", "-nostdin", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
    res = {"lufs": float(I[-1]) if I else None, "pico_dbfs": float(P[-1]) if P else None}
    mix = le_wav(path)
    if not len(mix):
        return res, None
    hop = SR // 10                                   # 0,1 s
    em = env_db(mix, hop)
    med = np.median(em)
    # pausas dramáticas: a mistura cai 18 dB abaixo da mediana por >= 0,25 s
    res["pausas"] = [{"de": round(a / 10, 1), "ate": round(b / 10, 1), "queda_db": round(float(med - em[a:b].mean()), 0)}
                     for a, b in runs(em < med - 18, 3)]
    curvas = {"mix": em}
    voz = mus = None
    if not rapido:
        vz, mu, erro = separa(path, out)
        if erro:
            res["separacao"] = erro
        else:
            voz, mus = le_wav(vz), le_wav(mu)
    base_mus = mus if mus is not None else mix
    emu = env_db(base_mus, hop)
    curvas["musica"] = emu
    # entradas/quedas: nível médio do 1,2 s anterior contra o 1 s seguinte (pega subida gradual de 1–2 s)
    ent, que = [], []
    for i in range(15, len(emu) - 10):
        antes, depois = emu[i - 15:i - 3].mean(), emu[i:i + 10].mean()
        if depois - antes >= 6:
            if ent and i / 10 - ent[-1]["t"] <= 3:
                if depois - antes > ent[-1]["sobe_db"]:
                    ent[-1] = {"t": round(i / 10, 1), "sobe_db": round(float(depois - antes), 0)}
            else:
                ent.append({"t": round(i / 10, 1), "sobe_db": round(float(depois - antes), 0)})
        if antes - depois >= 12 and (not que or i / 10 - que[-1]["t"] > 3):
            que.append({"t": round(i / 10, 1), "cai_db": round(float(antes - depois), 0)})
    res["musica"] = {"entradas": ent, "quedas": que}
    if voz is not None:
        ev = env_db(voz, hop)
        curvas["voz"] = ev
        fala = np.convolve(ev > max(ev.max() - 30, -45), np.ones(3), "same") > 0
        curvas["fala_mask"] = fala
        m = min(len(fala), len(emu))
        fala, emu2, ev2 = fala[:m], emu[:m], ev[:m]
        if fala.sum() > 5 and (~fala).sum() > 5:
            sem_fala = emu2[~fala & (emu2 > emu2.max() - 40)]
            res["voz"] = {
                "fala_s": round(fala.sum() / 10, 1), "fala_pct": round(100 * fala.mean(), 0),
                "musica_abaixo_da_voz_db": round(float(np.median(ev2[fala]) - np.median(emu2[fala])), 0),
                "musica_abaixa_na_fala_db": round(float(np.median(sem_fala) - np.median(emu2[fala])), 0) if len(sem_fala) else None,
                "dinamica_db": round(float(np.percentile(ev2[fala], 90) - np.percentile(ev2[fala], 10)), 0),
            }
            # eco/reverb: tempo para a voz cair 20 dB depois do fim de cada fala (hop de 10 ms)
            e10 = env_db(voz, SR // 100)
            ativo = e10 > max(e10.max() - 30, -45)
            dec = []
            for a, b in runs(ativo, 30):
                ref = e10[b - 3:b].max()
                j = b
                while j < len(e10) and j - b < 100 and e10[j] > ref - 20:
                    j += 1
                if j - b < 100:
                    dec.append((j - b) / 100)
            if dec:
                d = float(np.median(dec))
                res["voz"]["cauda_s"] = round(d, 2)
                res["voz"]["eco"] = "seca" if d < 0.12 else "pouco ambiente" if d < 0.25 else "eco/reverb aparente"
            res["voz"]["compressao"] = "forte" if res["voz"]["dinamica_db"] < 9 else "média" if res["voz"]["dinamica_db"] < 15 else "natural"
    # batida e cortes na batida (onset da música)
    fl, S = onset_env(base_mus)
    fps_on = SR / 512
    if len(fl) > 50:
        x = fl - fl.mean()
        ac = np.correlate(x, x, "full")[len(x) - 1:]
        lo, hi = int(fps_on * 60 / 180), int(fps_on * 60 / 60)
        lag = lo + int(np.argmax(ac[lo:hi]))
        bpm = 60 * fps_on / lag
        pk = picos(fl, int(fps_on * 0.2), np.percentile(fl, 90))       # só ataques fortes (bumbo/caixa/impacto)
        pt = np.array(pk) / fps_on
        res["batida"] = {"bpm_aprox": round(bpm, 0)}
        if len(cs) and len(pt):
            tol = 0.05
            na = [c for c in cs if np.min(np.abs(pt - c)) <= tol]
            acaso = min(1.0, len(pt) * 2 * tol / (len(base_mus) / SR))
            res["batida"].update({"cortes_na_batida_pct": round(100 * len(na) / len(cs), 0), "acaso_pct": round(100 * acaso, 0)})
        # SFX prováveis: impacto (onset muito forte e largo) e riser/whoosh (centróide subindo >= 0,6 s antes de um evento)
        freqs = np.fft.rfftfreq(2048, 1 / SR)
        cen = (S * freqs).sum(1) / (S.sum(1) + 1e-9)
        en = 20 * np.log10(S.sum(1) + 1e-9)
        # impacto = ataque 3x mais forte que os ataques fortes do entorno (±2 s), não a batida normal da música
        w2 = int(fps_on * 2)
        imp = [round(i / fps_on, 2) for i in picos(fl, int(fps_on * 0.5), np.percentile(fl, 98))
               if fl[i] > 1.6 * np.percentile(fl[max(0, i - w2):i + w2], 90)]
        # riser/whoosh: agudos (> 4 kHz) sobem >= 12 dB em 0,5–3 s até um pico;
        # música abafada (filtro passa-baixa): agudos caem >= 15 dB enquanto o volume geral cai bem menos
        k = int(fps_on * 0.25)
        hf = np.convolve(20 * np.log10(S[:, freqs > 4000].sum(1) + 1e-9), np.ones(k) / k, "same")
        en_ = np.convolve(en, np.ones(k) / k, "same")
        fmask = curvas.get("fala_mask")
        em_fala = lambda a, b: fmask is not None and fmask[int(a * 10):int(b * 10) + 1].mean() > 0.3 if fmask is not None and int(a * 10) < len(fmask) else False  # noqa: E731
        ris, abaf = [], []
        borda = int(fps_on * 0.5)
        for i in range(borda, len(hf) - borda):
            jan = hf[max(borda, i - int(fps_on * 3)):i + 1]
            viz = hf[max(0, i - int(fps_on * 0.3)):i + int(fps_on * 0.3)]
            if hf[i] >= viz.max() and hf[i] - jan.min() >= 15:
                a = i - (len(jan) - 1 - jan.argmin())
                seg = hf[a:i + 1]
                if i - a >= fps_on * 0.5 and np.corrcoef(np.arange(len(seg)), seg)[0, 1] > 0.85:
                    ris.append({"de": round(a / fps_on, 2), "fim": round(i / fps_on, 2), "sobe_db": round(float(hf[i] - jan.min()), 0)})
            if hf[i] <= viz.min() and jan.max() - hf[i] >= 20:
                a = i - (len(jan) - 1 - jan.argmax())
                if (en_[a] - en_[i]) < (jan.max() - hf[i]) - 10 and not em_fala(a / fps_on, i / fps_on):
                    abaf.append({"de": round(a / fps_on, 2), "ate": round(i / fps_on, 2), "agudos_caem_db": round(float(jan.max() - hf[i]), 0)})

        def junta(L, k0, k1, kv):
            out = []
            for r in sorted(L, key=lambda r: r[k0]):
                if out and r[k0] <= out[-1][k1] + 0.3:
                    out[-1][k1] = max(out[-1][k1], r[k1]); out[-1][kv] = max(out[-1][kv], r[kv])
                else:
                    out.append(dict(r))
            return out
        ris, abaf = junta(ris, "de", "fim", "sobe_db"), junta(abaf, "de", "ate", "agudos_caem_db")
        res["sfx_provaveis"] = {"impactos": imp, "risers": ris, "musica_abafada": abaf,
                                "obs": "detecção por energia na música separada; confirme de ouvido"}
    return res, curvas


# ---------------------------------------------------------------- fala
def modelo_whisper():
    if WHISPER and os.path.exists(WHISPER):
        return WHISPER
    for m in ("ggml-large-v3-turbo-q5_0.bin", "ggml-large-v3-turbo.bin", "ggml-large-v3.bin", "ggml-medium.bin", "ggml-base.bin"):
        p = Path.home() / ".whisper_models" / m
        if p.exists():
            return str(p)
    return None


def transcreve(path, out, curvas):
    """Item 4: whisper-cli local na voz separada; descarta alucinação e trecho sem voz."""
    m, cli = modelo_whisper(), shutil.which("whisper-cli")
    if not (m and cli):
        return {"erro": "whisper-cli ou modelo local ausente (~/.whisper_models)"}
    vz = out / "sep/htdemucs/_audio/vocals.wav"
    src = vz if vz.exists() else Path(path)
    w16 = out / "_voz16k.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "16000", str(w16)])
    sh([cli, "-m", m, "-l", "pt", "-osrt", "-of", str(out / "fala"), "-f", str(w16)])
    srt = out / "fala.srt"
    if not srt.exists():
        return {"erro": "whisper-cli não gerou SRT"}
    fala_mask = curvas.get("fala_mask") if curvas else None
    segs, fora, vistos = [], [], []
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()  # noqa: E731
    for bloco in srt.read_text(errors="ignore").strip().split("\n\n"):
        L = bloco.strip().splitlines()
        if len(L) < 3:
            continue
        a, b = [sum(float(x) * k for x, k in zip(s.replace(",", ".").split(":"), (3600, 60, 1))) for s in L[1].split(" --> ")]
        txt = " ".join(L[2:]).strip()
        voz_pct = None
        if fala_mask is not None:
            i0, i1 = int(a * 10), max(int(a * 10) + 1, int(b * 10))
            fm = fala_mask[i0:i1]
            voz_pct = float(fm.mean()) if len(fm) else 0.0
            on = np.flatnonzero(fm)
            if len(on):                                   # o Whisper estica o trecho sobre a música: corta na voz real
                a, b = (i0 + on[0]) / 10, (i0 + on[-1] + 1) / 10
        n_ = norm(txt)
        repete = any(n_ and (n_ == v or (len(n_) > 15 and (n_ in v or v.endswith(n_[-25:])))) for v in vistos)
        if ALUCINA.search(txt) or (voz_pct is not None and voz_pct < 0.2) or repete:
            fora.append(txt); continue
        vistos.append(n_)
        segs.append({"de": round(a, 1), "ate": round(b, 1), "texto": txt})
    return {"segmentos": segs, "descartados": fora}


# ---------------------------------------------------------------- legenda
def garante_ocr():
    if OCR_BIN.exists():
        return True
    src = AQUI / "ocr_quadros.swift"
    if not (src.exists() and shutil.which("swiftc")):
        return False
    OCR_BIN.parent.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "TMPDIR"}      # swiftc quebra com TMPDIR no SSD
    sh(["swiftc", "-O", str(src), "-o", str(OCR_BIN)], env=env)
    return OCR_BIN.exists()


def legenda_ocr(path, out, dur, fala):
    """Item 3: acha a legenda pelo texto que muda no tempo na mesma faixa e bate com a fala."""
    if not garante_ocr():
        return {"erro": "OCR indisponível (precisa de swiftc / macOS)"}
    d = out / "_ocr"
    shutil.rmtree(d, ignore_errors=True); d.mkdir()
    sh(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=2,scale=540:-2", str(d / "q%04d.png")])
    imgs = sorted(d.glob("q*.png"))
    linhas = []
    for i in range(0, len(imgs), 40):
        linhas += sh([str(OCR_BIN)] + [str(p) for p in imgs[i:i + 40]], text=True).stdout.splitlines()
    shutil.rmtree(d, ignore_errors=True)
    obs = []
    for l in linhas:
        try:
            o = json.loads(l)
        except ValueError:
            continue
        if o["conf"] >= 0.5 and len(o["texto"].strip()) >= 2:
            o["t"] = (int(Path(o["img"]).stem[1:]) - 1) / 2
            obs.append(o)
    if not obs:
        return {"achou": False}
    palavras = set(re.findall(r"\w+", " ".join(s["texto"] for s in fala.get("segmentos", [])).lower())) if fala else set()
    faixas = {}
    for o in obs:
        faixas.setdefault(round((o["y"] + o["h"] / 2) * 25) / 25, []).append(o)      # faixas de 4%
    melhor, nota = None, 0
    for yk, L in faixas.items():
        textos = {o["texto"].strip().lower() for o in L}
        if len(textos) < 3:
            continue
        ws = re.findall(r"\w+", " ".join(textos))
        bate = sum(w in palavras for w in ws) / max(1, len(ws)) if palavras else 0.5
        s = len(textos) * (0.3 + bate)
        if s > nota:
            melhor, nota = (yk, L, textos, bate), s
    fixos = sorted({o["texto"] for o in obs if sum(p["texto"] == o["texto"] for p in obs) >= 6})[:6]
    if not melhor:
        return {"achou": False, "textos_fixos": fixos}
    yk, L, textos, bate = melhor
    letras = "".join(o["texto"] for o in L if o["texto"].strip())
    al = [c for c in letras if c.isalpha()]
    trocas = sum(1 for a, b in zip(L, L[1:]) if a["texto"] != b["texto"])
    tempo_na_tela = len({o["t"] for o in L}) / 2
    return {"achou": True, "y_centro_pct": round(100 * yk, 0),
            "altura_letra_pct": round(100 * float(np.median([o["h"] for o in L])), 1),
            "largura_bloco_pct": round(100 * float(np.median([o["w"] for o in L])), 0),
            "centralizada": bool(abs(np.median([o["x"] + o["w"] / 2 for o in L]) - 0.5) < 0.08),
            "minusculas_pct": round(100 * sum(c.islower() for c in al) / max(1, len(al)), 0),
            "palavras_por_bloco": int(np.median([len(o["texto"].split()) for o in L])),
            "troca_media_s": round(tempo_na_tela / max(1, trocas), 2), "na_tela_s": tempo_na_tela,
            "bate_com_fala_pct": round(100 * bate, 0), "exemplos": sorted(textos)[:4], "textos_fixos": fixos}


# ---------------------------------------------------------------- folha
def linha_tempo(path, out, dur, cs, ef, incl, sm, curvas, fala):
    """Item 5: quadros em cima e trilhas de marcadores embaixo, na mesma escala de tempo."""
    nq = 24
    W = 1680
    tw = W // nq
    Fq = frames(path, tw, fps=nq / dur)
    th = Fq.shape[1]
    lab = 120
    tracks = [("cortes", (170, 170, 170)), ("flash", (0, 230, 255)), ("freeze", (255, 220, 0)), ("P&B / preto", (255, 255, 255)),
              ("inclinada/rampa", (200, 120, 255)), ("fala", (90, 220, 90)), ("musica (dB)", (0, 150, 255)),
              ("pausa / SFX", (80, 80, 255))]
    tk = 22
    H = th + 18 + tk * len(tracks) + 8
    img = np.full((H, W + lab, 3), 18, np.uint8)
    for i, f in enumerate(Fq[:nq]):
        img[:th, lab + i * tw: lab + i * tw + f.shape[1]] = f
    X = lambda s: int(lab + min(max(s, 0), dur) / dur * W)  # noqa: E731
    fnt = cv2.FONT_HERSHEY_SIMPLEX
    for s in range(0, int(dur) + 1, 5):
        cv2.line(img, (X(s), th), (X(s), H), (45, 45, 45), 1)
        cv2.putText(img, f"{s}s", (X(s) + 2, th + 13), fnt, 0.38, (200, 200, 200), 1)
    for k, (nome, cor) in enumerate(tracks):
        y0 = th + 18 + k * tk
        cv2.putText(img, nome, (4, y0 + 15), fnt, 0.4, cor, 1)
        if nome == "cortes":
            for c in cs:
                cv2.line(img, (X(c), y0 + 2), (X(c), y0 + tk - 3), cor, 1)
        elif nome == "flash":
            for f in ef["flashes"]:
                cv2.rectangle(img, (X(f["t"]) - 2, y0 + 2), (X(f["t"]) + 2, y0 + tk - 3), cor, -1)
        elif nome == "freeze":
            for f in ef["freezes"]:
                cv2.rectangle(img, (X(f["de"]), y0 + 2), (max(X(f["ate"]), X(f["de"]) + 3), y0 + tk - 3), cor, -1)
        elif nome.startswith("P&B"):
            for f in ef["pb"]:
                cv2.rectangle(img, (X(f["de"]), y0 + 2), (max(X(f["ate"]), X(f["de"]) + 3), y0 + tk - 3), cor, -1)
            for f in ef["preto"]:
                cv2.rectangle(img, (X(f["de"]), y0 + 2), (max(X(f["ate"]), X(f["de"]) + 3), y0 + tk - 3), (90, 90, 90), -1)
        elif nome.startswith("inclinada"):
            for f in incl + ef["rampas"]:
                cv2.rectangle(img, (X(f["de"]), y0 + 5), (max(X(f["ate"]), X(f["de"]) + 3), y0 + tk - 6), cor, -1)
        elif nome == "fala":
            for s in (fala or {}).get("segmentos", []):
                cv2.rectangle(img, (X(s["de"]), y0 + 2), (max(X(s["ate"]), X(s["de"]) + 3), y0 + tk - 3), cor, -1)
            if curvas is not None and curvas.get("fala_mask") is not None and not (fala or {}).get("segmentos"):
                for a, b in runs(curvas["fala_mask"], 2):
                    cv2.rectangle(img, (X(a / 10), y0 + 6), (X(b / 10), y0 + tk - 7), cor, -1)
        elif nome.startswith("musica") and curvas:
            c = curvas.get("musica", curvas["mix"])
            lo, hi = np.percentile(c, 5), c.max()
            pts = [(X(i / 10), int(y0 + tk - 3 - (min(max(v, lo), hi) - lo) / max(1, hi - lo) * (tk - 5))) for i, v in enumerate(c)]
            cv2.polylines(img, [np.array(pts, np.int32)], False, cor, 1)
        elif nome.startswith("pausa"):
            for p in sm.get("pausas", []):
                cv2.rectangle(img, (X(p["de"]), y0 + 2), (max(X(p["ate"]), X(p["de"]) + 3), y0 + tk - 3), cor, -1)
            sf = sm.get("sfx_provaveis", {})
            for s in sf.get("impactos", []):
                cv2.circle(img, (X(s), y0 + tk // 2), 4, (255, 0, 255), -1)
            for r in sf.get("risers", []):          # rampa subindo = riser/whoosh
                cv2.line(img, (X(r["de"]), y0 + tk - 4), (X(r["fim"]), y0 + 3), (255, 0, 255), 2)
            for r in sf.get("musica_abafada", []):  # rampa descendo = música abafada (passa-baixa)
                cv2.line(img, (X(r["de"]), y0 + 3), (X(r["ate"]), y0 + tk - 4), (255, 160, 0), 2)
    cv2.imwrite(str(out / "linha_tempo.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])


# ---------------------------------------------------------------- receita
def receita(est):
    """Item 5: o que encaixa no tema do reel-motion e o que ainda é montagem no DaVinci."""
    c, ef, sm, lg = est["cor"], est["efeitos"], est["som"], est.get("legenda", {})
    tema = {"theme.mediaFilter": f"saturate({min(1.3, max(0.4, c['saturacao'] / 0.45)):.2f}) contrast({min(1.4, max(0.8, c['contraste'] / 0.62)):.2f})"}
    if lg.get("achou"):
        tema["theme.caption"] = {"y_pct": lg["y_centro_pct"], "altura_letra_pct": lg["altura_letra_pct"],
                                 "caixa": "minúscula" if lg["minusculas_pct"] > 85 else "mista" if lg["minusculas_pct"] > 30 else "MAIÚSCULA",
                                 "palavras_por_bloco": lg["palavras_por_bloco"], "fundo": "verificar na folha"}
    v = sm.get("voz", {})
    if v.get("musica_abaixo_da_voz_db") is not None:
        tema["regras"] = f"música ~{v['musica_abaixo_da_voz_db']:.0f} dB abaixo da voz; abaixa ~{v.get('musica_abaixa_na_fala_db')} dB quando entra a fala"
    mont = []
    fl = ef["flashes"]
    if fl:
        ts = [f["t"] for f in fl]
        gaps = np.diff(ts) if len(ts) > 1 else np.array([0])
        meio = len(gaps) // 2
        mont.append(f"flash de exposição: {len(fl)}x, ~{int(np.median([f['quadros'] for f in fl]))} quadros acima da meia altura "
                    f"(rampa total ~{2 * int(np.median([f['quadros'] for f in fl]))}), "
                    f"{round(100 * np.mean([f['no_corte'] for f in fl]))}% em cima do corte; intervalo {np.median(gaps[:meio] if meio else gaps):.1f} s "
                    f"na 1ª metade → {np.median(gaps[meio:]):.1f} s na 2ª")
    for f in ef["freezes"]:
        mont.append(f"freeze {f['dur']} s em {f['de']} s" + (f", escurece {f['escureceu_pct']:.0f}%" if f.get("escureceu_pct") else ""))
    for p in ef["pb"]:
        mont.append(f"P&B {p['de']}–{p['ate']} s")
    for p in sm.get("pausas", []):
        mont.append(f"pausa no som {p['de']}–{p['ate']} s (−{p['queda_db']:.0f} dB)")
    sf = sm.get("sfx_provaveis", {})
    for r in sf.get("risers", []):
        mont.append(f"riser/whoosh {r['de']}→{r['fim']} s (agudos +{r['sobe_db']:.0f} dB)")
    for r in sf.get("musica_abafada", []):
        mont.append(f"música abafada (passa-baixa) {r['de']}→{r['ate']} s (agudos −{r['agudos_caem_db']:.0f} dB)")
    if sf.get("impactos"):
        mont.append("impactos prováveis em " + ", ".join(f"{s} s" for s in sf["impactos"]))
    for e in sm.get("musica", {}).get("entradas", []):
        mont.append(f"música sobe {e['sobe_db']:.0f} dB em {e['t']} s")
    if est.get("inclinada"):
        mont.append(f"câmera inclinada em {len(est['inclinada'])} plano(s): " + ", ".join(f"{i['de']}s ({i['graus']:+.0f}°)" for i in est["inclinada"][:4]))
    b = sm.get("batida", {})
    if b.get("cortes_na_batida_pct") is not None:
        mont.append(f"{b['cortes_na_batida_pct']:.0f}% dos cortes na batida (acaso daria {b['acaso_pct']:.0f}%), ~{b['bpm_aprox']:.0f} BPM")
    return {"tema_reel_motion": tema, "montagem_davinci": mont,
            "obs": "flash, freeze, P&B e pausa ainda não têm chave no tema do reel-motion: montar no DaVinci ou estender o motor"}


# ---------------------------------------------------------------- main
def main():
    ref = sys.argv[1]
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path(ref).with_suffix("").parent / (Path(ref).stem + "_estilo")
    rapido = "--rapido" in sys.argv
    out.mkdir(parents=True, exist_ok=True)
    W, H, fr, fps, dur = probe(ref)
    F = frames(ref, SW, fps=FPS)
    n, h, w = F.shape[:3]
    cs = [c for c in cuts(ref) if 0.2 < c < dur - 0.2]
    edges = [0.0] + cs + [dur]
    shots = np.diff(edges)
    det = cv2.FaceDetectorYN.create(YUNET, "", (w, h), 0.7)
    fs, fx = [], []
    for f in F[:: 2]:
        _, faces = det.detect(f)
        if faces is not None and len(faces):
            b = max(faces, key=lambda z: z[2])
            fs.append(b[3] / h); fx.append((b[0] + b[2] / 2) / w)
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in F[:: 4]])
    lab = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2LAB) for f in F[:: 4]]).astype(np.float32)
    ef, _ = efeitos(ref, fps, cs)
    incl = inclinacao(F, edges)
    sm, curvas = som(ref, out, cs, rapido)
    fala = None if rapido else transcreve(ref, out, curvas)
    lg = {"erro": "pulado (--rapido)"} if rapido else legenda_ocr(ref, out, dur, fala)
    est = {
        "formato": f"{W}x{H}", "qps": fr, "duracao_s": round(dur, 2),
        "ritmo": {"planos": int(len(shots)), "plano_mediano_s": round(float(np.median(shots)), 2),
                  "cortes_por_10s": round(len(cs) / dur * 10, 2), "cortes_s": [round(c, 2) for c in cs]},
        "rosto": {"presente_pct": round(100 * len(fs) / max(1, len(F[:: 2])), 0),
                  "altura_mediana_pct_do_quadro": round(100 * float(np.median(fs)), 1) if fs else None,
                  "posicao_x_mediana": round(float(np.median(fx)), 2) if fx else None},
        "cor": {"brilho": round(float(hsv[..., 2].mean()) / 255, 2), "saturacao": round(float(hsv[..., 1].mean()) / 255, 2),
                "contraste": round(float(lab[..., 0].std()) / 100, 2), "temperatura": round(float(lab[..., 2].mean() - 128), 1)},
        "efeitos": ef, "inclinada": incl, "som": sm, "fala": fala, "legenda": lg,
    }
    est["receita"] = receita(est)
    (out / "estilo.json").write_text(json.dumps(est, ensure_ascii=False, indent=1))
    mids = [(a + b) / 2 for a, b in zip(edges, edges[1:])][:16]
    tiles = [cv2.resize(F[min(n - 1, int(t * FPS))], (180, int(180 * h / w))) for t in mids]
    if tiles:
        rows = [np.hstack(tiles[i:i + 8] + [np.zeros_like(tiles[0])] * (8 - len(tiles[i:i + 8]))) for i in range(0, len(tiles), 8)]
        cv2.imwrite(str(out / "planos.jpg"), np.vstack(rows))
    linha_tempo(ref, out, dur, cs, ef, incl, sm, curvas, fala)
    # relatório completo
    R = [f"# Referência: {Path(ref).name}", "", f"{W}x{H}, {dur:.1f} s · {len(shots)} planos, mediano {np.median(shots):.2f} s",
         "", "## Receita — tema reel-motion", "```json", json.dumps(est["receita"]["tema_reel_motion"], ensure_ascii=False, indent=1), "```",
         "", "## Receita — montagem (DaVinci)"] + [f"- {m}" for m in est["receita"]["montagem_davinci"]]
    if fala and fala.get("segmentos"):
        R += ["", "## Fala"] + [f"- {s['de']}–{s['ate']} s: {s['texto']}" for s in fala["segmentos"]]
        if fala.get("descartados"):
            R += [f"- (descartado como alucinação/sem voz: {' | '.join(fala['descartados'])})"]
    if sm.get("voz"):
        R += ["", "## Voz", "- " + json.dumps(sm["voz"], ensure_ascii=False)]
    if sm.get("sfx_provaveis"):
        R += ["", "## SFX prováveis", "- " + json.dumps(sm["sfx_provaveis"], ensure_ascii=False)]
    if lg.get("achou"):
        R += ["", "## Legenda (OCR)", "- " + json.dumps({k: v for k, v in lg.items() if k != "textos_fixos"}, ensure_ascii=False)]
    (out / "relatorio.md").write_text("\n".join(R) + "\n")
    # saída curta (<= 15 linhas)
    v = sm.get("voz", {})
    linhas = [f"{W}x{H} {dur:.1f}s · {len(shots)} planos (mediano {np.median(shots):.2f}s, {len(cs) / dur * 10:.1f} cortes/10s)",
              f"efeitos: {len(ef['flashes'])} flashes · {len(ef['freezes'])} freeze · {len(ef['pb'])} P&B · {len(ef['preto'])} preto · "
              f"{len(incl)} inclinada · {len(ef['rampas'])} rampa provável",
              f"som: {sm.get('lufs')} LUFS · {len(sm.get('pausas', []))} pausa(s) · entradas da música {[e['t'] for e in sm.get('musica', {}).get('entradas', [])]}"]
    if v:
        linhas.append(f"voz: {v.get('fala_s')}s de fala ({v.get('fala_pct'):.0f}%) · {v.get('eco', '?')} · compressão {v.get('compressao')} · "
                      f"música {v.get('musica_abaixo_da_voz_db')} dB abaixo, abaixa {v.get('musica_abaixa_na_fala_db')} dB na fala")
    elif sm.get("separacao"):
        linhas.append("voz: " + sm["separacao"])
    if sm.get("batida", {}).get("cortes_na_batida_pct") is not None:
        b = sm["batida"]; linhas.append(f"batida: ~{b['bpm_aprox']:.0f} BPM · {b['cortes_na_batida_pct']:.0f}% dos cortes na batida (acaso {b['acaso_pct']:.0f}%)")
    if lg.get("achou"):
        linhas.append(f"legenda: y {lg['y_centro_pct']:.0f}% · letra {lg['altura_letra_pct']}% · {lg['minusculas_pct']:.0f}% minúsculas · "
                      f"{lg['palavras_por_bloco']} palavras/bloco · troca {lg['troca_media_s']}s")
    elif lg.get("erro"):
        linhas.append("legenda: " + lg["erro"])
    if fala and fala.get("segmentos") is not None:
        linhas.append(f"fala: {len(fala['segmentos'])} trechos · {len(fala.get('descartados', []))} descartados (alucinação/sem voz)")
    elif fala:
        linhas.append("fala: " + fala.get("erro", "?"))
    linhas += [f"relatório: {out / 'relatorio.md'}", f"folhas: {out / 'linha_tempo.jpg'} · {out / 'planos.jpg'}"]
    print("\n".join(linhas[:15]))
    for p in ("_audio.wav", "_voz16k.wav"):
        (out / p).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
