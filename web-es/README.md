# Web climabaires.es — guía de despliegue

Sitio **estático** (HTML/CSS/JS puro, sin build ni dependencias). Para publicarlo
se arma primero la carpeta ligera con `npm run es:publicar` y se sube
**`dist/sitio-es`**, nunca `web-es/` (ver «Qué se sube al hosting»).

## Qué relación tiene con `web/`

`web/` es **climabaires.com**, el sitio argentino, y sigue vivo. Este es su
hermano, no su traducción. Comparten arquitectura —el mismo generador en Python,
el mismo pipeline de fotos, el mismo QA de Playwright— y casi nada más, porque
son dos negocios distintos en dos países distintos:

| | `web/` (Argentina) | `web-es/` (España) |
|---|---|---|
| Obras locales | **No se muestran**: todavía no hay | **Sí**, con su municipio en el pie y en el `alt` |
| Antigüedad, reseñas, volumen | No se pueden afirmar | Se pueden y **se deben** mostrar |
| Idioma | Rioplatense (vos, tenés, acá) | Castellano de España (tú, tienes, aquí) |
| Marco legal | Ley 24.240, Ley 25.326 | RGPD, LOPDGDD, LSSI-CE, TRLGDCU |
| Desistimiento | 10 días + botón de arrepentimiento | **14 días naturales**, sin botón de arrepentimiento |
| Cookies | Sin banner | **Banner de consentimiento previo**, obligatorio |
| Aviso legal | No existe | **Página propia**, obligatoria (LSSI-CE art. 10) |
| Zonas | 6 del corredor norte del AMBA | 7 con landing + **toda la Costa del Sol** |
| Hemisferio | Sur: suma potencia el **norte** | Norte: suma potencia el **sur** |

Y una regla que va justo al revés que allí: **este sitio no menciona Argentina ni
Buenos Aires**, en ninguna parte. `tools/revisar-nota.py` lo bloquea igual que el
argentino bloquea cualquier mención a España.

Los dos sitios se generan y se despliegan por separado. Un cambio en `web/` no
toca `web-es/` y al revés: si arreglas algo estructural en uno, hay que llevarlo
a mano al otro.

## Antes de publicar (lista obligatoria)

> Los datos de contacto tienen **un solo punto de configuración** (`CB` en
> `assets/js/main.js`), pero `generar.py` los lee y los hornea en el HTML: los
> botones de WhatsApp, el mailto y las redes funcionan aunque el JS no cargue.
> Por eso, después de tocar `CB` hay que **regenerar las páginas**.

`npm run es:publicar` **se niega a armar el paquete** mientras quede algo de esta
lista sin completar. No es un capricho: cada línea rompe algo concreto.

### En `assets/js/main.js`, objeto `CB`

1. **WhatsApp español** — `whatsapp` en formato internacional sin `+`
   (ej. `34612345678`) y `whatsappVisible` como se muestra
   (ej. `+34 612 34 56 78`). Hoy contiene un valor de ejemplo (`34600000000`):
   con él, todos los botones del sitio llevan a un número inexistente.
2. **Email** — `info@climabaires.es` ya apunta al dominio; hay que crear el buzón
   antes de publicar.
3. **Redes** — `instagram` y `linkedin`. Están **vacíos a propósito**: mientras lo
   estén, el pie no muestra el enlace. Enlazar a un perfil que no existe es peor
   que no enlazar.
4. **Google Tag Manager** — `gtmId`. El contenedor argentino **no sirve**: son dos
   propiedades distintas, con dominios, campañas y audiencias distintas. Hay que
   crear uno nuevo. Ver «Medición».
5. **Agenda de visitas** — `agendaUrl`. Ver «Agenda».
6. **Place ID de Google** — `placeId`. Sin él no hay mapa en `contacto.html` ni
   enlaces a las reseñas. Ver «Reseñas de Google».
7. **Clave de Maps Embed API** — `mapsKey`, opcional. Ver «Reseñas de Google».

### En `tools/generar.py`

