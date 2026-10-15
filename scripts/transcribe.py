#!/usr/bin/env python3
"""Tempo de cada palavra da narração (para sincronizar cenas e legendas).

Uso: python3 transcribe.py <projeto> [--modelo small]
Lê audio/voz.wav e grava <projeto>/words.json = [{"w": "palavra", "s": início, "e": fim}, ...].

Usa o primeiro disponível: mlx_whisper (Mac Apple Silicon), faster-whisper ou openai-whisper.
A transcrição só serve para os TEMPOS: o texto das legendas vem do roteiro (ver build.py), então
erros de grafia do whisper ("Noose" em vez de "Nous") não aparecem no vídeo.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, load_config, need, run  # noqa: E402


def main():
    if len(sys.argv) < 2:
        die(__doc__)
    proj = Path(sys.argv[1])
    size = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--modelo" else "small"
    lang = load_config(proj)["voz"].get("idioma", "pt")
    need("ffmpeg")
    tmp = Path(tempfile.mkdtemp())
    wav = tmp / "voz16k.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "audio" / "voz.wav"), "-ac", "1", "-ar", "16000", str(wav)])
    words = []
    if shutil.which("mlx_whisper"):
        run(["mlx_whisper", str(wav), "--model", f"mlx-community/whisper-{size}-mlx", "--language", lang,
             "--word-timestamps", "True", "--output-format", "json", "--output-dir", str(tmp)])
        d = json.loads((tmp / "voz16k.json").read_text())
        words = [{"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)} for s in d["segments"] for w in s["words"]]
    else:
        try:
            from faster_whisper import WhisperModel
            segs, _ = WhisperModel(size).transcribe(str(wav), language=lang, word_timestamps=True)
            words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
        except ImportError:
            try:
                import whisper
                d = whisper.load_model(size).transcribe(str(wav), language=lang, word_timestamps=True)
                words = [{"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)} for s in d["segments"] for w in s["words"]]
            except ImportError:
                die("instale um whisper: `pip install mlx-whisper` (Mac M1+), `pip install faster-whisper` ou `pip install openai-whisper`.")
    (proj / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=0))
    print(f"{len(words)} palavras → {proj / 'words.json'}")


if __name__ == "__main__":
    main()
