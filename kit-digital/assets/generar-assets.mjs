// Genera los assets de marca del kit digital (avatar, portadas, plantilla de post)
// Uso: node kit-digital/assets/generar-assets.mjs
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require_('playwright')); }
catch { ({ chromium } = require_('/opt/node22/lib/node_modules/playwright')); }

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '..', '..');
const b64 = (p) => readFileSync(join(RAIZ, p)).toString('base64');

const isotipo = `data:image/svg+xml;base64,${b64('build/assets/isotipo.svg')}`;
const logoBlanco = `data:image/svg+xml;base64,${b64('build/assets/logo-principal-blanco.svg')}`;
const logo = `data:image/svg+xml;base64,${b64('build/assets/logo-principal.svg')}`;
const f400 = b64('build/assets/fonts/poppins-400.woff2');
const f600 = b64('build/assets/fonts/poppins-600.woff2');
const f800 = b64('build/assets/fonts/poppins-800.woff2');

const CSS = `
@font-face{font-family:P;font-weight:400;src:url(data:font/woff2;base64,${f400}) format('woff2')}
@font-face{font-family:P;font-weight:600;src:url(data:font/woff2;base64,${f600}) format('woff2')}
@font-face{font-family:P;font-weight:800;src:url(data:font/woff2;base64,${f800}) format('woff2')}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:P,sans-serif;-webkit-font-smoothing:antialiased}
.grad{background:linear-gradient(150deg,#0058B3 0%,#01417f 58%,#00285A 100%)}
`;

const LIENZOS = {
  // Avatar cuadrado (IG / WhatsApp / LinkedIn logo): isotipo sobre blanco (uso permitido v01)
  'avatar-1080.png': {
    w: 1080, h: 1080,
    html: `<div style="width:1080px;height:1080px;background:#fff;display:grid;place-items:center">
             <img src="${isotipo}" style="width:640px">
           </div>`,
  },
  // Variante sobre azul de marca (uso permitido v02) por si el blanco se pierde en fondos claros
  'avatar-azul-1080.png': {
    w: 1080, h: 1080,
    html: `<div class="grad" style="width:1080px;height:1080px;display:grid;place-items:center">
             <img src="${logoBlancoCuadrado()}" style="width:720px">
           </div>`,
  },
  // Portada LinkedIn (1584×396)
  'portada-linkedin-1584x396.png': {
    w: 1584, h: 396,
    html: `<div class="grad" style="width:1584px;height:396px;display:flex;align-items:center;justify-content:space-between;padding:0 90px">
             <div>
               <div style="color:#fff;font-weight:800;font-size:44px;line-height:1.2">Tu confort, nuestra prioridad</div>
               <div style="color:#bfe4ff;font-weight:400;font-size:24px;margin-top:12px">Aire acondicionado en el corredor norte de Buenos Aires<br>Venta · Instalación certificada · Posventa real</div>
             </div>
             <img src="${logoBlanco}" style="height:150px">
           </div>`,
  },
  // Portada Facebook/WhatsApp Business web (820×312)
  'portada-facebook-820x312.png': {
    w: 820, h: 312,
    html: `<div class="grad" style="width:820px;height:312px;display:flex;align-items:center;justify-content:center;gap:60px">
             <img src="${logoBlanco}" style="height:110px">
             <div style="color:#bfe4ff;font-size:20px;border-left:2px solid rgba(255,255,255,.4);padding-left:40px;line-height:1.7">Núñez · Vicente López · San Isidro<br>Tigre · Nordelta · Pilar</div>
           </div>`,
  },
  // Plantilla de post IG (1080×1080): marco de marca con área de contenido
  'post-plantilla-1080.png': {
    w: 1080, h: 1080,
    html: `<div class="grad" style="width:1080px;height:1080px;padding:56px;display:flex;flex-direction:column">
             <div style="flex:1;background:#fff;border-radius:28px;padding:64px;display:flex;flex-direction:column;justify-content:center">
               <div style="color:#00A8FC;font-weight:600;font-size:30px;letter-spacing:.12em;text-transform:uppercase">[ANTETÍTULO]</div>
               <div style="color:#00285A;font-weight:800;font-size:72px;line-height:1.15;margin-top:18px">[TITULAR DEL POST EN DOS LÍNEAS]</div>
               <div style="color:#5a6675;font-size:34px;margin-top:26px;line-height:1.5">[Bajada breve del mensaje]</div>
             </div>
             <div style="display:flex;align-items:center;justify-content:space-between;padding-top:36px">
               <img src="${logoBlanco}" style="height:84px">
               <div style="color:#bfe4ff;font-size:28px">climabaires.com</div>
             </div>
           </div>`,
  },
  // Historia/story 1080×1920 con CTA WhatsApp
  'story-plantilla-1080x1920.png': {
    w: 1080, h: 1920,
    html: `<div class="grad" style="width:1080px;height:1920px;padding:80px;display:flex;flex-direction:column;justify-content:space-between">
             <img src="${logoBlanco}" style="height:110px;align-self:flex-start">
             <div>
               <div style="color:#fff;font-weight:800;font-size:88px;line-height:1.15">[TITULAR<br>DE LA STORY]</div>
               <div style="color:#bfe4ff;font-size:40px;margin-top:30px;line-height:1.5">[Bajada o dato concreto]</div>
             </div>
             <div style="background:#25D366;border-radius:999px;color:#fff;font-weight:600;font-size:40px;text-align:center;padding:34px">Escribinos por WhatsApp 👆 link en bio</div>
           </div>`,
  },
};

// El "logo blanco cuadrado" del avatar azul es el isologotipo apilado en blanco:
function logoBlancoCuadrado() {
  const svg = readFileSync(join(RAIZ, 'build/assets/logo-apilado.svg'), 'utf8')
    .replace(/rgb\(0%, 15\.686035%, 35\.293579%\)/g, 'rgb(100%, 100%, 100%)');
  return 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
}

const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage();
mkdirSync(AQUI, { recursive: true });
for (const [nombre, { w, h, html }] of Object.entries(LIENZOS)) {
  await page.setViewportSize({ width: w, height: h });
  await page.setContent(`<style>${CSS}</style>${html}`, { waitUntil: 'load' });
  await page.waitForTimeout(150);
  await page.screenshot({ path: join(AQUI, nombre), clip: { x: 0, y: 0, width: w, height: h } });
  console.log('  ✓', nombre);
}
await browser.close();
console.log('Assets del kit generados en kit-digital/assets/');
