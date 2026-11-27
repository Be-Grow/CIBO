"""CIBO QA editorial/AV portátil. Python stdlib; Windows, Linux e macOS.
Bandeiras lexicais não comprovam conclusão da ideia.
"""
from __future__ import annotations
import hashlib,json,os,re,subprocess
from pathlib import Path
from typing import Any
CONNECTIVES={"e","mas","porque","então","aí","daí","pois","que","ou","porém","contudo","entretanto"}
DEICTIC={"isso","isto","aquilo","ele","ela","eles","elas","esse","essa","esses","essas","aquele","aquela","nisso","disso"}
DANGLING=CONNECTIVES|{"de","do","da","para","com","por","em","no","na","o","a","os","as","um","uma","como","quando","se"}
WORD=re.compile(r"[\wÀ-ÿ]+",re.UNICODE)

def _word(t,first=False):
    w=WORD.findall(t.lower())
    return (w[0] if first else w[-1]) if w else ""

def boundary_signals(segments:list[dict[str,Any]],start:float,end:float)->dict[str,Any]:
    if not 0<=start<end:raise ValueError("Intervalo inválido")
    units=sorted((s for s in segments
        if float(s.get("end",0))>start and float(s.get("start",0))<end),key=lambda s:float(s["start"]))
    if not units:return {"status":"review_required","signals":["no_transcript"],"first":"","last":"","duration":end-start}
    first=str(units[0].get("text","")).strip()
    last=str(units[-1].get("text","")).strip()
    signals=[]
    if float(units[0]["start"])<start-.12:signals.append("start_inside_segment")
    if float(units[-1]["end"])>end+.12:signals.append("end_inside_segment")
    if _word(first,True) in CONNECTIVES:signals.append("connective_opening")
    if _word(first,True) in DEICTIC:signals.append("dependent_opening")
    if _word(last) in DANGLING and not last.endswith((".","!","?")):signals.append("dangling_last_word")
    if last.endswith((",",":",";","—","-")):signals.append("unfinished_punctuation")
    if not last.endswith((".","!","?")):signals.append("unconfirmed_sentence_end")
    return {"status":"review_required" if signals else "boundary_only_ok","signals":signals,
            "first":first[:220],"last":last[-220:],"duration":round(end-start,3),
            "note":"Pontuação e limites não comprovam conclusão semântica."}

def media_report(video:str|Path,*,max_seconds:int=300,require_audio:bool=False)->dict[str,Any]:
    p=Path(video).resolve(strict=True)
    if not p.is_file() or not p.stat().st_size:raise ValueError("Arquivo de vídeo vazio/inexistente")
    def run(args,timeout):
        return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=timeout,check=False,text=True,encoding="utf-8",errors="replace")
    probe=run(["ffprobe","-v","error","-show_entries",
               "format=duration,size:stream=codec_type,codec_name,duration,width,height",
               "-of","json",str(p)],30)
    if probe.returncode:raise RuntimeError("ffprobe falhou: "+probe.stderr[-300:])
    data=json.loads(probe.stdout)
    streams=data.get("streams",[])
    v=next((s for s in streams if s.get("codec_type")=="video"),None)
    a=next((s for s in streams if s.get("codec_type")=="audio"),None)
    if not v:raise RuntimeError("Mídia sem vídeo")
    decoded=run(["ffmpeg","-nostdin","-hide_banner","-v","error","-xerror","-i",str(p),
                 "-map","0:v:0","-map","0:a:0?","-f","null","-"],max_seconds)
    vd=float(v.get("duration") or data.get("format",{}).get("duration") or 0)
    ad=float(a.get("duration") or 0) if a else None
    delta=abs(vd-ad) if ad is not None else None
    sha=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):sha.update(b)
    ok=decoded.returncode==0 and (delta is None or delta<=.25) and (not require_audio or a is not None)
    return {"file":str(p),"sha256":sha.hexdigest(),"bytes":p.stat().st_size,
            "duration":vd,"has_audio":a is not None,
            "av_delta_seconds":round(delta,3) if delta is not None else None,
            "decoder_ok":decoded.returncode==0,"status":"pass_technical" if ok else "review_required",
            "error":decoded.stderr[-450:] if decoded.returncode else None,"human_review_required":True}

def add_feedback(log_path:str|Path,*,job_id:str,source_sha256:str,decision:str,
                 reason:str,start:float|None=None,end:float|None=None)->dict[str,Any]:
    if decision not in {"approved","rejected","needs_review"}:raise ValueError("Decisão inválida")
    if not re.fullmatch(r"[a-fA-F0-9]{64}",source_sha256):raise ValueError("SHA-256 inválido")
    if not job_id or not reason.strip():raise ValueError("Job e motivo obrigatórios")
    if (start is None)!=(end is None):raise ValueError("Intervalo incompleto")
    if start is not None and not 0<=start<end:raise ValueError("Intervalo inválido")
    from datetime import datetime,timezone
    record={"at":datetime.now(timezone.utc).isoformat(),"job_id":job_id,
            "media_sha256":source_sha256.lower(),"decision":decision,
            "reason":reason.strip()[:1200],"start":start,"end":end}
    p=Path(log_path);p.parent.mkdir(parents=True,exist_ok=True)
    row=(json.dumps(record,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")
    fd=os.open(str(p),os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
    try:os.write(fd,row);os.fsync(fd)
    finally:os.close(fd)
    return record

def feedback_summary(log_path:str|Path)->dict[str,int]:
    counts={"approved":0,"rejected":0,"needs_review":0}
    p=Path(log_path)
    if not p.exists():return counts
    for row in p.read_text(encoding="utf-8").splitlines():
        if not row.strip():continue
        try:e=json.loads(row)
        except json.JSONDecodeError:continue
        if e.get("decision") in counts:counts[e["decision"]]+=1
    return counts
