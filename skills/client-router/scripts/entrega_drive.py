#!/usr/bin/env python3
"""Entrega no Google Drive pelo app Drive para desktop: copia, espera sincronizar, devolve links.

  entrega_drive.py PASTA_LOCAL --destino "Meu Drive/Clientes/João/Palestra UEMA"  [--confirmo]
  entrega_drive.py PASTA_LOCAL --link https://drive.google.com/drive/folders/<ID>  [--confirmo]
  entrega_drive.py onde                       mostra o Drive montado e os drives compartilhados

Sem `--confirmo` é só simulação (lista o que subiria): subir para o Drive é publicar, então
confirme com o editor o destino antes. Sobe `NN - *.mp4`, `CAPA - *.png` e `POST - *.txt`
(texto do post com hashtags), pulando o que já está lá com o mesmo tamanho. Pasta só
compartilhada com o editor ("Compartilhados comigo") precisa de "Adicionar atalho ao Drive"
antes; drive compartilhado precisa de permissão de Colaborador ou acima.
Links: o app grava o ID de cada item no atributo estendido `com.google.drivefs.item-id#S`
quando termina de sincronizar.
"""
import argparse, glob, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / "Library" / "CloudStorage"
ATTR = "com.google.drivefs.item-id#S"
PADROES = ["[0-9][0-9] - *.mp4", "CAPA - *.png", "POST - *.txt"]


def mounts():
    return sorted(p for p in ROOT.glob("GoogleDrive-*") if p.is_dir()) if ROOT.exists() else []


def item_id(p: Path):
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
    ap.add_argument("--confirmo", action="store_true")
    ap.add_argument("--espera", type=int, default=900, help="segundos esperando o Drive sincronizar")
    a = ap.parse_args()
    ms = mounts()
    if not ms:
        sys.exit("DRIVE_NAO_INSTALADO: instale o Google Drive para desktop e entre com a conta; ele monta em "
                 "~/Library/CloudStorage/GoogleDrive-<email>/.")
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
    if not a.confirmo:
        print("SIMULAÇÃO: nada foi enviado. Confirme o destino com o editor e rode com --confirmo.")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for f, d in plano:
        shutil.copy2(f, d)
    alvo = [dst / f.name for f in files]
    t0 = time.time()
    while time.time() - t0 < a.espera:
        falta = [p for p in alvo if not item_id(p)]
        if not falta:
            break
        time.sleep(10)
    print("pasta:", f"https://drive.google.com/drive/folders/{item_id(dst)}" if item_id(dst) else "(sem ID ainda)")
    for p in alvo:
        i = item_id(p)
        print(f"  {p.name}: " + (f"https://drive.google.com/file/d/{i}/view" if i else "AINDA SINCRONIZANDO"))


if __name__ == "__main__":
    main()
