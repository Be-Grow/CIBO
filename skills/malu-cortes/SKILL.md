---
name: malu-cortes
description: Cortes verticais 9:16 da Malu (entrevista Zeo/Turi-Ita) no padrão premium de bem-estar — mapa de edição, fala limpa, motion, legenda Montserrat, SFX curados, pente-fino. Use só em trabalhos da Malu.
---

# Malu — cortes de entrevista

Motor: os scripts da `fernanda-produto` (`render.py`, `review_job.py`, `sync_captions.py`, `face_track.py`, `speech.py`, `find_pauses.py`). Esta skill define **o estilo e as regras da Malu**; nada daqui vale para a Fernanda nem para o Bombordo. O que vier de outra skill (a legenda animada e a altura da legenda do Bombordo) é adaptado aqui, sem alterar a skill de origem. Leia `references/client-content-bible.md` antes de começar. Modelo de job: `assets/job.malu.json`. Fontes: `assets/fonts/` (Montserrat Light, Regular e SemiBold, licença OFL).

## Direção criativa

O padrão é um **Reel de marca premium de bem-estar editado por um motion designer sênior**: elegante, fluido, com algo acontecendo o tempo todo, sem virar poluição visual. Estar correto não basta: o corte precisa de ritmo e acabamento. Nas palavras do usuário: "uma edição boa, parecendo que foi feita por um editor com anos de experiência e com um bom motion no geral".

Regras de ritmo (valem para o mapa e são conferidas no pente-fino):
- **Gancho nos primeiros 1,5 s**: título animado com a frase mais forte **dela** no corte, zoom de abertura e SFX de entrada. A pergunta da entrevistadora nunca aparece no reel, nem a voz nem o texto na tela, mesmo quando a janela de corte começa nela.
- **Mudança visual a cada 2 a 4 s** (plano, zoom, referência, gráfico ou destaque de legenda). Nunca mais de 5 s sem nada mudar.
- **No máximo 2 eventos de motion ao mesmo tempo** (por exemplo, zoom e destaque de legenda). Zoom, referência e gráfico juntos, nunca. A legenda normal palavra por palavra, a volta lenta do zoom e o push de respiro são fundo e não contam como evento; entrada de gráfico, destaque, zoom, referência e transição contam.
- **Todo evento precisa de motivo na fala**: ênfase, número, produto, mudança de ideia, punchline.

## Fluxo

