import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

// Tema: cores, fontes e estilo de texto vêm de props.theme (temas/<cliente>.json); o padrão é o da Priscilla.
// Papéis das cores: paper/paper2 = fundo do painel; ink/ink2 = texto no painel; terra = destaque; peach = destaque sobre vídeo;
// white = superfície de card (contraste com ink); video = texto sobre o vídeo; onAccent = texto sobre o destaque; pill = pílula clara.
export const C: Record<string, string> = {
  paper: '#F2ECE4', paper2: '#E9E1D6', ink: '#2B2522', ink2: '#6E625B',
  terra: '#D9694A', terraDark: '#B9533A', peach: '#FFC7A8', white: '#FFFBF5',
  video: '#FFFBF5', onAccent: '#FFFBF5', pill: 'rgba(255,251,245,0.92)', bg: '#0f0d0c',
  shadow: '43,37,34', scrim: '15,13,12',   // r,g,b das sombras dos cards e do escurecimento sobre o vídeo (antes fixos no marrom da Priscilla)
};
type FontSpec = {family: string; file: string; weight?: string; style?: string};
export type Theme = {
  colors?: Partial<typeof C>;
  fonts?: FontSpec[];
  title?: {family?: string; weight?: number; upper?: boolean; ls?: number; scale?: number};
  caption?: {family?: string; weight?: number; upper?: boolean; ls?: number; scale?: number};
  label?: {family?: string; weight?: number};
  accent?: {family?: string; italic?: boolean; weight?: number};
  mediaFilter?: string; burnFilter?: string; burnOpacity?: number; grain?: number;
  // splitH = altura do painel (940 = metade; 768 = 40/60); camShift = quanto a pessoa desce na tela dividida;
  // capSplitY = legenda da tela dividida sobre o vídeo nessa altura (senão fica no rodapé do painel); capMaxW = largura máxima (zona segura)
  layout?: {splitH?: number; camShift?: number; capSplitY?: number; capFullY?: number; capMaxW?: number; autoTags?: boolean};
  // versão horizontal 16:9 (composição ReelH, Andreia 19/10/2026): painel à esquerda com largura panelW, pessoa à direita;
  // capY = linha da legenda; capSize = corpo da legenda; hookScale = escala do gancho/títulos em relação ao vertical
  layoutH?: {panelW?: number; capSplitY?: number; capFullY?: number; capSize?: number; hookScale?: number};
  // jeito de mexer do cliente (20/10/2026, pedido do editor para subir a qualidade do motion): perfil = atual | editorial | premium | energetico
  // (ver PERFIS); os campos soltos sobrescrevem o perfil. Sem motion no tema = "atual" (sai idêntico ao motor de antes).
  motion?: {perfil?: string; enter?: number[]; dur?: number; overshoot?: number; reveal?: 'bloco' | 'palavra'; stagger?: number; settle?: number; ambient?: number};
};
export const T = {
  fonts: [
    {family: 'ISerif', file: 'fonts/InstrumentSerif-Regular.ttf', style: 'normal'},
    {family: 'ISerif', file: 'fonts/InstrumentSerif-Italic.ttf', style: 'italic'},
    {family: 'MSans', file: 'fonts/Montserrat-SemiBold.ttf', weight: '600'},
    {family: 'MSans', file: 'fonts/Montserrat-Regular.ttf', weight: '400'},
  ] as FontSpec[],
  title: {family: 'ISerif', weight: 400, upper: false, ls: 0, scale: 1},
  caption: {family: 'ISerif', weight: 400, upper: false, ls: 0, scale: 1},
  label: {family: 'MSans', weight: 600},
  accent: {italic: true, weight: 400} as {family?: string; italic: boolean; weight: number},
  mediaFilter: 'saturate(0.88) sepia(0.10) contrast(1.03) brightness(0.98)',
  burnFilter: 'sepia(0.55) saturate(1.6) hue-rotate(-12deg) brightness(1.05)', burnOpacity: 0.85, grain: 0.08,
  layout: {splitH: 940, camShift: 600, capSplitY: 0, capFullY: 1300, capMaxW: 0, autoTags: false} as {splitH: number; camShift: number; capSplitY: number; capFullY: number; capMaxW: number; autoTags: boolean},
  motion: {perfil: 'atual'} as Required<Theme>['motion'],
  layoutH: {panelW: 1040, capSplitY: 968, capFullY: 950, capSize: 54, hookScale: 0.66} as {panelW: number; capSplitY: number; capFullY: number; capSize: number; hookScale: number},
};
export const C0 = {...C}, T0 = JSON.parse(JSON.stringify(T));
export const applyTheme = (th?: Theme) => {
  Object.assign(C, C0, th?.colors || {});
  const d = JSON.parse(JSON.stringify(T0));
  Object.assign(T, d, th || {}, {
    title: {...d.title, ...(th?.title || {})}, caption: {...d.caption, ...(th?.caption || {})},
    label: {...d.label, ...(th?.label || {})}, accent: {...d.accent, ...(th?.accent || {})}, fonts: th?.fonts || d.fonts,
    layout: {...d.layout, ...(th?.layout || {})}, layoutH: {...d.layoutH, ...(th?.layoutH || {})},
  });
  const pf = PERFIS[th?.motion?.perfil || 'atual'] || PERFIS.atual;
  M = {...pf, ...(th?.motion || {})} as typeof M;
  OUT_ = Easing.bezier(...(M.enter as [number, number, number, number]));
};
export const q = (f: string) => `'${f}'`;
export const sh = (a: number) => `rgba(${C.shadow},${a})`, scr = (a: number) => `rgba(${C.scrim},${a})`;
// parte isolada de um painel para o DaVinci (props.part, 17/10/2026: "não tá separando os elementos"): cada título, item,
// linha e risco vira um arquivo. <Pt k="item0">…</Pt> esconde (sem tirar do layout) tudo que não é a parte pedida.
let PART: string | null = null;
export const setPart = (k?: string | null) => { PART = k ?? null; };
export const Pt: React.FC<{k: string; children: React.ReactNode}> = ({k, children}) =>
  React.createElement('div', {style: {display: 'contents', visibility: PART === null || PART === k ? 'inherit' : 'hidden'}}, children);
