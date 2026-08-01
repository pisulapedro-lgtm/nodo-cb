# Web climabaires.com — guía de despliegue

Sitio **estático** (HTML/CSS/JS puro, sin build ni dependencias): se puede publicar en cualquier hosting subiendo el contenido de esta carpeta `web/` tal cual.

## Antes de publicar (checklist obligatorio)

1. **Número de WhatsApp argentino** — editar `assets/js/main.js`, bloque `CB` al inicio:
   - `whatsapp`: formato internacional sin `+` (ej. `5491160000000`).
   - `whatsappVisible`: cómo se muestra (ej. `+54 9 11 6000-0000`).
   - Hoy contiene un **placeholder** (`5491100000000`): la web no debe publicarse sin cambiarlo.
2. **Email** — mismo bloque (`info@climabaires.com` ya apunta al dominio; crear la casilla en Google Workspace antes).
3. **Redes** — actualizar `instagram` y `linkedin` en el mismo bloque cuando existan los perfiles definitivos (ver `/kit-digital`).
4. Si cambia el dominio (p. ej. se usa `climabaires.com.ar` como principal), regenerar las páginas: editar `DOMINIO` en `tools/generar.py` y correr `python3 web/tools/generar.py` (actualiza canónicas, Open Graph y sitemap).

## Dominios (los registra el usuario)

| Dominio | Dónde | Costo (08-2026) | Notas |
|---|---|---|---|
| climabaires.com | Cloudflare Registrar (a costo, ~USD 10/año) o cualquier registrador | ~USD 10-15/año | Principal del sitio |
| climabaires.com.ar | [nic.ar](https://nic.ar) | ARS 8.500 alta + 8.500/año | Requiere CUIT + clave fiscal nivel 2. Registrarlo **ya** para proteger la marca; redirigir 301 al .com |

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
3. **Pixel/Analytics**: cuando arranquen las campañas, añadir GA4 y el píxel de Meta antes de `</head>` en `tools/generar.py` (bloque `layout()`) y regenerar.

## Estructura

```
web/
├── index.html                  # inicio
├── servicios.html              # venta / instalación / posventa
├── calculadora-frigorias.html  # herramienta de captación
├── sobre-nosotros.html         # historia España → Argentina
├── contacto.html               # WhatsApp + formulario
├── 404.html
├── zonas/{nunez,vicente-lopez,san-isidro,tigre,nordelta,pilar}.html  # SEO local
├── sitemap.xml · robots.txt
├── assets/css/styles.css       # identidad de marca (paleta del manual)
├── assets/js/main.js           # config de contacto + menú + calculadora
├── assets/fonts/               # Poppins woff2 (aprox. libre de Goldplay)
├── assets/img/                 # logo.svg, logo-blanco.svg, iconos del isotipo
└── tools/
    ├── generar.py              # regenera todas las páginas (python3 web/tools/generar.py)
    └── shots.mjs               # QA: capturas desktop/móvil + enlaces (npm run web:shots)
```

Las capturas de QA se generan en `web/tools/shots/` y no se commitean.
