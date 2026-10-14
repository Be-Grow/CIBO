import {Composition} from 'remotion';
import {SeguirCard} from './SeguirCard';
import {GanchoTitle} from './GanchoTitle';
import {LottieOverlay} from './LottieOverlay';
import {Audiogram, calcAudiogram} from './Audiogram';
import {Reel, ReelProps} from './reel/Reel';
import {Capa} from './reel/Capa';
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="SeguirCard" component={SeguirCard} durationInFrames={150} fps={30}
      width={1080} height={1920} defaultProps={{name: 'João Guilherme Campos', handle: '@jgcampos'}} />
    <Composition id="GanchoTitle" component={GanchoTitle} durationInFrames={105} fps={30}
      width={1080} height={1920} defaultProps={{text: 'O podcast é um cavalo de Troia', accent: ['cavalo', 'de', 'troia']}} />
    <Composition id="LottieOverlay" component={LottieOverlay} durationInFrames={30} fps={30}
      width={1080} height={1920} defaultProps={{src: 'anel.json', x: 540, y: 960, width: 400}} />
    <Composition id="Audiogram" component={Audiogram} calculateMetadata={calcAudiogram} durationInFrames={300} fps={30}
      width={1080} height={1920} defaultProps={{audio: 'audio.wav', image: 'avatar.png', title: 'Título do episódio', subtitle: '@perfil', captions: []}} />
    <Composition id="Reel" component={Reel as any} fps={29.97} width={1080} height={1920} durationInFrames={300}
      defaultProps={{camera: 'r01/camera.mov', duration: 10, split: [], panels: [], captions: []} as ReelProps}
      calculateMetadata={({props}) => ({durationInFrames: Math.round((props as ReelProps).duration * 29.97)})} />
    <Composition id="Capa" component={Capa as any} fps={30} width={1080} height={1920} durationInFrames={1}
      defaultProps={{frame: 'r01/capa_frame.png', l1: 'Ninguém sabe', l2: 'vender no', accent: 'TikTok'}} />
    <Composition id="PriscillaReel" component={Reel as any} fps={29.97} width={1080} height={1920} durationInFrames={300}
      defaultProps={{camera: 'r01/camera.mov', duration: 10, split: [], panels: [], captions: []} as ReelProps}
      calculateMetadata={({props}) => ({durationInFrames: Math.round((props as ReelProps).duration * 29.97)})} />
    <Composition id="PriscillaCapa" component={Capa as any} fps={30} width={1080} height={1920} durationInFrames={1}
      defaultProps={{frame: 'r01/capa_frame.png', l1: 'Ninguém sabe', l2: 'vender no', accent: 'TikTok'}} />
  </>
);
