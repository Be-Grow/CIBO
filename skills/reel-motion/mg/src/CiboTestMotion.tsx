import {AbsoluteFill, Composition, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type CardProps = {index: string; label: string; line1: string; line2: string; hue: string; tokens: string[]};
type TransitionProps = {from: string; to: string};

const Card: React.FC<CardProps> = ({index, label, line1, line2, hue, tokens}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 95, mass: 0.9}});
  const title = spring({frame: frame - 10, fps, config: {damping: 17, stiffness: 110}});
  const finish = interpolate(frame, [101, 119], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tagEnter = spring({frame: frame - 26, fps, config: {damping: 19, stiffness: 105}});
  const glow = `${hue}55`;
  return (
    <AbsoluteFill style={{background: 'linear-gradient(145deg,#090E1C 0%,#101A2D 55%,#080B14 100%)', color: '#F5F8FF',
      fontFamily: 'Arial, sans-serif', overflow: 'hidden', opacity: finish}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.12, backgroundImage: 'linear-gradient(#9AB2D012 1px,transparent 1px),linear-gradient(90deg,#9AB2D012 1px,transparent 1px)',
        backgroundSize: '72px 72px', maskImage: 'radial-gradient(ellipse at 62% 48%, black, transparent 76%)'}} />
      <div style={{position: 'absolute', width: 920, height: 920, borderRadius: 460, border: `1px solid ${glow}`,
        left: 300, top: 90, transform: `rotate(${frame * 0.12}deg) scale(${0.78 + enter * 0.22})`, opacity: 0.75}} />
      <div style={{position: 'absolute', width: 760, height: 760, borderRadius: 380, border: '1px solid #FFFFFF18',
        left: 380, top: 170, transform: `scale(${1.12 - enter * 0.12})`, opacity: 0.6}} />
      <div style={{position: 'absolute', left: 94, top: 220, width: 7, height: 240, borderRadius: 5, background: hue,
        transform: `scaleY(${enter})`, transformOrigin: 'top', boxShadow: `0 0 36px ${glow}`}} />
      <div style={{position: 'absolute', left: 132, top: 214, color: '#A8B6CC', fontSize: 25, letterSpacing: 5,
        opacity: enter, transform: `translateY(${(1-enter)*16}px)`}}>{index}  /  {label}</div>
      <div style={{position: 'absolute', right: 92, top: 205, display: 'flex', alignItems: 'center', gap: 14,
        border: '1px solid #FFFFFF26', borderRadius: 28, padding: '11px 18px', color: '#C2CDDD', fontSize: 16,
        letterSpacing: 2, opacity: enter, transform: `translateY(${(1-enter)*10}px)`}}>
        <span style={{width: 8, height: 8, borderRadius: 4, background: hue, boxShadow: `0 0 14px ${glow}`}} />
        MOTION SYSTEM
      </div>
      <div style={{position: 'absolute', left: 130, right: 100, top: 720, transform: `translateY(${(1-title)*42}px)`, opacity: title}}>
        <div style={{fontSize: 86, lineHeight: 1.04, fontWeight: 700, letterSpacing: -2}}>{line1}</div>
        <div style={{fontSize: 86, lineHeight: 1.04, fontWeight: 700, letterSpacing: -2, color: hue,
          textShadow: `0 0 48px ${glow}`}}>{line2}</div>
        <div style={{marginTop: 38, height: 2, width: 430, background: `linear-gradient(90deg,${hue},transparent)`,
          transform: `scaleX(${title})`, transformOrigin: 'left'}} />
        <div style={{display: 'flex', gap: 12, marginTop: 24}}>
          {tokens.map((token, i) => <div key={token} style={{border: `1px solid ${hue}55`, borderRadius: 20,
            padding: '9px 15px', color: '#C5D2E3', fontSize: 16, letterSpacing: 1.5,
            opacity: tagEnter, transform: `translateY(${(1-tagEnter)*12}px)`, background: '#101A2D99'}}>
            <span style={{color: hue, marginRight: 8}}>0{i + 1}</span>{token}
          </div>)}
        </div>
      </div>
      <div style={{position: 'absolute', right: 96, top: 786, display: 'flex', flexDirection: 'column', gap: 14, alignItems: 'flex-end'}}>
        {[0, 1, 2, 3].map((i) => {
          const p = spring({frame: frame - 16 - i * 4, fps, config: {damping: 18, stiffness: 120}});
          return <div key={i} style={{height: 5, width: 26 + ((i + 1) % 3) * 13, background: i === 1 ? hue : '#C5D2E344',
            borderRadius: 3, transform: `scaleX(${p})`, transformOrigin: 'right', opacity: 0.85}} />;
        })}
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

const SwipeTransition: React.FC<TransitionProps> = ({from, to}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const x = interpolate(p, [0, 1], [1500, -1700]);
  return (
    <AbsoluteFill style={{background: '#080B14', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'linear-gradient(#A6B8D414 1px,transparent 1px),linear-gradient(90deg,#A6B8D414 1px,transparent 1px)', backgroundSize: '72px 72px'}} />
      <div style={{position: 'absolute', width: 1040, height: 2600, top: -340, left: x - 240, transform: 'skewX(-18deg)',
        background: `linear-gradient(90deg,${from}00 0%,${from}99 28%,${to} 62%,${to}00 100%)`, opacity: 0.92}} />
      <div style={{position: 'absolute', width: 18, height: 2600, top: -340, left: x + 720, transform: 'skewX(-18deg)',
        background: '#F4F7FF', opacity: interpolate(p, [0.25, 0.5, 0.85], [0, 0.8, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}} />
      <div style={{position: 'absolute', width: 340, height: 340, borderRadius: 170, top: 790, left: x + 130, border: `2px solid ${to}AA`,
        transform: `scale(${0.5 + p * 1.2})`, opacity: 0.7}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 958, height: 2, background: `linear-gradient(90deg,transparent,${to}88,transparent)`, opacity: 0.6}} />
    </AbsoluteFill>
  );
};

export const CiboTestCompositions: React.FC = () => (
  <>
    <Composition id="CIBOTest01" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '01', label: 'IDEIA', line1: 'IDEIAS', line2: 'EM MOVIMENTO', hue: '#63D7E8', tokens: ['CONCEITO', 'FORMA', 'RITMO']} as CardProps} />
    <Composition id="CIBOTest02" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '02', label: 'PROCESSO', line1: 'CLAREZA', line2: 'COM RITMO', hue: '#A59AFF', tokens: ['FOCO', 'PAUSA', 'FLUXO']} as CardProps} />
    <Composition id="CIBOTest03" component={Card} durationInFrames={120} fps={30} width={1080} height={1920}
      defaultProps={{index: '03', label: 'SÍNTESE', line1: 'UM FOCO', line2: 'POR VEZ', hue: '#8BE0B2', tokens: ['SÍNTESE', 'ESCOLHA', 'AÇÃO']} as CardProps} />
    <Composition id="CIBOTransition01" component={SwipeTransition} durationInFrames={15} fps={30} width={1080} height={1920}
      defaultProps={{from: '#63D7E8', to: '#A59AFF'} as TransitionProps} />
    <Composition id="CIBOTransition02" component={SwipeTransition} durationInFrames={15} fps={30} width={1080} height={1920}
      defaultProps={{from: '#A59AFF', to: '#8BE0B2'} as TransitionProps} />
  </>
);
