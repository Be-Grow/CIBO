#!/usr/bin/env python3
"""Entrega no Google Drive pelo app Drive para desktop: copia, espera sincronizar, devolve links.

  entrega_drive.py PASTA_LOCAL --destino "Meu Drive/Clientes/João/Palestra UEMA"            1º: mostra o plano (nada sobe)
  entrega_drive.py PASTA_LOCAL --destino "…" --aprovado "pode subir, tá ok"                  2º: só depois do OK do editor
  entrega_drive.py PASTA_LOCAL --link https://drive.google.com/drive/folders/<ID>  [--aprovado "…"]
  entrega_drive.py onde                       mostra o Drive montado e os drives compartilhados

TRAVA (editor, 23/11/2026: "a CIBO espera o editor dar okay antes de subir no Drive, isso é de extrema importância"):
nada sobe sem o OK do editor. O 1º passo (sem --aprovado) mostra o plano e grava PASTA/.drive_plano.json. Mostre ao editor
os arquivos e o destino e PERGUNTE. Só com a resposta dele, nas palavras dele, rode com --aprovado "<o que ele disse>".
O envio é recusado se não houver plano mostrado, se um arquivo ou o destino mudou depois (mostre de novo) ou se o texto do
OK estiver vazio. Cada envio fica registrado em PASTA/entregas_drive.log (data, palavras do editor, arquivos, destino).
Nunca invente, resuma ou reaproveite um OK antigo: OK de outro lote ou de outra conversa não vale. Sobe `NN - *.mp4`, `CAPA - *.png` e `POST - *.txt`
(texto do post com hashtags), pulando o que já está lá com o mesmo tamanho. Pasta só
compartilhada com o editor ("Compartilhados comigo") precisa de "Adicionar atalho ao Drive"
antes; drive compartilhado precisa de permissão de Colaborador ou acima.
Links: o app grava o ID de cada item no atributo estendido `com.google.drivefs.item-id#S`
quando termina de sincronizar.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(os.environ.get("CIBO_DRIVE_ROOT", Path.home() / "Google Drive"))
ATTR = "com.google.drivefs.item-id#S"
PADROES = ["[0-9][0-9] - *.mp4", "CAPA - *.png", "POST - *.txt"]


def mounts():
    if os.environ.get("CIBO_DRIVE_ROOT") and ROOT.is_dir():
        return [ROOT]
    if os.name == "nt":
        # Google Drive for desktop commonly mounts a virtual drive such as G:\\My Drive.
        roots = [Path(f"{letter}:/My Drive") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        roots += [Path(f"{letter}:/") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        return sorted({p for p in roots if p.is_dir() and (p.name == "My Drive" or (p / "Shared drives").is_dir())})
    return sorted(p for p in ROOT.glob("GoogleDrive-*") if p.is_dir()) if ROOT.exists() else []


def item_id(p: Path):
    if os.name == "nt":
        # DriveFS item IDs are not exposed as portable Windows extended attributes.
        return None
    r = subprocess.run(["xattr", "-p", ATTR, str(p)], capture_output=True, text=True)
    return r.stdout.strip() or None


def find_by_id(fid: str):
    for m in mounts():
        for sub in m.iterdir():
            if not sub.is_dir():
                continue
            for dirpath, dirs, _ in os.walk(sub):
                if dirpath.count(os.sep) - str(sub).count(os.sep) > 6:
                    dirs[:] = []
                    continue
                if item_id(Path(dirpath)) == fid:
                    return Path(dirpath)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta")
    ap.add_argument("--destino"); ap.add_argument("--link")
    ap.add_argument("--aprovado", help="as palavras do editor autorizando ESTE envio (obrigatório para subir)")
    ap.add_argument("--confirmo", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--espera", type=int, default=900, help="segundos esperando o Drive sincronizar")
    a = ap.parse_args()
    ms = mounts()
    if not ms:
        sys.exit("DRIVE_NAO_INSTALADO: configure CIBO_DRIVE_ROOT para a pasta/drive do Google Drive para desktop. "
                 "No Windows, normalmente é G:\\My Drive ou a unidade escolhida na instalação.")
    if a.pasta == "onde":
        for m in ms:
            print(m)
            for sub in sorted(m.iterdir()):
                if sub.is_dir():
                    print("  ", sub.name, "->", ", ".join(x.name for x in sorted(sub.iterdir())[:8] if x.is_dir()))
        return
    src = Path(a.pasta).expanduser()
    files = sorted({Path(f) for p in PADROES for f in glob.glob(str(src / p))})
    if not files:
        sys.exit(f"nada para subir em {src} (padrões: {', '.join(PADROES)})")
    if a.link:
        if os.name == "nt":
            sys.exit("No Windows o DriveFS não expõe o ID da pasta ao script; informe --destino relativo a CIBO_DRIVE_ROOT.")
        m = re.search(r"folders/([\w-]+)", a.link) or re.search(r"id=([\w-]+)", a.link)
        if not m:
            sys.exit("link de pasta não reconhecido")
        dst = find_by_id(m.group(1))
        if not dst:
            sys.exit("PASTA_NAO_ENCONTRADA no Drive montado: se ela foi só compartilhada com você, abra no "
                     "navegador e use 'Organizar > Adicionar atalho ao Drive'; depois rode de novo.")
    elif a.destino:
        dst = ms[0] / a.destino
    else:
        sys.exit("informe --destino ou --link")
    plano = [(f, dst / f.name) for f in files if not ((dst / f.name).exists() and (dst / f.name).stat().st_size == f.stat().st_size)]
    print(f"destino: {dst}\n{len(plano)} para subir, {len(files) - len(plano)} já estão lá")
    for f, _ in plano:
        print("  ", f.name, f"({f.stat().st_size / 2**20:.1f} MB)")
    assin = {"destino": str(dst), "arquivos": [[f.name, f.stat().st_size, int(f.stat().st_mtime)] for f in files]}
    plano_f = src / ".drive_plano.json"
    if a.confirmo and not a.aprovado:
        sys.exit("--confirmo não vale mais: o envio exige --aprovado com as palavras do editor (trava de 23/11/2026).")
    if not a.aprovado:
        plano_f.write_text(json.dumps({**assin, "mostrado_em": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False, indent=1))
        print("NADA FOI ENVIADO. Mostre a lista e o destino acima ao editor e espere o OK dele.")
        return
    if not a.aprovado.strip():
        sys.exit("OK vazio: pergunte ao editor.")
    try:
        mostrado = json.loads(plano_f.read_text())
    except (OSError, ValueError):
        sys.exit("RECUSADO: o editor ainda não viu o plano. Rode sem --aprovado, mostre a lista e pergunte.")
    if {k: mostrado.get(k) for k in assin} != assin:
        sys.exit("RECUSADO: arquivos ou destino mudaram depois que o editor viu o plano. Rode sem --aprovado e mostre de novo.")
    dst.mkdir(parents=True, exist_ok=True)
    for f, d in plano:
        shutil.copy2(f, d)
    with open(src / "entregas_drive.log", "a", encoding="utf-8") as lg:
        lg.write(json.dumps({"data": time.strftime("%Y-%m-%d %H:%M"), "ok_do_editor": a.aprovado.strip(), "destino": str(dst),
                             "arquivos": [f.name for f, _ in plano], "plano_mostrado_em": mostrado.get("mostrado_em")},
                            ensure_ascii=False) + "\n")
    plano_f.unlink(missing_ok=True)   # o OK vale para ESTE envio: outro envio precisa de outro plano e outro OK
    alvo = [dst / f.name for f in files]
    t0 = time.time()
    while os.name != "nt" and time.time() - t0 < a.espera:
        falta = [p for p in alvo if not item_id(p)]
        if not falta:
            break
        time.sleep(10)
    print("pasta:", f"https://drive.google.com/drive/folders/{item_id(dst)}" if item_id(dst) else f"{dst} (confirme a sincronização no Drive para desktop)")
    for p in alvo:
        i = item_id(p)
        print(f"  {p.name}: " + (f"https://drive.google.com/file/d/{i}/view" if i else "AINDA SINCRONIZANDO"))


if __name__ == "__main__":
    main()
