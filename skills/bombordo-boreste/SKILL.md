---
name: bombordo-boreste
description: Cortes verticais 9:16 do podcast Bombordo e Boreste com estilo, assets e fluxo próprios (legenda estática ou kinetic, capa com convidado sorrindo, entrega no DaVinci). Use só em trabalhos do Bombordo e Boreste.
---

# Bombordo e Boreste → Reels

**Local setup:** dependencies (Pillow, numpy, OpenCV headless) live in the bundled venv at
`~/.claude/skills/bombordo-boreste/.venv`. Run scripts with
`~/.claude/skills/bombordo-boreste/.venv/bin/python3
~/.claude/skills/bombordo-boreste/scripts/make_reels.py`, or activate that venv first,
instead of the bare `python3` shown below. Requires `ffmpeg` and `ffprobe` on PATH.

Builds finished vertical cuts from a master video + SRT. Everything is driven by one
`job.json`; the scripts do transcription-free caption timing (reused from the SRT),
silence-snapped trimming, caption rendering, audio sweetening and the cover.

## Motor dos cortes: reel-motion (editor, 01/11/2026)

"Mude o motor de bombordo e boreste para o mesmo da andreia e fernanda ... esse motor aqui erra muito nos cortes das falas."
Trechos e fala saem do `reel-motion` (tema `temas/bombordo.json`); a identidade continua a desta skill (legenda kinetic
escolhida pelo editor em 01/11, burn azul, clique, punch-in, capa, fade 0,42 s). O `make_reels.py`/`refina.py` antigos
não escolhem mais emendas.
1. Por corte, `04_work/rNN/{reel.json,segs.json}` (segs em segundos do bruto; cold open = 1º trecho fora de ordem).
   `src_48k.wav`/`src_16k.wav` extraídos uma vez do bruto e linkados em cada rNN (não rode `fonte` 7 vezes).
2. `~/.venvs/audiotools/bin/python reel-motion/scripts/reel.py PROJ rNN voz` (checa_takes, Whisper, MFA) e `revisa`
   (emenda no meio da palavra, hesitação, voz da equipe). Use o Python do venv: o python3 do sistema não tem numpy.
3. `scripts/ponte_reel.py PROJ rNN corteNN --segment` → `cortes/corteNN/{edit.json, edit16k.wav, kinetic/}`.
4. Camadas e XML com o kit do episódio (`04_work/cortes/{componentes,enquadra,cortes_xml,importa}.py`, copiado do EP 07):
   `enquadra.py`, `componentes.py corteNN`, `cortes_xml.py`, `importa.py` → Resolve.
5. Cartilha do cliente (trechos proibidos) vale para episódio e cortes: `07_manifests/remocoes.json`, que o
   `davinci_episodio.py` lê. Toda menção a política sai, inclusive brincadeira.
6. **Emenda com contexto** (editor 01/11/2026: "não pode só cortar algo e deixar um pedaço sem contexto"): depois de
   marcar a cartilha, leia cada emenda como ela soa (≈9 s antes ‖ 14 s depois, palavras de `ep_words.json`) e procure no
   que ficou qualquer referência ao que saiu. Fala que depende do trecho removido sai junto (EP 10: "é muita venda" sem o
   "final de ano"); pergunta refeita depois de interrupção perde a 1ª tentativa. Pontas sempre por palavra escolhida
   pelo sentido (`encaixa_palavras.py` só sugere; a palavra mais próxima no tempo deixou "e"/"eu"/"quando" sobrando).
   Depois, confira pelo ÁUDIO montado (6 s antes + 7 s depois de cada emenda, retranscrito com large-v3): o tempo de palavra
   do Whisper erra (EP 10, R12 comeu o "Yuli," que o texto dizia estar lá).
   A volta entra no ataque da 1ª palavra, não antes (o editor atrasou 7 voltas em 0,1–0,6 s no EP 10). Depois que o
   editor mexe na timeline do episódio, nunca reimporte (o script recusa sem `--refaz`); leia as bordas dele pela API e
   atualize `remocoes.json`/`episodio_keeps.json`.

