---
name: avatar-shorts-solocodando
description: >
  Cria vídeos verticais (Shorts, Reels, TikTok) sobre qualquer assunto SEM a pessoa gravar nada: o avatar
  dela no HeyGen abre e fecha o vídeo falando com a voz clonada dela no ElevenLabs, e o meio é feito de
  cenas animadas (câmera em movimento, texto que mexe, legendas palavra por palavra) com trilha em nível
  seguro — tudo renderizado em MP4 pelo HyperFrames. Use sempre que o usuário pedir "um short / reels /
  tiktok sobre X", "vídeo com meu avatar", "vídeo sem aparecer / sem gravar", "usa minha voz do ElevenLabs",
  "faz outro vídeo do mesmo assunto", ou quiser produzir conteúdo em série para um canal, mesmo sem citar
  HeyGen, ElevenLabs ou HyperFrames.
---

# Avatar Shorts — vídeos com seu avatar, sem gravar

Formato fixo: **avatar em tela cheia no começo → cenas animadas no meio → avatar no fim → card do canal**.
A voz é a voz escolhida no ElevenLabs, sem alteração além da velocidade do config (padrão 1.25x).
O avatar fala exatamente o mesmo áudio (lipsync no HeyGen a partir do arquivo), então voz e boca batem.

Fale com o usuário no idioma dele (padrão português). Scripts em `scripts/` (rode com `python3 <skill>/scripts/...`).
Cada projeto é uma pasta (ex.: `projetos/2026-10-hermes/`) com `roteiro.md`, `cenas.json`, `assets/` e `audio/`.

## 0. Primeira vez

`python3 scripts/check_setup.py` — precisa de ffmpeg, Node, whisper, `config.json` (copiado de
`config.example.json`) e as chaves no `.env`. Se faltar voice_id ou look_id, liste e pergunte qual usar:
`python3 scripts/voice.py voices` e `python3 scripts/avatar.py looks`. Detalhes: `references/instalacao.md`.

## 1. Briefing (pergunte só o que faltar, numa pergunta só)

- **Assunto** e ângulo (o que torna esse vídeo diferente de outro sobre o mesmo tema).
- **Duração**: padrão ~1:45 para Shorts longos; 45–60 s rende mais retenção no TikTok/Reels.
- **Estilo**: `moderno` (padrão — aurora em gradiente, vidro, visual de IA), `caderno` (papel claro, câmera
  viajando num mapa) ou `cinematico` (escuro, grade 3D, glitch). Mostre que existem; não force escolha.
- **CTA final** (padrão: `canal.cta` do config + pergunta para comentários).

## 2. Pesquisa e roteiro

Confirme todo fato (preço, número, data, nome de produto, comando) numa fonte oficial antes de escrever.
Escreva `<projeto>/roteiro.md` com três seções — `## INTRO`, `## MEIO`, `## FINAL` — seguindo
`references/roteiro.md` (gancho, ritmo, palavras por segundo, números por extenso). A INTRO e o FINAL viram
falas do avatar; o MEIO vira as cenas. Mostre o roteiro ao usuário antes de gastar créditos.

## 3. Voz → 4. Avatar (comece cedo, é o passo mais lento) → 5. Música

```bash
python3 scripts/voice.py <projeto>                 # ElevenLabs → audio/voz.wav + timing.json
python3 scripts/avatar.py criar <projeto>          # HeyGen: lipsync na intro e no final
python3 scripts/avatar.py esperar <projeto>        # rode em segundo plano (8–12 min)
python3 scripts/music.py gerar <projeto> "prompt"  # trilha instrumental (ou coloque audio/musica.mp3)
python3 scripts/music.py mixar <projeto>           # música 21 dB abaixo da voz, final −14 LUFS
python3 scripts/transcribe.py <projeto>            # tempo de cada palavra → words.json
```

A música fica **bem abaixo da voz** de propósito (`musica.abaixo_da_voz_db`, padrão 21). Se o usuário pedir
mais música, diminua esse número de 2 em 2 — nunca menos de 15. Prompt da trilha: instrumental, sem vocais,
"leaves room for a voiceover".

Para refazer só um trecho da fala: `voice.py <projeto> --force meio` (a intro/final exigem refazer o avatar).

## 6. Cenas

Enquanto o avatar renderiza, escreva `<projeto>/cenas.json` (formato completo em `references/cenas.md`;
exemplo real em `examples/hermes-agent/`). Princípios:
- Uma cena por ideia do MEIO; cada cena começa numa **frase exata do roteiro** (`"inicio"`).
- Cada elemento aparece **quando é falado** (`"em": "palavra"`), e o que aparece na tela reforça a fala
  com substantivos concretos, números, comandos, logos e prints reais (salve imagens em `assets/`).
- Varie os tipos (passos, busca, lista, terminal, opções, número grande, imagem, frase) e não repita
  o mesmo tipo em sequência. Overlays rápidos sobre o avatar (balão, números, botão inscrever) seguram o gancho.

## 7. Montar, conferir o enquadramento, renderizar

```bash
python3 scripts/build.py <projeto> --guias          # com as guias da zona segura
cd <projeto> && npx -y hyperframes@0.8.159 check     # precisa terminar em "Check passed"
npx -y hyperframes@0.8.159 snapshot --at <meio de cada cena, início/fim do avatar> --describe false -o snaps --no-end
```
Olhe as fotos: nada pode sair da caixa verde (conteúdo) nem da azul (legenda); nada cortado, sobreposto
ou ilegível; cada cena mostra o que está sendo dito. Ajuste `cenas.json` (texto mais curto, menos itens) e
monte de novo até ficar limpo. Regras em `references/zona-segura.md`. Depois:

```bash
python3 scripts/build.py <projeto>                                   # sem guias
npx -y hyperframes@0.8.159 render --quality delivery --output <Nome>.mp4
python3 scripts/verify.py <projeto> <Nome>.mp4                       # tudo precisa dar OK
```

## 8. Entrega e publicação

Envie o MP4, diga a duração, o que cada parte mostra e quanto foi gasto (créditos HeyGen, caracteres
ElevenLabs). Escreva `<projeto>/publicacao.md` com título e legenda nativa para YouTube, Instagram, TikTok
e X (`references/publicacao.md`). Lembre de marcar **conteúdo gerado por IA** em toda plataforma (avatar e
voz são sintéticos). Só publique ou preencha formulários de upload se o usuário pedir, e confirme antes de
clicar em publicar.

## Modo rascunho

"Rascunho", "teste", "sem gastar" → faça roteiro, `cenas.json` e um build com áudio de teste (por
exemplo a voz do sistema via `say`, salva como audio/raw_*.mp3) para revisar as cenas; liste os passos pagos que faltam.
