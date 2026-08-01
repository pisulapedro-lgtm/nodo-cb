# Prompt para evolucionar climabaires.com con fotografías reales

> Copiar todo el bloque de abajo y pegarlo en una sesión de Claude Code abierta sobre el repo `pisulapedro-lgtm/nodo-cb` (rama `claude/clima-baeres-argentina-plan-vzl5jx`). Antes de lanzar el prompt, subí las fotos originales a la carpeta `web/assets/img/originales/` (o adjuntalas a la sesión y el asistente las moverá ahí).

---

## PROMPT

Actúa como desarrollador web senior + editor fotográfico. Vas a evolucionar la web **climabaires.com** que ya existe en este repositorio, incorporando un lote grande de fotografías reales de obras, sin romper la identidad ni la arquitectura existente.

### Contexto del negocio

Clima Baires: venta + instalación certificada + posventa de aire acondicionado residencial premium en el corredor norte de Buenos Aires (Núñez, Vicente López, San Isidro, Tigre, Nordelta, Pilar). Nació en Málaga (España); el diferencial es transparencia de precios («lo que ves es lo que pagás»), presupuesto el mismo día y posventa real. Cliente objetivo: casas y barrios cerrados (Nordelta como objetivo clave). El canal de conversión nº 1 es WhatsApp; la agenda de visitas técnicas vive en Google Calendar y toda la operación corre sobre Google Workspace. El tráfico pago viene de Google Ads (cuenta argentina bajo la MCC de Málaga, con >€16.000 de histórico del mismo negocio en España).

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

**3. Conversión WhatsApp-first (la web es una máquina de iniciar chats):**
- **Regla editorial**: ninguna pantalla completa sin un CTA de WhatsApp visible. Cada sección relevante cierra con botón contextual; en móvil, añadir **barra inferior fija** con dos botones: «WhatsApp» y «Agendar visita» (ocultarla cuando el teclado está abierto).
- **Mensajes prellenados contextuales** (ya existe el patrón `data-wsp` en `main.js` — extenderlo): cada botón arma el texto con página/zona/servicio de origen. Ejemplos: desde `zonas/nordelta.html` → «Hola, estoy en Nordelta y quiero presupuesto de instalación»; desde el lightbox de la galería → «Vi la obra [nombre-foto] en su web, quiero algo así en casa»; desde la calculadora → ya incluye m² y frigorías calculadas (no tocar esa lógica, solo trazarla).
- **Botón flotante con nudge**: a los ~20 s o al 50% de scroll, mostrar una sola vez un globo discreto junto al botón flotante («¿Te pasamos presupuesto hoy?») — cerrable, sin sonido, sin repetir en la sesión (sessionStorage). Nada de popups de pantalla completa.
- **Todo clic medido**: cada CTA de WhatsApp, teléfono, email y agenda empuja un evento al dataLayer (spec abajo). Prohibido perder un clic sin atribución.

**4. Ecosistema Google (Workspace + Ads + Tag Manager):**
- **Google Tag Manager como única puerta de medición**: snippet GTM en `<head>`/`<body>` de todas las páginas vía el generador, con el ID en un solo lugar (`CB.gtmId` en `main.js` o constante del generador; placeholder `GTM-XXXXXXX` documentado en `web/README.md`). Sin gtag ni píxeles hardcodeados sueltos: GA4, Google Ads y el píxel de Meta se cargan DESDE GTM.
- **Spec de eventos dataLayer** (implementar exactamente y documentar en tabla en `web/README.md` para importarlos en GA4/Ads):
  | evento | parámetros | dispara |
  |---|---|---|
  | `whatsapp_click` | `origen` (hero/seccion/flotante/barra/lightbox/calculadora), `pagina`, `zona` | todo CTA de WhatsApp |
  | `agenda_click` | `origen`, `pagina`, `zona` | CTA «Agendar visita» |
  | `calculadora_uso` | `m2`, `frigorias_resultado`, `equipo_recomendado` | submit de la calculadora |
  | `form_envio` | `zona` | formulario de contacto |
  | `tel_click` / `email_click` | `pagina` | enlaces de contacto |
  Estos eventos son las **conversiones de Google Ads** (whatsapp_click y agenda_click como principales, calculadora_uso como secundaria) — dejar en el README el paso a paso de vincular GA4 ↔ Ads e importar conversiones, coherente con la cuenta bajo la MCC de Málaga.
