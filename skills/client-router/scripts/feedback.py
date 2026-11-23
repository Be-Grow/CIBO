#!/usr/bin/env python3
"""Registro das correções do editor, para ver onde o CIBO mais erra e fazer o erro repetido virar trava.

  feedback.py add --cliente joao-campos --categoria capa --texto "capas 1, 3 e 6 horríveis" \
                  [--skill podcast-reels] [--acao "close de rosto olhando para a câmera"] [--padrao borda-na-voz]
  feedback.py resumo [--dias 30]           contagem por categoria, cliente, skill e padrão
  feedback.py repetidos [--dias 0]         a pauta da revisão semanal: padrões que voltaram (sem trava = virar trava;
                                           com trava = a trava falhou)
  feedback.py lista [--categoria capa] [--padrao X] [-n 20]
  feedback.py padroes                      os padrões conhecidos e onde está a trava de cada um
  feedback.py classifica [--aplica]        sugere padrão e normaliza o cliente nas linhas antigas (sem --aplica só conta)

Categorias: capa, legenda, clique, audio, trilha, enquadramento, motion, cor, corte (escolha do
trecho), entrega, render (tempo), tokens, skill (não usou a skill certa), asset (perguntou onde
estava), processo, outro. Toda correção do usuário entra aqui no mesmo turno em que vira
atualização de skill. O arquivo fica no repositório (references/feedback.jsonl) e anda com o CIBO.

Aprendizado (23/11/2026): toda correção ganha um PADRÃO (tipo de erro, references/padroes.json). O `add` sugere o padrão
pelas palavras e diz quantas vezes ele já apareceu:
  1ª vez                 registra (e, se for gosto do cliente, `licao.py add` também);
  2ª vez sem trava       "VIRA TRAVA": anote em todo.md (seção "Viram trava") e faça a trava fora de produção;
  voltou COM trava       "A TRAVA FALHOU": a correção é na trava, não só no vídeo.
Padrão novo: `--padrao nome-curto` cria a entrada em padroes.json (descreva e ponha palavras depois).
"""
import argparse, collections, json, time, unicodedata
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "references"
LOG = REF / "feedback.jsonl"
PADROES = REF / "padroes.json"
REGISTRO = REF / "client-registry.json"
CATS = ["capa", "legenda", "clique", "audio", "trilha", "enquadramento", "motion", "cor", "corte", "entrega",
        "render", "tokens", "skill", "asset", "processo", "outro"]


def load():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]


def padroes():
    try:
        return {k: v for k, v in json.loads(PADROES.read_text()).items() if not k.startswith("_")}
    except FileNotFoundError:
        return {}


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def cliente(c):
    """nome do cliente no formato do client-registry (mesmo cliente com dois nomes estraga o resumo)"""
    base = _sem_acento(c.split("(")[0].strip().lower())
    try:
        reg = json.loads(REGISTRO.read_text())
    except FileNotFoundError:
        reg = {}
    for k, v in reg.items():
        nomes = {_sem_acento(x.lower()) for x in [k] + list(v.get("aliases") or [])}
        if base in nomes or base.replace(" ", "-") in nomes:
            return k
    return base.replace(" ", "-")


def sugere(texto, categoria):
    t = _sem_acento(texto.lower()); melhor = None
    for nome, p in padroes().items():
        hits = sum(_sem_acento(w.lower()) in t for w in p.get("palavras", []))
        if hits and (not p.get("categorias") or categoria in p["categorias"] or hits >= 2):
            if not melhor or hits > melhor[1]: melhor = (nome, hits)
    return melhor[0] if melhor else None


