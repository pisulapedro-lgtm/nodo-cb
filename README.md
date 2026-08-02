# Clima Baires Argentina — plan de negocio, web y kit digital

Repositorio de trabajo de los socios (Ignacio · Pedro · Sebastián) para el lanzamiento de Clima Baires en el corredor norte de Buenos Aires.

## Qué hay aquí

| Carpeta | Contenido |
|---|---|
| `dist/` | **Los entregables**: `Plan-de-Negocio-Clima-Baires-Argentina_vX.Y.pdf` (el documento completo) y `Modelo-Financiero-Clima-Baires-Argentina_vX.Y.xlsx` |
| `src/` | Fuente del PDF: un Markdown por sección + `datos.json` (números centralizados: tipo de cambio, presupuesto, cronograma, stack, supuestos financieros, partes) + `fuentes.json` |
| `build/` | Pipeline del PDF (`build.mjs`, plantilla CSS A4, assets de marca), los motores de cálculo (`financiero.mjs`, `marketing.mjs` y `comercial.mjs`), el generador de la planilla (`modelo-excel.py`) y el de miniaturas (`preparar-miniaturas.py`) |
| `web/` | Sitio **climabaires.com** completo: 21 páginas, galería de obras, blog y medición (manual técnico en `web/README.md`) |
| `kit-digital/` | Piezas gráficas de marca. Las guías de alta son las secciones 15 y 16 del PDF |

## Un solo documento

El PDF reúne todo el proyecto en siete partes:

| Parte | Secciones | Contenido |
|---|---|---|
| I | 1-5 | El plan de 30 días: resumen, decisiones, Semana 0, cronograma y presupuesto |
| II | 6 | El modelo financiero a 24 meses |
| III | 7-12 | Operación: fiscal, stack, go-to-market, personas, riesgos y checklist del Día 1 |
| IV | 13-16 | Los activos digitales: la web, su despliegue y el kit digital |
| V | 17-19 | Marketing y publicidad: embudo, Google Ads y Meta listos para cargar, y el tablero |
| VI | 20-23 | La operación comercial: tarifario, los documentos que se firman, manual de calidad y proveedores |
| VII | 24 | El horizonte: año 3, cuánto vale la empresa y cómo sale un socio |
| — | 25 | Anexos: glosario, checklist de España y las fuentes fechadas |

## Cómo regenerar los entregables

```bash
npm install          # una sola vez (dependencia: marked)
npm run todo         # miniaturas + PDF + planilla
```

O por separado:

```bash
npm run miniaturas   # build/assets/web/ desde las capturas del sitio
npm run build        # → dist/Plan-de-Negocio-Clima-Baires-Argentina_v1.3.pdf
npm run modelo       # → dist/Modelo-Financiero-Clima-Baires-Argentina_v1.3.xlsx
npm run build -- --version 1.4   # para emitir una versión distinta de la de datos.json
```

Los importes y el cronograma viven en `src/datos.json`: al cambiar un número (por ejemplo el tipo de cambio `cambio.eur_ars`), el build recalcula todas las conversiones, los totales del presupuesto (aborta si superan los € 15.000) y regenera el Gantt. La prosa vive en `src/*.md`; añadir un archivo `NN-titulo.md` lo incorpora al documento y al índice sin tocar nada más.

**El índice se pagina en dos pasadas**: la primera renderiza el PDF con los números en blanco, la segunda lo lee ya paginado con `pdftotext`, localiza el anclaje invisible de cada encabezado y rellena los números. Por eso el índice no puede mentir. Si `pdftotext` falta, el build avisa y emite el PDF sin números en lugar de fallar.

Requisitos del entorno: Node 22 + Playwright con Chromium (el build los detecta). Además: `poppler-utils` (paginación del índice y extracción de la marca), Python 3 con Pillow (miniaturas), `openpyxl` (planilla) y `libreoffice-calc` (para verificarla).

## El motor comercial

`build/comercial.mjs` deriva el **tarifario publicable** del mismo `financiero.mix` que alimenta el modelo: el precio de lista de una categoría *es* su ticket, así que no pueden contradecirse — no por una validación, sino por construcción. Lo que el build sí vigila es lo que una persona puede romper a mano: que ningún descuento deje el precio por debajo del costo directo y que pagar en cuotas nunca salga más barato que pagar de una vez.

El mismo módulo dimensiona el mercado del corredor de abajo hacia arriba (población → hogares → parque instalado → recambio anual → pesos), y `FIN.horizonte()` proyecta el año 3 y el rango de valoración.

## El plan de marketing

`build/marketing.mjs` hace con la pauta lo mismo que `financiero.mjs` con el dinero: convierte el presupuesto publicitario en clics, leads y obras, y calcula qué parte del plan **no** puede pagar la pauta. El reparto por canal de `datos.json` tiene que sumar exactamente la serie de marketing del modelo financiero — **el build aborta si no cuadra**, igual que aborta si el presupuesto supera los € 15.000. No hay pauta fuera del modelo.

## El modelo financiero

`build/financiero.mjs` es un módulo de funciones puras que lee los supuestos de `src/datos.json` (clave `financiero`) y produce unit economics, P&L a 24 meses, flujo de caja, punto de equilibrio y escenarios. **Lo consumen los dos entregables**: `build.mjs` para las tablas de la sección 6 del PDF, y `modelo-excel.py` para la planilla. Por construcción no pueden divergir, y la hoja «Verificación» del Excel lo comprueba celda a celda contra las cifras del motor.

La planilla lleva fórmulas de Excel reales, no valores volcados: la hoja «Supuestos» es la única editable (celdas en amarillo) y todo el libro recalcula al cambiarla.

Para comprobar que las fórmulas del Excel dan lo mismo que el motor del PDF:

```bash
soffice --headless --convert-to xlsx --outdir /tmp/recalc dist/Modelo-Financiero-*.xlsx
# abrir el resultado y leer la hoja «Verificación»: las 12 filas deben decir OK
```

## La web

```bash
npm run web:generar    # regenera las 21 páginas (incluidas galería y blog)
npm run web:shots      # QA: capturas, enlaces, eventos de medición y cobertura de CTA
npm run web:publicar   # arma dist/sitio/ para subir al hosting
npm run miniaturas     # lleva las capturas al PDF
```

Detalle completo —fotos de obra, medición con GTM, agenda de Calendar y el blog que se publica solo— en `web/README.md`.

## Estado

- **v1.3** — suma el dimensionamiento de mercado y las Partes VI y VII: tarifario, plantillas de presupuesto-contrato, garantía, checklist y locación de obra, manual de operaciones, plan de proveedores, año 3 y valoración. 25 secciones, 62 páginas, 52 fuentes. Agosto 2026.
- **v1.2** — Parte V: plan de marketing y publicidad. Histórico en `dist/`.
- **v1.1** — documento único: plan de 30 días + modelo financiero + web y activos digitales, con índice paginado. Histórico en `dist/`.
- **v1.0** — plan de acción con modelo financiero, sin la parte digital. Histórico en `dist/`.
- **v0.9** — borrador previo, sin modelo financiero. Histórico en `dist/`.

Pendiente de los socios: revisión del v1.3, el **número real de WhatsApp Business** (hoy hay un placeholder en `web/assets/js/main.js` y sin él la web no se publica) y la validación profesional de los puntos marcados `[VALIDAR CON …]`.