// texto de título/painel (serifa na Priscilla, Montserrat Black em caixa alta no João); size é escalado pelo tema
export const fTitle = (size?: number): React.CSSProperties => ({fontFamily: q(T.title.family), fontWeight: T.title.weight,
  textTransform: T.title.upper ? 'uppercase' : 'none', letterSpacing: T.title.ls, ...(size ? {fontSize: size * T.title.scale} : {})});
export const z = (size: number) => size * T.title.scale;
export const fAcc = (): React.CSSProperties => ({...(T.accent.family ? {fontFamily: q(T.accent.family)} : {}),
  ...(T.accent.italic ? {fontStyle: 'italic'} : {fontStyle: 'normal', fontWeight: T.accent.weight})});
export const fLab = (): React.CSSProperties => ({fontFamily: q(T.label.family), fontWeight: T.label.weight});
export const fCap = (): React.CSSProperties => ({fontFamily: q(T.caption.family), fontWeight: T.caption.weight,
  textTransform: T.caption.upper ? 'uppercase' : 'none', letterSpacing: T.caption.ls});
export const EASE = Easing.bezier(0.33, 0, 0.67, 1);
// Perfis de movimento (princípios de animação, 20/10/2026):
// enter = curva de entrada (desacelera até parar: começo rápido, pouso suave); dur = escala das durações;
// overshoot = quanto do "passa do ponto e volta" dos elementos com quique fica (0 = nenhum: conteúdo sério/bem-estar
// com quique parece brinquedo); reveal = título inteiro ou palavra por palavra subindo de trás de uma máscara;
// stagger = segundos entre palavras/itens; settle = atraso do detalhe que assenta depois do elemento principal
// (subtítulo do card); ambient = intensidade do fundo vivo (gradiente que deriva devagar, 0 = desligado).
const PERFIS: Record<string, {enter: number[]; dur: number; overshoot: number; reveal: 'bloco' | 'palavra'; stagger: number; settle: number; ambient: number}> = {
  atual:      {enter: [0.22, 0.61, 0.36, 1], dur: 1,    overshoot: 1,   reveal: 'bloco',   stagger: 0,    settle: 0,    ambient: 0},
  editorial:  {enter: [0.3, 0, 0.15, 1],     dur: 1.15, overshoot: 0,   reveal: 'palavra', stagger: 0.07, settle: 0.09, ambient: 1},
  premium:    {enter: [0.4, 0, 0.2, 1],      dur: 1.2,  overshoot: 0,   reveal: 'palavra', stagger: 0.08, settle: 0.1,  ambient: 0.7},
  energetico: {enter: [0.16, 1, 0.3, 1],     dur: 0.8,  overshoot: 1.3, reveal: 'palavra', stagger: 0.045, settle: 0.05, ambient: 0},
};
export let M = {...PERFIS.atual};
let OUT_ = Easing.bezier(0.22, 0.61, 0.36, 1);
export const OUT = (x: number) => OUT_(x);
// curva com quique (y1 > 1 passa do ponto): o perfil escala o quique; sem quique vira a curva de entrada do perfil
export const pop = (y1: number) => {
  const k = 1 + (y1 - 1) * M.overshoot;
  return k <= 1.001 ? OUT : Easing.bezier(0.3, k, 0.5, 1);
};
export const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const SPLIT = 940;      // altura de desenho do painel (os painéis são desenhados em 1080×940 e escalados para layout.splitH)

export type Panel = {type: string; s: number; e: number; [k: string]: any};
export type PanelProps = {p: Panel; t: number};

export const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return f / fps;
};
export const ramp = (t: number, a: number, d: number, ease = EASE) => interpolate(t, [a, a + d * M.dur], [0, 1], {...cl, easing: ease});

