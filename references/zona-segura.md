# Zona segura e enquadramento

Tela 1080×1920. Nos apps, a interface cobre partes do vídeo:

- topo (~200 px): barra de status, abas e título;
- direita (x > 940, y 700–1520): botões de curtir, comentar e compartilhar;
- base (y > 1500): nome do canal, descrição, música e barra de progresso.

Por isso o motor coloca:

- **conteúdo** em x 100–930, y 230–1180 (caixa verde com `--guias`);
- **legenda** em x 100–930, y 1240–1400 (caixa azul).

Ao revisar as fotos com guias, corrija:

- elemento que encosta ou sai da caixa verde → texto mais curto ou menos itens (não diminua a fonte abaixo do legível);
- carimbo cortado → texto de no máximo 2–3 palavras (carimbos laterais quebram em 2 linhas);
- título com mais de 2 linhas → reescreva mais curto (até ~28 caracteres por linha a 80 px);
- legenda em 3 linhas → frases mais curtas no roteiro;
- balão sobre o avatar cobrindo a boca → os overlays ficam em y 1000–1200, sobre o peito; mantenha o texto em uma linha.

Os avisos `canvas_overflow`/`panel_out_of_canvas` do `check` no estilo **caderno** são esperados: as outras cenas
ficam fora da tela no mapa até a câmera chegar nelas. O que vale é a foto de cada momento.
