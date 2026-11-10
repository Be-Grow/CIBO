// Portão `verifica` (reel.py PROJ rNN verifica): 1 quadro por painel, título, palavra-chave, gancho e tarja no layer
// 'verifica'; o Medidor (src/reel/Medidor.tsx) mede o DOM e responde pelo console. Painel que nem renderiza vira erro.
// uso: node verifica.mjs BUNDLE props.json SAIDA Reel|ReelH   → SAIDA/verifica.json + PNG marcado de cada alvo com problema
import {openBrowser, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
const [,, serveUrl, propsFile, outDir, comp] = process.argv;
const base = JSON.parse(fs.readFileSync(propsFile, 'utf8'));
const inputProps = {...base, layer: 'verifica', captions: []};
fs.rmSync(outDir, {recursive: true, force: true}); fs.mkdirSync(outDir, {recursive: true});
const FPS = 29.97, alvos = [];
// painel: no fim, com todas as peças e etiquetas dentro (0,15 s antes de e: o próximo ainda não entrou)
// e 0,15 s antes do início do seguinte quando eles se encostam ou se cruzam: senão o quadro já é do outro painel, vazio)
(base.panels || []).forEach((p, i, L) => {
  const prox = Math.min(...L.filter((q) => q !== p && q.s > p.s).map((q) => q.s), Infinity);
  alvos.push({id: `painel_${String(i).padStart(2, '0')}`, nome: `painel ${i} (${p.type}) ${p.s.toFixed(1)}–${p.e.toFixed(1)} s`, t: Math.max(p.s, Math.min(p.e, prox) - 0.15), painel: i});
});
if (base.hook) alvos.push({id: 'gancho', nome: 'gancho', t: Math.max(base.hook.s ?? 0, base.hook.e - 0.4)});
(base.titles || []).forEach((h, k) => alvos.push({id: `titulo_${String(k).padStart(2, '0')}`, nome: `título ${k} "${h.l1} ${h.l2 || ''} ${h.accent || ''}" ${h.s.toFixed(1)} s`, t: Math.max(h.s, h.e - 0.4)}));
(base.keywords || []).forEach((h, k) => alvos.push({id: `chave_${String(k).padStart(2, '0')}`, nome: `palavra-chave ${k} "${h.text} ${h.accent || ''}" ${h.s.toFixed(1)} s`, t: Math.max(h.s, h.e - 0.6)}));
if (base.lower) alvos.push({id: 'tarja', nome: 'tarja', t: Math.min((base.lower.s ?? 0) + 1.5, (base.lower.e ?? base.duration) - 0.6)});
if (base.endCard) alvos.push({id: 'cartao_final', nome: 'cartão final', t: base.duration - 0.3});

const browser = await openBrowser('chrome');
const composition = await selectComposition({serveUrl, id: comp, inputProps, puppeteerInstance: browser});
const res = [];
const um = async (a) => {
  const output = `${outDir}/${a.id}.png`;
  let achados = null, erro = null;
  try {
    await renderStill({composition, serveUrl, output, inputProps: {...inputProps, vfPainel: a.painel ?? null}, puppeteerInstance: browser, timeoutInMilliseconds: 60000,
      frame: Math.min(composition.durationInFrames - 1, Math.max(0, Math.round(a.t * FPS))),
      onBrowserLog: (l) => { if (l.text.startsWith('VERIFICA::')) achados = JSON.parse(l.text.slice(10)); }});
  } catch (e) {
    erro = String(e.message || e).split('\n')[0].slice(0, 200);
  }
  if (erro) achados = [{tipo: 'não renderiza', texto: erro}];
  else if (achados === null) achados = [{tipo: 'medidor não respondeu', texto: ''}];
  const guarda = !erro && (achados.length || process.env.VERIFICA_TUDO === '1');   // VERIFICA_TUDO=1: folha com todos os alvos
  if (!guarda) fs.rmSync(output, {force: true});
  res.push({...a, achados, png: guarda ? `${a.id}.png` : null});
};
const fila = [...alvos];
await Promise.all([0, 1, 2].map(async () => { while (fila.length) await um(fila.shift()); }));
res.sort((a, b) => a.t - b.t);
fs.writeFileSync(`${outDir}/verifica.json`, JSON.stringify(res, null, 1));
await browser.close({silent: true});
console.log(`verifica: ${alvos.length} alvos, ${res.filter((r) => r.achados.length).length} com problema`);
process.exit(0);