1. **Fonte e estrutura** (`video-project-structure`): master em `01_sources/masters`, transcrição do master inteiro em `02_transcripts` (large-v3 com `--word-timestamps True --condition-on-previous-text False`).
2. **Seleção e fala limpa** (skill `fala-limpa`, obrigatória): só a voz dela. Em trecho curto e duvidoso, decida quem fala comparando o timbre (ECAPA) com uma amostra limpa da Malu e outra da entrevistadora: a auditoria sozinha errou "Uma limpeza" e "ou qualquer argila". Cortes: `scripts/cuts.py AUDIO16K IN OUT --cut A B ...` encurta toda pausa > 0,45 s para ~0,25 s e leva cada corte de conteúdo para o silêncio real. Confira no envelope de 10 ms os pontos em que o teste de áudio perde sílaba: o /s/ final e o fechamento do /t/ passam por silêncio ("testes", "feito", "jamais"). Corte a pergunta do entrevistador, comentários e vozes ao fundo. Corte hesitações e encurte pausas de pensamento (> 0,45 s → ~0,25 s, inclusive nas **emendas**: silêncio de saída + de entrada). Corte de silêncio a silêncio; queda curta no meio da palavra é consoante, não pausa.
3. **Teste só no áudio** dos trechos (`atrim`) com os dois modelos antes de qualquer imagem. Toda frase precisa sair inteira.
4. **Mapa de edição (obrigatório, antes de montar imagem).** Escreva `05_qa/<reel>_mapa_edicao.md`: uma tabela com uma linha por evento — tempo, trecho da fala, plano, motion, referência, gráfico, SFX e a **intenção** de cada escolha. Confira as regras de ritmo acima: nenhum buraco > 5 s, nenhum instante com mais de 2 eventos, todo evento com motivo. **Mostre o mapa ao usuário e espere o ok antes de renderizar a prévia.** Textos que não saem da fala (lower third, cartão final) são perguntados ao usuário, nunca inventados.
5. **Planos e enquadramento.** Trecho com menos de 1,2 s não vira plano: mantenha a pausa natural quando ela é dramática ("fica sem… chão") ou esconda o salto sob card/tela cheia (`review_job.py` aceita plano curto sob `malu_refs` card/full). Três níveis: 0 aberto (1500 px), 1 médio (1300), 2 fechado (1050 — no Instagram, exibido em 1080, é praticamente nativo). Escolha com intenção: aberto quando começa uma ideia, fechado na ênfase/punchline. Nenhum nível repetido lado a lado; nada de A/B/A/B mecânico. Plano ≥ 1,2 s.
6. **Rastreamento de rosto** (`face_track.py job.json --debug qa/face_track.mp4`, depois `--apply`): matriz no rosto; olhos a ~1/3 da altura; espaço de olhar do lado para onde ela olha (ela olha para a **direita**, onde fica o entrevistador). Plano parado fica **travado**; plano em que o rosto sairia da zona segura é **seguido** com zona morta e amortecimento. Mostre o vídeo de diagnóstico quando o usuário quiser conferir. A posição do queixo por plano também sai daqui e define a altura da legenda.
7. **Referências** — ver seção própria. Entram e saem **no próprio corte** ou no centro de uma pausa real, nunca a menos de 1,2 s de um corte.
8. **Zooms** (estilo aprovado): entrada de 0,3 s, volta lenta de ~6 s, **motion blur de câmera com shutter angle 360°** (`camera.py`, até 16 subquadros por quadro em movimento), como o efeito Transform do Premiere. Nunca use mistura de quadros (`zoom_blur`/`tmix`: fantasma de mão e boca, "blur estranho"). **Zoom ancorado no rosto** (`zoom_center_face: true`, `zoom_amount: 0.14`, posição do rosto por plano vinda do `face_track.py --apply`): os olhos ficam na mesma altura e o rosto vai do espaço de olhar para o **centro exato** no auge ("a convidada não tá 100% centralizada no zoom"). Varie o tipo: **punch-in rápido** na ênfase/punchline (`camera_moves` `punch`) e **push-in lento** em ideias que crescem (`push`); plano longo sem zoom leva `breathe` de 2 a 3%. Um zoom de abertura em t=0; os outros em começo de frase, dentro de plano contínuo, a ≥ 0,5 s de corte e sem encostar em referência.
9. **Kit de motion** — ver seção própria.
10. **Legenda** — ver seção própria.
11. **SFX** — ver seção própria.
12. **Áudio.** Arquivo editável com três faixas (`sfx_separate: true`, `edit_suffix: "voz, musica e sfx separados"`): A1 voz, A2 música, A3 SFX. O "mix pronto para postar" tem tudo junto. Música *Motivating Mornings* a `-27.5` dB, `duck_threshold: 0.015`. **Backtiming**: o final natural da faixa coincide com o fim do reel (`offset: "auto"`); no início, entra com fade curto; leve crescendo no gancho e no encerramento. `tail_hold: 0.8` (a última palavra nunca é engolida pelo fade). Mix final a **-14 LUFS integrado, true peak -1 dBTP**. Use `lufs: -13` no job: o limitador do `render.py` come ~1 LU depois do ganho (no reel 01, `-14` entregou -15,0 e `-13` entregou -14,1).
13. **Pente-fino antes do render (obrigatório)**: `review_job.py` com a transcrição do áudio editado (large + turbo) e `audit_fala.py` na fonte com o job. Só renderize com **0 bloqueios**; cada aviso restante precisa de uma decisão de editor registrada (`cortes_revisados`, `caption_pins`).
14. **Prévia e pente-fino de motion.** Renderize a prévia (`render.py job.json preview INICIO DURACAO`, 1080×1920). Extraia frames **no meio de cada movimento** (zoom, entrada de gráfico, transição de referência, destaque) e monte folhas de contato (`kinetic/cli.py job.json sheet PREVIA SAIDA.jpg --start T0`). Confira: motion blur natural (sem fantasma), rosto e legenda na zona segura, gráfico sem cobrir o rosto, nenhum trecho parado demais nem poluído demais. **Só depois peça o ok do usuário para o render completo.**
15. **Render** (`render.py prep/check/render`, em background com vigia de CPU) e **QA** no arquivo final: `video-delivery-safety-check`, `caption-quality-gate`, `fala-limpa` no áudio final, `legenda-cruzada`. Um arquivo de 0 bytes ou incompleto em `06_deliverables` nunca fica lá: se o render travar, apague a saída parcial e registre.

