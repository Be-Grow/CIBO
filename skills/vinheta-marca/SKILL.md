---
name: vinheta-marca
description: Crie vinhetas, intros e aberturas de marca profissionais (programa, podcast, canal, palestrante) em Remotion a partir do manual de identidade, da logo e de imagens da pessoa — cold open com o nome, painéis verticais com a pessoa no ritmo da música, tela cheia com palavras da marca, linha que vira a revelação, símbolo se desenhando na pausa da trilha e logo completa no impacto, com partículas, brilho e fade. 16:9 em 1080p e 4K, master ProRes. Use quando pedirem vinheta, intro, abertura, sting de logo ou logo animada; o som é feito com a skill desenho-de-som.
---

# Vinheta de marca

Padrão aprovado na vinheta LPA "Caminhos e Visões" (13/10/2026). A v1 (6 s, só SFX, borda no glow
da logo) foi reprovada; a v2 (17 s, trilha marcante, SFX em cada evento) foi aprovada: "o motion e a
escolha do SFX junto com a música ficou muito bom". Caso completo: `references/caso-lpa.md`.

## Fluxo

1. `client-router` → cliente; `video-project-structure` (01_fontes, 04_work, 06_entregas, 07_manifests).
   Zip do Drive: extraia com `ditto -x -k` (o `unzip` quebra nome com acento). Espere downloads `.download` terminarem.
2. **Leia o manual da marca** (`pdftoppm -r 25` + uma folha de contato): cores (hex), fontes, versões da logo,
   frases/conceitos ("Caminhos → trajetória, escolhas"; "Visões → propósito"). Fonte da marca indisponível:
   serif de alto contraste do sistema (Didot / Bodoni 72) no destaque, a sans de apoio do manual em `public/`.
3. **Pergunte só o que o manual não responde:** formato (16:9 é o padrão para YouTube/podcast; 9:16 exige refazer o layout),
   conceito (pessoa + logo é o padrão) e duração. **Padrão: 15–17 s com trilha marcante**, nunca 6 s só com SFX.
4. **Projeto:** copie `assets/template` para `04_work/mg` e ligue o `node_modules` de um projeto que já tenha
   Remotion 4.0.535 (`ln -s ".../priscilla daher/04_work/mg/node_modules" node_modules`) ou rode `npm i`.
5. **Logo:** `python3 scripts/prepara_logo.py LOGO_HORIZONTAL.png 04_work/mg/public` (faixas com margem
   transparente + `logo.json`). Use a versão horizontal colorida (símbolo em cima, nome numa linha, assinatura).
6. **Trilha e tempos:** skill `desenho-de-som` → `analisa_trilha.py --alvo 11.75` dá batida, 1º acento, pausa e
   impacto. Copie para `config.ts` (`beatSec`, `firstHitSec`, `breakSec`, `logoHitSec`, `durSec`).
7. **Takes:** `scripts/clipes.py cortes FONTE` (cortes de cena dos teasers), `clipes.py folha FONTE t1 t2 ...`
   (uma folha por decisão) e `clipes.py extrai lista.txt public`. São 9 takes verticais (6 na 1ª leva com troca, 3 na 2ª),
   rosto da pessoa dominando o quadro (descarte quadro com outra pessoa em destaque, flare estourado ou produto),
   e 1 take horizontal nativo para a tela cheia (`wide`). Câmera com zoom no meio: janela estável + `lento` (fonte 60 fps).
8. **config.ts:** cores, nome do cold open, takes, palavras do manual (uma por batida), `wide.shiftX` (pessoa à direita,
   texto à esquerda), `logoWidth`, `look` (grade única que iguala eventos de cores diferentes).
9. **Stills antes do render**, uma folha: `for fr in 20 60 110 160 190 235 258 300 345 356 420 470; do npx remotion still src/index.ts Vinheta out/s$fr.jpg --frame=$fr --image-format=jpeg; done`.
   Confira se o rosto está inteiro em cada painel e na tela cheia, se as palavras estão legíveis e se a logo não tem borda.
