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
};
export const C0 = {...C}, T0 = JSON.parse(JSON.stringify(T));
export const applyTheme = (th?: Theme) => {
  Object.assign(C, C0, th?.colors || {});
  const d = JSON.parse(JSON.stringify(T0));
  Object.assign(T, d, th || {}, {
    title: {...d.title, ...(th?.title || {})}, caption: {...d.caption, ...(th?.caption || {})},
    label: {...d.label, ...(th?.label || {})}, accent: {...d.accent, ...(th?.accent || {})}, fonts: th?.fonts || d.fonts,
    layout: {...d.layout, ...(th?.layout || {})},
  });
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
export const OUT = Easing.bezier(0.22, 0.61, 0.36, 1);
export const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const SPLIT = 940;      // altura de desenho do painel (os painéis são desenhados em 1080×940 e escalados para layout.splitH)

export type Panel = {type: string; s: number; e: number; [k: string]: any};
export type PanelProps = {p: Panel; t: number};

export const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return f / fps;
};
export const ramp = (t: number, a: number, d: number, ease = EASE) => interpolate(t, [a, a + d], [0, 1], {...cl, easing: ease});

