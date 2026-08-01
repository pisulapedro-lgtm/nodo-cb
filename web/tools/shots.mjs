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
  'index.html', 'servicios.html', 'calculadora-frigorias.html',
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
    const flat = p.replaceAll('/', '_').replace('.html', '');
    await page.screenshot({ path: join(OUT, `${flat}-${nombre}.png`), fullPage: true });
  }
  // prueba funcional de la calculadora (solo desktop)
  if (nombre === 'desktop') {
    await page.goto('file://' + join(WEB, 'calculadora-frigorias.html'));
    await page.fill('#m2', '25');
    await page.selectOption('#orientacion', 'oeste');
    await page.click('button[type=submit]');
    const cifra = await page.textContent('#calc-resultado .cifra');
    console.log('Calculadora 25 m² oeste →', cifra?.trim());
    if (!cifra || !/frigorías/.test(cifra)) errores.push('calculadora sin resultado');
  }
  await page.close();
}
await browser.close();

if (errores.length) {
  console.error('ERRORES QA:\n - ' + [...new Set(errores)].join('\n - '));
  process.exit(1);
}
console.log(`QA OK: ${paginas.length} páginas × 2 viewports capturadas en web/tools/shots/`);
