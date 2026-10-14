import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {measureText} from '@remotion/layout-utils';
import {C, T, Theme, applyTheme} from './Reel';

// Capa do reel com o tema do cliente.
// layout "serif" (Priscilla): manchete no topo, destaque em itálico, rodapé com o nome.
// layout "faixa" (João, thumbs do canal): manchete pesada em caixa alta, 2ª linha sobre faixa na cor de destaque, "COM FULANO" no secundário.
export type CapaProps = {frame: string; l1: string; l2: string; accent: string; y?: number; shift?: number; footer?: string; sub?: string;
  layout?: 'serif' | 'faixa'; logo?: string; logoW?: number; logoY?: number; theme?: Theme};
const css = () => T.fonts.map((f) => `@font-face{font-family:'${f.family}';font-weight:${f.weight ?? 'normal'};font-style:${f.style ?? 'normal'};src:url('${staticFile(f.file)}');}`).join('\n');

export const Capa: React.FC<CapaProps> = ({frame, l1, l2, accent, y = 170, shift = 0, footer = 'PRISCILLA DAHER', sub, layout = 'serif', logo, logoW = 440, logoY, theme}) => {
  applyTheme(theme);
  const tf = {fontFamily: `'${T.title.family}'`, fontWeight: T.title.weight, textTransform: T.title.upper ? 'uppercase' : 'none', letterSpacing: T.title.ls} as React.CSSProperties;
  if (layout === 'faixa') {
    // cada linha cabe numa linha só: encolhe a fonte até a largura máxima (texto longo quebrava e invadia o logo)
    const fit = (txt: string, base: number, maxW: number) => {
      if (!txt) return base;
      const w = measureText({text: T.title.upper ? txt.toUpperCase() : txt, fontFamily: `'${T.title.family}'`, fontSize: base,
        fontWeight: String(T.title.weight), letterSpacing: `${T.title.ls}px`}).width * 1.04;
      return w > maxW ? base * maxW / w : base;
    };
    const band = [l2, accent].filter(Boolean).join(' ');
    const s1 = fit(l1, 92, 960), s2 = fit(band, 92, 900), fs = Math.min(s1, s2 * 1.15);
    return (
      <AbsoluteFill style={{background: C.bg}}>
        <style>{css()}</style>
        {shift > 0 && (   // quadro descido para o título caber no grid do feed (3:4): o topo vazio vira a própria imagem desfocada
        <Img src={staticFile(frame)} style={{position: 'absolute', width: 1080, height: 1920, objectFit: 'cover', filter: 'blur(40px) brightness(0.8)', transform: 'scale(1.1)'}} />
      )}
      <Img src={staticFile(frame)} style={{position: 'absolute', width: 1080, height: 1920, objectFit: 'cover', transform: `translateY(${shift}px)`}} />
        <AbsoluteFill style={{background: `linear-gradient(180deg, rgba(0,0,0,0) ${y - 22}%, ${C.paper}E6 ${y + 6}%, ${C.paper} 100%)`}} />
        <div style={{position: 'absolute', top: `${y}%`, left: 50, right: 50, textAlign: 'center', ...tf}}>
          <div style={{fontSize: fs, lineHeight: 1.04, color: C.video, textShadow: '0 4px 20px rgba(0,0,0,0.45)', whiteSpace: 'nowrap'}}>{l1}</div>
          <div style={{display: 'inline-block', marginTop: 14, padding: '6px 26px 10px', background: C.terraDark, borderRadius: 10, fontSize: s2, lineHeight: 1.04,
            color: C.video, boxShadow: '0 10px 30px rgba(0,0,0,0.35)', whiteSpace: 'nowrap'}}>{l2}{l2 && accent ? ' ' : ''}{accent ? <span style={{color: C.peach}}>{accent}</span> : null}</div>
          {logo && !logoY && <Img src={staticFile(logo)} style={{display: 'block', margin: '34px auto 0', width: logoW, filter: 'drop-shadow(0 8px 20px rgba(0,0,0,0.45))'}} />}
          {sub && <div style={{marginTop: 26, fontFamily: `'${T.label.family}'`, fontWeight: T.label.weight, fontSize: 34, letterSpacing: 3, color: C.gold ?? C.peach}}>{sub}</div>}
        </div>
        {/* logoY = centro do logo em px; perto da base mas dentro do recorte 3:4 da grade do Instagram (y 240–1680) */}
        {logo && logoY ? <Img src={staticFile(logo)} style={{position: 'absolute', left: 540 - logoW / 2, top: logoY - logoW * 0.28, width: logoW,
          filter: 'drop-shadow(0 8px 20px rgba(0,0,0,0.45))'}} /> : null}
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <style>{css()}</style>
      {shift > 0 && (   // quadro descido para o título caber no grid do feed (3:4): o topo vazio vira a própria imagem desfocada
        <Img src={staticFile(frame)} style={{position: 'absolute', width: 1080, height: 1920, objectFit: 'cover', filter: 'blur(40px) brightness(0.8)', transform: 'scale(1.1)'}} />
      )}
      <Img src={staticFile(frame)} style={{position: 'absolute', width: 1080, height: 1920, objectFit: 'cover', transform: `translateY(${shift}px)`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(15,13,12,0.78) 0%, rgba(15,13,12,0.45) 26%, rgba(15,13,12,0) 44%)'}} />
      <div style={{position: 'absolute', top: y, left: 60, right: 60, textAlign: 'center', color: C.video, ...tf, textShadow: '0 4px 24px rgba(0,0,0,0.45)'}}>
        <div style={{fontSize: 128 * T.title.scale, lineHeight: 0.98}}>{l1}</div>
        <div style={{fontSize: 150 * T.title.scale, lineHeight: 1.0}}>{l2} <span style={{...(T.accent.italic ? {fontStyle: 'italic'} : {fontWeight: T.accent.weight}), color: C.peach}}>{accent}</span></div>
      </div>
      <div style={{position: 'absolute', bottom: 120, left: 0, right: 0, textAlign: 'center', fontFamily: `'${T.label.family}'`, fontWeight: T.label.weight, fontSize: 26,
        letterSpacing: 6, color: C.video, opacity: 0.85, textShadow: '0 2px 10px rgba(0,0,0,0.6)'}}>{footer}</div>
    </AbsoluteFill>
  );
};
