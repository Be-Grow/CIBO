#!/usr/bin/env python3
"""Busca de B-roll stock para um corte: acervo primeiro, depois Pixabay (API) e Pexels (aba do Chrome).

  busca_stock.py checa PLANO                      queries fracas (uma palavra, cena posada, termo proibido)
  busca_stock.py pexels-js PLANO [-n 8]           imprime o JS para rodar numa aba www.pexels.com
  busca_stock.py busca PLANO DIR [--pexels J]     15–20 candidatos por trecho → DIR/candidatos.json
  busca_stock.py quadros DIR                      4 quadros por candidato e uma folha por trecho (DIR/folhas/)
  busca_stock.py nota DIR [--manual N.json]       naturalidade 0–10 + matriz semântica (API do Claude ou manual)
  busca_stock.py relatorio DIR [--md SAIDA]       top 3 por trecho (07_manifests/broll_candidatos.md)
  busca_stock.py baixa DIR TRECHO N --proj PROJ   baixa o escolhido, cataloga no acervo e copia para o projeto

PLANO (JSON): {"cliente": "andreia", "trechos": [{"id": "t1", "inicio": 12.3, "fim": 16.0, "fala": "…",
  "ideia": "o que a imagem precisa mostrar", "slot": "painel"|"cheia", "queries": ["…", …], "evitar": ["…"]}]}
As queries descrevem a cena inteira (ator + ação + lugar + função), ver semantic-broll-validator.
"""
from __future__ import annotations

import argparse, base64, io, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rede, fontes

MODELO = "claude-haiku-5-5"
POSADO = ["business people", "smiling at camera", "handshake", "thumbs up", "high five", "pointing", "isolated",
          "white background", "success", "happy", "concept", "teamwork", "celebrat", "excited", "cheering",
          "stock", "corporate", "smiling", "posing", "jump"]
PESOS = {"claim": .30, "funcao": .20, "ator": .15, "literal": .15, "emocao": .10, "tecnico": .05, "licenca": .05}


def plano(p):
    d = json.loads(Path(p).read_text())
    for t in d["trechos"]:
        t.setdefault("slot", "painel")
        t.setdefault("evitar", [])
    return d


# ---------- checa / pexels-js ----------

def avisos_query(q):
    av, ql = [], q.lower()
    if len(q.split()) < 3:
        av.append("curta demais: descreva ator + ação + lugar")
    av += [f"cena posada ('{w}')" for w in POSADO if w in ql]
    return av


def cmd_checa(a):
    ruim = 0
    for t in plano(a.plano)["trechos"]:
        qs = t.get("queries", [])
        if not 3 <= len(qs) <= 5:
            print(f"{t['id']}: {len(qs)} queries (use de 3 a 5)"); ruim += 1
        for q in qs:
            av = avisos_query(q) + [f"tem termo evitado '{e}'" for e in t["evitar"] if e.lower() in q.lower()]
            if av:
                print(f"{t['id']}: \"{q}\" → {'; '.join(av)}"); ruim += 1
    print("ok" if not ruim else f"{ruim} aviso(s)")
    sys.exit(1 if ruim else 0)


def cmd_pexels_js(a):
    qs = [{"query": q, "orientation": "portrait" if t["slot"] == "cheia" else "landscape"}
          for t in plano(a.plano)["trechos"] for q in t.get("queries", [])]
    js = (Path(__file__).parent / "pexels_chrome.js").read_text()
    print(js.replace("__QUERIES__", json.dumps(qs, ensure_ascii=False)).replace("__N__", str(a.n)))


# ---------- busca ----------

def serve(c, t):
    """filtro por slot e duração; devolve motivo de rejeição ou None"""
    w, h = c["w"] or 0, c["h"] or 0
    if c["dur"] and c["dur"] < (t["fim"] - t["inicio"]) + 1:
        return f"curto ({c['dur']:.0f} s)"
    if t["slot"] == "cheia":
        if not ((h > w and w >= 1080) or w >= 3840):
            return f"tela cheia pede vertical ≥1080 ou horizontal 4K ({w}x{h})"
    elif w < 1920 and h < 1920:
        return f"painel pede 1080p ({w}x{h})"
    return None


def usados(cliente):
    r = subprocess.run([sys.executable, str(fontes.ACERVO), "find", "--type", "video", "-n", "100000", "--json"],
                       capture_output=True, text=True)
    try:
        itens = json.loads(r.stdout or "[]")
    except ValueError:
        return set()
    return {((it.get("meta") or {}).get("fonte"), str((it.get("meta") or {}).get("id"))) for it in itens
            if any(u.get("client") == cliente for u in it.get("usos", []))}


