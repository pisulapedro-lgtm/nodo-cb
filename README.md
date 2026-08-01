# Clima Baires Argentina — plan de desembarco, web y kit digital

Repositorio de trabajo de los socios (Ignacio · Pedro · Sebastián) para el lanzamiento de Clima Baires en el corredor norte de Buenos Aires.

## Qué hay aquí

| Carpeta | Contenido |
|---|---|
| `dist/` | **Los entregables**: `Plan-Accion-30-Dias-Clima-Baires-Argentina_vX.Y.pdf` y `Modelo-Financiero-Clima-Baires-Argentina_vX.Y.xlsx` |
| `src/` | Fuente del PDF: un Markdown por sección + `datos.json` (números centralizados: tipo de cambio, presupuesto, cronograma, stack) + `fuentes.json` (fuentes con URL y fecha) |
| `build/` | Pipeline del PDF (`build.mjs`, plantilla CSS A4, assets de marca extraídos del Manual de Marca), el motor financiero (`financiero.mjs`) y el generador de la planilla (`modelo-excel.py`) |
| `web/` | Sitio **climabaires.com** completo y listo para desplegar (ver `web/README.md`) |
| `kit-digital/` | Guías de alta + textos + imágenes para WhatsApp Business, Instagram, LinkedIn, Google Workspace y Google Business Profile |

## Cómo regenerar el PDF

```bash
npm install          # una sola vez (dependencia: marked)
npm run build        # → dist/Plan-Accion-30-Dias-Clima-Baires-Argentina_v1.0.pdf
npm run modelo       # → dist/Modelo-Financiero-Clima-Baires-Argentina_v1.0.xlsx
npm run todo         # los dos de una vez
npm run build -- --version 1.1   # para emitir una nueva versión
```

Los importes y el cronograma viven en `src/datos.json`: al cambiar un número (p. ej. el tipo de cambio `cambio.eur_ars`), el build recalcula todas las conversiones, los totales del presupuesto (aborta si superan los € 15.000) y regenera el Gantt. La prosa vive en `src/*.md`.

Requisitos del entorno: Node 22 + Playwright con Chromium (el build los detecta; en este entorno ya están instalados). Para regenerar los assets de marca desde el manual hace falta además `poppler-utils` y Python 3 con Pillow. La planilla necesita `openpyxl`, y verificarla necesita `libreoffice-calc`.

## El modelo financiero

`build/financiero.mjs` es un módulo de funciones puras que lee los supuestos de `src/datos.json` (clave `financiero`) y produce unit economics, P&L a 24 meses, flujo de caja, punto de equilibrio y escenarios. **Lo consumen los dos entregables**: `build.mjs` para las tablas de la sección 6 del PDF, y `modelo-excel.py` para la planilla. Por construcción no pueden divergir, y la hoja «Verificación» del Excel lo comprueba celda a celda contra las cifras del motor.

La planilla lleva fórmulas de Excel reales, no valores volcados: la hoja «Supuestos» es la única editable (celdas en amarillo) y todo el libro recalcula al cambiarla.

Para comprobar que las fórmulas del Excel dan lo mismo que el motor del PDF:

```bash
soffice --headless --convert-to xlsx --outdir /tmp/recalc dist/Modelo-Financiero-*.xlsx
# abrir el resultado y leer la hoja «Verificación»: las 12 filas deben decir OK
```

## Cómo regenerar la web

```bash
python3 web/tools/generar.py   # regenera los .html desde el layout
npm run web:shots              # QA: capturas desktop/móvil + chequeo de enlaces
```

## Estado

- **v1.0** — plan (14 secciones, 29 páginas, 45 fuentes fechadas) + modelo financiero a 24 meses + web climabaires.com + kit digital. Agosto 2026.
- **v0.9** — borrador previo, sin modelo financiero. Se conserva en `dist/` como histórico.

Pendiente de los socios: revisión del v1.0, número real de WhatsApp Business (hoy hay un placeholder en `web/assets/js/main.js`) y validación profesional de los puntos marcados `[VALIDAR CON …]`.
