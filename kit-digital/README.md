# Kit digital — assets de marca

Las guías de alta ya **no viven acá**: son las secciones **15 y 16 del «Plan de Negocio»** (`dist/Plan-de-Negocio-Clima-Baires-Argentina_vX.Y.pdf`), con los textos listos para copiar y pegar. Se movieron para que haya una sola versión de cada cosa: mantener la misma guía en dos sitios garantizaba que se desincronizaran.

| Dónde está ahora | Qué contiene |
|---|---|
| Sección 15 del PDF | WhatsApp Business, Google Business Profile y Google Workspace |
| Sección 16 del PDF | Instagram, LinkedIn, calendario de contenidos y uso de estos assets |
| Sección 14 del PDF | Dominios, publicación de la web y los datos que hay que cargar tras cada alta |
| `web/README.md` | Detalle técnico del sitio: fotos, medición, blog y despliegue |

Esta carpeta conserva lo único que no es texto: las **piezas gráficas**.

## Assets (`assets/`)

| Archivo | Uso |
|---|---|
| `avatar-1080.png` | Foto de perfil de Instagram y WhatsApp (isotipo sobre blanco, uso v01 del manual) |
| `avatar-azul-1080.png` | Logo apilado blanco sobre azul (v02) — LinkedIn y fondos donde el blanco se pierde |
| `portada-linkedin-1584x396.png` | Banner de la página de empresa de LinkedIn |
| `portada-facebook-820x312.png` | Portada de Facebook (requisito para Instagram de empresa) y perfil de WhatsApp web |
| `post-plantilla-1080.png` | Plantilla de post cuadrado (reemplazar los textos [ENTRE CORCHETES]) |
| `story-plantilla-1080x1920.png` | Plantilla de historia con llamado a WhatsApp |
| `generar-assets.mjs` | Regenera todos los PNG desde los SVG de marca: `node kit-digital/assets/generar-assets.mjs` |

Colores exactos del Manual de Marca: azul `#0058B3` · celeste `#00A8FC` · navy `#00285A`. Tipografía Goldplay para piezas de diseño; Poppins (aproximación libre) en la web y en el PDF.
