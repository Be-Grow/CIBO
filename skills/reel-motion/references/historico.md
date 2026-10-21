# reel-motion — histórico (por que cada regra existe)

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

# reel-motion — motor genérico de reel com motion

Nasceu do motor aprovado da Priscilla Daher (13/10/2026). O editor pediu: **um motor generalista que
aceita configurações, não um motor por cliente**, e **uma biblioteca de componentes reutilizáveis
(princípio do React), não animação feita do zero a cada reel**.

## Padrão de edição do CIBO: o fluxo da Andreia (editor, 20/10/2026)

"Eu gostei muito do que foi feito lá e gostaria que fosse o padrão de edição da CIBO." Todo job de fala sem skill própria
segue esta receita; clientes com skill própria mantêm identidade e regras deles, mas entregam pelo mesmo pacote DaVinci.
Referência viva: `andreia/demandaVideoEstiloPriscilla/` (brief, review_2026-10-20.md, 8 timelines).

Teste de ponta a ponta (20/10/2026, `andreia/…/04_work/t01`, 15 s, painel `hub`, Resolve aberto): `fila_davinci.py` levou
3 min (pacote 0,6 GB, 26 clipes, 2 camadas de Fusion, `qa_resolve` OK). Achou e corrigiu: fundo do painel e etiquetas caíam
no bin `01 BRUTO`, e a reimportação do .drt deixava SFX órfãos duplicados ("X.wav import") — o `resolve_projeto.py organiza`
agora reclassifica e apaga só duplicado de mesmo arquivo que nenhuma timeline usa. Atalhos do teste: o `mix` remonta a voz do
`src_48k.wav` (copie/ligue o da fonte); `qa_paineis`, `capa_pausas` e `sfx_tema` rodam com `~/.venvs/audiotools/bin/python`.

- Sombra/escurecimento no tema: antes ficavam no marrom da Priscilla em todo cliente (17/10/2026).
- Partes de painel separadas no pacote DaVinci e SEM_RENDER: pedido do editor, 17/10/2026.
- Revisão automática e fila: 2ª auditoria, 14/10/2026. Biblioteca movimento.py: 20/10/2026.
- DaVinci como padrão do CIBO desde 18/10/2026.
