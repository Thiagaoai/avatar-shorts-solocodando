#!/usr/bin/env python3
"""Confere o vídeo final antes de entregar.

Uso: python3 verify.py <projeto> <video.mp4>

Checa: 1080x1920, duração de imagem e áudio iguais à narração, sem tela preta, sem imagem congelada
(>2,5 s), sem silêncio longo (>1,2 s), loudness perto de −14 LUFS e se a fala cobre o roteiro inteiro
(transcreve o áudio do vídeo e compara com roteiro.md). Imprime OK/FALHA por item.
"""
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, load_config, lufs, read_script, run  # noqa: E402


def norm(s):
    return re.sub(r"[^\w]", "", s.lower())


def main():
    if len(sys.argv) < 3:
        die(__doc__)
    proj, video = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = load_config(proj)
    timing = json.loads((proj / "timing.json").read_text())
    ok = True

    def res(name, good, info):
        nonlocal ok
        ok &= good
        print(f"{'OK   ' if good else 'FALHA'} {name}: {info}")

    pr = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration", "-of", "json", str(video)]))
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    res("formato", (v["width"], v["height"]) == (1080, 1920), f'{v["width"]}x{v["height"]}')
    res("áudio", bool(au), "presente" if au else "SEM ÁUDIO")
    dv = float(v["duration"]); da = float(au[0]["duration"]) if au else 0
    res("duração", abs(dv - timing["total"]) < 0.3 and abs(dv - da) < 0.3, f"vídeo {dv:.2f}s · áudio {da:.2f}s · narração {timing['total']:.2f}s")

    log = subprocess.run(["ffmpeg", "-i", str(video), "-vf", "blackdetect=d=0.3:pix_th=0.08,freezedetect=n=0.002:d=2.5",
                          "-af", "silencedetect=n=-45dB:d=1.2", "-f", "null", "-"], capture_output=True, text=True).stderr
    blacks = re.findall(r"black_start:([\d.]+)", log)
    freezes = re.findall(r"freeze_start: ([\d.]+)", log)
    sil = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    sil = [x for x in sil if x < timing["total"] - 2.2]          # o respiro final é proposital
    res("tela preta", not blacks, "nenhuma" if not blacks else f"em {blacks}")
    res("imagem congelada", not freezes, "nenhuma" if not freezes else f"em {freezes}")
    res("silêncio longo", not sil, "nenhum" if not sil else f"em {sil}")
    L = lufs(video)
    alvo = float(cfg.get("loudness_final_lufs", -14))
    res("loudness", L is not None and abs(L - alvo) <= 1.5, f"{L} LUFS (alvo {alvo})")

    # fala completa
    tmp = Path(tempfile.mkdtemp())
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(tmp / "a.wav")])
    heard = ""
    try:
        run(["mlx_whisper", str(tmp / "a.wav"), "--model", "mlx-community/whisper-small-mlx", "--language", cfg["voz"].get("idioma", "pt"),
             "--output-format", "txt", "--output-dir", str(tmp)])
        heard = (tmp / "a.txt").read_text()
    except SystemExit:
        try:
            from faster_whisper import WhisperModel
            segs, _ = WhisperModel("small").transcribe(str(tmp / "a.wav"), language=cfg["voz"].get("idioma", "pt"))
            heard = " ".join(s.text for s in segs)
        except Exception:
            print("AVISO fala completa: sem whisper para checar")
    if heard:
        sc = read_script(proj)
        ref = [norm(w) for w in " ".join(sc.values()).split() if norm(w)]
        got = [norm(w) for w in heard.split() if norm(w)]
        ratio = difflib.SequenceMatcher(None, ref, got, autojunk=False).ratio()
        res("fala completa", ratio > 0.85, f"{ratio:.0%} do roteiro reconhecido na fala")
    print("\nRESULTADO:", "tudo certo" if ok else "corrigir os itens com FALHA")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