def cmd_busca(a):
    P = plano(a.plano)
    out = Path(a.dir); out.mkdir(parents=True, exist_ok=True)
    fs = [fontes.Acervo(P["cliente"]), fontes.Pixabay(), fontes.PexelsChrome(a.pexels)]
    fs = [f for f in fs if f.ok()]
    print("fontes:", ", ".join(f.nome for f in fs) or "nenhuma")
    ja = usados(P["cliente"])
    res = {}
    for t in P["trechos"]:
        vistos, cands, rej = set(), [], {}
        for q in t.get("queries", []):
            for f in fs:
                try:
                    lst = f.busca(q, a.n)
                except Exception as e:   # uma fonte fora do ar não derruba a busca
                    print(f"  {f.nome} '{q}': {e}", file=sys.stderr); continue
                for c in lst:
                    k = (c["fonte"], c["id"])
                    if k in vistos:
                        continue
                    vistos.add(k)
                    motivo = "já usado por este cliente" if k in ja else serve(c, t)
                    if any(e.lower() in (c["tags"] + " " + c["pagina"]).lower() for e in t["evitar"]):
                        motivo = "tem termo evitado"
                    if motivo:
                        rej[motivo.split(" (")[0]] = rej.get(motivo.split(" (")[0], 0) + 1
                    else:
                        cands.append(c)
        cands = cands[:a.max]
        res[t["id"]] = {"trecho": t, "candidatos": cands, "rejeitados": rej}
        print(f"{t['id']}: {len(cands)} candidatos" + (f"  (fora: {rej})" if rej else ""))
    (out / "candidatos.json").write_text(json.dumps({"cliente": P["cliente"], "trechos": res}, ensure_ascii=False, indent=1))


# ---------- quadros ----------

def ffquadro(src, t, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                    "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2", str(dst)],
                   capture_output=True)
    return Path(dst).exists()