10. **Som:** `desenho-de-som/scripts/deixas_vinheta.py` com os mesmos tempos → `mix.py deixas.json som.wav`.
11. **Render:** `npx remotion render src/index.ts Vinheta out/v.mov --codec=prores --prores-profile=hq`; **4K:** o mesmo com
    `--scale=2` (3840x2160 redesenhado, logo e texto nítidos; os takes 1080p ficam um pouco mais macios).
    **Curta (sting de ~7,7 s, meio/fim de episódio):** `npx remotion render src/index.ts VinhetaCurta out/curta.mov --codec=prores --prores-profile=hq`
    (começa 2,5 s antes do impacto, com o símbolo se desenhando).
12. **Entrega + QA num comando:** `python3 scripts/entrega.py PROJETO "Vinheta - Marca" --video out/v.mov --som som.wav
    --video4k out/v4k.mov --curta out/curta.mov --curta-ini <(impacto - 2,5)>` → MP4 H.264 + master ProRes de cada uma,
    a versão anterior vai para `04_work/vN`, e o QA sai em `04_work/qa`.
13. **QA:** folha a cada 0,5 s, `blackdetect` (o 1,5 s inicial escuro é o cold open, é proposital), recorte ampliado da
    logo com `eq=gamma=1.8` (borda de glow aparece aí), perfil e LUFS do som. Uma versão em `06_entregas`; a anterior vai para `04_work/vN`.
    Anote o que foi feito em `07_manifests/brief.md`.

## Estrutura (17 s a 30 fps; tempos derivados da trilha)

| Tempo | Bloco | Motion |
|---|---|---|
| 0–1,5 s | cold open | constelação do manual surge, flare dourado atravessa, nome com tracking fechando + blur→nítido |
| 1º acento | painéis A | 3 painéis verticais (596 px, vão 26) entram de baixo com clip-path, stagger de 3 quadros, borda dourada 1,5 px, push-out 1,16→1,04 |
| +2 batidas | troca | cada painel troca de take com 3 quadros de defasagem e um flash rápido |
| +4 batidas | tela cheia | take horizontal com degradê preto à esquerda; sobretítulo sans espaçado + palavra serif itálica dourada, 1 por batida |
| +7 batidas | painéis C | 3 takes novos; fecham em direção ao centro logo antes da pausa |
| pausa | suspense | linha dourada se abre e some; o símbolo se desenha devagar (máscara) com glow crescente, centralizado |
| impacto | revelação | clarão, símbolo sobe com spring, nome entra do centro (scaleX 1,12→1 + blur), assinatura em seguida, explosão de 46 partículas, tremor de 12 quadros |
| +1,6 s | brilho | faixa de luz atravessa símbolo e nome; push 1→1,045 até o fim |
| últimos 0,7 s | fade | fade para o preto |

## Regras que custaram retrabalho

- **Glow/blur/drop-shadow na logo:** PNG com margem transparente (o `prepara_logo.py` faz isso) e o `drop-shadow` num wrapper,
  nunca no elemento com `mask-image`. Senão aparece um retângulo em volta do símbolo.
- Takes verticais nunca esticados para tela cheia 16:9: use painéis. A tela cheia é só com fonte horizontal nativa.
- Teaser já editado: escolha a janela entre dois cortes de cena (`clipes.py cortes`), senão o take pula no meio do painel.
- Grade única (`look` + soft-light na cor da marca + degradê) para eventos com cores diferentes parecerem um material só.
- Todo valor animado é função do frame (`interpolate` com clamp, `spring`, `random(seed)`): nada de CSS transition ou `Math.random`.
- Disco: ProRes HQ 1080p de 17 s ≈ 290 MB e 4K ≈ 1,2 GB. Confira `df -h` antes.

## Autoteste

`python3 scripts/autoteste.py` (sintético, ~10 s): recorte da logo em faixas com margem, detecção de corte de cena
e aviso de janela cruzando o corte. O template foi validado contra a vinheta LPA aprovada (mesmos quadros).
