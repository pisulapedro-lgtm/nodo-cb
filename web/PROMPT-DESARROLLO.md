# Prompt para evolucionar climabaires.com con fotografías reales

> Copiar todo el bloque de abajo y pegarlo en una sesión de Claude Code abierta sobre el repo `pisulapedro-lgtm/nodo-cb` (rama `claude/clima-baeres-argentina-plan-vzl5jx`). Antes de lanzar el prompt, subí las fotos originales a la carpeta `web/assets/img/originales/` (o adjuntalas a la sesión y el asistente las moverá ahí).

---

## PROMPT

Actúa como desarrollador web senior + editor fotográfico. Vas a evolucionar la web **climabaires.com** que ya existe en este repositorio, incorporando un lote grande de fotografías reales de obras, sin romper la identidad ni la arquitectura existente.

### Contexto del negocio

Clima Baires: venta + instalación certificada + posventa de aire acondicionado residencial premium en el corredor norte de Buenos Aires (Núñez, Vicente López, San Isidro, Tigre, Nordelta, Pilar). Nació en Málaga (España); el diferencial es transparencia de precios («lo que ves es lo que pagás»), presupuesto el mismo día y posventa real. Cliente objetivo: casas y barrios cerrados (Nordelta como objetivo clave). El canal de conversión nº 1 es WhatsApp.

### Punto de partida (NO empezar de cero)

La web ya está construida en `/web`: sitio **estático puro** (HTML/CSS/JS sin frameworks, sin CDN externos), 12 páginas:
`index` · `servicios` · `calculadora-frigorias` · `sobre-nosotros` · `contacto` · `404` · `zonas/{nunez, vicente-lopez, san-isidro, tigre, nordelta, pilar}` + `sitemap.xml` + `robots.txt`.

Piezas clave que debés respetar:
- **Generador**: las páginas se regeneran con `python3 web/tools/generar.py` (layout + contenidos en `PAGINAS`/funciones). Si tocás estructura común (header, footer, secciones repetidas), editá el generador y regenerá — no edites 12 HTML a mano.
- **Config de contacto centralizada**: `web/assets/js/main.js`, objeto `CB` (WhatsApp, email, redes). No dupliques datos de contacto en el HTML.
- **QA existente**: `npm run web:shots` (Playwright: captura 12 páginas × desktop/móvil y chequea enlaces + calculadora). Debe terminar en verde tras tus cambios.
- **Preview PDF**: `python3 web/tools/preview-pdf.py` regenera `dist/Web-climabaires-com-Preview_v0.9.pdf`.

### Identidad de marca (obligatoria, del Manual de Marca oficial)

- Azul primario `#0058B3` · celeste `#00A8FC` · navy `#00285A` · fondo hielo `#f2f7fc`.
- Tipografía Poppins (ya embebida en `web/assets/fonts/`, pesos 400/500/600/800).
- Logos ya extraídos: `web/assets/img/logo.svg` (color) y `logo-blanco.svg`; isotipo en `icon-512.png`.
- Prohibido (página «usos prohibidos» del manual): rotar, estirar, recolorear el logo o alterar el orden CLIMA/BAIRES.
- Tono de textos: es-AR (vos/tenés), directo, premium sin solemnidad.

### TAREA PRINCIPAL — integrar el lote de fotos reales

Las originales están en `web/assets/img/originales/` (pueden ser decenas, en JPG/HEIC/PNG, con nombres de cámara tipo IMG_1234).

**1. Pipeline de optimización (crear script `web/tools/fotos.py` y dejarlo documentado):**
- Leer cada original, corregir orientación EXIF, y exportar a `web/assets/img/obras/` en **WebP calidad 80**, en dos tamaños: `-1600` (ancho máx. 1600 px, para lightbox/hero) y `-800` (para tarjetas/grillas). Eliminar metadatos EXIF (privacidad: hay domicilios de clientes).
- Renombrar con patrón descriptivo kebab-case: `{tipo}-{detalle}-{zona}-{nn}.webp` (ej.: `instalacion-split-nordelta-01.webp`, `antes-despues-condensadora-san-isidro-02.webp`). Si el contenido de la foto no es evidente, listámelas y te paso yo la descripción antes de continuar — **no inventes ubicaciones ni marcas de equipos**.
- Generar un índice `web/assets/img/obras/index.json` con: archivo, alt, zona, tipo (instalación / recambio / mantenimiento / piso-techo / conductos / antes-después), destacada sí/no.
- **Alt SEO local** en cada foto: descriptivo + zona («Instalación de split inverter en dormitorio, Nordelta, Tigre») — nunca keyword stuffing.

