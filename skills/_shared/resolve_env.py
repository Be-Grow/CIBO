"""Onde mora a API de scripting do DaVinci Resolve em cada sistema (Mac, Windows, Linux).

Uso no topo de qualquer script que fala com o Resolve (antes de `import DaVinciResolveScript`):

    import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../_shared'))
    import resolve_env  # noqa: F401  (põe Modules no sys.path e define RESOLVE_SCRIPT_API/LIB)

Ordem de busca (a primeira que existir vale):
  1. variáveis já definidas: RESOLVE_SCRIPT_API, RESOLVE_SCRIPT_LIB
  2. CIBO_RESOLVE_DIR: pasta do app do Resolve (instalação fora do lugar padrão)
  3. lugar padrão do instalador oficial em cada sistema
No Mac nada muda: os caminhos padrão são os mesmos que os scripts usavam fixos.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

WIN = os.name == "nt"
MAC = sys.platform == "darwin"


def _primeiro(cands):
    for c in cands:
        if c and Path(c).exists():
            return str(c)
    return str(cands[0]) if cands else ""


def app_dir() -> Path | None:
    d = os.environ.get("CIBO_RESOLVE_DIR")
    if d:
        return Path(d).expanduser()
    if WIN:
        return Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blackmagic Design" / "DaVinci Resolve"
    if MAC:
        return Path("/Applications/DaVinci Resolve/DaVinci Resolve.app")
    return Path("/opt/resolve")


def api_dir() -> str:
    if os.environ.get("RESOLVE_SCRIPT_API"):
        return os.environ["RESOLVE_SCRIPT_API"]
    app = app_dir()
    if WIN:
        pd = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        cands = [pd / "Blackmagic Design" / "DaVinci Resolve" / "Support" / "Developer" / "Scripting",
                 app / "Developer" / "Scripting" if app else None]
    elif MAC:
        cands = [Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting")]
    else:
        cands = [Path("/opt/resolve/Developer/Scripting"), Path("/home/resolve/Developer/Scripting")]
    return _primeiro([c for c in cands if c])


def lib_path() -> str:
    if os.environ.get("RESOLVE_SCRIPT_LIB"):
        return os.environ["RESOLVE_SCRIPT_LIB"]
    app = app_dir()
    if WIN:
        return _primeiro([app / "fusionscript.dll"])
    if MAC:
        return _primeiro([app / "Contents" / "Libraries" / "Fusion" / "fusionscript.so"])
    return _primeiro([Path("/opt/resolve/libs/Fusion/fusionscript.so")])


def manual_pdf() -> Path:
    app = app_dir()
    if MAC:
        return Path("/Applications/DaVinci Resolve/DaVinci Resolve Manual.pdf")
    return (app / "Documents" / "DaVinci Resolve.pdf") if app else Path("DaVinci Resolve.pdf")


def configura() -> None:
    api, lib = api_dir(), lib_path()
    os.environ.setdefault("RESOLVE_SCRIPT_API", api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", lib)
    mods = str(Path(api) / "Modules")
    if mods not in sys.path:
        sys.path.append(mods)
    # subprocessos (fila_davinci chama outros scripts) herdam o caminho
    pp = os.environ.get("PYTHONPATH", "")
    if mods not in pp.split(os.pathsep):
        os.environ["PYTHONPATH"] = mods + (os.pathsep + pp if pp else "")


def limite(seg: int, msg=None) -> None:
    """Tempo limite para o script inteiro (a API trava calada com diálogo aberto no Resolve).
    Unix: SIGALRM, como antes. Windows (sem SIGALRM): um temporizador que encerra o processo."""
    texto = lambda: msg() if callable(msg) else (msg or f"PAREI: {seg} s sem resposta do Resolve")
    if hasattr(__import__("signal"), "SIGALRM"):
        import signal

        def fim(*_):
            sys.exit(texto())
        signal.signal(signal.SIGALRM, fim)
        signal.alarm(seg)
        return
    def fim_win():
        try:
            print(texto(), file=sys.stderr, flush=True)
        finally:
            os._exit(124)
    t = threading.Timer(seg, fim_win)
    t.daemon = True
    t.start()


def roda_com_limite(cmd, seg: int, **kw) -> subprocess.CompletedProcess:
    """Substitui `perl -e 'alarm N; exec @ARGV'` (não existe no Windows): mata o filho no tempo limite e devolve código 124."""
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    if MAC:   # Mac: exatamente como antes da camada (regra das camadas de plataforma, WINDOWS.md)
        return subprocess.run(["perl", "-e", f"alarm {seg}; exec @ARGV", *map(str, cmd)], **kw)
    try:
        return subprocess.run(list(map(str, cmd)), timeout=seg, **kw)
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return subprocess.CompletedProcess(e.cmd, 124, out, err + f"\n(tempo limite de {seg} s)")


def janelas_resolve() -> str:
    """Janelas abertas do Resolve (diálogo modal = API presa). Mac: osascript; Windows: lista de títulos."""
    try:
        if MAC:
            return subprocess.run(["osascript", "-e", 'tell application "System Events" to tell process "Resolve" '
                                   "to get name of every window"], capture_output=True, text=True, timeout=10).stdout.strip()
        if WIN:
            ps = ("Get-Process Resolve -ErrorAction SilentlyContinue | Where-Object MainWindowTitle | "
                  "ForEach-Object MainWindowTitle")
            return subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                                  timeout=10).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"(não li: {e})"
    return "(sem leitor de janelas neste sistema)"


configura()
