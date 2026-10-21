# Fontes externas avaliadas (skills de vídeo de terceiros)

Pente fino feito em 12/10/2026 em `freshtechbro/claudedesignskills` e
`zhuyansen/awesome-claude-video-skills` (283 projetos; lidos a fundo ~25). Ideias e números
foram adaptados com crédito; código de terceiro só entra se a licença permitir (MIT/Apache ok;
AGPL e sem licença, não).

## Adotado

| Fonte | Licença | O que entrou | Onde |
|---|---|---|---|
| kvrancic/oneshot-video | MIT | doutrina de seleção de momentos; checagem de começo/fim do corte; níveis e densidade de SFX; limpeza de voz por SNR; latência do afftdn/arnndn; áreas seguras e regras de legenda | podcast-reels (Escolha dos momentos, `checa_cortes.py`), fala-limpa, regras transversais |
| kmilo93sd/agent-video-editor | MIT (sons CC0) | 128 sons/músicas CC0 medidos; tempos de grafismo e leitura; níveis de trilha/SFX | acervo (`cc0-*`), lettering-motion |
| kurbaitaev/ghost-editor | MIT | calibração de ritmo (corte seco, plano ~3 s, SFX 0,4–0,9/10 s, punch-in ≤ 3); aviso de Content ID | regras transversais |
| louisedesadeleer/cut-video | MIT | alarme de palavra esticada; limiar de silêncio relativo ao ruído; tabela de ritmo | fala-limpa (`audit_fala.py`), briefing (ritmo) |
| iart-ai/motion-design-skills | MIT | curvas e durações de entrada/saída/pop; escalonamento; contenção | lettering-motion |
| Tejashmakwana/motionmaxxing | Apache-2.0 | leis de ofício (entrada desacelerando, uma mola por peça, quase nada por fade, palavras no ritmo da fala, "nunca entregar", checagens) | lettering-motion |
| IskakovDamir/apple-motion | MIT | mola calibrada (15,35/115), entrada em ~8 quadros, saída por corte | lettering-motion, template |
| remotion-dev/skills | sem licença (oficial) | guias usados como referência local, não copiados para o CIBO | `~/.cibo/vendor/remotion-skills`, lettering-motion |
| hassancs91/claude-youtube-editor | MIT | teste A/B/C de capa no YouTube; ganho extra para SFX percussivo | seo-youtube-podcast |

## Adotado depois (12/10/2026, "faça todos")

| Ideia | Fonte | Onde ficou |
|---|---|---|
| Projeto editável Premiere Pro + DaVinci Resolve (XML do FCP7) | kvrancic/oneshot-video (MIT) | `podcast-reels/scripts/projeto_nle.py` — sempre oferecer, gerar só sob pedido; no Resolve 20 o encaixe automático, o centro relativo ao clipe encaixado, o `<when>` com o `<in>` e o áudio de MP4 quebram este gerador: use as regras validadas em `bombordo-boreste/references/davinci-xml.md`, seção "XML para o DaVinci" |
| MFA (tempo exato de palavra, português) | louisedesadeleer/cut-video | `fala-limpa/scripts/alinha_mfa.py`, instalado no SSD |
| Lottie no Remotion | remotion-dev/skills, diffusionstudio/lottie | `lettering-motion` template `LottieOverlay`, acervo `--type lottie` |
| Variações de gancho + checagem AVFoundation | krusemediallc/video-editor-agent | `podcast-reels/scripts/variacoes_gancho.py`, `av_check.swift` |
| Audiograma | iart-ai/youtube-video-skills | `lettering-motion/scripts/audiograma.py`, composição `Audiogram` |
| Presets de legenda por conteúdo | kvrancic/oneshot-video captions.md | `podcast-reels` `CAP_PRESET` (veredito, historia, aula) + `EMPH_MAX` |
| Estilo de um reel de referência | edenfunf/reelmimic, krusemediallc | `briefing-criativo/scripts/analisa_referencia.py` |

## Ainda não feito

- Legenda "diálogo" (duas pessoas, lados opostos) e "epígrafe": precisam de layout novo no `render_caps`.
- Catálogo de costuras por velocidade (zoom-through, rack-focus) do reelmimic `cut-the-curve`.
- Triagem de takes por visão (Fagan1024/smart-video-editor) para gravações com vários takes (Katia).
- Migrar Bombordo, Autismo Cast e Content Hub para o motor único (sessão própria).

## Descartado

Web/3D interativo (claudedesignskills: Framer Motion, GSAP de rolagem, Three.js, WebXR): roda em
tempo real no navegador, incompatível com render quadro a quadro. Avatares/IA generativa, vídeo
explicativo com narração sintética, recaps em chinês: fora do tipo de trabalho do CIBO.
OpenMontage, OpenChatCut, Montara (AGPL): não copiar código.

## Rodada de 20/10/2026 (qualidade criativa: gancho, ritmo, variação)

Clones rasos em `~/.cibo/vendor/<dono>_<repo>`. Nenhum código copiado; só ideias e números.

| Fonte | Licença | Aproveitado | Onde |
|---|---|---|---|
| SamurAIGPT/AI-Youtube-Shorts-Generator | MIT | gancho nos 3 primeiros s; nunca cortar no meio da frase; não completar o lote com clipe fraco; justificativa por clipe | `gancho-e-ritmo` (gancho, final) |
| FujiwaraChoki/supoclip | **AGPL-3.0 — só ideias** | notas por dimensão com justificativa; tipo de gancho (pergunta, afirmação, número, história, contraste, nenhum); histórico do criador só como desempate | `gancho-e-ritmo` (tipo de gancho), `rubrica.md` |
| mutonby/openshorts | MIT | push-in ≤12 % com curva assimétrica e intervalo mínimo entre pushes; "crop estático longo é o vídeo menos editado" | `gancho-e-ritmo` (tempo morto visual), `variacao.py` |
| browser-use/video-use | MIT | self-eval nos cortes e nos 2 s de início/fim; crítico com problemas ranqueados por timecode e as 5 primeiras correções; no máximo 3 passes; memória por projeto; anti-padrão "SFX em toda transição" | `gancho-e-ritmo` (relatório), `licoes.md`, `variacao.py` |
| SysAdminDoc/OpenCut | MIT | ranking de takes repetidos (completude, muleta, estabilidade de ritmo ±35 % da mediana, duração); muletas seguras × dependentes de contexto; ducking attack 20 ms / release 300 ms | `gancho-e-ritmo` (variação de ritmo); candidato para `fala-limpa` |
| digitalsamba/claude-code-video-toolkit | MIT | perfil de marca em JSON separado do motor; projeto multi-sessão com histórico | confirma `temas/<cliente>.json`; `licoes.md` |

Descartado: gancho reescrito por LLM (o CIBO só usa a fala real), efeitos por batida estilo clipe musical, reframe automático.
