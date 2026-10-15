# cenas.json — formato

```json
{
  "estilo": "moderno",
  "intro":  [ overlays sobre o avatar do começo ],
  "cenas":  [ cenas do meio, em ordem ],
  "final":  [ overlays sobre o avatar do fim ],
  "card_final": { "titulo": "Solo*codando*", "subtitulo": "IA na prática", "pergunta": "Comenta: SIM ou NÃO?" }
}
```

Exemplo completo e real: `examples/hermes-agent/cenas.json`.

## Âncoras de tempo

- `"inicio"` (em cada cena, menos a primeira): frase **exata** do roteiro onde a cena começa. A cena entra
  ~0,35 s antes e vai até a próxima cena. A primeira cena começa quando o avatar sai.
- `"em"`: palavra ou frase do roteiro em que o elemento aparece. Procura a primeira ocorrência **a partir
  do início da cena**. Aceita ajuste: `"zero+0.3"`, `"salva-0.2"`. Sem `em`, os elementos entram escalonados.
- Acentos, maiúsculas e pontuação são ignorados na busca. Use 1–3 palavras que só aparecem ali.
- O build avisa `âncora não encontrada` — corrija antes de renderizar.

## Texto

`*palavra*` no título destaca com a cor de acento do estilo. Textos curtos: título até ~28 caracteres por
linha (2 linhas no máximo), carimbo até 3 palavras, cartão/linha até ~32 caracteres.

## Overlays sobre o avatar (`intro` e `final`)

Aparecem um de cada vez, sobre o peito (y 1000–1200); cada um some quando o próximo entra.

| tipo | campos |
|---|---|
| `balao` | `texto`, `em`, `riscar_em` (risca o texto — bom para "o concorrente esquece"), `destaque` (fundo de destaque) |
| `numeros` | `valores` (ex. `["1","2","3"]`), `em` — entram um a um |
| `inscrever` | `texto` (padrão "Inscreva-se"), `em` — botão + cursor clicando |

## Tipos de cena

Campos comuns opcionais: `numero` ("01"), `titulo`, `titulo_em`.

| tipo | para quê | campos |
|---|---|---|
| `abertura` | apresentar o produto/assunto | `icone` (img quadrada), `imagem` (logo/banner largo), `kicker`, `carimbos` [até 3 `{texto, em}`], `nota` `{texto, em}` |
| `passos` | processo em 3 etapas | `passos` [3 `{texto, em}`], `nota` `{titulo, linhas[≤4], em}`, `carimbos` [até 2 `{texto, em, cor}`] (laterais) |
| `busca` | memória, pesquisa, histórico | `busca` `{texto, em}` (digitado), `cartoes` [≤3 `{texto, meta, em, destaque_em}`], `chips` [`{texto, em, cor}`] |
| `comparar` | antes × depois, A × B | `esquerda`/`direita` `{icone (emoji), rotulo, em, apagar_em}`, `chips`, `audio` `{em, linhas[≤2 {texto, em}]}` (nota de voz) |
| `lista` | "e tem mais", recursos | `titulo`, `itens` [≤4 `{icone, titulo, sub, em, chips[≤4 {texto, em}]}`] |
| `terminal` | comando, instalação, código | `comando` (digitado), `em`, `progresso` (barra), `saida` [≤3 `{texto, em}`], `carimbo` `{texto, em, cor}` |
| `opcoes` | escolher entre alternativas | `opcoes` [≤4 `{texto, em}`] (acende a falada), `carimbo` |
| `numero_grande` | um número que impressiona | `valor` ("250 mil", "40+", "US$ 5" — conta até o número), `rotulo`, `sub`, `em`, `contar` |
| `imagem` | print real, foto, gráfico | `arquivo` (em `assets/`), `em`, `legenda` — com zoom lento |
| `frase` | frase de impacto | `linhas` [≤4 `{texto, em}`] — usa `*destaque*` |

`cor` dos carimbos: `"1"` acento, `"2"` secundária, `"3"` verde. `cor` dos chips: qualquer cor CSS (ex. cor da marca).

## Ritmo

- 6 a 10 cenas num vídeo de 1:45; 4 a 6 num de 45–60 s.
- Cena com menos de 4 s fica corrida; mais de 15 s pede mais elementos entrando ao longo da fala.
- Alterne tipos; termine o meio com algo prático (como instalar, onde achar, preço).
- Prints reais (site, repositório, app) aumentam a confiança: capture em 1080 px de largura e use `imagem`.
