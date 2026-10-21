# Regras transversais — DaVinci Resolve pela API (medido no Resolve 20.2.3, EP 06, 18/10/2026)

**Projeto organizado (regra do CIBO, 20/10/2026: "os projetos que são feitos no DaVinci precisam estar sim organizados"):**
todo projeto entregue no Resolve sai arrumado, não só a timeline.
- Project Manager: pasta do cliente na árvore que o editor já usa (`BeGrow/<Cliente>/`) e projeto com o nome do job (`EP 07 - Izaac Nava`), nunca solto na raiz nem "Untitled".
- Media Pool em bins por tipo, na ordem: `01 BRUTO`, `02 VOZ`, `03 TRILHA`, `04 SFX`, `05 LEGENDA`, `06 GRAFISMOS` (painéis, títulos,
  lower, cartões), `07 BURNS`, `08 CAPAS`, `09 REFERÊNCIA` (prévias/renders de conferência) e `00 TIMELINES` com uma sub-bin por
  formato (`Episódio`, `Cortes 9x16`, `Versão 15 min`...). Nada solto na Master.
- Timelines com o nome da entrega (`NN - HEADLINE`, `EPISÓDIO - …`, `15 MIN - …`), faixas nomeadas e clipes coloridos (tabela abaixo).
- Nome de arquivo único por pacote (ver Lições da Andrea) para os bins não misturarem mídia de vídeos diferentes.
- Feito pela API (`MediaPool.AddSubFolder`, `MoveClips`, `pm.CreateFolder`); confira a árvore lendo de volta antes de dizer que está pronto.

**Cores e nomes das camadas (regra do CIBO, 19/10/2026, pedido do editor para organizar a timeline):** toda timeline
entregue no DaVinci sai com cada clipe na cor do seu tipo e cada faixa com o nome do tipo. A API não pinta a faixa,
só o clipe. Aplicar com `reel-motion/scripts/resolve_cores.py` (o `resolve_fx.py` já chama no fim).

| Tipo | Cor do clipe | Nome da faixa |
|---|---|---|
| Câmera (bruto) / áudio da câmera | Blue | CÂMERA bruto / ÁUDIO câmera (ref.) |
| Fundo desfocado, câmera renderizada de referência | Navy | CÂMERA fundo desfocado / CÂMERA renderizada (ref.) |
| Movimento: punch/zoom (clipe de ajuste com Fusion) | Orange | MOV punch/zoom (Fusion) |
| Movimento: troca de tela dividida (ajuste com Fusion) | Apricot | MOV tela dividida (Fusion) |
| Mídia / B-roll | Teal | MÍDIA / B-roll |
| Fundo do painel | Purple | PAINEL fundo |
| Partes do painel (título, itens, linha) e etapa | Violet | PAINEL partes |
| Etiquetas | Pink | ETIQUETAS |
| Títulos, gancho, tarja, palavra-chave | Yellow | TÍTULOS / gancho / tarja |
| Legenda (um bloco por frase) | Lime | LEGENDA (frase) |
| Burns | Tan | BURNS |
| Extras (cartão de marca etc.) | Beige | EXTRAS |
| Capa | Brown | CAPA |
| Voz | Green | VOZ |
| Trilha | Olive | TRILHA |
| SFX | Chocolate | SFX |

**Motor padrão = fluxo da Andreia (20/10/2026, "gostaria que fosse o padrão de edição da CIBO"):** todo job de fala segue
a receita de 10 etapas da `reel-motion` ("Padrão de edição do CIBO"): briefing com tema e grafia dos nomes → fonte (rastreio,
fps automático) → trechos e fala limpa → legenda MFA conferida → motion nascido da fala no perfil do cliente → trilha e SFX
com prévia no trecho real → prévia aprovada → `fila_davinci.py` (pacote com nomes únicos, projeto organizado, Fusion,
cores, `qa_resolve`) → `qa_render` depois do render do editor → correção só do que mudou. Cliente com skill própria
mantém estilo, assets e regras dele; o que muda é a entrega pelo mesmo pacote DaVinci.

**Nada de ffmpeg na entrega (20/10/2026, Bombordo EP 07, segunda vez que o editor cobra):** nem o episódio completo
"só com corte e fade" sai pelo ffmpeg. Todo cliente usa o fluxo DaVinci do `reel-motion` (pacote por camadas, projeto novo
organizado, Fusion nos movimentos, QA na timeline e no render). ffmpeg é só para análise, extração e prévia leve.

**Padrão do CIBO para todo cliente (18/10/2026): o render final é do editor, no DaVinci.** Entregue prévias de
conferência (baixa, rápidas) + pacote com cada camada isolada (câmera, mídia/B-roll, painéis, legenda com alfa,
títulos, cartão final, voz/trilha/SFX em WAV separados) + XML. **Não rode o render final queimado** (CRF baixo,
preset lento): ele custa o maior tempo do job e o editor refaz a cor e o acabamento no Resolve de qualquer jeito.
MP4 pronto para postar só se o editor pedir. Valide importando pela API num **projeto novo com o nome do job**
(ex.: "Growth Leaders – Reels"), nunca no projeto que ele tem aberto (no dia era o do Bombordo e Boreste), e
devolva o projeto anterior ao terminar. ("o DaVinci acaba sendo mais eficiente nessa parte", Bombordo EP 06;
"isso deveria ser na cibo mesmo, no geral", João/Growth Leaders, 18/10/2026)

