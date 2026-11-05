# Manuscrito de obras públicas para IJCOPI

- [Paper37_IJCOPI_v1_extendida.docx](Paper37_IJCOPI_v1_extendida.docx): versión vigente para revisión de autores.
- [Paper37_IJCOPI_v0_fiel.docx](Paper37_IJCOPI_v0_fiel.docx): base congelada para comparar la extensión; no modificar.

Ambos Word se copiaron sin cambios desde `PublicMunicipalWorks_DWH/paper/ijcopi/`,
rama `ijcopi-obras`. La v1 incluye los enlaces y la cita de PublicMunicipalWorks_IJCOPI
preparados en la revisión del 4 de noviembre de 2026. Su presencia aquí no constituye
aprobación final ni envío a la revista.

Revisión local del 5 de noviembre de 2026: v1 regenerada desde el script original,
15 páginas y 9,655 palabras (41.07 % sobre las 6,844 de la base). Se precisaron el
alcance de la evidencia sintética y oficial, el uso de exportaciones estáticas en el mapa,
la aproximación geográfica y el trabajo futuro. Se conservaron los autores, la plantilla,
las siete ecuaciones nativas y el marcado amarillo. Gabriel autorizó el commit y push
de esta revisión el 5 de noviembre de 2026; sigue pendiente la aprobación final de autores.

Los generadores y fuentes permanecen en el repositorio original: el texto se modifica
mediante `paper/ijcopi/extender_v1.py`; no editar estos Word a mano. Cada actualización
debe regenerarse en el original y copiarse aquí, conservando la v0. Cada commit y push
requiere autorización expresa de Gabriel y el verificador Springer sin fallos.

Al clonar este repositorio se recuperan ambos Word. Para regenerarlos se necesitan
también el proyecto original, sus instrucciones y dependencias. Git solo recupera archivos
publicados; los cambios locales y los chats de Codex no se trasladan automáticamente.
Esta carpeta no se sirve en Pages: el workflow publica únicamente `lakehouse/sitio/`.