## Legenda

- **Montserrat fina**: Regular no texto e SemiBold no destaque, substituindo DM Sans + Playfair. No teste do reel 01, a Light branca sumiu sobre a estante clara ("da Turi-Ita", tela dividida); por isso o padrão é Regular com sombra suave e halo escuro largo (`halo_alpha`). Use Light só sobre fundo escuro, conferindo na prévia. O destaque é **contido**: 1,3x (faixa de 1,2 a 1,4x), nunca os 2x do Bombordo.
- **Pontuação na tela**: saem vírgula, ponto, aspas, dois-pontos e reticências; ficam "?" e "!". Nunca saem o hífen dentro da palavra ("Turi-Ita"), acentos, números, "%" e "R$". Depois de qualquer mudança no motor, confira no render que "Turi-Ita" saiu certo.
- **Animação palavra por palavra** adaptada do Bombordo (ver "Motor da Malu"): deslize com blur, queda vertical e revelação por máscara, todos em Easy Ease. A palavra aparece ~1,5 quadro antes do som, a palavra falada ganha a cor de destaque da paleta, e o micro-movimento é só respiração de escala (~1,2%). **Sem** `pop_spring` nem `ease_out_back`: o destaque entra como unidade, com zoom suave de 1,06→1 e blur. Cores da paleta da bíblia, nunca o azul do Bombordo.
- **Altura logo abaixo do queixo**, pelo queixo medido no vídeo já com zoom (o zoom de 14% desce o queixo). Nunca cobre o rosto e respeita a área segura do Reels (coluna de botões à direita, faixa de baixo). Em tela dividida e card, a legenda segue a regra do layout.
- **Camada sem perdas**: QuickTime Animation RGBA. Se um dia ela virar H.264 cor + máscara, a máscara tem que ser qp 0 e a cor yuv444p; a Light é fina e serrilha com compressão.
- Mantém: texto revisado à mão (quebra por sentido, linha ≤ 26 caracteres, nunca terminar linha em palavra funcional), `sync_captions.py` para colocar cada bloco no ataque real da fala, 6 a 8 palavras-chave (destaques) por minuto escolhidas pelo sentido. Casos que nenhuma regra resolve: `caption_pins` (tempo do original).

## Nunca mais (erros reprovados)

- Reel entregue sem a explicação central (a antiga cortou "a silver e a standard são mais grossas").
- `keywords` inflada (23+ palavras com pontuação), destaque caindo em "marido".
- Voz do entrevistador antes de "É a micronização"; "vai preparando o corpo" (pessoa ao fundo). Atenção: "ou deixa sair, né?" é da Malu (conferido por timbre); cortar isso deixou a fala do Thomas pela metade e o usuário reclamou.
- "Eeee" de hesitação, pausas de 0,8 s nas emendas, palavra final engolida pelo fade.
- Zoom começando 0,07 s depois de um corte; referência saindo 0,2–0,6 s antes de um corte; pingue-pongue de enquadramento.
- Blur de zoom por mistura de quadros (fantasma) e zoom no centro do quadro com o rosto fora do centro.
- Legenda entrando 0,3–0,6 s fora da fala por confiar no tempo do Whisper.
- Edição correta mas sem ritmo nem acabamento: trechos de 5 s ou mais sem nada mudar, plano 100% parado, evento sem motivo na fala.
- Render travado deixando arquivo de 0 bytes em `06_deliverables` (v10 do reel 01).
- Flash de 1 quadro na emenda (plano seguinte com o enquadramento do anterior): o `camera.py` decide o plano pela contagem exata de quadros do trim, nunca pelo tempo arredondado.
- Palavra final comida pelo `out` ("desconforto" sem o "-to"): confira no envelope o fim real da última palavra.

## Referências (abra só quando o gatilho bater)

| Arquivo | Abra se |
|---|---|
| `references/motor.md` | rodar ou corrigir os scripts (mapa, burn, áudio, render) e o motor da Fernanda por baixo |
| `references/motion.md` | título de gancho, lower third, números, callouts, cards |
| `references/sfx.md` | escolher ou nivelar SFX |
| `references/referencias-tela.md` | referência em tela dividida, tela cheia ou card |
| `references/client-content-bible.md` | identidade e tom da cliente |
