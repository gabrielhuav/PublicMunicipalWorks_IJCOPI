/**
 * End-to-end regression check for the national project view.
 * Run with the bundled Node.js runtime: node scripts/pruebas/vista_nacional.cjs
 * Requires the Playwright package beside that runtime; uses installed Microsoft
 * Edge on Windows and Playwright Chromium elsewhere. No services or live external
 * providers are needed: a read-only loopback server serves the repository's real
 * exported data. Delayed/failed HTTP responses exercise cancellation and retry.
 * Source files, map data and published artifacts are never modified.
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const assert = require('assert/strict');
const modules = path.resolve(path.dirname(process.execPath), '../node_modules');
const { chromium } = require(path.join(modules, 'playwright'));
const root = path.resolve(__dirname, '../../lakehouse/sitio');
const objects = x => x.filas.map(r => Object.fromEntries(x.columnas.map((k,i)=>[k,r[i]])));
const read = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const index = read('datos/05_puntos_2024/indice.json');
const parts = Object.keys(index.archivos).map(Number);
const source = parts.flatMap(id=>objects(read(`datos/05_puntos_2024/${id}.json`)).map(r=>({...r,entidad:id})));
const municipalities = objects(read('datos/02_municipios.json')).filter(m=>m.lat!=null);
const state15 = source.filter(p=>p.entidad===15);
const inState = p => {
  let best=0,dist=Infinity,c=Math.cos(p.lat*Math.PI/180);
  for(const m of municipalities){const d=(m.lat-p.lat)**2+((m.lon-p.lon)*c)**2;if(d<dist){dist=d;best=Number(m.cvemun.slice(0,2));}}
  return best===p.entidad;
};
const state15Visible = state15.filter(inState);
const expected = {
  total:source.length, noCompleted:source.filter(p=>p.g!==0).length,
  noCompletedDocs:source.filter(p=>p.g!==0&&(p.evidencia&1)).length,
  state15:state15.length, state15Visible:state15Visible.length,
  state15Filtered:state15Visible.filter(p=>p.g!==0&&(p.evidencia&1)).length,
};
const statusCounts = rows => rows.reduce((counts, p) => { counts[p.g]++; return counts; }, [0, 0, 0, 0]);
const expectedStatuses = statusCounts(source);
assert.equal(expected.total,253346);
assert.deepEqual(expectedStatuses, [145246, 94955, 11793, 1352]);
console.log('Expected source counts:',JSON.stringify(expected));
const server = http.createServer((req,res)=>{
  let pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(pathname.endsWith('/'))pathname+='index.html';
  const p=path.resolve(root,'.'+pathname);
  if(!p.startsWith(path.resolve(root)+path.sep)){res.writeHead(403).end();return;}
  try { const data=fs.readFileSync(p); const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'}[path.extname(p)]||'application/octet-stream';res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store'}).end(data); }
  catch{res.writeHead(404).end();}
});
const errors=[];
let browser;
const waitCount = (page,n)=>page.waitForFunction(n=>document.querySelector('canvas.proyectos-canvas')?.dataset.proyectos===String(n),n,{timeout:45000});
async function checkIndividuals(page, total, statuses) {
  const metadata = await page.locator('canvas.proyectos-canvas').evaluate(canvas => ({
    mode: canvas.dataset.modo, total: Number(canvas.dataset.proyectos), radius: Number(canvas.dataset.radio),
    zoom: Number(canvas.dataset.zoom), statuses: JSON.parse(canvas.dataset.estatus), groups: JSON.parse(canvas.dataset.grupos),
  }));
  assert.equal(metadata.mode, 'individual');
  assert.equal(metadata.total, total);
  assert.deepEqual(metadata.statuses, statuses);
  assert.deepEqual(metadata.groups, []);
  if (metadata.zoom <= 5) assert.equal(metadata.radius, 1);
}
async function checkReference(page) {
  await page.waitForFunction(() => document.querySelector('canvas.estados-canvas')?.dataset.estados === '32');
  const metadata = await page.locator('canvas.estados-canvas').evaluate(canvas => ({
    states: Number(canvas.dataset.estados), lines: Number(canvas.dataset.lineas),
    names: JSON.parse(canvas.dataset.nombres), labels: JSON.parse(canvas.dataset.etiquetas),
    z: Number(canvas.parentElement.style.zIndex), pointsZ: Number(document.querySelector('canvas.proyectos-canvas').parentElement.style.zIndex),
  }));
  assert.equal(metadata.states, 32);
  assert.equal(new Set(metadata.names).size, 32);
  assert.ok(metadata.names.includes('State of Mexico'));
  assert.ok(metadata.names.includes('Mexico City'));
  assert.ok(metadata.names.includes('San Luis Potosí'));
  assert.equal(metadata.lines, 690);
  assert.ok(metadata.z > metadata.pointsZ, 'Reference must be painted above project points');
  assert.equal(metadata.labels.length, 32, 'Every state has a visible national label');
}
async function checkAggregation(page, total, statuses) {
  const metadata = await page.locator('canvas.proyectos-canvas').evaluate(canvas => ({
    mode: canvas.dataset.modo, cell: Number(canvas.dataset.celda),
    statuses: JSON.parse(canvas.dataset.estatus), groups: JSON.parse(canvas.dataset.grupos),
  }));
  assert.equal(metadata.mode, 'agrupado');
  assert.equal(metadata.cell, 32);
  assert.deepEqual(metadata.statuses, statuses);
  const sums = [0, 0, 0, 0];
  for (const group of metadata.groups) {
    assert.equal(group.conteos.length, 4);
    assert.equal(group.conteos.reduce((a, b) => a + b, 0), group.n);
    group.conteos.forEach((n, g) => { sums[g] += n; });
  }
  assert.equal(metadata.groups.reduce((n, g) => n + g.n, 0), total);
  assert.deepEqual(sums, statuses);
}
async function clickVisibleGroup(page) {
  const selected = await page.locator('canvas.proyectos-canvas').evaluate(canvas => {
    const [lat, lon, zoom] = new URL(location.href).searchParams.get('c').split(',').map(Number);
    const s = Math.sin(lat * Math.PI / 180), scale = 2 ** zoom;
    const center = [(lon + 180) / 360 * 256 * scale,
      (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * 256 * scale];
    const map = document.getElementById('mapa').getBoundingClientRect();
    return JSON.parse(canvas.dataset.grupos).map(group => ({ ...group,
      px: group.x - center[0] + map.width / 2, py: group.y - center[1] + map.height / 2, zoom,
    })).filter(group => group.px > 400 && group.px < map.width - 40 && group.py > 80 && group.py < map.height - 80)
      .sort((a, b) => b.n - a.n)[0];
  });
  assert.ok(selected, 'A populated aggregate must be clickable in the visible map');
  await page.locator('#mapa').click({ position: { x: selected.px, y: selected.py } });
  await page.locator(`[data-grupo-total="${selected.n}"]`).waitFor();
  assert.equal(await page.locator('[data-grupo-total]').getAttribute('data-grupo-estatus'), selected.conteos.join(','));
  await page.waitForFunction(zoom => Number(document.querySelector('canvas.proyectos-canvas')?.dataset.zoom) === zoom + 2, selected.zoom);
  await page.locator('.leaflet-popup-close-button').click();
}
async function newPage(){const page=await browser.newPage({viewport:{width:1500,height:938}});page.on('pageerror',e=>errors.push(e.message));await page.route(/^https?:\/\/(?!127\.0\.0\.1:)/,r=>r.abort());
  // Inspect text actually painted on current local tiles, including after redraw.
  await page.addInitScript(() => {
    const proto = CanvasRenderingContext2D.prototype, clear = proto.clearRect, fill = proto.fillText;
    proto.clearRect = function (...args) { this.canvas.__paintedLabels = []; return clear.apply(this, args); };
    proto.fillText = function (...args) { (this.canvas.__paintedLabels ||= []).push(String(args[0])); return fill.apply(this, args); };
  });
  return page;
}
async function checkLocalLabels(page, visible) {
  await page.waitForFunction(visible => {
    const tiles = [...document.querySelectorAll('canvas.leaflet-tile-loaded')];
    const labels = tiles.flatMap(canvas => canvas.__paintedLabels || []);
    return tiles.length > 0 && (visible ? labels.includes('Ciudad de México') : labels.length === 0);
  }, visible);
}
const url = (port,q='estado=0&capa=proyectos')=>`http://127.0.0.1:${port}/?lang=en&modo=claro&teselas=local&${q}`;
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;
  browser=await chromium.launch({ headless: true, ...(process.platform === 'win32' ? { channel: 'msedge' } : {}) });
  const page=await newPage();
  const requests=new Map();page.on('request',r=>{const m=r.url().match(/05_puntos_2024\/(\d+)\.json/);if(m)requests.set(m[1],(requests.get(m[1])||0)+1);});
  const start=Date.now();await page.goto(url(port));await waitCount(page,expected.total);
  console.log('Initial national ready ms:',Date.now()-start);
  assert.equal(await page.locator('#estadoObras').inputValue(),'0');
  assert.equal(await page.locator('#estadoObras option').first().textContent(),'All Mexico');
  assert.equal(await page.locator('#filtroUbicacion').isHidden(),true);
  assert.match(await page.locator('#filtroConteo').textContent(),/253,346 of 253,346/);
  await checkIndividuals(page, expected.total, expectedStatuses);
  await checkReference(page);
  await checkLocalLabels(page, false);
  assert.match(await page.locator('#leyenda').textContent(), /Individual projects/);
  assert.equal(await page.locator('#resumenesEstatus').isChecked(), false);
  assert.equal(await page.locator('#mostrarLimites').isChecked(), true);
  await page.locator('#mostrarLimites').uncheck();
  await page.waitForFunction(() => !document.querySelector('canvas.estados-canvas'));
  assert.equal(new URL(page.url()).searchParams.get('limites'), '0');
  await checkLocalLabels(page, true);
  await checkIndividuals(page, expected.total, expectedStatuses);
  await page.locator('#mostrarLimites').check();await checkReference(page);
  await checkLocalLabels(page, false);
  assert.equal(new URL(page.url()).searchParams.has('limites'), false);
  await page.setViewportSize({width:1600,height:980});
  await page.waitForFunction(() => document.querySelector('canvas.estados-canvas')?.style.width === '1600px');
  await page.locator('#modo').click();
  await checkIndividuals(page, expected.total, expectedStatuses);
  assert.equal(await page.locator('canvas.estados-canvas').count(), 1);
  await page.locator('#modo').click();
  await page.setViewportSize({width:1500,height:938});
  console.log('PASS default individual points, 32 state reference labels, layer order, toggle, resize and theme');
  await page.locator('#resumenesEstatus').check();
  await page.waitForFunction(() => document.querySelector('canvas.proyectos-canvas')?.dataset.modo === 'agrupado');
  assert.equal(new URL(page.url()).searchParams.get('agrupado'), '1');
  await checkAggregation(page, expected.total, expectedStatuses);
  assert.match(await page.locator('#leyenda').textContent(), /logarithmic count scale/);
  const boundaryGroups = await page.evaluate(() => ProyectosMapa.agrupar([
    { x0: 0, y0: 0, g: 0 }, { x0: 31.999, y0: 0, g: 1 },
    { x0: 32, y0: 0, g: 2 }, { x0: -0.01, y0: 0, g: 3 },
    { x0: 0, y0: 32, g: 0 },
  ], 0));
  assert.deepEqual(boundaryGroups, [
    { x: 16, y: 16, n: 2, conteos: [1, 1, 0, 0] },
    { x: 48, y: 16, n: 1, conteos: [0, 0, 1, 0] },
    { x: -16, y: 16, n: 1, conteos: [0, 0, 0, 1] },
    { x: 16, y: 48, n: 1, conteos: [1, 0, 0, 0] },
  ]);
  await page.locator('#filtrosEstatus button').nth(0).click();await waitCount(page,expected.noCompleted);
  await checkAggregation(page, expected.noCompleted, statusCounts(source.filter(p => p.g !== 0)));
  await page.locator('#filtrosAdicionales').evaluate(el=>el.open=true);
  await page.locator('#filtrosEvidencia button').nth(0).click();await waitCount(page,expected.noCompletedDocs);
  await page.locator('#estadoObras').selectOption('15');await waitCount(page,expected.state15Filtered);
  assert.equal(await page.locator('#filtrosEstatus button').nth(0).getAttribute('aria-pressed'),'false');
  assert.equal(await page.locator('#filtrosEvidencia button').nth(0).getAttribute('aria-pressed'),'true');
  await page.locator('#estadoObras').selectOption('0');await waitCount(page,expected.noCompletedDocs);
  await page.locator('#restablecerFiltros').click();await waitCount(page,expected.total);
  await checkAggregation(page, expected.total, expectedStatuses);
  // A group reports its exact composition and zooms; a second drilldown reveals individuals.
  await clickVisibleGroup(page);
  await checkAggregation(page, expected.total, expectedStatuses);
  await clickVisibleGroup(page);
  assert.equal(await page.locator('canvas.proyectos-canvas').getAttribute('data-modo'), 'individual');
  assert.deepEqual(JSON.parse(await page.locator('canvas.proyectos-canvas').getAttribute('data-estatus')), expectedStatuses);
  assert.equal(new URL(page.url()).searchParams.get('estado'), '0');
  console.log('PASS all-record aggregation, four-status conservation, cell boundaries and group drilldown');
  await page.locator('#resumenesEstatus').uncheck();
  assert.equal(new URL(page.url()).searchParams.has('agrupado'), false);
  await page.locator('#vistaMunicipios').click();assert.equal(await page.locator('canvas.proyectos-canvas').count(),0);
  await page.locator('#vistaProyectos').click();await waitCount(page,expected.total);
  assert.equal(requests.size,32);assert.ok([...requests.values()].every(n=>n===1),'Cache should reuse each partition');
  for(let i=0;i<5;i++){await page.locator('.leaflet-control-zoom-in').click();await page.waitForTimeout(300);}
  await page.waitForTimeout(650);assert.equal(new URL(page.url()).searchParams.get('estado'),'0');
  const zoom=Number(new URL(page.url()).searchParams.get('c').split(',')[2]);assert.ok(zoom>=9);
  await page.locator('#vistaNacional').click();await waitCount(page,expected.total);
  assert.equal(new URL(page.url()).searchParams.get('estado'),'0');
  await checkIndividuals(page, expected.total, expectedStatuses);
  await page.locator('#buscar').fill('MEX17170401001337');await page.locator('#sugerencias button').first().click();
  await page.locator('#detalle h2').waitFor();assert.equal(new URL(page.url()).searchParams.get('estado'),'0');
  await page.locator('#cerrarDetalle').click();
  const p=source.find(p=>p.folio==='MEX17170401001337');
  const pixel=await page.evaluate(p=>{const [lat,lon,z]=new URL(location.href).searchParams.get('c').split(',').map(Number);const xy=(lat,lon)=>{const s=Math.sin(lat*Math.PI/180);return[(lon+180)/360*256,(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*256];};const a=xy(p.lat,p.lon),b=xy(lat,lon),r=document.getElementById('mapa').getBoundingClientRect();return{x:(a[0]-b[0])*2**z+r.width/2,y:(a[1]-b[1])*2**z+r.height/2};},p);
  await page.locator('#mapa').click({position:pixel});await page.locator('#detalle h2').waitFor();
  await page.close();console.log('PASS national/state/filter/cache/zoom/search/canvas-click');

  const race=await newPage();
  await race.route('**/05_puntos_2024/[1-6].json',async r=>{await new Promise(x=>setTimeout(x,800));await r.continue();});
  await race.goto(url(port));await race.locator('#estadoObras').waitFor();await race.waitForFunction(()=>document.querySelector('#estadoObras')?.options.length===33);
  await race.locator('#estadoObras').selectOption('15');await waitCount(race,expected.state15Visible);await race.waitForTimeout(1200);
  assert.equal(await race.locator('#estadoObras').inputValue(),'15');assert.equal(await race.locator('canvas.proyectos-canvas').getAttribute('data-proyectos'),String(expected.state15Visible));
  await race.locator('#estadoObras').selectOption('0');await waitCount(race,expected.total);
  await race.close();console.log('PASS national-to-state race and resumed national load');

  const fail=await newPage();let failures=0;
  await fail.route('**/05_puntos_2024/3.json',r=>{if(!failures++){return r.fulfill({status:503,body:'unavailable'});}return r.continue();});
  await fail.goto(url(port));await fail.locator('#reintentarProyectos').waitFor({state:'visible'});
  assert.equal(await fail.locator('#estadoObras').getAttribute('aria-busy'),'false');
  await fail.waitForTimeout(200);assert.equal(await fail.locator('#reintentarProyectos').isVisible(),true);
  await fail.locator('#reintentarProyectos').click();await waitCount(fail,expected.total);assert.equal(failures,2);
  await fail.close();console.log('PASS failed partition recovery');

  const badIndex=await newPage();let indexFails=0;
  await badIndex.route('**/05_puntos_2024/indice.json',r=>{if(!indexFails++)return r.fulfill({status:503,body:'unavailable'});return r.continue();});
  await badIndex.goto(url(port,'estado=todos&capa=proyectos'));await badIndex.locator('#reintentarProyectos').waitFor({state:'visible'});
  await badIndex.locator('#reintentarProyectos').click();await waitCount(badIndex,expected.total);assert.equal(indexFails,2);
  assert.equal(new URL(badIndex.url()).searchParams.get('estado'),'0');
  await badIndex.close();console.log('PASS index retry and todos alias');

  const noReference=await newPage();
  await noReference.goto(url(port,'estado=0&capa=proyectos&limites=0&agrupado=1'));
  await waitCount(noReference,expected.total);
  assert.equal(await noReference.locator('canvas.estados-canvas').count(),0);
  assert.equal(await noReference.locator('#mostrarLimites').isChecked(),false);
  assert.equal(await noReference.locator('#resumenesEstatus').isChecked(),true);
  await checkAggregation(noReference, expected.total, expectedStatuses);
  await noReference.close();console.log('PASS shared reference and summary URL options');

  const boundaryFailure=await newPage();let referenceFails=0;
  await boundaryFailure.route('**/mapa-base/mexico.json',r=>{referenceFails++;return r.fulfill({status:503,body:'unavailable'});});
  await boundaryFailure.goto(url(port));await waitCount(boundaryFailure,expected.total);
  await boundaryFailure.locator('#errorLimites').waitFor({state:'visible'});
  await checkIndividuals(boundaryFailure,expected.total,expectedStatuses);
  assert.equal(await boundaryFailure.locator('canvas.estados-canvas').count(),0);
  await boundaryFailure.unroute('**/mapa-base/mexico.json');
  await boundaryFailure.locator('#reintentarLimites').click();await checkReference(boundaryFailure);
  assert.equal(await boundaryFailure.locator('#errorLimites').isHidden(),true);
  assert.ok(referenceFails>=1);
  await boundaryFailure.close();console.log('PASS reference failure does not block projects and retry recovers');
  assert.deepEqual(errors,[]);console.log('PASS no browser script errors');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.close();});
