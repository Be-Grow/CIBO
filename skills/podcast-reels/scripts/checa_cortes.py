#!/usr/bin/env python3
"""Confere começo e fim de cada corte ANTES do render (português).

uso: JOB=job.json checa_cortes.py [corte01 ...]

Para cada clipe, lê o texto do primeiro e do último trecho mantido (pelo SRT do job, no tempo
do master) e acusa:
  ABERTURA   começa com conectivo solto ("então", "e", "mas", "aí", "porque", "tipo") — o
             estranho chega no meio do raciocínio
  PENDURADO  primeira frase com pronome ou dêitico sem referência ("isso", "ele", "ela", "esse",
             "aquilo", "lá") — falta o antecedente
  MINÚSCULA  a primeira palavra vem em minúscula no SRT: o Whisper continuou uma frase anterior
  RABO       termina em vírgula, conectivo ou preposição: a ideia não fechou
  DURAÇÃO    fora da faixa pedida (padrão 30–90 s mantidos)
Corrigir contexto = adiantar o começo, nunca cortar o desfecho. Inspirado em
`kvrancic/oneshot-video` candidates.py e references/selection.md (MIT), 12/10/2026.
"""
import json, os, re, sys

CONECT = {"então", "e", "mas", "aí", "daí", "porque", "pois", "tipo", "né", "só", "que", "ou", "também",
          "inclusive", "ainda", "enfim", "assim", "logo", "porém", "contudo", "entretanto", "senão"}
DEIT = {"isso", "isto", "aquilo", "ele", "ela", "eles", "elas", "esse", "essa", "esses", "essas", "aquele",
        "aquela", "lá", "dele", "dela", "nisso", "disso", "daquilo"}
FIM_RUIM = CONECT | {"de", "do", "da", "dos", "das", "em", "no", "na", "para", "pra", "com", "por", "pelo",
                     "pela", "o", "a", "os", "as", "um", "uma", "como", "quando", "se"}


def srt(path):
    txt = open(path, encoding="utf-8").read()
    out = []
    for b in re.split(r"\n\s*\n", txt.strip()):
        ls = b.strip().splitlines()
        m = next((re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", l) for l in ls if "-->" in l), None)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        t = " ".join(l for l in ls if "-->" not in l and not l.strip().isdigit())
        out.append((s, e, t.strip()))
    return out


def text_in(cues, a, b):
    return " ".join(t for s, e, t in cues if e > a + 0.05 and s < b - 0.05)


def words(t):
    return re.findall(r"[\wÀ-ÿ%]+[.,!?;:…]*", t)


def main():
    job = json.load(open(os.environ["JOB"]))
    cues = srt(job["srt"])
    lo, hi = float(os.environ.get("MIN_S", 30)), float(os.environ.get("MAX_S", 90))
    ks = sys.argv[1:] or list(job["clips"])
    bad = 0
    for k in ks:
        c = job["clips"][k]
        mi = float(c.get("master_in", 0))
        K = c["keeps"]
        head = text_in(cues, mi + K[0][0], mi + K[0][0] + 6)
        tail = text_in(cues, mi + K[-1][1] - 6, mi + K[-1][1])
        # a primeira palavra efetivamente ouvida: a do cue que contém o início
        hw = words(head)        # funciona com SRT por frase e com SRT palavra a palavra
        tw = words(tail)
        flags = []
        if hw:
            w0 = hw[0].strip(".,!?;:…").lower()
            if w0 in CONECT:
                flags.append(f"ABERTURA começa com '{hw[0]}'")
            if any(x.strip(".,!?;:…").lower() in DEIT for x in hw[:6]):
                flags.append("PENDURADO pronome/dêitico na 1ª frase: " + " ".join(hw[:8]))
            if hw[0][:1].islower():
                flags.append(f"MINÚSCULA '{hw[0]}': o corte pode estar no meio da frase")
        if tw:
            last = tw[-1]
            if last.endswith(",") or last.strip(".,!?;:…").lower() in FIM_RUIM and not last.endswith((".", "!", "?")):
                flags.append(f"RABO termina em '{last}'")
        dur = sum(b - a for a, b in K)
        if not lo <= dur <= hi:
            flags.append(f"DURAÇÃO {dur:.1f}s fora de {lo:.0f}–{hi:.0f}s")
        bad += bool(flags)
        print(f"{'OK  ' if not flags else 'VER '} {k} ({dur:.0f}s)  começo: «{' '.join(hw[:9])}…»  fim: «…{' '.join(tw[-7:])}»")
        for f in flags:
            print("      " + f)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
