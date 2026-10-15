#!/usr/bin/env python3
"""Acervo do CIBO: biblioteca de assets de edição com lugar fixo, catálogo e cópias.

A biblioteca mora num lugar só, escolhido pelo editor na primeira vez (`init`) e gravado
em ~/.cibo/acervo.json. O catálogo (`catalog.json`) fica dentro da biblioteca e anda com ela.

  acervo.py where                          onde está a biblioteca e se está acessível
  acervo.py init CAMINHO                   cria a biblioteca (pergunte ao editor antes)
  acervo.py move-library CAMINHO           copia a biblioteca para outro lugar e passa a usar lá
  acervo.py add ARQ [--type T] [--client C] [--tags a,b] [--note "..."] [--license "..."] [--ref]
                                           copia para a biblioteca e cataloga (--ref: só indexa)
  acervo.py index PASTA [--type T] [--client C] [--tags a,b]
                                           indexa uma pasta inteira como referência (sem copiar)
  acervo.py find TERMOS... [--type T] [--client C] [-n 10] [--json]
  acervo.py path ID [--segment N]          caminho absoluto (para scripts)
  acervo.py get ID --to PASTA [--segment N]
                                           copia para o projeto e registra em 07_manifests/assets_usados.md
  acervo.py segments ID [--min-black 0.3]  acha trechos separados por preto (pacotes de transição)
  acervo.py check                          confere tudo; religa pelo hash o que mudou de lugar
  acervo.py dupes                          arquivos repetidos (mesmo hash)
Só biblioteca padrão; ffprobe/ffmpeg para mídia.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, shutil, subprocess, sys, time, unicodedata
from pathlib import Path

CONF = Path(os.environ.get("CIBO_ACERVO_CONF", Path.home() / ".cibo" / "acervo.json"))
SUGESTAO = str(Path.home() / "CIBO Acervo")
try:
    from skills._shared.paths import cibo_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from skills._shared.paths import cibo_root
REGISTRY = Path(os.environ.get("CIBO_CLIENT_REGISTRY", cibo_root() / "skills/client-router/references/client-registry.json"))
MEDIA = {".mp4", ".mov", ".mkv", ".webm", ".wav", ".mp3", ".aif", ".aiff", ".m4a", ".flac", ".ogg"}
SKIP = {".DS_Store", "Thumbs.db"}


# ------------------------------------------------------------------ config / catálogo
def conf() -> dict:
    try:
        raw = CONF.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Configuração criada no Windows com encoding legado do PowerShell.
            text = raw.decode("cp1252")
        return json.loads(text)
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def lib() -> Path:
    c = conf()
    if not c.get("library"):
        sys.exit(f"ACERVO_SEM_BIBLIOTECA: pergunte ao editor onde a biblioteca deve ficar "
                 f"(sugestão: {SUGESTAO}) e rode `acervo.py init CAMINHO`.")
    p = Path(c["library"])
    if not p.exists():
        sys.exit(f"ACERVO_INACESSIVEL: a biblioteca {p} não está acessível (SSD desconectado?). "
                 f"Peça ao editor para conectar o disco; não procure cópias soltas.")
    return p


def cat_path() -> Path:
    return lib() / "catalog.json"


def load() -> dict:
    try:
        return json.loads(cat_path().read_text())
    except (OSError, ValueError):
        return {"version": 1, "items": {}}


def save(cat: dict) -> None:
    p = cat_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(cat, ensure_ascii=False, indent=1) + "\n")
    tmp.replace(p)
    # cópia de segurança do catálogo fora do disco da biblioteca (é pequeno)
    bk = CONF.parent / "catalog_backup.json"
    bk.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, bk)


# ------------------------------------------------------------------ utilidades
def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "item"


def qhash(p: Path) -> str:
    """Hash rápido: tamanho + 4 MB do começo + 4 MB do fim. Basta para achar o mesmo arquivo."""
    h = hashlib.sha256()
    size = p.stat().st_size
    h.update(str(size).encode())
    with open(p, "rb") as f:
        if size <= 8 << 20:          # pequeno: arquivo inteiro
            h.update(f.read())
        else:
            h.update(f.read(4 << 20))
            f.seek(-(4 << 20), 2)
            h.update(f.read())
    return h.hexdigest()[:20]


def media_info(p: Path) -> dict:
    if p.suffix.lower() not in MEDIA:
        return {}
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,width,height,r_frame_rate",
                          "-of", "json", str(p)], capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
    except ValueError:
        return {}
    info = {"duration": round(float(d.get("format", {}).get("duration") or 0), 3)}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if v:
        info["video"] = f'{v.get("width")}x{v.get("height")}@{v.get("r_frame_rate")}'
    info["audio"] = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    return info


def guess_type(p: Path) -> str:
    n = str(p).lower()
    ext = p.suffix.lower()
    if ext in {".ttf", ".otf", ".woff", ".woff2"}:
        return "fonte"
    if ext == ".onnx":
        return "modelo"
    if "burn" in n or "film burn" in n:
        return "filmburn"
    if re.search(r"click|clique|whoosh|swoosh|pop|efx|sfx|riser|hit|impact|transi", n) and ext in {".wav", ".mp3", ".aif", ".aiff", ".m4a"}:
        return "sfx"
    if ext in {".wav", ".mp3", ".aif", ".aiff", ".m4a", ".flac", ".ogg"}:
        return "musica"
    if "logo" in n and ext in {".png", ".svg", ".pdf", ".ai"}:
        return "logo"
    if ext in {".mp4", ".mov", ".mkv", ".webm"}:
        return "overlay" if re.search(r"overlay|light|leak|grain|card|seguir|instagram", n) else "video"
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        return "imagem"
    if ext in {".cube", ".3dl"}:
        return "lut"
    return "outro"


def guess_client(p: Path) -> str:
    n = slug(str(p))
    try:
        reg = json.loads(REGISTRY.read_text())
    except (OSError, ValueError):
        reg = {}
    for key, v in reg.items():
        for a in [key] + v.get("aliases", []):
            if len(slug(a)) > 3 and slug(a) in n:
                return key
    return "_global"


def resolve(it: dict) -> Path:
    return lib() / it["rel"] if it["kind"] == "lib" else Path(it["path"])


def new_id(cat: dict, typ: str, name: str) -> str:
    base = f"{typ}-{slug(Path(name).stem)}"[:70]
    i, out = 1, base
    while out in cat["items"]:
        i += 1
        out = f"{base}-{i}"
    return out


def by_hash(cat: dict) -> dict:
    return {it["qhash"]: k for k, it in cat["items"].items()}


# ------------------------------------------------------------------ comandos
def cmd_init(a):
    p = Path(a.caminho).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    CONF.parent.mkdir(parents=True, exist_ok=True)
    c = conf()
    c.update({"library": str(p), "since": time.strftime("%Y-%m-%d")})
    CONF.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    if not (p / "catalog.json").exists():
        save({"version": 1, "items": {}})
    print(f"biblioteca: {p}")


def cmd_where(a):
    c = conf()
    p = Path(c["library"]) if c.get("library") else None
    ok = bool(p and p.exists())
    n = len(load()["items"]) if ok else "?"
    print(json.dumps({"library": str(p) if p else None, "acessivel": ok, "itens": n,
                      "config": str(CONF)}, ensure_ascii=False))


def add_one(cat, src: Path, typ, client, tags, note, lic, ref, want_id=None) -> str:
    src = src.expanduser().resolve()
    qh = qhash(src)
    known = by_hash(cat).get(qh)
    if known:   # mesmo arquivo já catalogado: só junta metadados
        it = cat["items"][known]
        it["tags"] = sorted(set(it["tags"]) | set(tags))
        if note and note not in (it.get("note") or ""):
            it["note"] = ((it.get("note") or "") + " | " + note).strip(" |")
        it.setdefault("seen_at", [])
        if str(src) not in it["seen_at"] and str(src) != str(resolve(it)):
            it["seen_at"].append(str(src))
        return known
    typ = typ or guess_type(src)
    client = client or guess_client(src)
    k = want_id if want_id and want_id not in cat["items"] else new_id(cat, typ, src.name)
    it = {"id": k, "name": src.name, "type": typ, "client": client, "tags": sorted(set(tags)),
          "note": note or "", "license": lic or "", "qhash": qh, "size": src.stat().st_size,
          "source": str(src), "added": time.strftime("%Y-%m-%d"), **media_info(src)}
    if ref:
        it.update(kind="ref", path=str(src))
    else:
        rel = Path(typ) / client / src.name
        dst = lib() / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and qhash(dst) != qh:
            dst = dst.with_name(f"{dst.stem}_{qh[:6]}{dst.suffix}")
            rel = dst.relative_to(lib())
        if not dst.exists():
            shutil.copy2(src, dst)
        it.update(kind="lib", rel=str(rel))
    cat["items"][k] = it
    return k


def cmd_add(a):
    cat = load()
    k = add_one(cat, Path(a.arquivo), a.type, a.client, [t for t in (a.tags or "").split(",") if t],
                a.note, a.license, a.ref, a.id)
    save(cat)
    it = cat["items"][k]
    print(f"{k}  [{it['kind']}]  {resolve(it)}")


def cmd_index(a):
    cat = load()
    root = Path(a.pasta).expanduser().resolve()
    n0 = len(cat["items"])
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in SKIP and not p.name.startswith("._"):
            add_one(cat, p, a.type, a.client, [t for t in (a.tags or "").split(",") if t], None, None, True)
    cat.setdefault("indexed_roots", [])
    if str(root) not in cat["indexed_roots"]:
        cat["indexed_roots"].append(str(root))
    save(cat)
    print(f"{root}: {len(cat['items']) - n0} novos (total {len(cat['items'])})")


def score(it, terms):
    hay = slug(" ".join([it["id"], it["name"], it["type"], it["client"], " ".join(it["tags"]),
                         it.get("note", ""), it.get("source", "")]))
    s = 0
    for t in terms:
        t = slug(t)
        if t and t in hay:
            s += 3 if t in slug(it["name"]) or t in it["tags"] else 1
    return s + (2 if s and "favorito" in it["tags"] else 0)


def cmd_find(a):
    cat = load()
    a.termos = [t for x in a.termos for t in x.split()]
    res = []
    for it in cat["items"].values():
        if a.type and it["type"] != a.type:
            continue
        if a.client and it["client"] not in (a.client, "_global"):
            continue
        s = score(it, a.termos) if a.termos else 1
        if s:
            res.append((s, it))
    res.sort(key=lambda x: (-x[0], x[1]["id"]))
    res = res[: a.n]
    if a.json:
        print(json.dumps([dict(it, abs=str(resolve(it)), ok=resolve(it).exists()) for _, it in res], ensure_ascii=False))
        return
    for _, it in res:
        p = resolve(it)
        seg = f" segs={len(it['segments'])}" if it.get("segments") else ""
        print(f"{'ok ' if p.exists() else 'FALTA'} {it['id']} [{it['type']}/{it['client']}]{seg} {p}"
              + (f"\n      nota: {it['note']}" if it.get("note") else ""))
    if not res:
        print("nada encontrado — se o editor apontar o arquivo, rode `acervo.py add` na hora")


def get_item(cat, key):
    if key in cat["items"]:
        return cat["items"][key]
    hits = [it for it in cat["items"].values() if score(it, key.split()) >= 3]
    if len(hits) == 1:
        return hits[0]
    sys.exit(f"ID ambíguo ou desconhecido: {key} ({len(hits)} candidatos) — use `find`")


def segment_file(it, n, dst: Path) -> Path:
    s = it["segments"][n - 1]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s[0]:.3f}", "-i", str(resolve(it)), "-t",
                    f"{s[1] - s[0]:.3f}", "-c:v", "libx264", "-crf", "12", "-preset", "fast",
                    "-c:a", "pcm_s16le", str(dst)], check=True)
    return dst


def cmd_path(a):
    cat = load()
    it = get_item(cat, a.id)
    if a.segment:
        cache = lib() / "_segmentos" / f"{it['id']}_{a.segment:02d}.mov"
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            segment_file(it, a.segment, cache)
        print(cache)
    else:
        print(resolve(it))


def cmd_get(a):
    cat = load()
    it = get_item(cat, a.id)
    to = Path(a.to).expanduser().resolve()
    to.mkdir(parents=True, exist_ok=True)
    if a.segment:
        dst = segment_file(it, a.segment, to / f"{Path(it['name']).stem}_{a.segment:02d}.mov")
    else:
        dst = to / it["name"]
        if not dst.exists() or qhash(dst) != it["qhash"]:
            shutil.copy2(resolve(it), dst)
    # registro no projeto: sobe até achar 07_manifests
    proj = next((p for p in [to, *to.parents] if (p / "07_manifests").is_dir()), None)
    if proj:
        log = proj / "07_manifests" / "assets_usados.md"
        new = not log.exists()
        with open(log, "a") as f:
            if new:
                f.write("| Data | ID | Arquivo no projeto | Origem | Licença |\n|---|---|---|---|---|\n")
            f.write(f"| {time.strftime('%Y-%m-%d')} | {it['id']}{f' #{a.segment}' if a.segment else ''} | "
                    f"{dst.relative_to(proj)} | {resolve(it)} | {it.get('license') or '?'} |\n")
    it["uses"] = it.get("uses", 0) + 1
    save(cat)
    print(dst)


def cmd_segments(a):
    cat = load()
    it = get_item(cat, a.id)
    p = resolve(it)
    err = subprocess.run(["ffmpeg", "-nostdin", "-i", str(p), "-vf", f"blackdetect=d={a.min_black}:pix_th=0.10",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    blk = [(float(x), float(y)) for x, y in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    dur = it.get("duration") or media_info(p).get("duration", 0)
    segs, prev_end = [], 0.0
    edges = blk + [(dur, dur)]
    for i, (bs, be) in enumerate(edges):
        if bs - prev_end > 0.15:
            # margem: metade do preto vizinho de cada lado (o burn entra e sai do preto)
            a0 = prev_end - (min(0.4, (prev_end - edges[i - 1][0]) / 2) if i else 0)
            b0 = bs + min(0.4, (be - bs) / 2)
            segs.append([round(max(0, a0), 3), round(min(dur, b0), 3)])
        prev_end = be
    it["segments"] = segs
    save(cat)
    print(f"{it['id']}: {len(segs)} trechos")
    for n, (x, y) in enumerate(segs, 1):
        print(f"  #{n:02d} {x:7.3f}–{y:7.3f} ({y - x:.2f} s)")


def cmd_edit(a):
    """Corrige tipo/cliente/tags/nota; item da biblioteca muda de pasta junto."""
    cat = load()
    it = get_item(cat, a.id)
    if a.type: it["type"] = a.type
    if a.client: it["client"] = a.client
    if a.tags is not None: it["tags"] = sorted({t for t in a.tags.split(",") if t})
    if a.add_tags: it["tags"] = sorted(set(it["tags"]) | {t for t in a.add_tags.split(",") if t})
    if a.note is not None: it["note"] = a.note
    if a.license is not None: it["license"] = a.license
    if it["kind"] == "lib":
        new = Path(it["type"]) / it["client"] / Path(it["rel"]).name
        if str(new) != it["rel"]:
            (lib() / new).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(lib() / it["rel"]), str(lib() / new))
            it["rel"] = str(new)
    save(cat)
    print(it["id"], resolve(it))


def cmd_check(a):
    cat = load()
    hashes = None
    missing, relinked = [], []
    for k, it in cat["items"].items():
        p = resolve(it)
        if p.exists():
            continue
        if it["kind"] == "ref":
            if hashes is None:   # varre as raízes indexadas uma vez só
                hashes = {}
                for r in cat.get("indexed_roots", []):
                    for q in Path(r).rglob("*") if Path(r).exists() else []:
                        if q.is_file() and q.name not in SKIP and not q.name.startswith("._"):
                            hashes.setdefault(qhash(q), q)
            q = hashes.get(it["qhash"])
            if q:
                it["path"] = str(q)
                relinked.append(k)
                continue
        missing.append(k)
    save(cat)
    print(f"{len(cat['items'])} itens; religados {len(relinked)}; faltando {len(missing)}")
    for k in missing[:30]:
        print("  FALTA", k, cat["items"][k].get("path") or cat["items"][k].get("rel"))


def cmd_dupes(a):
    cat = load()
    seen = {}
    for it in cat["items"].values():
        for extra in it.get("seen_at", []):
            seen.setdefault(it["id"], []).append(extra)
    for k, v in seen.items():
        print(k, "também em:", *v, sep="\n  ")
    if not seen:
        print("sem duplicados registrados")


def cmd_move(a):
    old = lib()
    new = Path(a.caminho).expanduser()
    new.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(old, new, dirs_exist_ok=True, copy_function=shutil.copy2)
    except OSError as e:
        sys.exit(f"cópia falhou; biblioteca continua configurada no lugar antigo: {e}")
    c = conf()
    c.update(library=str(new), moved_from=str(old), moved_at=time.strftime("%Y-%m-%d"))
    CONF.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    bad = [k for k, it in load()["items"].items() if it["kind"] == "lib" and not resolve(it).exists()]
    print(f"biblioteca agora em {new}; {len(bad)} itens com problema. A cópia antiga em {old} "
          f"continua lá: apague só depois que o editor confirmar.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init"); p.add_argument("caminho"); p.set_defaults(f=cmd_init)
    p = sp.add_parser("where"); p.set_defaults(f=cmd_where)
    p = sp.add_parser("move-library"); p.add_argument("caminho"); p.set_defaults(f=cmd_move)
    for name, fn in (("add", cmd_add), ("index", cmd_index)):
        p = sp.add_parser(name)
        p.add_argument("arquivo" if name == "add" else "pasta")
        p.add_argument("--type"); p.add_argument("--client"); p.add_argument("--tags")
        if name == "add":
            p.add_argument("--note"); p.add_argument("--license"); p.add_argument("--ref", action="store_true")
            p.add_argument("--id", help="ID curto (ex.: filmburn-pack)")
        p.set_defaults(f=fn)
    p = sp.add_parser("find"); p.add_argument("termos", nargs="*"); p.add_argument("--type"); p.add_argument("--client")
    p.add_argument("-n", type=int, default=10); p.add_argument("--json", action="store_true"); p.set_defaults(f=cmd_find)
    p = sp.add_parser("path"); p.add_argument("id"); p.add_argument("--segment", type=int); p.set_defaults(f=cmd_path)
    p = sp.add_parser("get"); p.add_argument("id"); p.add_argument("--to", required=True); p.add_argument("--segment", type=int)
    p.set_defaults(f=cmd_get)
    p = sp.add_parser("segments"); p.add_argument("id"); p.add_argument("--min-black", type=float, default=0.3)
    p.set_defaults(f=cmd_segments)
    p = sp.add_parser("edit"); p.add_argument("id")
    for o in ("--type", "--client", "--tags", "--add-tags", "--note", "--license"): p.add_argument(o)
    p.set_defaults(f=cmd_edit)
    p = sp.add_parser("check"); p.set_defaults(f=cmd_check)
    p = sp.add_parser("dupes"); p.set_defaults(f=cmd_dupes)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