8. **`EMPRESA`** — denominación social, CIF/NIF, domicilio social y datos
   registrales (Registro Mercantil, tomo, folio, hoja), más el responsable del
   tratamiento de datos. Son los que exige el artículo 10 de la LSSI-CE y sin
   ellos el aviso legal no existe. Hoy salen como `PENDIENTE` en el pie de todas
   las páginas.
9. **`ANIOS_EXPERIENCIA`** — los años que lleva la empresa instalando en la
   Costa del Sol. Es el dato que este sitio sí puede mostrar y el argentino no, y
   sale en la franja de confianza de la portada. Tiene que ser real: no se estima.
10. **`METROS_INCLUIDOS`** — metros de tubería que entran en el precio cerrado.
    Es el único número del bloque «qué entra en el precio» de `servicios.html` y
    el primero que un cliente va a reclamar si no coincide.
11. **`GARANTIA_INSTALACION`** — plazo de garantía de la mano de obra. Aparece en
    servicios y en los términos, junto a la garantía legal de conformidad.

> **Qué se quitó y por qué.** La franja de confianza llegó a llevar el número de
> instalaciones realizadas y el número de registro como empresa instaladora
> habilitada (RITE). Los dos se retiraron a petición del titular: como sellos no
> aportaban lo que costaban —dos datos más que pedir antes de publicar— y el
> segundo, sin el número al lado, no prueba nada. En su lugar la franja habla de
> antigüedad, cobertura y obra propia, que se sostienen solas. Si algún día se
> quieren de vuelta, es una entrada más en `franja_confianza()` y una línea en
> `publicar.py`.

### En contenido

12. **`contenido/resenas.json`** — puntuación media y número de reseñas reales de
    la ficha de Google, más dos o tres textos transcritos con nombre y fecha
    reales. Ver «Reseñas de Google».
13. **`tools/fotos.py` → `MAPEO`** — el municipio de cada foto. Ver «Fotos de
    obras».

### Promesas operativas a confirmar

El sitio compromete por escrito **cómo se trabaja**. No son datos verificables
solos: hay que leerlas y confirmar que la operación las cumple, o cambiar el
texto en `tools/generar.py` antes de publicar.

| Dónde | Promesa |
| --- | --- |
| `bloque_quien_entra()` — nosotros + 6 zonas | La víspera se manda por WhatsApp el nombre, la foto y el documento del técnico, más la matrícula de la furgoneta |
| ídem | Franja de llegada de **dos horas**, furgoneta rotulada, aviso si hay retraso |
| ídem | Se cubren suelos y muebles; el aspirador lo trae el equipo |
| ídem | Se retiran embalaje, restos de obra **y el equipo antiguo** el mismo día, con recuperación del gas y entrega a gestor autorizado |
| ídem | La documentación que pide la comunidad de propietarios la presenta la empresa |
| `bloque_que_incluye()` — servicios | Las 10 líneas de «entra en el precio» (vacío con bomba, estanqueidad con nitrógeno, desagüe probado con agua, puesta en marcha medida, garantía por escrito) |
| ídem | Las 7 de «se cobra aparte»: que ninguna se cobre sin figurar antes en el presupuesto |
| ídem | Ante un extra durante la obra: se para, se enseña y se sigue **sólo con aprobación por WhatsApp** |
| `servicios.html` | Marcas listadas: Daikin, Mitsubishi Electric, LG, Samsung, Midea y Johnson — confirmar que son las que efectivamente se sirven |
| `CB.horario` | De lunes a sábado, de 8:00 a 19:00. De ahí sale la promesa de «respondemos en minutos» del asistente |
| `COBERTURA` y `OTRAS_ZONAS` | El sitio afirma dar servicio en **toda la Costa del Sol, de Manilva a Nerja**, y nombra once municipios más allá de los siete con landing. Confirmar que se va a todos |

> **Marcas**: se han quitado BGH y Surrey, que son argentinas y aquí no pintan
> nada, y se ha añadido **Johnson**, que aparece en una de las fotos de obra. Su
> logotipo (`assets/img/marcas/johnson.png`) se ha bajado del sitio oficial de la
> marca en España, que hoy lleva EAS Electric: viene a 174×36 con transparencia y
> se ha reescalado a los 80 px de alto de los demás endureciendo el canal alfa,
> porque es una marca plana de un solo color. Si el distribuidor os pasa el
> original en vectorial, sustituidlo y ganará un punto de nitidez.

