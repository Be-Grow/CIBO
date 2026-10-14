import React, {useEffect, useState} from 'react';
import {
  Img, AbsoluteFill, Easing, OffthreadVideo, Sequence, continueRender, delayRender, interpolate,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import {C, T, SPLIT, Panel, PanelProps, fTitle, z, fAcc, fLab, fCap, EASE, OUT, cl, ramp, useT} from './theme';
import {Pill, MediaFrame, Title, I, Counter, DropCard, StrikeChip, PhotoFrame} from './primitives';

const PanelStat: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const n = Math.round(interpolate(t, [p.countAt, p.countAt + 1.1], [0, p.countTo ?? 20], {...cl, easing: OUT}));
  const show = ramp(t, p.countAt - 0.2, 0.5, OUT);
  return (
    <>
      <MediaFrame src={p.media} t={t} s={p.s} e={p.e} from={p.from}>
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(20,16,14,0) 35%, rgba(20,16,14,0.72) 100%)'}} />
        <div style={{position: 'absolute', left: 48, bottom: 40, color: C.video, opacity: show, transform: `translateY(${(1 - show) * 24}px)`}}>
          <div style={{...fTitle(190), lineHeight: 0.9}}>{p.prefix ?? '+'}{n}<span style={{...fAcc(), fontSize: z(110)}}> {p.unit ?? 'anos'}</span></div>
          <div style={{...fLab(), fontSize: 26, letterSpacing: 3, textTransform: 'uppercase', opacity: 0.85, marginTop: 10}}>{p.sub ?? 'escolhendo o que vai na prateleira'}</div>
        </div>
      </MediaFrame>
      <div style={{position: 'absolute', top: 210, left: 100, display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'flex-start'}}>
        {(p.pills || []).map((x: any, i: number) => <Pill key={i} text={x.text} p={ramp(t, x.at, 0.4, OUT)} size={28} />)}
      </div>
    </>
  );
};

// 2) canal novo: gráfico vazio se desenhando
const PanelEmptyChart: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const ax = ramp(t, p.s + 0.1, 0.7);
  const ln = ramp(t, p.lineAt, 0.6);
  const lab = ramp(t, p.labelAt, 0.45, OUT);
  const same = ramp(t, p.sameAt, 0.5, OUT);
  const W = 860, H = 420, X0 = 110, Y0 = 690;
  const path = `M ${X0} ${Y0 - 40} C ${X0 + 60} ${Y0 - 50}, ${X0 + 90} ${Y0 - 90}, ${X0 + 150} ${Y0 - 110}`;
  return (
    <>
      <Title top={150} size={58} p={ramp(t, p.s, 0.5, OUT)} text={<span style={{...fLab(), fontSize: 28, letterSpacing: 3, color: C.ink2}}>TIKTOK SHOP · BRASIL</span>} />
      <svg width={1080} height={SPLIT} style={{position: 'absolute', left: 0, top: 0}}>
        <line x1={X0} y1={Y0} x2={X0 + W * ax} y2={Y0} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />
        <line x1={X0} y1={Y0} x2={X0} y2={Y0 - H * ax} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />
        {[1, 2, 3, 4].map((k) => (
          <line key={k} x1={X0} y1={Y0 - k * 95} x2={X0 + W} y2={Y0 - k * 95} stroke={C.ink2} strokeOpacity={0.18 * ax} strokeWidth={2} strokeDasharray="6 12" />
        ))}
        <path d={path} fill="none" stroke={C.terra} strokeWidth={9} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - ln} />
        <circle cx={X0 + 150} cy={Y0 - 110} r={14 * ln} fill={C.terra} />
        <rect x={X0 + 190} y={Y0 - H} width={(W - 210) * ax} height={H - 6} fill={C.ink} fillOpacity={0.04} rx={18} />
      </svg>
      <div style={{position: 'absolute', left: 380, top: 380, width: 560, textAlign: 'center', opacity: lab, transform: `translateY(${(1 - lab) * 20}px)`, filter: `blur(${(1 - lab) * 8}px)`}}>
        <div style={{...fTitle(104), ...fAcc(), color: C.ink, lineHeight: 1}}>sem histórico</div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 735, display: 'flex', justifyContent: 'center', gap: 18}}>
        {[0, 1].map((k) => {
          const q = ramp(t, p.sameAt + k * 0.14, 0.4, OUT);
          return <div key={k} style={{opacity: q * same, transform: `translateY(${(1 - q) * 16}px)`, padding: '12px 22px', borderRadius: 16,
            background: C.white, boxShadow: '0 8px 24px rgba(43,37,34,0.12)', ...fLab(), fontSize: 27, letterSpacing: 2.4, color: C.ink2}}>{k === 0 ? 'MESMA INFORMAÇÃO' : 'PARA TODO MUNDO'}</div>;
        })}
      </div>
    </>
  );
};

// 3) tese: risca uma ideia, sobe a outra
const PanelStrike: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const a = ramp(t, p.s + 0.15, 0.5, OUT);
  const st = ramp(t, p.strikeAt, 0.35);
  const b = ramp(t, p.line2At, 0.55, OUT);
  const acc = ramp(t, p.accentAt, 0.4, OUT);
  return (
    <>
      <div style={{position: 'absolute', top: 250, left: 0, right: 0, textAlign: 'center', ...fTitle(84), color: C.ink2,
        opacity: a * (1 - 0.45 * st), transform: `translateY(${(1 - a) * 24}px)`, filter: `blur(${(1 - a) * 8}px)`}}>
        <span style={{position: 'relative', display: 'inline-block'}}>
          {p.a ?? 'quem tem informação'}
          {/* o risco acompanha a largura do texto (viewBox esticado); antes a curva fixa de 700 px passava do fim de "uma marca" (Priscilla 03) */}
          <svg style={{position: 'absolute', left: -12, top: '52%', overflow: 'visible'}} width="calc(100% + 24px)" height="10" viewBox="0 0 100 10" preserveAspectRatio="none">
            <path d="M 0 6 Q 43 -2 100 4" fill="none" stroke={C.terra} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - st} opacity={st > 0.002 ? 1 : 0} />
          </svg>
        </span>
      </div>
      <div style={{position: 'absolute', top: 420, left: 0, right: 0, textAlign: 'center', ...fTitle(118), lineHeight: 1.0, color: C.ink,
        opacity: b, transform: `translateY(${(1 - b) * 40}px)`, filter: `blur(${(1 - b) * 12}px)`}}>
        {p.b ?? 'quem sabe'}<br />
        <span style={{...fAcc(), color: C.terra, display: 'inline-block', transform: `scale(${1.06 - 0.06 * acc})`, opacity: 0.35 + 0.65 * acc}}>{p.accent ?? 'ler categoria'}</span>
      </div>
    </>
  );
};

