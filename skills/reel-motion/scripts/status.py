#!/usr/bin/env python3
"""Mostra etapas, entregas e processos ativos de um projeto reel-motion."""
import json, os, subprocess, sys, time
from pathlib import Path

P = Path(sys.argv[1]); WK = P / "04_work"
if not WK.exists():
    sys.exit(f"projeto não encontrado: {P}")

def processes():
    if os.name == "nt":
        cmd = "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine,Name,CreationDate | ConvertTo-Json -Compress"
        raw = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True).stdout
        try:
            rows = json.loads(raw) if raw.strip() else []
            if isinstance(rows, dict): rows = [rows]
            now = time.time(); out = []
            for x in rows:
                created = x.get("CreationDate")
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(created.split(".")[0]).replace(tzinfo=datetime.timezone.utc)
                    elapsed = int(now - dt.timestamp())
                except Exception: elapsed = 0
                out.append(dict(pid=str(x.get("ProcessId", "")), ppid=str(x.get("ParentProcessId", "")),
                                elapsed=f"{elapsed//3600}:{elapsed//60%60:02d}", state="", cmd=x.get("CommandLine") or x.get("Name") or ""))
            return out
        except (ValueError, TypeError): return []
    raw = subprocess.run(["ps", "-eo", "pid=,ppid=,etime=,stat=,command="], capture_output=True, text=True).stdout
    out=[]
    for line in raw.splitlines():
        p=line.split(None,4)
        if len(p)==5 and "/bin/zsh -c" not in p[4] and "uv run" not in p[4]:
            out.append(dict(pid=p[0],ppid=p[1],elapsed=p[2],state=p[3],cmd=p[4]))
    return out

ps=processes()
def hm(f): return time.strftime("%H:%M", time.localtime(f.stat().st_mtime)) if f.exists() else "—"
for r in sorted(d.name for d in WK.iterdir() if d.is_dir() and (d / "reel.json").exists()):
    W=WK/r
    etapas=[(n,f) for n,f in (("voz",W/"edit_mfa.json"),("legenda",W/"blocos.json"),("props",WK/"public"/r/"props.json"),
        ("camera",WK/"public"/r/"camera.mov"),("mix",W/"mix.wav"),("final",W/"video2.mp4")) if f.exists()]
    ult=max(etapas,key=lambda e:e[1].stat().st_mtime) if etapas else None
    active=[x for x in ps if P.name in x["cmd"] and f" {r} " in x["cmd"] and "reel.py" in x["cmd"]]
    rod=", ".join(f"{x['cmd'].split(f' {r} ',1)[1].split()[0]} há {x['elapsed']}" for x in active) or "—"
    nome=json.loads((W/"reel.json").read_text(encoding="utf-8")).get("name",r).split(" - ",1)[-1]
    ent=next(P.glob(f"06_deliverables/{r[1:]} -*.mp4"),None); prev=next(P.glob(f"05_qa/previas/{r[1:]} -*.mp4"),None)
    print(f"{r} {nome[:34]:34} | última etapa: {ult[0]+' '+hm(ult[1]) if ult else '—':15} | rodando: {rod:22} | prévia {hm(prev) if prev else '—'} | entrega {hm(ent) if ent else '—'}")
heavy=[x["cmd"][-90:] for x in ps if any(k in x["cmd"] for k in ("camera.py","remotion render","wt.py","face_track"))]
print(f"trabalhos pesados agora: {len(heavy)}" + (" → "+" | ".join(heavy) if heavy else ""))
