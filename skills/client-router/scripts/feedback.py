#!/usr/bin/env python3
"""Registro das correções do editor, para ver onde o CIBO mais erra e onde vale investir.

  feedback.py add --cliente joao-campos --categoria capa --texto "capas 1, 3 e 6 horríveis" \
                  [--skill podcast-reels] [--acao "close de rosto olhando para a câmera"]
  feedback.py resumo [--dias 30]           contagem por categoria e por cliente
  feedback.py lista [--categoria capa] [-n 20]

Categorias: capa, legenda, clique, audio, trilha, enquadramento, motion, cor, corte (escolha do
trecho), entrega, render (tempo), tokens, skill (não usou a skill certa), asset (perguntou onde
estava), processo, outro. Toda correção do usuário entra aqui no mesmo turno em que vira
atualização de skill. O arquivo fica no repositório (references/feedback.jsonl) e anda com o CIBO.
"""
import argparse, collections, json, os, time
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "references" / "feedback.jsonl"
CATS = ["capa", "legenda", "clique", "audio", "trilha", "enquadramento", "motion", "cor", "corte", "entrega",
        "render", "tokens", "skill", "asset", "processo", "outro"]


def load():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("add")
    p.add_argument("--cliente", required=True); p.add_argument("--categoria", required=True, choices=CATS)
    p.add_argument("--texto", required=True); p.add_argument("--skill"); p.add_argument("--acao")
    p.add_argument("--data", default=time.strftime("%Y-%m-%d"))
    p = sp.add_parser("resumo"); p.add_argument("--dias", type=int, default=0)
    p = sp.add_parser("lista"); p.add_argument("--categoria"); p.add_argument("-n", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "add":
        LOG.parent.mkdir(parents=True, exist_ok=True)
        e = {"data": a.data, "cliente": a.cliente, "categoria": a.categoria, "texto": a.texto,
             "skill": a.skill, "acao": a.acao}
        with open(LOG, "a") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print("registrado:", a.categoria, "/", a.cliente)
        return
    rows = load()
    if a.cmd == "resumo":
        if a.dias:
            lim = time.strftime("%Y-%m-%d", time.localtime(time.time() - a.dias * 86400))
            rows = [r for r in rows if r["data"] >= lim]
        print(f"{len(rows)} correções" + (f" nos últimos {a.dias} dias" if a.dias else ""))
        for nome, campo in (("categoria", "categoria"), ("cliente", "cliente"), ("skill", "skill")):
            c = collections.Counter(r.get(campo) or "-" for r in rows)
            print(f"  por {nome}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    else:
        rows = [r for r in rows if not a.categoria or r["categoria"] == a.categoria][-a.n:]
        for r in rows:
            print(f"{r['data']} [{r['categoria']}/{r['cliente']}] {r['texto']}" + (f"  → {r['acao']}" if r.get("acao") else ""))


if __name__ == "__main__":
    main()