// 4) imagem com etiqueta (e carimbo opcional)
const PanelMedia: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const lab = ramp(t, p.labelAt ?? p.s + 0.3, 0.4, OUT);
  const stamp = p.stampAt ? ramp(t, p.stampAt, 0.22, Easing.bezier(0.5, 0, 0.75, 0)) : 0;
  return (
    <MediaFrame src={p.media} t={t} s={p.s} e={p.e} from={p.from} height={590}>
      {p.label && <div style={{position: 'absolute', left: 40, bottom: 40}}><Pill text={p.label} p={lab} dark size={30} /></div>}
      {p.stampAt && (
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `rgba(20,16,14,${0.35 * stamp})`}}>
          <div style={{border: `8px solid ${C.video}`, borderRadius: 18, padding: '18px 40px', color: C.video, ...fLab(), fontSize: 70,
            letterSpacing: 6, opacity: stamp, transform: `rotate(-6deg) scale(${1.5 - 0.5 * stamp})`}}>{p.stamp}</div>
        </div>
      )}
    </MediaFrame>
  );
};

// 5) barras: participação que encolhe
const Bar: React.FC<{t: number; label: string; sub: string; v0: number; v1: number; fillAt: number; dropAt: number; dropDur?: number; appearAt?: number; top: number; max: number; noNum?: boolean}> = ({t, label, sub, v0, v1, fillAt, dropAt, dropDur = 0.9, appearAt, top, max, noNum}) => {
  const appear = ramp(t, appearAt ?? fillAt - 0.9, 0.45, OUT);
  const fill = ramp(t, fillAt - 0.35, 0.7, OUT);
  const drop = ramp(t, dropAt, dropDur);
  const v = v0 * fill - (v0 - v1) * drop;
  const W = 900;
  const wPx = (Math.max(v, 0) / max) * W;
  const ghost = (v0 / max) * W * fill;
  return (
    <div style={{position: 'absolute', top, left: 90, width: W, opacity: appear, transform: `translateY(${(1 - appear) * 20}px)`}}>
      <div style={{...fTitle(54), color: C.ink, lineHeight: 1}}>{label}</div>
      <div style={{...fLab(), fontSize: 21, letterSpacing: 2.4, color: C.ink2, textTransform: 'uppercase', marginTop: 8}}>{sub}</div>
      <div style={{position: 'relative', height: 64, marginTop: 20}}>
        <div style={{position: 'absolute', left: 0, top: 0, height: 64, width: W, borderRadius: 14, background: C.paper2}} />
        <div style={{position: 'absolute', left: 0, top: 0, height: 64, width: ghost, borderRadius: 14, background: C.ink, opacity: 0.12 * drop}} />
        <div style={{position: 'absolute', left: 0, top: 0, height: 64, width: wPx, borderRadius: 14, background: drop > 0 ? C.terra : C.ink}} />
        <div style={{position: 'absolute', top: -14, left: wPx + 22, ...fTitle(84), color: drop > 0.02 ? C.terra : C.ink, lineHeight: 1}}>
          {noNum ? '' : `${Math.round(Math.max(v, 0))}%`}
        </div>
      </div>
    </div>
  );
};
// logo da marca citada: cartão entra no centro, etiquetas na fala, depois encolhe para o lado do nome na barra
const LogoCard: React.FC<{l: any; t: number}> = ({l, t}) => {
  const a = ramp(t, l.at, 0.5, OUT);
  const rev = ramp(t, l.at + 0.15, 0.55);
  const shine = ramp(t, l.at + 0.6, 0.7);
  const mv = ramp(t, l.chipAt, 0.6);
  const x = interpolate(mv, [0, 1], [540, 870]), y = interpolate(mv, [0, 1], [400, 222]);
  const sc = interpolate(mv, [0, 1], [1, 0.36]) * (0.92 + 0.08 * a);
  const fo = l.outAt ? 1 - ramp(t, l.outAt, 0.45) : 1;   // sai em fade, nunca some seco
  return (
    <>
      <div style={{position: 'absolute', left: x - 290, top: y - 135, width: 580, height: 270, borderRadius: 40, background: '#123E7C', overflow: 'hidden',
        opacity: a * fo, transform: `scale(${sc})`, filter: `blur(${(1 - a) * 10 + (1 - fo) * 6}px)`, boxShadow: '0 24px 60px rgba(18,62,124,0.35)'}}>
        <img src={staticFile(l.src)} style={{position: 'absolute', left: 60, top: 35, width: 460, height: 200, objectFit: 'contain', clipPath: `inset(0 ${(1 - rev) * 100}% 0 0)`}} />
        <div style={{position: 'absolute', top: -60, bottom: -60, width: 120, left: interpolate(shine, [0, 1], [-200, 760]), transform: 'rotate(18deg)',
          background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.35), rgba(255,255,255,0))', opacity: shine > 0 && shine < 1 ? 1 : 0}} />
      </div>
      <div style={{position: 'absolute', top: 580, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 16, opacity: 1 - mv}}>
        {l.tags.map((g: any, i: number) => <Pill key={i} text={g.text} p={ramp(t, g.at, 0.4, OUT)} dark={i > 0} size={28} />)}
      </div>
    </>
  );
};
const PanelBars: React.FC<{p: Panel; t: number}> = ({p, t}) => (
  <>
    {p.title && <div style={{position: 'absolute', top: 70, left: p.step ? 170 : 90, ...fLab(), fontSize: 26, letterSpacing: 3, color: C.ink2,
      opacity: ramp(t, p.s + 0.1, 0.45, OUT)}}>{p.title}</div>}
    {p.bars.map((b: any, i: number) => <Bar key={i} t={t} {...b} top={(p.top0 ?? 180) + i * (p.gap ?? 300)} max={p.max} />)}
    {p.logo && <LogoCard l={p.logo} t={t} />}
  </>
);

