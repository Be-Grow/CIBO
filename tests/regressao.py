#!/usr/bin/env python3
"""Teste de regressão dos motores de corte do CIBO.

Renderiza o mesmo material sintético em cada motor e compara a "impressão digital" da saída
(vídeo quadro a quadro, áudio sem os últimos 0,5 s, capa PNG) com a gravada em `golden/`.
Sem as chaves opt-in, uma mudança de código não pode alterar nenhuma delas.

  regressao.py check [--engine podcast-reels ...]   compara com a referência (padrão)
  regressao.py record [--engine ...]                grava a referência atual
  regressao.py list

Rode `check` antes de todo push para o CIBO que mexa em script de motor. Falhou: ou é bug, ou
a mudança é intencional (aí grave de novo com `record` e diga no commit o que mudou e por quê).
O material é gerado pelo próprio ffmpeg (determinístico para a mesma versão); se o ffmpeg mudar
de versão, todas as referências mudam juntas: grave de novo com `record`.
"""
from __future__ import annotations

import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden"
SKILLS = Path(os.environ.get("CIBO_SKILLS", HERE.parent / "skills"))
WORK = Path(os.environ.get("CIBO_TEST_WORK", Path.home() / ".cache" / "cibo" / "regressao"))
ENGINES = ["podcast-reels", "bombordo-boreste", "katia", "autismo-cast", "content-hub"]
# chaves de clipe que exigem arquivos externos do cliente: fora do teste
TIMEOUT = int(os.environ.get("CIBO_TEST_TIMEOUT", 240))   # macOS não tem `timeout`; travar vira erro
DROP = {"broll", "letterings", "music", "impact_pulses", "long_moves", "cropx_timeline", "overlays", "cover_src"}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ffversion():
    return sh(["ffmpeg", "-version"]).stdout.split("\n")[0].split(" Copyright")[0]


def fixture() -> Path:
    fx = WORK / "fixture"
    stamp = fx / "ffmpeg.txt"
    if stamp.exists() and stamp.read_text(encoding="utf-8") == ffversion():
        return fx
    shutil.rmtree(fx, ignore_errors=True)
    fx.mkdir(parents=True)
    # "fala": tom modulado em rajadas de ~1,5 s com pausas de 0,4 s (o snap de silêncio precisa delas)
    voice = ("aevalsrc='0.3*sin(2*PI*180*t)*(0.6+0.4*sin(2*PI*3*t))*lt(mod(t,1.9),1.5)"
             "|0.3*sin(2*PI*180*t)*(0.6+0.4*sin(2*PI*3*t))*lt(mod(t,1.9),1.5)':s=48000:d=20")
    r = sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=20",
            "-f", "lavfi", "-i", voice, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
            "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest", str(fx / "src.mov")])
    if r.returncode:
        sys.exit(r.stderr[-800:])
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
        "aevalsrc='0.2*sin(2*PI*220*t)+0.15*sin(2*PI*277*t)+0.1*sin(2*PI*330*t)':s=48000:d=40",
        "-ac", "2", "-c:a", "pcm_s16le", str(fx / "music.wav")])
    falas = ["Quantas vezes tu já viu", "alguém na internet", "com mais resultado", "que você tem hoje",
             "só porque teve coragem", "de produzir conteúdo", "e tu não faz isso", "por vergonha",
             "isso é uma força"]
    srt = []
    for i, t in enumerate(falas):
        a, b = i * 1.9, i * 1.9 + 1.5
        f = lambda x: f"00:00:{int(x):02d},{int(round((x % 1) * 1000)):03d}"
        srt.append(f"{i + 1}\n{f(a)} --> {f(b)}\n{t}\n")
    (fx / "src.srt").write_text("\n".join(srt), encoding="utf-8")
    stamp.write_text(ffversion(), encoding="utf-8")
    return fx


