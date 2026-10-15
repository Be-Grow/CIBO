"""Cross-platform paths shared by CIBO scripts."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def cibo_root() -> Path:
    override = os.environ.get("CIBO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "skills").is_dir() and (parent / "README.md").exists():
            return parent
    raise RuntimeError("CIBO_ROOT não definido e raiz do CIBO não encontrada")


def skills_root() -> Path:
    return Path(os.environ.get("CIBO_SKILLS", cibo_root() / "skills")).expanduser()


def acervo_root() -> Path | None:
    conf = Path(os.environ.get("CIBO_ACERVO_CONF", Path.home() / ".cibo" / "acervo.json"))
    try:
        library = __import__("json").loads(conf.read_text(encoding="utf-8")).get("library")
        return Path(library).expanduser() if library else None
    except (OSError, ValueError):
        return None


def work_temp(name: str = "tmp") -> Path:
    base = Path(os.environ.get("CIBO_TEMP", os.environ.get("TMPDIR", tempfile.gettempdir()))).expanduser()
    path = base / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def portable_path(value: str | Path) -> Path:
    """Translate CIBO's known Mac install paths to this checkout/library on Windows."""
    raw = str(value)
    if os.name == "nt":
        old_library = "/Volumes/SSD/CIBO Acervo/"
        if raw.startswith(old_library):
            root = acervo_root()
            if root:
                return root / raw[len(old_library):]
        old_skills = "/.claude/skills/"
        if old_skills in raw:
            return skills_root() / raw.split(old_skills, 1)[1]
        if raw == "/Volumes/SSD/CIBO/tmp":
            return work_temp()
    return Path(value).expanduser()
