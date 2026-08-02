# Prompt para desarrollar climabaires.es

> Pegá todo lo que sigue en una sesión nueva de Claude Code, sobre el repo
> `pisulapedro-lgtm/nodo-cb`. Antes de pegarlo, completá los datos marcados con
> `«…»`: son los que no puedo saber yo y sin los cuales el sitio no se publica.

---

Quiero desarrollar **climabaires.es**, el sitio de Clima Baires en Málaga
(España), reutilizando todo el código de climabaires.com que ya está en este
repo.

## De dónde partís

En la rama `claude/climabaires-web-dev-hvk85y`, la carpeta `web/` tiene el sitio
argentino terminado. **Leé `web/README.md` completo antes de tocar nada**: ahí
está cómo funciona todo. Resumen de la arquitectura:

- Sitio **estático puro**, sin build ni dependencias. `web/tools/generar.py` es
  un generador en Python que escribe las 21 páginas, el sitemap, el robots y el
  RSS. Nada de frameworks: si querés cambiar una página, cambiás la función que
  la genera.
- `web/tools/fotos.py` procesa las fotos: recorta, mejora, exporta WebP a 1600 y
  800 px, **elimina los metadatos EXIF** y arma `index.json`. La galería, el
  hero y los `og:image` salen de ahí.
- `web/tools/blog.py` + `siguiente-nota.py` + `revisar-nota.py` son el blog y su
  sistema de publicación automática cada tres días.
- `web/tools/shots.mjs` es el QA con Playwright y **es bloqueante**: captura las
  páginas en escritorio y móvil, y falla si hay enlaces rotos, saltos de
  encabezado, contraste por debajo de AA, más de 2,5 pantallas de scroll sin un
  CTA de WhatsApp, o si el chatbot no completa.
- `web/tools/publicar.py` es la puerta de publicación: **se niega a compilar** si
  quedan datos en `PENDIENTE`.
- `web/tools/preview-html.py` arma dos vistas previa navegables en un solo
  archivo, para revisar en el celular.

Trabajá en una rama nueva, `claude/climabaires-es`, y en una carpeta nueva
`web-es/` — **no toques `web/`**, que es el sitio argentino y sigue vivo.

## Lo importante: no es una traducción, es otro negocio

El sitio argentino está escrito con una restricción fuerte: en Argentina la
empresa **todavía no tiene obras hechas**, así que no puede mostrar trabajos
locales, ni antigüedad, ni reseñas. Por eso `revisar-nota.py` bloquea frases
como «la semana pasada instalamos en Nordelta».

**En Málaga es al revés.** Ahí la empresa opera hace años, tiene obras reales,
clientes reales y reseñas reales. Todas esas restricciones hay que **invertirlas**:

- Las fotos de obra **sí llevan su ubicación real** (Málaga capital, Marbella,
  etc.) en el `alt` y en el pie. En `fotos.py`, el campo `zona` vuelve a ser
  obligatorio y las zonas son las españolas.
- Se pueden y se deben mostrar: años de experiencia, cantidad de instalaciones,
  reseñas, certificaciones.
- En `revisar-nota.py`: sacá la regla que bloquea «origen extranjero» y la que
  bloquea trabajos locales. Dejá las demás (magnitudes inventadas, precios que
  se desactualizan, superlativos sin respaldo). **Esas siguen valiendo**: que el
  negocio tenga historia no autoriza a inventar cifras.
- Al revés, agregá una regla nueva: el sitio español **no menciona Argentina ni
  Buenos Aires**. Son dos marcas separadas.

## Idioma: castellano de España

El sitio argentino está en rioplatense y hay que darlo vuelta entero. En
`revisar-nota.py` hay una lista `ESPANOLISMOS` que marca lo que NO debe
aparecer en el sitio argentino: **esa lista, invertida, es tu guía de traducción**.

| Argentina | España |
|---|---|
| vos tenés / podés / querés | tú tienes / puedes / quieres |
| acá | aquí |
| camioneta | furgoneta |
| depósito | nave |
| plomero | fontanero |
| tarugo | taco |
| plata | dinero |
| celular | móvil |
| computadora | ordenador |
| heladera | nevera |
| living | salón |
| departamento | piso |
| vereda | acera |
| country / barrio cerrado | urbanización |
| cuadra | manzana |
| frigorías | frigorías *(igual)* + menciona BTU |
| service | mantenimiento / servicio técnico |
| «te lo dejamos andando» | «te lo dejamos funcionando» |

Cuidado con los falsos amigos que ya me mordieron a mí: en el sitio argentino
«taco» sólo vale para *taco antivibratorio*; en España el taco de pared también
se llama taco, así que esa excepción sobra. Y revisá el tuteo de forma
sistemática: es el error que más se cuela.

Reescribí también los **mensajes de WhatsApp** de todos los CTA y las cuatro
preguntas del chatbot. Están en `generar.py` y en `assets/js/main.js`.

## Zonas

Reemplazá las seis zonas del AMBA por las de la Costa del Sol. Propuesta a
confirmar: **«…Málaga capital, Marbella, Torremolinos, Benalmádena, Fuengirola,
Mijas…»**. Cada una necesita:

- Su intro, sus barrios y su párrafo `especial` (lo que cambia de verdad ahí:
  urbanizaciones con comunidad de propietarios, salitre en primera línea de
  playa, obra nueva, edificios protegidos en el centro histórico…).
