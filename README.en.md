# avatar-shorts-solocodando

**Short videos with your avatar and your voice — no filming, no showing up on camera.**
[Versão em português](README.md)

A [Claude Code](https://claude.com/claude-code) skill that turns a topic into a ready-to-post Short / Reel / TikTok:

1. Claude researches and writes the script;
2. **ElevenLabs** narrates it with your cloned voice (or any voice);
3. **HeyGen** renders your avatar lip-syncing that same audio at the start and the end;
4. the middle becomes **animated scenes** — moving camera, text that appears exactly when it is spoken,
   word-by-word captions, a cinematic music bed at a safe level;
5. **HyperFrames** renders a 1080×1920 MP4, and a checker verifies framing, audio and speech.

Requirements: Claude Code, an ElevenLabs API key (voice + music), a HeyGen API key and avatar, ffmpeg, Node 18+,
Python 3.10+ and whisper (`mlx-whisper` on Apple Silicon or `faster-whisper`). Rendering runs locally for free.
Typical cost per ~1:45 video: ~15 HeyGen credits and ~2k ElevenLabs characters plus one music track.

## Install

```bash
git clone https://github.com/Thiagaoai/avatar-shorts-solocodando.git ~/.claude/skills/avatar-shorts-solocodando
cd ~/.claude/skills/avatar-shorts-solocodando
cp config.example.json config.json && cp .env.example .env   # add your keys, voice_id and look_id
python3 scripts/voice.py voices && python3 scripts/avatar.py looks
python3 scripts/check_setup.py
```

## Use

Ask Claude Code: *"make a 90-second short about <topic> with my avatar, modern style"*. It writes the script,
asks you to approve it before spending credits, then produces and checks the video and writes per-platform captions.
The skill instructions are in Portuguese; set `voz.idioma` in `config.json` (e.g. `en`) to produce videos in English.

Styles: `moderno` (default, gradient aurora + glass cards), `caderno` (light notebook, camera travels a map),
`cinematico` (dark 3D grid, whip cuts). Always label avatar/voice content as AI-generated when posting.

MIT license · made by [@thiagaoai](https://github.com/Thiagaoai) · Solocodando channel.
