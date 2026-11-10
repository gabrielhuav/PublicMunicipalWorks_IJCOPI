/** Capture the actual application in English, nationally and for the State of Mexico.
 * Uses the bundled Playwright package and installed Edge, with a private read-only
 * local HTTP server. No data are fabricated or changed for the figure.
 */
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const site = resolve(root, 'lakehouse/sitio');
const output = resolve(here, 'capturas_figura5');
const modules = resolve(dirname(process.execPath), '../node_modules');
const require = createRequire(import.meta.url);
const { chromium } = require(resolve(modules, 'playwright'));
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://localhost');
    const name = decodeURIComponent(url.pathname).replace(/^\/+/, '') || 'index.html';
    const path = resolve(site, name);
    if (!path.startsWith(site + sep)) { response.writeHead(403).end(); return; }
    const bytes = await readFile(path);
    response.writeHead(200, { 'Content-Type': mime[extname(path)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    response.end(bytes);
  } catch { response.writeHead(404).end(); }
});

let browser;
try {
  await mkdir(output, { recursive: true });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/`;
  browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 900, height: 500 },
    deviceScaleFactor: 2, locale: 'en-GB', colorScheme: 'light', reducedMotion: 'reduce', ignoreHTTPSErrors: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const results = [];
  for (const view of [
    { id: 'national', state: 0, total: 253346, camera: '23.6,-102.2,5' },
    { id: 'state_of_mexico', state: 15, total: 21335, camera: '19.3,-99.6,8' },
  ]) {
    const query = new URLSearchParams({ lang: 'en', modo: 'claro', vista: 'figura',
      capa: 'proyectos', estado: String(view.state), teselas: 'esri-gris', c: view.camera });
    await page.goto(base + '?' + query, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(total => {
      const counter = document.getElementById('filtroConteo');
      const numbers = (counter?.textContent.match(/\d[\d,]*/g) || []).map(x => Number(x.replaceAll(',', '')));
      return document.getElementById('estadoObras')?.getAttribute('aria-busy') === 'false'
        && !document.getElementById('filtros')?.hidden && numbers[1] === total;
    }, view.total, { timeout: 90000 });
    // A transient tile error can leave the application's offline outline below
    // one tile. Retry the actual basemap selector until this capture is complete.
    let complete = false;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        await page.waitForFunction(() => {
          const tiles = [...document.querySelectorAll('.leaflet-tile')].filter(img => img.tagName === 'IMG');
          return window.MapaTeselas?.actual() === 'esri-gris' && tiles.length > 0
            && tiles.every(img => img.complete && img.naturalWidth > 0)
            && !document.querySelector('.leaflet-control-attribution')?.textContent.includes('Natural Earth');
        }, null, { timeout: 15000 });
        complete = true; break;
      } catch {
        await page.evaluate(() => { MapaTeselas.usar('local'); MapaTeselas.usar('esri-gris'); });
      }
    }
    if (!complete) throw new Error(`Incomplete basemap in ${view.id}`);
    await page.waitForTimeout(500);
    // Keep the map and its original attribution; use one common English legend
    // outside both map panels in the composed publication figure.
    await page.addStyleTag({ content: '.panel-lateral { display:none!important; } .escena { height:100vh!important; }' });
    const record = await page.evaluate(() => {
      const counter = document.getElementById('filtroConteo').textContent;
      const numbers = (counter.match(/\d[\d,]*/g) || []).map(x => Number(x.replaceAll(',', '')));
      return { language: document.documentElement.lang, counter, visible: numbers[0], total: numbers[1],
        selectedState: document.getElementById('estadoObras').value,
        attribution: document.querySelector('.leaflet-control-attribution')?.textContent || '',
        locationNote: document.getElementById('filtroUbicacion')?.textContent || '',
        loadedTiles: document.querySelectorAll('.leaflet-tile-loaded').length,
        canvases: document.querySelectorAll('#mapa canvas').length,
        renderingMode: document.querySelector('canvas.proyectos-canvas')?.dataset.modo || '',
        statusTotals: JSON.parse(document.querySelector('canvas.proyectos-canvas')?.dataset.estatus || '[]'),
        groupedCells: JSON.parse(document.querySelector('canvas.proyectos-canvas')?.dataset.grupos || '[]').length,
        aggregationNote: document.getElementById('leyenda')?.textContent || '',
        statusLabels: [...document.querySelectorAll('#filtrosEstatus button')].map(x => x.textContent),
        url: location.href.replace(location.origin, '') };
    });
    if (record.language !== 'en' || record.total !== view.total || !record.canvases) throw new Error(JSON.stringify(record));
    if (view.state === 0 && record.visible !== 253346) throw new Error('Incomplete national view');
    const png = resolve(output, view.id + '.png');
    await page.locator('#mapa').screenshot({ path: png, animations: 'disabled' });
    results.push({ view: view.id, ...record, image: view.id + '.png' });
    console.log(JSON.stringify({ view: view.id, visible: record.visible, total: record.total, loadedTiles: record.loadedTiles, canvases: record.canvases }));
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(resolve(output, 'evidencia.json'), JSON.stringify({ language: 'en', errors, views: results }, null, 2) + '\n');
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
