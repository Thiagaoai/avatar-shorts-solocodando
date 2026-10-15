# avatar-shorts-solocodando

**Vídeos curtos com o seu avatar e a sua voz, sem gravar nada e sem aparecer.**
[English version](README.en.md)

Uma skill para o [Claude Code](https://claude.com/claude-code) que transforma um assunto num Short/Reels/TikTok
pronto para postar:

1. o Claude pesquisa e escreve o roteiro;
2. o **ElevenLabs** narra com a sua voz clonada (ou qualquer outra voz);
3. o **HeyGen** gera o seu avatar falando esse mesmo áudio, com lipsync, no começo e no fim;
4. o meio vira **cenas animadas**: câmera em movimento, texto que aparece na hora em que é falado, legendas
   palavra por palavra, trilha cinematográfica em volume seguro;
5. o **HyperFrames** renderiza o MP4 1080×1920, e um verificador confere enquadramento, áudio e fala.

Feita para quem quer produzir conteúdo todo dia, mas não gosta (ou não tem tempo) de gravar e aparecer.

## O que você precisa

| | Para quê | Custo aproximado por vídeo de ~1:45 |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | conduz tudo | seu plano |
| [ElevenLabs](https://elevenlabs.io) (plano Creator ou maior) | voz + trilha | ~2 mil caracteres + 1 trilha |
| [HeyGen](https://heygen.com) (plano com API) | avatar | ~15 créditos (só 2 trechos curtos) |
| ffmpeg, Node 18+, Python 3.10+, whisper | edição local | grátis |

O render roda no seu computador (grátis).

## Instalar

```bash
git clone https://github.com/Thiagaoai/avatar-shorts-solocodando.git ~/.claude/skills/avatar-shorts-solocodando
cd ~/.claude/skills/avatar-shorts-solocodando
cp config.example.json config.json && cp .env.example .env
```

1. No `.env`, cole a `ELEVENLABS_API_KEY` e a `HEYGEN_API_KEY`.
2. Ache seus IDs e cole no `config.json`:
   ```bash
   python3 scripts/voice.py voices    # voice_id da sua voz
   python3 scripts/avatar.py looks    # look_id do seu avatar
   ```
3. Preencha `canal` (nome, slogan e CTA) e confira: `python3 scripts/check_setup.py`

Ainda não tem avatar ou voz clonada? No HeyGen, crie um **Digital Twin** (vídeo curto seu) ou um **Photo Avatar**
(uma foto). No ElevenLabs, use **Voice Clone** com 1–3 minutos de áudio seu, ou escolha uma voz da biblioteca.

## Usar

Abra o Claude Code numa pasta de trabalho e peça:

> faz um short de 1 minuto e meio sobre o lançamento do Gemini 4, com meu avatar, estilo moderno

O Claude segue a skill: pergunta o que faltar, escreve o roteiro e mostra para você aprovar antes de gastar
créditos. Depois gera voz, avatar, música e cenas, confere o enquadramento e entrega o MP4 com as legendas
prontas para cada rede.

Também dá para rodar passo a passo (veja o [SKILL.md](SKILL.md)):

```bash
python3 scripts/voice.py projetos/meu-video
python3 scripts/avatar.py criar projetos/meu-video && python3 scripts/avatar.py esperar projetos/meu-video
python3 scripts/music.py gerar projetos/meu-video "calm cinematic underscore, piano and strings"
python3 scripts/music.py mixar projetos/meu-video
python3 scripts/transcribe.py projetos/meu-video
python3 scripts/build.py projetos/meu-video
cd projetos/meu-video && npx -y hyperframes@0.8.159 render --quality delivery --output video.mp4
```

## Estilos

| `moderno` (padrão) | `caderno` | `cinematico` |
|---|---|---|
| preto profundo, aurora em gradiente, rede neural, cartões de vidro, transições com foco | papel claro, cartões com borda preta, câmera viajando num mapa | escuro, grade 3D voando, dourado e ciano, cortes em chicote com glitch |

## Estrutura

```
SKILL.md              o passo a passo que o Claude segue
config.example.json   canal, voz, avatar, música, estilo
scripts/              voice · avatar · music · transcribe · build · verify · check_setup
styles/               base.css + um CSS por estilo
references/           roteiro, tipos de cena, zona segura, publicação, instalação
examples/hermes-agent roteiro.md + cenas.json de um vídeo real
```

## Boas práticas

- Marque **conteúdo gerado por IA** ao publicar: o avatar e a voz são sintéticos.
- Use só a sua voz e o seu avatar, ou os de quem autorizou.
- Confira os fatos do roteiro em fonte oficial antes de publicar.

## Licença

MIT. Feito por [@thiagaoai](https://github.com/Thiagaoai) · canal **Solocodando**.
