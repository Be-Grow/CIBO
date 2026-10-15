import {existsSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve, basename} from 'node:path';

const project = process.env.CIBO_TEST_PROJECT || 'S:/Edição BEGrow/Teste Motion CIBO';
const library = process.env.CIBO_ACERVO_DIR || 'S:/Edição BEGrow/CIBO Acervo';
const videoDir = resolve(project, '04_work/motion');
const audioDir = resolve(project, '03_assets');
const out = resolve(project, '06_deliverables/CIBO Motion Teste.xml');
const fps = 30;
const total = 12 * fps;
const assets = new Map();
const esc = (s) => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const rate = () => '<rate><timebase>30</timebase><ntsc>FALSE</ntsc></rate>';
const url = (p) => `file://localhost/${encodeURI(resolve(p).replaceAll('\\', '/')).replace(/^([A-Za-z]):/, '$1%3A').replaceAll('#', '%23')}`;

function wavInfo(path) {
  const b = readFileSync(path);
  if (b.toString('ascii', 0, 4) !== 'RIFF' || b.toString('ascii', 8, 12) !== 'WAVE') throw new Error(`WAV inválido: ${path}`);
  let pos = 12, channels, sampleRate, bits, dataBytes;
  while (pos + 8 <= b.length) {
    const tag = b.toString('ascii', pos, pos + 4);
    const size = b.readUInt32LE(pos + 4);
    if (tag === 'fmt ') { channels = b.readUInt16LE(pos + 10); sampleRate = b.readUInt32LE(pos + 12); bits = b.readUInt16LE(pos + 22); }
    if (tag === 'data') dataBytes = size;
    pos += 8 + size + (size % 2);
  }
  if (!channels || !sampleRate || !bits || !dataBytes) throw new Error(`Cabeçalho WAV incompleto: ${path}`);
  return {channels, sampleRate, bits, frames: Math.floor(dataBytes / (channels * bits / 8) * fps / sampleRate)};
}

function mediaFile(path, id, kind) {
  path = resolve(path);
  if (!existsSync(path)) throw new Error(`Mídia não encontrada: ${path}`);
  const name = basename(path);
  const video = kind === 'video';
  const info = video ? {frames: 120, width: 1080, height: 1920} : wavInfo(path);
  const media = video
    ? `<media><video><samplecharacteristics>${rate()}<width>1080</width><height>1920</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></video></media>`
    : `<media><audio><samplecharacteristics><depth>${info.bits}</depth><samplerate>${info.sampleRate}</samplerate></samplecharacteristics><channelcount>${info.channels}</channelcount></audio></media>`;
  const xml = `<file id="${id}"><name>${esc(name)}</name><pathurl>${esc(url(path))}</pathurl>${rate()}<duration>${info.frames}</duration>${media}</file>`;
  assets.set(path, {id, xml, frames: info.frames, channels: info.channels || 0});
  return assets.get(path);
}

let n = 0;
function clip(path, kind, start, sourceIn, length, name, db = null) {
  path = resolve(path);
  let a = assets.get(path);
  const firstUse = !a;
  if (firstUse) a = mediaFile(path, `file-${assets.size + 1}`, kind);
  const id = `clipitem-${++n}`;
  const sourceTrack = kind === 'audio' ? '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>' : '';
  const level = db === null ? '' : `<filter><effect><name>Audio Levels</name><effectid>audiolevels</effectid><effectcategory>audiolevels</effectcategory><effecttype>audiolevels</effecttype><mediatype>audio</mediatype><parameter authoringApp="PremierePro"><parameterid>level</parameterid><name>Level</name><valuemin>0</valuemin><valuemax>3.98109</valuemax><value>${(10 ** (db / 20)).toFixed(5)}</value></parameter></effect></filter>`;
  const fileRef = firstUse ? a.xml : `<file id="${a.id}"/>`;
  return `<clipitem id="${id}"><name>${esc(name)}</name><duration>${a.frames}</duration>${rate()}<start>${start}</start><end>${start + length}</end><in>${sourceIn}</in><out>${sourceIn + length}</out><enabled>TRUE</enabled>${fileRef}${sourceTrack}${level}</clipitem>`;
}

const videos = [
  ['01-ideias-em-movimento.mp4', '01 — Ideias em movimento'],
  ['02-clareza-com-ritmo.mp4', '02 — Clareza com ritmo'],
  ['03-um-foco-por-vez.mp4', '03 — Um foco por vez'],
].map(([file, title], i) => clip(resolve(videoDir, file), 'video', i * 120, 0, 120, title));

const musicPath = resolve(audioDir, 'music/trilha-sintetica-teste.wav');
const whooshPath = resolve(audioDir, 'sfx/Whoosh V2 02.wav');
const boomPath = resolve(audioDir, 'sfx/Medium Cinematic Boom 01.wav');
const music = clip(musicPath, 'audio', 0, 0, total, 'Música sintética original — referência de mix', -14);
const whooshInfo = wavInfo(whooshPath);
const whooshes = [0, 120, 240].map((at, i) => clip(whooshPath, 'audio', at + 8, 0, Math.min(whooshInfo.frames, 30), `Whoosh — entrada do bloco ${i + 1}`, -10));
const boomInfo = wavInfo(boomPath);
const boom = clip(boomPath, 'audio', 255, 0, Math.min(boomInfo.frames, 45), 'Boom — destaque do último bloco', -14);

const tc = `<timecode>${rate()}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>`;
const audioFormat = '<format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>';
const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="sequence-1"><name>CIBO — Motion genérico (teste)</name><duration>${total}</duration>${rate()}${tc}<media><video><format><samplecharacteristics>${rate()}<width>1080</width><height>1920</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></format><track>${videos.join('')}</track></video><audio><numOutputChannels>2</numOutputChannels>${audioFormat}<track>${music}</track><track>${whooshes.join('')}</track><track>${boom}</track></audio></media></sequence></xmeml>\n`;
writeFileSync(out, xml, 'utf8');
const catalogPath = resolve(library, 'catalog.json');
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));
const assetRow = (id, target) => {
  const item = catalog.items[id];
  if (!item) throw new Error(`ID ausente no acervo: ${id}`);
  const source = item.source || item.path || item.original || '?';
  return `| 2026-10-14 | ${id} | ${target} | ${source} | ${item.license || 'não verificada'} |`;
};
const manifest = [
  '| Data | ID | Arquivo no projeto | Origem | Licença |',
  '|---|---|---|---|---|',
  assetRow('sfx-707501-killerkipler-whoosh-v2-02', '03_assets/sfx/Whoosh V2 02.wav'),
  assetRow('sfx-medium-cinematic-boom-01', '03_assets/sfx/Medium Cinematic Boom 01.wav'),
  '| 2026-10-14 | original-sintetico-teste | 03_assets/music/trilha-sintetica-teste.wav | Gerada localmente para teste técnico; sem gravação de terceiros | original |',
  '',
].join('\n');
writeFileSync(resolve(project, '07_manifests/assets_usados.md'), manifest, 'utf8');
console.log(`Criado ${out} — sequência ${total / fps}s; 3 módulos, música e duas trilhas de SFX.`);
