---
name: priscilla-daher
description: Reels verticais da Priscilla Daher — talking head com motion em Remotion, tela dividida (painel off-white em cima), legenda serifada, burn nas trocas. Use para qualquer corte, ajuste ou lote dela.
---

# Priscilla Daher — reels com motion

> Motor: agora é a skill `reel-motion` (tema `priscilla`, mesmo resultado pixel a pixel, 13/10/2026). Reel novo dela roda no motor único; a cópia em `04_work/` só para refazer os já aprovados.

Projeto: `/Volumes/SSD/Movies/Edição/Mídia/priscilla daher/`. O pipeline mora em `04_work/` (um `rNN/` por reel + `mg/` com o Remotion). Mapa dos reels em `05_qa/mapa_de_cortes.md`; decisões em `07_manifests/brief.md`.

## Material
Sony 4K 29,97, câmera deitada (rotate clock), Rec.709. Cada bruto de roteiro = 1 reel, com retakes. **A equipe sopra a fala baixinho (−30/−50 dB) antes de ela repetir (−13/−20 dB): o take certo é sempre o dela, alto, depois do sopro.** O videomaker também comenta ("ficou estranho?") — nunca entra.

## Estilo aprovado (piloto 01 e reel 02 aprovados sem erro)
- Tela dividida (SPLIT 940) com painel off-white, paleta off-white / grafite / terracota; ela em tela cheia no gancho, nos "títulos" de virada e no fechamento.
- Legenda C: Instrument Serif, destaque em itálico terracota; grafite sobre o painel, branca com halo em tela cheia. "R$ 82" com espaço não separável (`R$ 82`).
- Lower third só com o nome. CTA só onde ela fala ("já me segue").
- **Toda troca de painel dentro da tela dividida tem burn** (film burn vertical do acervo global em screen 85%, tom quente, pico no corte) + whoosh.
- **Animação de dado termina antes de qualquer transição**; troca de layout cai numa pausa/emenda.
- Painel de cima nunca fica mais de 2,5 s sem algo entrar.
- Cada reel ganha pelo menos um painel próprio (não repetir a mesma família de painéis no feed). Painéis prontos em `mg/src/priscilla/Reel.tsx`: stat, empty, strike (textos a/b/accent), media (+carimbo), bars (+logo, noNum), ruler, cards, sides, grid, checklist, rank, route, coins, tickets, oscillate; extras por painel: `tags` (pílulas com x/y/at) e `step` (numeral 1-2-3-4).
- Trilha alterna por reel (acervo global `musica/_global`): 01 lofi-tea, 02 cozy-acoustic, 03 curiosity. SFX da biblioteca CC0 global — o editor amou.
- Marca citada (Gomes da Costa, Alva…): logo/foto do site oficial em `03_assets/marcas_terceiros/` com `origem.csv`.

## Pipeline (sempre nesta ordem)
`python3 04_work/reel.py rNN ETAPA`, com `rNN/reel.json` (nome, bruto, trilha, prompt, fix_words, shot_levels, camera_moves, capa) e `rNN/segs.json`.
1. Transcreva o bruto (`wt.py`, mlx-whisper via `uv run --with mlx-whisper`) e liste as frases marcando a voz da equipe pelo nível (p90 < −25 dB = equipe).
2. Escolha os takes (último inteiro dela), alinhe cada um no MFA e corte em palavra (início −0,06 s, fim +0,10 s); pausas internas > 0,6 s viram emenda.
3. `takes` (barra a voz da equipe) → `voz` (monta, retranscreve, MFA com números por extenso) → leia o texto montado inteiro antes de seguir.
4. Escreva `blocos_manual.txt` → `legenda`.
5. Escreva `rNN/props.py` e `sfx.json` → `props` (o checador tem que dar "OK: nenhuma pendência") → quadros-teste com `mg/stills.mjs`.
6. `camera` (face_track com `--debug`, senão não grava framings) e `mix`.
6b. Capa: escolha o quadro OLHANDO a imagem (folha com 6 a 16 quadros dos trechos em tela cheia, depois quadro a quadro em volta do melhor): olhos bem abertos, olhando para a câmera, **boca fechada** (procure nas pausas entre frases), nunca no meio do piscar nem falando (o 03 com a boca aberta foi reprovado). No 02 o quadro escolhido só pelo tempo saiu de olhos fechados e o editor reprovou ("a capa ta horrivel"). Para trocar só a capa: `capa.mjs` e depois `reel.py rNN entrega`.
7. `previa` (540p em `05_qa/previas`) → **o editor aprova** → `final` (capa no quadro 0, Rec.709, ≤10 Mb/s, verify + legenda cruzada).
8. Ajuste pontual: `trecho A B` (só aqueles segundos) ou refaça o mix e troque só o áudio. Nunca re-renderize o que já está aprovado.

## Feedback de 13/10/2026 (áudios no WhatsApp, em `02_transcripts/feedback/`)
- **Capa pensada para o feed:** o grid do Instagram corta a capa 9:16 para 3:4 (sai ~240 px em cima e embaixo). Título dentro dessa área segura e **nunca sobre o rosto**: enquadre ela mais baixa (use o quadro aberto da fonte 4K, não o close da câmera) e deixe o título acima da cabeça.
- **Trilha mais baixa:** o som de fundo estava alto. Trilha uns 5 dB abaixo do que foi no 01/02 (`volume=-11.5dB` no mix em vez de −6.5).
- **Olhar para o lado:** quando ela desvia o olho/cabeça no meio da fala, isso não pode aparecer. Detectar no rastreio de rosto e cortar fora ou cobrir (tela cheia de painel/B-roll).
- **Variação de layout:** gostaram da tela dividida; às vezes inverter, com ela em cima e o topo da cabeça um pouco cortado.

## Regras do editor
- Tudo no SSD, inclusive temporários (`TMPDIR=/Volumes/SSD/CIBO/tmp`); não apagar temporários até ele liberar.
- Arquivos inúteis e zips vão para `lixo/`.
- Gastar poucos tokens: saídas filtradas, uma folha de contato por decisão.
- Pode rodar até 3 trabalhos pesados em paralelo (render, câmera, transcrição): adiante o próximo reel enquanto o atual renderiza.

## Feedback de 14/10/2026 (4 áudios em `criticas/`, transcritos em `05_qa/criticas/`)
- **Nada de tudo igual.** Antes de montar, escolha o formato pelo conteúdo e pelo que está performando: tela dividida
  com motion é um formato, não o padrão. Ex.: o 06 (suplemento saturado) pedia **só legenda** + uma imagem pequena da
  marca do momento (Growth) como gancho visual de feed. Proponha o formato ao editor ("pra esse conteúdo, acho que fica
  melhor X") com visão de editor, sem esperar referência.
- **Imagens reais além das animações**: logo da marca citada (Shein), foto do que ela descreve (navio com gente
  costurando). Gancho visual forte nos primeiros segundos.
- **Corte comendo palavra** (07): `reel.py … revisa` antes de todo final, e ouvir cada aviso de corte.
- **Trilha**: orgânicos podem ir sem; nunca acima da voz; BPM casado com o ritmo da fala (fala lenta, trilha calma).
