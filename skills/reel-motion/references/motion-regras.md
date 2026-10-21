# reel-motion — regras de motion, cor e variações

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Animação ligada ao conteúdo (regra do editor, 13/10/2026)

- **As animações não podem ser todas do mesmo jeito: cada painel nasce do que está sendo falado** naquele
  trecho (número dito vira contador; contraste vira lados; trajetória vira rota; tese corrigida vira
  riscado; lista dita vira checklist). Não use painel genérico só para "ter motion".
- Variar entre os reels do mesmo lote e do mesmo feed: cada reel tem pelo menos um painel próprio e não
  repete a família de painéis do reel anterior.
- Tempos de entrada casados com a palavra no `edit_mfa.json` (o `checa_props.py` cobra).

## Sem sobreposição (regra do editor, 13/10/2026)

- O João reprovou os cortes 02 e 03 por "elementos sobrepondo outros". Quadros-teste soltos não pegam isso.
- **Antes de mostrar qualquer prévia ou final: `qa_paineis.py PROJ rNN 0.5 --video <prévia>`** (painel a cada 0,5 s, folhas em 05_qa; com `--video` os quadros saem da prévia em segundos, sem renderStill quadro a quadro, que levava ~9 s/quadro com a máquina ocupada) e olhe
  todas as folhas: pílula sobre título, texto quebrando, elemento cortado na borda do painel, linhas de pílulas coladas.
- Pílulas soltas (`tags`): com `layout.autoTags` (tema do João) as da mesma linha (mesmo y) são distribuídas pela largura
  medida, sem colidir; linhas de pílulas abaixo de y 870 do desenho saem da borda — use 790/855.
- Prefira dar a informação dentro do próprio painel (destaque no título, pulso do item, subtítulo do card) a uma pílula solta.

## Jeito de mexer por cliente (perfis de movimento, 20/10/2026)

O editor pediu mais qualidade no motion; aprovado no antes/depois do 02 da Andrea ("ficou mais suave", 05_qa/motion_antes_depois).
Tudo no Remotion, só princípios de animação (o editor não usa After Effects). `theme.motion` no tema do cliente:

| Perfil | Curva de entrada | Duração | Quique | Título | Fundo vivo | Para |
|---|---|---|---|---|---|---|
| `atual` (padrão sem bloco) | bezier(.22,.61,.36,1) | 1× | sim | inteiro | não | sai idêntico ao motor antigo |
| `editorial` | bezier(.3,0,.15,1) | 1,15× | não | palavra por palavra, 70 ms | sim | bem-estar, espiritualidade, editorial (Andrea) |
| `premium` | bezier(.4,0,.2,1) | 1,2× | não | palavra, 80 ms | leve | luxo, marca premium |
| `energetico` | bezier(.16,1,.3,1) | 0,8× | 1,3× | palavra, 45 ms | não | hype, negócios rápidos |

- Campos soltos sobrescrevem o perfil: `{"perfil": "editorial", "dur": 1.05, "ambient": 0.5}`.
- Peças: `Title` (máscara por palavra), `Ambient` (manchas de luz que derivam ~16 s), `pop(y1)` no lugar de curva com
  quique fixa (o perfil escala ou zera o quique), `M.settle` = detalhe que assenta depois do elemento (subtítulo do card em `sides`).
- Princípios que valem para painel novo: entrada desacelera até parar, saída acelera; um destaque por quadro;
  grupo entra escalonado (40–80 ms por item, grupo inteiro ≤ 0,8 s); elemento maior ou que anda mais leva mais tempo;
  conteúdo sério/bem-estar sem quique; pelo menos 0,3 s parado depois de cada movimento.
- Escolha o perfil no briefing pelo tom do cliente; mostre antes/depois de 10 s quando mudar.
- Tipografia (20/10/2026, ajuste fino aprovado sem diferença perceptível; o ganho visível está no movimento): título com
  `title.lh` 1,1 e `title.ls` '-0.015em' (serifa grande); legenda ≥ 60 px na tela dividida; `motion.peso` [ini, fim] faz a
  palavra de destaque engrossar ao aparecer (só fonte variável; Andrea [400, 750]).

## Cor: identidade sem perder leitura (regra do editor, 13/10/2026)

- As cores dos painéis vêm da identidade do cliente (medidas de material real dele: thumbs, banner,
  capa aprovada), **mas nunca à custa da leitura**. Todo par texto/fundo do tema passa no contraste
  WCAG ≥ 4,5:1 (≥ 3:1 para título ≥ 60 px). Meça com `scripts/contraste.py temas/<tema>.json` ao criar ou
  mudar um tema; destaque que não passa vira fundo (faixa) com texto claro, não texto colorido.

## Variações pedidas pela Priscilla (13/10/2026)
- **Tela dividida invertida:** `split: [{s, e, inv: true}]` põe ela em cima (topo da cabeça um pouco cortado, `layout.camUp`, padrão 300) e o painel embaixo, subido `layout.invPad` (150) acima da borda por causa da interface do Instagram; a legenda vai para cima do painel, sobre o vídeo. Entre um trecho normal e um invertido, ponha uma tela cheia curta (não emende os dois).
- **Olhar para o lado:** `scripts/olhar.py public/rNN/camera.mov --folha 05_qa/rNN_olhar.jpg` antes da prévia; o detector marca também piscada e cabeça inclinada, então confira a folha. Olhada clara numa emenda/pausa: segure o quadro anterior olhando para a câmera (`freezeframes`) e re-renderize só o trecho; olhada com ela falando em tela cheia fica.
- **Capa para o feed:** `capa.frame_file` = quadro recortado da fonte aberta 4K (ela mais baixa, título acima da cabeça, dentro da faixa 240–1680 do grid 3:4); com `shift` o topo vazio vira a imagem desfocada.
- **Trilha:** `music_gap` 18,5 dB (o `mix` calibra sozinho).
