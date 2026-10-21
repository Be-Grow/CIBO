#!/usr/bin/env python3
"""QA de áudio que "escuta" por medição: o que o editor ouviria e reprovaria.

uso: JOB=job.json audio_qa.py [corte01 ...] [--clicks ARQ|'.../x_{k}.wav'] [--clicks-final] [--final ARQ]
(--clicks-final: os tempos do arquivo de cliques já incluem a capa, como no reaudio.py)

Cruza três sinais do motor: a voz cortada (`WORK/A_<clip>.mp4`, sem trilha nem clique), os
cliques (`WORK/clicks_<clip>.wav` ou `--clicks`) e o MP4 entregue. Tempos na saída são do
arquivo entregue (capa de 1 quadro incluída). Checa:
  - clique no meio de palavra (voz ativa e longe do começo de uma palavra) ou alto demais
    (pico do clique acima do nível local da mixagem): o "click bizarro no meio das falas";
  - trilha: presente desde o primeiro segundo e abaixo da voz (a diferença entre os trechos
    com voz e as pausas deve ficar entre ~8 e ~28 dB);
  - emenda cortando palavra: voz forte dos dois lados da emenda, fora do fade;
  - última palavra engolida: voz ainda ativa nos últimos 120 ms do vídeo.
Uma linha por corte; só os problemas são detalhados (até 5 por tipo).
"""
if __name__ == '__main__':   # saída curta + log completo em 05_qa/logs (client-router/scripts/saida_curta.py)
    import os as _o, sys as _s; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), '../../client-router/scripts')); import saida_curta; saida_curta.curta()
import json, os, subprocess, sys
import numpy as np

SR = 16000
HOP = 0.01   # janelas de 10 ms


def audio(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def env_db(x):
    n = int(SR * HOP)
    m = len(x) // n
    r = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r + 1e-9)


def at(e, t):
    i = int(round(t / HOP))
    return e[min(max(i, 0), len(e) - 1)]


def win(e, a, b):
    i, j = int(max(a, 0) / HOP), int(max(b, 0) / HOP)
    return e[i:max(j, i + 1)]


def check_clip(k, c, work, outdir, clicks_arg=None, final_arg=None, clicks_final=False):
    cd = 1 / 30
    voice = audio(f"{work}/A_{k}.mp4")
    ve = env_db(voice)
    act = ve > (np.percentile(ve, 95) - 22)          # voz ativa: até 22 dB abaixo do forte
    speech = np.median(ve[act]) if act.any() else -30
    final = final_arg or os.path.join(outdir, (c.get("filename") or k) + ".mp4")
    fe = env_db(audio(final))
    probs = {"clique": [], "trilha": [], "emenda": [], "fim": []}

    # --- cliques
    cpath = clicks_arg or f"{work}/clicks_{k}.wav"
    nclk = 0
    if os.path.exists(cpath):
        ce = env_db(audio(cpath))
        on = np.flatnonzero((ce[1:] > -45) & (ce[:-1] <= -45)) + 1
        # um clique de câmera tem 3–4 transientes internos: junta os que estão a < 0,35 s
        on = [x for j, x in enumerate(on) if j == 0 or x - on[j - 1] > 35]
        # começos de palavra: início de cada bloco de legenda (é onde o motor põe o clique)
        try:
            starts = np.array([b["s"] for b in json.load(open(f"{work}/captions_{k}.json"))["caps"]])
        except (OSError, ValueError, KeyError):
            starts = np.array([])
        for i in on:
            t = i * HOP - (cd if clicks_final else 0)     # tempo do clique na voz (sem a capa)
            i = int(round(t / HOP))
            nclk += 1
            peak = ce[int(round((t + (cd if clicks_final else 0)) / HOP)):][:8].max()
            local = np.percentile(win(fe, t + cd - 0.3, t + cd + 0.3), 90)
            # começo de palavra: perto do início de um bloco de legenda, ou silêncio logo antes
            onset = (len(starts) and np.abs(starts - t).min() <= 0.15) or not act[max(0, i - 8):i + 1].all()
            mid = act[min(i, len(act) - 1)] and not onset
            loud = peak > local + 1.0
            if mid or loud:
                probs["clique"].append(f"{t + cd:.2f}s " + ("no meio da fala" if mid else "")
                                       + (" alto (+%.0f dB sobre a mix)" % (peak - local) if loud else ""))

    # --- trilha: compara janelas com voz e pausas no final
    n = min(len(fe), len(act) + int(cd / HOP))
    a_final = np.zeros(n, bool)
    a_final[int(cd / HOP):] = act[: n - int(cd / HOP)]
    with_v, pause = fe[:n][a_final], fe[:n][~a_final & (fe[:n] > -90)]
    gap = (np.median(with_v) - np.median(pause)) if len(with_v) and len(pause) else None
    first = win(fe, cd, 1.0)
    if c.get("music"):
        if len(first) and np.median(first) < -50:
            probs["trilha"].append("trilha inaudível no 1º segundo")
        if gap is not None and gap < 8:
            probs["trilha"].append(f"voz só {gap:.0f} dB acima das pausas (trilha alta)")
        if gap is not None and gap > 28:
            probs["trilha"].append(f"pausas {gap:.0f} dB abaixo da voz (trilha some)")

    # --- emendas
    t = 0.0
    for a, b in c["keeps"][:-1]:
        t += b - a
        l, r = win(ve, t - 0.09, t - 0.04), win(ve, t + 0.04, t + 0.09)
        if len(l) and len(r) and l.mean() > speech - 6 and r.mean() > speech - 6:
            probs["emenda"].append(f"{t + cd:.2f}s voz forte dos dois lados")

    # --- fim
    end = len(voice) / SR
    if win(ve, end - 0.12, end).mean() > speech - 8:
        probs["fim"].append(f"voz ativa nos últimos 120 ms ({end + cd:.2f}s): palavra pode ter sido engolida")

    bad = sum(len(v) for v in probs.values())
    print(f"{'OK  ' if not bad else 'VER '} {k}: {nclk} cliques, voz−pausas {gap:.0f} dB" if gap is not None
          else f"{'OK  ' if not bad else 'VER '} {k}: {nclk} cliques")
    for kind, v in probs.items():
        for x in v[:5]:
            print(f"     {kind}: {x}")
    return bad


def main():
    args = sys.argv[1:]
    opt = {}
    cf = "--clicks-final" in args
    if cf:
        args.remove("--clicks-final")
    for o in ("--clicks", "--final"):
        if o in args:
            i = args.index(o)
            opt[o] = args[i + 1]
            del args[i:i + 2]
    job = json.load(open(os.environ["JOB"]))
    work = os.environ.get("WORK", job.get("work", "./work"))
    plan = json.load(open(os.path.join(work, "plan.json")))
    ks = args or list(plan)
    bad = 0
    for k in ks:
        clk = opt.get("--clicks")
        if clk and "{k}" in clk:
            clk = clk.format(k=k)
        bad += check_clip(k, plan[k], work, job.get("outdir", work), clk, opt.get("--final"), cf)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
