process.env.TMPDIR = '/Volumes/SSD/CIBO/tmp';   // bundle do Remotion no SSD
import fs from 'node:fs';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {fileURLToPath} from 'node:url';
const [,, out, propsJson] = process.argv;
const inputProps = JSON.parse(propsJson || '{}');
const serveUrl = await bundle({entryPoint: fileURLToPath(new URL('./src/index.ts', import.meta.url)), publicDir: process.env.PUBLIC_DIR || fileURLToPath(new URL('./public', import.meta.url))});
const composition = await selectComposition({serveUrl, id: process.env.COMP || 'Capa', inputProps});
await renderStill({composition, serveUrl, output: out, frame: 0, inputProps, imageFormat: 'jpeg', jpegQuality: 95});
console.log('ok', out);
// o bundle é só uma CÓPIA da pasta pública (camera.mov etc.): apagar depois do render. Sem isso o SSD lotou
// (13 GB de cópias, 13/10/2026; o editor autorizou). Os temporários de trabalho continuam guardados.
fs.rmSync(serveUrl, {recursive: true, force: true});
