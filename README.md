# Public works analysis reproducibility materials

Source code, exported official data and a static demonstrator accompany the
research on municipal public works. Official records and the synthetic conference
demonstration are separate datasets.

## Interactive demonstrator

The static site is in `lakehouse/sitio/`. Open the [map](lakehouse/sitio/) or the
[paired queries and provenance](lakehouse/sitio/consultas.html). The root entry
point forwards to the map and retains query parameters and fragments. Serve that directory
over HTTP or HTTPS; opening the HTML as a local file can prevent data loading.
The demonstrator reads exported JSON and does not issue live database queries.

For a local preview with Python:

```sh
python -m http.server 8000 --directory lakehouse/sitio
```

## Reproduction

Follow `lakehouse/README.md` for the environment, official source downloads,
bronze/silver/gold construction and additive PostgreSQL load. Official source
locations and SHA-256 values are recorded in `lakehouse/fuentes.json`.
`lakehouse/consultas/README.md` describes the seven PostgreSQL/DuckDB query pairs.
`lakehouse/verificacion/` holds the verification scripts and recorded evidence.
`lakehouse/grafo/` contains the RDF mappings, queries and reproduction instructions.
The original synthetic warehouse components remain in `backend/`, `db/`,
`docker/` and `scripts/`. Reproduction can rebuild data; inspect the instructions
and scripts before running the complete pipeline.

## Licences and attribution

Code copyright and the MIT permission notice remain in `LICENSE.md`. Human origin
credits and dataset/provider licence information are retained in `CREDITS.md` and
the accompanying source files. Third-party map and library notices are unchanged.
Manuscripts, editorial history and Git metadata are not included in this source
snapshot.

## Review-host data transport

Some review hosts apply an opaque-origin CSP sandbox without same-origin access.
For that environment, `scripts/preparar_jsonp_revision.py` builds deterministic
`.jsonp.js` companions for the site's JSON and GeoJSON files. The original files,
published hashes, query results and historical performance measurements remain
unchanged. Rebuild companions after updating an original export.

`revision.js` loads before the shared site code. Only on the review host or an
opaque origin, local JSON GET requests use classic script companions allowed by
the existing sandbox. Each caller receives a fresh JSON Response; concurrent
requests share a cached load, with bounded retries and timeouts. A caller's abort
does not cancel other consumers. Remote geocoding and imagery requests retain
the browser's original fetch implementation. No permissions, credentials, CSP
directives or CORS headers are added or weakened.
