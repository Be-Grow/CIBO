import React, {useEffect, useState} from 'react';
import {measureText} from '@remotion/layout-utils';
import {
  AbsoluteFill, Easing, OffthreadVideo, Sequence, continueRender, delayRender, interpolate,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import {C, T, SPLIT, Panel, PanelProps, fTitle, z, fAcc, fLab, fCap, EASE, OUT, cl, ramp, useT} from './theme';
import {Fonts, VBlur, Grain, Pill, I} from './primitives';
import {PANELS} from './panels';
export {C, T, applyTheme} from './theme';
export type {Theme} from './theme';
import {applyTheme, Theme} from './theme';

// Reel com tela dividida: pessoa embaixo, painel de motion em cima, ou pessoa em tela cheia.
// Tudo em segundos do vídeo editado; a câmera (cortes, recorte) vem pronta em camera.mov.

const TR = 0.42;               // duração da troca de layout (s)

type Word = {t: string; s: number; e: number; hl?: boolean};
type Block = {s: number; e: number; words: Word[]};
type Seg = {s: number; e: number; inv?: boolean};
export type ReelProps = {
  camera: string; duration: number; split: Seg[]; panels: Panel[]; captions: Block[];
  hook?: {s: number; e: number; l1: string; l2: string; accent: string; l2At?: number; aside?: string; asideAt?: number; strikeAt?: number};
  lower?: {s: number; e: number; name: string};
  endFade?: number;
  titles?: {s: number; e: number; l1: string; l2: string; accent: string; l2At?: number}[];
  burns?: {t: number; src: string; peak: number; dur: number}[];
  theme?: Theme;
  // vídeo de inserção (B-roll): cobre a pessoa quando a fonte não mostra quem fala, ou ilustra a fala.
  // area "bottom" = parte da pessoa na tela dividida; "full" = tela inteira (abaixo do painel, legenda por cima)
  inserts?: {s: number; e: number; src: string; from?: number; area?: 'bottom' | 'full'; push?: number; pos?: string}[];
};

// presença da tela dividida (0 = tela cheia, 1 = dividida) e velocidade, para o blur de movimento
const splitAmount = (t: number, split: Seg[]) => {
  let v = 0;
  for (const g of split) {
    const a = g.s - TR * 0.35, b = g.e - TR * 0.35;
    v = Math.max(v, Math.min(ramp(t, a, TR), 1 - ramp(t, b, TR)));
  }
  return v;
};

// etiquetas na mesma linha (mesmo y): posições calculadas pela largura medida de TODAS as etiquetas da linha
// (inclusive as que ainda vão entrar), centradas, sem sobrepor e sem mudar de lugar quando uma nova aparece
const laneTags = (tags: any[]) => {
  const rows: Record<string, any[]> = {};
  tags.forEach((g) => { (rows[Math.round(g.y)] = rows[Math.round(g.y)] || []).push(g); });
  const out: any[] = [];
  for (const row of Object.values(rows)) {
    const sz0 = row[0].size ?? 28, GAP = 18, MAXW = 1000;
    const wOf = (g: any, sz: number) => measureText({text: String(g.text).toUpperCase(), fontFamily: `'${T.label.family}'`, fontSize: sz,
      fontWeight: String(T.label.weight), letterSpacing: '2.2px'}).width + sz * 1.8;
    let sz = sz0, ws = row.map((g) => wOf(g, sz)), tot = ws.reduce((a, b) => a + b, 0) + GAP * (row.length - 1);
    if (tot > MAXW) { sz = sz0 * MAXW / tot; ws = row.map((g) => wOf(g, sz)); tot = ws.reduce((a, b) => a + b, 0) + GAP * (row.length - 1); }
    let x = (1080 - tot) / 2;
    row.forEach((g, k) => { out.push({...g, x, size: sz}); x += ws[k] + GAP; });
  }
  return out;
};

// ---------- legenda ----------
const Captions: React.FC<{blocks: Block[]; t: number; sp: number; hide?: boolean; inv?: boolean}> = ({blocks, t, sp, hide, inv}) => {
  if (hide) return null;
  const i = blocks.findIndex((b, k) => t >= b.s - 0.08 && t < Math.min(b.e + 0.35, blocks[k + 1] ? blocks[k + 1].s - 0.04 : 1e9));
  if (i < 0) return null;
  const b = blocks[i];
  const next = blocks[i + 1];
  const end = Math.min(b.e + 0.35, next ? next.s - 0.04 : b.e + 0.6);
  const out = ramp(t, end - 0.12, 0.12);
  // em transição de layout a legenda some (nenhum bloco atravessa a troca)
  if (sp > 0.02 && sp < 0.98) return null;
  const split = sp >= 0.98;
  const L = T.layout, onVideo = !split || L.capSplitY > 0 || !!inv;
  // invertida (ela em cima, painel embaixo): legenda sobre o vídeo, logo acima do painel
  const y = split ? (inv ? 1920 - L.splitH - (L.invPad ?? 150) - 70 : L.capSplitY > 0 ? L.capSplitY : L.splitH - 78 * L.splitH / SPLIT) : L.capFullY;
  const color = onVideo ? C.video : C.ink;
  const hl = onVideo ? C.peach : C.terra;
  let size = (split ? 70 : 82) * T.caption.scale;
  if (L.capMaxW > 0) {   // zona segura: encolhe o bloco até caber na largura máxima (a interface do Instagram cobre as bordas)
    const txt = b.words.map((w) => w.t).join(' ');
    const m = measureText({text: T.caption.upper ? txt.toUpperCase() : txt, fontFamily: `'${T.caption.family}'`, fontSize: size,
      fontWeight: String(T.caption.weight), letterSpacing: `${T.caption.ls}px`}).width * 1.06;
    if (m > L.capMaxW) size *= L.capMaxW / m;
  }
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: y, height: 0, display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
      <div style={{whiteSpace: 'nowrap', ...fCap(), fontSize: size, color, opacity: 1 - out, transform: `translateY(${-out * 10}px)`,
        textShadow: !onVideo ? 'none' : '0 0 3px rgba(0,0,0,0.55), 0 2px 14px rgba(0,0,0,0.7), 0 0 44px rgba(0,0,0,0.55)'}}>
        {b.words.map((w, k) => {
          const p = ramp(t, w.s - 0.05, 0.22, OUT);
          return (
            <span key={k} style={{display: 'inline-block', marginRight: k < b.words.length - 1 ? '0.22em' : 0, opacity: p,
              transform: `translateY(${(1 - p) * 16}px) scale(${w.hl ? 1.08 - 0.08 * p : 1})`, filter: `blur(${(1 - p) * 7}px)`,
              ...(w.hl ? fAcc() : {}), color: w.hl ? hl : color, fontSize: w.hl ? '1.12em' : '1em'}}>{w.t}</span>
          );
        })}
      </div>
    </div>
  );
};

