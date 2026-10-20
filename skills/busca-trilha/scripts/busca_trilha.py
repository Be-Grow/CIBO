#!/usr/bin/env python3
"""Busca de trilha de fundo para fala: acervo primeiro, depois Openverse (CC0 e CC-BY) e Freesound (CC0, opcional).

  busca_trilha.py busca BRIEF DIR          candidatas medidas → DIR/candidatas.json (5–8 aprovadas na medição)
  busca_trilha.py relatorio DIR [--md M]   tabela com medidas, licença e crédito (CC-BY exige crédito na descrição)
  busca_trilha.py previa DIR N --voz V [--em S] [--gap 18.5]   10 s da candidata N sob a voz real (prévia ao editor)
  busca_trilha.py corte DIR N --dur D [--alvo T]               trecho e offset pela analisa_trilha (desenho-de-som)
  busca_trilha.py baixa DIR N --proj PROJ [--cliente C]        cataloga no acervo, registra o uso e copia para 03_assets/trilha

BRIEF (JSON): {"cliente": "andreia", "mood": "calmo, acolhedor", "energia": "baixa"|"media"|"alta", "bpm": [70, 95],
  "queries": ["calm piano ambient", "soft acoustic background"], "duracao_min": 60, "evitar": ["epic", "vocal"]}
Só CC0 e CC-BY: BY-SA obrigaria o vídeo a sair com licença aberta; BY-ND proíbe obra derivada (o filtro
license_type=commercial do Openverse inclui by-nd, por isso a busca usa license=cc0,by). NC fica de fora (uso comercial).
"""
from __future__ import annotations

import argparse, json, re, subprocess, sys
from pathlib import Path

import numpy as np

SK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SK / "busca-stock" / "scripts"))
sys.path.insert(0, str(SK / "talking-head-music" / "scripts"))
import rede
from analyze_music import analyse

ACERVO = SK / "acervo" / "scripts" / "acervo.py"
TRILHA = SK / "desenho-de-som" / "scripts" / "analisa_trilha.py"
VOCAL = ("vocal", "vocals", "singing", "singer", "voice", "lyrics", "rap", "choir", "vox")
LICENCAS = {"cc0": "CC0 (domínio público)", "by": "CC BY"}


# ---------- fontes ----------

