import {Composition} from 'remotion';
import {SeguirCard} from './SeguirCard';
import {GanchoTitle} from './GanchoTitle';
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="SeguirCard" component={SeguirCard} durationInFrames={150} fps={30}
      width={1080} height={1920} defaultProps={{name: 'João Guilherme Campos', handle: '@jgcampos'}} />
    <Composition id="GanchoTitle" component={GanchoTitle} durationInFrames={105} fps={30}
      width={1080} height={1920} defaultProps={{text: 'O podcast é um cavalo de Troia', accent: ['cavalo', 'de', 'troia']}} />
  </>
);
