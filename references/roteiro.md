# Como escrever o roteiro

`roteiro.md` tem três seções. O título de cada uma pode ter número ou comentário, mas precisa começar com a palavra:

```markdown
# Título do vídeo (livre)

## 1. INTRO (avatar)
Gancho em 2–3 frases. Quem assiste decide aqui se fica.

## 2. MEIO
O conteúdo. Vira as cenas animadas.

## 3. FINAL (avatar)
Pergunta para os comentários + chamada para se inscrever.
```

## Tamanho

A voz é acelerada pelo `voz.velocidade` do config (padrão 1.25x). Com 1.25x, uma voz em português fala ~3 palavras/s:

| Duração alvo | Palavras no total | INTRO | FINAL |
|---|---|---|---|
| 45 s | ~130 | 25–30 | 20–25 |
| 60 s | ~175 | 30 | 25 |
| 1:45 | ~320 | 30–40 | 25–30 |

Mantenha a INTRO e o FINAL curtos: são os trechos do avatar (créditos do HeyGen) e os mais assistidos.

## Gancho (INTRO)

Funciona: contraste ("O seu ChatGPT esquece tudo… esse aqui não"), número forte ("250 mil estrelas no GitHub"),
promessa contada ("três coisas que eu nunca vi juntas"), pergunta direta. Termine a INTRO puxando para o meio.

## Meio

- Uma ideia por parágrafo; cada parágrafo vira uma cena. Comece parágrafos com marcadores falados que viram
  âncoras fáceis: "Número um:", "E tem mais.", "Para instalar…".
- Prefira substantivos que a tela consegue mostrar (nomes de apps, números, comandos, antes/depois).
- Escreva números e siglas como devem ser **falados**: "cinco dólares", "duzentas e cinquenta mil",
  "dois ponto zero". A legenda mostra exatamente o texto do roteiro.
- Nome estrangeiro que a voz pronuncia mal: escreva do jeito que deve soar só se o usuário pedir, porque a
  legenda vai mostrar a mesma grafia.

## Final

Uma pergunta que gere comentário (sim/não, qual você usaria) + CTA do canal (`canal.cta`). Sem nova informação.

## Fatos

Todo número, preço, data, comando de instalação ou recurso precisa estar confirmado em fonte oficial
(site, repositório, documentação). Na dúvida, tire do roteiro.
