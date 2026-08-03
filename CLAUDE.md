# Clima Baires Argentina — contexto del repo

Si abrís una sesión acá, esto es lo que necesitás saber antes de tocar nada.

## Qué es

Sitio de **climabaires.com**: venta, instalación y posventa de aire
acondicionado en el corredor norte del AMBA (Núñez, Vicente López, San Isidro,
Tigre, Nordelta, Pilar). WhatsApp es el canal de conversión número uno y
Nordelta el objetivo comercial principal. Se planea tráfico de Google Ads, así
que las páginas de zona son landings, no relleno.

El desarrollo vive en la rama **`claude/climabaires-web-dev-hvk85y`**. `main`
sólo tiene el commit inicial: si estás en `main` no vas a ver nada.

## Dónde está cada cosa

```
web/                     el sitio (esto es lo que se trabaja)
  *.html, zonas/, blog/  GENERADO — no editar a mano, se pisa
  contenido/             el contenido editable de verdad
    blog/NN-slug.md        las entradas del blog, en Markdown
    calendario.json        temario del blog
    estilo-blog.md         guía que recibe el sistema automático
    faq-zonas.json         preguntas frecuentes de cada zona
  assets/                css, js, fuentes, imágenes
    img/originales/        fotos en bruto — NUNCA se publican
  tools/                 los scripts que arman todo
dist/                    salidas generadas (ignoradas por git)
kit-digital/, build/     otro proyecto, no tocar
```

**El HTML es generado.** Si editás `web/index.html` a mano, el próximo
`generar.py` lo pisa. Los cambios van en `web/tools/generar.py` o en
`web/contenido/`.

## Comandos

```bash
npm run web:generar    # regenera las 21 páginas + sitemap + robots + RSS
npm run web:shots      # QA con Playwright — BLOQUEANTE
npm run web:preview    # dos vistas previa navegables en un archivo cada una
npm run web:publicar   # arma dist/sitio/, lo único que se sube al hosting
npm run blog:tema      # de qué toca escribir en el blog
npm run blog:revisar   # control de calidad de las entradas
npm run blog:estado    # qué se publicó y qué falta
```

El ciclo normal después de cualquier cambio es
`web:generar` → `web:shots`. Si el QA sale rojo, se arregla; no se avanza.

## Las tres reglas que no se negocian

**1. No inventar.** La empresa **todavía no tiene obras hechas en Argentina**.
No existe «la semana pasada instalamos en Nordelta», ni clientes locales, ni
años de experiencia acá, ni reseñas. Tampoco precios en pesos (se desactualizan
y quedan como mentira), plazos de garantía sin confirmar, certificaciones ni
magnitudes de mercado («cientos de countries»). `web/tools/revisar-nota.py`
bloquea todo eso automáticamente en el blog.

Las fotos de `obras.html` son trabajos propios del equipo pero **no del AMBA**:
por eso llevan pie técnico y **sin ciudad**. Ninguna dice ni puede decir que se
hizo en Nordelta o San Isidro. Cuando existan obras de acá, se cargan con su
zona real en `fotos.py` y el filtro de zonas de la galería reaparece solo.

**2. El sitio se presenta 100% de Buenos Aires.** Decisión comercial: no se
menciona Málaga, España, «casa matriz» ni el dominio .es en ninguna parte —ni en
el copy, ni en los alt, ni en los nombres de archivo, ni en los datos
estructurados. El validador del blog también lo bloquea.

**3. El QA y la puerta de publicación son bloqueantes.**
`shots.mjs` falla si hay enlaces rotos, saltos de encabezado, contraste bajo AA,
más de 2,5 pantallas de scroll sin un CTA de WhatsApp, o si el chatbot no
completa. `publicar.py` se niega a compilar si quedan datos en `PENDIENTE`.
No los desactives para avanzar: están para eso.

## Cosas que sorprenden si no las sabés

- **Los enlaces de WhatsApp están escritos en el HTML**, no sólo armados por JS,
  para que funcionen sin JavaScript. Por eso hay que regenerar después de tocar
  el bloque `CB` de `main.js`.
- **`fotos.py` cachea**: compara contra la fecha de la foto original *y* la del
  propio script. Si editás un recorte, corré el script de nuevo y sí se rehace.
- **Los CTA fijos** (píldora flotante y barra inferior en móvil) abren el
  asistente de 4 preguntas; los CTA de contenido van directo a WhatsApp con su
  propio mensaje. Un botón con `data-chat` **no** dispara `whatsapp_click`: mide
  `chatbot_inicio`, y la conversión se cuenta recién al salir a WhatsApp.
- **El blog se publica solo** cada tres días mediante una Rutina programada, que
  escribe la entrada, la valida y la commitea. La Rutina está atada a la cuenta
  que la creó: si trabajás desde otra cuenta, no existe para vos.

## Lo que falta para publicar

`npm run web:publicar` los lista, pero en resumen son datos que sólo puede dar
el dueño: número de WhatsApp real, contenedor de GTM, agenda de Calendar, razón
social + CUIT + domicilio, y el plazo de garantía. Además hay una lista de
**promesas operativas a confirmar** en `web/README.md` (franja de dos horas,
documento del técnico el día anterior, retiro del equipo viejo): son compromisos
de cómo se trabaja, no datos verificables, y el dueño tiene que validarlos.

## Documentación más larga

- `web/README.md` — despliegue, medición, fotos, blog, legales. Es la referencia.
- `dist/PROMPT-subir-a-hostinger.md` — cómo publicarlo en Hostinger.
- `dist/PROMPT-climabaires-es.md` — cómo replicar el sitio para el mercado español.