**Pacote DaVinci = fluxo da Andreia/Fernanda, nunca XML do FCP7** (editor 01/11/2026: "não é pra usar xml, é pra montar dentro
do davinci ... assim como os outros clientes"): `reel.py PROJ rNN legenda|props|mix` e `fila_davinci.py PROJ "EP NN - Convidado"
"BeGrow/Bombordo e Boreste" r01 …`, no MESMO projeto do episódio. Legenda do motor (tema `bombordo`), cliques em `sfx.json`,
burn azul no props (`burns/filmburn_blue.mp4` em `04_work/public`, tema com `burnFF: null`), sem `formato: so_legenda`
(ele apaga os SFX). **Enquadramento e zoom no DaVinci:** bruto 16:9 em timeline 9:16 precisa de `"zoom": 1.7778` no reel.json
(sem ele o motor deixa escala nativa e o Resolve mostra o quadro horizontal com barra preta; 3,16 estoura o rosto). Primeiro
`crops` com `at: 0`. Conferência por folha fora do Resolve (nunca still do Resolve). Episódio no mesmo projeto: timeline com
resolução própria 1920×1080 (`useCustomSettings`), senão vira vertical junto com os cortes.

**Cortes saem do episódio EDITADO** (editor 01/11/2026: "é pra usar a versão editada pra pegar os cortes"; o MOV que ele exporta, ex.
`ep 8(edit).mov`): `scripts/cortes_do_editado.py PROJ editado/<arq> r01 …` leva os segs para o tempo do editado (trecho que a cartilha
tirou sai), parte cada trecho em toda troca de câmera (scdet) e dá a cada pedaço o pan do maior rosto; o Daniel tem dois ângulos e
um pan só por trecho deixou ele na borda e a cadeira vazia. **Enquadramento = etapa 2 do padrão CIBO:** `reel-motion/scripts/rastreio.py
<editado> rNN/track.json --a A --b B` e `"track"` no reel.json (keyframes que seguem o rosto no DaVinci); trave as pontas de cada pedaço na
mediana do plano (a suavização desliza entre Daniel e Iully). **Conferência fora do Resolve** (`regras/davinci.md`): folha com o recorte
calculado sobre quadros da fonte; still do Resolve vem do cache e mentiu no EP 10 (pan −400/0/+400 deram o mesmo quadro).

## Regras do cliente (correções do usuário e do Daniel)

- **Tudo no DaVinci, nunca ffmpeg na entrega.** Episódio completo, cortes e versões longas são montados e renderizados no Resolve com o fluxo
  do `reel-motion` (pacote `davinci`, `resolve_render.py`, `resolve_fx.py` para punch-in/zoom no Fusion, `resolve_cores.py`,
  `resolve_mix.py`, `qa_resolve.py`/`qa_render.py`), em projeto novo e organizado (client-router/references/regras/davinci.md → "Projeto
  organizado"). O `make_reels.py`/`render.py` daqui queimam tudo no ffmpeg: use-os só para gerar camadas (legenda com
  alfa, capa) e prévias de conferência, nunca para o MP4 final. ffmpeg fica para análise, extração de áudio e prévia.

- **Punchline no início.** O Daniel (host) pediu: "seria legal já colocar a punch line no
  início do corte". O corte abre com a frase mais forte (gancho nos 3 primeiros segundos),
  mesmo que ela venha do meio do trecho. Pode ser um *cold open* de 1 frase antes do
  contexto, desde que a frase volte inteira e sem corte seco no meio de palavra.
- **7 cortes por episódio (5 do convidado + 2 do host Daniel), sem repetir fala.** Os do Daniel usam a experiência e o olhar dele sobre o tema (ex.: agente
  marítimo na pandemia). Para achar a fala dele, use a câmera: cortina escura atrás dele, parede cinza clara atrás do convidado
  (o áudio é mono duplicado, sem canal por microfone). Capa do Daniel: quadro em que ele sorri. Conte o que já existe e complete. Nenhuma fala pode aparecer em dois cortes. Antes de
  escolher, levante as janelas já usadas (`master_in` + cada `keeps` de cada `job.json`,
  mais os cortes que vieram prontos do Drive) e descarte candidatos que se sobreponham.
- **Pastas dos episódios.** Uma pasta por episódio com o nome do Drive e a numeração
  do YouTube: `content/bombordo/EP NN - Convidado/`, na estrutura da skill `video-project-structure`:
  bruto em `01_sources/masters/`, projeto de edição (job.json, pipeline) em `04_work/`, entregas em
  `06_deliverables/` (episódio, cortes, capas; `_versoes_antigas/`). Pastas antigas `epN`, `CORTES/` e
  `brutos/` não existem mais; o mapa está em `_migracao_2026-10-09.json`. Identifique o episódio pelos
  convidados ou pela duração, nunca só pelo número (arquivos antigos usam epN = EP N-1).
- **Grafia:** "Bombordo e Boreste", com "Bombordo" sempre junto. O Whisper escreve
  "Bom Bordo" ou parte a palavra entre duas cues: as regras de `fix` do `job.json` cobrem
  os dois casos. Copie-as para cada episódio novo e confira nas transcrições entregues.
- **Sempre partir do bruto/master do episódio** em `EP NN - Convidado/01_sources/masters/` (ou o master
  em `04_work/sources/master/`), nunca de um MP4 solto em `~/Movies` (pode ser versão substituída, com a grafia errada).
- **Capa:** a pessoa de frente, olhos abertos e sorriso real (`cover_pick.py --master`).
  A convidada precisa ficar bonita: pode vir de qualquer momento do episódio (`cover_from`).
- **Música a −27 dB** (`mix.music_db`), não −21: "a música tá um pouco muito alta".
- **Entrega:** os cortes vão para `EP NN - Convidado/06_deliverables/cortes/`, sem níveis numerados. Arquivos
  `NN - HEADLINE.mp4`, com acentos, numerados pela ordem em que a fala aparece no
  episódio (ordenar por `master_in`), e a capa `CAPA - NN - HEADLINE.png` (prefixo, para as
  capas ficarem agrupadas no Finder). Grave o nome em `filename` no `job.json`, senão o
  próximo render volta ao nome antigo. Troque `"` por `'` no nome do arquivo.
- **Transcrição sempre com tempo** (`[hh:mm:ss - hh:mm:ss] texto`, blocos de ~20 s, mais
  o SRT). Texto corrido sem tempo o usuário considera inútil. Entregue a de todos os
  episódios do lote.

## Workflow

Before editing, read and update `references/client-content-bible.md` and `references/asset-source-catalog.md`. Use `video-project-structure` to audit the fixed project layout and prevent raw/stock media from entering Drive asset packages.

1. **Read the SRT, not the video.** Collapse it into a readable transcript first:
   group cues into ~15 s blocks and print `[start - end] text`. Pick the clips from
   that. Never scrub the video looking for moments.
2. **Identify host vs guest** from conversational flow (who introduces, who asks,
   who answers) and say so before proposing cuts.
3. **Pick moments** with a hook in the first 3 s, one clear idea, and a closing
   punchline or a cliffhanger question. Target 42–55 s of *kept* audio — the trim
   removes 15–25 % of the raw window, so choose a window ~20 % longer.
4. **Write `job.json`** (see `assets/job.example.json`) with, per clip: `src`,
   `master_in` (its IN point in the master, seconds — used to map SRT cues),
   `headline`, fallback `cropx`, `cover_t`, and `keeps` (list of `[start,end]` in
   *clip-local* seconds). Before rendering, generate and visually review a
   shot-aware `cropx_timeline` with `face_crop.py`; never assume one crop fits every
   camera in a clip.
5. **Polish captions against the real audio (mandatory after any keeps change):**
   ```bash
   JOB=job.json python3 scripts/asr_polish.py --beats
   ```
   Re-transcribes every kept segment with large-v3 AND turbo (no domain prompt —
   a "ports" prompt turned "no ponto" into "no porto"), fixes punctuation/casing,
   drops edge phantoms / adds audible edge words only when both models agree,
   never touches acronyms or `emph` terms (both models hear "CCO" as "social"),
   and re-places clicks/zooms on emphasised captions (they are output-time and go
   stale when keeps move). Everything else lands in `asr_polish_report.json` —
   read it; one-model disagreements are decided by an isolated no-prompt check.
   `make_reels.py` also warns when a `cropx_timeline` change sits just after a
   keep start (the first frames would keep the previous shot's crop — ep4 showed
   an empty shelf for 0.5 s).
   **Caption height:** captions must never cover a face. After the cut exists, run
   `python3 scripts/safe_zone.py <work>/A_<clip>.mp4` and put the returned centre in
   `job.clips.<clip>.cap_cy` (band = cap_cy±210; ep4 landed at 1218–1380, the old
   fixed 1020 sat on chins and beards). Two-line captions use tight leading
   (`LINE_PITCH` in render_caps.py) — the old ascent+descent stacking read as two captions.
   **Cover frame:** run `python3 scripts/cover_pick.py [clip]` and choose `cover_t`
   from `<work>/cover_cands_<clip>.jpg` (frontal, eyes open, composed mouth). A round
   second picked blind landed on profiles, blinks and mid-word mouths.
   The cover must make the guest look good. If every frame inside the cut is a
   profile (ep4: Juliana), take the still from anywhere in the episode — usually the
   guest's introduction, filmed frontal and smiling — with
   `job.clips.<clip>.cover_from = {"src": master, "t": s, "x0": crop x}`; it gets a
   subtle edge-preserving skin/light retouch (`cover_retouch_amount`, default 0.35).
   Find those moments with `python3 scripts/cover_pick.py --master <master.mp4>`
   (genuine smiles: strict smile + teeth + eyes open, whole episode). Approved by the
   client: a real smile with eyes open, or a soft smile in a slight 3/4 turn. Rejected:
   mid-word mouths, raised eyebrows, a serious/sad face, a flat straight-on close-up.
6. **Run it** — gera só camadas (legenda com alfa, capa) e prévias de conferência; o MP4 final sai do DaVinci
   (regra "Tudo no DaVinci" acima). MP4 queimado só se o editor pedir.
   ```bash
   JOB=job.json python3 scripts/make_reels.py            # all clips
   JOB=job.json python3 scripts/make_reels.py corte01    # one clip
   ```

## Referências (abra só quando o gatilho bater)

| Arquivo | Abra se |
|---|---|
| `references/motor.md` | escolher `keeps`, mudar um corte pronto, conferir algo sem render inteiro, regras do motor, música, entregáveis |
| `references/legenda.md` | recorte por plano de câmera, ritmo da legenda, legenda mostrando o que não é ouvido |
| `references/kinetic.md` | legenda animada palavra por palavra (`scripts/kinetic/`) |
| `references/chamada.md` | chamada do episódio (`scripts/chamada.py`) |
| `references/davinci-xml.md` | Histórias do Porto ou qualquer entrega em XML/camadas para o DaVinci |
| `references/historico-falhas.md` | algo falhou: índice de falhas conhecidas e o histórico de cada uma |
| `references/client-content-bible.md` | identidade, tom e convenções do cliente |
| `references/asset-source-catalog.md` | de onde vem cada asset |
| `references/rubrica.md` | avaliar se o corte está no padrão aprovado |
