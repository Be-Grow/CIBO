import {Composition} from 'remotion';
import {Vinheta, DUR, VinhetaCurta, CURTA_DUR} from './Vinheta';
// 4K: renderize com --scale=2 (3840x2160 redesenhado, não ampliado)
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Vinheta" component={Vinheta} durationInFrames={DUR} fps={30} width={1920} height={1080} />
    <Composition id="VinhetaCurta" component={VinhetaCurta} durationInFrames={CURTA_DUR} fps={30} width={1920} height={1080} />
  </>
);
