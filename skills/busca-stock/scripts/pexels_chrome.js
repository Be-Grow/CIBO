// Busca no Pexels de dentro de uma aba www.pexels.com (Claude in Chrome → javascript_tool).
// `busca_stock.py pexels-js PLANO` troca __QUERIES__ e __N__ e imprime este código pronto.
// O retorno do javascript_tool é cortado em ~1000 caracteres: o JSON (lista) vai para o corpo da página e é lido inteiro
// com get_page_text; salve em pexels.json e passe com --pexels. A aba fica sem o site depois (recarregue para usar).
// Só lê páginas públicas.
(async () => {
  const QUERIES = __QUERIES__;   // [{query, orientation}]
  const N = __N__;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const out = [];
  for (const {query, orientation} of QUERIES) {
    const slug = encodeURIComponent(query.trim().replace(/\s+/g, '-'));
    const html = await (await fetch(`/search/videos/${slug}/` + (orientation ? `?orientation=${orientation}` : ''))).text();
    const slugs = [...new Set([...html.matchAll(/href="\/(?:[a-z-]+\/)?video\/([a-z0-9-]+-(\d+))\/"/g)].map(m => m[1]))].slice(0, N);
    for (const s of slugs) {
      const id = s.match(/(\d+)$/)[1];
      const pg = await (await fetch(`/video/${s}/`)).text();
      const files = [...new Set([...pg.matchAll(new RegExp(`https://videos\\.pexels\\.com/video-files/${id}/[^"'\\s\\\\]+?_\\d+_\\d+_[\\d.]+fps\\.mp4`, 'g'))].map(m => m[0]))]
        .map(link => { const m = link.match(/_(\d+)_(\d+)_[\d.]+fps\.mp4$/); return {link, width: +m[1], height: +m[2]}; });
      const dur = +(pg.match(/"duration":\s*(\d+(?:\.\d+)?)/) || [])[1] || 0;
      const user = (pg.match(/"user":\s*\{[^}]*?"(?:first_name|name)":\s*"([^"]+)"/) || [])[1] || '';
      // a página lista também os relacionados (filtrados pelo id acima); fica só a prévia (~640) e o maior
      const big = files.reduce((a, f) => (f.width * f.height > (a ? a.width * a.height : 0) ? f : a), null);
      const prev = files.filter(f => Math.min(f.width, f.height) >= 360).sort((a, b) => a.width * a.height - b.width * b.height)[0];
      out.push({query, id, url: `https://www.pexels.com/video/${s}/`, user, alt: s.replace(/-\d+$/, '').replace(/-/g, ' '),
                duration: dur, width: big ? big.width : 0, height: big ? big.height : 0, files: [prev, big].filter(Boolean)});
      await sleep(400);
    }
  }
  document.body.innerHTML = '<article><pre id="cibo"></pre></article>';
  document.getElementById('cibo').textContent = JSON.stringify(out);
  return `${out.length} vídeos na página: leia com get_page_text`;
})()
