// Tudo que muda de uma vinheta para outra fica aqui. Valores atuais = LPA "Caminhos e Visões" (aprovada em 13/10/2026).
// Tempos em segundos vêm de `desenho-de-som/scripts/analisa_trilha.py` (batida, 1º impacto, pausa, impacto grande).
import logo from '../public/logo.json'; // gerado por scripts/prepara_logo.py

export const CFG = {
  fps: 30,
  durSec: 17,
  // cores do manual da marca
  bg: '#0D0C0F',
  accent: '#B59E64',
  accentLight: '#E9D9A6',
  // fontes: sans de apoio em public/ (@font-face); serif de destaque do sistema (Didot ~ IvyPresto)
  sansFile: 'RedHatDisplay-VariableFont_wght.ttf',
  serif: 'Didot, "Bodoni 72", serif',
  // cold open
  name: 'LILIAN PRIMO ALBUQUERQUE',
  // trilha (vinheta-relativo)
  beatSec: 0.859, // 70 BPM
  firstHitSec: 1.5, // painéis entram
  breakSec: 8.5, // pausa da música: painéis viram linha, símbolo se desenha
  logoHitSec: 11.75, // impacto grande: logo completa
  // painéis: [antes da troca, depois da troca] por painel; troca na 2ª batida
  panelsA: [['clip1.mp4', 'clip4.mp4'], ['clip2.mp4', 'clip5.mp4'], ['clip3.mp4', 'clip6.mp4']],
  panelsC: ['clip7.mp4', 'clip8.mp4', 'clip9.mp4'],
  // tela cheia horizontal (16:9 nativo, nunca vertical esticado); shiftX empurra a pessoa para a direita
  wide: {src: 'wide.mp4', shiftX: 300, scale: [1.14, 1.08]},
  // uma palavra por batida a partir da 4ª; "over" = sobretítulo pequeno (mostrado quando muda)
  words: [
    {over: 'CAMINHOS', word: 'Trajetória'},
    {over: 'CAMINHOS', word: 'Escolhas'},
    {over: 'VISÕES', word: 'Propósito'},
  ],
  // logo: parts[0] = símbolo (desenha na pausa); demais entram no impacto
  logo: logo as {srcW: number; srcH: number; pad: number; parts: {file: string; w: number; h: number; top: number; dx: number}[]},
  logoWidth: 1190, // largura na tela da peça mais larga (px)
  look: 'saturate(0.62) contrast(1.08) brightness(0.92) sepia(0.18)', // grade única sobre as imagens
};
