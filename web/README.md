# Web climabaires.com — guía de despliegue

Sitio **estático** (HTML/CSS/JS puro, sin build ni dependencias): se puede publicar en cualquier hosting subiendo el contenido de esta carpeta `web/` tal cual.

## Antes de publicar (checklist obligatorio)

> Los datos de contacto siguen teniendo **un solo punto de configuración** (`CB` en
> `assets/js/main.js`), pero `generar.py` los lee y los hornea en el HTML: los
> botones de WhatsApp, el mailto y las redes funcionan aunque el JS no cargue.
> Por eso, después de tocar `CB` hay que **regenerar las páginas**.

1. **Número de WhatsApp argentino** — editar `assets/js/main.js`, bloque `CB` al inicio:
   - `whatsapp`: formato internacional sin `+` (ej. `5491160000000`).
   - `whatsappVisible`: cómo se muestra (ej. `+54 9 11 6000-0000`).
   - Hoy contiene un **placeholder** (`5491100000000`): la web no debe publicarse sin cambiarlo.
2. **Email** — mismo bloque (`info@climabaires.com` ya apunta al dominio; crear la casilla en Google Workspace antes).
3. **Redes** — actualizar `instagram` y `linkedin` en el mismo bloque cuando existan los perfiles definitivos (ver `/kit-digital`).
4. **Google Tag Manager** — `CB.gtmId` en el mismo bloque (hoy `GTM-XXXXXXX`, placeholder: no carga nada). Ver «Medición» más abajo.
5. **Agenda de visitas** — `CB.agendaUrl` en el mismo bloque (hoy vacío: los botones «Agendar visita» derivan a WhatsApp). Ver «Agenda» más abajo.
6. Si cambia el dominio (p. ej. se usa `climabaires.com.ar` como principal), regenerar las páginas: editar `DOMINIO` en `tools/generar.py` y correr `python3 web/tools/generar.py` (actualiza canónicas, Open Graph y sitemap).

## Cómo añadir fotos de obras

Las fotos reales viven en dos carpetas: `assets/img/originales/` (material en bruto,
con nombre de cámara/WhatsApp) y `assets/img/obras/` (derivados WebP optimizados que
se publican). El flujo:

1. Copiar los originales (JPG/PNG/WebP) a `assets/img/originales/`.
2. Abrir `tools/fotos.py` y agregar una entrada en `MAPEO` por cada foto:
   `slug` descriptivo en kebab-case (`{tipo}-{detalle}-{zona}-{nn}`), `alt` con la
   zona real (nunca inventar ubicación ni marca de equipo), `zona`, `tipo`
   (`instalacion / recambio / mantenimiento / piso-techo / conductos / antes-despues / equipo`)
   y `destacada` (las 6 destacadas salen en la home).
   - Pares antes/después: dos fotos con el mismo valor en `par`, slugs `antes-…` y `despues-…`.
   - Fotos inutilizables: entrada en `DESCARTES` con el motivo → van a `originales/descartadas/`.
3. `python3 web/tools/fotos.py` — corrige orientación EXIF, **elimina metadatos**
   (privacidad: hay domicilios), exporta WebP q80 en 1600/800 px, regenera el hero
   16:9 y los `og-*.jpg` 1200×630, y escribe `assets/img/obras/index.json`.
   Es idempotente; `--force` rehace todo. Ninguna imagen publicada supera 350 KB.
4. `python3 web/tools/generar.py` — reconstruye las páginas leyendo `index.json`
   (galería con filtros, «Últimas obras», hero de portada, franja «así trabajamos»).
5. `npm run web:shots` — el QA debe quedar en verde antes de publicar.

La foto de la tarjeta del hero (y de los `og:image`) se elige con `HERO_ORIGEN`
(+ ventanas `HERO_VENTANA_TARJETA` y `HERO_VENTANA_OG`) en `tools/fotos.py`.

## Medición: GTM + eventos dataLayer