def cmd_quadros(a):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.load_default(size=18)   # a padrão sem tamanho não tem acento
    D = Path(a.dir); J = json.loads((D / "candidatos.json").read_text())
    (D / "prev").mkdir(exist_ok=True); (D / "folhas").mkdir(exist_ok=True)
    for tid, r in J["trechos"].items():
        cells = []
        for i, c in enumerate(r["candidatos"], 1):
            src = Path(c["preview"])
            if c["fonte"] != "acervo":
                src = D / "prev" / f"{c['fonte']}_{c['id']}.mp4"
                if not src.exists():
                    try:
                        rede.baixa(c["preview"], src, c["pagina"] or None)
                    except Exception as e:
                        print(f"  {tid} #{i}: prévia falhou ({e})", file=sys.stderr); continue
            pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                                capture_output=True, text=True).stdout.strip()
            dur = float(pr or 0) or c["dur"] or 8   # a duração da página do Pexels pode ser de outro vídeo
            fr = [D / "prev" / f"{c['fonte']}_{c['id']}_{k}.jpg" for k in range(4)]
            ok = [ffquadro(src, dur * p, f) for p, f in zip((.1, .35, .6, .85), fr)]
            if not any(ok):
                continue
            cell = Image.new("RGB", (640, 384), (20, 20, 20))
            for k, f in enumerate(fr):
                if f.exists():
                    cell.paste(Image.open(f), ((k % 2) * 320, (k // 2) * 180 + 24))
            ImageDraw.Draw(cell).text((6, 2), f"#{i} {c['fonte']} {c['w']}x{c['h']} {c['dur']:.0f}s", fill=(255, 220, 0), font=fnt)
            c["celula"] = str(D / "prev" / f"{c['fonte']}_{c['id']}_cel.jpg"); cell.save(c["celula"], quality=85)
            cells.append(cell)
        if cells:
            cols = 4; rows = -(-len(cells) // cols)
            sheet = Image.new("RGB", (640 * cols, 384 * rows + 40), (0, 0, 0))
            ImageDraw.Draw(sheet).text((10, 12), f"{tid}: {r['trecho']['fala'][:160]}", fill=(255, 255, 255), font=fnt)
            for k, cell in enumerate(cells):
                sheet.paste(cell, ((k % cols) * 640, (k // cols) * 384 + 40))
            sheet.save(D / "folhas" / f"{tid}.jpg", quality=80)
            print(f"{tid}: {len(cells)} candidatos → {D / 'folhas' / (tid + '.jpg')}")
    (D / "candidatos.json").write_text(json.dumps(J, ensure_ascii=False, indent=1))


# ---------- nota ----------

PROMPT = """Você avalia B-roll de banco para um vídeo de fala (talking head) em português.
Fala do trecho: "{fala}"
O que a imagem precisa mostrar: {ideia}
Cada imagem é um candidato (4 quadros do mesmo vídeo). Para cada um, dê notas inteiras:
- naturalidade 0–10: 10 = parece filmado de verdade (gente real, luz natural, ação espontânea); 0 = cena posada de banco
  (sorriso para a câmera, aperto de mão encenado, fundo branco, gente comemorando sem motivo).
- claim 0–5: mostra a mesma afirmação/causa da fala? funcao 0–5: cumpre a função narrativa (exemplo, prova, contraste)?
- ator 0–5: ator, escala e lugar certos? literal 0–5: evita leitura literal de expressão figurada?
- emocao 0–5: emoção e tom combinam com a cliente (fala calma, editorial, premium)?
- risco: o que o espectador poderia entender errado (curto).
Responda só JSON: [{{"n": 1, "naturalidade": 0, "claim": 0, "funcao": 0, "ator": 0, "literal": 0, "emocao": 0, "risco": ""}}, …]"""


def tecnico(c, t):
    w, h = c["w"] or 0, c["h"] or 0
    if t["slot"] == "cheia":
        return 5 if h > w and h >= 1920 else 4 if (h > w or w >= 3840) else 2
    return 5 if max(w, h) >= 3840 else 4 if max(w, h) >= 1920 else 2


def licenca(c):
    return 5 if c["fonte"] in fontes.FONTES or (c["fonte"] == "acervo" and c["licenca"]) else 0


def nota_api(r, key):
    imgs = [c for c in r["candidatos"] if c.get("celula")]
    if not imgs:
        return {}
    content = []
    for i, c in enumerate(imgs, 1):
        content += [{"type": "text", "text": f"Candidato {i}:"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                 "data": base64.b64encode(Path(c["celula"]).read_bytes()).decode()}}]
    t = r["trecho"]
    content.append({"type": "text", "text": PROMPT.format(fala=t["fala"], ideia=t.get("ideia", t["fala"]))})
    d = rede.post_json("https://api.anthropic.com/v1/messages",
                       {"model": MODELO, "max_tokens": 4000, "messages": [{"role": "user", "content": content}]},
                       {"x-api-key": key, "anthropic-version": "2023-06-01"})
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    m = re.search(r"\[.*\]", txt, re.S)
    lst = json.loads(m.group(0)) if m else []
    return {imgs[x["n"] - 1]["fonte"] + ":" + imgs[x["n"] - 1]["id"]: x for x in lst if 1 <= x.get("n", 0) <= len(imgs)}


def cmd_nota(a):
    D = Path(a.dir); J = json.loads((D / "candidatos.json").read_text())
    man = json.loads(Path(a.manual).read_text()) if a.manual else None
    key = rede.chave("ANTHROPIC_API_KEY")
    if not man and not key:
        sys.exit("sem ANTHROPIC_API_KEY: olhe as folhas e passe --manual notas.json "
                 '({"t1": {"3": {"naturalidade": 8, "claim": 4, "funcao": 4, "ator": 4, "literal": 5, "emocao": 4, "risco": ""}}})')
    for tid, r in J["trechos"].items():
        if man is not None:
            ns = {f"{r['candidatos'][int(n) - 1]['fonte']}:{r['candidatos'][int(n) - 1]['id']}": v
                  for n, v in man.get(tid, {}).items() if 0 < int(n) <= len(r["candidatos"])}
        else:
            ns = nota_api(r, key)
        for c in r["candidatos"]:
            n = ns.get(f"{c['fonte']}:{c['id']}")
            if not n:
                continue
            n = {**n, "tecnico": tecnico(c, r["trecho"]), "licenca": licenca(c)}
            sem = sum(PESOS[k] * float(n.get(k, 0)) for k in PESOS)
            nat = float(n.get("naturalidade", 0))
            c["nota"] = {**n, "semantica": round(sem, 2), "final": round(.7 * sem + .3 * nat / 2, 2),
                         "aprovado": sem >= 4 and float(n.get("claim", 0)) >= 4 and n["licenca"] == 5 and nat >= 7}
        print(f"{tid}: {sum('nota' in c for c in r['candidatos'])} com nota, "
              f"{sum(c.get('nota', {}).get('aprovado', False) for c in r['candidatos'])} aprovados")
    (D / "candidatos.json").write_text(json.dumps(J, ensure_ascii=False, indent=1))


# ---------- relatório / baixa ----------

def top(r, k=3):
    return sorted([c for c in r["candidatos"] if "nota" in c], key=lambda c: -c["nota"]["final"])[:k]


def cmd_relatorio(a):
    D = Path(a.dir); J = json.loads((D / "candidatos.json").read_text())
    L = [f"# B-roll — candidatos ({J['cliente']})", "",
         "Vídeos do Pixabay (pixabay.com) e do Pexels (pexels.com), além do acervo. Nota final = 70 % matriz semântica "
         "(0–5) + 30 % naturalidade (0–10 ÷ 2). Aprovado: semântica ≥ 4, claim ≥ 4, licença verificada e naturalidade ≥ 7.", ""]
    for tid, r in J["trechos"].items():
        t = r["trecho"]
        L += [f"## {tid} ({t['inicio']:.1f}–{t['fim']:.1f} s, {t['slot']})", f"> {t['fala']}", ""]
        best = top(r)
        if not best:
            L += ["Nenhum candidato com nota. " + (f"Fora do filtro: {r['rejeitados']}" if r["rejeitados"] else ""), ""]
            continue
        L += ["| # | fonte | nota | natural. | semânt. | ok | risco | página |", "|---|---|---|---|---|---|---|---|"]
        for c in best:
            n = r["candidatos"].index(c) + 1; s = c["nota"]
            L.append(f"| {n} | {c['fonte']} {c['w']}x{c['h']} | {s['final']} | {s.get('naturalidade')} | {s['semantica']} | "
                     f"{'sim' if s['aprovado'] else 'não'} | {s.get('risco', '')} | {c['pagina']} |")
        L += ["", f"Folha: `{D / 'folhas' / (tid + '.jpg')}`", ""]
    txt = "\n".join(L) + "\n"
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True); Path(a.md).write_text(txt); print(a.md)
    else:
        print(txt)


def cmd_baixa(a):
    D = Path(a.dir); J = json.loads((D / "candidatos.json").read_text())
    r = J["trechos"][a.trecho]; c = r["candidatos"][a.n - 1]
    destino = Path(a.proj) / "03_assets" / "broll"
    run = lambda *x: subprocess.run([sys.executable, str(fontes.ACERVO), *x], capture_output=True, text=True)
    if c["fonte"] == "acervo":
        k = c["id"]
    else:
        arq = D / "baixados" / f"{c['fonte']}_{c['id']}.mp4"
        if not arq.exists():
            rede.baixa(c["arquivo"], arq, c["pagina"] or None)
        meta = {k: c[k] for k in ("fonte", "id", "autor", "query")} | {"url": c["pagina"], "nota": c.get("nota", {}).get("final")}
        tags = ",".join(["stock", c["fonte"]] + re.findall(r"[a-zà-ú]{4,}", (c["tags"] + " " + c["query"]).lower())[:12])
        p = run("add", str(arq), "--type", "video", "--client", "stock", "--tags", tags, "--license", c["licenca"],
                "--id", f"{c['fonte']}-{c['id']}", "--meta", json.dumps(meta, ensure_ascii=False),
                "--note", f"B-roll: {r['trecho'].get('ideia') or r['trecho']['fala'][:80]}")
        if p.returncode:
            sys.exit(p.stderr[-500:])
        k = p.stdout.split()[0]
    p = run("get", k, "--to", str(destino), "--client", J["cliente"])
    if p.returncode:
        sys.exit(p.stderr[-500:])
    # o get com --client já registra o uso (não repete com `usa`)
    print(f"{k} → {destino}  (licença: {c['licenca']}; página: {c['pagina']})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("checa"); p.add_argument("plano"); p.set_defaults(f=cmd_checa)
    p = sp.add_parser("pexels-js"); p.add_argument("plano"); p.add_argument("-n", type=int, default=8); p.set_defaults(f=cmd_pexels_js)
    p = sp.add_parser("busca"); p.add_argument("plano"); p.add_argument("dir"); p.add_argument("--pexels")
    p.add_argument("-n", type=int, default=10, help="resultados por query e fonte"); p.add_argument("--max", type=int, default=20)
    p.set_defaults(f=cmd_busca)
    p = sp.add_parser("quadros"); p.add_argument("dir"); p.set_defaults(f=cmd_quadros)
    p = sp.add_parser("nota"); p.add_argument("dir"); p.add_argument("--manual"); p.set_defaults(f=cmd_nota)
    p = sp.add_parser("relatorio"); p.add_argument("dir"); p.add_argument("--md"); p.set_defaults(f=cmd_relatorio)
    p = sp.add_parser("baixa"); p.add_argument("dir"); p.add_argument("trecho"); p.add_argument("n", type=int)
    p.add_argument("--proj", required=True); p.set_defaults(f=cmd_baixa)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
