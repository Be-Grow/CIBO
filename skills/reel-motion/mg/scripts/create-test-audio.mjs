import {mkdirSync, writeFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';

// Original synthetic bed for Remotion's Audiogram example; not a client deliverable.
const here = dirname(fileURLToPath(import.meta.url));
const output = join(here, '..', 'public', 'audio.wav');
const rate = 48_000;
const seconds = 12;
const channels = 2;
const dataBytes = rate * seconds * channels * 2;
const wav = Buffer.alloc(44 + dataBytes);
wav.write('RIFF', 0);
wav.writeUInt32LE(36 + dataBytes, 4);
wav.write('WAVE', 8);
wav.write('fmt ', 12);
wav.writeUInt32LE(16, 16);
wav.writeUInt16LE(1, 20);
wav.writeUInt16LE(channels, 22);
wav.writeUInt32LE(rate, 24);
wav.writeUInt32LE(rate * channels * 2, 28);
wav.writeUInt16LE(channels * 2, 32);
wav.writeUInt16LE(16, 34);
wav.write('data', 36);
wav.writeUInt32LE(dataBytes, 40);

const chord = [110, 138.59, 164.81];
for (let i = 0; i < rate * seconds; i++) {
  const t = i / rate;
  const fade = Math.max(0, Math.min(1, t / 0.8, (seconds - t) / 1.2));
  const pad = chord.reduce((sum, f) => sum + Math.sin(2 * Math.PI * f * t), 0) / 3;
  const pulse = Math.exp(-((t % 0.75) / 0.12)) * Math.sin(2 * Math.PI * 440 * t);
  const value = Math.max(-1, Math.min(1, 0.18 * fade * (0.82 * pad + 0.18 * pulse)));
  const pcm = Math.round(value * 32767);
  const offset = 44 + i * channels * 2;
  wav.writeInt16LE(pcm, offset);
  wav.writeInt16LE(pcm, offset + 2);
}

mkdirSync(dirname(output), {recursive: true});
writeFileSync(output, wav);
console.log(`Created ${output} (${seconds}s, ${rate} Hz, stereo PCM16)`);
