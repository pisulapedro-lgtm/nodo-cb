# Clima Baires Argentina — plan de desembarco, web y kit digital

Repositorio de trabajo de los socios (Ignacio · Pedro · Sebastián) para el lanzamiento de Clima Baires en el corredor norte de Buenos Aires.

## Qué hay aquí

| Carpeta | Contenido |
|---|---|
| `dist/` | **El entregable**: `Plan-Accion-30-Dias-Clima-Baires-Argentina_vX.Y.pdf` |
| `src/` | Fuente del PDF: un Markdown por sección + `datos.json` (números centralizados: tipo de cambio, presupuesto, cronograma, stack) + `fuentes.json` (fuentes con URL y fecha) |
| `build/` | Pipeline del PDF (`build.mjs`, plantilla CSS A4, assets de marca extraídos del Manual de Marca) |
| `web/` | Sitio **climabaires.com** completo y listo para desplegar (ver `web/README.md`) |
| `kit-digital/` | Guías de alta + textos + imágenes para WhatsApp Business, Instagram, LinkedIn, Google Workspace y Google Business Profile |

## Cómo regenerar el PDF

```bash
npm install          # una sola vez (dependencia: marked)
npm run build        # → dist/Plan-Accion-30-Dias-Clima-Baires-Argentina_v0.9.pdf
npm run build -- --version 1.0   # para emitir una nueva versión
```

Los importes y el cronograma viven en `src/datos.json`: al cambiar un número (p. ej. el tipo de cambio `cambio.eur_ars`), el build recalcula todas las conversiones, los totales del presupuesto (aborta si superan los € 15.000) y regenera el Gantt. La prosa vive en `src/*.md`.

Requisitos del entorno: Node 22 + Playwright con Chromium (el build los detecta; en este entorno ya están instalados). Para regenerar los assets de marca desde el manual hace falta además `poppler-utils` y Python 3 con Pillow.

## Cómo regenerar la web

```bash
python3 web/tools/generar.py   # regenera los .html desde el layout
npm run web:shots              # QA: capturas desktop/móvil + chequeo de enlaces
```

## Estado

- **v0.9** — borrador completo para revisión de los socios (agosto 2026). Pendiente: feedback → v1.0.
