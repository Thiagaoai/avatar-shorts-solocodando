"""Funções compartilhadas pelos scripts do avatar-shorts-solocodando.

Só usa a biblioteca padrão do Python (3.10+). Ferramentas externas: ffmpeg/ffprobe, Node (npx), whisper.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


# ---------------- configuração ----------------
def load_env():
    """Carrega .env da pasta da skill (sem sobrescrever variáveis já definidas)."""
    env = SKILL_DIR / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_config(project=None):
    """config.json da skill, com sobrescritas opcionais em <projeto>/config.json."""
    base = SKILL_DIR / "config.json"
    if not base.exists():
        die("config.json não existe. Copie config.example.json para config.json e preencha voice_id e look_id.")
    cfg = json.loads(base.read_text())
    if project:
        local = Path(project) / "config.json"
        if local.exists():
            deep_update(cfg, json.loads(local.read_text()))
    return cfg


def deep_update(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_update(a[k], v)
        else:
            a[k] = v


def die(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------- HTTP ----------------
def http(method, url, headers=None, body=None, raw=False, timeout=180):
    data = None
    headers = dict(headers or {})
    if body is not None and not isinstance(body, (bytes, bytearray)):
        data = json.dumps(body).encode()
        headers.setdefault("Content-Type", "application/json")
    elif body is not None:
        data = body
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = r.read()
            return out if raw else json.loads(out or b"{}")
    except urllib.error.HTTPError as e:
        die(f"{method} {url} → HTTP {e.code}: {e.read().decode(errors='replace')[:400]}")


def multipart(url, headers, field, path, mime):
    boundary = "----avatarshorts" + str(int(time.time() * 1000))
    data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{Path(path).name}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n").encode() + Path(path).read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    h = dict(headers)
    h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    return http("POST", url, h, data)


# ---------------- áudio / vídeo ----------------
def need(binary):
    if not shutil.which(binary):
        die(f"'{binary}' não encontrado no PATH.")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        die(f"comando falhou: {' '.join(map(str, cmd))[:200]}\n{r.stderr[-800:]}")
    return r.stdout + r.stderr


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip().splitlines()[0])


def lufs(path):
    out = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else None


# ---------------- roteiro ----------------
def read_script(project):
    """Lê <projeto>/roteiro.md e devolve {'intro': str, 'meio': str, 'final': str}.

    Formato: três seções começando por '## INTRO', '## MEIO' e '## FINAL' (o resto do título é livre).
    """
    p = Path(project) / "roteiro.md"
    if not p.exists():
        die(f"{p} não existe.")
    parts, cur = {}, None
    for line in p.read_text().splitlines():
        m = re.match(r"^##\s*(?:\d+[.)]\s*)?(INTRO|MEIO|FINAL)\b", line.strip(), re.I)
        if m:
            cur = m.group(1).lower(); parts[cur] = []
            continue
        if line.startswith("#"):
            continue
        if cur:
            parts[cur].append(line)
    out = {k: "\n".join(v).strip() for k, v in parts.items()}
    for k in ("intro", "meio", "final"):
        if not out.get(k):
            die(f"roteiro.md sem a seção '## {k.upper()}'.")
    return out