// 6) régua de preço: a categoria mudou de faixa
const PanelRuler: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const a = ramp(t, p.s + 0.1, 0.6, OUT);
  const mv = ramp(t, p.moveAt, 1.1);
  const lab = ramp(t, p.labelAt, 0.45, OUT);
  const X0 = 110, X1 = 970, Y = 560;
  const x = interpolate(mv, [0, 1], [X0 + 150, X1 - 230]);
  return (
    <>
      <Title top={200} size={86} p={a} text={<>a categoria mudou<br /><I>de faixa de preço</I></>} />
      <svg width={1080} height={SPLIT} style={{position: 'absolute', left: 0, top: 0}}>
        <line x1={X0} y1={Y} x2={X0 + (X1 - X0) * a} y2={Y} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />
        {Array.from({length: 9}).map((_, k) => (
          <line key={k} x1={X0 + k * (X1 - X0) / 8} y1={Y - 14} x2={X0 + k * (X1 - X0) / 8} y2={Y + 14} stroke={C.ink} strokeWidth={3} opacity={a} />
        ))}
        <rect x={x - 120} y={Y - 30} width={240} height={60} rx={30} fill={C.terra} opacity={a} />
      </svg>
      <div style={{position: 'absolute', top: Y + 40, left: X0 - 20, ...fLab(), fontSize: 24, letterSpacing: 2, color: C.ink2, opacity: a}}>MAIS BARATO</div>
      <div style={{position: 'absolute', top: Y + 40, right: 1080 - X1 - 20, ...fLab(), fontSize: 24, letterSpacing: 2, color: C.ink2, opacity: a}}>MAIS CARO</div>
      <div style={{position: 'absolute', top: Y + 110, left: 0, right: 0, textAlign: 'center', opacity: lab, transform: `translateY(${(1 - lab) * 16}px)`}}>
        <Pill text="nos últimos 3 anos" p={1} size={26} />
      </div>
    </>
  );
};

// 7) dois cards numerados: a ordem certa
const PanelCards: React.FC<{p: Panel; t: number}> = ({p, t}) => (
  <div style={{position: 'absolute', top: 210, left: 90, right: 90, display: 'flex', flexDirection: 'column', gap: 34}}>
    {p.cards.map((c: any, i: number) => {
      const q = ramp(t, c.at, 0.5, OUT);
      return (
        <div key={i} style={{display: 'flex', alignItems: 'center', gap: 34, padding: '34px 44px', borderRadius: 30,
          background: i === 0 ? C.ink : C.white, color: i === 0 ? C.white : C.ink, boxShadow: '0 20px 50px rgba(43,37,34,0.16)',
          opacity: q, transform: `translateX(${(1 - q) * (i === 0 ? -60 : 60)}px)`, filter: `blur(${(1 - q) * 10}px)`}}>
          <div style={{...fTitle(120), ...fAcc(), lineHeight: 0.8, color: C.terra}}>{i + 1}</div>
          <div style={{...fTitle(82), lineHeight: 1}}>{c.text}</div>
        </div>
      );
    })}
  </div>
);


// 8) dois lados do balcão: linha divide quem compra e quem vende
const PanelSides: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const ln = ramp(t, p.lineAt, 0.6);
  const l = ramp(t, p.leftAt, 0.45, OUT), r = ramp(t, p.rightAt, 0.45, OUT), ti = ramp(t, p.titleAt, 0.5, OUT);
  const side = (q: number, _txt: string, dark: boolean, dx: number): React.CSSProperties => ({position: 'absolute', top: p.cardTop ?? 470, width: p.cardW ?? 380, padding: '30px 0', borderRadius: 26,
    textAlign: 'center', background: dark ? C.ink : C.white, color: dark ? C.onAccent : C.ink, boxShadow: '0 16px 40px rgba(43,37,34,0.14)', ...fTitle(p.cardSize ?? 64),
    whiteSpace: 'nowrap', opacity: q, transform: `translateX(${(1 - q) * dx}px)`, filter: `blur(${(1 - q) * 8}px)`});
  const subS: React.CSSProperties = {...fLab(), fontSize: 30, letterSpacing: 2, textTransform: 'uppercase', marginTop: 12, opacity: 0.85};
  return (
    <>
      <Title top={150} size={92} p={ti} text={<>{p.title}<br /><I>{p.accent}</I></>} />
      <div style={{position: 'absolute', left: 538, top: 440, width: 4, height: 260 * ln, background: C.terra, borderRadius: 2}} />
      <div style={{...side(l, p.left, true, -60), left: p.cardW ? 540 - 30 - p.cardW : 110}}>{p.left}{p.leftSub && <div style={subS}>{p.leftSub}</div>}</div>
      <div style={{...side(r, p.right, false, 60), left: p.cardW ? 570 : 590}}>{p.right}{p.rightSub && <div style={subS}>{p.rightSub}</div>}</div>
    </>
  );
};

// 9) grade de produtos iguais: todo mundo oferece a mesma coisa
const PanelGrid: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const cols = 5, rows = 3, Wc = 150, Hc = 150, gx = 26, X0 = (1080 - cols * Wc - (cols - 1) * gx) / 2, Y0 = 190;
  const lab = ramp(t, p.labelAt, 0.45, OUT), push = p.pushAt ? ramp(t, p.pushAt, 0.5, OUT) : 0;
  return (
    <>
      <div style={{position: 'absolute', top: 95, left: 0, right: 0, textAlign: 'center', opacity: lab, transform: `translateY(${(1 - lab) * 16}px)`}}>
        <Pill text={p.label} p={1} size={30} />
      </div>
      {Array.from({length: cols * rows}).map((_, k) => {
        const q = ramp(t, p.at + k * 0.06, 0.35, OUT);
        const wv = p.waveAt ? Math.sin(Math.PI * ramp(t, p.waveAt + (k % cols) * 0.07 + Math.floor(k / cols) * 0.05, 0.4)) : 0;
        const hot = k === p.hot;
        const x = X0 + (k % cols) * (Wc + gx), y = Y0 + Math.floor(k / cols) * (Hc + gx);
        return (
          <div key={k} style={{position: 'absolute', left: x, top: y, width: Wc, height: Hc, borderRadius: 24, background: hot && push > 0.5 ? C.terra : C.white,
            boxShadow: '0 10px 26px rgba(43,37,34,0.12)', opacity: q, transform: `translateY(${-wv * 18}px) scale(${(0.7 + 0.3 * q) * (hot ? 1 + 0.18 * push : 1)})`, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: hot ? 2 : 1}}>
            <svg width={70} height={84} viewBox="0 0 70 84"><rect x={22} y={2} width={26} height={12} rx={4} fill={hot && push > 0.5 ? C.white : C.ink2} opacity={0.8} />
              <rect x={10} y={16} width={50} height={66} rx={14} fill={hot && push > 0.5 ? C.white : C.ink} opacity={hot && push > 0.5 ? 1 : 0.85} /></svg>
          </div>
        );
      })}
      <div style={{position: 'absolute', top: 728, left: 0, right: 0, textAlign: 'center', opacity: push, transform: `translateY(${(1 - push) * 16}px)`}}>
        {p.pushLabel && <Pill text={p.pushLabel} p={1} dark size={30} />}
      </div>
    </>
  );
};

