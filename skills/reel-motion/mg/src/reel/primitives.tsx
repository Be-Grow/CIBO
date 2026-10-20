import React, {useEffect, useState} from 'react';
import {
  Img, AbsoluteFill, Easing, OffthreadVideo, Sequence, continueRender, delayRender, interpolate,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import {C, T, SPLIT, Panel, PanelProps, fTitle, z, fAcc, fLab, fCap, EASE, OUT, cl, ramp, useT, sh} from './theme';

// Peças reutilizáveis dos painéis. Painel novo = composição destas peças; só crie peça nova quando nenhuma serve.

export const Fonts: React.FC = () => {
  const [h] = useState(() => delayRender('fontes'));
  useEffect(() => {
    const list = T.fonts.map((f) => new FontFace(f.family, `url(${staticFile(f.file)})`, {weight: f.weight ?? 'normal', style: f.style ?? 'normal'}));
    Promise.all(list.map((f) => f.load())).then((fs) => {
      fs.forEach((f) => (document.fonts as any).add(f));
      continueRender(h);
    });
  }, [h]);
  return null;
};

// filtro de blur só na vertical, proporcional à velocidade (motion blur da troca de layout)
// x = blur na horizontal (troca de layout lado a lado da versão 16:9)
export const VBlur: React.FC<{id: string; amount: number; x?: boolean}> = ({id, amount, x}) => (
  <svg width="0" height="0" style={{position: 'absolute'}}>
    <filter id={id} x={x ? '-20%' : '0'} y={x ? '0' : '-20%'} width={x ? '140%' : '100%'} height={x ? '100%' : '140%'}>
      <feGaussianBlur stdDeviation={x ? `${amount.toFixed(2)} 0` : `0 ${amount.toFixed(2)}`} />
    </filter>
  </svg>
);

export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.06}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'overlay', opacity}}>
      <svg width="100%" height="100%">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 12} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};

// ---------- peças do painel ----------
export const Pill: React.FC<{text: string; p: number; dark?: boolean; size?: number; style?: React.CSSProperties}> = ({text, p, dark, size = 30, style}) => (
  <div style={{
    display: 'inline-block', padding: `${size * 0.42}px ${size * 0.9}px`, borderRadius: 999,
    background: dark ? C.terra : C.pill, color: dark ? C.onAccent : C.ink,
    ...fLab(), fontSize: size, letterSpacing: 2.2, textTransform: 'uppercase',
    opacity: p, transform: `translateY(${(1 - p) * 18}px)`, filter: `blur(${(1 - p) * 6}px)`,
    boxShadow: `0 10px 30px ${sh(0.18)}`, whiteSpace: 'nowrap', ...style,
  }}>{text}</div>
);

