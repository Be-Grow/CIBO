// Medidor do portão `verifica` (10/11/2026): roda dentro da página no layer 'verifica', mede o DOM de verdade e devolve
// pelo console ("VERIFICA::<json>") o que vaza do painel/quadro, estoura a própria caixa ou fica sobreposto.
// Nasceu do YT 01 da Priscilla: 8 de 28 painéis com texto cortado passaram pelo checa_props, que só olha tempo.
import React, {useEffect, useState} from 'react';
import {continueRender, delayRender, getInputProps} from 'remotion';
import {T} from './theme';

type R = {x: number; y: number; w: number; h: number};
const rr = (r: DOMRect | R): R => ('width' in r ? {x: r.left, y: r.top, w: r.width, h: r.height} : r);
const inter = (a: R, b: R) => Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
// a caixa de linha é mais alta que a tinta (entrelinha 1,0 em título grande): sobreposição se mede no miolo da letra
const miolo = (r: R): R => ({x: r.x, y: r.y + r.h * 0.22, w: r.w, h: r.h * 0.56});
const MIN = 19;
const arr = (r: R) => [Math.round(r.x), Math.round(r.y), Math.round(r.w), Math.round(r.h)];

const medir = (alvoPainel: boolean) => {
  const root = document.querySelector('[data-vf-root]') as HTMLElement;
  const VW = root.clientWidth, VH = root.clientHeight;
  const painel = root.querySelector('[data-vf="painel"]') as HTMLElement | null;
  const pr = painel ? rr(painel.getBoundingClientRect()) : null;
  const opac = (el: Element | null) => {
    let o = 1;
    for (let e = el; e && e !== root.parentElement; e = e.parentElement) {
      const c = getComputedStyle(e);
      if (c.display === 'none' || c.visibility === 'hidden') return 0;
      o *= parseFloat(c.opacity || '1');
    }
    return o;
  };
  // textos: caixa da tinta de cada nó de texto visível
  const textos: {el: Element; txt: string; r: R; dentro: boolean}[] = [];
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const txt = (n.textContent || '').trim(), el = n.parentElement;
    if (!txt || !el || el.closest('[data-vf-marca]') || opac(el) < 0.3) continue;
    const rg = document.createRange(); rg.selectNodeContents(n);
    const rs = [...rg.getClientRects()].filter((q) => q.width > 1 && q.height > 1);
    if (!rs.length) continue;
    const x0 = Math.min(...rs.map((q) => q.left)), y0 = Math.min(...rs.map((q) => q.top));
    const r = {x: x0, y: y0, w: Math.max(...rs.map((q) => q.right)) - x0, h: Math.max(...rs.map((q) => q.bottom)) - y0};
    textos.push({el, txt, r, dentro: !!painel && painel.contains(el)});
  }
  // caixas: elementos com fundo sólido (chip, card, ladrilho, barra); fundo do painel e véus grandes ficam de fora
  const caixas: {el: Element; r: R}[] = [];
  const rgb = (el: Element) => (getComputedStyle(el).backgroundColor.match(/[\d.]+/g) || []).map(Number);
  const papel = painel ? rgb(painel) : [];
  root.querySelectorAll('div,span').forEach((el) => {
    if (el === painel || el.closest('[data-vf-marca]')) return;
    const m = getComputedStyle(el).backgroundColor.match(/rgba?\(([^)]+)\)/);
    const p = m ? m[1].split(',').map(Number) : [];
    if (!m || (p.length > 3 ? p[3] : 1) < 0.5) return;
    const r = rr(el.getBoundingClientRect());
    const ref = painel && painel.contains(el) && pr ? pr.w * pr.h : VW * VH;
    if (r.w < 24 || r.h < 12 || r.w * r.h > 0.45 * ref || opac(el) < 0.3) return;
    // trilho/base quase da cor do papel (barra vazia) não é peça: número em cima dele é desenho, não defeito
    if (painel && painel.contains(el) && !(el.textContent || '').trim() && papel.length >= 3 && Math.abs(p[0] - papel[0]) + Math.abs(p[1] - papel[1]) + Math.abs(p[2] - papel[2]) < 45) return;
    caixas.push({el, r});
  });
  const out: any[] = [], F = 3, B = 10;   // B: respiro mínimo até a borda do painel/quadro
  if (pr) for (const c of caixas) if (painel!.contains(c.el) && (c.r.x < pr.x + F || c.r.x + c.r.w > Math.min(pr.x + pr.w, VW) - F))
    out.push({tipo: 'caixa cortada pela borda do painel', texto: (c.el.textContent || '').trim().slice(0, 60), r: arr(c.r)});
  if (alvoPainel && !textos.some((t) => t.dentro)) out.push({tipo: 'painel vazio no quadro de conferência', texto: 'nada visível: tempos s/e cruzados com o painel vizinho?', r: pr ? arr(pr) : [0, 0, VW, VH]});
  for (const t of textos) {
    // tamanho real da letra no quadro (fonte × escala do painel): abaixo de MIN px em 1080 ninguém lê (etiquetas espremidas numa linha só)
    const he = t.el as HTMLElement, esc = he.offsetHeight ? he.getBoundingClientRect().height / he.offsetHeight : 1;
    const px = parseFloat(getComputedStyle(he).fontSize) * esc;
    // caixa que corta (overflow escondido) com entrelinha colada na letra: a perna do g/p/q/ç some ("30 g", YT 01 da Priscilla)
    const cs = getComputedStyle(he), lh = parseFloat(cs.lineHeight) / parseFloat(cs.fontSize);
    if (cs.overflow !== 'visible' && lh < 1.12 && /[gjpqyç,;]/.test(t.txt)) out.push({tipo: 'descendente cortado (entrelinha colada + overflow escondido)', texto: t.txt, r: arr(t.r)});
    if (px < MIN) out.push({tipo: `letra pequena demais (${px.toFixed(0)} px, mínimo ${MIN})`, texto: t.txt, r: arr(t.r)});
    const lim = t.dentro && pr ? {x: Math.max(pr.x, 0), y: Math.max(pr.y, 0), w: Math.min(pr.x + pr.w, VW) - Math.max(pr.x, 0), h: Math.min(pr.y + pr.h, VH) - Math.max(pr.y, 0)} : {x: 0, y: 0, w: VW, h: VH};
    if (t.r.x < lim.x + B || t.r.y < lim.y - F || t.r.x + t.r.w > lim.x + lim.w - B || t.r.y + t.r.h > lim.y + lim.h + F)
      out.push({tipo: t.dentro ? 'vaza do painel' : 'vaza do quadro', texto: t.txt, r: arr(t.r)});
    const dona = caixas.filter((c) => c.el.contains(t.el)).sort((a, b) => a.r.w * a.r.h - b.r.w * b.r.h)[0];
    if (dona && (t.r.x < dona.r.x - F || t.r.x + t.r.w > dona.r.x + dona.r.w + F || t.r.y < dona.r.y - 8 || t.r.y + t.r.h > dona.r.y + dona.r.h + 8))
      out.push({tipo: 'estoura a caixa', texto: t.txt, r: arr(t.r), outro: arr(dona.r)});
    // soma do que as peças de fora cobrem do miolo da letra (ladrilhos pequenos somam)
    const fora = caixas.filter((c) => !c.el.contains(t.el) && !t.el.contains(c.el)).map((c) => ({c, a: inter(miolo(t.r), c.r)})).filter((q) => q.a > 0);
    if (fora.reduce((n, q) => n + q.a, 0) > 0.25 * t.r.w * t.r.h * 0.56)
      out.push({tipo: 'texto sobre elemento', texto: t.txt, r: arr(t.r), outro: arr(fora.sort((x, y) => y.a - x.a)[0].c.r)});
  }
  for (let i = 0; i < textos.length; i++) for (let j = i + 1; j < textos.length; j++) {
    const a = textos[i], b = textos[j];
    if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
    if (inter(miolo(a.r), miolo(b.r)) > 0.12 * 0.56 * Math.min(a.r.w * a.r.h, b.r.w * b.r.h)) out.push({tipo: 'textos sobrepostos', texto: `${a.txt} × ${b.txt}`, r: arr(a.r), outro: arr(b.r)});
  }
  // pílula/chip com texto em cima de outra (linhas de etiqueta coladas): mesmo que as letras não se toquem
  const comTexto = caixas.filter((c) => (c.el.textContent || '').trim());
  for (let i = 0; i < comTexto.length; i++) for (let j = i + 1; j < comTexto.length; j++) {
    const a = comTexto[i], b = comTexto[j];
    if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    if (inter(a.r, b.r) > 0.08 * Math.min(a.r.w * a.r.h, b.r.w * b.r.h))
      out.push({tipo: 'peças sobrepostas', texto: `${(a.el.textContent || '').trim().slice(0, 30)} × ${(b.el.textContent || '').trim().slice(0, 30)}`, r: arr(a.r), outro: arr(b.r)});
  }
  // marca no próprio quadro: vermelho = o texto, magenta = a outra peça
  const marca = (r: number[], cor: string) => {
    const d = document.createElement('div');
    d.setAttribute('data-vf-marca', '');
    d.style.cssText = `position:absolute;left:${r[0] - 4}px;top:${r[1] - 4}px;width:${r[2] + 8}px;height:${r[3] + 8}px;border:4px solid ${cor};box-sizing:border-box;z-index:9999`;
    root.appendChild(d);
  };
  out.forEach((o) => { marca(o.r, '#ff0033'); if (o.outro) marca(o.outro, '#ff00ff'); });
  return out;
};

export const Medidor: React.FC = () => {
  const P = getInputProps() as any;
  const [h] = useState(() => delayRender('verifica'));
  useEffect(() => {
    const t0 = Date.now();
    const pronto = () => {
      const fs = [...((document as any).fonts as Set<FontFace>)];
      const fontes = T.fonts.every((f) => fs.some((x) => x.family.replace(/["']/g, '') === f.family && x.status === 'loaded'));
      const imgs = [...document.images].every((i) => i.complete);
      return (fontes && imgs) || Date.now() - t0 > 8000;
    };
    const tick = () => {
      if (!pronto()) { setTimeout(tick, 50); return; }
      setTimeout(() => {   // um ciclo de layout depois das fontes
        let res: any[];
        try { res = medir(P.vfPainel !== null && P.vfPainel !== undefined); } catch (e) { res = [{tipo: 'erro do medidor', texto: String(e), r: [0, 0, 0, 0]}]; }
        console.log('VERIFICA::' + JSON.stringify(res));
        continueRender(h);
      }, 80);
    };
    tick();
  }, [h]);
  return null;
};
