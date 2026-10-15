import {AbsoluteFill, Composition, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type CardProps = {index: string; label: string; line1: string; line2: string; hue: string};

const Card: React.FC<CardProps> = ({index, label, line1, line2, accent, hue}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 95, mass: 0.9}});
  const title = spring({frame: frame - 10, fps, config: {damping: 17, stiffness: 110}});
  const finish = interpolate(frame, [101, 119], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const glow = `${hue}55`;
  return (
    <AbsoluteFill style={{background: 'linear-gradient(145deg,#090E1C 0%,#101A2D 55%,#080B14 100%)', color: '#F5F8FF',
      fontFamily: 'Arial, sans-serif', overflow: 'hidden', opacity: finish}}>
      <div style={{position: 'absolute', width: 920, height: 920, borderRadius: 460, border: `1px solid ${glow}`,
        left: 300, top: 90, transform: `scale(${0.78 + enter * 0.22})`, opacity: 0.75}} />
      <div style={{position: 'absolute', width: 760, height: 760, borderRadius: 380, border: '1px solid #FFFFFF18',
        left: 380, top: 170, transform: `scale(${1.12 - enter * 0.12})`, opacity: 0.6}} />
      <div style={{position: 'absolute', left: 94, top: 220, width: 7, height: 240, borderRadius: 5, background: hue,
        transform: `scaleY(${enter})`, transformOrigin: 'top', boxShadow: `0 0 36px ${glow}`}} />
      <div style={{position: 'absolute', left: 132, top: 214, color: '#A8B6CC', fontSize: 25, letterSpacing: 5,
        opacity: enter, transform: `translateY(${(1-enter)*16}px)`}}>{index}  /  {label}</div>
      <div style={{position: 'absolute', left: 130, right: 100, top: 720, transform: `translateY(${(1-title)*42}px)`, opacity: title}}>
        <div style={{fontSize: 86, lineHeight: 1.04, fontWeight: 700, letterSpacing: -2}}>{line1}</div>
        <div style={{fontSize: 86, lineHeight: 1.04, fontWeight: 700, letterSpacing: -2, color: hue,
          textShadow: `0 0 48px ${glow}`}}>{line2}</div>
        <div style={{marginTop: 38, height: 2, width: 430, background: `linear-gradient(90deg,${hue},transparent)`,
          transform: `scaleX(${title})`, transformOrigin: 'left'}} />
      </div>
      <div style={{position: 'absolute', left: 132, bottom: 190, fontSize: 22, letterSpacing: 3, color: '#98A8C0', opacity: enter}}>
        MOTION TEST  /  REMOTION
      </div>
      <div style={{position: 'absolute', right: 90, bottom: 178, width: 88, height: 6, borderRadius: 3, background: '#FFFFFF22'}}>
        <div style={{width: `${Math.min(100, (frame / 119) * 100)}%`, height: '100%', background: hue, borderRadius: 3}} />
      </div>
    </AbsoluteFill>
  );
};

export const CiboTestCompositions: React.FC = () => (
  <>
    <Composition id="CIBOTest01" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '01', label: 'IDEIA', line1: 'IDEIAS', line2: 'EM MOVIMENTO', hue: '#63D7E8'} as CardProps} />
    <Composition id="CIBOTest02" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '02', label: 'PROCESSO', line1: 'CLAREZA', line2: 'COM RITMO', hue: '#A59AFF'} as CardProps} />
    <Composition id="CIBOTest03" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '03', label: 'SÍNTESE', line1: 'UM FOCO', line2: 'POR VEZ', hue: '#8BE0B2'} as CardProps} />
  </>
);
