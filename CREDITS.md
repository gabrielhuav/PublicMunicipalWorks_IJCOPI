## Credit and licences

`backend/`, `db/`, `docker/` and `scripts/` come from the chapter's repository,
[`gabrielhuav/PublicMunicipalWorks_DWH`](https://github.com/gabrielhuav/PublicMunicipalWorks_DWH), whose
origin is [`Urigc/Obras_publicas`](https://github.com/Urigc/Obras_publicas) by Uriel González Casiano and
Marco Tulio Maldonado Mejía. The extension is `lakehouse/` and two scripts:
`scripts/evaluacion/eval_criterio_costo.py`, which evaluates the per-type cost criterion, and
`scripts/cifras_capitulo.py`. Code is released under the MIT licence; see `LICENSE.md`.

Data keep the terms of their publishers, listed file by file in `lakehouse/fuentes.json`: SHCP under
its [terms of use](https://www.transparenciapresupuestaria.gob.mx/es/PTP/Terminos_y_Condiciones),
INEGI as open data and CONEVAL under CC BY 4.0. Leaflet 1.9.4 is included in `lakehouse/sitio/vendor/`
under its BSD-2-Clause licence. Base map tiles come from the providers credited on the map; the offline
copy the map falls back to is made with Natural Earth (public domain) by `lakehouse/etl/mapa_base.py`.
