"""CLI Windows/Codex para o núcleo portátil do CIBO."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from editorial import add_feedback,boundary_signals,feedback_summary,media_report

def main(argv=None):
    parser=argparse.ArgumentParser(description="CIBO QA portátil — Windows, Codex e ChatGPT")
    sub=parser.add_subparsers(dest="command",required=True)
    cut=sub.add_parser("check-cut",help="Verifica sinais de risco em bordas transcritas")
    cut.add_argument("--transcription",required=True,help="JSON com segments, ou lista de segments")
    cut.add_argument("--start",type=float,required=True)
    cut.add_argument("--end",type=float,required=True)
    qa=sub.add_parser("check-video",help="Decodifica integralmente e verifica duração A/V")
    qa.add_argument("--video",required=True)
    fb=sub.add_parser("feedback",help="Registra revisão humana em arquivo local JSONL")
    fb.add_argument("--log",required=True)
    fb.add_argument("--job-id")
    fb.add_argument("--sha256")
    fb.add_argument("--decision",choices=["approved","rejected","needs_review"])
    fb.add_argument("--reason")
    fb.add_argument("--start",type=float)
    fb.add_argument("--end",type=float)
    fb.add_argument("--summary",action="store_true")
    args=parser.parse_args(argv)
    if args.command=="check-cut":
        data=json.loads(Path(args.transcription).read_text(encoding="utf-8"))
        if isinstance(data,dict):data=data.get("segments",data.get("transcription_segments"))
        if not isinstance(data,list):raise ValueError("JSON não contém segmentos")
        result=boundary_signals(data,args.start,args.end)
    elif args.command=="check-video":
        result=media_report(args.video)
    else:
        if args.summary:result=feedback_summary(args.log)
        else:
            if not all((args.job_id,args.sha256,args.decision,args.reason)):
                parser.error("feedback exige --job-id --sha256 --decision --reason")
            result=add_feedback(args.log,job_id=args.job_id,source_sha256=args.sha256,
                decision=args.decision,reason=args.reason,start=args.start,end=args.end)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (ValueError,RuntimeError,OSError,TimeoutError) as e:
        print(f"CIBO_ERROR: {e}",file=sys.stderr)
        sys.exit(2)