// 10) checklist: o que estudar antes, com um item riscado no fim
const PanelChecklist: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const ti = ramp(t, p.s + 0.1, 0.5, OUT);
  return (
    <>
      <Title top={p.titleTop ?? 110} size={p.titleSize ?? 92} p={ti} text={<>{p.title} <I>{p.accent}</I></>} />
      <div style={{position: 'absolute', top: p.top ?? 300, left: p.left ?? 150, display: 'flex', flexDirection: 'column', gap: p.rowGap ?? 30}}>
        {p.items.map((it: any, i: number) => {
          const q = ramp(t, it.at, 0.4, OUT), ck = ramp(t, it.at + 0.15, 0.35), B = p.box ?? 70;
          const pu = it.pulseAt !== undefined ? Math.sin(Math.PI * ramp(t, it.pulseAt, 0.5)) : 0;   // o item é retomado na fala: pulsa
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, opacity: q, transform: `translateX(${(1 - q) * -40}px) scale(${1 + 0.07 * pu})`, transformOrigin: 'left center'}}>
              <svg width={B} height={B} viewBox="0 0 70 70"><rect x={3} y={3} width={64} height={64} rx={16} fill={ck > 0.5 ? C.terra : 'none'} stroke={ck > 0.5 ? C.terra : C.ink} strokeWidth={4} />
                <path d="M 18 36 L 31 49 L 53 23" fill="none" stroke={C.white} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - ck} /></svg>
              <div style={{...fTitle(p.size ?? 76), color: pu > 0.05 ? C.terra : C.ink, lineHeight: 1, whiteSpace: 'nowrap'}}>{it.text}</div>
            </div>
          );
        })}
      </div>
      {p.strike && (() => {
        const a = ramp(t, p.strike.at, 0.4, OUT), st = ramp(t, p.strike.strikeAt, 0.35);
        return (
          <div style={{position: 'absolute', top: 700, left: 0, right: 0, textAlign: 'center', ...fTitle(70), ...fAcc(), color: C.ink2, opacity: a * (1 - 0.4 * st)}}>
            <span style={{position: 'relative', display: 'inline-block'}}>{p.strike.text}
              <svg style={{position: 'absolute', left: -10, top: '55%', overflow: 'visible'}} width="calc(100% + 20px)" height="10" viewBox="0 0 100 10" preserveAspectRatio="none">
                <path d="M 0 6 Q 42 -2 100 4" fill="none" stroke={C.terra} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - st} opacity={st > 0.002 ? 1 : 0} /></svg>
            </span>
          </div>
        );
      })()}
    </>
  );
};


// 11) ranking: posições com a marca destacada e as concorrentes entrando abaixo
const PanelRank: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const img = ramp(t, p.imgAt, 0.6, OUT);
  return (
    <>
      <div style={{position: 'absolute', top: 70, left: 90, ...fLab(), fontSize: 26, letterSpacing: 3, color: C.ink2, opacity: ramp(t, p.s + 0.1, 0.45, OUT)}}>{p.title}</div>
      <img src={staticFile(p.img)} style={{position: 'absolute', right: 40, top: 150, width: 380, height: 520, objectFit: 'contain', opacity: img,
        transform: `translateY(${(1 - img) * 40}px) rotate(${(1 - img) * 6}deg)`, filter: `drop-shadow(0 30px 40px rgba(43,37,34,0.25)) blur(${(1 - img) * 8}px)`}} />
      {p.rows.map((r: any, i: number) => {
        const q = ramp(t, r.at, 0.45, OUT), hl = r.hl;
        return (
          <div key={i} style={{position: 'absolute', left: 90, top: 150 + i * 120, width: 520, height: 96, borderRadius: 22, display: 'flex', alignItems: 'center', gap: 26, padding: '0 30px',
            background: hl ? C.terra : C.white, color: hl ? C.white : C.ink, boxShadow: '0 12px 30px rgba(43,37,34,0.12)', opacity: q * (r.dim ? 0.45 : 1),
            transform: `translateX(${(1 - q) * -50}px) scale(${hl ? 1 + 0.05 * Math.sin(Math.PI * ramp(t, r.at + 0.3, 0.5)) : 1})`}}>
            <div style={{...fTitle(64), ...fAcc(), width: 70}}>{i + 1}º</div>
            <div style={{...fTitle(58), filter: r.dim ? 'blur(6px)' : undefined}}>{r.text}</div>
          </div>
        );
      })}
    </>
  );
};

// 12) rota: de onde vem → para onde vai, com o arco se desenhando
const PanelRoute: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const ti = ramp(t, p.titleAt, 0.5, OUT), a = ramp(t, p.fromAt, 0.45, OUT), ln = ramp(t, p.fromAt + 0.3, 1.0), b = ramp(t, p.toAt, 0.45, OUT);
  const X0 = 250, X1 = 830, Y = 600;
  const path = `M ${X0} ${Y} C ${X0 + 120} ${Y - 260}, ${X1 - 120} ${Y - 260}, ${X1} ${Y}`;
  return (
    <>
      <Title top={240} size={96} p={ti} text={<>{p.title} <I>{p.accent}</I></>} />
      <svg width={1080} height={SPLIT} style={{position: 'absolute', left: 0, top: 0}}>
        <path d={path} fill="none" stroke={C.terra} strokeWidth={7} strokeLinecap="round" strokeDasharray="2 18" pathLength={1} opacity={0.35 * ln} />
        <path d={path} fill="none" stroke={C.terra} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - ln} />
        <circle cx={X0} cy={Y} r={16 * a} fill={C.ink} /><circle cx={X1} cy={Y} r={16 * b} fill={C.terra} />
      </svg>
      <div style={{position: 'absolute', left: X0 - 150, width: 300, top: Y + 40, textAlign: 'center'}}><Pill text={p.from} p={a} size={30} /></div>
      <div style={{position: 'absolute', left: X1 - 150, width: 300, top: Y + 40, textAlign: 'center'}}><Pill text={p.to} p={b} dark size={30} /></div>
    </>
  );
};

