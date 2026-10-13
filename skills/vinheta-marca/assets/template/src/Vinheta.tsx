import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, random, spring, staticFile, useCurrentFrame, Easing} from 'remotion';

import {CFG} from './config';

// Estrutura aprovada (LPA, 13/10/2026). Cores, takes, palavras, logo e tempos vêm de config.ts.
const BLACK = CFG.bg;
const GOLD = CFG.accent;
const GOLD_LIGHT = CFG.accentLight;
const W = 1920;
const H = 1080;
const FPS = CFG.fps;

export const DUR = Math.round(CFG.durSec * FPS);
const BEAT = CFG.beatSec * FPS;
const b = (n: number) => Math.round(CFG.firstHitSec * FPS + n * BEAT); // batida n a partir do 1º impacto
const HIT1 = b(0); // entram os painéis
const SWAP = b(2); // troca dos painéis
const WIDE = b(4); // tela cheia + palavras (uma por batida)
const SETC = b(4 + Math.max(CFG.words.length, 1)); // painéis de novo
const COLLAPSE = Math.round(CFG.breakSec * FPS) - 7; // painéis viram a linha logo antes da pausa
const LOGO_HIT = Math.round(CFG.logoHitSec * FPS); // impacto grande

const ease = Easing.bezier(0.22, 1, 0.36, 1);
const easeIn = Easing.bezier(0.64, 0, 0.78, 0);
const c = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const tw = (f: number, a: number, z: number, from = 0, to = 1, e = ease) =>
  interpolate(f, [a, z], [from, to], {...c, easing: e});

// ---------- Constelação (fundo do manual) ----------
const N = 50;
const pts = Array.from({length: N}, (_, i) => ({
  x: random('x' + i) * W, y: random('y' + i) * H,
  vx: (random('vx' + i) - 0.5) * 0.3, vy: (random('vy' + i) - 0.5) * 0.22,
  r: 1.2 + random('r' + i) * 2.4, ph: random('p' + i) * Math.PI * 2,
}));
const Constellation: React.FC<{opacity: number}> = ({opacity}) => {
  const f = useCurrentFrame();
  const p = pts.map((q) => ({...q, x: q.x + q.vx * f, y: q.y + q.vy * f}));
  const lines: React.ReactNode[] = [];
  for (let i = 0; i < N; i++)
    for (let j = i + 1; j < N; j++) {
      const d = Math.hypot(p[i].x - p[j].x, p[i].y - p[j].y);
      if (d < 250)
        lines.push(<line key={i + '-' + j} x1={p[i].x} y1={p[i].y} x2={p[j].x} y2={p[j].y}
          stroke={GOLD_LIGHT} strokeWidth={0.8} strokeOpacity={0.15 * (1 - d / 250)} />);
    }
  return (
    <svg width={W} height={H} style={{position: 'absolute', opacity}}>
      {lines}
      {p.map((q, i) => {
        const t = 0.45 + 0.55 * Math.abs(Math.sin(f / 14 + q.ph));
        return (
          <g key={i}>
            <circle cx={q.x} cy={q.y} r={q.r * 4} fill={GOLD_LIGHT} opacity={0.06 * t} />
            <circle cx={q.x} cy={q.y} r={q.r} fill={GOLD_LIGHT} opacity={0.85 * t} />
          </g>
        );
      })}
    </svg>
  );
};

// ---------- Grade única (dourada, quente) ----------
const Grade: React.FC = () => {
  const f = useCurrentFrame();
  const flash = interpolate(f, [0, 5], [0.8, 0], c);
  return (
    <>
      <AbsoluteFill style={{background: GOLD, mixBlendMode: 'soft-light', opacity: 0.45}} />
      <AbsoluteFill style={{background: `linear-gradient(180deg, ${BLACK}55 0%, transparent 30%, transparent 62%, ${BLACK}DD 100%)`}} />
      <AbsoluteFill style={{background: GOLD_LIGHT, opacity: flash, mixBlendMode: 'screen'}} />
    </>
  );
};
const LOOK = CFG.look;

