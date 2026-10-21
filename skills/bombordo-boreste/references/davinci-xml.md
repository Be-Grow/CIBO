# Bombordo — Histórias do Porto → XML para o DaVinci

Movido do SKILL.md em 20/10/2026 (carregar sob demanda). Conteúdo preservado sem cortes.

## Histórias do Porto → XML para o DaVinci (EP 06, 18/10/2026)

O editor prefere fazer o render final no DaVinci: entregue um XML (FCP7) com **cada camada numa
trilha** em vez do MP4 queimado. Scripts prontos em
`scripts/historias_xml/` (cópia do EP 06; README explica a ordem): `componentes.py <historia>` (painéis ProRes
1080x660, legenda ProRes 4444 com alfa, sombra, fade, trilha mixada, capa, `xml_cfg.json`) e
`xml_resolve.py <historia>` (V1 Daniel, V2 painéis, V3 sombra, V4 legenda, V5 burn Screen, V6 fade, V7 capa;
A1 voz, A2/A3 trilha L/R, A4 cliques, A5 whooshes, A6 SFX/bipe). Copie para a história nova e troque `STORIES`.

O que o Resolve 20 faz com XML do FCP7 (medido importando e renderizando pela API, não suposto):
- **Encaixa o clipe na timeline antes do Movimento** ("Scale entire image to fit", o padrão): o bruto
  1920x1080 numa timeline 1080x1920 já entra a 0,5625, então escala do XML = escala desejada / encaixe.
- O centro (`horiz`/`vert`) é fração do **clipe já encaixado** (1080x607 no bruto, 1080x660 num painel).
- O `<when>` de cada keyframe conta do **início da mídia** (soma o `<in>`). Sem isso, os keyframes do
  Daniel (bruto começando em 4:28) caíam fora do clipe e o punch-in e a descida sumiam.
- Recusa a importação inteira se uma trilha de áudio aponta para o áudio do MP4 ("Operation canceled"):
  extraia `voz_bruto.wav`.
- Toda trilha de áudio vira **mono centralizada (−3 dB)**: voz dual-mono numa trilha só (+3 dB no ganho),
  trilha estéreo em duas com `audiopan` −1/+1.
- Teste sempre: projeto "TESTE XML CIBO", `ImportTimelineFromFile` + render 540x960 e folha de quadros.
  Arquivo trocado no mesmo caminho fica em cache no Media Pool (use nome novo para medir de novo).
- A API não cria Adjustment Clip: entregue o LUT (.cube) e o editor aplica.
- **Film burn em Tela pela API (EP 07, 20/10/2026: "vc n colocou o burning como camada screen... resultado, telas pretas").** O Resolve ignora o `<compositemode>screen</compositemode>` do XML do FCP7, e o burn entra em Normal, cobrindo a abertura e o fechamento com preto. Depois de importar, rode `item.SetProperty("CompositeMode", 5)` (5 = COMPOSITE_SCREEN) em todo item `filmburn` e confira se `GetProperty("CompositeMode") == 5` antes de renderizar.
- **`ImportTimelineFromFile` sempre com `importSourceClips: True` (EP 07, 20/10/2026).** Com `False`, a timeline importa sem ligação com o clipe que já está no Media Pool, e o render sai com **Media Offline**. Depois de importar, confira se cada item tem `GetMediaPoolItem()` com "Online Status" igual a "Online", ignorando as transições.
- **Capa pela API (`AppendToTimeline`) não pode ser PNG nem `.mov` de 1 quadro (EP 07, 20/10/2026).** O Resolve trata os dois como still de 5 s e ignora o `endFrame`: a capa entrou com 150 quadros e cobriu o início dos 5 cortes. Use um ProRes de 5 quadros (`ffmpeg -loop 1 -i capa.png -frames:v 5 -r 30 -c:v prores_ks -profile:v 3 "capa ... 5q.mov"`) com `startFrame 0`, `endFrame 1` (`endFrame 0` é recusado), na faixa de cima "CAPA". Depois confira se `GetDuration() == 1`. No XML a capa PNG de 1 quadro funciona, porque lá o in e out é respeitado.

Som do Histórias do Porto: trilha a **−23 dB** (o editor achou −27 baixa), ducking ratio 3; whoosh nas
emendas (nunca no burn de abertura/fechamento) e na entrada/saída dos painéis; os dois cliques alternados; SFX cômico na piada (disco arranhado antes da resposta seca,
grilos no silêncio constrangedor); **palavrão leva bipe** 1 kHz (acervo `bipe-censura`, nível −5 dB,
voz cortada na palavra) e a legenda mostra "c*". Uma gravação de Histórias pode ter duas histórias e
muitas tomadas: use só a última tomada completa de cada uma, mais a vinheta de outra tomada.

**Início de tomada ("pode ir, vai"):** o Daniel dá a deixa antes de começar, e o Whisper engole o "vai" no
"A história" (põe as duas palavras coladas e erra o tempo). Não identifique a sílaba pelo Whisper: no perfil
de energia em 10 ms do `voz_bruto.wav` a sequência é deixa → "vai" → **respiração** (~-40 dB, 0,3 s) →
"A história"; o início vai no vale entre a respiração e o "A" (EP 06: "vai" 205,58–205,72, respiração
205,95–206,25, "A" 206,30 → início 206,267). Mover o início é deslocar **todas** as camadas (edit.json,
words/blocks, `edit_a_fc.txt`, refs/música/SFX em `STORIES`, SRT) e refazer XML e MP4; confira com
correlação do MP4 contra o bruto, não com transcrição (o Whisper "ouve" o "vai" mesmo depois de ele sair).
