# Kit digital de puesta en marcha — Clima Baires Argentina

Todo lo necesario para dar de alta la presencia digital de la empresa. Las cuentas las creáis vosotros (requieren teléfono argentino, verificación de identidad y tarjeta); cada guía es paso a paso y deja los textos e imágenes listos para copiar y pegar.

## Orden de ejecución recomendado

| # | Qué | Guía | Antes necesitás |
|---|-----|------|-----------------|
| 1 | Dominios climabaires.com y .com.ar | `../web/README.md` | CUIT (para .com.ar) + tarjeta |
| 2 | Google Workspace (email @climabaires.com) | `google-workspace/guia.md` | Dominio comprado |
| 3 | WhatsApp Business | `whatsapp-business/guia.md` | Chip/línea argentina nueva para la empresa |
| 4 | Instagram | `instagram/guia.md` | WhatsApp activo (para el botón de contacto) |
| 5 | LinkedIn (página de empresa) | `linkedin/guia.md` | Email corporativo activo |
| 6 | Google Business Profile | `google-business/guia.md` | Web publicada + teléfono |

Después del alta de cada cuenta, **actualizar `web/assets/js/main.js`** (número de WhatsApp y URLs de redes) y regenerar la web si cambió el dominio.

## Assets incluidos (`assets/`)

| Archivo | Uso |
|---|---|
| `avatar-1080.png` | Foto de perfil IG / WhatsApp (isotipo sobre blanco, uso permitido v01 del manual) |
| `avatar-azul-1080.png` | Variante logo apilado blanco sobre azul (v02) — para LinkedIn o donde el blanco se pierda |
| `portada-linkedin-1584x396.png` | Banner de la página de empresa de LinkedIn |
| `portada-facebook-820x312.png` | Portada de Facebook (necesaria para IG empresa) y perfil de WhatsApp web |
| `post-plantilla-1080.png` | Plantilla de post cuadrado (reemplazar textos [ENTRE CORCHETES] en Canva/Figma) |
| `story-plantilla-1080x1920.png` | Plantilla de historia con CTA WhatsApp |
| `generar-assets.mjs` | Regenera todos los PNG desde los SVG de marca (`node kit-digital/assets/generar-assets.mjs`) |

Colores exactos (Manual de Marca): azul `#0058B3` · celeste `#00A8FC` · navy `#00285A`. Tipografía: Goldplay (la original del manual, para piezas de diseño) o Poppins (aproximación libre usada en web y PDF).

## Contenido

El plan de los primeros 10 posts (con copies listos) está en `calendario-contenidos.md`, alineado con el go-to-market del PDF (lanzamiento septiembre → pico diciembre).
