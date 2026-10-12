import {AbsoluteFill, staticFile, spring, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Título de gancho: painel escuro abre na horizontal, palavras sobem uma a uma com mola,
// as palavras de `accent` ficam na cor de destaque; no fim o bloco sobe e some.
type Props = {text: string; accent?: string[]; color?: string; font?: string; top?: number; size?: number};
export const GanchoTitle: React.FC<Props> = ({text, accent = [], color = '#4F95FF', font = 'CalSans-Regular.ttf', top = 150, size = 66}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const OUT = durationInFrames - 14;
  const fontFace = `@font-face{font-family:'GFont';src:url('${staticFile(font)}') format('truetype');}`;
  const norm = (w: string) => w.replace(/[^\p{L}\p{N}]/gu, '').toUpperCase();
  const acc = new Set(accent.map(norm));
  const words = text.toUpperCase().split(' ');

  const panel = spring({frame, fps, config: {damping: 20, mass: 0.6}});
  const leave = spring({frame: frame - OUT, fps, config: {damping: 200}});
  const y = interpolate(leave, [0, 1], [0, -60]);
  const opacity = interpolate(frame, [OUT, durationInFrames - 1], [1, 0], clamp);

  return (
    <AbsoluteFill>
      <style>{fontFace}</style>
      <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center',
        transform: `translateY(${y}px)`, opacity}}>
        <div style={{maxWidth: 940, padding: '30px 40px', borderRadius: 32, background: 'rgba(10,14,26,0.84)',
          border: '1.5px solid rgba(255,255,255,0.14)', boxShadow: '0 18px 50px rgba(0,0,0,0.45)',
          transform: `scaleX(${panel})`, transformOrigin: 'center'}}>
          <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: 18, rowGap: 4}}>
            {words.map((w, i) => {
              const s = spring({frame: frame - 6 - i * 3, fps, config: {damping: 13, mass: 0.5}});
              const isAcc = acc.has(norm(w));
              return (
                <span key={i} style={{fontFamily: 'GFont', fontSize: size, lineHeight: 1.12, color: isAcc ? color : '#fff',
                  display: 'inline-block', opacity: interpolate(s, [0, 0.4], [0, 1], clamp),
                  transform: `translateY(${interpolate(s, [0, 1], [34, 0])}px) scale(${interpolate(s, [0, 1], [0.86, 1])})`}}>{w}</span>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