> **Aerotermia**: el sitio **no la ofrece**, por decisión del titular. Se ha
> quitado de la tarjeta de servicios, de la FAQ de Marbella, del calendario del
> blog y de los datos estructurados, y `revisar-nota.py` bloquea la palabra para
> que la rutina automática no la reintroduzca. Lo que sí se dice es **bomba de
> calor**, que es el mismo equipo de aire dando calor en invierno.

## Cobertura: seis landings, una comarca entera

Las siete páginas de zona son las grandes ciudades de la costa entre Málaga y
Estepona: Málaga capital, Torremolinos, Benalmádena, Fuengirola, Mijas, Marbella
y Estepona. Existen por SEO local y por Google Ads, que es donde está el volumen
y donde tiene sentido gastar campaña. **No son el límite del servicio.** El sitio
dice en todas partes que se trabaja en toda la Costa del Sol, de Manilva a Nerja,
más el interior cercano, y nombra los municipios sin landing propia.

Dos constantes en `tools/generar.py` lo gobiernan todo:

- `COBERTURA` — la frase que se repite en el pie, en el hero, en «sobre
  nosotros», en contacto y en el aviso legal.
- `OTRAS_ZONAS` — los municipios sin página propia. Salen en prosa en la sección
  de zonas de la portada, en el pie de cada página de zona, en el pie del sitio y
  en el `areaServed` de los datos estructurados, que además declara «Costa del
  Sol» y «Provincia de Málaga» como áreas.

Si mañana alguno de esos municipios merece su propia landing, se añade a `ZONAS`
con su intro, sus barrios, su párrafo `especial` y sus cuatro preguntas en
`faq-zonas.json`, y se quita de `OTRAS_ZONAS`. El resto —chips, pie, sitemap,
selector del formulario, opciones del asistente— se actualiza solo.

## Cookies y consentimiento (esto no existe en el sitio argentino)

En la UE, nada que no sea estrictamente necesario puede cargarse **antes** de que
el usuario diga que sí (LSSI-CE art. 22.2 y RGPD). Aquí eso afecta a tres cargas:

- **Google Tag Manager** —y con él GA4, Ads y cualquier píxel—,
- el **iframe de la agenda** de Google Calendar en `contacto.html`,
- el **mapa** de la ficha de Google en `contacto.html`.

Ninguna se inyecta hasta que hay consentimiento. Cómo está resuelto:

- Banda inferior, no muro: el sitio se lee entero mientras se decide.
- **Aceptar** y **Rechazar** tienen el mismo tamaño y el mismo número de clics,
  que es lo que exige la guía de la AEPD. No hay «aceptar» destacado con un
  «configurar» escondido.
- Mientras la banda está abierta se ocultan el botón flotante, la barra inferior
  móvil y el aviso emergente: no hay dos capas peleando por la esquina.
- Se usa **Consent Mode v2**: los permisos se declaran denegados antes de que
  exista GTM y se actualizan sólo al aceptar.
- La decisión se guarda en `localStorage` (`cb-cookies`). El enlace
  **«Preferencias de cookies»** del pie la borra y vuelve a preguntar: es el modo
  de retirar un consentimiento ya dado.
- Si se rechaza, el sitio funciona igual. Lo único que se pierde es el mapa y la
  reserva incrustados; los dos tienen botón que abre Google en otra pestaña,
  cosa que decide el usuario y no necesita permiso previo.
- `contenido`/`cookies.html` documenta la lista de cookies. Si se añade una carga
  externa nueva, **hay que actualizar esa tabla**.

El QA lo comprueba en las 18 páginas: si una se queda sin banner, falla.

## Reseñas de Google

Google **no permite incrustar el texto de las reseñas con un iframe**. Las
opciones reales, y por qué se eligió la que se eligió:

