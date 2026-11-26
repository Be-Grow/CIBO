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
# fora do Mac: a mesma interface da CIBO (_shared/asr_compat: faster-whisper, ffmpeg lê o áudio, placa de vídeo se houver)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_shared"))
import asr_compat  # noqa: E402
r = asr_compat.transcribe(audio, model_name, language="pt", word_timestamps=True,
                          condition_on_previous_text=False, initial_prompt=prompt)
with open(out, "w", encoding="utf-8") as f:
    json.dump({"segments": r["segments"], "text": r["text"]}, f, ensure_ascii=False)