class Acervo:
    nome = "acervo"

    def __init__(self, cliente):
        self.cliente = cliente

    def ok(self):
        return ACERVO.exists()

    def busca(self, q, n):
        r = subprocess.run([sys.executable, str(ACERVO), "find", *q.split(), "--type", "musica", "--sem-uso", self.cliente,
                            "-n", str(n), "--json"], capture_output=True, text=True)
        try:
            itens = json.loads(r.stdout or "[]")
        except ValueError:
            return []
        termos = [t for t in q.lower().split() if len(t) >= 4]
        out = []
        for it in itens:
            hay = " ".join([it["name"], " ".join(it.get("tags", [])), it.get("note") or ""]).lower()
            if it.get("ok") and sum(t in hay for t in termos) >= max(1, len(termos) // 2):
                m = it.get("meta") or {}
                out.append({"fonte": "acervo", "id": it["id"], "titulo": it["name"], "autor": m.get("autor", ""),
                            "licenca": it.get("license") or "", "pagina": m.get("url", ""), "credito": m.get("credito", ""),
                            "audio": it["abs"], "dur": float(it.get("duration") or 0), "tags": " ".join(it.get("tags", [])), "query": q})
        return out


class Openverse:
    """API aberta do Openverse (catálogo CC; sem chave, limite anônimo baixo — cache de 24 h do rede.py).
    A licença é a do item (CC0 ou CC BY), conferida campo a campo; CC BY exige crédito (TASL) na descrição do vídeo."""
    nome = "openverse"

    def ok(self):
        return True

    def busca(self, q, n):
        d = rede.get_json("https://api.openverse.org/v1/audio/", {"q": q, "license": "cc0,by", "category": "music",
                                                                  "page_size": max(1, min(n, 20))})
        out = []
        for r in d.get("results", []):
            lic = (r.get("license") or "").lower()
            if lic not in LICENCAS or not r.get("url"):
                continue
            nome = LICENCAS[lic] + (f" {r['license_version']}" if lic == "by" and r.get("license_version") else "")
            out.append({"fonte": self.nome, "id": r["id"], "titulo": r.get("title") or "", "autor": r.get("creator") or "",
                        "licenca": nome, "pagina": r.get("foreign_landing_url") or "", "audio": r["url"],
                        "dur": (r.get("duration") or 0) / 1000, "query": q,
                        "tags": " ".join([t.get("name", "") for t in r.get("tags") or []] + (r.get("genres") or [])),
                        "credito": "" if lic == "cc0" else f"\"{r.get('title')}\" de {r.get('creator')} ({r.get('foreign_landing_url')}), "
                                                           f"licença {nome} (creativecommons.org/licenses/by/{r.get('license_version') or '4.0'}/)"})
        return out


class Freesound:
    """Opcional (FREESOUND_API_KEY). Só CC0. O original exige OAuth2: usa a prévia HQ (mp3 ~128 kb/s) — avise o editor."""
    nome = "freesound"

    def __init__(self):
        self.key = rede.chave("FREESOUND_API_KEY")

    def ok(self):
        return bool(self.key)

    def busca(self, q, n):
        d = rede.get_json("https://freesound.org/apiv2/search/text/",
                          {"query": q, "filter": 'license:"Creative Commons 0" duration:[45 TO 600]', "page_size": max(1, min(n, 30)),
                           "fields": "id,name,username,license,url,duration,tags,previews"}, {"Authorization": f"Token {self.key}"})
        return [{"fonte": self.nome, "id": str(r["id"]), "titulo": r["name"], "autor": r["username"], "licenca": "CC0 (domínio público)",
                 "pagina": r["url"], "audio": r["previews"]["preview-hq-mp3"], "dur": float(r["duration"]), "query": q,
                 "tags": " ".join(r.get("tags", [])), "credito": ""} for r in d.get("results", []) if "previews" in r]


class ElevenLabs:
    """Plano B desligado: música gerada quando nada do banco serve. Ligar só com pedido do editor, a chave
    ELEVENLABS_API_KEY e os termos do plano conferidos (uso comercial depende do plano pago)."""
    nome = "elevenlabs"

    def ok(self):
        return False


# ---------- medição ----------

def banda_voz(path, seg=90):
    """fração da energia espectral em 1–4 kHz (onde mora a inteligibilidade da fala)"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(seg), "-i", str(path), "-ac", "1", "-ar", "22050", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if x.size < 22050:
        return None
    n = 4096
    fr = x[: (x.size // n) * n].reshape(-1, n) * np.hanning(n)
    sp = (np.abs(np.fft.rfft(fr, axis=1)) ** 2).sum(axis=0)
    f = np.fft.rfftfreq(n, 1 / 22050)
    return round(float(sp[(f >= 1000) & (f <= 4000)].sum() / (sp[f >= 40].sum() + 1e-12)), 3)


def bpm_ok(b, faixa):
    if not faixa or not b:
        return True
    return any(faixa[0] <= v <= faixa[1] for v in (b, b / 2, b * 2))


def usados(cliente):
    r = subprocess.run([sys.executable, str(ACERVO), "find", "--type", "musica", "-n", "100000", "--json"], capture_output=True, text=True)
    try:
        itens = json.loads(r.stdout or "[]")
    except ValueError:
        return set()
    return {((it.get("meta") or {}).get("fonte"), str((it.get("meta") or {}).get("id"))) for it in itens
            if any(u.get("client") == cliente for u in it.get("usos", []))}


def cmd_busca(a):
    B = json.loads(Path(a.brief).read_text())
    D = Path(a.dir); (D / "audio").mkdir(parents=True, exist_ok=True)
    fs = [f for f in (Acervo(B["cliente"]), Openverse(), Freesound(), ElevenLabs()) if f.ok()]
    print("fontes:", ", ".join(f.nome for f in fs))
    evitar = [e.lower() for e in B.get("evitar", [])]
    vistos, cands, rej = set(), [], {}
    ja = usados(B["cliente"])   # variedade: trilha não se repete no mesmo cliente
    fora = lambda m: rej.__setitem__(m, rej.get(m, 0) + 1)
    for q in B["queries"]:
        for f in fs:
            try:
                lst = f.busca(q, a.n)
            except Exception as e:
                print(f"  {f.nome} '{q}': {e}", file=sys.stderr); continue
            for c in lst:
                k = (c["fonte"], c["id"])
                if k in vistos:
                    continue
                vistos.add(k)
                if k in ja:
                    fora("já usada por este cliente"); continue
                txt = (c["titulo"] + " " + c["tags"]).lower()
                if any(re.search(rf"\b{v}\b", txt) for v in VOCAL) and "instrumental" not in txt:
                    fora("vocal nas tags"); continue
                if any(e in txt for e in evitar):
                    fora("termo evitado"); continue
                if not c["licenca"]:   # item do acervo sem licença registrada: registre com `acervo edit --license`
                    fora("sem licença registrada"); continue
                if c["dur"] and c["dur"] < B.get("duracao_min", 45):
                    fora("curta"); continue
                cands.append(c)
    medidas = []
    for c in cands[: a.max_medir]:
        arq = Path(c["audio"]) if c["fonte"] == "acervo" else D / "audio" / f"{c['fonte']}_{c['id']}.mp3"
        if not arq.exists():
            try:
                rede.baixa(c["audio"], arq, c["pagina"] or None)
            except Exception as e:
                print(f"  {c['fonte']} {c['id']}: download falhou ({e})", file=sys.stderr); continue
        try:
            m = analyse(str(arq))
        except Exception as e:
            print(f"  {arq.name}: medição falhou ({e})", file=sys.stderr); continue
        c.update(arquivo=str(arq), medida={k: m.get(k) for k in ("duration_seconds", "integrated_lufs", "estimated_bpm",
                                                                  "brightness_centroid_hz", "dynamic_range_db", "crest_factor_db")},
                 banda_voz=banda_voz(arq))
        motivo = None
        if c["banda_voz"] is None or c["banda_voz"] > a.banda_max:
            motivo = "energia em 1–4 kHz alta (briga com a voz)"
        elif not bpm_ok(m.get("estimated_bpm"), B.get("bpm")):
            motivo = "BPM fora da faixa"
        elif m.get("duration_seconds", 0) < B.get("duracao_min", 45):
            motivo = "curta"
        if motivo:
            fora(motivo); continue
        # menos banda de voz e menos dinâmica = fundo mais estável sob a fala
        c["nota"] = round(10 - 30 * c["banda_voz"] - 0.15 * max(0, (m.get("dynamic_range_db") or 0) - 8), 2)
        medidas.append(c)
    medidas.sort(key=lambda c: -c["nota"])
    medidas = medidas[: a.max]
    (D / "candidatas.json").write_text(json.dumps({"brief": B, "candidatas": medidas, "rejeitadas": rej}, ensure_ascii=False, indent=1))
    print(f"{len(medidas)} candidatas" + (f"  (fora: {rej})" if rej else ""))


def carrega(d):
    return json.loads((Path(d) / "candidatas.json").read_text())


def cmd_relatorio(a):
    J = carrega(a.dir); B = J["brief"]
    L = [f"# Trilha — candidatas ({B['cliente']})", "", f"Brief: {B.get('mood', '')}, energia {B.get('energia', '?')}, BPM {B.get('bpm')}.",
         "Fontes: acervo, Openverse (openverse.org) e Freesound (freesound.org). Só CC0 e CC BY. Banda de voz = fração da energia "
         "em 1–4 kHz (acima de 15 % fica de fora).", "",
         "| # | título | autor | fonte | licença | BPM | LUFS | banda voz | dur | nota |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(J["candidatas"], 1):
        m = c["medida"]
        L.append(f"| {i} | {c['titulo'][:40]} | {c['autor'][:24]} | {c['fonte']} | {c['licenca'].split(' — ')[0][:28]} | {m['estimated_bpm']} | "
                 f"{m['integrated_lufs']} | {c['banda_voz'] * 100:.0f} % | {m['duration_seconds']:.0f} s | {c['nota']} |")
    cred = [f"- #{i}: {c['credito']}" for i, c in enumerate(J["candidatas"], 1) if c.get("credito")]
    if cred:
        L += ["", "Crédito obrigatório (CC BY) — vai na descrição do post se a escolhida for uma destas:", *cred]
    L += ["", "Antes do render: `previa` de 10 s das 2–3 melhores no trecho real e aprovação do editor."]
    txt = "\n".join(L) + "\n"
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True); Path(a.md).write_text(txt); print(a.md)
    else:
        print(txt)


def lufs(path, extra=()):
    r = subprocess.run(["ffmpeg", "-hide_banner", *extra, "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -23.0


def cmd_previa(a):
    J = carrega(a.dir); c = J["candidatas"][a.n - 1]
    out = Path(a.dir) / f"previa_{a.n:02d}.mp3"
    sec = ["-ss", str(a.em), "-t", "10"]
    lv, lm = lufs(a.voz, sec), lufs(c["arquivo"], ["-ss", "20", "-t", "10"])
    ganho = (lv - a.gap) - lm
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sec, "-i", a.voz, "-ss", "20", "-t", "10", "-i", c["arquivo"], "-filter_complex",
                    f"[1:a]volume={ganho:.1f}dB,afade=t=in:d=1,afade=t=out:st=9:d=1[m];[0:a][m]amix=inputs=2:normalize=0[o]",
                    "-map", "[o]", "-b:a", "192k", str(out)], check=True)
    print(f"{out}  (trilha {a.gap} dB abaixo da voz; ganho {ganho:+.1f} dB)")


def cmd_corte(a):
    c = carrega(a.dir)["candidatas"][a.n - 1]
    py = SK / "talking-head-music" / ".venv" / "bin" / "python"
    cmd = [str(py if py.exists() else sys.executable), str(TRILHA), c["arquivo"], "--ate", str(max(150, a.dur + 30))]
    if a.alvo is not None:
        cmd += ["--alvo", str(a.alvo)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-2500:] or r.stderr[-800:])
    print(f"duração do vídeo {a.dur:.1f} s; trilha {c['medida']['duration_seconds']:.0f} s"
          + ("  → vai precisar de loop ou emenda" if c["medida"]["duration_seconds"] < a.dur else ""))


def cmd_baixa(a):
    J = carrega(a.dir); c = J["candidatas"][a.n - 1]; cli = a.cliente or J["brief"]["cliente"]
    run = lambda *x: subprocess.run([sys.executable, str(ACERVO), *x], capture_output=True, text=True)
    k = c["id"]
    if c["fonte"] != "acervo":
        meta = {"fonte": c["fonte"], "id": c["id"], "autor": c["autor"], "url": c["pagina"], "query": c["query"],
                "credito": c.get("credito", ""), "bpm": c["medida"]["estimated_bpm"], "banda_voz": c["banda_voz"]}
        tags = ",".join(["trilha", c["fonte"]] + re.findall(r"[a-zà-ú]{4,}", (c["tags"] + " " + c["query"]).lower())[:12])
        p = run("add", c["arquivo"], "--type", "musica", "--client", "stock", "--tags", tags, "--license", c["licenca"],
                "--id", f"{c['fonte']}-{c['id'][:12]}", "--meta", json.dumps(meta, ensure_ascii=False),
                "--note", f"{c['titulo']} — {c['autor']}" + (f" | crédito: {c['credito']}" if c.get("credito") else ""))
        if p.returncode:
            sys.exit(p.stderr[-500:])
        k = p.stdout.split()[0]
    p = run("get", k, "--to", str(Path(a.proj) / "03_assets" / "trilha"), "--client", cli)   # registra o uso
    if p.returncode:
        sys.exit(p.stderr[-500:])
    print(f"{k} → {Path(a.proj) / '03_assets' / 'trilha'}  ({c['licenca']})" + (f"\nCRÉDITO na descrição: {c['credito']}" if c.get("credito") else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("busca"); p.add_argument("brief"); p.add_argument("dir"); p.add_argument("-n", type=int, default=10)
    p.add_argument("--max", type=int, default=8); p.add_argument("--max-medir", type=int, default=24)
    p.add_argument("--banda-max", type=float, default=0.15); p.set_defaults(f=cmd_busca)
    p = sp.add_parser("relatorio"); p.add_argument("dir"); p.add_argument("--md"); p.set_defaults(f=cmd_relatorio)
    p = sp.add_parser("previa"); p.add_argument("dir"); p.add_argument("n", type=int); p.add_argument("--voz", required=True)
    p.add_argument("--em", type=float, default=0); p.add_argument("--gap", type=float, default=18.5); p.set_defaults(f=cmd_previa)
    p = sp.add_parser("corte"); p.add_argument("dir"); p.add_argument("n", type=int); p.add_argument("--dur", type=float, required=True)
    p.add_argument("--alvo", type=float); p.set_defaults(f=cmd_corte)
    p = sp.add_parser("baixa"); p.add_argument("dir"); p.add_argument("n", type=int); p.add_argument("--proj", required=True)
    p.add_argument("--cliente"); p.set_defaults(f=cmd_baixa)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
