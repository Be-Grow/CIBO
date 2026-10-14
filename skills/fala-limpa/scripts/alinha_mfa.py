#!/usr/bin/env python3
"""Tempo exato de cada palavra com o Montreal Forced Aligner (MFA), em português.

uso: alinha_mfa.py --audio MASTER --words whisper_words.json --range IN OUT --out alinhado.json
     [--margem 1.0] [--srt palavras.srt]

Pega o texto que o Whisper já transcreveu no trecho (só o TEXTO; o tempo do Whisper atrasa ou
estica palavra) e alinha ao áudio com o MFA: fronteiras de palavra com ~10–20 ms e silêncios
explícitos. Saída no formato do Whisper (`segments[].words[]` com `word`, `start`, `end` no tempo
do arquivo de origem), mais `silences`. Palavra que o MFA não alinhou fica com o tempo do Whisper
e `"mfa": false`. MFA e modelos ficam no SSD (`/Volumes/SSD/CIBO`, `CIBO_MFA_HOME` muda).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HOME = Path(os.environ.get("CIBO_MFA_HOME", "/Volumes/SSD/CIBO"))
MFA = HOME / "miniforge" / "envs" / "mfa" / "bin" / "mfa"
ROOT = HOME / "mfa_root"


def textgrid_words(tg):
    """Lê o tier `words` de um TextGrid (formato longo do MFA): [(xmin, xmax, texto)]."""
    s = tg.read_text(encoding="utf-8")
    tiers = re.split(r'\n\s*item \[\d+\]:', s)
    tier = next((t for t in tiers if re.search(r'name = "words"', t)), "")
    return [(float(a), float(b), c) for a, b, c in
            re.findall(r'xmin = ([\d.]+)\s*\n\s*xmax = ([\d.]+)\s*\n\s*text = "(.*?)"', tier)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True); ap.add_argument("--words", required=True)
    ap.add_argument("--range", nargs=2, type=float, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--margem", type=float, default=1.0)
    ap.add_argument("--srt", help="também grava SRT palavra a palavra (o formato que o podcast-reels lê)")
    a = ap.parse_args()
    if not MFA.exists():
        sys.exit(f"MFA_AUSENTE em {MFA} (SSD desconectado?): use os tempos do Whisper e avise.")
    # A nunca negativo: o ffmpeg trata -ss negativo como 0 e todos os tempos saíam deslocados pela margem
    A, B = max(0.0, a.range[0] - a.margem), a.range[1] + a.margem
    d = json.load(open(a.words))
    W = [w for s in d.get("segments", []) for w in s.get("words", []) if A <= w["start"] < B]
    texto = " ".join(w["word"].strip() for w in W)
    with tempfile.TemporaryDirectory() as tmp:
        corp = Path(tmp) / "corpus"; corp.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{A:.3f}", "-to", f"{B:.3f}", "-i", a.audio, "-ac", "1",
                        "-ar", "16000", str(corp / "trecho.wav")], check=True)
        (corp / "trecho.txt").write_text(texto)
        env = dict(os.environ, MFA_ROOT_DIR=str(ROOT), PATH=f"{MFA.parent}:{os.environ.get('PATH', '')}")   # openfst/kaldi do ambiente
        r = subprocess.run([str(MFA), "align", "--clean", "--single_speaker", "-q", str(corp), "portuguese_brazil_mfa",
                            "portuguese_mfa", str(Path(tmp) / "out")], capture_output=True, text=True, env=env)
        tg = Path(tmp) / "out" / "trecho.TextGrid"
        if r.returncode or not tg.exists():
            sys.exit("MFA falhou: " + (r.stderr or r.stdout)[-800:])
        ali = textgrid_words(tg)
    # casa as palavras alinhadas com as do Whisper, na ordem
    norm = lambda x: re.sub(r"[^\wà-ÿ]", "", x.lower())
    words = [(s + A, e + A, t) for s, e, t in ali if t.strip()]
    sil = [(round(s + A, 3), round(e + A, 3)) for s, e, t in ali if not t.strip() and e - s >= 0.05]
    out, j, hit = [], 0, 0
    for w in W:
        k = norm(w["word"])
        m = next((i for i in range(j, min(j + 4, len(words))) if norm(words[i][2]) == k), None)
        if m is not None:
            s, e, _ = words[m]; j = m + 1; hit += 1
            out.append({"word": w["word"], "start": round(s, 3), "end": round(e, 3), "mfa": True,
                        "whisper": [w["start"], w["end"]]})
        else:
            out.append({"word": w["word"], "start": w["start"], "end": w["end"], "mfa": False})
    json.dump({"segments": [{"start": A, "end": B, "words": out}], "silences": sil}, open(a.out, "w"),
              ensure_ascii=False, indent=1)
    if a.srt:
        f = lambda t: f"{int(t // 3600):02d}:{int(t // 60 % 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}"
        Path(a.srt).write_text("\n".join(f"{i}\n{f(x['start'])} --> {f(x['end'])}\n{x['word'].strip()}\n"
                                         for i, x in enumerate(out, 1)))
    dif = [abs(x["start"] - x["whisper"][0]) for x in out if x["mfa"]]
    dif.sort()
    print(f"{hit}/{len(W)} palavras alinhadas pelo MFA; {len(sil)} silêncios; diferença para o Whisper no início da "
          f"palavra: mediana {dif[len(dif) // 2] * 1000:.0f} ms, p90 {dif[int(len(dif) * 0.9)] * 1000:.0f} ms" if dif else "nada alinhado")


if __name__ == "__main__":
    main()
