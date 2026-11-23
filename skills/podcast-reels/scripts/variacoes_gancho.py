#!/usr/bin/env python3
"""Variações de gancho: um corpo × N ganchos = N vídeos prontos para teste A/B.

uso: variacoes_gancho.py CORPO.mp4 GANCHO1.mp4 [GANCHO2.mp4 ...] [--out PASTA] [--sem-capa]

Cada saída é `<gancho> + <corpo>.mp4`: o gancho no começo, depois o corpo inteiro. O volume do
gancho é igualado ao do corpo (LUFS medido) para a emenda não pular; o gancho é ajustado ao
tamanho/qps do corpo. `--sem-capa` tira o 1º quadro do corpo (a capa do motor) quando o gancho
entra antes dele. Codifica na GPU se `VENC=videotoolbox` (ou `auto` pelo perfil de hardware), senão
x264. Cada arquivo é verificado pelo ffmpeg (decodifica inteiro) e pelo AVFoundation (`av_check`:
reproduzível e com quadro gerado no começo, na emenda e no fim), porque um arquivo pode rodar no
ffmpeg e travar no QuickTime/iPhone. Ideia de `krusemediallc/video-editor-agent` hook-variations.
"""
import json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AVBIN = Path.home() / ".cache" / "cibo" / "bin" / "av_check"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(p):
    d = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", p]).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    n, de = v["r_frame_rate"].split("/")
    return float(d["format"]["duration"]), v["width"], v["height"], float(n) / float(de)


def lufs(p):
    e = run(["ffmpeg", "-nostdin", "-i", p, "-af", "ebur128", "-f", "null", "-"]).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)
    return float(m[-1]) if m else -23.0


def venc():
    v = os.environ.get("VENC", "x264")
    if v == "auto":
        try:
            v = json.loads(run([sys.executable, str(HERE.parent.parent / "video-render-optimizer" / "scripts" / "hw_profile.py"),
                                "env", "--json"]).stdout)["VENC"]
        except Exception:
            v = "x264"
    if v == "videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "20M", "-realtime", "false", "-profile:v", "high"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]


def ensure_av():
    if os.name == "nt":
        print("AVFoundation indisponível no Windows; validando o arquivo por decodificação integral no FFmpeg.")
        return
    src = HERE / "av_check.swift"
    if not AVBIN.exists() or AVBIN.stat().st_mtime < src.stat().st_mtime:
        AVBIN.parent.mkdir(parents=True, exist_ok=True)
        r = run(["swiftc", "-O", str(src), "-o", str(AVBIN)])
        if r.returncode:
            print("aviso: av_check não compilou; só a checagem do ffmpeg vale:", r.stderr[-300:])


def main():
    args = sys.argv[1:]
    out = Path(".")
    if "--out" in args:
        i = args.index("--out"); out = Path(args[i + 1]); del args[i:i + 2]
    nocover = "--sem-capa" in args
    if nocover:
        args.remove("--sem-capa")
    body, hooks = args[0], args[1:]
    out.mkdir(parents=True, exist_ok=True)
    ensure_av()
    bd, bw, bh, bfps = probe(body)
    bl = lufs(body)
    skip = 1 / bfps if nocover else 0
    ok_all = True
    for h in hooks:
        hd = probe(h)[0]
        gain = bl - lufs(h)
        dst = out / f"{Path(h).stem} + {Path(body).stem}.mp4"
        fc = (f"[0:v]scale={bw}:{bh}:force_original_aspect_ratio=decrease,pad={bw}:{bh}:(ow-iw)/2:(oh-ih)/2,"
              f"fps={bfps},setsar=1,format=yuv420p[hv];[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain:.2f}dB[ha];"
              f"[1:v]trim=start={skip},setpts=PTS-STARTPTS,fps={bfps},setsar=1,format=yuv420p[bv];"
              f"[1:a]atrim=start={skip},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[ba];"
              f"[hv][ha][bv][ba]concat=n=2:v=1:a=1[v][a]")
        r = run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", h, "-i", body, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                 *venc(), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)])
        if r.returncode:
            print("ERRO", dst.name, r.stderr[-300:]); ok_all = False; continue
        dec = run(["ffmpeg", "-v", "error", "-i", str(dst), "-f", "null", "-"]).returncode == 0
        av = {"ok": None}
        if AVBIN.exists():
            res = run([str(AVBIN), str(dst), "0.3", f"{hd:.2f}", f"{hd + 0.2:.2f}", f"{probe(str(dst))[0] - 0.2:.2f}"])
            try:
                av = json.loads(res.stdout)
            except ValueError:
                av = {"ok": False, "error": res.stderr[-200:]}
        good = dec and av.get("ok") is not False
        ok_all &= good
        print(f"{'OK  ' if good else 'ERRO'} {dst.name}  gancho {hd:.1f}s, ganho {gain:+.1f} dB, "
              f"ffmpeg {'ok' if dec else 'falhou'}, AVFoundation {av.get('ok')}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
