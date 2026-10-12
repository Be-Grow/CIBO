#!/usr/bin/env python3
"""Perfil de hardware do CIBO: detecta a máquina, escolhe o encoder mais eficiente por
benchmark e revalida a escolha de tempos em tempos.

uso:
  hw_profile.py detect                 # só o hardware (CPU, RAM, GPU, encoders, disco)
  hw_profile.py env [--json]           # garante o perfil e imprime as variáveis do motor
  hw_profile.py check                  # teste rápido do encoder escolhido (periódico)
  hw_profile.py bench [--sample F]     # benchmark completo agora
  hw_profile.py install-schedule       # opcional (macOS): teste semanal via launchd, além do teste por uso
  hw_profile.py uninstall-schedule

Quando `env` roda, o perfil é refeito sozinho se a máquina, o FFmpeg ou os encoders
mudaram, ou se o benchmark tem mais de REBENCH_DAYS dias; e passa por um `check` se o
último teste foi há CHECK_RUNS renders (padrão 10). Se o encoder de hardware falhar no teste, o
perfil cai para CPU (libx264) até o próximo benchmark passar.
Só usa a biblioteca padrão; ffmpeg/ffprobe no PATH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import benchmark_encoder as be  # noqa: E402

CACHE = Path(os.environ.get("CIBO_HW_CACHE", Path.home() / ".cache" / "cibo" / "hw"))
PROFILE = CACHE / "profile.json"
REBENCH_DAYS = float(os.environ.get("CIBO_HW_REBENCH_DAYS", 30))
# teste rápido a cada N renders (cada `env`, ou seja, cada vez que o motor resolve o encoder)
CHECK_RUNS = int(os.environ.get("CIBO_HW_CHECK_RUNS", 10))
# perfil de entrega padrão do CIBO (Reels 1080x1920/30): alvo e teto de bitrate
TARGET_MBPS = float(os.environ.get("CIBO_TARGET_MBPS", 8))
MAX_MBPS = float(os.environ.get("CIBO_MAX_MBPS", 10))
CPU_PRESET, CPU_CRF = "slow", 18
VENC_NAME = {"libx264": "x264", "h264_videotoolbox": "videotoolbox", "h264_nvenc": "nvenc",
             "h264_qsv": "qsv", "h264_amf": "amf", "h264_vaapi": "vaapi"}
LABEL = "com.cibo.hwprofile"


def sh(cmd: list[str], timeout: float | None = None) -> str:
    try:
        return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def now() -> float:
    return time.time()


def days(ts: float | None) -> float:
    return 1e9 if not ts else (now() - ts) / 86400


# ---------------------------------------------------------------- detecção
def detect() -> dict:
    sysname = platform.system()
    hw: dict = {"system": sysname, "machine": platform.machine(), "python": platform.python_version()}
    if sysname == "Darwin":
        q = lambda k: sh(["sysctl", "-n", k]).strip()
        hw["cpu"] = q("machdep.cpu.brand_string")
        hw["cpu_threads"] = int(q("hw.ncpu") or 0)
        hw["cpu_perf_cores"] = int(q("hw.perflevel0.physicalcpu") or 0)
        hw["cpu_eff_cores"] = int(q("hw.perflevel1.physicalcpu") or 0)
        hw["ram_gb"] = round(int(q("hw.memsize") or 0) / 2**30, 1)
        gtxt = sh(["system_profiler", "SPDisplaysDataType"], timeout=30)
        hw["gpu"] = re.findall(r"Chipset Model:\s*(.+)", gtxt)
        hw["gpu_cores"] = re.findall(r"Total Number of Cores:\s*(.+)", gtxt)
        hw["metal"] = re.findall(r"Metal(?: Support| Family)?:\s*(.+)", gtxt)
    elif sysname == "Linux":
        cpuinfo = Path("/proc/cpuinfo").read_text(errors="ignore") if Path("/proc/cpuinfo").exists() else ""
        m = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        hw["cpu"] = m.group(1).strip() if m else platform.processor()
        hw["cpu_threads"] = os.cpu_count()
        mem = Path("/proc/meminfo").read_text() if Path("/proc/meminfo").exists() else ""
        m = re.search(r"MemTotal:\s*(\d+)", mem)
        hw["ram_gb"] = round(int(m.group(1)) / 2**20, 1) if m else None
        gpus = [l.split(": ", 1)[-1] for l in sh(["lspci"]).splitlines() if re.search(r"VGA|3D|Display", l)]
        nv = sh(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]).strip()
        hw["gpu"] = gpus + ([f"nvidia-smi: {nv}"] if nv else [])
    elif sysname == "Windows":
        hw["cpu"] = platform.processor()
        hw["cpu_threads"] = os.cpu_count()
        ps = sh(["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name; (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        lines = [l.strip() for l in ps.splitlines() if l.strip()]
        hw["gpu"] = [l for l in lines if not l.isdigit()]
        tot = [l for l in lines if l.isdigit()]
        hw["ram_gb"] = round(int(tot[-1]) / 2**30, 1) if tot else None
    ff = sh(["ffmpeg", "-version"]).splitlines()
    hw["ffmpeg"] = ff[0].split(" Copyright")[0] if ff else None
    enc = sh(["ffmpeg", "-hide_banner", "-encoders"])
    hw["encoders"] = sorted(set(re.findall(r"^\s*V\S*\s+((?:lib)?x26[45]\w*|\w+_(?:videotoolbox|nvenc|qsv|vaapi|amf|v4l2m2m))\b",
                                           enc, re.M)))
    hw["hwaccels"] = [l.strip() for l in sh(["ffmpeg", "-hide_banner", "-hwaccels"]).splitlines()[1:] if l.strip()]
    du = shutil.disk_usage(Path.home())
    hw["disk_free_gb_home"] = round(du.free / 2**30, 1)
    # paralelismo seguro: ~5 GB de RAM por render 1080p (decode + quadros crus + encode)
    ram = hw.get("ram_gb") or 8
    hw["max_parallel_renders"] = max(1, min(3, int(ram // 5)))
    return hw


def hw_fingerprint(hw: dict) -> str:
    keys = ("system", "machine", "cpu", "gpu", "ffmpeg", "encoders")
    return hashlib.sha256(json.dumps({k: hw.get(k) for k in keys}, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- amostra
def synthetic_sample() -> Path:
    """10 s 1080x1920/30 com detalhe fino, gradiente, ruído temporal e texto: substitui um trecho
    real quando nenhum foi dado. Gerado uma vez e reaproveitado."""
    p = CACHE / "sample_synthetic_1080x1920.mp4"
    if p.exists():
        return p
    CACHE.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=10",
        "-f", "lavfi", "-i", "gradients=size=1080x1920:rate=30:duration=10:speed=0.02",
        "-filter_complex", "[0:v][1:v]blend=all_mode=overlay:all_opacity=0.5,noise=alls=10:allf=t,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "8", str(p)], check=True)
    return p


def pick_sample(arg: str | None, prof: dict | None) -> Path:
    if arg and Path(arg).is_file():
        return Path(arg)
    last = (prof or {}).get("benchmark", {}).get("sample")
    if last and Path(last).is_file():
        return Path(last)
    return synthetic_sample()


def sample_window(sample: Path) -> tuple[float, float]:
    dur = float(be.ffprobe(sample)["format"].get("duration") or 10)
    secs = min(12.0, max(3.0, dur - 1))
    start = max(0.0, min(dur * 0.3, dur - secs - 0.5))   # meio do arquivo, não a abertura
    return start, secs


# ---------------------------------------------------------------- benchmark e teste
def bench(sample_arg: str | None = None, reason: str = "manual") -> dict:
    hw = detect()
    prof = load()
    sample = pick_sample(sample_arg, prof)
    start, secs = sample_window(sample)
    selected = [n for n in ("libx264", *be.HW_ENCODERS) if n in be.available_encoders()]
    tgt, mx, buf = f"{TARGET_MBPS:g}M", f"{MAX_MBPS:g}M", f"{MAX_MBPS * 2:g}M"
    tmp = CACHE / "bench_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    results = [be.benchmark_one(sample, tmp / f"{n}.mp4", n, start, secs, tgt, mx, buf, CPU_PRESET, CPU_CRF)
               for n in selected]
    for r in results:
        r.pop("output", None)
    shutil.rmtree(tmp, ignore_errors=True)
    rec = be.recommend(results, MAX_MBPS, "speed")
    enc = rec.get("encoder") or "libx264"
    prof = {
        "fingerprint": hw_fingerprint(hw), "hardware": hw,
        "benchmark": {"at": now(), "reason": reason, "sample": str(sample), "start": start, "seconds": secs,
                      "target_mbps": TARGET_MBPS, "max_mbps": MAX_MBPS, "results": results, "recommendation": rec},
        "choice": {"encoder": enc, "venc": VENC_NAME.get(enc, "x264"), "reason": rec.get("reason")},
        "last_check": None, "history": (prof or {}).get("history", [])[-20:],
    }
    prof["history"].append({"at": now(), "event": "bench", "reason": reason, "choice": enc})
    save(prof)
    return prof


def check(prof: dict | None = None, quiet: bool = False) -> dict:
    """Teste curto do encoder escolhido: codifica 4 s, decodifica inteiro, mede SSIM e velocidade
    contra o próprio benchmark. Falhou ou perdeu qualidade -> volta para libx264."""
    prof = prof or load()
    if not prof:
        return bench(reason="sem perfil")
    enc = prof["choice"]["encoder"]
    sample = pick_sample(None, prof)
    start, _ = sample_window(sample)
    out = CACHE / "check.mp4"
    r = be.benchmark_one(sample, out, enc, start, 4.0, f"{TARGET_MBPS:g}M", f"{MAX_MBPS:g}M",
                         f"{MAX_MBPS * 2:g}M", CPU_PRESET, CPU_CRF)
    decode_ok = r.get("ok") and subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "null", "-"],
                                               capture_output=True).returncode == 0
    out.unlink(missing_ok=True)
    base = next((x for x in prof["benchmark"]["results"] if x.get("encoder") == enc and x.get("ok")), {})
    cpu = next((x for x in prof["benchmark"]["results"] if x.get("encoder") == "libx264" and x.get("ok")), {})
    problems = []
    if not decode_ok:
        problems.append(f"{enc} falhou ao codificar/decodificar: {str(r.get('error', ''))[-300:]}")
    else:
        floor = max(0.96, (cpu.get("ssim") or 0.97) - 0.01) if enc != "libx264" else 0.96
        if (r.get("ssim") or 0) < floor:
            problems.append(f"SSIM {r.get('ssim')} abaixo de {floor:.4f}")
        if base.get("realtime_factor") and r["realtime_factor"] < 0.6 * base["realtime_factor"]:
            # lento não invalida a escolha (pode ser calor ou prioridade baixa em background),
            # mas fica registrado e aparece no aviso
            problems.append(f"lento: {r['realtime_factor']}x tempo real contra {base['realtime_factor']}x no benchmark")
    fatal = [p for p in problems if not p.startswith("lento")]
    prof["runs_since_check"] = 0
    prof["last_check"] = {"at": now(), "encoder": enc, "ok": not fatal, "problems": problems,
                          "realtime_factor": r.get("realtime_factor"), "ssim": r.get("ssim")}
    if fatal and enc != "libx264":
        prof["choice"] = {"encoder": "libx264", "venc": "x264",
                          "reason": f"fallback: {enc} reprovou no teste periódico ({'; '.join(fatal)})"}
        prof["benchmark"]["at"] = 0   # força benchmark completo no próximo `env`
    prof["history"].append({"at": now(), "event": "check", "encoder": enc, "ok": not fatal, "problems": problems})
    prof["history"] = prof["history"][-30:]
    save(prof)
    if not quiet:
        print(json.dumps(prof["last_check"], ensure_ascii=False, indent=2))
    return prof


def ensure(sample: str | None = None) -> dict:
    prof = load()
    hw_fp = hw_fingerprint(detect())
    if not prof or prof.get("fingerprint") != hw_fp:
        return bench(sample, reason="hardware/ffmpeg/encoders mudaram" if prof else "primeiro uso")
    if not prof["benchmark"].get("at"):
        return bench(sample, reason="revalidação depois de falha no teste periódico")
    if days(prof["benchmark"].get("at")) > REBENCH_DAYS:
        return bench(sample, reason=f"benchmark com mais de {REBENCH_DAYS:g} dias")
    prof["runs_since_check"] = prof.get("runs_since_check", 0) + 1
    if prof["runs_since_check"] >= CHECK_RUNS:
        return check(prof, quiet=True)
    save(prof)
    return prof


def env_vars(prof: dict) -> dict:
    return {"VENC": prof["choice"]["venc"], "VT_MBPS": f"{TARGET_MBPS:g}", "VT_MAX_MBPS": f"{MAX_MBPS:g}",
            "CIBO_MAX_PARALLEL": str(prof["hardware"].get("max_parallel_renders", 1))}


# ---------------------------------------------------------------- persistência
def load() -> dict | None:
    try:
        return json.loads(PROFILE.read_text())
    except (OSError, ValueError):
        return None


def save(prof: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = PROFILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(prof, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(PROFILE)


# ---------------------------------------------------------------- agenda (macOS)
def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def install_schedule() -> None:
    if platform.system() != "Darwin":
        print(f"Fora do macOS, agende no cron: 0 10 * * 1 {sys.executable} {Path(__file__).resolve()} check")
        return
    ffdir = str(Path(shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg").parent)
    CACHE.mkdir(parents=True, exist_ok=True)
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key><array>
    <string>{sys.executable}</string><string>{Path(__file__).resolve()}</string><string>scheduled</string>
  </array>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>{ffdir}:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>{CACHE / 'scheduled.log'}</string>
  <key>StandardErrorPath</key><string>{CACHE / 'scheduled.log'}</string>
</dict></plist>
"""
    p = plist_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
    p.write_text(plist)
    subprocess.run(["launchctl", "load", str(p)], check=True)
    print(f"agendado: toda segunda 10:00 -> {p} (log em {CACHE / 'scheduled.log'})")


