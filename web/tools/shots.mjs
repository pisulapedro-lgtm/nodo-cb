// Capturas QA de climabaires.com (desktop 1440 y móvil 390) + chequeo de enlaces internos.
// Uso: npm run web:shots   → escribe PNGs en web/tools/shots/
import { createRequire } from 'node:module';
import { readdirSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require_('playwright')); }
catch { ({ chromium } = require_('/opt/node22/lib/node_modules/playwright')); }

const WEB = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(WEB, 'tools', 'shots');
mkdirSync(OUT, { recursive: true });

const paginas = [
  'index.html', 'servicios.html', 'obras.html', 'calculadora-frigorias.html',
  'sobre-nosotros.html', 'contacto.html', '404.html',
  ...readdirSync(join(WEB, 'zonas')).map((f) => 'zonas/' + f),
];

const browser = await chromium.launch({ args: ['--no-sandbox'] });
const errores = [];

for (const [nombre, viewport] of [['desktop', { width: 1440, height: 900 }], ['movil', { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport });
  page.on('pageerror', (e) => errores.push(`JS ${nombre}: ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') errores.push(`console ${nombre}: ${m.text()}`); });
  for (const p of paginas) {
    await page.goto('file://' + join(WEB, p), { waitUntil: 'load' });
    // chequeo de enlaces internos rotos (solo file://)
    const rotos = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('a[href]').forEach((a) => {
        const h = a.getAttribute('href');
        if (h.startsWith('http') || h.startsWith('#') || h.startsWith('mailto')) return;
        out.push(h);
      });
      return out;
    });
    for (const h of rotos) {
      const destino = join(WEB, dirname(p), h.split('#')[0]);
      try { readdirSync(dirname(destino)); const { existsSync } = await import('node:fs');
        if (!existsSync(destino)) errores.push(`enlace roto en ${p}: ${h}`);
      } catch { errores.push(`enlace roto en ${p}: ${h}`); }
    }
    // forzar la carga de imágenes lazy antes de la captura fullPage
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; });
      scrollTo(0, document.body.scrollHeight);
      scrollTo(0, 0);
      await Promise.race([
        Promise.all(Array.from(document.images).map((i) => i.decode().catch(() => {}))),
        new Promise((r) => setTimeout(r, 4000)),          // tope: nunca colgarse
      ]);
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    });
    const flat = p.replaceAll('/', '_').replace('.html', '');
    await page.screenshot({ path: join(OUT, `${flat}-${nombre}.png`), fullPage: true });
  }
  // pruebas funcionales (solo desktop)
  if (nombre === 'desktop') {
    // calculadora + evento calculadora_uso en el dataLayer
    await page.goto('file://' + join(WEB, 'calculadora-frigorias.html'));
    await page.fill('#m2', '25');
    await page.selectOption('#orientacion', 'oeste');
    await page.click('button[type=submit]');
    const cifra = await page.textContent('#calc-resultado .cifra');
    console.log('Calculadora 25 m² oeste →', cifra?.trim());
    if (!cifra || !/frigorías/.test(cifra)) errores.push('calculadora sin resultado');
    const evCalc = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'calculadora_uso'));
    if (!evCalc || evCalc.m2 !== 25 || !evCalc.frigorias_resultado || !evCalc.equipo_recomendado) {
      errores.push('dataLayer sin calculadora_uso válido: ' + JSON.stringify(evCalc));
    } else console.log('dataLayer calculadora_uso →', JSON.stringify(evCalc));

    // whatsapp_click: clic en el CTA del hero sin navegar
    await page.goto('file://' + join(WEB, 'index.html'), { waitUntil: 'load' });
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), true));
    await page.click('.hero a[data-wsp]');
    const evWsp = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'whatsapp_click'));
    if (!evWsp || evWsp.origen !== 'hero' || evWsp.pagina !== 'index') {
      errores.push('dataLayer sin whatsapp_click de hero: ' + JSON.stringify(evWsp));
    } else console.log('dataLayer whatsapp_click →', JSON.stringify(evWsp));

    // agenda_click desde la página de servicios
    await page.goto('file://' + join(WEB, 'servicios.html'), { waitUntil: 'load' });
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), true));
    await page.click('a[data-agenda]');
    const evAg = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'agenda_click'));
    if (!evAg || evAg.pagina !== 'servicios') errores.push('dataLayer sin agenda_click: ' + JSON.stringify(evAg));
    else console.log('dataLayer agenda_click →', JSON.stringify(evAg));

    // galería: filtros + lightbox accesible (abre, navega, cierra con Escape)
    await page.goto('file://' + join(WEB, 'obras.html'), { waitUntil: 'load' });
    const total = await page.locator('.obra').count();
    await page.click('.filtro[data-grupo="tipo"][data-valor="instalacion"]');
    const filtradas = await page.locator('.obra:not(.oculta)').count();
    if (!total || filtradas >= total) errores.push(`filtros de obras sin efecto (${filtradas}/${total})`);
    await page.click('.filtro[data-grupo="tipo"][data-valor="todos"]');
    await page.click('.obra-abrir');
    if (!(await page.isVisible('#lightbox'))) errores.push('lightbox no abre');
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Escape');
    if (await page.isVisible('#lightbox')) errores.push('lightbox no cierra con Escape');
    console.log(`Galería: ${total} obras, filtro instalación → ${filtradas} visibles, lightbox OK`);
  }
  // barra inferior fija visible en móvil
  if (nombre === 'movil') {
    await page.goto('file://' + join(WEB, 'index.html'), { waitUntil: 'load' });
    const barraOk = await page.evaluate(() => {
      const b = document.querySelector('.barra-movil');
      if (!b) return false;
      const r = b.getBoundingClientRect();
      return getComputedStyle(b).display !== 'none' && r.bottom <= innerHeight + 1 && r.height > 40;
    });
    if (!barraOk) errores.push('barra móvil ausente o fuera de pantalla');
  }
  await page.close();
}
await browser.close();

if (errores.length) {
  console.error('ERRORES QA:\n - ' + [...new Set(errores)].join('\n - '));
  process.exit(1);
}
console.log(`QA OK: ${paginas.length} páginas × 2 viewports capturadas en web/tools/shots/`);