| Opción | Da | Coste |
|---|---|---|
| Mapa incrustado (Maps Embed API) | Ficha, puntuación y número de reseñas. **No** el texto | Gratis; la API oficial pide clave |
| Places API | Hasta 5 reseñas en JSON, actualizadas solas | Clave + facturación activa + políticas de atribución |
| Widget de terceros (Elfsight, Trustindex…) | Todo | Cuota mensual y una carga externa más: rompe el «sin dependencias» |
| Reseñas transcritas a mano | El texto, con nombre y fecha reales | Cero, pero hay que actualizarlo a mano |

**Lo implementado es 1 + 4**: el mapa da la prueba visual y la puntuación, dos o
tres reseñas transcritas dan el texto, y el enlace al perfil deja verificarlo
todo. Sin clave, sin coste y sin dependencias.

Cómo se completa:

1. Sacar el **Place ID** del buscador de Place ID de Google Maps Platform y
   pegarlo en `CB.placeId` (`assets/js/main.js`). Con eso se arman solos:
   ```
   Ver todas las reseñas:  https://search.google.com/local/reviews?placeid=PLACE_ID
   Dejar una reseña:       https://search.google.com/local/writereview?placeid=PLACE_ID
   Abrir en Maps:          https://www.google.com/maps/place/?q=place_id:PLACE_ID
   ```
2. Rellenar `contenido/resenas.json` con la puntuación media y el número de
   reseñas **reales y actuales**, y transcribir dos o tres con su nombre y su
   fecha tal como figuran en la ficha.
3. `npm run es:generar`.

Con esos datos aparece el `aggregateRating` en los datos estructurados, que es lo
que puede hacer que salgan las estrellas en el resultado de búsqueda. **Si el dato
no es exacto, no se pone**: Google penaliza el marcado que no coincide con lo
visible, así que el generador sólo lo emite cuando hay puntuación, número y
reseñas cargadas a la vez.

Sobre `CB.mapsKey`: sin clave, el mapa usa el embed clásico
(`maps.google.com/…&output=embed`), que funciona pero no está cubierto por el
contrato de la Maps Embed API. Con clave, se usa el endpoint oficial. Las dos
formas van diferidas (`loading="lazy"`), sólo en `contacto.html` y sólo con
consentimiento: es la tercera carga externa del sitio y no debe competir con el
LCP de la portada.

## Fotos de obras

Las fotos reales viven en dos carpetas: `assets/img/originales/` (material en
bruto) y `assets/img/obras/` (derivados WebP optimizados que se publican). El
flujo:

1. Copiar los originales (JPG/PNG/WebP) a `assets/img/originales/`.
2. Abrir `tools/fotos.py` y añadir una entrada en `MAPEO` por cada foto:
   `slug` descriptivo en kebab-case, `alt` con lo que se ve, **`zona`** (el
   municipio real), `tipo` (`instalacion / sustitucion / mantenimiento /
   suelo-techo / conductos / antes-despues / equipo`) y `destacada` (las 6
   destacadas salen en la portada).
   - Pares antes/después: dos fotos con el mismo valor en `par`, slugs `antes-…`
     y `despues-…`.
   - Fotos inservibles: entrada en `DESCARTES` con el motivo → van a
     `originales/descartadas/`.
3. `python3 web-es/tools/fotos.py` — corrige la orientación EXIF, **elimina los
   metadatos** (privacidad: hay domicilios), exporta WebP q80 en 1600/800 px,
   regenera la tarjeta del hero y los `og-*.jpg` 1200×630, borra los derivados
   huérfanos y escribe `assets/img/obras/index.json`. Es idempotente; `--force`
   rehace todo. Ninguna imagen publicada supera 350 KB.
4. `npm run es:generar` — reconstruye las páginas leyendo `index.json`.
5. `npm run es:shots` — el QA debe quedar en verde antes de publicar.

### La zona es obligatoria

Es la inversión más importante respecto al sitio argentino. Allí las fotos van
sin ciudad porque no hay obras locales que enseñar; **aquí decir dónde se hizo
cada trabajo es media venta** y es lo que alimenta el filtro por zona de la
galería y el SEO local de las páginas de municipio.