def uninstall_schedule() -> None:
    p = plist_path()
    subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
    p.unlink(missing_ok=True)
    print("agenda removida")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["detect", "env", "check", "bench", "scheduled", "install-schedule", "uninstall-schedule", "show"])
    ap.add_argument("--sample", help="trecho real (8–15 s úteis) para o benchmark; senão o último usado ou um sintético")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "detect":
        print(json.dumps(detect(), ensure_ascii=False, indent=2))
    elif a.cmd == "bench":
        p = bench(a.sample)
        print(json.dumps({"choice": p["choice"], "results": p["benchmark"]["results"]}, ensure_ascii=False, indent=2))
    elif a.cmd == "check":
        check()
    elif a.cmd == "scheduled":
        # agenda semanal: benchmark se estiver velho ou a máquina mudou, senão teste rápido
        p = ensure()
        if days((p.get("last_check") or {}).get("at")) > 0.01:
            p = check(p, quiet=True)
        print(time.strftime("%Y-%m-%d %H:%M"), json.dumps({"choice": p["choice"], "last_check": p["last_check"]}, ensure_ascii=False))
    elif a.cmd == "env":
        p = ensure(a.sample)
        v = env_vars(p)
        if a.json:
            print(json.dumps(v | {"reason": p["choice"]["reason"], "last_check": p.get("last_check")}, ensure_ascii=False))
        else:
            print("\n".join(f"export {k}={v}" for k, v in v.items()))
            lc = p.get("last_check") or {}
            if lc.get("problems"):
                print(f"# aviso do último teste: {'; '.join(lc['problems'])}", file=sys.stderr)
    elif a.cmd == "show":
        print(json.dumps(load(), ensure_ascii=False, indent=2))
    elif a.cmd == "install-schedule":
        install_schedule()
    elif a.cmd == "uninstall-schedule":
        uninstall_schedule()


if __name__ == "__main__":
    main()