**Google Tag Manager es la única puerta de medición**: GA4, Google Ads y el píxel de
Meta se configuran como etiquetas DENTRO del contenedor — nunca pegar snippets
sueltos en el HTML. El contenedor se crea gratis en
[tagmanager.google.com](https://tagmanager.google.com) con la cuenta de Workspace;
el ID (`GTM-XXXXXXX`) se pega en **un solo lugar**: `CB.gtmId` en `assets/js/main.js`.
`main.js` inyecta GTM en las 13 páginas con carga diferida (no penaliza el LCP); con
el placeholder no se carga nada y la web funciona igual.

Todos los CTA ya empujan eventos al `dataLayer` (verificado por el QA de Playwright):

| evento | parámetros | dispara |
|---|---|---|
| `whatsapp_click` | `origen` (hero/seccion/menu/barra/cinta/lightbox/calculadora/chatbot), `pagina`, `zona` | todo CTA de WhatsApp |
| `agenda_click` | `origen`, `pagina`, `zona` | CTA «Agendar visita» |
| `calculadora_uso` | `m2`, `frigorias_resultado`, `equipo_recomendado` | submit de la calculadora |
| `form_envio` | `zona` | formulario de contacto |
| `tel_click` / `email_click` | `pagina` | enlaces de teléfono / email |
| `chatbot_inicio` | `pagina` | apertura del asistente flotante |
| `chatbot_paso` | `paso` (1-4), `respuesta`, `pagina` | cada respuesta del asistente (el nombre NO se envía: sin datos personales en el dataLayer) |

**Chatbot**: el botón flotante abre un asistente de 4 preguntas (nombre, zona,
servicio, tipo de aire) que arma el mensaje y deriva a WhatsApp con
`origen=chatbot`. Sin backend ni librerías: vive en `assets/js/main.js`.

**Cobertura de conversión**: `npm run web:shots` falla si alguna página deja más
de 2,5 pantallas de scroll sin un CTA de WhatsApp en el flujo del documento (el
botón flotante y la barra móvil son fijos y no cuentan para la medición). Si al
agregar contenido salta ese error, intercalá una `cinta_cta(...)` del generador.

### Conectar GA4 y Google Ads (cuenta bajo la MCC de Málaga)

1. En GTM: crear etiqueta **GA4 Configuration** con el Measurement ID de la
   propiedad GA4 nueva (crearla como `climabaires.com — AR`). Disparador: All Pages.
2. Por cada evento de la tabla: etiqueta **GA4 Event** (mismo nombre de evento,
   parámetros mapeados desde variables de capa de datos) + disparador
   *Custom Event* con el nombre exacto (`whatsapp_click`, etc.). Publicar el contenedor.
3. En GA4 → Administración → Eventos: marcar `whatsapp_click` y `agenda_click`
   como **conversiones** (principales) y `calculadora_uso` (secundaria).
4. En Google Ads (la cuenta argentina de la MCC): **Herramientas → Conversiones →
   Importar → Google Analytics 4** y traer esas tres conversiones. Asignar
   `whatsapp_click` y `agenda_click` como acciones de conversión *primarias* de las
   campañas y `calculadora_uso` como *secundaria* (observación).
5. Vincular GA4 ↔ Ads: GA4 → Administración → Vinculaciones con Google Ads →
   elegir la cuenta AR de la MCC. Con esto cada peso invertido queda atribuido a
   chats y citas reales.

## Agenda de visitas (Google Calendar / Workspace)

1. Con `ignacio@climabaires.com`: Calendar → Crear → **Agenda de citas** (duración
   45–60 min, horario laboral, buffer de viaje). Copiar el enlace público de la
   página de reservas.
2. Pegarlo en `CB.agendaUrl` (`assets/js/main.js`). Desde ese momento:
   - los botones «Agendar visita» (barra móvil, servicios, calculadora, contacto)
     abren la página de reservas y miden `agenda_click`;
   - `contacto.html` embebe además el iframe de reservas (única carga externa junto
     a GTM, inyectada en diferido; si no carga, queda el botón).
3. Las reservas llegan solas a Calendar + Gmail: el flujo de confirmación no toca código.
4. Con `CB.agendaUrl` vacío los botones derivan a WhatsApp con mensaje de visita técnica.

## Dominios (los registra el usuario)

| Dominio | Dónde | Costo (08-2026) | Notas |
|---|---|---|---|
| climabaires.com | Cloudflare Registrar (a costo, ~USD 10/año) o cualquier registrador | ~USD 10-15/año | Principal del sitio |
| climabaires.com.ar | [nic.ar](https://nic.ar) | ARS 8.500 alta + 8.500/año | Requiere CUIT + clave fiscal nivel 2. Registrarlo **ya** para proteger la marca; redirigir 301 al .com |

## Logos

El sitio muestra `assets/img/logo.webp` y `logo-blanco.webp` (9 y 8 KB): son el
mismo logo rasterizado a 3× del tamaño de uso, indistinguible en pantalla. Los
**SVG originales siguen en el repo** (`logo.svg`, `logo-blanco.svg`) como fuente
de marca para imprenta, cartelería y kit digital — pesan 99 KB cada uno porque
vienen del manual con el texto convertido a curvas, y a 100 KB por página eran
el recurso más pesado del sitio.

Para regenerarlos tras un cambio de marca: abrir el sitio con
`npx http-server web -p 8099`, y con Playwright capturar `.logo img` y
`.logo-pie` con `deviceScaleFactor: 3`, guardando en WebP calidad 90.

## Qué se sube al hosting

**No subas `web/` tal cual**: pesa ~40 MB porque incluye los originales de las
fotos (sin optimizar y con metadatos), las capturas de QA y los scripts. Si se
publican, esas fotos quedan accesibles por URL.

```
npm run web:publicar     # deja el sitio listo en dist/sitio/ (~5 MB, 58 archivos)
```

El script copia sólo lo que el navegador necesita y agrega `_headers` (caché
larga para fuentes e imágenes, corta para HTML) y `_redirects` (www → dominio
raíz), que Cloudflare Pages y Netlify leen solos.

## Publicación recomendada (gratis, con SSL)

**Opción A — Cloudflare Pages** (recomendada: CDN + SSL + dominio en el mismo panel):
1. Crear cuenta en Cloudflare → Workers & Pages → *Create* → *Pages* → *Upload assets* (o conectar este repo de GitHub, *build command* vacío, *output dir* `web`).
2. Custom domain → `climabaires.com` (si el dominio está en Cloudflare, los DNS se configuran solos).

**Opción B — Netlify**: arrastrar la carpeta `web/` a [app.netlify.com/drop](https://app.netlify.com/drop) → *Domain settings* → agregar `climabaires.com` y seguir las instrucciones de DNS.

**Opción C — GitHub Pages**: *Settings → Pages* del repo, servir desde una rama que contenga solo `web/` (o usar Action de deploy). Custom domain + *Enforce HTTPS*.

En los tres casos: apuntar también `www` (CNAME) y verificar que `https://climabaires.com/sitemap.xml` responda.

## Después de publicar

1. **Google Search Console**: dar de alta la propiedad `climabaires.com`, enviar `sitemap.xml`.
2. **Google Business Profile**: crear el perfil como *empresa de área de servicio* (sin dirección visible) con las 6 zonas — guía completa en `/kit-digital/google-business/` si existe, o seguir el plan GTM del PDF.
3. **Analytics/Ads/Meta**: todo se configura dentro del contenedor GTM (sección «Medición» de arriba) — no pegar snippets en el HTML.

## Estructura

```
web/
├── index.html                  # inicio (hero con foto real + últimas obras)
├── servicios.html              # venta / instalación / posventa
├── obras.html                  # galería de obras: filtros + lightbox
├── calculadora-frigorias.html  # herramienta de captación
├── sobre-nosotros.html         # historia España → Argentina + «así trabajamos»
├── contacto.html               # WhatsApp + formulario + agenda de visitas
├── 404.html
├── zonas/{nunez,vicente-lopez,san-isidro,tigre,nordelta,pilar}.html  # SEO local / landings de Ads
├── sitemap.xml · robots.txt
├── assets/css/styles.css       # identidad de marca (paleta del manual)
├── assets/js/main.js           # config CB (contacto + gtmId + agendaUrl), medición, galería
├── assets/fonts/               # Poppins woff2 (aprox. libre de Goldplay)
├── assets/img/                 # logo.svg, logo-blanco.svg, iconos del isotipo
│   ├── originales/             # fotos en bruto (no se publican tal cual)
│   └── obras/                  # WebP optimizados + index.json (genera fotos.py)
└── tools/
    ├── fotos.py                # pipeline de fotos (python3 web/tools/fotos.py)
    ├── generar.py              # regenera todas las páginas (python3 web/tools/generar.py)
    └── shots.mjs               # QA: capturas + enlaces + eventos dataLayer (npm run web:shots)
```

Las capturas de QA se generan en `web/tools/shots/` y no se commitean.
