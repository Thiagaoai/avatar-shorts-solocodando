#!/usr/bin/env python3
"""Confere se está tudo pronto para produzir: programas, chaves, voz e avatar.

Uso: python3 check_setup.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import SKILL_DIR, load_env  # noqa: E402


def main():
    load_env()
    ok = True

    def line(good, name, info=""):
        nonlocal ok
        ok &= good
        print(f"{'✓' if good else '✗'} {name}{(' — ' + info) if info else ''}")

    line(sys.version_info >= (3, 10), "Python 3.10+", sys.version.split()[0])
    for b in ("ffmpeg", "ffprobe", "node", "npx"):
        line(bool(shutil.which(b)), b, "" if shutil.which(b) else "instale (macOS: brew install ffmpeg node)")
    wh = shutil.which("mlx_whisper")
    if not wh:
        try:
            import faster_whisper  # noqa: F401
            wh = "faster-whisper"
        except ImportError:
            try:
                import whisper  # noqa: F401
                wh = "openai-whisper"
            except ImportError:
                pass
    line(bool(wh), "whisper", wh or "pip install mlx-whisper (Mac M1+) ou faster-whisper")

    cfgp = SKILL_DIR / "config.json"
    line(cfgp.exists(), "config.json", "" if cfgp.exists() else "cp config.example.json config.json")
    cfg = json.loads(cfgp.read_text()) if cfgp.exists() else {}
    vid = cfg.get("voz", {}).get("voice_id", "")
    look = cfg.get("avatar", {}).get("look_id", "")
    line(bool(vid) and "COLE_AQUI" not in vid, "voz.voice_id", vid if "COLE_AQUI" not in vid else "liste com: python3 scripts/voice.py voices")
    if cfg.get("avatar", {}).get("usar") != "nenhum":
        line(bool(look) and "COLE_AQUI" not in look, "avatar.look_id", look if "COLE_AQUI" not in look else "liste com: python3 scripts/avatar.py looks")

    line(bool(os.environ.get("ELEVENLABS_API_KEY")), "ELEVENLABS_API_KEY", "no .env da skill")
    has_hg = bool(os.environ.get("HEYGEN_API_KEY")) or (Path.home() / ".heygen/credentials").exists()
    line(has_hg, "HeyGen", "HEYGEN_API_KEY no .env ou login: npx -y hyperframes@latest auth login")
    if has_hg and os.environ.get("ELEVENLABS_API_KEY") is not None:
        r = subprocess.run([sys.executable, str(SKILL_DIR / "scripts/avatar.py"), "whoami"], capture_output=True, text=True)
        line(r.returncode == 0, "HeyGen responde", (r.stdout or r.stderr).strip()[:160])
    print("\nPronto para produzir." if ok else "\nResolva os itens com ✗ antes de começar.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
