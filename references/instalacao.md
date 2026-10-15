# Instalação e problemas comuns

## Requisitos

- Python 3.10+, ffmpeg, Node 18+ (`brew install ffmpeg node` no macOS).
- Whisper para os tempos das palavras: `pip install mlx-whisper` (Mac M1+) ou `pip install faster-whisper`.
- Conta **ElevenLabs** com uma voz (a sua clonada ou qualquer voz da biblioteca) e chave de API.
- Conta **HeyGen** com um avatar (Digital Twin ou Photo Avatar) e chave de API (ou login OAuth).

## Configurar

```bash
cp config.example.json config.json   # preencha canal, voz.voice_id e avatar.look_id
cp .env.example .env                 # cole ELEVENLABS_API_KEY e HEYGEN_API_KEY
python3 scripts/voice.py voices      # lista suas vozes → copie o voice_id
python3 scripts/avatar.py looks      # lista seus avatares → copie o look_id
python3 scripts/check_setup.py
```

`config.json` de um projeto (na pasta do projeto) sobrescreve só as chaves que tiver — útil para usar outra voz
ou outro avatar num vídeo específico.

## Problemas

- **HeyGen 401**: chave revogada ou token OAuth vencido. Gere outra chave ou rode `npx -y hyperframes@latest auth login`.
- **Look sem suporte a `avatar_v`**: deixe `avatar.engine` vazio (`""`) para usar o motor padrão do HeyGen (os motores aceitos aparecem em `avatar.py looks`).
- **Âncora não encontrada** no build: o texto de `inicio`/`em` precisa existir igual no roteiro (acentos e
  pontuação são ignorados). Use 1–3 palavras distintivas.
- **Legenda com palavra errada**: a legenda vem do roteiro; corrija o roteiro. Se a fala mudou, rode
  `voice.py --force meio`, `music.py mixar`, `transcribe.py` e `build.py` de novo.
- **Música alta**: aumente `musica.abaixo_da_voz_db` e rode `music.py mixar` + render.
- **Render lento ou travado**: feche outros apps pesados; o render usa o Chrome headless do HyperFrames.
- **Render para com "Disk capture may need … MB"**: o modo paralelo guarda todos os quadros no disco
  (~1 GB a cada 15 s de vídeo). Rode com `--workers 1`, que grava direto no MP4 (mais lento, quase sem disco).