Las diez fotos del lote actual están **sin zona**: son obras reales del equipo,
pero nadie ha confirmado el municipio de cada una y este proyecto no inventa
ubicaciones. Mientras siga así:

- la galería no muestra el filtro por zona (una fila con un solo botón no filtra
  nada),
- los pies salen sólo con la descripción técnica,
- `publicar.py` no arma el paquete y lista las que faltan.

Para resolverlo basta con rellenar `zona` en `MAPEO` con uno de estos slugs:
`malaga-capital`, `marbella`, `torremolinos`, `benalmadena`, `fuengirola`,
`mijas`.

> Pista, a confirmar: `instalacion-unidad-exterior-azotea-01` es una azotea sobre
> un casco urbano denso con torre de iglesia y chimenea de ladrillo al fondo, muy
> compatible con Málaga capital. No se ha etiquetado como tal porque «muy
> compatible» no es «confirmado».

La foto de la tarjeta del hero (y de los `og:image`) se elige con `HERO_ORIGEN`
(+ ventanas `HERO_VENTANA_TARJETA` y `HERO_VENTANA_OG`) en `tools/fotos.py`.

### Dos recortes que cambian respecto al sitio argentino

- **Foto de la azotea**: en `web/` está excluida, porque el casco urbano del
  fondo delataba el origen del negocio. Aquí ese fondo es exactamente lo que se
  quiere enseñar, así que se publica.
- **Furgoneta en la nave**: en `web/` se recortaba justo antes de la matrícula
  por su formato español. Aquí entra entera: es un vehículo propio rotulado, en
  la nave propia, y verlo completo suma.
- **Plataforma elevadora**: este recorte **se mantiene**. Deja fuera un teléfono
  rotulado en la plataforma que no es nuestro, sino de la empresa que la alquila.
  Publicar el teléfono de un tercero no procede en ningún país.

## Medición: GTM + eventos dataLayer

**Google Tag Manager es la única puerta de medición**: GA4, Google Ads y el píxel
de Meta se configuran como etiquetas DENTRO del contenedor — nunca pegar snippets
sueltos en el HTML. Hay que crear un contenedor **nuevo**, distinto del argentino.
El ID se pega en un solo sitio: `CB.gtmId` en `assets/js/main.js`. Con el valor de
ejemplo no se carga nada, y sin consentimiento tampoco.

| evento | parámetros | dispara |
|---|---|---|
| `whatsapp_click` | `origen` (hero/seccion/menu/cinta/nota/listado/faq/tarjeta/lightbox/calculadora/chatbot), `pagina`, `zona` | todo CTA que sale a WhatsApp |
| `agenda_click` | `origen`, `pagina`, `zona` | CTA «Concertar visita» |
| `calculadora_uso` | `m2`, `frigorias_resultado`, `equipo_recomendado` | envío de la calculadora |
| `form_envio` | `zona` | formulario de contacto |
| `tel_click` / `email_click` | `pagina` | enlaces de teléfono / email |
| `resenas_click` | `destino` (ver/escribir/maps), `pagina` | enlaces a la ficha de Google |
| `chatbot_inicio` | `pagina` | apertura del asistente |
| `chatbot_paso` | `paso` (1-4), `respuesta`, `pagina` | cada respuesta del asistente (el nombre NO se envía: sin datos personales en el dataLayer) |
| `cookies_consentimiento` | `decision` (aceptado/rechazado) | decisión del banner |

**Chatbot**: cuatro preguntas (nombre, zona, servicio, tipo de aire), arma el
mensaje y sólo entonces deriva a WhatsApp, con `origen=chatbot`. Sin backend ni
librerías: vive en `assets/js/main.js`.

Qué entra por el asistente y qué va directo:

- **Los CTA fijos que acompañan todo el scroll** —el botón flotante y el de
  WhatsApp de la barra inferior en móvil— abren el asistente. Son los que se
  pulsan sin contexto («quiero hablar»), así que conviene preguntar antes.