// 13) produto + moedas: "de cada 4 reais, 3 são da marca"
const PanelCoins: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const img = ramp(t, p.imgAt, 0.6, OUT), lab = ramp(t, p.labelAt, 0.45, OUT);
  return (
    <>
      <div style={{position: 'absolute', top: 90, left: 0, right: 0, textAlign: 'center', opacity: ramp(t, p.tagAt, 0.45, OUT)}}><Pill text={p.tag} p={1} size={28} /></div>
      <img src={staticFile(p.img)} style={{position: 'absolute', left: 60, top: 170, width: 400, height: 560, objectFit: 'contain', opacity: img,
        transform: `translateY(${(1 - img) * 40}px) scale(${0.9 + 0.1 * img})`, filter: `drop-shadow(0 30px 40px rgba(43,37,34,0.25))`}} />
      <div style={{position: 'absolute', left: 520, top: 260, display: 'grid', gridTemplateColumns: '200px 200px', gap: 30}}>
        {[0, 1, 2, 3].map((k) => {
          const q = ramp(t, p.coinsAt + k * 0.12, 0.4, OUT), on = k < 3 ? ramp(t, p.fillAt + k * 0.15, 0.35) : 0;
          // p.coin = imagem da moeda (Priscilla 03: "coloque 4 pngs da moeda de 1 real"): as que acendem ganham anel do destaque, a outra apaga
          if (p.coin) {
            const lit = ramp(t, p.fillAt, 0.4);
            return <div key={k} style={{width: 200, height: 200, borderRadius: 100, opacity: q * (k < 3 ? 1 : 1 - 0.55 * lit),
              transform: `scale(${(0.6 + 0.4 * q) * (1 + 0.1 * Math.sin(Math.PI * on))}) rotate(${(1 - q) * -40}deg)`,
              boxShadow: on > 0.5 ? `0 0 0 8px ${C.terra}, 0 16px 34px rgba(43,37,34,0.3)` : '0 14px 30px rgba(43,37,34,0.22)',
              filter: k === 3 && lit > 0 ? `grayscale(${lit})` : undefined}}>
              <Img src={staticFile(p.coin)} style={{width: 200, height: 200}} /></div>;
          }
          return <div key={k} style={{width: 200, height: 200, borderRadius: 100, background: on > 0.5 ? C.terra : C.white, border: `6px solid ${on > 0.5 ? C.terra : C.ink}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', ...fTitle(84), color: on > 0.5 ? C.white : C.ink,
            opacity: q, transform: `scale(${(0.6 + 0.4 * q) * (1 + 0.08 * Math.sin(Math.PI * on))})`, boxShadow: '0 14px 30px rgba(43,37,34,0.14)'}}>R$1</div>;
        })}
      </div>
      <div style={{position: 'absolute', left: 520, width: 430, top: 730, textAlign: 'center', opacity: lab, transform: `translateY(${(1 - lab) * 14}px)`}}><Pill text={p.label} p={1} dark size={28} /></div>
    </>
  );
};

// 14) dois tickets com o valor contando: marca x média do canal
const PanelTickets: React.FC<{p: Panel; t: number}> = ({p, t}) => (
  <>
    <div style={{position: 'absolute', top: 90, left: 0, right: 0, textAlign: 'center', opacity: ramp(t, p.tagAt, 0.45, OUT)}}><Pill text={p.tag} p={1} size={28} /></div>
    {p.tickets.map((k: any, i: number) => {
      const q = ramp(t, k.at, 0.45, OUT);
      const n = Math.round(interpolate(t, [k.countAt, k.countAt + 0.9], [0, k.value], {...cl, easing: OUT}));
      return (
        <div key={i} style={{position: 'absolute', top: 200, left: i === 0 ? 90 : 560, width: 430, height: 520, borderRadius: 34, background: i === 0 ? C.ink : C.white,
          color: i === 0 ? C.white : C.ink, boxShadow: '0 22px 50px rgba(43,37,34,0.18)', opacity: q, transform: `translateY(${(1 - q) * 50}px)`, filter: `blur(${(1 - q) * 8}px)`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14}}>
          <div style={{...fLab(), fontSize: 24, letterSpacing: 3, opacity: 0.75}}>{k.label}</div>
          <div style={{...fTitle(150), lineHeight: 1, color: i === 0 ? C.peach : C.ink}}><span style={{fontSize: z(70)}}>R$</span>{n}</div>
          <div style={{...fTitle(44), ...fAcc(), opacity: 0.8}}>{k.sub}</div>
        </div>
      );
    })}
  </>
);

// 15) mesmo produto, preço oscilando entre o mínimo e o máximo
const PanelOscillate: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const img = ramp(t, p.s + 0.1, 0.5, OUT), go = ramp(t, p.goAt, 0.3);
  const f = (t - p.goAt) * 7;
  const v = go <= 0 ? p.min : Math.round(p.min + (p.max - p.min) * (0.5 + 0.5 * Math.sin(f * 1.7) * Math.cos(f * 0.6)));
  const mn = ramp(t, p.minAt, 0.4, OUT), mx = ramp(t, p.maxAt, 0.4, OUT);
  return (
    <>
      <img src={staticFile(p.img)} style={{position: 'absolute', left: 340, top: 90, width: 400, height: 520, objectFit: 'contain', opacity: img, filter: 'drop-shadow(0 30px 40px rgba(43,37,34,0.25))'}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 600, textAlign: 'center', ...fTitle(130), color: C.terra, opacity: go,
        transform: `rotate(${Math.sin(f) * 2}deg)`}}><span style={{fontSize: z(64)}}>R$</span>{v}</div>
      <div style={{position: 'absolute', left: 90, top: 640}}><Pill text={`mín. R$ ${p.min}`} p={mn} size={28} /></div>
      <div style={{position: 'absolute', right: 90, top: 640}}><Pill text={`máx. R$ ${p.max}`} p={mx} dark size={28} /></div>
    </>
  );
};


// 16) contador com grade: "fomos de 4 para 12 negócios" — número salta nos valores ditos e as peças acendem
const PanelCounter: React.FC<PanelProps> = ({p, t}) => {
  const steps: {at: number; v: number}[] = p.steps;
  const cur = [...steps].reverse().find((s) => t >= s.at);
  const lit = cur ? Math.round(interpolate(t, [cur.at, cur.at + 0.9], [steps[steps.indexOf(cur) - 1]?.v ?? 0, cur.v], {...cl, easing: OUT})) : 0;
  const n = p.tiles ?? steps[steps.length - 1].v, cols = p.cols ?? 6, S = 104, G = 22, X0 = (1080 - cols * S - (cols - 1) * G) / 2;
  return (
    <>
      {p.label && <div style={{position: 'absolute', top: 110, left: 0, right: 0, textAlign: 'center', ...fLab(), fontSize: 30, letterSpacing: 4,
        color: C.ink2, opacity: ramp(t, p.s + 0.1, 0.4, OUT)}}>{p.label}</div>}
      <div style={{position: 'absolute', top: 170, left: 0, right: 0, textAlign: 'center', opacity: ramp(t, steps[0].at - 0.2, 0.4, OUT)}}>
        <Counter t={t} at={steps[0].at} from={p.from ?? 0} to={steps[0].v} steps={steps} size={300} color={C.terra} />
        <div style={{...fTitle(110), color: C.ink, marginTop: -10}}>{p.unit}</div>
      </div>
      {Array.from({length: n}).map((_, k) => {
        const on = k < lit, q = ramp(t, (p.gridAt ?? steps[0].at) + k * 0.04, 0.35, OUT);   // gridAt: grade apagada entra antes do número (painel não fica vazio)
        const pop = on ? Math.sin(Math.PI * ramp(t, (k < steps[0].v ? steps[0].at : cur!.at) + (k % 4) * 0.05, 0.3)) : 0;
        return <div key={k} style={{position: 'absolute', left: X0 + (k % cols) * (S + G), top: (p.gridTop ?? 520) + Math.floor(k / cols) * (S + G), width: S, height: S, borderRadius: 20,
          background: on ? C.terra : C.white, opacity: q, transform: `scale(${(0.8 + 0.2 * q) * (1 + 0.12 * pop)})`, boxShadow: on ? `0 0 28px ${C.terra}66` : 'none'}} />;
      })}
      {p.sub && <div style={{position: 'absolute', top: p.subTop ?? 790, left: 0, right: 0, textAlign: 'center'}}><Pill text={p.sub} p={ramp(t, p.subAt, 0.4, OUT)} dark size={28} /></div>}
    </>
  );
};

// 17) pilha: responsabilidades caindo uma sobre a outra (peso acumulando); a última pode vir em destaque
const PanelStack: React.FC<PanelProps> = ({p, t}) => {
  const cards: {text: string; at: number; hot?: boolean}[] = p.cards;
  const H = p.gap ?? 150, base = p.base ?? 760;
  return (
    <>
      {p.title && <div style={{position: 'absolute', top: 90, left: 0, right: 0, textAlign: 'center', ...fLab(), fontSize: 30, letterSpacing: 4, color: C.ink2,
        opacity: ramp(t, p.s + 0.1, 0.4, OUT)}}>{p.title}</div>}
      {cards.map((c, i) => {
        // cada card novo aperta os de baixo um pouco (peso)
        const press = cards.slice(i + 1).reduce((a, n) => a + 10 * ramp(t, n.at + 0.3, 0.25), 0);
        return <DropCard key={i} t={t} at={c.at} text={c.text} hot={c.hot} y={base - i * H} size={c.hot ? 70 : 58} w={c.hot ? 820 : 740}
          tilt={i % 2 ? 3 : -3} press={press} />;
      })}
    </>
  );
};

// 18) papéis: vários papéis da vida; um papel central cresce e empurra os outros, que vão sendo riscados (esquecidos)
const PanelRoles: React.FC<PanelProps> = ({p, t}) => {
  const c = p.center, grow = c ? ramp(t, c.growAt ?? c.at + 1, 0.8, OUT) : 0, cin = c ? ramp(t, c.at, 0.5, OUT) : 0;
  const ti = ramp(t, p.titleAt ?? p.s + 0.1, 0.5, OUT), ac = ramp(t, p.accentAt ?? p.s + 0.5, 0.45, OUT);
  return (
    <>
      <div style={{position: 'absolute', top: 90, left: 60, right: 60, textAlign: 'center', opacity: ti * (1 - 0.6 * cin), transform: `translateY(${(1 - ti) * 24}px)`}}>
        <div style={{...fTitle(120), color: C.ink, lineHeight: 1.05}}>{p.title}</div>
        {p.accent && <div style={{display: 'inline-block', marginTop: 14, padding: '4px 22px 8px', borderRadius: 10, background: C.terraDark,
          ...fTitle(120), color: C.video, opacity: ac, transform: `scale(${0.92 + 0.08 * ac})`}}>{p.accent}</div>}
      </div>
      {(p.roles || []).map((r: any, i: number) => {
        // empurrados para fora quando o papel central cresce
        const dx = (r.x - 540) * 0.22 * grow, dy = (r.y - 520) * 0.22 * grow;
        return <StrikeChip key={i} t={t} at={r.at} text={r.text} strikeAt={r.strikeAt} pulseAt={r.pulseAt} warnAt={r.warnAt} dim={grow * (r.pulseAt ? 0 : 0.6)} size={p.chipSize ?? 76}
          style={{left: r.x + dx, top: r.y + dy, translate: '-50% -50%'}} />;
      })}
      {c && (
        <div style={{position: 'absolute', left: 540, top: 520, translate: '-50% -50%', padding: '26px 46px', borderRadius: 26, background: C.terra,
          color: C.onAccent, ...fTitle(110 + 40 * grow), opacity: cin, transform: `scale(${0.7 + 0.3 * cin})`, boxShadow: `0 0 ${40 * grow}px ${C.terra}77`,
          whiteSpace: 'nowrap'}}>{c.text}</div>
      )}
    </>
  );
};

// 19) leque: uma ideia central que abre em várias saídas ("isso abre um leque de oportunidades")
const PanelHub: React.FC<PanelProps> = ({p, t}) => {
  const cx = 540, cy = p.cy ?? 300, c = ramp(t, p.centerAt ?? p.s + 0.1, 0.45, OUT);
  const items: {text: string; sub?: string; at: number; subAt?: number}[] = p.items;
  const n = items.length, R = p.radius ?? 330;
  return (
    <>
      {p.title && <div style={{position: 'absolute', top: 70, left: 0, right: 0, textAlign: 'center', ...fTitle(64), color: C.ink2,
        opacity: ramp(t, p.s + 0.1, 0.4, OUT)}}>{p.title}{p.titleAccent && <span style={{color: t >= (p.titleAccentAt ?? 0) ? C.terra : C.ink2,
        transition: 'none', display: 'inline-block', marginLeft: '0.3em', transform: `scale(${1 + 0.12 * Math.sin(Math.PI * ramp(t, p.titleAccentAt ?? 0, 0.4))})`}}>{p.titleAccent}</span>}</div>}
      <svg width={1080} height={SPLIT} style={{position: 'absolute', left: 0, top: 0}}>
        {items.map((it, i) => {
          const a = Math.PI * (0.15 + 0.7 * (n === 1 ? 0.5 : i / (n - 1))), x = cx - R * Math.cos(a), y = cy + R * Math.sin(a) * 1.25;
          const ray = p.raysAt !== undefined ? ramp(t, p.raysAt + i * 0.12, 0.5) : 0, q = ramp(t, it.at - 0.25, 0.5);
          return (
            <g key={i}>
              {/* raio tracejado = o leque se abrindo antes de cada saída ser dita */}
              <line x1={cx} y1={cy} x2={cx + (x - cx) * ray} y2={cy + (y - cy) * ray} stroke={C.terra} strokeWidth={4} strokeDasharray="4 14" strokeLinecap="round" opacity={0.5} />
              <line x1={cx} y1={cy} x2={cx + (x - cx) * q} y2={cy + (y - cy) * q} stroke={C.terra} strokeWidth={6} strokeLinecap="round" opacity={0.85} />
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: cx, top: cy, translate: '-50% -50%', padding: '26px 48px', borderRadius: 26, background: C.terra, color: C.onAccent,
        ...fTitle(130), opacity: c, transform: `scale(${(0.7 + 0.3 * c) * (1 + 0.1 * Math.sin(Math.PI * (p.pulseAt !== undefined ? ramp(t, p.pulseAt, 0.5) : 0)))})`,
        boxShadow: `0 0 40px ${C.terra}66`, whiteSpace: 'nowrap'}}>{p.center}</div>
      {items.map((it, i) => {
        const a = Math.PI * (0.15 + 0.7 * (n === 1 ? 0.5 : i / (n - 1))), x = cx - R * Math.cos(a), y = cy + R * Math.sin(a) * 1.25;
        const q = ramp(t, it.at, 0.45, OUT);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, translate: '-50% -50%', textAlign: 'center', opacity: q, transform: `scale(${0.85 + 0.15 * q})`}}>
            <div style={{padding: '16px 28px', borderRadius: 20, background: C.white, color: C.ink, ...fTitle(82), whiteSpace: 'nowrap', boxShadow: '0 12px 30px rgba(0,0,0,0.3)'}}>{it.text}</div>
            {it.sub && <div style={{marginTop: 12, ...fLab(), fontSize: 30, letterSpacing: 2, color: C.terra, textTransform: 'uppercase', opacity: ramp(t, it.subAt ?? it.at + 0.3, 0.35, OUT)}}>{it.sub}</div>}
          </div>
        );
      })}
    </>
  );
};

// 20) escada: cada degrau dito sobe um nível ("quanto mais acredita, mais vende…"); o último degrau em destaque
const PanelLadder: React.FC<PanelProps> = ({p, t}) => {
  const steps: {text: string; at: number; hot?: boolean}[] = p.steps;
  const n = steps.length, SW = p.sw ?? Math.min(220, 960 / n), SH = p.sh ?? Math.min(96, 560 / n), X0 = (1080 - n * SW) / 2, Y0 = p.base ?? 760;
  return (
    <>
      {p.title && <div style={{position: 'absolute', top: 70, left: 60, right: 60, textAlign: 'center', ...fTitle(96), color: C.ink, lineHeight: 1.05,
        opacity: ramp(t, p.titleAt ?? p.s + 0.1, 0.45, OUT)}}>{p.title}</div>}
      {steps.map((st, i) => {
        const q = ramp(t, st.at, 0.45, Easing.bezier(0.3, 1.3, 0.5, 1)), h = SH * (i + 1);
        return (
          <div key={i} style={{position: 'absolute', left: X0 + i * SW + 8, width: SW - 16, top: Y0 - h * q, height: h * q, borderRadius: '18px 18px 0 0',
            background: st.hot ? C.terra : C.white, boxShadow: st.hot ? `0 0 34px ${C.terra}77` : 'none', overflow: 'visible'}}>
            <div style={{position: 'absolute', top: -70, left: -40, right: -40, textAlign: 'center', ...fTitle(62), color: st.hot ? C.terra : C.ink,
              opacity: ramp(t, st.at + 0.15, 0.3, OUT), whiteSpace: 'nowrap'}}>{st.text}</div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: X0, width: n * SW, top: Y0, height: 6, borderRadius: 3, background: C.ink2, opacity: 0.6 * ramp(t, p.s + 0.1, 0.4)}} />
    </>
  );
};

// 21) linha do tempo: marcos de uma trajetória entrando na ordem em que são ditos
const PanelTimeline: React.FC<PanelProps> = ({p, t}) => {
  const ev: {text: string; sub?: string; at: number; hot?: boolean}[] = p.events;
  const X0 = 120, X1 = 960, Y = p.y ?? 470, n = ev.length;
  const last = [...ev].reverse().find((e) => t >= e.at), prog = last ? (ev.indexOf(last) + ramp(t, last.at, 0.6)) / Math.max(n - 1, 1) : 0;
  return (
    <>
      {p.title && <div style={{position: 'absolute', top: 80, left: 0, right: 0, textAlign: 'center', ...fTitle(100), color: C.ink,
        opacity: ramp(t, p.s + 0.1, 0.45, OUT)}}>{p.title}</div>}
      <div style={{position: 'absolute', left: X0, top: Y - 3, width: X1 - X0, height: 6, borderRadius: 3, background: C.white}} />
      <div style={{position: 'absolute', left: X0, top: Y - 3, width: (X1 - X0) * Math.min(prog, 1), height: 6, borderRadius: 3, background: C.terra}} />
      {ev.map((e, i) => {
        const x = X0 + (X1 - X0) * (n === 1 ? 0.5 : i / (n - 1)), q = ramp(t, e.at, 0.45, OUT), up = i % 2 === 0;
        return (
          <div key={i}>
            <div style={{position: 'absolute', left: x, top: Y, translate: '-50% -50%', width: 34 * (0.4 + 0.6 * q), height: 34 * (0.4 + 0.6 * q), borderRadius: 99,
              background: q > 0.5 ? (e.hot ? C.terra : C.ink) : C.white, boxShadow: e.hot && q > 0.5 ? `0 0 26px ${C.terra}` : 'none'}} />
            <div style={{position: 'absolute', left: x, top: up ? Y - 60 : Y + 60, translate: up ? '-50% -100%' : '-50% 0', textAlign: 'center', opacity: q,
              transform: `translateY(${(1 - q) * (up ? 20 : -20)}px)`}}>
              <div style={{...fTitle(70), color: e.hot ? C.terra : C.ink, whiteSpace: 'nowrap'}}>{e.text}</div>
              {e.sub && <div style={{...fLab(), fontSize: 24, letterSpacing: 2, color: C.ink2, textTransform: 'uppercase', marginTop: 6, whiteSpace: 'nowrap'}}>{e.sub}</div>}
            </div>
          </div>
        );
      })}
    </>
  );
};


// lista numerada de nichos/itens: contador 1..N fixo no topo, foto do item, nome, valor de → para e multiplicador
// (Priscilla 04 "6 nichos", 13/10/2026). p.n item atual, p.total, p.img, p.fit, p.name/nameAt, p.from/fromAt, p.to/toAt, p.mult/multAt, p.note/noteAt
const PanelNiche: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const total = p.total ?? 6;
  const nm = ramp(t, p.nameAt ?? p.s + 0.2, 0.45, OUT), fr = p.fromAt ? ramp(t, p.fromAt, 0.4, OUT) : 0, to = p.toAt ? ramp(t, p.toAt, 0.45, OUT) : 0;
  const mu = p.multAt ? ramp(t, p.multAt, 0.35, OUT) : 0, kick = p.toAt ? Math.sin(Math.PI * ramp(t, p.toAt, 0.4)) : 0;
  const no = p.noteAt ? ramp(t, p.noteAt, 0.4, OUT) : 0;
  return (
    <>
      <div style={{position: 'absolute', top: 40, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 22}}>
        {Array.from({length: total}).map((_, k) => {
          const cur = k + 1 === p.n, done = k + 1 < p.n;
          const q = cur ? ramp(t, p.s, 0.4, OUT) : 1;
          return <div key={k} style={{width: 64, height: 64, borderRadius: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
            ...fTitle(38), background: cur ? C.terra : done ? C.ink : 'transparent', color: cur ? C.onAccent : done ? C.paper : C.ink2,
            border: `3px solid ${cur ? C.terra : done ? C.ink : C.ink2}`, opacity: cur ? 1 : done ? 0.85 : 0.4, transform: `scale(${cur ? 0.85 + 0.25 * q : 1})`}}>{k + 1}</div>;
        })}
      </div>
      <PhotoFrame src={p.img} t={t} s={p.s} e={p.e} at={p.imgAt ?? p.s + 0.1} x={60} y={150} w={420} h={560} fit={p.fit ?? 'cover'} />
      <div style={{position: 'absolute', left: 520, right: 50, top: 170, ...fTitle(66), lineHeight: 1.02, color: C.ink, opacity: nm,
        transform: `translateY(${(1 - nm) * 24}px)`, filter: `blur(${(1 - nm) * 8}px)`}}>{p.name}{p.accent ? <> <span style={{opacity: p.accentAt ? ramp(t, p.accentAt, 0.4, OUT) : 1}}><I>{p.accent}</I></span></> : null}</div>
      {p.from && <div style={{position: 'absolute', left: 520, top: 430, ...fTitle(54), color: C.ink2, opacity: fr * (1 - 0.35 * to),
        transform: `translateX(${(1 - fr) * -20}px)`}}>{p.from}<span style={{...fLab(), fontSize: 24, marginLeft: 14, letterSpacing: 2}}>{p.fromLabel ?? ''}</span></div>}
      {p.to && <div style={{position: 'absolute', left: 520, top: 500, ...fTitle(104), ...fAcc(), color: C.terra, lineHeight: 1, opacity: to,
        transform: `translateY(${(1 - to) * 30}px) scale(${1 + 0.06 * kick})`, transformOrigin: 'left center'}}>{p.to}</div>}
      {p.mult && <div style={{position: 'absolute', left: 520, top: 640, opacity: mu, transform: `scale(${0.6 + 0.4 * mu})`, transformOrigin: 'left center'}}>
        <Pill text={p.mult} p={1} dark size={34} /></div>}
      {p.note && <div style={{position: 'absolute', left: 60, right: 60, top: 745, textAlign: 'center', opacity: no}}><Pill text={p.note} p={1} size={28} /></div>}
    </>
  );
};


// rosca de participação: enche até v1 em fillAt (conta junto), marca opcional do valor antigo (v0 em markAt), rótulo e sub
// (Priscilla 05 "biodegradável já tem 69%… em 2024 era 53%", 13/10/2026)
const PanelDonut: React.FC<{p: Panel; t: number}> = ({p, t}) => {
  const R = 210, SW = 64, CX = 540, CY = 470, L = 2 * Math.PI * R;
  const ap = ramp(t, p.appearAt ?? p.s + 0.2, 0.5, OUT), fill = ramp(t, p.fillAt, 1.0, OUT), mk = p.markAt ? ramp(t, p.markAt, 0.45, OUT) : 0;
  const v = Math.round((p.v1 ?? 0) * fill);
  const ang0 = -Math.PI / 2 + 2 * Math.PI * (p.v0 ?? 0) / 100;
  return (
    <>
      {p.title && <div style={{position: 'absolute', top: 70, left: 0, right: 0, textAlign: 'center', ...fLab(), fontSize: 26, letterSpacing: 3, color: C.ink2,
        textTransform: 'uppercase', opacity: ramp(t, p.titleAt ?? p.s + 0.1, 0.45, OUT)}}>{p.title}</div>}
      <svg width={1080} height={SPLIT} style={{position: 'absolute', left: 0, top: 0, opacity: ap, transform: `scale(${0.92 + 0.08 * ap})`, transformOrigin: `${CX}px ${CY}px`}}>
        <circle cx={CX} cy={CY} r={R} fill="none" stroke={C.paper2} strokeWidth={SW} />
        <circle cx={CX} cy={CY} r={R} fill="none" stroke={C.terra} strokeWidth={SW} strokeLinecap="butt"
          strokeDasharray={`${L * (p.v1 ?? 0) / 100 * fill} ${L}`} transform={`rotate(-90 ${CX} ${CY})`} />
        {p.markAt && <line x1={CX + (R - SW / 2 - 14) * Math.cos(ang0)} y1={CY + (R - SW / 2 - 14) * Math.sin(ang0)} x2={CX + (R + SW / 2 + 14) * Math.cos(ang0)}
          y2={CY + (R + SW / 2 + 14) * Math.sin(ang0)} stroke={C.ink} strokeWidth={6} strokeLinecap="round" opacity={mk} />}
      </svg>
      <div style={{position: 'absolute', left: CX - 200, width: 400, top: CY - 95, textAlign: 'center', opacity: ap}}>
        <div style={{...fTitle(150), ...fAcc(), color: C.terra, lineHeight: 1}}>{v}<span style={{fontSize: 70}}>%</span></div>
        <div style={{...fLab(), fontSize: 24, letterSpacing: 2.4, color: C.ink2, textTransform: 'uppercase', marginTop: 8}}>{p.label}</div>
      </div>
      {p.markAt && <div style={{position: 'absolute', left: CX + (R + SW + 30) * Math.cos(ang0) - 90, top: CY + (R + SW + 30) * Math.sin(ang0) - 24, width: 180,
        textAlign: 'center', opacity: mk}}><Pill text={p.markLabel ?? `${p.v0}%`} p={1} size={26} /></div>}
    </>
  );
};

export const PANELS: Record<string, React.FC<{p: Panel; t: number}>> = {
  stat: PanelStat, empty: PanelEmptyChart, strike: PanelStrike, media: PanelMedia, bars: PanelBars, ruler: PanelRuler, cards: PanelCards, sides: PanelSides, grid: PanelGrid, checklist: PanelChecklist, rank: PanelRank, route: PanelRoute, coins: PanelCoins, tickets: PanelTickets, oscillate: PanelOscillate,
  counter: PanelCounter, stack: PanelStack, roles: PanelRoles,
  hub: PanelHub, ladder: PanelLadder, timeline: PanelTimeline, niche: PanelNiche, donut: PanelDonut,
};

