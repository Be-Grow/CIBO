#!/usr/bin/env python3
"""Mede o estilo de um vídeo de referência para o CIBO copiar o "jeito", não o conteúdo.

uso: analisa_referencia.py REFERENCIA.mp4 [--out PASTA]   (venv da content-hub: opencv + numpy)

Mede, com números: formato e duração; ritmo de corte (planos, duração mediana, cortes por 10 s);
enquadramento (tamanho e posição do rosto, YuNet); faixa provável da legenda e quanto tempo cada
bloco fica na tela; cor (brilho, contraste, saturação, temperatura); som (LUFS, pico, transientes
por minuto como estimativa de SFX). Grava `estilo.json`, `planos.jpg` (um quadro por plano, até
16) e imprime sugestões de ajuste do CIBO (ritmo, preset de legenda, enquadramento, cor). Use no
briefing quando o editor mandar uma referência ("quero nesse estilo"). Ideia de
`edenfunf/reelmimic` e `krusemediallc/video-editor-agent` (estilo de um reel de referência).
"""
import json, os, re, subprocess, sys
from pathlib import Path
import cv2
import numpy as np

YUNET = os.environ.get("YUNET", str(Path(__file__).resolve().parents[2] / "content-hub" / "assets" / "yunet.onnx"))
SW, SH, FPS = 270, 480, 4          # análise em 270 px de largura, 4 qps


def frames(path, w):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", path],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    W, H = v["width"], v["height"]
    h = int(round(w * H / W / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw[: n * w * h * 3], np.uint8).reshape(n, h, w, 3), float(d["format"]["duration"]), W, H, v["r_frame_rate"]


def cuts(path):
    e = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-vf", "scdet=threshold=12:sc_pass=0", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", e)]