- **Citas con Google Calendar (Workspace)**: integrar la **página de reservas de citas de Calendar** («appointment schedule» de ignacio@climabaires.com). Config central `CB.agendaUrl` (placeholder documentado). CTA «Agendar visita técnica» en: contacto, barra móvil, sección «Cuatro pasos» de servicios y confirmación de la calculadora. En `contacto.html`, además del enlace, **embeber el iframe de reservas** de Calendar (es la única excepción permitida a la regla «sin recursos externos», junto con GTM; que la página degrade elegante si el iframe no carga). Las reservas llegan solas a Calendar + Gmail de Ignacio — flujo de confirmación sin tocar código.
- **Gmail**: mantener `mailto:` centralizado con asunto/cuerpo prellenados por contexto («Presupuesto — Nordelta»). Las notificaciones de formulario no necesitan backend: el formulario sigue derivando a WhatsApp, y la cita de Calendar ya notifica por Gmail.
- **Google Ads readiness**: cada página de zona debe funcionar como landing de Ads — mensaje coherente con las keywords del histórico de Málaga (instalación / recambio / service / urgencia), carga < 2,5 s LCP en móvil, y CTA above the fold. No crear landings duplicadas: las páginas de zona SON las landings.

**5. Rendimiento y técnica (requisitos duros):**
- `loading="lazy"` en toda imagen bajo el fold; `srcset` con los dos tamaños; `width`/`height` explícitos para evitar CLS.
- Peso total de la home < 900 KB en la primera carga; ninguna imagen > 350 KB.
- Sin dependencias nuevas de runtime (nada de jQuery ni lightbox de terceros). Únicas cargas externas permitidas: **GTM** y el **iframe de reservas de Calendar** — ambas con carga diferida para no penalizar el LCP. Python con Pillow para el pipeline está OK.
- JSON-LD: en `obras.html` añadir `ImageObject`/`ItemList`; mantener el `HVACBusiness` existente.
- Accesibilidad: navegable por teclado, focus visible en filtros y lightbox.

**6. Qué NO tocar:**
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
7. GTM presente en las 13 páginas (incluida `obras.html`) con ID centralizado; los eventos del spec verificados en el QA de Playwright (simular clic en un CTA de WhatsApp y comprobar el push al dataLayer).
8. `CB.agendaUrl` y `CB.gtmId` como únicos puntos de configuración, documentados en `web/README.md` junto a la tabla de eventos y la guía de conversiones GA4 ↔ Ads.
9. Muéstrame antes/después de la home y la galería en capturas, y una tabla con: nº de fotos procesadas, peso total original → optimizado, y las fotos que necesiten que yo aclare descripción/zona.

Si algo del lote es inutilizable (borrosa, vertical extrema, sin relación con el negocio), apártala en `originales/descartadas/` con una línea de motivo — no la publiques.

---

## Cómo usarlo

1. Abrí una sesión de Claude Code sobre `pisulapedro-lgtm/nodo-cb` (rama `claude/clima-baeres-argentina-plan-vzl5jx`).
2. Subí tus fotos a `web/assets/img/originales/` (arrastrándolas a la sesión o por git).
3. Pegá el bloque PROMPT completo.
4. Cuando el asistente te liste las fotos ambiguas, contestá con zona/descripción de cada una — con eso los `alt` y los filtros quedan bien de verdad.
5. Tené a mano (o pedile al asistente que deje placeholders documentados): el **ID del contenedor GTM** (se crea gratis en tagmanager.google.com con la cuenta de Workspace) y la **URL de la página de reservas de Calendar** (Calendar → Crear → Agenda de citas, con ignacio@climabaires.com). Sin ellos la web funciona igual; con ellos, cada peso de Google Ads queda atribuido a chats y citas reales.
