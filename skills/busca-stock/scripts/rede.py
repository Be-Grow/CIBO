"""Rede das buscas do CIBO (busca-stock e busca-trilha): chaves, GET/POST JSON com nova tentativa no limite (429/5xx),
cache de 24 h (exigência da API do Pixabay) e modo simulado para o teste de regressão.

Chaves: variável de ambiente ou ~/.cibo/chaves.env (NOME=valor), nunca no código nem no repositório.
Modo simulado: CIBO_BUSCA_MOCK=PASTA. Cada host responde com PASTA/<host>.json (ex.: pixabay.com.json) e os downloads
saem de PASTA/downloads.json ({url: arquivo}) ou de PASTA/video.mp4 / PASTA/audio.mp3.
Só biblioteca padrão e o curl do sistema.
"""
from __future__ import annotations

import hashlib, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse
from pathlib import Path

CHAVES = Path(os.environ.get("CIBO_CHAVES", Path.home() / ".cibo" / "chaves.env"))
CACHE = Path(os.environ.get("CIBO_BUSCA_CACHE", Path.home() / ".cache" / "cibo" / "busca"))
MOCK = os.environ.get("CIBO_BUSCA_MOCK")
UA = "CIBO-busca/1.0"


def chave(nome: str) -> str | None:
    if os.environ.get(nome):
        return os.environ[nome]
    try:
        for ln in CHAVES.read_text().splitlines():
            k, _, v = ln.strip().partition("=")
            if k == nome and v:
                return v.strip().strip('"\'')
    except OSError:
        pass
    return None


def _mock_json(url: str):
    host = urllib.parse.urlparse(url).hostname or "x"
    f = Path(MOCK) / f"{host}.json"
    if not f.exists():
        raise RuntimeError(f"simulado sem resposta para {host}")
    return json.loads(f.read_text())


class HTTPError(Exception):
    def __init__(self, code, body=b""):
        super().__init__(f"HTTP {code}: {body[:160]!r}")
        self.code, self.body = code, body


def _cfg(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _abre(url, headers=None, data=None, tentativas=4):
    """GET/POST pelo curl (o Cloudflare do Pixabay recusa o urllib com 403). A URL e os cabeçalhos vão pelo stdin
    (curl -K -), assim a chave não aparece no `ps`. Espera crescente em 429/5xx; respeita Retry-After/X-RateLimit-Reset."""
    with tempfile.TemporaryDirectory() as td:
        hd, bd = Path(td) / "h", Path(td) / "b"
        cfg = [f"url = {_cfg(url)}", f"user-agent = {_cfg(UA)}", f"dump-header = {_cfg(hd)}", f"output = {_cfg(bd)}",
               "location", "silent", "show-error", "max-time = 120", 'write-out = "%{http_code}"']
        cfg += [f"header = {_cfg(k + ': ' + v)}" for k, v in (headers or {}).items()]
        if data is not None:
            (Path(td) / "d").write_bytes(data)
            cfg += [f"data-binary = {_cfg('@' + str(Path(td) / 'd'))}"]
        for n in range(tentativas):
            r = subprocess.run(["curl", "-K", "-"], input="\n".join(cfg), capture_output=True, text=True)
            code = int(r.stdout.strip() or 0)
            body = bd.read_bytes() if bd.exists() else b""
            if 200 <= code < 300:
                h = {}
                for ln in (hd.read_text(errors="replace") if hd.exists() else "").splitlines():
                    k, _, v = ln.partition(":")
                    if v:
                        h[k.strip().lower()] = v.strip()
                return body, h
            if code not in (0, 429, 500, 502, 503, 504) or n == tentativas - 1:
                raise HTTPError(code, body or r.stderr.encode())
            h = hd.read_text(errors="replace").lower() if hd.exists() else ""
            m = re.search(r"^(?:retry-after|x-ratelimit-reset):\s*(\d+)", h, re.M)
            espera = min(float(m.group(1)) if m else 2 ** (n + 1), 60)
            print(f"  [rede] {code or r.stderr.strip()[:60]} em {url.split('?')[0][:60]}; nova tentativa em {espera:.0f} s", file=sys.stderr)
            time.sleep(espera)


def get_json(url: str, params: dict | None = None, headers: dict | None = None, cache_h: float = 24):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    if MOCK:
        return _mock_json(url)
    cf = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if cache_h and cf.exists() and time.time() - cf.stat().st_mtime < cache_h * 3600:
        return json.loads(cf.read_text())
    body, _ = _abre(url, headers)
    data = json.loads(body)
    if cache_h:
        CACHE.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(data))
    return data


def post_json(url: str, payload: dict, headers: dict | None = None):
    if MOCK:
        return _mock_json(url)
    body, _ = _abre(url, {"content-type": "application/json", **(headers or {})}, json.dumps(payload).encode())
    return json.loads(body)


def baixa(url: str, dst: Path, referer: str | None = None) -> Path:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if MOCK:
        m = Path(MOCK)
        mapa = json.loads((m / "downloads.json").read_text()) if (m / "downloads.json").exists() else {}
        src = Path(mapa[url]) if url in mapa else m / ("audio.mp3" if dst.suffix in (".mp3", ".wav", ".ogg") else "video.mp4")
        shutil.copy2(src, dst)
        return dst
    tmp = dst.with_suffix(dst.suffix + ".part")
    body, _ = _abre(url, {"Referer": referer} if referer else None)
    tmp.write_bytes(body)
    tmp.rename(dst)
    return dst
