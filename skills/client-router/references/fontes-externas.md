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
| Projeto editável Premiere Pro + DaVinci Resolve (XML do FCP7) | kvrancic/oneshot-video (MIT) | `podcast-reels/scripts/projeto_nle.py` — sempre oferecer, gerar só sob pedido; falta o editor confirmar a importação nos dois programas |
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