A API funciona
(`DaVinciResolveScript`, ambiente em `RESOLVE_SCRIPT_API`/`RESOLVE_SCRIPT_LIB`/`PYTHONPATH`).
- **XML do FCP7 no Resolve:** clipe encaixado antes do Movimento; centro relativo ao clipe encaixado;
  `<when>` do keyframe conta do início da mídia (soma o `<in>`); áudio de MP4 numa trilha derruba a
  importação inteira (extraia WAV); cada trilha de áudio vira mono centralizada a −3 dB (voz dual-mono numa
  trilha só +3 dB; estéreo em duas com `audiopan` −1/+1). Gerador validado e detalhes: `bombordo-boreste`
  SKILL.md, seção "XML para o DaVinci". O `projeto_nle.py` antigo ainda tem esses erros.
- **Render:** chame `LoadRenderPreset('H.264 Master')` antes de `SetRenderSettings`. Uma chave inválida
  (ex.: `FrameRate`) faz o `SetRenderSettings` falhar inteiro, e uma configuração antiga presa na Deliver
  gerou MP4 só de áudio duas vezes. Confira o retorno e os streams (`ffprobe`) de todo arquivo.
- **AAC sai a 64 kb/s** e não há chave para o bitrate: renderize também um MOV com `AudioCodec: lpcm` e
  remonte o MP4 com `-c:v copy -c:a aac -b:a 256k`.
- **`SetLUT` só aceita LUT da pasta do sistema** (`/Library/Application Support/Blackmagic Design/DaVinci
  Resolve/LUT`) e precisa de `RefreshLUTList()`; aplique pelo `GetNodeGraph().SetLUT(1, nome)`. A API não
  cria Adjustment Clip.
- **Arquivo trocado no mesmo caminho fica em cache** no Media Pool: para medir de novo, use nome novo.
- **O projeto aberto é do editor:** teste num projeto próprio ("TESTE XML CIBO"), devolva o projeto que
  estava aberto ao terminar, e não reabra/renomeie timeline dele sem avisar. Corte feito pelo editor na
  timeline importada não acompanha a legenda (clipe único): refaça o corte no pipeline e reimporte.

- **Lições da Andrea (20/10/2026, 4 vídeos × 2 formatos; o editor achou os defeitos um por um na tela):**
  - Nunca edite a timeline por ciclos de exportar/importar .drt: o GlobalIn do Fusion sobe e o render falha. Edite o XML do
    backup e importe uma vez (`reel-motion/scripts/resolve_refaz_de_backup.py`).
  - Arquivo de mesmo nome em pacotes diferentes (`voz.wav`, `trilha.wav`, `sfx/*.wav`) vira um item só no Media Pool: o
    vídeo 03 tocou a voz do 01. O `davinci.py` grava todo arquivo com o sufixo do reel (`voz__r01.wav`) desde 20/10/2026;
    pacote antigo: religar com `pacote_certo()`. Gerador de outra skill (XML do Bombordo etc.) faz igual.
  - Clipe recolocado pela API entra com Scaling 0 e sem RotationAngle: copie as propriedades dos irmãos.
  - Importação de XML (EP 07, 20/10/2026): um still PNG no xmeml faz `ImportTimelineFromFile` devolver None para a timeline
    inteira. Capa fora do XML e pela API: `ImportMedia` + `AppendToTimeline` com `startFrame 0, endFrame 1` (endFrame 0 é
    recusado). PNG com número no fim do nome vira sequência de imagens; `pathurl` em NFC não casa com o disco do Mac (use NFD);
    nome igual entre cortes vira um item só. Voz medida em mono: ganho = −16 − I (LUFS).
  - **Antes de dizer "corrigido": `reel-motion/scripts/qa_resolve.py`** (offline, outro pacote, transform diferente entre
    os trechos, GlobalIn) com o render parado, e depois do render `qa_render.py PROJ` (sincronia por trecho, offline, preto),
    nos dois formatos. Conferir só o trecho mexido deixou passar o mesmo defeito na outra versão.
  - Renderize só o que mudou, na ordem que o editor precisa; não refaça os 8 por mudança num só.
- **Render no Deliver pela API (19/10/2026):** H.264 com qualidade limitada a **25.000 kb/s** (`SetRenderSettings({'VideoQuality': 25000})`),
  nunca o automático/80.000 do preset. Resolução de cada job = a da timeline. Pedido do editor (Andreia).

Volta ao checklist: [`_checklist.md`](_checklist.md).