export const MediaFrame: React.FC<{src: string; t: number; s: number; e: number; from?: number; children?: React.ReactNode; height?: number}> = ({src, t, s, e, from = 0, children, height = 590}) => {
  const {fps} = useVideoConfig();
  const push = interpolate(t, [s, e], [1.0, 1.07], cl);
  const inP = ramp(t, s, 0.5, OUT);
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: 170, height, borderRadius: 34, overflow: 'hidden',
      boxShadow: `0 30px 60px ${sh(0.22)}`, opacity: inP, transform: `scale(${0.97 + 0.03 * inP})`}}>
      <Sequence from={Math.round(s * fps)} layout="none">
        <OffthreadVideo src={staticFile(src)} muted startFrom={Math.round(from * fps)}
          style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${push})`,
            filter: T.mediaFilter}} />
      </Sequence>
      {children}
    </div>
  );
};

export const Title: React.FC<{text: React.ReactNode; p: number; size?: number; top: number; color?: string; align?: 'center' | 'left'}> = ({text, p, size = 92, top, color = C.ink, align = 'center'}) => (
  <div style={{position: 'absolute', top, left: 70, right: 70, textAlign: align, ...fTitle(), fontSize: size,
    lineHeight: 1.02, color, opacity: p, transform: `translateY(${(1 - p) * 30}px)`, filter: `blur(${(1 - p) * 10}px)`}}>{text}</div>
);
export const I: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = C.terra}) => (
  <span style={{...fAcc(), color}}>{children}</span>
);

// 1) autoridade: corredor + contador + pílulas

// ---------- peças genéricas (13/10/2026) ----------

// número que conta de `from` para `to` a partir de `at`; `steps` faz pular por valores ditos ([4, 12])
export const Counter: React.FC<{t: number; at: number; from: number; to: number; dur?: number; steps?: {at: number; v: number}[];
  size?: number; color?: string; suffix?: string}> = ({t, at, from, to, dur = 0.9, steps, size = 260, color = C.ink, suffix}) => {
  let v = Math.round(interpolate(t, [at, at + dur], [from, to], {...cl, easing: OUT}));
  let kick = 0;
  if (steps && steps.length) {
    const cur = [...steps].reverse().find((s) => t >= s.at);
    const prev = cur ? steps[steps.indexOf(cur) - 1] : undefined;
    v = cur ? Math.round(interpolate(t, [cur.at, cur.at + dur], [prev ? prev.v : from, cur.v], {...cl, easing: OUT})) : from;
    kick = cur ? Math.sin(Math.PI * ramp(t, cur.at, 0.35)) : 0;
  }
  return <span style={{...fTitle(size), color, display: 'inline-block', lineHeight: 0.9, transform: `scale(${1 + 0.08 * kick})`,
    fontVariantNumeric: 'tabular-nums'}}>{v}{suffix ? <span style={{fontSize: '0.45em'}}>{suffix}</span> : null}</span>;
};

// card que cai e assenta (pilha): `at` = quando entra; `hot` = destaque (cor de acento)
export const DropCard: React.FC<{t: number; at: number; text: string; hot?: boolean; y: number; w?: number; size?: number; tilt?: number; press?: number}> =
  ({t, at, text, hot, y, w = 760, size = 64, tilt = 0, press = 0}) => {
  const q = ramp(t, at, 0.42, Easing.bezier(0.3, 1.25, 0.5, 1));
  const land = Math.sin(Math.PI * ramp(t, at + 0.3, 0.25));
  return (
    <div style={{position: 'absolute', left: (1080 - w) / 2, width: w, top: y + press, height: size * 1.9, borderRadius: 22,
      background: hot ? C.terra : C.white, color: hot ? C.onAccent : C.ink, display: 'flex', alignItems: 'center', justifyContent: 'center',
      ...fTitle(size), boxShadow: '0 18px 40px rgba(0,0,0,0.30)', opacity: q > 0 ? 1 : 0,
      transform: `translateY(${(1 - q) * -520}px) rotate(${tilt * (1 - 0.6 * q)}deg) scaleY(${1 - 0.06 * land})`}}>{text}</div>
  );
};

// chip com risco que se desenha em `strikeAt` (ideia/papel abandonado); `pulseAt` = pulsa em destaque
export const StrikeChip: React.FC<{t: number; at: number; text: string; strikeAt?: number; pulseAt?: number; dim?: number; size?: number;
  hot?: boolean; warnAt?: number; style?: React.CSSProperties}> = ({t, at, text, strikeAt, pulseAt, dim = 0, size = 46, hot, warnAt, style}) => {
  const shake = warnAt !== undefined ? Math.sin((t - warnAt) * 46) * 7 * Math.sin(Math.PI * ramp(t, warnAt, 0.5)) : 0;
  const q = ramp(t, at, 0.4, OUT);
  const st = strikeAt !== undefined ? ramp(t, strikeAt, 0.35) : 0;
  const pu = pulseAt !== undefined && t >= pulseAt ? 0.5 + 0.5 * Math.sin((t - pulseAt) * 7) : 0;
  const on = pulseAt !== undefined && t >= pulseAt;
  return (
    <div style={{position: 'absolute', padding: `${size * 0.32}px ${size * 0.62}px`, borderRadius: 999, ...fTitle(size),
      background: on || hot ? C.terra : C.pill, color: on || hot ? C.onAccent : C.ink, opacity: q * (1 - 0.55 * st) * (1 - 0.5 * dim),
      transform: `translate(${shake}px, ${(1 - q) * 24}px) scale(${(0.9 + 0.1 * q) * (1 + 0.06 * pu)})`, filter: `blur(${(1 - q) * 6}px)`,
      boxShadow: on ? `0 0 ${30 + 30 * pu}px ${C.terra}88` : '0 10px 24px rgba(0,0,0,0.25)', whiteSpace: 'nowrap', ...style}}>
      <span style={{position: 'relative', display: 'inline-block'}}>
        {text}
        {strikeAt !== undefined && (
          <div style={{position: 'absolute', left: '-6%', top: '52%', height: Math.max(4, size * 0.09), width: `${112 * st}%`, borderRadius: 4,
            background: C.terra, transform: 'translateY(-50%) rotate(-3deg)'}} />
        )}
      </span>
    </div>
  );
};

// foto com movimento lento (Ken Burns) num cartão; fit "contain" para produto recortado (PNG) sobre o papel
export const PhotoFrame: React.FC<{src: string; t: number; s: number; e: number; at?: number; x: number; y: number; w: number; h: number; fit?: 'cover' | 'contain'}> =
  ({src, t, s, e, at, x, y, w, h, fit = 'cover'}) => {
  const inP = ramp(t, at ?? s, 0.5, OUT);
  const push = interpolate(t, [s, e], [1.0, 1.08], cl);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 30, overflow: 'hidden',
      background: fit === 'contain' ? C.white : undefined, boxShadow: `0 26px 54px ${sh(0.22)}`,
      opacity: inP, transform: `translateY(${(1 - inP) * 30}px) scale(${0.96 + 0.04 * inP})`, filter: `blur(${(1 - inP) * 8}px)`}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: fit, transform: `scale(${push})`,
        filter: fit === 'cover' ? T.mediaFilter : `drop-shadow(0 20px 30px ${sh(0.25)})`, padding: fit === 'contain' ? 30 : 0, boxSizing: 'border-box'}} />
    </div>
  );
};
