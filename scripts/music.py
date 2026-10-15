#!/usr/bin/env python3
"""Trilha (ElevenLabs Music) e mixagem com a voz em nível seguro.

Uso:
  python3 music.py gerar <projeto> "prompt da trilha"   compõe audio/musica.mp3 (instrumental, duração da voz)
  python3 music.py mixar <projeto>                       audio/voz.wav + audio/musica.mp3 → audio/mix.wav

Mixagem (sem mexer no timbre da voz):
  1. a música é ajustada para ficar `musica.abaixo_da_voz_db` (padrão 21 dB) abaixo da voz, medido em LUFS;
  2. ela ainda abaixa um pouco quando você fala (sidechain leve, 3:1);
  3. o conjunto recebe só ganho até `loudness_final_lufs` (padrão −14, o alvo de YouTube/TikTok/Reels).
Sem música (musica.usar=false ou sem musica.mp3) o mix é só a voz normalizada.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, duration, http, load_config, load_env, lufs, need, run  # noqa: E402


def main():
    load_env()
    if len(sys.argv) < 3:
        die(__doc__)
    cmd, proj = sys.argv[1], Path(sys.argv[2])
    need("ffmpeg")
    cfg = load_config(proj); a = proj / "audio"
    voz = a / "voz.wav"
    if not voz.exists():
        die("audio/voz.wav não existe — rode voice.py antes.")
    total = duration(voz)

    if cmd == "gerar":
        prompt = sys.argv[3] if len(sys.argv) > 3 else (
            "Calm modern cinematic underscore for a tech explainer narration: soft piano motif, warm string pads, "
            "gentle pulsing synth arpeggio, light ticking percussion. Steady low intensity, subtle lift near the end, "
            "soft resolving ending. Sparse mid-range so a voiceover sits clearly on top. Instrumental, no vocals.")
        k = os.environ.get("ELEVENLABS_API_KEY") or die("ELEVENLABS_API_KEY não definida.")
        body = {"prompt": prompt, "music_length_ms": int(min(600000, max(10000, (total + 2) * 1000))),
                "model_id": "music_v2", "force_instrumental": True}
        print("ElevenLabs Music: compondo…")
        audio = http("POST", "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192",
                     {"xi-api-key": k, "Accept": "audio/mpeg"}, body, raw=True, timeout=600)
        (a / "musica.mp3").write_bytes(audio)
        print(f"ok → {a / 'musica.mp3'} ({duration(a / 'musica.mp3'):.1f}s)")

    elif cmd == "mixar":
        alvo = float(cfg.get("loudness_final_lufs", -14))
        mus = a / "musica.mp3"
        lv = lufs(voz)
        pre = a / "premix.wav"
        if cfg.get("musica", {}).get("usar", True) and mus.exists():
            lm = lufs(mus)
            g = (lv - float(cfg["musica"].get("abaixo_da_voz_db", 21))) - lm
            fade = max(0.0, total - 3)
            fc = (f"[0]aformat=channel_layouts=stereo,asplit=2[v][sc];"
                  f"[1]atrim=0:{total},volume={g:.2f}dB,afade=t=in:d=1,afade=t=out:st={fade:.2f}:d=3[m];"
                  f"[m][sc]sidechaincompress=threshold=0.02:ratio=3:attack=30:release=500[md];"
                  f"[v][md]amix=inputs=2:normalize=0:duration=first[o]")
            run(["ffmpeg", "-v", "error", "-y", "-i", str(voz), "-i", str(mus), "-filter_complex", fc, "-map", "[o]", "-ar", "48000", str(pre)])
            print(f"voz {lv:.1f} LUFS · música original {lm:.1f} LUFS · ganho na música {g:+.1f} dB")
        else:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(voz), "-ac", "2", "-ar", "48000", str(pre)])
        g2 = alvo - lufs(pre)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f"volume={g2:.2f}dB,alimiter=limit=0.89:level=false", str(a / "mix.wav")])
        print(f"mix final: {lufs(a / 'mix.wav'):.1f} LUFS → {a / 'mix.wav'}")
    else:
        die(__doc__)


if __name__ == "__main__":
    main()