def job_for(engine: str, fx: Path, run: Path) -> Path:
    ex = json.loads((SKILLS / engine / "assets" / "job.example.json").read_text(encoding="utf-8"))
    clips = ex.get("clips")
    c0 = dict(next(iter(clips.values())) if isinstance(clips, dict) else clips[0])
    for k in DROP:
        c0.pop(k, None)
    c0.update(src="src.mov", master_in=0, keeps=[[0.3, 5.5], [5.75, 11.2], [11.45, 16.9]], cover_t=3.0,
              cropx=0.5, headline="TESTE DE\nREGRESSAO", filename="01 - TESTE DE REGRESSAO")
    if engine == "content-hub":
        c0.update(cover_cropx=0.5)
    job = {k: v for k, v in ex.items() if k not in ("clips",)}
    job.update(srt=str(fx / "src.srt"), srcdir=str(fx), work=str(run / "work"), outdir=str(run / "out"),
               clips={"corte01": c0})
    # caminhos de asset do exemplo: relativos à skill, ou o mesmo nome em assets/; se não existir
    # (placeholder "/path/..."), sai do job e o motor usa o padrão dele
    for k in ("filmburn", "click", "pop", "whoosh", "logo", "font"):
        v = job.get(k)
        if not isinstance(v, str):
            continue
        cands = [Path(v), SKILLS / engine / v, SKILLS / engine / "assets" / Path(v).name]
        hit = next((c for c in cands if c.is_file()), None)
        if hit:
            job[k] = str(hit)
        else:
            job.pop(k)
    p = run / "job.json"
    p.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def digest(out_dir: Path) -> dict:
    mp4 = next(out_dir.glob("*.mp4"), None)
    png = next(out_dir.glob("*.png"), None)
    if not mp4:
        return {"erro": "sem MP4 na saída"}
    v = sh(["ffmpeg", "-v", "error", "-i", str(mp4), "-map", "0:v", "-f", "framemd5", "-"]).stdout
    vlines = [l for l in v.splitlines() if l and not l.startswith("#")]
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)]).stdout or 0)
    a = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-t", f"{max(0, dur - 0.5):.3f}", "-map", "0:a",
                        "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return {"frames": len(vlines), "video": hashlib.sha256("\n".join(vlines).encode()).hexdigest()[:16],
            "audio": hashlib.sha256(a).hexdigest()[:16], "audio_bytes": len(a),
            "capa": hashlib.sha256(png.read_bytes()).hexdigest()[:16] if png else None,
            "duracao": round(dur, 3)}


def render(engine: str) -> tuple[dict, float, str]:
    fx = fixture()
    run = WORK / engine
    shutil.rmtree(run, ignore_errors=True)
    run.mkdir(parents=True)
    job = job_for(engine, fx, run)
    bindir = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python3"
    py = SKILLS / engine / ".venv" / bindir / exe
    if not py.exists():
        py = SKILLS / "podcast-reels" / ".venv" / bindir / exe
    if not py.exists():
        py = Path(sys.executable)
    env = {k: v for k, v in os.environ.items()
           if k not in ("VENC", "PASSA_DIRECT", "BURN_END_INLINE", "BURN_END_LIMIT", "BURN_END_BT709", "ZOOM_AMT",
                        "BURN_OUT", "JOB", "WORK", "SRCDIR", "FONT", "FILMBURN", "LOGO", "VIDEO_ENCODER", "REPLAN")}
    env.update(JOB=str(job), PYTHONHASHSEED="0")
    t = time.time()
    # em background o macOS joga tudo nos núcleos lentos; os filhos herdam a prioridade
    try:
        r = subprocess.run([str(py), str(SKILLS / engine / "scripts" / "make_reels.py"), "corte01"], cwd=run,
                           env=env, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(e.pid)], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", str(run)], capture_output=True)
        return {"erro": f"travou: passou de {TIMEOUT}s (encode parado?)"}, time.time() - t, str(e.stdout or "")[-800:]
    el = time.time() - t
    log = (r.stdout + r.stderr)[-1500:]
    if r.returncode:
        return {"erro": f"make_reels saiu com {r.returncode}"}, el, log
    return digest(run / "out"), el, log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="check", choices=["check", "record", "list"])
    ap.add_argument("--engine", nargs="*", default=None)
    a = ap.parse_args()
    if a.cmd == "list":
        print("\n".join(ENGINES))
        return
    GOLDEN.mkdir(exist_ok=True)
    falhas = 0
    for eng in a.engine or ENGINES:
        d, el, log = render(eng)
        g = GOLDEN / f"{eng}.json"
        if a.cmd == "record":
            if "erro" in d:
                print(f"ERRO   {eng}: {d['erro']}\n{log}")
                falhas += 1
                continue
            g.write_text(json.dumps(d | {"ffmpeg": ffversion()}, indent=1) + "\n", encoding="utf-8")
            print(f"GRAVADO {eng} ({el:.0f}s) {d}")
            continue
        if not g.exists():
            print(f"SEM_REFERENCIA {eng}: rode `regressao.py record --engine {eng}`")
            falhas += 1
            continue
        ref = json.loads(g.read_text(encoding="utf-8"))
        if "erro" in d:
            print(f"ERRO   {eng}: {d['erro']}\n{log}")
            falhas += 1
            continue
        diff = [k for k in ("frames", "video", "audio", "capa", "duracao") if ref.get(k) != d.get(k)]
        if ref.get("ffmpeg") != ffversion():
            print(f"AVISO  {eng}: referência gravada com {ref.get('ffmpeg')}, ffmpeg atual {ffversion()}")
        print(f"{'OK   ' if not diff else 'MUDOU'}  {eng} ({el:.0f}s)" + (f"  diferente: {', '.join(diff)}" if diff else ""))
        falhas += bool(diff)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
