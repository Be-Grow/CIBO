import {Composition} from 'remotion';
import {SeguirCard} from './SeguirCard';
import {GanchoTitle} from './GanchoTitle';
import {LottieOverlay} from './LottieOverlay';
import {Audiogram, calcAudiogram} from './Audiogram';
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
  </>
);
