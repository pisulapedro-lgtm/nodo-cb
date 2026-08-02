// Capturas QA de climabaires.es (escritorio 1440 y móvil 390) + comprobación de enlaces internos.
// Uso: npm run es:shots   → escribe PNGs en web-es/tools/shots/
//
// Frente al QA del sitio argentino hay una pieza nueva y bloqueante: el banner de
// consentimiento de cookies. En la UE nada que no sea estrictamente necesario
// puede cargarse antes del «sí», así que se comprueba que aparece, que rechazar
// funciona y que mientras está abierto no hay dos capas peleando por la esquina
// inferior. Como tapa la pantalla, en el resto de páginas se despacha justo
// después de las comprobaciones y antes de la captura.
import { createRequire } from 'node:module';
import { readdirSync, mkdirSync, existsSync, statSync } from 'node:fs';
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
  'sobre-nosotros.html', 'contacto.html',
  'aviso-legal.html', 'privacidad.html', 'cookies.html', 'terminos.html', '404.html',
  ...readdirSync(join(WEB, 'zonas')).map((f) => 'zonas/' + f),
  // el blog crece solo: el índice siempre, y la entrada más nueva como muestra
  ...(existsSync(join(WEB, 'blog')) ? ['blog/index.html', ...ultimaNota()] : []),
];

/** Abre una página y despacha el banner de cookies (rechazando: es el peor caso
 *  para el sitio, así que es el que conviene fotografiar y medir). */
async function ir(page, ruta, opciones = { waitUntil: 'load' }) {
  await page.goto('file://' + join(WEB, ruta), opciones);
  await page.evaluate(() => document.querySelector('#cookies .ck-rechazar')?.click());
}

