# Manuscrito de obras públicas para IJCOPI

- [Paper37_IJCOPI_v1_extendida.docx](Paper37_IJCOPI_v1_extendida.docx): versión vigente para revisión de autores.
- [Paper37_IJCOPI_v0_fiel.docx](Paper37_IJCOPI_v0_fiel.docx): base congelada para comparar la extensión; no modificar.

Ambos Word se copiaron sin cambios desde `PublicMunicipalWorks_DWH/paper/ijcopi/`,
rama `ijcopi-obras`. La v1 incluye los enlaces y la cita de PublicMunicipalWorks_IJCOPI
preparados en la revisión del 4 de noviembre de 2026. Su presencia aquí no constituye
aprobación final ni envío a la revista.

Revisión editorial publicada en 191585d el 5 de noviembre de 2026: v1 regenerada desde el script original,
15 páginas y 9,655 palabras (41.07 % sobre las 6,844 de la base). Se precisaron el
alcance de la evidencia sintética y oficial, el uso de exportaciones estáticas en el mapa,
la aproximación geográfica y el trabajo futuro. Se conservaron los autores, la plantilla,
las siete ecuaciones nativas y el marcado amarillo. Gabriel autorizó el commit y push
de esta revisión el 5 de noviembre de 2026; sigue pendiente la aprobación final de autores.

Revisión visual posterior del 5 de noviembre: 15 páginas y 9,659 palabras
(41.13 % de ampliación). Se reubicó el bloque 6.1 para aprovechar el espacio de la página 6
y se actualizaron y ampliaron las capturas de las figuras 4 y 5 desde la web de IJCOPI.
La figura 3 histórica se conserva. En esa revisión, la referencia del software identificaba el commit
191585d, correspondiente a la interfaz capturada. Gabriel autorizó el commit y push de esta revisión;
la aprobación académica final y el envío a la revista siguen pendientes.

Revisión de errores del 9 de noviembre: 15 páginas y 9,769 palabras
(42.74 % sobre la base). Corrige el orden de autores de la referencia de CIDR 2021 (Armbrust
et al.), la regla de decisión frente a la puntuación de anomalía (Sección 3.5), el desglose de
los eventos de auditoría y de voto medido en la base, el sistema operativo de las mediciones
(Windows 11), la excepción de la consulta de un folio en la Sección 9.1 y el alcance de la
respuesta a RQ1. Añade la comparación pareada por semilla del criterio por tipo y su
repetición en semillas nuevas (52–61). Amarillo completo: 0 palabras nuevas sin resaltar.

El cierre precisa que C2 se activa al superar 120 días de retraso y que los intervalos
de la comparación pareada son IC del 95 % normales aproximados. Aclara la asistencia
en la implementación dentro de la declaración académica de IA y armoniza el año de
los encabezados con la portada. Se conservan los autores y contactos aprobados,
las siete ecuaciones nativas, las figuras y los valores de la Tabla 2. Se inspeccionaron
las 15 páginas renderizadas; resumen de 142 palabras y seis palabras clave.

Ese cierre citaba la versión estable del código y sus evidencias:
[8da559b](https://github.com/gabrielhuav/PublicMunicipalWorks_IJCOPI/tree/8da559b314d47ab0c7d9d17c3e6ab51ef1ca59f8).
El Word se publicó después en e4b35db. Gabriel autorizó
las correcciones y su commit y push el 9 de noviembre de 2026. La aprobación académica
final de los autores y el envío a la revista siguen pendientes.

Revisión posterior a la evaluación externa del 9 de noviembre: la versión vigente precisa
el monto aprobado y el logaritmo del costo unitario en C1 sobre registros federales, las
imágenes JPEG/PNG frente a referencias PDF, la autenticación de personal frente a sesiones
ciudadanas, el ajuste y evaluación retrospectivos sobre la misma muestra y la puntuación R2.
Los intervalos son normales aproximados; las métricas de la Tabla 2 se conservan.
La Figura 1 aclara la autenticación y la Figura 4 usa una captura nueva del mapa corregido.
Autores, contactos, siete ecuaciones nativas y base v0 se conservan.
Control final con Microsoft Word: 15 páginas y 9,744 palabras, 42.37 % sobre las 6,844
de v0; resumen de 142 palabras y seis palabras clave. Quince páginas renderizadas
inspeccionadas y cero palabras nuevas sin amarillo; figuras modificadas con marco amarillo.

La cita del código y sus evidencias corresponde ahora a
[661e7da](https://github.com/gabrielhuav/PublicMunicipalWorks_IJCOPI/tree/661e7dadee63e6f947a8fde3623a519fb15e9fe1),
que incluye la deduplicación de importes por municipio e identificador de contrato,
la URI de OC4IDS y las mejoras de la web. La nueva evidencia focalizada recalcula la capa 04
desde archivos oficiales; no reemplaza las mediciones históricas de rendimiento.
Gabriel autorizó las correcciones y su commit y push. Esta publicación sigue pendiente
de aprobación académica de los autores y no constituye envío a la revista.

Los generadores y fuentes permanecen en el repositorio original: el texto se modifica
mediante `paper/ijcopi/extender_v1.py`; no editar estos Word a mano. Cada actualización
debe regenerarse en el original y copiarse aquí, conservando la v0. Cada commit y push
requiere autorización expresa de Gabriel y el verificador Springer sin fallos.

Al clonar este repositorio se recuperan ambos Word. Para regenerarlos se necesitan
también el proyecto original, sus instrucciones y dependencias. Git solo recupera archivos
publicados; los cambios locales y los chats de Codex no se trasladan automáticamente.
Esta carpeta no se sirve en Pages: el workflow publica únicamente `lakehouse/sitio/`.
