import {AbsoluteFill, Img, staticFile, spring, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Cartão "seguir" do Instagram: entra com mola, o botão é tocado e vira "Seguindo", sai descendo.
type Props = {name: string; handle: string; avatar?: string; font?: string; top?: number; tap?: number};
// Props por cliente: `avatar` e `font` são arquivos em public/; `top` é o y do cartão em 1080×1920
// (fica acima da faixa de UI do Instagram, no canto inferior); `tap` é o quadro do toque no botão.
export const SeguirCard: React.FC<Props> = ({name, handle, avatar = 'avatar.png', font = 'CalSans-Regular.ttf', top = 1420, tap = 52}) => {
  const fontFace = `@font-face{font-family:'CardFont';src:url('${staticFile(font)}') format('truetype');}`;
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const OUT = durationInFrames - 16;

  const enter = spring({frame, fps, config: {damping: 15, mass: 0.7}});
  const leave = spring({frame: frame - OUT, fps, config: {damping: 200}});
  const y = interpolate(enter, [0, 1], [140, 0]) + interpolate(leave, [0, 1], [0, 160]);
  const opacity = interpolate(frame, [0, 8], [0, 1], clamp) * interpolate(frame, [OUT, durationInFrames - 2], [1, 0], clamp);
  const scale = interpolate(enter, [0, 1], [0.92, 1]);

  // avatar e textos chegam um pouco depois do cartão
  const avatarS = spring({frame: frame - 4, fps, config: {damping: 12, mass: 0.5}});
  const textS = spring({frame: frame - 8, fps, config: {damping: 18}});
  const btnS = spring({frame: frame - 14, fps, config: {damping: 11, mass: 0.6}});

  // toque no botão: aperta em 52-58 e troca para "Seguindo"
  const TAP = tap;
  const press = interpolate(frame, [TAP - 4, TAP, TAP + 6], [1, 0.88, 1], clamp);
  const followed = frame >= TAP;
  const ring = interpolate(frame, [TAP, TAP + 14], [0, 1], clamp);

  return (
    <AbsoluteFill>
      <style>{fontFace}</style>
      <div style={{position: 'absolute', left: 60, right: 60, top,
        transform: `translateY(${y}px) scale(${scale})`, transformOrigin: 'left bottom', opacity}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26, padding: '24px 28px',
          borderRadius: 34, background: 'rgba(10,14,26,0.84)',
          border: '1.5px solid rgba(255,255,255,0.14)', boxShadow: '0 18px 50px rgba(0,0,0,0.45)'}}>
          <div style={{width: 112, height: 112, borderRadius: 56, padding: 5, flexShrink: 0,
            background: 'conic-gradient(from 210deg, #FEDA75, #FA7E1E, #D62976, #962FBF, #4F5BD5, #FEDA75)',
            transform: `scale(${avatarS})`}}>
            <Img src={staticFile(avatar)} style={{width: '100%', height: '100%', borderRadius: '50%',
              border: '4px solid rgb(10,14,26)', objectFit: 'cover'}} />
          </div>
          <div style={{flex: 1, minWidth: 0, opacity: textS, transform: `translateX(${interpolate(textS, [0, 1], [-24, 0])}px)`}}>
            <div style={{fontFamily: 'CardFont', color: '#fff', fontSize: 40, lineHeight: 1.1, whiteSpace: 'nowrap'}}>{name}</div>
            <div style={{fontFamily: 'CardFont', color: 'rgba(255,255,255,0.72)', fontSize: 34, marginTop: 6}}>{handle}</div>
          </div>
          <div style={{position: 'relative', flexShrink: 0, transform: `scale(${btnS * press})`}}>
            <div style={{position: 'absolute', inset: -10, borderRadius: 26,
              border: `3px solid rgba(255,255,255,${0.6 * (1 - ring)})`, transform: `scale(${0.9 + ring * 0.35})`,
              opacity: followed ? 1 : 0}} />
            <div style={{fontFamily: 'CardFont', fontSize: 34, color: '#fff', padding: '18px 30px', borderRadius: 20,
              background: followed ? 'rgba(255,255,255,0.16)' : '#0095F6', whiteSpace: 'nowrap'}}>
              {followed ? 'Seguindo' : 'Seguir'}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