- **Los CTA de contenido** (hero, cintas, tarjetas, entradas del blog, preguntas
  de zona) van directos a WhatsApp, porque cada uno lleva su propio mensaje con
  el contexto de dónde se pulsó.

Para mandar cualquier otro botón por el asistente basta con añadirle el atributo
`data-chat`; el `href` a `wa.me` se deja igual, así el botón sigue sirviendo si el
JS no cargó. Un botón con `data-chat` **no** dispara `whatsapp_click` al pulsarlo:
mide `chatbot_inicio`, y la conversión se cuenta en «Continuar en WhatsApp».

**Cobertura de conversión**: `npm run es:shots` falla si alguna página deja más de
2,5 pantallas de scroll sin un CTA de WhatsApp en el flujo del documento (el botón
flotante y la barra móvil son fijos y no cuentan). Si al añadir contenido salta
ese error, intercala una `cinta_cta(...)` del generador.

### Conectar GA4 y Google Ads

1. En GTM: etiqueta **GA4 Configuration** con el Measurement ID de una propiedad
   GA4 nueva (crearla como `climabaires.es — ES`). Disparador: All Pages.
2. Por cada evento de la tabla: etiqueta **GA4 Event** + disparador *Custom Event*
   con el nombre exacto. Publicar el contenedor.
3. Configurar el **consentimiento** en el contenedor para que respete las señales
   de Consent Mode que ya manda el sitio.
4. En GA4 → Administración → Eventos: marcar `whatsapp_click` y `agenda_click`
   como conversiones principales y `calculadora_uso` como secundaria.
5. En Google Ads: **Herramientas → Conversiones → Importar → Google Analytics 4**.
6. Vincular GA4 ↔ Ads.

## Agenda de visitas (Google Calendar / Workspace)

1. Calendar → Crear → **Agenda de citas** (duración 45-60 min, horario laboral,
   margen de desplazamiento). Copiar el enlace público de la página de reservas.
2. Pegarlo en `CB.agendaUrl`. Desde ese momento los botones «Concertar visita»
   abren la página de reservas y miden `agenda_click`, y `contacto.html` incrusta
   además el iframe **si hay consentimiento de cookies**; si no, queda el botón.
3. Con `CB.agendaUrl` vacío los botones derivan a WhatsApp.

## Legales: es otro país, no vale con traducir

Las páginas legales están reescritas contra derecho español. Lo que cambia
respecto a `web/`, por si alguien compara:

- **`privacidad.html`** → RGPD (UE 2016/679) + LOPDGDD 3/2018. Lleva responsable
  del tratamiento, tabla de datos/finalidad/**base legal**/plazo de conservación,
  destinatarios y transferencias internacionales, derechos ARCO-POL completos
  (acceso, rectificación, supresión, oposición, limitación, portabilidad y
  decisiones automatizadas) y la **AEPD** como autoridad de control.
- **`terminos.html`** → TRLGDCU (RDL 1/2007). El derecho de **desistimiento es de
  14 días naturales**, no 10. El «botón de arrepentimiento» es una figura
  argentina y **no existe en España**: se ha quitado del pie y el ancla
  `#revocacion` ha pasado a ser `#desistimiento`. Incluye la garantía legal de
  conformidad de tres años, que en Argentina no aplica.
- **`aviso-legal.html`** → **página nueva**, obligatoria por el artículo 10 de la
  LSSI-CE: denominación social, CIF, domicilio, datos registrales, contacto,
  actividad y número de instaladora RITE.
- **`cookies.html`** → **página nueva**, con la tabla de cookies, qué es necesario
  y qué no, y cómo revocar.

Nada de esto es asesoramiento jurídico. Antes de publicar, que lo lea la asesoría:
los textos están redactados para ser correctos y legibles, pero los datos de la
empresa y algunas decisiones (plazos de conservación, encargados del tratamiento)
las tiene que confirmar quien conoce la operación.

## Preguntas frecuentes de las páginas de zona

