#!/usr/bin/env python3
"""Baixa SÓ os trechos pedidos de um vídeo grande do Google Drive (sem baixar o arquivo todo).

Por quê: bruto de podcast no Drive tem 50+ GB e o SSD não comporta; a net também não.
O Drive aceita Range FECHADO (bytes=A-B) mas ignora o aberto (bytes=A-), que é o que o
ffmpeg pede ao buscar. Este script sobe um proxy local que converte cada pedido do ffmpeg
em pedaços fechados de 16 MB e o ffmpeg corta com -c copy (sem recodificar, ~qualidade original).

Uso:
  trecho_drive.py <link-ou-id-do-drive> --saida <projeto>/01_sources \
      --trecho "03=00:42:58-00:44:32" --trecho "04=1:58:51-2:00:27" [--folga 5] [--prefixo cam1]
  trecho_drive.py <link> --info            # só tamanho/duração/streams

Saída: <saida>/<prefixo>_<nome>_<ini>.mp4 com --folga s antes e depois (o corte fino é na edição),
mais <saida>/trechos_drive.json com o deslocamento de cada arquivo (tempo no bruto = tempo no
trecho + offset). Confere áudio x vídeo de cada trecho (memória conferir-fonte-baixada).
O arquivo no Drive precisa estar como "qualquer pessoa com o link".
"""
import argparse, http.server, json, re, socketserver, subprocess, sys, threading, urllib.request

CHUNK = 16 * 1024 * 1024
UA = {"User-Agent": "Mozilla/5.0"}


def file_id(s):
    m = re.search(r"/d/([\w-]{20,})", s) or re.search(r"[?&]id=([\w-]{20,})", s)
    return m.group(1) if m else s.strip()


def resolve(fid):
    """URL direta de download (passa o aviso de 'arquivo grande demais para verificar vírus')."""
    base = f"https://drive.usercontent.google.com/download?id={fid}&export=download"
    req = urllib.request.Request(base, headers={**UA, "Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        ctype, body, cr = r.headers.get("Content-Type", ""), r.read(200000), r.headers.get("Content-Range")
    if not ctype.startswith("text/html"):
        url = base
    else:
        html = body.decode("utf-8", "ignore")
        uuid = re.search(r'name="uuid" value="([^"]+)"', html)
        if not uuid:
            sys.exit("Drive não liberou o download (link privado ou cota excedida). Confira o compartilhamento.")
        url = f"{base}&confirm=t&uuid={uuid.group(1)}"
        req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            cr = r.headers.get("Content-Range")
    size = int(cr.rsplit("/", 1)[1])
    return url, size


def make_proxy(url, size):
    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _range(self):
            m = re.match(r"bytes=(\d+)-(\d*)", self.headers.get("Range", ""))
            if not m:
                return 0, size - 1, False
            a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
            return a, min(b, size - 1), True

        def _head(self, a, b, partial):
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1))
            if partial:
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.end_headers()

        def do_HEAD(self):
            self._head(*self._range())

        def do_GET(self):
            a, b, partial = self._range()
            self._head(a, b, partial)
            pos = a
            try:
                while pos <= b:
                    end = min(pos + CHUNK - 1, b)
                    for tent in range(4):
                        try:
                            req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={pos}-{end}"})
                            with urllib.request.urlopen(req, timeout=60) as r:
                                data = r.read()
                            break
                        except (BrokenPipeError, ConnectionResetError):
                            raise
                        except Exception:
                            if tent == 3:
                                raise
                    self.wfile.write(data)
                    pos = end + 1
            except (BrokenPipeError, ConnectionResetError):
                pass  # ffmpeg já leu o que queria e fechou

    class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    srv = S(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/video.mp4"


def secs(t):
    p = [float(x) for x in t.split(":")]
    while len(p) < 3:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def hms(s):
    s = int(round(s)); return f"{s//3600:02d}{s%3600//60:02d}{s%60:02d}"


def dur(path, sel):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries",
                          "stream=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    try:
        return float(out.split()[0])
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("link")
    ap.add_argument("--trecho", action="append", default=[], help='"nome=INI-FIM" (hh:mm:ss)')
    ap.add_argument("--folga", type=float, default=5.0)
    ap.add_argument("--saida")
    ap.add_argument("--prefixo", default="bruto")
    ap.add_argument("--info", action="store_true")
    a = ap.parse_args()

    url, size = resolve(file_id(a.link))
    srv, local = make_proxy(url, size)
    print(f"Drive ok: {size/1e9:.1f} GB")
    if a.info or not a.trecho:
        subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
                        "-of", "compact", local])
        return
    if not a.saida:
        sys.exit("--saida é obrigatório com --trecho")
    import os
    os.makedirs(a.saida, exist_ok=True)
    man = []
    for t in a.trecho:
        nome, faixa = t.split("=", 1)
        ini, fim = (secs(x) for x in faixa.split("-"))
        s0 = max(0.0, ini - a.folga); d = fim - ini + 2 * a.folga
        out = os.path.join(a.saida, f"{a.prefixo}_{nome}_{hms(ini)}.mp4")
        cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{s0:.3f}", "-i", local, "-t", f"{d:.3f}",
               "-map", "0:v:0", "-map", "0:a?", "-c", "copy", "-avoid_negative_ts", "make_zero",
               "-map_metadata", "-1", "-write_tmcd", "0", "-movflags", "+faststart", out]   # sem tmcd: o grupo Track Reference quebrava o ffprobe csv do reel.py
        r = subprocess.run(cmd, capture_output=True, text=True)
        dv, da = dur(out, "v:0"), dur(out, "a:0")
        ok = r.returncode == 0 and dv > d * 0.95 and abs(dv - da) < 0.5
        mb = os.path.getsize(out) / 1e6 if os.path.exists(out) else 0
        print(f"{'OK ' if ok else 'FALHA'} {nome}: {faixa} -> {os.path.basename(out)} "
              f"({mb:.0f} MB, vídeo {dv:.1f}s / áudio {da:.1f}s)")
        if r.returncode:
            print("   " + r.stderr.strip()[-400:])
        man.append({"nome": nome, "arquivo": out, "pedido": faixa, "offset_s": round(s0, 3),
                    "duracao_video": dv, "duracao_audio": da, "ok": ok})
    with open(os.path.join(a.saida, "trechos_drive.json"), "w") as f:
        json.dump({"fonte": a.link, "bytes": size, "folga_s": a.folga, "trechos": man}, f, ensure_ascii=False, indent=1)
    srv.shutdown()
    sys.exit(0 if all(m["ok"] for m in man) else 1)


if __name__ == "__main__":
    main()
