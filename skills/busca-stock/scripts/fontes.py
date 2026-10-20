"""Fontes de vídeo stock da busca-stock. Toda fonte devolve candidatos no mesmo formato:

  {"fonte", "id", "pagina", "autor", "licenca", "w", "h", "dur", "preview", "arquivo", "query", "tags"}

`preview` é um arquivo pequeno para tirar quadros; `arquivo` é a maior resolução (só baixada depois da escolha).
Fonte nova (Mixkit, Coverr…): uma classe com `nome`, `licenca` e `busca(query, n)`, registrada em FONTES.
Antes de registrar, confira a licença da fonte e de cada item: fonte sem licença verificável fica de fora.
"""
from __future__ import annotations

import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rede

ACERVO = Path(__file__).resolve().parents[2] / "acervo" / "scripts" / "acervo.py"


class Pixabay:
    """API oficial (chave grátis). Pixabay Content License: uso comercial sem crédito; proibido revender o arquivo
    sem alteração, usar marca/logo visível em produto, e uso enganoso ou ofensivo com pessoa reconhecível.
    A API pede cache de 24 h (rede.get_json faz) e que se diga de onde vem o resultado (vai no relatório)."""
    nome, licenca = "pixabay", "Pixabay Content License (uso comercial, sem crédito obrigatório)"

    def __init__(self):
        self.key = rede.chave("PIXABAY_API_KEY")

    def ok(self):
        return bool(self.key or rede.MOCK)

    def busca(self, query, n=20):
        d = rede.get_json("https://pixabay.com/api/videos/", {"key": self.key or "mock", "q": query, "per_page": max(3, min(n, 200)),
                                                              "video_type": "film", "safesearch": "true"})
        out = []
        for h in d.get("hits", []):
            v = h.get("videos", {})
            big = next((v[k] for k in ("large", "medium", "small") if v.get(k, {}).get("url")), None)
            prev = next((v[k] for k in ("tiny", "small", "medium") if v.get(k, {}).get("url")), None)
            if not big or not prev:
                continue
            out.append({"fonte": self.nome, "id": str(h["id"]), "pagina": h.get("pageURL", ""), "autor": h.get("user", ""),
                        "licenca": self.licenca, "w": big["width"], "h": big["height"], "dur": float(h.get("duration", 0)),
                        "preview": prev["url"], "arquivo": big["url"], "query": query, "tags": h.get("tags", "")})
        return out


class PexelsChrome:
    """Pexels sem chave (emissão de chaves pausada em 10/2026): a busca roda numa aba do Pexels no Chrome com
    `pexels_chrome.js` e o resultado vira um JSON (--pexels). Pexels License: uso livre e comercial, sem crédito;
    proibido mostrar pessoa reconhecível de forma ofensiva, sugerir endosso, revender sem alterar."""
    nome, licenca = "pexels", "Pexels License (uso comercial, sem crédito obrigatório)"

    def __init__(self, arquivo=None):
        self.itens = json.loads(Path(arquivo).read_text()) if arquivo and Path(arquivo).exists() else []

    def ok(self):
        return bool(self.itens)

    def busca(self, query, n=20):
        out = []
        for it in [x for x in self.itens if x.get("query") == query][:n]:
            files = sorted(it.get("files", []), key=lambda f: f.get("width") or 0)
            prev = next((f["link"] for f in files if (f.get("width") or 0) >= 360), files[0]["link"] if files else None)
            if not prev:
                continue
            out.append({"fonte": self.nome, "id": str(it["id"]), "pagina": it.get("url", ""), "autor": it.get("user", ""),
                        "licenca": self.licenca, "w": it.get("width", 0), "h": it.get("height", 0), "dur": float(it.get("duration", 0)),
                        "preview": prev, "arquivo": f"https://www.pexels.com/download/video/{it['id']}/", "query": query, "tags": it.get("alt", "")})
        return out


class Acervo:
    """Primeiro o acervo local: vídeos já catalogados que este cliente ainda não usou."""
    nome = "acervo"

    def __init__(self, cliente):
        self.cliente = cliente

    def ok(self):
        return ACERVO.exists()

    def busca(self, query, n=20):
        r = subprocess.run([sys.executable, str(ACERVO), "find", *query.split(), "--type", "video", "--sem-uso", self.cliente,
                            "-n", str(n), "--json"], capture_output=True, text=True)
        try:
            itens = json.loads(r.stdout or "[]")
        except ValueError:
            return []
        out, termos = [], [t for t in query.lower().split() if len(t) >= 4]
        for it in itens:
            hay = " ".join([it["name"], " ".join(it.get("tags", [])), it.get("note") or ""]).lower()
            # metade dos termos da cena no nome/tags; palavra solta ("home") traz qualquer coisa
            if not it.get("ok") or sum(t in hay for t in termos) < max(2, len(termos) // 2):
                continue
            w, _, h = (it.get("video") or "0x0").split("@")[0].partition("x")
            out.append({"fonte": self.nome, "id": it["id"], "pagina": (it.get("meta") or {}).get("url", ""),
                        "autor": (it.get("meta") or {}).get("autor", ""), "licenca": it.get("license") or "",
                        "w": int(w or 0), "h": int(h or 0), "dur": float(it.get("duration") or 0),
                        "preview": it["abs"], "arquivo": it["abs"], "query": query, "tags": " ".join(it.get("tags", []))})
        return out


FONTES = {"pixabay": Pixabay, "pexels": PexelsChrome}   # próximas: Mixkit (licença restrita no gratuito), Coverr (API com chave)
