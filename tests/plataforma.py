"""Camada de plataforma do teste de regressão (26/11/2026).

O teste chama sempre a mesma interface; cada sistema responde do seu jeito. A implementação do Mac devolve exatamente o
que o teste usava antes desta camada (nada muda lá); a do Windows traz os caminhos desta máquina. Sistema novo = classe
nova aqui, sem tocar no `regressao.py`.
"""
from __future__ import annotations

import os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Plataforma:
    nome = "base"

    def __init__(self, skills: Path):
        self.skills = skills

    def golden_dir(self) -> Path:
        """onde ficam as referências de render (comparadas bit a bit: ffmpeg/sistema diferentes mudam os bits)"""
        raise NotImplementedError

    def venv_py(self, skill: str) -> Path:
        """Python do .venv de uma skill"""
        raise NotImplementedError

    def reel_motion_deps(self) -> Path:
        """node_modules do motor do reel-motion (sem ele o teste do reel-motion não roda)"""
        raise NotImplementedError

    def tmp_dir(self) -> Path:
        """onde o teste do reel-motion monta o projeto sintético"""
        raise NotImplementedError


class Mac(Plataforma):
    nome = "mac"

    def golden_dir(self):
        return HERE / "golden"

    def venv_py(self, skill):
        return self.skills / skill / ".venv" / "bin" / "python"

    def reel_motion_deps(self):
        return Path("/Volumes/SSD/CIBO/reel-motion/node_modules")

    def tmp_dir(self):
        return Path("/Volumes/SSD/CIBO/tmp")


class Windows(Plataforma):
    nome = "windows"

    def golden_dir(self):
        return HERE / "golden" / "windows"   # gravada de um checkout limpo da main nesta máquina

    def venv_py(self, skill):
        py = self.skills / skill / ".venv" / "Scripts" / "python.exe"
        return py if py.exists() else Path(sys.executable)   # aqui as skills usam o Python único da CIBO (audiotools)

    def reel_motion_deps(self):
        return self.skills / "reel-motion" / "mg" / "node_modules"

    def tmp_dir(self):
        return Path(os.environ.get("CIBO_TEMP") or r"C:\CIBO\tmp")


def atual(skills: Path) -> Plataforma:
    return (Windows if os.name == "nt" else Mac)(skills)