// ---------- gancho e lower third ----------
const Hook: React.FC<{h: NonNullable<ReelProps['hook']>; t: number}> = ({h, t}) => {
  if (t > h.e + 0.3) return null;
  const l1 = ramp(t, h.s, 0.5, OUT), l2 = ramp(t, h.l2At ?? h.s + 0.35, 0.55, OUT);
  const as = h.asideAt ? ramp(t, h.asideAt, 0.4, OUT) : 0;
  const st = h.strikeAt ? ramp(t, h.strikeAt, 0.35) : 0;
  const out = ramp(t, h.e - 0.25, 0.3);
  const line = (p: number): React.CSSProperties => ({display: 'block', opacity: p * (1 - out), transform: `translateY(${(1 - p) * 34 - out * 20}px)`, filter: `blur(${(1 - p) * 12 + out * 8}px)`});
  return (
    <div style={{position: 'absolute', top: 120, left: 50, right: 50, textAlign: 'center', ...fTitle(), color: C.video,
      textShadow: '0 3px 18px rgba(0,0,0,0.45)'}}>
      <span style={{...line(l1), fontSize: z(104), lineHeight: 1}}>{h.l1}</span>
      <span style={{...line(l2), fontSize: z(120), lineHeight: 1.05}}>{h.l2} <I color={C.peach}>{h.accent}</I></span>
      {h.aside && (
        <span style={{...line(as), fontSize: z(58), ...fAcc(), marginTop: 18, position: 'relative'}}>
          <span style={{position: 'relative', display: 'inline-block'}}>
            {h.aside}
            <svg style={{position: 'absolute', left: -10, top: '50%', overflow: 'visible'}} width="calc(100% + 20px)" height="10" viewBox="0 0 100 10" preserveAspectRatio="none">
              <path d="M 0 4 Q 38 10 100 0" fill="none" stroke={C.peach} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - st} opacity={st > 0.002 ? 1 : 0} />
            </svg>
          </span>
        </span>
      )}
    </div>
  );
};

