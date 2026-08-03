#!/usr/bin/env node
/**
 * Hoja suelta de la semana — Clima Baires Argentina.
 *
 *   npm run semana   →   dist/Semana-1-Ignacio_03-10-agosto.pdf
 *
 * Lee **el mismo archivo** que el build del plan inyecta como subsección 4.1
 * (`src/anexos/semana-ignacio.md`), así que la hoja impresa y el documento no
 * pueden decir cosas distintas. Reutiliza `build/template.html` para que la
 * tipografía, la paleta y las casillas sean las mismas.
 *
 * Es lo único del repositorio que caduca: el lunes siguiente se reescribe el
 * markdown con la semana nueva y se vuelve a correr.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const { marked } = require_('marked');
let chromium;
try {
  ({ chromium } = require_('playwright'));
} catch {
  ({ chromium } = require_('/opt/node22/lib/node_modules/playwright'));
}

const datos = JSON.parse(readFileSync(join(ROOT, 'src', 'datos.json'), 'utf8'));
const TITULO = 'Semana 1 — Ignacio · 3 al 10 de agosto de 2026';
const SALIDA = join(ROOT, 'dist', 'Semana-1-Ignacio_03-10-agosto.pdf');

const md = readFileSync(join(ROOT, 'src', 'anexos', 'semana-ignacio.md'), 'utf8');
const cuerpo = `<section class="capitulo hoja">
<h1>Semana 1 — del lunes 3 al lunes 10 de agosto</h1>
${marked.parse(md, { gfm: true })}
</section>`;

const template = readFileSync(join(ROOT, 'build', 'template.html'), 'utf8');
const htmlPath = join(ROOT, 'dist', 'semana.html');
writeFileSync(htmlPath, template.replace('{{TITULO}}', TITULO).replace('{{CONTENIDO}}', cuerpo));

const logoB64 = readFileSync(join(ROOT, 'build', 'assets', 'logo-header.png')).toString('base64');
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.goto('file://' + htmlPath, { waitUntil: 'load' });
await page.pdf({
  path: SALIDA,
  format: 'A4',
  printBackground: true,
  displayHeaderFooter: true,
  margin: { top: '22mm', bottom: '14mm', left: '15mm', right: '15mm' },
  headerTemplate: `
    <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:4mm 15mm 0; display:flex; align-items:center; justify-content:space-between;">
      <img src="data:image/png;base64,${logoB64}" style="height:8mm"/>
      <span style="text-align:right;">Semana 1 · 3 al 10 de agosto de 2026</span>
    </div>`,
  footerTemplate: `
    <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:0 15mm 4mm; display:flex; justify-content:space-between;">
      <span>Clima Baires · sección 4.1 del Plan de Negocio v${datos.meta.version}</span>
      <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
    </div>`,
});
await browser.close();

console.log(`OK  ${SALIDA}`);
