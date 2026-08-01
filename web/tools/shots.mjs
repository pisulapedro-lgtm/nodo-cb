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
    // contraste WCAG AA de los textos sobre fondos de color plano
    const bajos = await page.evaluate(() => {
      const canal = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
      const lum = (c) => 0.2126 * canal(c[0]) + 0.7152 * canal(c[1]) + 0.0722 * canal(c[2]);
      const parse = (s) => (s.match(/\d+(\.\d+)?/g) || []).slice(0, 3).map(Number);
      const fondo = (el) => {
        let n = el;
        while (n && n !== document.documentElement) {
          const cs = getComputedStyle(n);
          if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;  // degradado/foto: no medible así
          const bg = cs.backgroundColor;
          if (bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(bg)) return parse(bg);
          n = n.parentElement;
        }
        return [255, 255, 255];
      };
      const out = [];
      document.querySelectorAll('h1,h2,h3,h4,p,li,a,span,button,figcaption,label').forEach((el) => {
        if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') return;
        const t = el.textContent.trim();
        if (!t || el.children.length) return;
        const cs = getComputedStyle(el);
        const fg = parse(cs.color), bg = fondo(el);
        if (fg.length < 3 || !bg) return;
        const l1 = lum(fg), l2 = lum(bg);
        const r = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        const px = parseFloat(cs.fontSize);
        const grande = px >= 24 || (px >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
        if (r < (grande ? 3 : 4.5)) out.push(`${Math.round(r * 100) / 100}:1 "${t.slice(0, 30)}"`);
      });
      return [...new Set(out)];
    });
    if (bajos.length) errores.push(`${p} (${nombre}): contraste bajo AA → ${bajos.slice(0, 3).join(' · ')}`);

    // cobertura de conversión: ninguna franja larga de scroll sin CTA de WhatsApp
    // en el flujo del documento (el flotante y la barra móvil son fijos y no cuentan)
    const cob = await page.evaluate(() => {
      const enFlujo = (el) => {
        let n = el;
        while (n && n !== document.body) {
          if (getComputedStyle(n).position === 'fixed') return false;
          n = n.parentElement;
        }
        return el.offsetParent !== null;
      };
      const ys = Array.from(document.querySelectorAll('[data-wsp], [data-agenda]'))
        .filter(enFlujo).map((el) => el.getBoundingClientRect().top + scrollY).sort((a, b) => a - b);
      const alto = document.body.scrollHeight;
      let hueco = 0, prev = 0;
      for (const y of ys) { hueco = Math.max(hueco, y - prev); prev = y; }
      return { hueco: Math.max(hueco, alto - prev), ctas: ys.length };
    });
    const tope = viewport.height * 2.5;
    if (cob.hueco > tope) {
      errores.push(`${p} (${nombre}): ${Math.round(cob.hueco / viewport.height * 10) / 10} pantallas sin CTA de WhatsApp`);
    }

    // las páginas son landings de Google Ads: el primer CTA entra en el fold
    if (nombre === 'movil' && p !== '404.html') {
      const primero = await page.evaluate(() => {
        const enFlujo = (el) => {
          let n = el;
          while (n && n !== document.body) { if (getComputedStyle(n).position === 'fixed') return false; n = n.parentElement; }
          return el.offsetParent !== null;
        };
        const ys = Array.from(document.querySelectorAll('[data-wsp], [data-agenda]')).filter(enFlujo)
          .map((el) => el.getBoundingClientRect().top).sort((a, b) => a - b);
        return ys[0] ?? Infinity;
      });
      if (primero >= viewport.height) errores.push(`${p} (movil): primer CTA a ${Math.round(primero)}px, fuera del fold`);
    }

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

    // chatbot: 4 preguntas → enlace de WhatsApp armado + eventos
    await page.goto('file://' + join(WEB, 'index.html'), { waitUntil: 'load' });
    await page.click('.wsp-flotante');
    await page.fill('#chat-pie input', 'Test QA');
    await page.click('#chat-pie button[type=submit]');
    await page.click('.chat-chip[data-valor="Nordelta"]');
    await page.click('.chat-chip[data-valor="Instalación nueva"]');
    await page.click('.chat-chip[data-valor="Split"]');
    const hrefChat = await page.getAttribute('.chat-final', 'href');
    const evChat = await page.evaluate(() => ({
      inicio: (window.dataLayer || []).some((e) => e.event === 'chatbot_inicio'),
      pasos: (window.dataLayer || []).filter((e) => e.event === 'chatbot_paso').length,
    }));
    if (!hrefChat || !hrefChat.includes('Test%20QA') || !hrefChat.includes('Nordelta')) {
      errores.push('chatbot: enlace final sin datos (' + hrefChat + ')');
    }
    if (!evChat.inicio || evChat.pasos !== 4) errores.push('chatbot: eventos dataLayer incompletos ' + JSON.stringify(evChat));
    await page.keyboard.press('Escape');
    if (await page.isVisible('#chat')) errores.push('chatbot no cierra con Escape');
    console.log('Chatbot OK →', decodeURIComponent(hrefChat.split('text=')[1] || ''));

    // accesibilidad por teclado: anillo de foco visible en filtros y fotos
    await page.goto('file://' + join(WEB, 'obras.html'), { waitUntil: 'load' });
    for (const clase of ['filtro', 'obra-abrir']) {
      let visto = null;
      for (let i = 0; i < 45; i++) {
        await page.keyboard.press('Tab');
        visto = await page.evaluate((c) => {
          const el = document.activeElement;
          if (!el?.classList?.contains(c)) return null;
          const cs = getComputedStyle(el);
          return { w: parseFloat(cs.outlineWidth), s: cs.outlineStyle };
        }, clase);
        if (visto) break;
      }
      if (!visto) errores.push(`.${clase} no es alcanzable con Tab`);
      else if (!(visto.w >= 2 && visto.s !== 'none')) errores.push(`.${clase} sin anillo de foco visible (${visto.w}px ${visto.s})`);
    }

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
