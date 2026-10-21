# Content Hub — regras visuais e técnicas

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Regras visuais e técnicas

Antes do primeiro render em uma máquina ou perfil novo, use a skill `video-render-optimizer`: detecte GPU e encoders FFmpeg, faça benchmark CPU × hardware em 8–15 s do material real e escolha por velocidade, SSIM, compatibilidade e bitrate. Para 1080×1920/30, comece em 6–8 Mb/s com teto de 10 Mb/s; confirme o bitrate real no MP4 final. Não use GPU automaticamente se ela inflar o arquivo ou perder qualidade.

- Toda entrega tem capa. Use `assets/logo_content_hub_transparent.png`, headline coerente com o trecho e Montserrat em CAIXA ALTA. Centralize visualmente a pessoa, preserve olhos/queixo e mova a logo para o lado oposto ao rosto quando necessário.
- A assinatura da capa é exclusiva da Content Hub. Use thumbnails apenas como repertório de composição e compare a direção com o registro de capas dos demais clientes; não reutilize estrutura visual.
- A identidade é azul profundo com acento laranja. Palavras enfatizadas e a barra da capa usam o laranja da marca.
- Legendas têm no máximo 18 caracteres por bloco, até duas linhas, baseline compartilhada e correção manual do português.
- Lettering não é legenda ampliada. Use Montserrat ExtraBold/Black, card azul profundo, acento laranja e popup eased curto no canto inferior esquerdo ou em outra área negativa segura. Mostre de uma a duas peças por corte, sincronizadas a números, contrastes ou teses, sem cobrir rosto ou legenda. O card deve medir o texto, ampliar largura/altura e quebrar linhas automaticamente; nunca trate `width` como caixa de corte. Bloqueie o render se qualquer glyph sair da safe box ou se a posição renderizada divergir de `side`/`y` do job.
- O enquadramento é vertical 1080×1920, consciente das trocas de câmera e centrado no convidado.
- Clicks e movimentos marcam poucos pontos semânticos. Não aplique click na palavra de abertura.
- Música precisa ser licenciada/aprovada, ficar abaixo da fala e usar ducking. Faça um brief e uma escolha independentes para cada corte, incluindo assunto, subtexto, arco emocional, energia, velocidade da fala, duração e objetivo. Compare 3–5 candidatas no trecho real, selecione também um `music_offset` que comece em uma seção útil e registre a decisão; nunca escolha apenas pelo gênero ou por audição isolada.
- B-roll precisa passar por validação semântica: leia a oração completa e pelo menos uma frase antes/depois, classifique usos literais e figurativos, descreva em uma frase o que a imagem prova e rejeite correspondência baseada apenas em palavra-chave. Se a imagem estreitar, contradizer ou banalizar a tese, use talking head ou lettering.
- No split-screen, não use headline entre os painéis. O B-roll ocupa o topo; o talking head fica abaixo na escala original. A emenda tem blur real estreito e somente uma borda inferior azul semitransparente. Entrada e saída usam film burn, nunca fade.
- Preserve `setsar=1`, blend em RGB, limiter com `level=false` e o fluxo de cor + matte H.264 para transparência das legendas.
- Preserve e sinalize Rec.709 (`color_range=tv`, `colorspace`, `color_primaries` e `color_trc` em `bt709`). Use grade por plano: recupere detalhe nas sombras sem lavar pele nem transformar roupa preta em cinza; controle saturação de fundos laranja/azul e revise a luminância do rosto.
- No talking head, o rosto é a âncora. Introduza mudança visual útil a cada novo bloco de raciocínio, normalmente a cada 3–6 s: palavra enfatizada, zoom eased, card numérico, recorte, documento ou B-roll licenciado. Não cubra o rosto por longos períodos e não force B-roll quando a fala já é visualmente suficiente.
- Use no máximo 2–3 acentos sonoros principais por minuto. Clicks marcam palavras ou números; whooshes acompanham movimentos longos; pops graves ficam reservados a dados ou conclusões. Evite clusters e nunca aplique SFX na palavra de abertura.
- As referências editoriais (Cleo Abram, Codie Sanchez, Hayden Hillier-Smith, Jordan Orme, Johnny Harris, Rafael Gratta, Anderson Gaveta, Pedro Loos, Fill Rocha e Olga Lehnerg) orientam clareza, ritmo e hierarquia, não cópia de identidade ou reutilização de trechos.
- Não adicione patrocinador, linguagem clínica, elementos náuticos ou assinatura herdada dos outros clientes sem material explícito do job.