def audio(path):
    e = subprocess.run(["ffmpeg", "-nostdin", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-af", "highpass=f=2500",
                          "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if not len(x):
        return {"lufs": None}
    n = 160
    env = 20 * np.log10(np.sqrt((x[: len(x) // n * n].reshape(-1, n) ** 2).mean(1)) + 1e-9)
    base = np.convolve(env, np.ones(50) / 50, "same")
    on = np.flatnonzero((env[1:] - base[1:] > 12) & (env[1:] > env[:-1] + 6)) + 1
    on = [o for j, o in enumerate(on) if j == 0 or o - on[j - 1] > 30]   # 0,3 s entre transientes
    dur = len(x) / 16000
    return {"lufs": float(I[-1]) if I else None, "pico_dbfs": float(P[-1]) if P else None,
            "transientes_por_min": round(len(on) / dur * 60, 1)}


def main():
    ref = sys.argv[1]
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path(ref).with_suffix("").parent / (Path(ref).stem + "_estilo")
    out.mkdir(parents=True, exist_ok=True)
    F, dur, W, H, fr = frames(ref, SW)
    n, h, w = F.shape[:3]
    # ritmo
    cs = [c for c in cuts(ref) if 0.2 < c < dur - 0.2]
    edges = [0.0] + cs + [dur]
    shots = np.diff(edges)
    # rosto
    det = cv2.FaceDetectorYN.create(YUNET, "", (w, h), 0.7)
    fs, fx = [], []
    for f in F[:: 2]:
        _, faces = det.detect(f)
        if faces is not None and len(faces):
            b = max(faces, key=lambda z: z[2])
            fs.append(b[3] / h); fx.append((b[0] + b[2] / 2) / w)
    # legenda: faixa horizontal com mais borda "de texto" que muda no tempo
    g = np.stack([cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 120, 240) for f in F]).astype(np.float32) / 255
    bands = 24
    dens = g.reshape(n, bands, h // bands, w)[:, :, :, :].mean(axis=(2, 3)) if h % bands == 0 else \
        np.stack([g[:, i * h // bands:(i + 1) * h // bands].mean(axis=(1, 2)) for i in range(bands)], 1)
    var = dens.std(0)
    cb = int(np.argmax(var[2:-2]) + 2)
    sig = dens[:, cb]
    ch = np.flatnonzero(np.abs(np.diff(sig)) > max(0.004, sig.std() * 0.8))
    cap_hold = (n / FPS) / max(1, len(ch)) if len(ch) else None
    # cor
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in F[:: 4]])
    lab = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2LAB) for f in F[:: 4]]).astype(np.float32)
    est = {
        "formato": f"{W}x{H}", "qps": fr, "duracao_s": round(dur, 2),
        "ritmo": {"planos": int(len(shots)), "plano_mediano_s": round(float(np.median(shots)), 2),
                  "cortes_por_10s": round(len(cs) / dur * 10, 2)},
        "rosto": {"presente_pct": round(100 * len(fs) / max(1, len(F[:: 2])), 0),
                  "altura_mediana_pct_do_quadro": round(100 * float(np.median(fs)), 1) if fs else None,
                  "posicao_x_mediana": round(float(np.median(fx)), 2) if fx else None},
        "legenda": {"faixa_y_pct": round(100 * (cb + 0.5) / bands, 0), "troca_media_s": round(cap_hold, 2) if cap_hold else None},
        "cor": {"brilho": round(float(hsv[..., 2].mean()) / 255, 2), "saturacao": round(float(hsv[..., 1].mean()) / 255, 2),
                "contraste": round(float(lab[..., 0].std()) / 100, 2),
                "temperatura": round(float(lab[..., 2].mean() - 128), 1)},   # >0 quente, <0 fria
        "som": audio(ref),
    }
    # sugestões para o CIBO
    sug = []
    r = est["ritmo"]
    sug.append(f"ritmo: plano mediano {r['plano_mediano_s']} s, {r['cortes_por_10s']} cortes/10 s"
               + (" — corte mais agressivo (pausas de 0,1 s)" if r["plano_mediano_s"] < 2.5 else " — ritmo equilibrado"))
    hold = est["legenda"]["troca_media_s"]
    if hold:
        sug.append("legenda: " + ("`CAP_PRESET=veredito` (blocos curtos e rápidos)" if hold < 0.9 else
                                  "`CAP_PRESET=historia`" if hold < 1.6 else "`CAP_PRESET=aula` (blocos longos)")
                   + f", faixa em ~{est['legenda']['faixa_y_pct']:.0f}% da altura")
    fh = est["rosto"]["altura_mediana_pct_do_quadro"]
    if fh:
        sug.append("enquadramento: " + ("close (rosto grande)" if fh > 14 else "plano médio" if fh > 8 else "aberto") + f" — rosto com {fh}% da altura")
    c = est["cor"]
    sug.append(f"cor: saturação {c['saturacao']}, contraste {c['contraste']}, temperatura {c['temperatura']:+} "
               + ("(quente)" if c["temperatura"] > 4 else "(fria)" if c["temperatura"] < -4 else "(neutra)"))
    if est["som"].get("transientes_por_min") is not None:
        sug.append(f"som: {est['som']['lufs']} LUFS, ~{est['som']['transientes_por_min']} transientes/min (SFX + ataques de fala)")
    est["sugestoes"] = sug
    (out / "estilo.json").write_text(json.dumps(est, ensure_ascii=False, indent=1))
    # folha: um quadro no meio de cada plano (até 16)
    mids = [(a + b) / 2 for a, b in zip(edges, edges[1:])][:16]
    tiles = [cv2.resize(F[min(n - 1, int(t * FPS))], (180, int(180 * h / w))) for t in mids]
    if tiles:
        rows = [np.hstack(tiles[i:i + 8] + [np.zeros_like(tiles[0])] * (8 - len(tiles[i:i + 8]))) for i in range(0, len(tiles), 8)]
        cv2.imwrite(str(out / "planos.jpg"), np.vstack(rows))
    print(json.dumps({k: v for k, v in est.items() if k != "sugestoes"}, ensure_ascii=False))
    print("\n".join("- " + s for s in sug))
    print(f"folha: {out / 'planos.jpg'}")


if __name__ == "__main__":
    main()