Las siete páginas de zona son las landings de Google Ads, y cada una tiene sus
propias preguntas en `contenido/faq-zonas.json` — cuatro por zona, sobre lo que
realmente cambia allí: comunidad de propietarios y centro protegido en Málaga
capital, patios interiores y ruido en Benalmádena, ITE y cuadro eléctrico antiguo
en Fuengirola, salitre y alquiler turístico en Torremolinos, tendidos largos y
obra nueva en Mijas, normas de urbanización y segunda residencia en Marbella, y
preinstalación de promotora y comunidad recién constituida en Estepona.

De ese archivo salen dos cosas a la vez: el acordeón visible y el bloque
`FAQPage` de datos estructurados. Editas el JSON, ejecutas `npm run es:generar` y
se actualizan los dos. Si una zona no figura, el build no se rompe pero avisa
(`! slug: sin preguntas propias…`) y publica las genéricas — que en una landing de
Ads es dinero tirado.

## Blog: cómo funciona y cómo se publica solo

El blog no se escribe en HTML. Cada entrada es un `.md` en `contenido/blog/` con
cinco líneas de front-matter (título, resumen, fecha, categoría, minutos) y
`generar.py` arma el índice, la página de cada entrada, el RSS y las entradas del
sitemap. Una entrada con **fecha futura no se publica**: queda escrita esperando
su turno.

`contenido/blog/` está **vacío a propósito**: las entradas argentinas hablaban de
countries, consorcios y frigorías por ambiente, y no se traducen, se reescriben.
El calendario editorial ya tiene once temas del mercado español (ayudas a la
eficiencia, certificado energético, salitre, comunidad de propietarios, ITE,
sustitución de equipos antiguos…).

Publicar una entrada a mano:

```bash
npm run es:blog:tema      # ¿de qué toca escribir? (lee contenido/calendario.json)
# escribir el .md en la ruta que indicó el paso anterior
npm run es:blog:revisar   # control de calidad — no publiques nada que salga con ✗
npm run es:generar && npm run es:shots
```

`revisar-nota.py` bloquea lo que no puede salir: **español rioplatense**,
cualquier mención a Argentina o Buenos Aires, importes, cifras dentro de una ayuda
pública, magnitudes inventadas, superlativos sin respaldo, plazos de garantía sin
confirmar, enlaces rotos, entradas demasiado cortas o sin subtítulos. Las reglas
de fondo están en `contenido/estilo-blog.md`; si cambias las reglas, actualiza
también las expresiones de `revisar-nota.py`.

Lo que **sí** se permite aquí y no en el sitio argentino: hablar de trabajo hecho
en la zona. El límite es que un caso concreto tiene que haber ocurrido de verdad;
si no se puede señalar, se describe el mecanismo sin la anécdota. Eso lo vigila
un aviso, no un error: la decisión es de quien revisa.

### La publicación automática cada tres días

Igual que en el sitio argentino: una Rutina programada ejecuta
`siguiente-nota.py`, escribe la entrada que toque siguiendo `estilo-blog.md`, la
pasa por `revisar-nota.py` y por el QA, y la commitea. Si el calendario se queda
sin temas **avisa y no publica nada**: no se inventa uno.

- **Cambiar los temas** → `contenido/calendario.json` (añadir al final con
  `estado: "pendiente"`).
- **Cambiar el tono o las reglas** → `contenido/estilo-blog.md`.
- **Ver cómo va** → `npm run es:blog:estado`.

> Si se configura una Rutina para este sitio, tiene que ser **distinta** de la del
> sitio argentino y apuntar a `web-es/`. Una sola rutina para los dos escribiría
> en rioplatense en la mitad de las publicaciones.

## Qué se sube al hosting

**No subas `web-es/` tal cual**: pesa unos 20 MB porque incluye los originales de
las fotos (sin optimizar y con metadatos), las capturas de QA y los scripts. Si se
publican, esas fotos quedan accesibles por URL.

```
npm run es:publicar      # deja el sitio listo en dist/sitio-es/
```

El comando **se niega a armar el paquete** si queda algo de la lista de arriba sin
completar. Para una demo se puede forzar con
`python3 web-es/tools/publicar.py --force`.

