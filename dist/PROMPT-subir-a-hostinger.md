# Prompt para subir climabaires.com a Hostinger

> Pegá todo lo que sigue en una sesión nueva de Claude Code, sobre el repo
> `pisulapedro-lgtm/nodo-cb`, rama `claude/climabaires-web-dev-hvk85y`.
>
> **Antes de pegarlo, completá los seis datos del bloque «Datos».** Sin ellos el
> script de publicación se niega a armar el paquete, y con razón: publicar con
> el WhatsApp de prueba deja todos los botones del sitio apuntando a un número
> que no existe.

---

Quiero publicar el sitio de este repo en **Hostinger**, bajo el dominio
**climabaires.com**.

## Qué hay

En la rama `claude/climabaires-web-dev-hvk85y`, la carpeta `web/` tiene el sitio
terminado: 21 páginas HTML estáticas, sin build ni dependencias. Leé
`web/README.md` antes de empezar.

Lo importante para publicar: **no se sube `web/`**. Esa carpeta pesa unos 40 MB
porque incluye las fotos originales sin optimizar y con metadatos EXIF (hay
domicilios de clientes ahí), las capturas de QA y los scripts. Subirla dejaría
todo eso accesible por URL.

Lo que se sube es lo que arma `python3 web/tools/publicar.py`, que deja en
`dist/sitio/` sólo lo que el navegador necesita: unos 5 MB, 76 archivos.

## Datos que tenés que cargar primero

Editá el bloque `CB` al inicio de `web/assets/js/main.js`:

- `whatsapp`: **«54911XXXXXXX»** (formato internacional, sin el +)
- `whatsappVisible`: **«+54 9 11 XXXX-XXXX»**
- `gtmId`: **«GTM-XXXXXXX»**
- `agendaUrl`: **«URL de la agenda de Google Calendar, o dejalo vacío»**

Editá el diccionario `EMPRESA` en `web/tools/generar.py`:

- `razon_social`, `cuit`, `domicilio`, `inicio_actividades`: **«…»**

Y en `web/terminos.html` queda un `PENDIENTE`: el **plazo de garantía de la
instalación** en meses. Ese texto lo genera `generar.py`, así que buscalo ahí.

Después de cargar todo: `python3 web/tools/generar.py` para rehornear los datos
en el HTML. Los botones de WhatsApp llevan el enlace escrito en el HTML, no sólo
en el JS, para que funcionen aunque el JavaScript no cargue — por eso hay que
regenerar.

## Paso 1 — armar el paquete

```bash
python3 web/tools/generar.py      # rehornea los datos nuevos
node web/tools/shots.mjs          # QA: si sale rojo, no sigas
python3 web/tools/publicar.py     # arma dist/sitio/
```

`publicar.py` corta si queda algo en `PENDIENTE` y te dice qué falta. **No uses
`--force` para saltearlo**: esa bandera es para armar una demo, no para
publicar.

Fijate que `dist/sitio/` tenga:

- las 21 páginas `.html`, `sitemap.xml`, `robots.txt`
- `assets/` con css, js, fonts e img — y **sin** `assets/img/originales/`
- `blog/` con el índice, las entradas y `rss.xml`
- **`.htaccess`** ← el importante, mirá el paso 3

## Paso 2 — subirlo

Hostinger tiene dos caminos. Elegí según lo que tengas a mano.

**a) Administrador de archivos (más simple, sin credenciales)**

Comprimí el contenido y decime dónde quedó el zip:

```bash
cd dist/sitio && zip -r ../climabaires-sitio.zip . -x '.DS_Store' && cd -
```

Yo lo subo desde hPanel → Archivos → Administrador de archivos, entro a
`public_html/`, borro lo que haya (Hostinger deja un `default.php` de bienvenida)
y descomprimo el zip **dentro de `public_html/`, no en una subcarpeta**.

**b) FTP (si me pasás las credenciales)**

Si preferís que lo suba yo, decímelo y te paso host, usuario y contraseña de FTP
(hPanel → Archivos → Cuentas FTP). Ojo: **el zip comprimido con `zip -r .` no
incluye los archivos que empiezan con punto en algunas versiones** — verificá
que `.htaccess` haya viajado, y si no, subilo aparte.

## Paso 3 — el `.htaccess`, que es lo que casi siempre se olvida

