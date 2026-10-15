"""Portable Whisper word timing backend (faster-whisper on Windows/Linux/macOS)."""
import json, sys
from faster_whisper import WhisperModel

audio, out, model_name = sys.argv[1:4]
prompt = sys.argv[4] if len(sys.argv) > 4 else None
device = "cuda" if __import__("os").environ.get("CIBO_ASR_DEVICE", "auto") == "cuda" else "cpu"
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