- **Sus cuatro preguntas frecuentes propias**, en
  `contenido/faq-zonas.json`. No las traduzcas: las argentinas hablan de alta de
  contratista y reglamento de country. Las españolas tienen que hablar de
  comunidad de propietarios, licencia de obra menor, ITE, salitre.

## Legales: es otro país, no alcanza con traducir

Las páginas `privacidad.html` y `terminos.html` están escritas contra ley
argentina y **no sirven en España**. Hay que rehacerlas:

- **Privacidad** → RGPD (UE 2016/679) + LOPDGDD 3/2018. Base legal del
  tratamiento, derechos ARCO-POL, plazo de conservación, y la AEPD como
  autoridad de control.
- **Términos** → TRLGDCU. El derecho de desistimiento en España es de **14 días**,
  no 10. El «botón de arrepentimiento» es una figura argentina: **no existe en
  España**, sacalo del pie y del ancla `#revocacion`.
- **Falta una página nueva: Aviso Legal**, obligatoria por la LSSI-CE art. 10
  (denominación social, CIF, domicilio, datos registrales, contacto).
- **Cookies**: si se carga GTM, en la UE hace falta banner de consentimiento
  previo y página de política de cookies. En Argentina no era exigible, acá sí.
  Esto es trabajo adicional real, no un detalle.
- En `generar.py`, el diccionario `EMPRESA` pide CUIT: cambialo por **CIF/NIF**,
  domicilio social y datos del Registro Mercantil.

## Google Maps con las reseñas

Esto es lo que pediste y tiene una limitación técnica que conviene saber de
entrada: **Google no deja incrustar las reseñas completas con un iframe**. Las
opciones reales son:

1. **Mapa incrustado** (`Maps Embed API`). Muestra la ficha con la puntuación y
   el número de reseñas, no el texto. Es una línea de HTML, gratis.
2. **Places API**. Devuelve hasta 5 reseñas en JSON. Necesita clave, facturación
   activa y cumplir las políticas de atribución de Google. Es la única forma
   legítima de mostrarlas actualizadas solas.
3. **Widget de terceros** (Elfsight, Trustindex…). Funciona, pero es una carga
   externa más, tiene coste mensual y rompe el «sin dependencias» del proyecto.
4. **Reseñas transcritas a mano** en el HTML, con nombre y fecha reales, más el
   enlace al perfil para verificarlas.

**Mi recomendación: 1 + 4.** El mapa incrustado da la prueba visual y la
puntuación; dos o tres reseñas reales transcritas dan el texto; el enlace deja
verificar todo. Sin clave de API, sin coste y sin dependencia.

Los enlaces que necesitás, con el Place ID del negocio:

```
Ver todas las reseñas:  https://search.google.com/local/reviews?placeid=«PLACE_ID»
Dejar una reseña:       https://search.google.com/local/writereview?placeid=«PLACE_ID»
Abrir en Maps:          https://www.google.com/maps/place/?q=place_id:«PLACE_ID»
```

El Place ID se saca del buscador de Place ID de Google Maps Platform.

Sumá el `aggregateRating` a los datos estructurados **sólo con la puntuación y
el número de reseñas reales** — es lo que puede hacer que salgan las estrellas
en el resultado de búsqueda. Si el dato no es exacto, no lo pongas: Google
penaliza el marcado que no coincide con lo visible.

Y una advertencia de arquitectura: hoy el sitio sólo permite dos cargas
externas, GTM y el iframe de la agenda. El mapa sería la tercera. Cargalo
diferido (`loading="lazy"`) y sólo en la página de contacto, no en todas.

## Datos que necesito de vos antes de publicar

`publicar.py` se niega a compilar mientras estos sigan en `PENDIENTE`:

- WhatsApp español en formato internacional (`34…`) y cómo se muestra.
- Denominación social, CIF, domicilio social y datos registrales.
- Contenedor de GTM (el argentino no sirve: son propiedades distintas).
- URL de la agenda de Calendar.
- Metros de tubería incluidos en el precio cerrado.
- Plazo de garantía de la instalación.
- **Place ID de Google** y la puntuación y número de reseñas actuales.
- Número de registro como **empresa instaladora RITE** — en España es
  obligatorio para instalar climatización y es el mejor sello de confianza que
  hay. Ponelo visible.

## Cómo trabajar

1. Copiá `web/` a `web-es/` y andá adaptando, no empieces de cero.
2. Después de cada cambio grande: `python3 web-es/tools/generar.py` y
   `node web-es/tools/shots.mjs`. **El QA es bloqueante: si sale rojo, no sigas.**
3. El blog: vaciá `contenido/blog/` y `calendario.json`, y escribí temas nuevos
   para el mercado español (subvenciones a bomba de calor, certificación
   energética, salitre en la costa, aerotermia). Reescribí `estilo-blog.md`
   entero: es lo que lee el sistema automático.
4. Antes de dar nada por terminado, corré `python3 web-es/tools/publicar.py` y
   mostrame qué falta.
5. Al final, generá la vista previa con `python3 web-es/tools/preview-html.py` y
   publicala como artifact para que la vea en el móvil.

No abras un pull request salvo que te lo pida.

## Lo que NO quiero

- Que traduzcas literal y quede un sitio argentino con acento. Es otro público.
- Que inventes reseñas, cifras de instalaciones o años de experiencia. Si no te
  paso el dato, dejalo en `PENDIENTE` y avisame.
- Que menciones Argentina o Buenos Aires en ninguna parte.
- Que rompas el QA para avanzar más rápido.
