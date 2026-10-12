import {useAudioData, visualizeAudio, getAudioDurationInSeconds} from '@remotion/media-utils';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate, CalculateMetadataFunction} from 'remotion';

// Audiograma para podcast só de áudio (ou trecho sem vídeo bom): foto/capa em círculo, barras que
// seguem o áudio real (quadro a quadro), legenda sincronizada e título. Arquivos em public/.
type Cap = {s: number; e: number; t: string};
export type AudiogramProps = {audio: string; image?: string; title?: string; subtitle?: string; captions?: Cap[];
  color?: string; bg?: string; font?: string};

export const calcAudiogram: CalculateMetadataFunction<AudiogramProps> = async ({props}) => ({
  durationInFrames: Math.ceil((await getAudioDurationInSeconds(staticFile(props.audio))) * 30),
});

export const Audiogram: React.FC<AudiogramProps> = ({audio, image, title = '', subtitle = '', captions = [], color = '#4F95FF',
  bg = '#0A0E1A', font = 'CalSans-Regular.ttf'}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const data = useAudioData(staticFile(audio));
  const t = frame / fps;
  const cap = captions.find((c) => t >= c.s - 0.1 && t < c.e + 0.3);   // aparece 100 ms antes da fala
  const N = 48;
  // voz concentra energia nos graves: compensa as frequências altas e espelha a partir do centro
  const half = data ? visualizeAudio({fps, frame, audioData: data, numberOfSamples: 64, optimizeFor: 'speed'})
    .slice(0, N / 2).map((v, i) => Math.min(1, Math.sqrt(v * (1 + i * 0.9)) * 1.6)) : [];
  const bars = [...[...half].reverse(), ...half];
  const ff = `@font-face{font-family:'AgFont';src:url('${staticFile(font)}') format('truetype');}`;
  const intro = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: bg, fontFamily: 'AgFont', color: '#fff', alignItems: 'center'}}>
      <style>{ff}</style>
      <Audio src={staticFile(audio)} />
      {image ? <Img src={staticFile(image)} style={{marginTop: 260, width: 520, height: 520, borderRadius: 260, objectFit: 'cover',
        border: `8px solid ${color}`, transform: `scale(${0.92 + 0.08 * intro})`, opacity: intro}} /> : null}
      <div style={{marginTop: 60, fontSize: 58, textAlign: 'center', padding: '0 90px', lineHeight: 1.1}}>{title}</div>
      <div style={{marginTop: 14, fontSize: 36, opacity: 0.7}}>{subtitle}</div>
      <div style={{display: 'flex', alignItems: 'center', gap: 8, height: 220, marginTop: 50}}>
        {bars.map((v, i) => {
          const h = 12 + v * 200;
          return <div key={i} style={{width: (width - 260) / N - 8, height: h, borderRadius: 8, background: color, opacity: 0.55 + 0.45 * (h / 212)}} />;
        })}
      </div>
      <div style={{position: 'absolute', top: 1380, width: 920, textAlign: 'center', fontSize: 64, lineHeight: 1.15,
        textShadow: '0 4px 18px rgba(0,0,0,0.6)'}}>{cap ? cap.t : ''}</div>
    </AbsoluteFill>
  );
};
