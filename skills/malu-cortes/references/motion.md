# Malu — kit de motion

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Kit de motion

Toda animação usa **ease in e ease out como no Premiere** (`cubic-bezier(0.33, 0, 0.67, 1)` ou mais suave), **sem spring e sem overshoot**, com **motion blur de câmera em shutter angle 360°** em tudo o que se move. Os gráficos são renderizados em camada transparente (skill `motion-graphics` com Remotion quando disponível, exportando ProRes 4444 ou WebM com alfa) e compostos pelo `render.py`.

- **Câmera que respira**: em plano longo sem zoom, push-in lento de 2 a 3% ao longo do plano. Nada fica 100% parado.
- **Zooms**: o estilo aprovado do fluxo (item 8), variando entre punch-in e push-in.
- **Título de gancho**: 1 a 2 linhas em Montserrat, revelado por máscara com blur, sai com fade e blur antes de 2,5 s.
- **Lower third** na primeira aparição da Malu: nome e função (pergunte o texto ao usuário), entrada suave, sai em 3 s.
- **Números e prazos** ("40 dias"): número grande animado por 1 a 1,5 s.
- **Linhas de produto** (premium, gold, silver, standard): callout ou lista animada quando ela compara. Mostre só o que ela afirma; ela troca os nomes às vezes (ver bíblia).
- **Transições de referência**: varie entre tela dividida com deslize, tela cheia com push lento e card flutuante com cantos arredondados e sombra suave.
- **Troca de layout nunca em corte seco** ("deixa o vídeo feio e amador"): film burn vermelho do arquivo do usuário (`scripts/burn.py`, `burn_events`, `burn: true`) com o pico de luz exatamente no corte, em toda saída de tela dividida/card/tela cheia e em toda entrada de tela cheia; alterne os burns B9, B13, B10, B12 e B4. A tela dividida entra com deslize e o card com a própria animação. O som do burn vai para a trilha de SFX (evento com `src`). Jump cut com troca de nível dentro da mesma fala continua seco.
- **Encerramento**: o último quadro dela desfoca em fade (`malu_refs` `endbg`), a música termina no fim natural e o vídeo sai em fade. **Sem cartão final de produto e sem card com o recorte dos pacotes Turi-Ita**: o usuário reprovou os dois em todos os cortes (o recorte fica mole ampliado).
- **Unidade visual**: grão de filme bem sutil e o mesmo tratamento de cor sobre tudo (câmera, referências e gráficos), para colar as fontes diferentes.
- **Proibido**: shake, glitch, transições de template, emojis, cores fora da paleta da bíblia. Exceção pedida pelo usuário: o film burn vermelho nas trocas de layout.
