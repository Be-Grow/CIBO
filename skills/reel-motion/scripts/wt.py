import sys,json,mlx_whisper
audio,out,model=sys.argv[1],sys.argv[2],sys.argv[3]
prompt=sys.argv[4] if len(sys.argv)>4 else None
r=mlx_whisper.transcribe(audio,path_or_hf_repo=model,language="pt",word_timestamps=True,condition_on_previous_text=False,initial_prompt=prompt)
json.dump(r,open(out,'w'),ensure_ascii=False)
print('ok',len(r['segments']))
