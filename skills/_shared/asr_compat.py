"""Compatible Whisper interface: MLX on Apple Silicon, faster-whisper elsewhere."""
from __future__ import annotations

import os


def transcribe(audio, path_or_hf_repo=None, language="pt", word_timestamps=False,
               condition_on_previous_text=False, verbose=None, initial_prompt=None, **kwargs):
    model = path_or_hf_repo or "large-v3"
    try:
        import mlx_whisper
        if os.uname().sysname == "Darwin":
            return mlx_whisper.transcribe(audio, path_or_hf_repo=model, language=language,
                word_timestamps=word_timestamps, condition_on_previous_text=condition_on_previous_text,
                verbose=verbose, initial_prompt=initial_prompt, **kwargs)
    except (ImportError, AttributeError):
        pass
    from faster_whisper import WhisperModel
    model = {"mlx-community/whisper-large-v3-mlx":"large-v3", "mlx-community/whisper-large-v3-turbo":"large-v3-turbo",
             "mlx-community/whisper-small-mlx":"small"}.get(model, model)
    device = os.environ.get("CIBO_ASR_DEVICE", "cpu")
    compute = os.environ.get("CIBO_ASR_COMPUTE_TYPE", "int8" if device == "cpu" else "float16")
    engine = WhisperModel(model, device=device, compute_type=compute)
    segs, info = engine.transcribe(str(audio), language=language, word_timestamps=word_timestamps,
        condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt)
    output=[]
    for s in segs:
        row={"start":s.start,"end":s.end,"text":s.text}
        if word_timestamps:
            row["words"]=[{"start":w.start,"end":w.end,"word":w.word,"probability":w.probability} for w in (s.words or [])]
        output.append(row)
    return {"segments":output,"text":"".join(x["text"] for x in output),"language":info.language}