/** La entrada publicada más reciente, para que la rutina automática pase por QA. */
function ultimaNota() {
  const notas = readdirSync(join(WEB, 'blog'))
    .filter((f) => f.endsWith('.html') && f !== 'index.html')
    .map((f) => ({ f, t: statSync(join(WEB, 'blog', f)).mtimeMs }))
    .sort((a, b) => b.t - a.t);
  return notas.length ? ['blog/' + notas[0].f] : [];
}

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
    // el banner tiene que estar en TODAS las páginas: es la única puerta que
    // impide que GTM, el mapa y la agenda carguen sin permiso. Se deja abierto
    // hasta después del control de contraste, para que sus textos también se midan.
    if (!(await page.locator('#cookies .ck-aceptar').count()) ||
        !(await page.locator('#cookies .ck-rechazar').count())) {
      errores.push(`${p} (${nombre}): sin banner de consentimiento de cookies`);
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
    // estructura y accesibilidad básica del documento
    const estructura = await page.evaluate(() => {
      const out = [];
      const h1 = document.querySelectorAll('h1').length;
      if (h1 !== 1) out.push(`${h1} etiquetas h1`);
      const niveles = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map((h) => +h.tagName[1]);
      for (let i = 1; i < niveles.length; i++) {
        if (niveles[i] - niveles[i - 1] > 1) { out.push(`salto de encabezado h${niveles[i - 1]}→h${niveles[i]}`); break; }
      }
      const sinAlt = [...document.images].filter((i) => !i.hasAttribute('alt')).length;
      if (sinAlt) out.push(`${sinAlt} imágenes sin alt`);
      // width/height explícitos evitan CLS (las que llena el JS arrancan sin src)
      const sinDim = [...document.images].filter((i) => i.getAttribute('src') &&
        !i.getAttribute('width') && !getComputedStyle(i).aspectRatio.includes('/')).length;
      if (sinDim) out.push(`${sinDim} imágenes sin width/height`);
      const ids = [...document.querySelectorAll('[id]')].map((e) => e.id);
      const dup = [...new Set(ids.filter((v, i) => ids.indexOf(v) !== i))];
      if (dup.length) out.push(`ids duplicados: ${dup.join(',')}`);
      const mudos = [...document.querySelectorAll('a,button')].filter((e) =>
        !e.textContent.trim() && !e.getAttribute('aria-label') && !e.querySelector('img[alt]:not([alt=""])')).length;
      if (mudos) out.push(`${mudos} enlaces/botones sin nombre accesible`);
      if (!document.documentElement.lang) out.push('sin atributo lang');
      return out;
    });
    if (estructura.length) errores.push(`${p} (${nombre}): ${estructura.join(' · ')}`);

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
    // el banner ya se ha medido: se despacha rechazando (el peor caso para el
    // sitio) y el resto se mide y se fotografía sin nada encima
    await page.evaluate(() => document.querySelector('#cookies .ck-rechazar')?.click());

    const comercial = !['404.html', 'aviso-legal.html', 'privacidad.html',
                        'cookies.html', 'terminos.html'].includes(p);
    const tope = viewport.height * 2.5;
    if (comercial && cob.hueco > tope) {
      errores.push(`${p} (${nombre}): ${Math.round(cob.hueco / viewport.height * 10) / 10} pantallas sin CTA de WhatsApp`);
    }

    // las páginas son landings de Google Ads: el primer CTA entra en el fold
    if (nombre === 'movil' && comercial) {
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
  // pruebas funcionales (solo escritorio)
  if (nombre === 'desktop') {
    // consentimiento: aparece, aparta los flotantes mientras decide, y se cierra
    // al rechazar sin dejar ninguna carga externa metida en la página.
    // El bucle de arriba ya ha rechazado y la decisión queda guardada, así que
    // primero se limpia el almacenamiento: si no, esto probaría la segunda visita.
    await page.goto('file://' + join(WEB, 'index.html'), { waitUntil: 'load' });
    await page.evaluate(() => { try { localStorage.clear(); } catch (e) { /* file:// */ } });
    await page.reload({ waitUntil: 'load' });
    if (!(await page.isVisible('#cookies'))) errores.push('el banner de cookies no aparece en la primera visita');
    const tapado = await page.evaluate(() =>
      getComputedStyle(document.querySelector('.wsp-flotante')).display === 'none');
    if (!tapado) errores.push('con el banner abierto, el flotante de WhatsApp sigue disputándole la esquina');
    await page.screenshot({ path: join(OUT, 'cookies-desktop.png') });
    await page.click('#cookies .ck-rechazar');
    if (await page.isVisible('#cookies')) errores.push('el banner de cookies no se cierra al rechazar');
    const externas = await page.evaluate(() => ({
      iframes: document.querySelectorAll('iframe').length,
      scripts: [...document.querySelectorAll('script[src]')]
        .filter((s) => /^https?:/.test(s.getAttribute('src'))).length,
    }));
    if (externas.iframes || externas.scripts) {
      errores.push('tras rechazar quedan cargas externas: ' + JSON.stringify(externas));
    }
    console.log('Consentimiento OK → rechazar deja el sitio sin cargas de terceros');

    // calculadora + evento calculadora_uso en el dataLayer
    await ir(page, 'calculadora-frigorias.html');
    await page.fill('#m2', '25');
    await page.selectOption('#orientacion', 'oeste');
    await page.click('button[type=submit]');
    const cifra = await page.textContent('#calc-resultado .cifra');
    console.log('Calculadora 25 m² oeste →', cifra?.trim());
    if (!cifra || !/frigorías/.test(cifra)) errores.push('calculadora sin resultado');
    if (!cifra || !/BTU/.test(cifra)) errores.push('la calculadora no muestra la equivalencia en BTU');
    const evCalc = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'calculadora_uso'));
    if (!evCalc || evCalc.m2 !== 25 || !evCalc.frigorias_resultado || !evCalc.equipo_recomendado) {
      errores.push('dataLayer sin calculadora_uso válido: ' + JSON.stringify(evCalc));
    } else console.log('dataLayer calculadora_uso →', JSON.stringify(evCalc));

    // whatsapp_click: clic en el CTA del hero sin navegar
    await ir(page, 'index.html');
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), true));
    await page.click('.hero a[data-wsp]');
    const evWsp = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'whatsapp_click'));
    if (!evWsp || evWsp.origen !== 'hero' || evWsp.pagina !== 'index') {
      errores.push('dataLayer sin whatsapp_click de hero: ' + JSON.stringify(evWsp));
    } else console.log('dataLayer whatsapp_click →', JSON.stringify(evWsp));

    // agenda_click desde la página de servicios
    await ir(page, 'servicios.html');
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), true));
    await page.click('a[data-agenda]');
    const evAg = await page.evaluate(() => (window.dataLayer || []).find((e) => e.event === 'agenda_click'));
    if (!evAg || evAg.pagina !== 'servicios') errores.push('dataLayer sin agenda_click: ' + JSON.stringify(evAg));
    else console.log('dataLayer agenda_click →', JSON.stringify(evAg));

    // chatbot: 4 preguntas → enlace de WhatsApp armado + eventos
    await ir(page, 'index.html');
    await page.click('.wsp-flotante');
    await page.fill('#chat-pie input', 'Test QA');
    await page.click('#chat-pie button[type=submit]');
    await page.click('.chat-chip[data-valor="Marbella"]');
    await page.click('.chat-chip[data-valor="Instalación nueva"]');
    await page.click('.chat-chip[data-valor="Split"]');
    const hrefChat = await page.getAttribute('.chat-final', 'href');
    const evChat = await page.evaluate(() => ({
      inicio: (window.dataLayer || []).some((e) => e.event === 'chatbot_inicio'),
      pasos: (window.dataLayer || []).filter((e) => e.event === 'chatbot_paso').length,
    }));
    if (!hrefChat || !hrefChat.includes('Test%20QA') || !hrefChat.includes('Marbella')) {
      errores.push('chatbot: enlace final sin datos (' + hrefChat + ')');
    }
    if (!evChat.inicio || evChat.pasos !== 4) errores.push('chatbot: eventos dataLayer incompletos ' + JSON.stringify(evChat));
    await page.keyboard.press('Escape');
    if (await page.isVisible('#chat')) errores.push('chatbot no cierra con Escape');
    console.log('Chatbot OK →', decodeURIComponent(hrefChat.split('text=')[1] || ''));

    // accesibilidad por teclado: anillo de foco visible en filtros y fotos
    await ir(page, 'obras.html');
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

    // captura del asistente para la revisión (una conversación completa)
    await ir(page, 'index.html');
    await page.click('.wsp-flotante');
    await page.fill('#chat-pie input', 'Sofía');
    await page.click('#chat-pie button[type=submit]');
    await page.click('.chat-chip[data-valor="Málaga capital"]');
    await page.click('.chat-chip[data-valor="Sustitución de equipo"]');
    await page.click('.chat-chip[data-valor="Multisplit"]');
    await page.screenshot({ path: join(OUT, 'chatbot-desktop.png') });

    // galería: filtros + lightbox accesible (abre, navega, cierra con Escape)
    await ir(page, 'obras.html');
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
    await ir(page, 'index.html');
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
console.log(`QA OK: ${paginas.length} páginas × 2 tamaños capturadas en web-es/tools/shots/`);
