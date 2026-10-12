import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {AbsoluteFill, cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import {useEffect, useState} from 'react';

// Toca uma animação Lottie (JSON do LottieFiles ou exportado do After Effects/Bodymovin) sobre o
// vídeo, com fundo transparente. Quadro a quadro como todo o Remotion. `src` em public/.
type Props = {src?: string; x?: number; y?: number; width?: number; loop?: boolean; playbackRate?: number};

export const LottieOverlay: React.FC<Props> = ({src = 'anel.json', x = 540, y = 960, width = 400, loop = false, playbackRate = 1}) => {
  const [handle] = useState(() => delayRender('carregando lottie'));
  const [data, setData] = useState<LottieAnimationData | null>(null);
  useEffect(() => {
    fetch(staticFile(src)).then((r) => r.json()).then((j) => {setData(j); continueRender(handle);}).catch((e) => cancelRender(e));
  }, [handle, src]);
  if (!data) return null;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: x - width / 2, top: y - width / 2, width, height: width}}>
        <Lottie animationData={data} loop={loop} playbackRate={playbackRate} />
      </div>
    </AbsoluteFill>
  );
};
