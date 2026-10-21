# reel-motion — pacote DaVinci e lições do Resolve

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

Nomes no pacote: todo arquivo leva o sufixo do reel (`voz__r01.wav`, `el/painel_0__r01h.mov`, `capa__r01.mov`), porque o
Resolve junta arquivos de mesmo nome entre pacotes (foi o "áudio de outro vídeo" do 03). Pacote antigo sem sufixo é
renomeado na próxima etapa `davinci`, sem renderizar de novo. Regras gerais do Resolve (nomes, FPS, .drt,
GlobalIn, mesclagem, bins, cores): `client-router/references/regras/davinci.md`.

## Pacote para o DaVinci (14/10/2026)
- `reel.py PROJ rNN davinci` → `07_davinci/<nome>/timeline.fcpxml` + mídia. Para reel com correção pedida: o editor
  importa (File > Import > Timeline), corrige o erro bobo e exporta por lá; nada de render final aqui.
- Tudo fragmentado: bruto em takes com alça, voz por take, cada painel/etiqueta/etapa/título/bloco de legenda/burn/SFX
  em arquivo e clipe próprios. `davinci painel_2` re-renderiza só esse elemento (Reel.tsx: props `layer` + `el`).
- Custo no 10 (41 s): câmera 121 s, fundo 38 s, legenda 45 s, 17 elementos ~3 min; 110 clipes, 2,6 GB.
- Não abrir o DaVinci para testar (pedido do editor).
- `"formato": "so_legenda"` no reel.json: ela em tela cheia com gancho, títulos e legenda; sem painéis, tela dividida
  e burns; SFX só nos textos (o original fica em sfx_com_paineis.json). Pedido da Priscilla para variar formato (06, 14/10/2026).
- `"extras": [{"arq": "extras/x.mov", "s": 0, "nome": "…"}]`: elemento feito fora do Remotion (ex.: cartão com logo de
  marca no gancho), entra numa faixa própria do pacote DaVinci junto com o PNG.

- `"grosso": true` no reel.json (aula longa, João 21/10/2026: "a parte das aulas deveria ser algo simples, mas com legenda", "nem tracking deveria ter", "o Resolve consegue fazer isso sozinho"): pacote só com bruto cortado nos segs, voz, trilha e `legenda.srt`; sem painel, título, SFX, burn, rastreio, movimento nem render no Remotion; timeline no fps da fonte (sem cópia 29,97). ~3 s por aula. **Aula/vídeo longo vai direto assim: nada de prévia no Remotion.**
