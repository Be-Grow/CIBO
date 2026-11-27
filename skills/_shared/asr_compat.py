"""Whisper da CIBO: uma interface, uma implementação por sistema (26/11/2026, polimorfismo pedido pelo editor).

    transcribe(audio, modelo, language="pt", word_timestamps=False, ...) -> {"segments", "text", "language"}

- `MLX` (Mac Apple Silicon): chama o mlx_whisper exatamente como antes desta camada.
- `FasterWhisper` (Windows/Linux): faster-whisper; o áudio é lido pelo ffmpeg (PyAV 19 x faster-whisper 1.2.1); usa a
  placa de vídeo (CUDA) quando as bibliotecas da NVIDIA carregam e cai para o processador se não. `CIBO_ASR_DEVICE`
  (`auto` padrão, `cuda` ou `cpu`) e `CIBO_ASR_COMPUTE_TYPE` mandam quando definidos.
Sistema novo = classe nova aqui; quem chama `transcribe` não muda.
"""
from __future__ import annotations

import os, sys

MODELOS_MLX = {"mlx-community/whisper-large-v3-mlx": "large-v3", "mlx-community/whisper-large-v3-turbo": "large-v3-turbo",
               "mlx-community/whisper-small-mlx": "small", "mlx-community/whisper-tiny": "tiny",
               "mlx-community/whisper-large-v3-mlx-8bit": "large-v3"}


class Backend:
    nome = "base"

    def transcribe(self, audio, modelo, language="pt", word_timestamps=False, condition_on_previous_text=False,
                   verbose=None, initial_prompt=None, **kwargs) -> dict:
        raise NotImplementedError


class MLX(Backend):
    nome = "mlx"

    def transcribe(self, audio, modelo, language="pt", word_timestamps=False, condition_on_previous_text=False,
                   verbose=None, initial_prompt=None, **kwargs):
        import mlx_whisper
        return mlx_whisper.transcribe(audio, path_or_hf_repo=modelo, language=language,
            word_timestamps=word_timestamps, condition_on_previous_text=condition_on_previous_text,
            verbose=verbose, initial_prompt=initial_prompt, **kwargs)


def ffmpeg_audio(audio):
    """float32 mono 16 kHz lido pelo ffmpeg; array já decodificado passa direto"""
    import subprocess
    import numpy as np
    if not isinstance(audio, (str, os.PathLike)):
        return audio
    raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(audio), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


class FasterWhisper(Backend):
    nome = "faster-whisper"
    _cache = {}

    @staticmethod
    def _dlls_nvidia():
        """Windows: as DLLs de cuBLAS/cuDNN instaladas pelo pip (nvidia-*-cu12) ficam em site-packages/nvidia/*/bin"""
        if os.name != "nt":
            return
        import site
        for sp in site.getsitepackages() + [site.getusersitepackages()]:
            base = os.path.join(sp, "nvidia")
            if os.path.isdir(base):
                for pkg in os.listdir(base):
                    b = os.path.join(base, pkg, "bin")
                    if os.path.isdir(b):
                        os.add_dll_directory(b)
                        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")

    def _engine(self, modelo):
        from faster_whisper import WhisperModel
        pedido = os.environ.get("CIBO_ASR_DEVICE", "auto")
        tentativas = ["cuda", "cpu"] if pedido == "auto" else [pedido]
        erro = None
        for device in tentativas:
            compute = os.environ.get("CIBO_ASR_COMPUTE_TYPE") or ("int8_float16" if device == "cuda" else "int8")
            chave = (modelo, device, compute)
            if chave in self._cache:
                return self._cache[chave]
            try:
                if device == "cuda":
                    self._dlls_nvidia()
                    import ctranslate2
                    if not ctranslate2.get_cuda_device_count():
                        raise RuntimeError("sem placa CUDA")
                eng = WhisperModel(modelo, device=device, compute_type=compute)
                if device == "cuda":   # a DLL que falta só aparece no primeiro uso: testa com 1 s de silêncio
                    import numpy as np
                    list(eng.transcribe(np.zeros(16000, np.float32), language="pt")[0])
                self._cache[chave] = (eng, device)
                return eng, device
            except Exception as e:  # noqa: BLE001 — placa indisponível: tenta o próximo
                erro = e
        raise RuntimeError(f"faster-whisper não iniciou ({pedido}): {erro}")

    def transcribe(self, audio, modelo, language="pt", word_timestamps=False, condition_on_previous_text=False,
                   verbose=None, initial_prompt=None, **kwargs):
        eng, device = self._engine(MODELOS_MLX.get(modelo, modelo))
        segs, info = eng.transcribe(ffmpeg_audio(audio), language=language, word_timestamps=word_timestamps,
                                    condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt)
        out = []
        for s in segs:
            row = {"start": s.start, "end": s.end, "text": s.text}
            if word_timestamps:
                row["words"] = [{"start": w.start, "end": w.end, "word": w.word, "probability": w.probability}
                                for w in (s.words or [])]
            out.append(row)
        return {"segments": out, "text": "".join(x["text"] for x in out), "language": info.language, "device": device}


def backend() -> Backend:
    if sys.platform == "darwin":
        try:
            import mlx_whisper  # noqa: F401
            return MLX()
        except ImportError:
            pass
    return FasterWhisper()


def transcribe(audio, path_or_hf_repo=None, language="pt", word_timestamps=False,
               condition_on_previous_text=False, verbose=None, initial_prompt=None, **kwargs):
    return backend().transcribe(audio, path_or_hf_repo or "large-v3", language=language, word_timestamps=word_timestamps,
                                condition_on_previous_text=condition_on_previous_text, verbose=verbose,
                                initial_prompt=initial_prompt, **kwargs)
