#!/usr/bin/env python3
"""Narração: roteiro.md → voz no ElevenLabs (sem alterar a voz) → velocidade → voz.wav + timing.json.

Uso:
  python3 voice.py <projeto>                 gera só as partes que ainda não existem
  python3 voice.py <projeto> --force meio    regenera uma parte (intro|meio|final|todas)
  python3 voice.py voices [--busca texto]    lista as vozes da sua conta ElevenLabs

Saídas em <projeto>/audio/: raw_intro.mp3, raw_meio.mp3, raw_final.mp3 (originais do ElevenLabs),
intro.wav/meio.wav/final.wav (na velocidade do config), voz.wav (tudo junto) e <projeto>/timing.json.
A velocidade é aplicada com atempo (mantém o tom da voz); nenhuma outra alteração é feita.
"""
import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, duration, http, load_config, load_env, need, read_script, run  # noqa: E402

API = "https://api.elevenlabs.io/v1"
GAP_AFTER_INTRO = 0.25
GAP_BEFORE_FINAL = 0.35
TAIL = 1.8           # respiro no fim para o card final


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        die("ELEVENLABS_API_KEY não definida (coloque no .env da skill).")
    return k


def list_voices(search=""):
    q = "?search=" + urllib.parse.quote(search) if search else ""
    d = http("GET", f"https://api.elevenlabs.io/v2/voices{q}", {"xi-api-key": key()})
    for v in d.get("voices", []):
        print(f'{v["voice_id"]}  [{v.get("category","")}]  {v["name"]}')


def tts(text, out, cfg):
    v = cfg["voz"]
    body = {"text": text, "model_id": v.get("model_id", "eleven_multilingual_v2"),
            "language_code": v.get("idioma", "pt"),
            "voice_settings": {"stability": v.get("stability", 0.5), "similarity_boost": v.get("similarity_boost", 0.75)}}
    if body["model_id"].startswith("eleven_multilingual_v2"):
        body.pop("language_code")          # v2 detecta o idioma sozinho
    audio = http("POST", f"{API}/text-to-speech/{v['voice_id']}?output_format=mp3_44100_192",
                 {"xi-api-key": key(), "Accept": "audio/mpeg"}, body, raw=True)
    Path(out).write_bytes(audio)


def main():
    load_env()
    if len(sys.argv) > 1 and sys.argv[1] == "voices":
        return list_voices(sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--busca" else "")
    if len(sys.argv) < 2:
        die(__doc__)
    proj = Path(sys.argv[1]); force = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--force" else None
    need("ffmpeg")
    cfg = load_config(proj)
    if "COLE_AQUI" in cfg["voz"]["voice_id"]:
        die("preencha voz.voice_id no config.json (liste com: python3 voice.py voices).")
    parts = read_script(proj)
    a = proj / "audio"; a.mkdir(parents=True, exist_ok=True)
    speed = float(cfg["voz"].get("velocidade", 1.0))

    for name in ("intro", "meio", "final"):
        raw = a / f"raw_{name}.mp3"
        if force in (name, "todas") or not raw.exists():
            print(f"ElevenLabs: gerando {name} ({len(parts[name])} caracteres)…")
            tts(parts[name], raw, cfg)
        filt = f"atempo={speed}" if abs(speed - 1) > 1e-3 else "anull"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", filt, "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(a / f"{name}.wav")])
        # mp3 do trecho para o lipsync do avatar
        run(["ffmpeg", "-v", "error", "-y", "-i", str(a / f"{name}.wav"), "-c:a", "libmp3lame", "-b:a", "192k", str(a / f"{name}.mp3")])

    d = {n: duration(a / f"{n}.wav") for n in ("intro", "meio", "final")}
    sil = lambda t: ["-f", "lavfi", "-t", str(t), "-i", "anullsrc=r=48000:cl=mono"]
    run(["ffmpeg", "-v", "error", "-y", "-i", str(a / "intro.wav"), *sil(GAP_AFTER_INTRO), "-i", str(a / "meio.wav"),
         *sil(GAP_BEFORE_FINAL), "-i", str(a / "final.wav"), *sil(TAIL),
         "-filter_complex", "[0][1][2][3][4][5]concat=n=6:v=0:a=1[o]", "-map", "[o]", "-ar", "48000", str(a / "voz.wav")])
    t_meio = d["intro"] + GAP_AFTER_INTRO
    t_final = t_meio + d["meio"] + GAP_BEFORE_FINAL
    timing = {"velocidade": speed,
              "intro": [0.0, round(d["intro"], 3)],
              "meio": [round(t_meio, 3), round(t_meio + d["meio"], 3)],
              "final": [round(t_final, 3), round(t_final + d["final"], 3)],
              "total": round(duration(a / "voz.wav"), 3)}
    (proj / "timing.json").write_text(json.dumps(timing, indent=2))
    print(json.dumps(timing))


if __name__ == "__main__":
    main()
