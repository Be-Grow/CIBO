"""Tempo palavra a palavra com Whisper: mlx-whisper no Mac (Apple Silicon, como sempre foi), faster-whisper no Windows/Linux
(Igor 14/10/2026). uso: wt.py AUDIO SAIDA.json MODELO [PROMPT]"""
import json, os, sys

audio, out, model_name = sys.argv[1:4]
prompt = sys.argv[4] if len(sys.argv) > 4 else None
if sys.platform == "darwin":
    import mlx_whisper
    r = mlx_whisper.transcribe(audio, path_or_hf_repo=model_name, language="pt", word_timestamps=True,
                               condition_on_previous_text=False, initial_prompt=prompt)
    json.dump(r, open(out, "w"), ensure_ascii=False)
    sys.exit(0)
from faster_whisper import WhisperModel
model_name = {"mlx-community/whisper-large-v3-mlx": "large-v3", "mlx-community/whisper-large-v3-turbo": "large-v3-turbo"}.get(model_name, model_name)
device = "cuda" if os.environ.get("CIBO_ASR_DEVICE", "auto") == "cuda" else "cpu"
compute = "float16" if device == "cuda" else "int8"
model = WhisperModel(model_name, device=device, compute_type=compute)
segments, _ = model.transcribe(audio, language="pt", word_timestamps=True,
                               condition_on_previous_text=False, initial_prompt=prompt)
data = []
for seg in segments:
    data.append({"start": seg.start, "end": seg.end, "text": seg.text,
                 "words": [{"start": w.start, "end": w.end, "word": w.word, "probability": w.probability}
                           for w in (seg.words or [])]})
with open(out, "w", encoding="utf-8") as f:
    json.dump({"segments": data, "text": "".join(s["text"] for s in data)}, f, ensure_ascii=False)