const Clip: React.FC<{src: string; dur: number; drift: number}> = ({src, dur, drift}) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, dur], [1.16, 1.04], c);
  const y = interpolate(f, [0, dur], [drift, -drift], c);
  return (
    <AbsoluteFill>
      <OffthreadVideo src={staticFile(src)} muted
        style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s}) translateY(${y}px)`, filter: LOOK}} />
      <Grade />
    </AbsoluteFill>
  );
};

// ---------- Painéis verticais ----------
const PW = 596;
const GAP = 26;
const X0 = (W - (PW * 3 + GAP * 2)) / 2;
type Shot = {src: string; from: number; to: number};
const Panel: React.FC<{i: number; shots: Shot[]; inAt: number; outAt?: number}> = ({i, shots, inAt, outAt}) => {
  const f = useCurrentFrame();
  const st = inAt + i * 3;
  const open = tw(f, st, st + 14);
  const close = outAt === undefined ? 0 : tw(f, outAt + i * 3, outAt + i * 3 + 10, 0, 1, easeIn);
  const top = close * 50;
  const bottom = Math.min((1 - open) * 100 + close * 50, 100 - top);
  const y = tw(f, st, st + 16, 160, 0);
  return (
    <div style={{position: 'absolute', left: X0 + i * (PW + GAP), top: 0, width: PW, height: H,
      clipPath: `inset(${top}% 0 ${bottom}% 0)`, transform: `translateY(${y}px)`}}>
      {shots.map((s, k) => (
        <Sequence key={k} from={s.from} durationInFrames={s.to - s.from} layout="none">
          <Clip src={s.src} dur={s.to - s.from} drift={k % 2 ? -10 : 10} />
        </Sequence>
      ))}
      <AbsoluteFill style={{boxShadow: `inset 0 0 0 1.5px ${GOLD}`, opacity: 0.9 * tw(f, st + 4, st + 16)}} />
    </div>
  );
};

// ---------- Tela cheia com palavras do manual ----------
const WORDS = CFG.words.map((w, k) => ({...w, at: b(4 + k)}));
const Wide: React.FC = () => {
  const lf = useCurrentFrame();
  const f = lf + WIDE; // frame absoluto
  const s = interpolate(f, [WIDE, SETC + 4], CFG.wide.scale, c);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{transform: `translateX(${CFG.wide.shiftX}px) scale(${s})`, transformOrigin: '50% 50%'}}>
        <OffthreadVideo src={staticFile(CFG.wide.src)} muted
          style={{width: '100%', height: '100%', objectFit: 'cover', filter: LOOK + ' brightness(0.82)'}} />
      </AbsoluteFill>
      <Grade />
      <AbsoluteFill style={{background: `linear-gradient(90deg, ${BLACK} 0%, ${BLACK}F2 22%, ${BLACK}99 42%, transparent 62%)`}} />
      {WORDS.map((w, k) => {
        const end = k < WORDS.length - 1 ? WORDS[k + 1].at : SETC;
        if (f < w.at || f >= end) return null;
        const inn = tw(f, w.at, w.at + 10);
        const out = tw(f, end - 4, end, 0, 1, easeIn);
        const showOver = k === 0 || WORDS[k - 1].over !== w.over;
        const overIn = showOver ? inn : 1;
        return (
          <div key={k} style={{position: 'absolute', left: 150, top: 420, opacity: 1 - out}}>
            <div style={{fontFamily: 'RedHat', fontWeight: 600, fontSize: 26, letterSpacing: `${0.55 - 0.15 * overIn}em`,
              color: GOLD, opacity: overIn, marginBottom: 18}}>
              {w.over}
              <span style={{display: 'inline-block', width: 90 * overIn, height: 1.5, background: GOLD, marginLeft: 22, verticalAlign: 'middle'}} />
            </div>
            <div style={{fontFamily: CFG.serif, fontStyle: 'italic', fontSize: 132, lineHeight: 1.1,
              background: `linear-gradient(100deg, ${GOLD} 10%, ${GOLD_LIGHT} 50%, ${GOLD} 90%)`, WebkitBackgroundClip: 'text',
              color: 'transparent', opacity: inn, filter: `blur(${(1 - inn) * 10}px)`,
              transform: `translateY(${(1 - inn) * 30}px)`, paddingRight: 30}}>
              {w.word}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- Logo ----------
// partes recortadas por prepara_logo.py, com margem transparente (pad): glow/blur nunca batem na borda
const LG = CFG.logo;
const SC = CFG.logoWidth / Math.max(...LG.parts.map((p) => p.w));
const P = LG.pad;
const LOGO_TOP = H / 2 - (LG.srcH * SC) / 2 - 10;
const SYM = LG.parts[0];
const SYM_CENTER_Y = LOGO_TOP + (SYM.top + SYM.h / 2) * SC;
const part = (pt: typeof SYM, topOffset: number, extra: React.CSSProperties = {}) => (
  <Img src={staticFile(pt.file)} style={{position: 'absolute', left: W / 2 + pt.dx * SC - ((pt.w + 2 * P) * SC) / 2,
    top: LOGO_TOP + pt.top * SC + topOffset - P * SC, width: (pt.w + 2 * P) * SC, height: (pt.h + 2 * P) * SC, ...extra}} />
);

const Burst: React.FC<{t: number}> = ({t}) => (
  <svg width={W} height={H} style={{position: 'absolute'}}>
    {Array.from({length: 46}, (_, i) => {
      const ang = random('a' + i) * Math.PI * 2;
      const sp = 260 + random('s' + i) * 620;
      const d = tw(t, 0, 50) * sp;
      const o = interpolate(t, [0, 4, 50], [0, 1, 0], c);
      return <circle key={i} cx={W / 2 + Math.cos(ang) * d} cy={H / 2 + 40 + Math.sin(ang) * d * 0.6}
        r={1 + random('r2' + i) * 2.6} fill={GOLD_LIGHT} opacity={o} />;
    })}
  </svg>
);

const Logo: React.FC = () => {
  const f = useCurrentFrame(); // relativo ao início da pausa (COLLAPSE + 20)
  const hit = LOGO_HIT - (COLLAPSE + 20);
  const t = f - hit; // relativo ao impacto
  // pausa: símbolo se desenha devagar, centralizado
  const draw = tw(f, 10, hit - 6, 0, 1, Easing.inOut(Easing.cubic));
  const symGlow = interpolate(f, [10, hit - 2, hit + 20], [0.2, 1, 0.55], c);
  // impacto: símbolo sobe para o lugar, texto entra
  const rise = t < 0 ? 0 : spring({frame: t, fps: FPS, config: {damping: 18, mass: 0.7}});
  const symY = (H / 2 - SYM_CENTER_Y) * (1 - rise);
  const shake = t >= 0 && t < 12 ? (random('sh' + t) - 0.5) * 14 * (1 - t / 12) : 0;
  const push = interpolate(t, [0, DUR - LOGO_HIT], [1, 1.045], c);
  const shine = interpolate(t, [48, 84], [-30, 130], {...c, easing: Easing.inOut(Easing.cubic)});

  const symMask = `linear-gradient(90deg, #000 ${draw * 130 - 30}%, transparent ${draw * 130}%)`;
  const center = (r: number) => `linear-gradient(90deg, transparent ${50 - r * 60}%, #000 ${50 - r * 50}%, #000 ${50 + r * 50}%, transparent ${50 + r * 60}%)`;
  const shineMask = `linear-gradient(105deg, transparent ${shine - 12}%, #000 ${shine}%, transparent ${shine + 12}%)`;

  const sym = (extra: React.CSSProperties = {}) => part(SYM, symY, extra);
  const rest = LG.parts.slice(1);
  const restRev = (k: number) => tw(t, k * 8, k * 8 + (k === 0 ? 14 : 18));
  const restEl = (k: number, extra: React.CSSProperties = {}) =>
    part(rest[k], 0, {transform: k === 0 ? `scaleX(${1.12 - 0.12 * restRev(0)})` : undefined, ...extra});

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: `radial-gradient(ellipse 46% 52% at 50% 50%, ${GOLD}40 0%, transparent 70%)`, opacity: symGlow}} />
      {t >= 0 && <Burst t={t} />}
      <AbsoluteFill style={{transform: `translate(${shake}px, ${shake * 0.6}px) scale(${push})`, transformOrigin: '50% 48%'}}>
        <AbsoluteFill style={{filter: `drop-shadow(0 0 ${10 + 22 * symGlow}px ${GOLD}88)`}}>
          {sym({WebkitMaskImage: symMask})}
        </AbsoluteFill>
        {t >= 0 && rest.map((_, k) => (
          <React.Fragment key={k}>
            {restEl(k, {WebkitMaskImage: center(restRev(k)), opacity: restRev(k), filter: k === 0 ? `blur(${(1 - restRev(0)) * 10}px)` : undefined})}
          </React.Fragment>
        ))}
        {t >= 40 && (
          <AbsoluteFill style={{WebkitMaskImage: shineMask, filter: 'brightness(2.1) saturate(0.7)', mixBlendMode: 'screen'}}>
            {sym()}
            {rest.length > 0 && restEl(0)}
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- Composição ----------
export const Vinheta: React.FC = () => {
  const f = useCurrentFrame();
  const stars = tw(f, 0, 30, 0, 0.6) * interpolate(f, [HIT1, HIT1 + 8], [1, 0.5], c) * interpolate(f, [WIDE, WIDE + 4, SETC, SETC + 4], [1, 0, 0, 1], c)
    + tw(f, COLLAPSE + 10, COLLAPSE + 60, 0, 0.35);
  // cold open: nome da Lilian + flare dourado
  const nameIn = tw(f, 6, 22);
  const nameOut = tw(f, 34, 44, 0, 1, easeIn);
  const flareX = interpolate(f, [4, 44], [-0.3, 1.3], {...c, easing: Easing.inOut(Easing.quad)});
  // linha dourada que fecha os painéis
  const lineIn = tw(f, COLLAPSE + 6, COLLAPSE + 18);
  const lineOut = tw(f, COLLAPSE + 22, COLLAPSE + 50, 0, 1, easeIn);
  const lineW = lineIn * W * 0.85 * (1 - lineOut * 0.9);
  // flashes nos impactos
  const flash = Math.max(
    interpolate(f, [HIT1, HIT1 + 2, HIT1 + 10], [0, 0.5, 0], c),
    interpolate(f, [WIDE, WIDE + 2, WIDE + 8], [0, 0.6, 0], c),
    interpolate(f, [LOGO_HIT, LOGO_HIT + 2, LOGO_HIT + 16], [0, 0.75, 0], c)
  );
  const fadeOut = interpolate(f, [DUR - 22, DUR], [1, 0], c);

  return (
    <AbsoluteFill style={{background: BLACK}}>
      <style>{`@font-face{font-family:'RedHat';src:url('${staticFile(CFG.sansFile)}');}`}</style>
      <AbsoluteFill style={{opacity: fadeOut}}>
        <Constellation opacity={stars} />
        {/* cold open */}
        <div style={{position: 'absolute', top: H / 2 - 1, left: 0, width: W, height: 2, opacity: 0.9 * (1 - nameOut),
          background: `radial-gradient(ellipse 18% 100% at ${flareX * 100}% 50%, ${GOLD_LIGHT}, transparent)`}} />
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: nameIn * (1 - nameOut)}}>
          <div style={{fontFamily: 'RedHat', fontWeight: 500, fontSize: 30, color: GOLD_LIGHT, marginTop: 70,
            letterSpacing: `${0.7 - 0.25 * nameIn}em`, filter: `blur(${(1 - nameIn) * 6}px)`}}>
            {CFG.name}
          </div>
        </AbsoluteFill>
        {/* painéis 1 */}
        <Sequence from={0} durationInFrames={WIDE}>
          {CFG.panelsA.map(([a, z], i) => (
            <Panel key={i} i={i} inAt={HIT1} shots={[{src: a, from: HIT1, to: SWAP + i * 3}, {src: z, from: SWAP + i * 3, to: WIDE}]} />
          ))}
        </Sequence>
        {/* tela cheia + palavras */}
        <Sequence from={WIDE} durationInFrames={SETC + 6 - WIDE}>
          <Wide />
        </Sequence>
        {/* painéis 2, fecham na linha */}
        <Sequence from={0} durationInFrames={COLLAPSE + 20}>
          {CFG.panelsC.map((s, i) => (
            <Panel key={i} i={i} inAt={SETC} outAt={COLLAPSE} shots={[{src: s, from: SETC, to: COLLAPSE + 20}]} />
          ))}
        </Sequence>
        <div style={{position: 'absolute', top: H / 2 - 1, left: W / 2 - lineW / 2, width: lineW, height: 2,
          background: `linear-gradient(90deg, transparent, ${GOLD_LIGHT}, transparent)`, opacity: 1 - lineOut, boxShadow: `0 0 24px ${GOLD}`}} />
        {/* pausa + logo */}
        <Sequence from={COLLAPSE + 20}>
          <Logo />
        </Sequence>
        <AbsoluteFill style={{background: `radial-gradient(circle at 50% 50%, ${GOLD_LIGHT}, transparent 62%)`, opacity: flash, mixBlendMode: 'screen'}} />
        <AbsoluteFill style={{background: `radial-gradient(ellipse at center, transparent 55%, ${BLACK} 100%)`, opacity: 0.8}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- Versão curta (sting): só a pausa + revelação, para meio/fim de episódio ----------
export const CURTA_INI = LOGO_HIT - Math.round(2.5 * FPS); // começa com o símbolo se desenhando
export const CURTA_DUR = DUR - CURTA_INI;
export const VinhetaCurta: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: BLACK}}>
      <AbsoluteFill style={{opacity: interpolate(f, [0, 8], [0, 1], c)}}>
        <Sequence from={-CURTA_INI}>
          <Vinheta />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
