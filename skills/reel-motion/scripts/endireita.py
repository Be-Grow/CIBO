#!/usr/bin/env python3
"""Endireita vídeo gravado torto (celular inclinado) no DaVinci pela API.

1. mede a inclinação pelas linhas retas da sala (telão, paredes, teto) a cada N s (Hough, parte de cima do quadro);
2. resume por trecho (mediana) para ver se é constante ou se precisa animar;
3. calcula o zoom/pan que cobre a timeline sem borda preta com esse giro;
4. com --aplica, grava RotationAngle no clipe (guarda o antes em JSON ao lado do log).

Uso (roda com o python3 do sistema, que fala com o Resolve; a medida vai para um Python com OpenCV achado sozinho
— CIBO_CV_PY ou o primeiro .venv de skill com cv2 —, porque o venv com cv2 lê o clipe com propriedades vazias):
  endireita.py VIDEO --passo 2                       # só mede e mostra
  endireita.py VIDEO --clipe IMG_1386.MP4 --aplica   # mede e aplica no clipe da timeline atual
  endireita.py VIDEO --clipe X --aplica --angulo 6.4 # aplica um ângulo já medido

Sinal: inclinação medida positiva = cena tombada no sentido horário; RotationAngle positivo no Resolve corrige (medido
27/11/2026, IMG_1386, emerson). Cobertura vale para fonte do mesmo tamanho da timeline (Pan 1:1); fonte de outro tamanho segue a
"lei medida" de regras/davinci.md (Pan × largura do arquivo ÷ largura da timeline).
"""
import argparse, json, math, os, sys

RESOLVE_MOD = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"


def mede(video, passo):
    import cv2, numpy as np
    cap = cv2.VideoCapture(video); fps = cap.get(5); n = int(cap.get(7)); res = []
    for k in range(0, n, max(1, int(fps * passo))):
        cap.set(1, k); ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]; esc = 540 / min(w, h)
        g = cv2.cvtColor(cv2.resize(fr, (int(w * esc), int(h * esc))), cv2.COLOR_BGR2GRAY)
        g = g[: int(g.shape[0] * 0.65)]  # parte de cima: o chão em perspectiva atrapalha
        L = cv2.HoughLinesP(cv2.Canny(g, 60, 160), 1, np.pi / 720, 60, minLineLength=90, maxLineGap=6)
        angs, pes = [], []
        for x1, y1, x2, y2 in (L[:, 0] if L is not None else []):
            a = math.degrees(math.atan2(y2 - y1, x2 - x1))
            a = a + 180 if a <= -90 else a - 180 if a > 90 else a
            ln = math.hypot(x2 - x1, y2 - y1)
            if abs(a) < 15: angs.append(a); pes.append(ln * 0.6)                        # horizontal
            elif abs(a) > 75: angs.append(a - 90 * (1 if a > 0 else -1)); pes.append(ln)  # vertical
        if len(angs) >= 3:
            a = np.array(angs); p = np.array(pes); m = np.median(a); s = np.abs(a - m) < 4
            res.append((k / fps, float(np.average(a[s], weights=p[s]))))
    return res


def py_cv():
    import glob, subprocess
    for p in [os.environ.get("CIBO_CV_PY")] + sorted(glob.glob(os.path.expanduser("~/.claude/skills/*/.venv/bin/python3"))):
        if p and subprocess.run([p, "-c", "import cv2, numpy"], capture_output=True).returncode == 0:
            return p
    sys.exit("nenhum Python com OpenCV (defina CIBO_CV_PY)")


def mede_fora(video, passo):
    import subprocess
    r = subprocess.run([py_cv(), os.path.realpath(__file__), video, "--passo", str(passo), "--so-mede"], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-800:])
    return json.loads(r.stdout)


def cobre(th, zoom, px, py, W, H):
    """margem (px da fonte) que sobra com giro th, zoom e pan; negativa = aparece borda."""
    t = math.radians(th); c, s = math.cos(t), math.sin(t); mx = my = 0
    for x, y in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)):
        u, v = (x - px) / zoom, (y - py) / zoom
        mx, my = max(mx, abs(c * u + s * v)), max(my, abs(-s * u + c * v))
    return min(W / 2 - mx, H / 2 - my)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--passo", type=float, default=2)
    ap.add_argument("--clipe"); ap.add_argument("--aplica", action="store_true"); ap.add_argument("--angulo", type=float)
    ap.add_argument("--so-mede", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.so_mede:
        print(json.dumps(mede(a.video, a.passo))); return
    ang = a.angulo
    if ang is None:
        from statistics import median, quantiles
        r = mede_fora(a.video, a.passo)
        if not r: sys.exit("nenhuma linha reta medida")
        for s0 in range(0, int(r[-1][0]) + 1, 120):
            v = [x[1] for x in r if s0 <= x[0] < s0 + 120]
            if v: print(f"{s0//60:02d}:{s0%60:02d}  {median(v):5.1f}°")
        v = [x[1] for x in r]; q = quantiles(v, n=10)
        ang = round(median(v), 1)
        print(f"inclinação: mediana {ang}° (p10 {q[0]:.1f}, p90 {q[-1]:.1f}; picos isolados = perspectiva/luminária)")
    if not a.clipe:
        return
    sys.path.append(RESOLVE_MOD); import DaVinciResolveScript as dvr
    tl = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject().GetCurrentTimeline()
    W, H = int(tl.GetSetting("timelineResolutionWidth")), int(tl.GetSetting("timelineResolutionHeight"))
    itens = [i for tr in range(1, tl.GetTrackCount("video") + 1) for i in tl.GetItemListInTrack("video", tr) if i.GetName() == a.clipe]
    if not itens: sys.exit(f"clipe {a.clipe} não está na timeline atual")
    K = ["Pan", "Tilt", "ZoomX", "ZoomY", "RotationAngle"]
    for it in itens:
        p = {k: it.GetProperty(k) for k in K}
        if None in p.values():
            sys.exit("o Resolve devolveu propriedades vazias (janela/diálogo aberto ou página sem resposta); feche e rode de novo")
        m = cobre(ang, p["ZoomX"], p["Pan"], p["Tilt"], W, H)
        zmin = next(z / 100 for z in range(100, 400) if cobre(ang, z / 100, 0, 0, W, H) >= 0)
        print(f"antes {p} | com {ang}°: margem {m:.0f} px (zoom mínimo centrado {zmin:.2f})")
        if m < 0: print("  AVISO: aparece borda preta; suba o zoom ou traga o pan para o centro")
        if a.aplica:
            json.dump(p, open(os.path.join(os.environ.get("TMPDIR", "."), f"endireita_antes_{a.clipe}.json"), "w"))
            print("  RotationAngle:", it.SetProperty("RotationAngle", ang))


if __name__ == "__main__":
    main()
