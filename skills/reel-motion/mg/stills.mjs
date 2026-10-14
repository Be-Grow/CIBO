process.env.TMPDIR = '/Volumes/SSD/CIBO/tmp';   // bundle do Remotion no SSD
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const [,, propsFile, outDir, ...times] = process.argv;
const inputProps = JSON.parse(fs.readFileSync(propsFile, 'utf8'));
const serveUrl = await bundle({entryPoint: fileURLToPath(new URL('./src/index.ts', import.meta.url)), publicDir: process.env.PUBLIC_DIR || fileURLToPath(new URL('./public', import.meta.url))});
const composition = await selectComposition({serveUrl, id: process.env.COMP || 'Reel', inputProps});
fs.mkdirSync(outDir, {recursive: true});
for (const t of times) {
  const frame = Math.round(parseFloat(t) * 29.97);
  await renderStill({composition, serveUrl, output: `${outDir}/f_${t}.png`, frame, inputProps});
  console.log('ok', t);
}
// o bundle é só uma CÓPIA da pasta pública (camera.mov etc.): apagar depois do render. Sem isso o SSD lotou
// (13 GB de cópias, 13/10/2026; o editor autorizou). Os temporários de trabalho continuam guardados.
fs.rmSync(serveUrl, {recursive: true, force: true});