`publicar.py` genera tres archivos de configuración de servidor y **sólo uno le
sirve a Hostinger**:

| Archivo | Para qué | ¿Lo lee Hostinger? |
|---|---|---|
| `_headers` | caché | **No** — es de Cloudflare Pages y Netlify |
| `_redirects` | www → raíz | **No** — mismo caso |
| `.htaccess` | todo eso | **Sí** — Hostinger corre LiteSpeed/Apache |

Sin `.htaccess` el sitio se ve, pero: no fuerza https, `www.climabaires.com` no
redirige al dominio raíz, las fotos y las fuentes se vuelven a descargar en cada
visita, y un enlace roto muestra el 404 genérico de Hostinger en vez del que
tiene el sitio.

Así que **confirmá que `.htaccess` esté en `public_html/`**. En el administrador
de archivos hay que activar «mostrar archivos ocultos» para verlo.

Los otros dos son inofensivos: dejalos o borralos, da igual.

## Paso 4 — dominio y SSL

Decime dónde está registrado **climabaires.com**:

- **En Hostinger** → sólo hay que apuntarlo al hosting desde hPanel.
- **En otro registrador** (Namecheap, GoDaddy, Nic.ar…) → hay que cambiar los
  nameservers a los de Hostinger, o crear un registro A a la IP del hosting.
  Decime cuál preferís y te doy los valores exactos a cargar.

Después: hPanel → Seguridad → SSL, e instalar el certificado gratuito de Let's
Encrypt. **No se puede instalar antes de que el dominio apunte al hosting**, así
que ese es el orden. La propagación DNS puede tardar de minutos a 24 horas.

Cuando el SSL esté activo, activá también «Forzar HTTPS» en hPanel (el
`.htaccess` ya lo hace, pero que estén los dos no molesta).

## Paso 5 — verificar de verdad

No des el trabajo por terminado hasta comprobar esto, y mostrame el resultado:

1. `https://climabaires.com` carga y se ve el hero.
2. `http://climabaires.com` redirige a https con **un solo salto** (301).
3. `https://www.climabaires.com` redirige a la raíz.
4. `https://climabaires.com/una-pagina-que-no-existe` muestra el 404 del sitio
   (el que dice «Uy, esta página se quedó sin frío»), no el de Hostinger.
5. `https://climabaires.com/blog/` abre el índice del blog.
6. `https://climabaires.com/sitemap.xml` y `/robots.txt` responden.
7. Las fotos cargan (son `.webp`: si el servidor no las conoce las ofrece como
   descarga, y ahí hace falta revisar el `AddType` del `.htaccess`).
8. En el móvil: el botón de WhatsApp de la barra inferior abre el asistente, las
   cuatro preguntas se completan y el enlace final lleva al número real.
9. Las cabeceras de caché están puestas:
   `curl -sI https://climabaires.com/assets/fonts/poppins-400.woff2 | grep -i cache`

Podés verificar 1–7 con `curl -I` sin salir de la terminal.

## Paso 6 — después de publicar

1. **Google Search Console**: dar de alta `climabaires.com` y enviar el sitemap.
2. **Google Business Profile**: crear el perfil como *empresa de área de
   servicio* (sin dirección visible) con las seis zonas.
3. **GTM**: publicar el contenedor y crear los disparadores de evento
   personalizado para `whatsapp_click`, `agenda_click`, `calculadora_uso`,
   `form_envio` y `chatbot_inicio`. Están documentados en `web/README.md`.
4. En **Google Ads**, marcar `whatsapp_click` y `agenda_click` como conversiones
   primarias.

## Para actualizar el sitio más adelante

Cada vez que cambie algo, el ciclo es el mismo:

```bash
python3 web/tools/generar.py && node web/tools/shots.mjs && python3 web/tools/publicar.py
```

y volver a subir `dist/sitio/`. Como el blog publica solo una entrada cada tres
días, conviene repetir esto cada tanto o automatizarlo — si te interesa, pedime
que arme el despliegue automático por FTP y lo enchufo a la misma rutina.

## Lo que NO quiero

- Que subas `web/` en vez de `dist/sitio/`. Ahí están las fotos originales con
  metadatos.
- Que uses `--force` para saltear la puerta de publicación.
- Que des por bueno el despliegue sin correr las comprobaciones del paso 5.
- Que toques el diseño ni el contenido: esto es sólo publicar.