**2. Dónde usar las fotos:**
- **Hero de la home**: reemplazar el degradado plano por una foto real de obra (la mejor horizontal) con overlay del degradado azul de marca al 75-85% para que el texto blanco siga legible (contraste AA mínimo).
- **Nueva página `obras.html`** («Obras recientes»): grilla responsive con filtros por zona y por tipo (JS puro, sin librerías), lightbox simple accesible (Escape para cerrar, navegación con flechas), y CTA a WhatsApp bajo la grilla. Añadirla al menú, al footer y al `sitemap.xml`.
- **Home**: nueva sección «Últimas obras» con las 6 destacadas del `index.json` y enlace a la galería.
- **Bloques antes/después**: componente de dos fotos lado a lado (o slider CSS simple) para los pares etiquetados `antes-`/`despues-`; usarlo en `servicios.html` (sección instalación) y en la galería.
- **Páginas de zona**: 1-2 fotos reales de ESA zona en cada página (si una zona no tiene fotos, dejarla como está — no rellenar con fotos de otra zona).
- **Sobre nosotros**: si hay fotos de equipo/vehículo/herramientas, una franja «así trabajamos».
- **Open Graph**: `og:image` de la home y de `obras.html` pasa a ser la mejor foto real (1200×630 recorte, generarlo en el pipeline).

**3. Rendimiento y técnica (requisitos duros):**
- `loading="lazy"` en toda imagen bajo el fold; `srcset` con los dos tamaños; `width`/`height` explícitos para evitar CLS.
- Peso total de la home < 900 KB en la primera carga; ninguna imagen > 350 KB.
- Sin dependencias nuevas de runtime (nada de CDNs, jQuery, lightbox de terceros); Python con Pillow para el pipeline está OK.
- JSON-LD: en `obras.html` añadir `ImageObject`/`ItemList`; mantener el `HVACBusiness` existente.
- Accesibilidad: navegable por teclado, focus visible en filtros y lightbox.

**4. Qué NO tocar:**
- Paleta, tipografías, logos y estructura del header/footer.
- La calculadora de frigorías y su lógica.
- El patrón de configuración de contacto (`CB` en `main.js`) y los placeholders de WhatsApp.
- Los textos legales/fiscales del resto del repo (carpetas `src/`, `build/`, `kit-digital/`): tu alcance es SOLO `/web`.

### Entrega y criterios de aceptación

1. `python3 web/tools/fotos.py` procesa el lote completo sin intervención manual (idempotente: correrlo dos veces no duplica).
2. `python3 web/tools/generar.py` regenera todo (incluida `obras.html`) sin warnings.
3. `npm run web:shots` en verde, ahora incluyendo `obras.html` en las capturas.
4. `python3 web/tools/preview-pdf.py` regenerado para que los socios revisen en PDF.
5. Actualizar `web/README.md` (sección nueva: «Cómo añadir fotos de obras») y el `sitemap.xml`.
6. Commit descriptivo en la rama actual + push. No crear PR salvo pedido expreso.
7. Muéstrame antes/después de la home y la galería en capturas, y una tabla con: nº de fotos procesadas, peso total original → optimizado, y las fotos que necesiten que yo aclare descripción/zona.

Si algo del lote es inutilizable (borrosa, vertical extrema, sin relación con el negocio), apártala en `originales/descartadas/` con una línea de motivo — no la publiques.

---

## Cómo usarlo

1. Abrí una sesión de Claude Code sobre `pisulapedro-lgtm/nodo-cb` (rama `claude/clima-baeres-argentina-plan-vzl5jx`).
2. Subí tus fotos a `web/assets/img/originales/` (arrastrándolas a la sesión o por git).
3. Pegá el bloque PROMPT completo.
4. Cuando el asistente te liste las fotos ambiguas, contestá con zona/descripción de cada una — con eso los `alt` y los filtros quedan bien de verdad.