El script copia sólo lo que el navegador necesita y añade `_headers` (caché larga
para tipografías e imágenes, corta para HTML) y `_redirects` (www → dominio raíz),
que Cloudflare Pages y Netlify leen solos.

## Publicación recomendada (gratis, con SSL)

**Opción A — Cloudflare Pages**: ejecutar `npm run es:publicar` y subir
**`dist/sitio-es`** en Workers & Pages → *Create* → *Pages* → *Upload assets*. Si
prefieres conectar el repo: *build command* `npm run es:publicar`, *output dir*
`dist/sitio-es`. Después, Custom domain → `climabaires.es`.

**Opción B — Netlify**: arrastrar `dist/sitio-es` a app.netlify.com/drop y añadir
el dominio.

En los dos casos: apuntar también `www` (CNAME) y verificar que
`https://climabaires.es/sitemap.xml` responde.

> **Importante**: `climabaires.es` y `climabaires.com` son dos proyectos de
> hosting separados. No redirijas uno al otro ni pongas `hreflang` entre ellos:
> son dos marcas, no dos idiomas del mismo sitio.

## Vista previa navegable

```
npm run es:preview
```

Deja dos archivos autocontenidos en `dist/`: uno con selector de páginas y marco
de móvil, y otro a pantalla completa. Sirven para revisar en el teléfono sin
levantar un servidor, y para publicarlos como artifact.

## Después de publicar

1. **Google Search Console**: dar de alta la propiedad `climabaires.es` y enviar
   `sitemap.xml`.
2. **Google Business Profile**: la ficha ya existe (de ahí sale el Place ID).
   Comprobar que las seis zonas de servicio están dadas de alta y que el enlace
   del sitio web apunta a `climabaires.es`.
3. **Analytics/Ads/Meta**: todo dentro del contenedor GTM.

## Estructura

```
web-es/
├── index.html                  # inicio (hero con foto real + credenciales + últimas obras)
├── servicios.html              # venta / instalación / posventa
├── obras.html                  # galería de obras: filtros + lightbox
├── calculadora-frigorias.html  # herramienta de captación (frigorías + BTU)
├── sobre-nosotros.html         # historia, reseñas y «así trabajamos»
├── contacto.html               # WhatsApp + formulario + agenda + mapa de la ficha
├── aviso-legal.html            # LSSI-CE art. 10
├── privacidad.html             # RGPD + LOPDGDD
├── cookies.html                # política de cookies
├── terminos.html               # TRLGDCU (desistimiento 14 días)
├── 404.html
├── zonas/{malaga-capital,torremolinos,benalmadena,fuengirola,mijas,marbella,estepona}.html
├── blog/                       # generado: índice, una página por entrada y rss.xml
├── contenido/
│   ├── blog/NN-slug.md         # las entradas, en Markdown (esto es lo que se edita)
│   ├── calendario.json         # temario del blog
│   ├── estilo-blog.md          # guía de estilo que recibe quien escribe
│   ├── faq-zonas.json          # preguntas frecuentes de cada zona (acordeón + FAQPage)
│   └── resenas.json            # reseñas de Google transcritas + puntuación real
├── sitemap.xml · robots.txt
├── assets/css/styles.css       # identidad de marca (paleta del manual)
├── assets/js/main.js           # config CB, consentimiento, medición, galería
├── assets/fonts/               # Poppins woff2
├── assets/img/                 # logos, iconos, marcas
│   ├── originales/             # fotos en bruto (no se publican tal cual)
│   └── obras/                  # WebP optimizados + index.json (genera fotos.py)
└── tools/
    ├── fotos.py                # pipeline de fotos
    ├── generar.py              # regenera todas las páginas
    ├── blog.py                 # lee los .md del blog y los pasa a HTML
    ├── preview-html.py         # dos vistas previa navegables en un archivo cada una
    ├── siguiente-nota.py       # de qué toca escribir
    ├── revisar-nota.py         # control de calidad de una entrada
    └── shots.mjs               # QA: capturas + enlaces + consentimiento + dataLayer
```

Las capturas de QA se generan en `web-es/tools/shots/` y no se commitean.
