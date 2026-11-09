/* Las consultas detrás del mapa, y la comparación del lago contra el almacén tal como la
   escribió lakehouse/verificacion/verificar_lago.py. */
(function () {
  'use strict';

  const S = window.Sitio;
  const TXT = {
    es: {
      titulo: 'Consultas al lago y al almacén',
      lema: 'Lo que muestra el mapa es el resultado de estas consultas. Cada una se puede repetir en la base de datos.',
      'lago.titulo': 'El lago contra el almacén',
      'lago.texto': 'Las mismas consultas, escritas una vez para PostgreSQL y otra para DuckDB sobre el lago, dan resultados idénticos byte por byte.',
      'lago.nota': 'Milisegundos: media y percentil 95 de {n} repeticiones tras una de calentamiento. PostgreSQL {pg} con su configuración por omisión; DuckDB {duck} con {hilos} hilos; {anfitrion}.',
      'capas.titulo': 'Las consultas detrás de cada capa',
      'capas.texto': 'Con el almacén y el lago levantados, estos comandos repiten cada consulta y comparan el sitio con las bases de datos.',
      consulta: 'Consulta', filas: 'Filas', igual: 'Igual', si: 'sí', no: 'NO',
      archivos: 'repartidas en {n} archivos, uno por {col}; muestra: {muestra}',
      'col.id_entidad': 'estado', 'col.cvemun': 'municipio',
      'muestra.id_entidad': 'Estado de México', 'muestra.cvemun': 'Temascaltepec',
      'filas.n': '{n} filas', primeras: 'Ver las primeras {n} filas', sql: 'Ver SQL',
      'motor.pg': 'PostgreSQL (almacén)', 'motor.duck': 'DuckDB sobre el lago',
      'muestra.error': 'No se pudo cargar la muestra. Cierra y vuelve a abrir para reintentar.',
      'sql.comandos': 'SQL y comandos para reproducir',
    },
    en: {
      titulo: 'Queries to the lake and the warehouse',
      lema: 'What the map shows is the result of these queries. Each one can be repeated in the database.',
      'lago.titulo': 'The lake against the warehouse',
      'lago.texto': 'The same queries, written once for PostgreSQL and once for DuckDB over the lake, return results that are identical byte by byte.',
      'lago.nota': 'Milliseconds: mean and 95th percentile of {n} runs after one warm-up run. PostgreSQL {pg} with its default configuration; DuckDB {duck} with {hilos} threads; {anfitrion}.',
      'capas.titulo': 'The queries behind each layer',
      'capas.texto': 'With the warehouse and the lake running, these commands repeat every query and compare the site with the databases.',
      consulta: 'Query', filas: 'Rows', igual: 'Equal', si: 'yes', no: 'NO',
      archivos: 'split into {n} files, one per {col}; sample: {muestra}',
      'col.id_entidad': 'state', 'col.cvemun': 'municipality',
      'muestra.id_entidad': 'State of Mexico', 'muestra.cvemun': 'Temascaltepec',
      'filas.n': '{n} rows', primeras: 'Show the first {n} rows', sql: 'Show SQL',
      'motor.pg': 'PostgreSQL (warehouse)', 'motor.duck': 'DuckDB over the lake',
      'muestra.error': 'The sample could not be loaded. Close and reopen to retry.',
      'sql.comandos': 'SQL and commands to reproduce',
    },
  };
  const t = (k, v) => S.t(TXT, k, v);
  const TITULOS = {
    '01_resumen.pg.sql': ['Resumen por año', 'Summary by year'],
    '02_municipios.duck.sql': ['Población y rezago municipal', 'Population and deprivation'],
    '03_municipio_ciclo.pg.sql': ['Inversión y proyectos por municipio', 'Spending and projects by municipality'],
    '04_cruce_cngmd_2022.duck.sql': ['Contratos: INEGI y SHCP', 'Contracts: INEGI and SHCP'],
    '05_puntos_2024.duck.sql': ['Proyectos que aparecen en el mapa', 'Projects shown on the map'],
    '06_detalle_2024.duck.sql': ['Ficha y evidencia de cada proyecto', 'Project details and evidence'],
  };
  /* En español se usa el comentario de cada consulta; esto es su traducción. */
  const RESUMEN_EN = {
    '01_resumen.pg.sql': 'Summary by fiscal year of what the warehouse holds: states, municipalities, projects, amounts and how many projects each criterion flags. The criteria apply to investment projects only; they flag what to review and do not prove an irregularity.',
    '02_municipios.duck.sql': "The municipalities of the 2020 Census at the point of their seat (ITER locality 0001), with their population and CONEVAL's 2020 social deprivation level. The lake has no municipal polygons, so the map draws one point per municipality.",
    '03_municipio_ciclo.pg.sql': 'By municipality and fiscal year: projects, amounts and how many each criterion flags. Paid per inhabitant divides by the 2020 population. `evaluados` counts investment projects, the only ones the criteria apply to.',
    '04_cruce_cngmd_2022.duck.sql': 'Works contracts in 2022 according to two official sources: what each municipality declared to INEGI in the 2023 CNGMD, and the works contracts SHCP records with a municipality as the contracting party. A difference does not prove an irregularity: the CNGMD covers all municipal resources and SHCP only federally funded spending.',
    '05_puntos_2024.duck.sql': "The 2024 projects as map points, one file per state: what the map needs to draw, filter and search them. g is the status; marcas adds C1 = 1, C2 = 2, C3 = 4 and C4 = 8 and is null for non-investment projects; evidencia adds 1 if the agency published links, 2 if one is a PDF, 4 if one is a photo and 8 if the project started after the first release of Esri's imagery archive (2014-02-20). Flags ask for a review; they do not prove an irregularity.",
    '06_detalle_2024.duck.sql': "Details of the 2024 projects, one file per municipality, loaded when a project is opened: amounts, progress, dates and the links the agency published with SHCP for its contracts, shown as reported. Links to personal OneDrive sites are left out, because their path carries the uploader's e-mail account. Contractor names are not included.",
  };
  const PASOS = [
    'docker compose -f docker/compose.yml up -d db',
    'docker compose -f lakehouse/compose.yml up -d',
    'lakehouse/.venv/Scripts/python lakehouse/verificacion/verificar_capas.py',
  ].join('\n');
  const MUESTRA = { id_entidad: '15', cvemun: '15086' };

  function celda(v) {
    const s = v == null ? '' : (Array.isArray(v) ? v.join(' ') : String(v));
    const n = typeof v === 'number';
    return `<td${n ? ' class="n"' : ''}>${S.esc(s.length > 60 ? s.slice(0, 60) + '…' : s)}</td>`;
  }

  /* Las siete preguntas con el nombre que llevan en la Tabla 3 del artículo; el archivo se conserva
     debajo para encontrar la consulta en lakehouse/consultas/. */
  const PREGUNTAS = {
    '01_totales_por_ciclo': ['Proyectos y montos por año', 'Projects and amounts by year'],
    '02_clasificacion_2024': ['Gasto por estado y tipo, 2024', 'Spending by state and type, 2024'],
    '03_estado_de_mexico_2024': ['Estado de México, 2024', 'State of Mexico, 2024'],
    '04_rezago_2023': ['Pagado por habitante según rezago, 2023', 'Paid per head by deprivation, 2023'],
    '05_alertas_por_ciclo': ['Marcas por criterio y año', 'Flags by criterion and year'],
    '06_historial_de_un_folio': ['Estatus de un folio en cada año', 'Status of one folio in each year'],
    '07_temascaltepec': ['Temascaltepec por año', 'Temascaltepec by year'],
  };

  /* platform.version() da 10.0.<compilación>; desde la 22000 es Windows 11 aunque diga 10. */
  function anfitrion(texto) {
    const m = /^Windows 10\.0\.(\d+)$/.exec(texto || '');
    if (!m) return texto;
    const version = Number(m[1]) >= 22000 ? '11' : '10';
    return `Windows ${version} (${S.idioma === 'en' ? 'build' : 'compilación'} ${m[1]})`;
  }

  function lago(ev) {
    const cab = [t('consulta'), t('filas'), 'SHA-256', t('igual'), 'PostgreSQL ms', 'p95', 'DuckDB ms', 'p95']
      .map(x => `<th scope="col">${S.esc(x)}</th>`).join('');
    const nombre = k => {
      const p = PREGUNTAS[k];
      return p ? `${S.esc(p[S.idioma === 'en' ? 1 : 0])}<br><code>${S.esc(k)}</code>` : S.esc(k);
    };
    const filas = Object.entries(ev.consultas).map(([k, r]) => `<tr><td>${nombre(k)}</td>${celda(r.filas)}
      <td><code>${r.sha256.slice(0, 16)}…</code></td><td>${r.igual ? t('si') : t('no')}</td>
      ${celda(r.pg_ms)}${celda(r.pg_p95)}${celda(r.lago_ms)}${celda(r.lago_p95)}</tr>`).join('');
    document.getElementById('lago').innerHTML = `<table><thead><tr>${cab}</tr></thead><tbody>${filas}</tbody></table>`;
    const e = ev.entorno;
    document.getElementById('lagoNota').textContent = t('lago.nota', { n: e.repeticiones, pg: e.postgresql,
      duck: e.duckdb, hilos: e.hilos_duckdb, anfitrion: anfitrion(e.anfitrion) });
  }

  function tarjeta(c, man) {
    const cmd = c.motor === 'pg'
      ? `docker exec -i obras-publicas-db-1 psql -U obras -d obras_publicas < lakehouse/capas/${c.consulta}`
      : `lakehouse/.venv/Scripts/python lakehouse/consultas/lago.py lakehouse/capas/${c.consulta}`;
    const resumen = (S.idioma === 'en' && RESUMEN_EN[c.consulta])
      || c.sql.split('\n').filter(l => l.startsWith('--') && !l.startsWith('-- particion')).map(l => l.replace(/^--\s?/, '')).join(' ');
    const datos = c.particion ? `${c.datos}${MUESTRA[c.particion]}.json` : c.datos;
    const partes = c.particion ? ' · ' + t('archivos', { n: S.numero(c.archivos), col: t('col.' + c.particion), muestra: t('muestra.' + c.particion) }) : '';
    return `<section class="panel tarjeta">
      <h2>${S.esc((TITULOS[c.consulta] || [c.consulta, c.consulta])[S.idioma === 'en' ? 1 : 0])}</h2>
      <p>${S.esc(resumen)}</p>
      <p class="meta">${S.esc(t('motor.' + c.motor))} · ${S.esc(t('filas.n', { n: S.numero(c.filas) }))}${S.esc(partes)} · ${S.esc(man.generado_en)} · SHA-256 <code>${c.sha256_datos.slice(0, 16)}…</code></p>
      <details data-datos="${S.esc(datos)}"><summary>${S.esc(t('primeras', { n: Math.min(10, c.filas) }))}</summary><div class="tabla"></div></details>
      <details><summary>${S.esc(t('sql.comandos'))}</summary><p class="meta"><code>${S.esc(c.consulta)}</code></p><pre>${S.esc(cmd)}</pre><pre>${S.esc(c.sql)}</pre></details>
    </section>`;
  }

  /* Las filas se bajan solo al abrir la tarjeta. */
  function alAbrir(det) {
    det.addEventListener('toggle', async () => {
      const caja = det.querySelector('.tabla');
      if (!det.open || det.dataset.cargado === 'true' || caja.getAttribute('aria-busy') === 'true') return;
      caja.setAttribute('aria-busy', 'true');
      caja.textContent = t('cargando');
      try {
        const capa = await S.json('datos/' + det.dataset.datos);
        const cab = capa.columnas.map(x => `<th scope="col">${S.esc(x)}</th>`).join('');
        const cuerpo = capa.filas.slice(0, 10).map(f => `<tr>${f.map(celda).join('')}</tr>`).join('');
        caja.innerHTML = `<table><thead><tr>${cab}</tr></thead><tbody>${cuerpo}</tbody></table>`;
        det.dataset.cargado = 'true';
      } catch (e) {
        caja.textContent = t('muestra.error');
      } finally {
        caja.setAttribute('aria-busy', 'false');
      }
    });
  }

  async function iniciar() {
    S.pintarFijos(TXT);
    document.title = t('titulo');
    document.getElementById('pasos').textContent = PASOS;
    const status = document.getElementById('estado');
    try {
      const man = await S.json('datos/manifiesto.json');
      lago(await S.json('datos/' + man.evidencia.datos));
      document.getElementById('lista').innerHTML = man.consultas.map(c => tarjeta(c, man)).join('');
      document.querySelectorAll('details[data-datos]').forEach(alAbrir);
      status.hidden = true;
    } catch (e) {
      status.textContent = t('error', { msg: e.message });
    }
  }

  iniciar();
})();