const Lower: React.FC<{l: NonNullable<ReelProps['lower']>; t: number; sp: number}> = ({l, t, sp}) => {
  const a = ramp(t, l.s, 0.5, OUT), b = ramp(t, l.e - 0.4, 0.4);
  const p = a * (1 - b);
  if (p <= 0) return null;
  const top = interpolate(sp, [0, 1], [1420, T.layout.splitH + 46]);
  return (
    <div style={{position: 'absolute', left: 64, top, display: 'flex', alignItems: 'center', gap: 18, opacity: p, filter: `blur(${(1 - p) * 8}px)`}}>
      <div style={{width: 70 * p, height: 3, background: C.peach, borderRadius: 2}} />
      <div style={{...fTitle(54), ...fAcc(), color: C.video, textShadow: '0 2px 14px rgba(0,0,0,0.5)', transform: `translateX(${(1 - p) * -16}px)`}}>{l.name}</div>
    </div>
  );
};

// ---------- composição ----------
export const Reel: React.FC<ReelProps> = (props) => {
  applyTheme(props.theme);
  const t = useT();
  const {fps} = useVideoConfig();
  // trecho com inv: true = tela dividida invertida (ela em cima com o topo da cabeça cortado, painel embaixo; pedido da Priscilla, 13/10/2026)
  const spI = splitAmount(t, props.split.filter((g) => g.inv));
  const sp = splitAmount(t, props.split);
  const sp2 = splitAmount(t + 1 / fps, props.split);
  const inv = spI > 0.001;
  const vel = Math.abs(sp2 - sp) * fps;               // presença por segundo
  const blurPx = Math.min(vel * 22, 26);
  const H = T.layout.splitH, K = H / SPLIT;
  // invertida: o painel sobe invPad acima da borda (a interface do Instagram cobre a parte de baixo); a faixa extra é papel
  const PAD = inv ? (T.layout.invPad ?? 150) : 0;
  const panelY = inv ? 1920 - H - PAD + (H + PAD) * (1 - sp) : -H * (1 - sp);
  const camY = inv ? -(T.layout.camUp ?? 300) * sp : T.layout.camShift * sp;
  const lead = (p: Panel) => (p.tr === 'burn' ? 0 : 0.12);
  const live = props.panels.filter((p) => t >= p.s - lead(p) && t < p.e + 0.2);
  const panel = live.length ? live[live.length - 1] : undefined;
  // troca de painel: com burn é corte seco escondido no pico de luz; sem burn, o novo entra deslizando da direita
  const pIn = panel ? (panel.tr === 'burn' ? (t >= panel.s ? 1 : 0) : ramp(t, panel.s - 0.12, 0.38)) : 1;
  const prev = panel ? props.panels.find((p) => Math.abs(p.e - panel.s) < 0.05) : undefined;
  const swap = prev && pIn < 1 && sp > 0.98;
  const endF = props.endFade ? ramp(t, props.duration - props.endFade, props.endFade) : 0;
  const Comp = panel ? PANELS[panel.type] : null;
  const PrevComp = swap && prev ? PANELS[prev.type] : null;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <Fonts />
      <VBlur id="vb" amount={blurPx} />
      <AbsoluteFill style={{transform: `translateY(${camY}px)`, filter: blurPx > 0.3 ? 'url(#vb)' : undefined}}>
        <OffthreadVideo src={staticFile(props.camera)} muted style={{width: 1080, height: 1920, filter: `blur(${endF * 14}px)`}} />
      </AbsoluteFill>
      {(props.inserts || []).map((v, k) => {
        if (t < v.s - 0.25 || t > v.e + 0.25) return null;
        // opaco ANTES do instante da troca (a fonte pode trocar de plano um quadro antes); vizinhos colados = corte seco
        const all = props.inserts || [];
        const glueIn = all.some((o) => Math.abs(o.e - v.s) < 0.05), glueOut = all.some((o) => Math.abs(o.s - v.e) < 0.05);
        const f = (glueIn ? (t >= v.s ? 1 : 0) : ramp(t, v.s - 0.22, 0.16)) * (glueOut ? (t < v.e ? 1 : 0) : 1 - ramp(t, v.e + 0.04, 0.16));
        const top = v.area === 'full' ? 0 : inv ? 0 : H * sp;
        const push = interpolate(t, [v.s, v.e], [1.0, 1 + (v.push ?? 0.06)], cl);
        return (
          <div key={k} style={{position: 'absolute', left: 0, right: 0, top, bottom: 0, overflow: 'hidden', opacity: f}}>
            <Sequence from={Math.round((v.s - 0.25) * fps)} layout="none">
              <OffthreadVideo src={staticFile(v.src)} muted startFrom={Math.round((v.from ?? 0) * fps)}
                style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: v.pos ?? 'center', transform: `scale(${push})`, filter: T.mediaFilter}} />
            </Sequence>
          </div>
        );
      })}
      {sp > 0.001 && (
        <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: H + PAD, transform: `translateY(${panelY}px)`, overflow: 'hidden',
          background: C.paper, boxShadow: inv ? '0 -18px 40px rgba(0,0,0,0.25)' : '0 18px 40px rgba(0,0,0,0.25)', filter: blurPx > 0.3 ? 'url(#vb)' : undefined}}>
          <Grain opacity={T.grain} />
          <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: SPLIT, transform: `scale(${K})`, transformOrigin: 'top center'}}>
          {PrevComp && prev && (
            <div style={{position: 'absolute', inset: 0, opacity: 1 - pIn, transform: `translateX(${-pIn * 120}px)`, filter: `blur(${pIn * 10}px)`}}>
              <PrevComp p={prev} t={t} />
            </div>
          )}
          {Comp && panel && (
            <div style={{position: 'absolute', inset: 0, opacity: swap ? pIn : 1, transform: swap ? `translateX(${(1 - pIn) * 120}px)` : undefined,
              filter: swap ? `blur(${(1 - pIn) * 10}px)` : undefined}}>
              <Comp p={panel} t={t} />
              {panel.step && (
                <div style={{position: 'absolute', left: 40, top: 20, ...fTitle(150), ...fAcc(), lineHeight: 1, color: C.terra,
                  opacity: 0.9 * ramp(t, panel.step.at, 0.4, OUT), transform: `translateY(${(1 - ramp(t, panel.step.at, 0.4, OUT)) * -30}px)`}}>{panel.step.n}</div>
              )}
              {(T.layout.autoTags ? laneTags(panel.tags || []) : (panel.tags || [])).map((g: any, i: number) => (
                <div key={i} style={{position: 'absolute', left: g.x ?? 0, right: g.x === undefined ? 0 : undefined, top: g.y, textAlign: 'center'}}>
                  <Pill text={g.text} p={ramp(t, g.at, 0.4, OUT)} dark={g.dark} size={g.size ?? 28} />
                </div>
              ))}
            </div>
          )}
          </div>
        </div>
      )}
      {props.hook && t < props.hook.e + 0.3 && (
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(15,13,12,0.62) 0%, rgba(15,13,12,0.28) 22%, rgba(15,13,12,0) 38%)',
          opacity: ramp(t, 0, 0.3) * (1 - ramp(t, props.hook.e - 0.25, 0.3))}} />
      )}
      {props.hook && <Hook h={props.hook} t={t} />}
      {(props.titles || []).map((h, k) => <Hook key={k} h={h} t={t} />)}
      {props.lower && <Lower l={props.lower} t={t} sp={sp} />}
      <Captions blocks={props.captions} t={t} sp={sp} inv={inv} hide={!!panel && panel.hideCapsFrom !== undefined && t >= panel.hideCapsFrom && t < panel.e} />
      {(props.burns || []).map((b, k) => (
        <Sequence key={k} from={Math.round((b.t - b.peak) * fps)} durationInFrames={Math.round(b.dur * fps)} layout="none">
          <AbsoluteFill style={{mixBlendMode: 'screen', pointerEvents: 'none', opacity: T.burnOpacity}}>
            <OffthreadVideo src={staticFile(b.src)} muted style={{width: 1080, height: 1920, filter: T.burnFilter}} />
          </AbsoluteFill>
        </Sequence>
      ))}
      <Grain opacity={0.035} />
      <AbsoluteFill style={{background: '#0f0d0c', opacity: endF * 0.85}} />
    </AbsoluteFill>
  );
};