def aviso(padrao, rows):
    """o que dizer ao registrar mais uma ocorrência deste padrão"""
    p = padroes().get(padrao, {}); n = sum(r.get("padrao") == padrao for r in rows)
    if p.get("trava"):
        return f"!! A TRAVA FALHOU: '{padrao}' já tem trava ({p['trava']}) e voltou ({n}ª vez). Revise a trava, não só o vídeo."
    if n >= 2:
        return f"!! VIRA TRAVA: '{padrao}' é a {n}ª vez. Anote em todo.md (\"Viram trava\") e faça a trava fora de produção."
    return f"padrão '{padrao}': 1ª vez."


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("add")
    p.add_argument("--cliente", required=True); p.add_argument("--categoria", required=True, choices=CATS)
    p.add_argument("--texto", required=True); p.add_argument("--skill"); p.add_argument("--acao")
    p.add_argument("--padrao"); p.add_argument("--data", default=time.strftime("%Y-%m-%d"))
    p = sp.add_parser("resumo"); p.add_argument("--dias", type=int, default=0)
    p = sp.add_parser("repetidos"); p.add_argument("--dias", type=int, default=0)
    p = sp.add_parser("lista"); p.add_argument("--categoria"); p.add_argument("--padrao"); p.add_argument("-n", type=int, default=20)
    sp.add_parser("padroes")
    p = sp.add_parser("classifica"); p.add_argument("--aplica", action="store_true")
    a = ap.parse_args()

    if a.cmd == "add":
        LOG.parent.mkdir(parents=True, exist_ok=True)
        padrao = a.padrao or sugere(a.texto, a.categoria)
        if a.padrao and a.padrao not in padroes():
            d = json.loads(PADROES.read_text()) if PADROES.exists() else {}
            d[a.padrao] = {"descricao": a.texto[:120], "categorias": [a.categoria], "palavras": [], "trava": ""}
            PADROES.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            print(f"padrão novo '{a.padrao}' criado em padroes.json (complete descrição e palavras)")
        e = {"data": a.data, "cliente": cliente(a.cliente), "categoria": a.categoria, "texto": a.texto,
             "skill": a.skill, "acao": a.acao, "padrao": padrao}
        with open(LOG, "a") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print("registrado:", a.categoria, "/", e["cliente"] + (f" / padrão {padrao}" + (" (sugerido; troque com --padrao se não for)" if not a.padrao else "") if padrao else " / sem padrão"))
        if padrao:
            print(aviso(padrao, load()))
        return

    if a.cmd == "padroes":
        for nome, p in padroes().items():
            print(f"{nome}: {p['descricao']} | trava: {p.get('trava') or 'AINDA NÃO'}")
        return

    rows = load()
    if a.cmd == "classifica":
        mud_cli = collections.Counter(); mud_pad = collections.Counter(); novas = []
        for r in rows:
            r = dict(r); c = cliente(r["cliente"])
            if c != r["cliente"]: mud_cli[f"{r['cliente']} -> {c}"] += 1; r["cliente"] = c
            if not r.get("padrao"):
                s = sugere(r.get("texto", "") + " " + (r.get("acao") or ""), r["categoria"])
                if s: mud_pad[s] += 1; r["padrao"] = s
            novas.append(r)
        print("clientes normalizados: " + (", ".join(f"{k} ({v})" for k, v in mud_cli.items()) or "nenhum"))
        print("padrões sugeridos: " + (", ".join(f"{k} {v}" for k, v in mud_pad.most_common()) or "nenhum"))
        print(f"sem padrão: {sum(not r.get('padrao') for r in novas)} de {len(novas)}")
        if a.aplica:
            bak = LOG.with_name(LOG.name + ".bak-classifica")
            if not bak.exists(): bak.write_text(LOG.read_text())
            LOG.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in novas))
            print(f"gravado (original em {bak.name})")
        else:
            print("só simulação: rode com --aplica para gravar")
        return

    if getattr(a, "dias", 0):
        lim = time.strftime("%Y-%m-%d", time.localtime(time.time() - a.dias * 86400))
        rows = [r for r in rows if r["data"] >= lim]

    if a.cmd == "resumo":
        print(f"{len(rows)} correções" + (f" nos últimos {a.dias} dias" if a.dias else ""))
        for nome, campo in (("categoria", "categoria"), ("cliente", "cliente"), ("skill", "skill"), ("padrão", "padrao")):
            c = collections.Counter(r.get(campo) or "-" for r in rows)
            print(f"  por {nome}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    elif a.cmd == "repetidos":
        P = padroes(); c = collections.Counter(r["padrao"] for r in rows if r.get("padrao"))
        ult = {}
        for r in rows:
            if r.get("padrao"): ult[r["padrao"]] = max(ult.get(r["padrao"], ""), r["data"])
        sem = [(k, n) for k, n in c.most_common() if n >= 2 and not P.get(k, {}).get("trava")]
        com = [(k, n) for k, n in c.most_common() if P.get(k, {}).get("trava")]
        print("VIRAR TRAVA (repetiu e ainda não tem):")
        for k, n in sem: print(f"  {k}: {n}x, última {ult[k]} — {P.get(k, {}).get('descricao', '?')}")
        if not sem: print("  nenhum")
        print("COM TRAVA (ocorrências depois da data da trava = a trava falhou):")
        for k, n in com:
            dt = next((w for w in P[k]["trava"].replace(",", " ").split() if w.count("/") == 2), "")
            depois = 0
            if dt:
                d, m, y = dt.split("/"); iso = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                depois = sum(r.get("padrao") == k and r["data"] > iso for r in rows)
            print(f"  {k}: {n}x no total" + (f", {depois} DEPOIS da trava ({dt}): revisar" if depois else (f", nenhuma depois de {dt}" if dt else "")))
        print(f"sem padrão: {sum(not r.get('padrao') for r in rows)} (classifique na revisão: `lista` + `--padrao`)")
    else:
        rows = [r for r in rows if (not a.categoria or r["categoria"] == a.categoria) and (not a.padrao or r.get("padrao") == a.padrao)][-a.n:]
        for r in rows:
            print(f"{r['data']} [{r['categoria']}/{r['cliente']}" + (f"/{r['padrao']}" if r.get("padrao") else "") + f"] {r['texto']}" + (f"  → {r['acao']}" if r.get("acao") else ""))


if __name__ == "__main__":
    main()
