#!/usr/bin/env node
/**
 * Build del «Plan de Acción 30 Días — Clima Baires Argentina»
 * src/*.md + src/datos.json + src/fuentes.json  →  dist/plan.html  →  PDF (Playwright/Chromium)
 *
 * Uso:  npm run build            (versión de src/datos.json → meta.version)
 *       npm run build -- --version 1.0
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require_ = createRequire(import.meta.url);
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'src');
const DIST = join(ROOT, 'dist');

const { marked } = require_('marked');
let chromium;
try {
  ({ chromium } = require_('playwright'));
} catch {
  ({ chromium } = require_('/opt/node22/lib/node_modules/playwright'));
}

// ---------- datos ----------
const datos = JSON.parse(readFileSync(join(SRC, 'datos.json'), 'utf8'));
const fuentes = JSON.parse(readFileSync(join(SRC, 'fuentes.json'), 'utf8'));

const argv = process.argv.slice(2);
const vIdx = argv.indexOf('--version');
const VERSION = vIdx >= 0 ? argv[vIdx + 1] : datos.meta.version;
const TC = datos.cambio.eur_ars; // ARS por 1 EUR

const fmtARS = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 });
const fmtEUR = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 });
const ars = (n) => `$ ${fmtARS.format(Math.round(n))}`;
const eur = (n) => `€ ${fmtEUR.format(Math.round(n))}`;

// ---------- helpers de plantilla ----------
function getPath(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function sustituir(md) {
  return md.replace(/\{\{([a-z]+):([\w.]+)\}\}|\{\{([\w.]+)\}\}/g, (m, fmt, fpath, path) => {
    if (fmt) {
      const v = getPath(datos, fpath);
      if (v === undefined) return m; // se detecta en validación
      if (fmt === 'eur') return eur(v);
      if (fmt === 'ars') return ars(v);
      if (fmt === 'arsdeeur') return ars(v * TC);
      if (fmt === 'pct') return `${v}%`;
      return m;
    }
    // generadores reservados se resuelven fuera
    if (['gantt', 'tabla_presupuesto', 'tabla_fuentes', 'tabla_stack', 'tabla_semana_1', 'tabla_semana_2', 'tabla_semana_3', 'tabla_semana_4', 'tabla_semana_0'].includes(path)) return m;
    const v = getPath(datos, path);
    return v === undefined ? m : String(v);
  });
}

// ---------- generadores ----------
const WS_META = {
  legal:     { nombre: 'Legal / societario', clase: 'on-legal' },
  fiscal:    { nombre: 'Fiscal',             clase: 'on-fiscal' },
  banca:     { nombre: 'Banca y cobros',     clase: 'on-banca' },
  ops:       { nombre: 'Operaciones',        clase: 'on-ops' },
  stack:     { nombre: 'Stack digital',      clase: 'on-stack' },
  comercial: { nombre: 'Comercial / GTM',    clase: 'on-comercial' },
  personas:  { nombre: 'Personas',           clase: 'on-personas' },
};

function renderGantt(cron) {
  const DIAS = datos.meta.dias_plan || 30;
  const orden = Object.keys(WS_META);
  const tareas = cron.filter((t) => !t.semana0).sort((a, b) =>
    orden.indexOf(a.workstream) - orden.indexOf(b.workstream) || a.dia_inicio - b.dia_inicio);

  let html = '<table class="gantt"><thead><tr><th class="tarea">Tarea</th>';
  for (let d = 1; d <= DIAS; d++) html += `<th>${d}</th>`;
  html += '</tr><tr><th class="tarea">Semana</th>';
  for (let d = 1; d <= DIAS; d++) {
    const s = Math.min(4, Math.ceil(d / 7));
    html += `<th>S${s}</th>`;
  }
  html += '</tr></thead><tbody>';

  let wsActual = null;
  for (const t of tareas) {
    if (t.workstream !== wsActual) {
      wsActual = t.workstream;
      html += `<tr class="grupo"><td colspan="${DIAS + 1}">${WS_META[wsActual]?.nombre ?? wsActual}</td></tr>`;
    }
    html += `<tr><td class="tarea">${t.tarea}</td>`;
    for (let d = 1; d <= DIAS; d++) {
      const on = d >= t.dia_inicio && d <= t.dia_fin;
      html += `<td class="${on ? (WS_META[t.workstream]?.clase ?? '') : ''}"></td>`;
    }
    html += '</tr>';
  }
  html += '</tbody></table>';

  html += '<p class="gantt-leyenda"><strong>Workstreams:</strong>';
  for (const k of orden) {
    const bg = { legal: '#0058B3', fiscal: '#3E8BD8', banca: '#00A8FC', ops: '#00285A', stack: '#7fc8f0', comercial: '#63c7a4', personas: '#f0b45a' }[k];
    html += ` <span class="chip" style="background:${bg}"></span>${WS_META[k].nombre}`;
  }
  html += '</p>';
  return html;
}

function fechaDia(d) {
  // día 1 = fecha_inicio del plan
  const base = new Date(datos.meta.fecha_inicio + 'T12:00:00');
  const f = new Date(base.getTime() + (d - 1) * 86400000);
  const dias = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
  return `${dias[f.getDay()]} ${String(f.getDate()).padStart(2, '0')}/${String(f.getMonth() + 1).padStart(2, '0')}`;
}

function renderSemana(cron, semana) {
  let tareas;
  if (semana === 0) {
    tareas = cron.filter((t) => t.semana0);
  } else {
    const d0 = (semana - 1) * 7 + 1, d1 = semana === 4 ? 99 : semana * 7;
    tareas = cron.filter((t) => !t.semana0 && t.dia_inicio >= d0 && t.dia_inicio <= d1);
  }
  tareas = [...tareas].sort((a, b) => a.dia_inicio - b.dia_inicio || a.dia_fin - b.dia_fin);
  let html = '<table><thead><tr><th>Días</th><th>Tarea</th><th>Responsable</th><th>Depende de</th><th class="num">Costo</th></tr></thead><tbody>';
  for (const t of tareas) {
    const rango = t.semana0 ? (t.fechas ?? '—')
      : (t.dia_inicio === t.dia_fin ? `${t.dia_inicio} (${fechaDia(t.dia_inicio)})` : `${t.dia_inicio}–${t.dia_fin} (${fechaDia(t.dia_inicio)} → ${fechaDia(t.dia_fin)})`);
    const costo = t.costo_eur ? `${eur(t.costo_eur)} · ${ars(t.costo_eur * TC)}` : (t.costo_texto ?? '—');
    html += `<tr><td>${rango}</td><td><strong>${t.tarea}</strong>${t.detalle ? `<br>${t.detalle}` : ''}</td><td>${t.responsable ?? '—'}</td><td>${t.dependencias ?? '—'}</td><td class="num">${costo}</td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

function renderPresupuesto(p) {
  let html = '<table><thead><tr><th>#</th><th>Partida</th><th>Detalle</th><th class="num">EUR</th><th class="num">ARS</th><th>Carácter</th></tr></thead><tbody>';
  let i = 0, suma = 0;
  let bloque = null;
  for (const it of p.partidas) {
    if (it.bloque !== bloque) {
      bloque = it.bloque;
      html += `<tr class="subtotal"><td colspan="6">${bloque}</td></tr>`;
    }
    i += 1; suma += it.eur;
    const car = it.caracter === 'estimacion' ? '<span class="estimacion">estimación †</span>' : 'verificado';
    const fx = it.fuente ? ` <small>[${it.fuente}]</small>` : '';
    html += `<tr><td>${i}</td><td><strong>${it.concepto}</strong></td><td>${(it.nota ?? '')}${fx}</td><td class="num">${eur(it.eur)}</td><td class="num">${ars(it.eur * TC)}</td><td>${car}</td></tr>`;
  }
  html += `<tr class="total"><td colspan="3">TOTAL COMPROMETIDO</td><td class="num">${eur(suma)}</td><td class="num">${ars(suma * TC)}</td><td></td></tr>`;
  if (p.total_eur - suma > 0.5) {
    html += `<tr class="total"><td colspan="3">SIN ASIGNAR (reserva)</td><td class="num">${eur(p.total_eur - suma)}</td><td class="num">${ars((p.total_eur - suma) * TC)}</td><td></td></tr>`;
  }
  html += '</tbody></table>';
  html += `<p class="leyenda">† = estimación propia sobre fuentes de mercado, no cotización en firme. Conversión ARS al TC ${fmtARS.format(TC)} ARS/EUR (${datos.cambio.tipo}, ${datos.cambio.fecha}).</p>`;
  return { html, suma };
}

function renderFuentes(fs) {
  let html = '<table><thead><tr><th>ID</th><th>Fuente</th><th>URL</th><th>Consulta</th><th>Tipo</th></tr></thead><tbody>';
  for (const f of fs) {
    html += `<tr><td><strong>${f.id}</strong></td><td>${f.titulo}</td><td><a href="${f.url}">${f.url}</a></td><td>${f.fecha_consulta}</td><td>${f.tipo}</td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

function renderStack(stack) {
  let html = '<table><thead><tr><th>Herramienta</th><th>Rol (equivalente España)</th><th class="num">ARS/mes</th><th class="num">EUR/mes</th><th>Notas</th></tr></thead><tbody>';
  let tot = 0;
  for (const s of stack) {
    tot += s.ars_mes;
    const fx = s.fuente ? ` <small>[${s.fuente}]</small>` : '';
    html += `<tr><td><strong>${s.item}</strong></td><td>${s.rol ?? ''}</td><td class="num">${ars(s.ars_mes)}</td><td class="num">${eur(s.ars_mes / TC)}</td><td>${(s.nota ?? '')}${fx}</td></tr>`;
  }
  html += `<tr class="total"><td colspan="2">TOTAL STACK MENSUAL</td><td class="num">${ars(tot)}</td><td class="num">${eur(tot / TC)}</td><td></td></tr>`;
  html += '</tbody></table>';
  return html;
}

// ---------- ensamblado ----------
const archivos = readdirSync(SRC).filter((f) => f.endsWith('.md')).sort();
if (archivos.length === 0) throw new Error('No hay .md en src/');

const presupuestoR = datos.presupuesto.partidas.length ? renderPresupuesto(datos.presupuesto) : { html: '<p><em>Presupuesto pendiente.</em></p>', suma: 0 };

const bloques = {
  gantt: datos.cronograma.length ? renderGantt(datos.cronograma) : '<p><em>Cronograma pendiente.</em></p>',
  tabla_presupuesto: presupuestoR.html,
  tabla_fuentes: fuentes.length ? renderFuentes(fuentes) : '<p><em>Fuentes pendientes.</em></p>',
  tabla_stack: (datos.stack ?? []).length ? renderStack(datos.stack) : '<p><em>Stack pendiente.</em></p>',
  tabla_semana_0: renderSemana(datos.cronograma, 0),
  tabla_semana_1: renderSemana(datos.cronograma, 1),
  tabla_semana_2: renderSemana(datos.cronograma, 2),
  tabla_semana_3: renderSemana(datos.cronograma, 3),
  tabla_semana_4: renderSemana(datos.cronograma, 4),
};

let contenido = '';
for (const f of archivos) {
  let md = readFileSync(join(SRC, f), 'utf8');
  md = sustituir(md);
  let html = marked.parse(md, { gfm: true });
  for (const [k, v] of Object.entries(bloques)) html = html.replaceAll(`{{${k}}}`, v);
  // marcas editoriales
  html = html.replaceAll(/\[VALIDAR CON ([^\]]+)\]/g, '<span class="validar">[VALIDAR CON $1]</span>');
  const esPortada = f.startsWith('00');
  contenido += `<section class="capitulo${esPortada ? ' portada' : ''}" id="sec-${f.slice(0, 2)}">\n${html}\n</section>\n`;
}

// ---------- validaciones ----------
const errores = [], avisos = [];
const residual = contenido.match(/\{\{[\w.:]+\}\}/g);
if (residual) errores.push(`Placeholders sin resolver: ${[...new Set(residual)].join(', ')}`);

const citadas = new Set([...contenido.matchAll(/\[(F\d+)\]/g)].map((m) => m[1]));
const registradas = new Set(fuentes.map((f) => f.id));
for (const c of citadas) if (!registradas.has(c)) errores.push(`Cita ${c} sin registrar en fuentes.json`);
for (const r of registradas) if (!citadas.has(r)) avisos.push(`Fuente ${r} registrada pero nunca citada`);

if (datos.presupuesto.partidas.length) {
  const suma = presupuestoR.suma;
  if (suma > datos.presupuesto.total_eur + 0.5) {
    errores.push(`Presupuesto comprometido (€${suma}) EXCEDE el total (€${datos.presupuesto.total_eur})`);
  }
}
if (!TC || TC <= 0) errores.push('Tipo de cambio EUR/ARS inválido en datos.json');

if (avisos.length) console.warn('AVISOS:\n - ' + avisos.join('\n - '));
if (errores.length) {
  console.error('ERRORES DE VALIDACIÓN:\n - ' + errores.join('\n - '));
  process.exit(1);
}

// ---------- HTML final ----------
const template = readFileSync(join(ROOT, 'build', 'template.html'), 'utf8');
const TITULO = `Plan de Acción 30 Días — Clima Baires Argentina (v${VERSION})`;
const pagina = template.replace('{{TITULO}}', TITULO).replace('{{CONTENIDO}}', contenido);
const htmlPath = join(DIST, 'plan.html');
writeFileSync(htmlPath, pagina);

// ---------- PDF ----------
const logoB64 = readFileSync(join(ROOT, 'build', 'assets', 'logo-header.png')).toString('base64');
const pdfPath = join(DIST, `Plan-Accion-30-Dias-Clima-Baires-Argentina_v${VERSION}.pdf`);

const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.goto('file://' + htmlPath, { waitUntil: 'load' });
await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  displayHeaderFooter: true,
  margin: { top: '24mm', bottom: '16mm', left: '15mm', right: '15mm' },
  headerTemplate: `
    <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:4mm 15mm 0; display:flex; align-items:center; justify-content:space-between;">
      <img src="data:image/png;base64,${logoB64}" style="height:8mm"/>
      <span style="text-align:right;">Plan de Acción 30 Días — Argentina · v${VERSION}</span>
    </div>`,
  footerTemplate: `
    <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:0 15mm 4mm; display:flex; justify-content:space-between;">
      <span>Clima Baires · confidencial — uso interno de los socios</span>
      <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
    </div>`,
});
await browser.close();

console.log(`OK  ${pdfPath}`);
console.log(`    versión ${VERSION} · TC ${fmtARS.format(TC)} ARS/EUR (${datos.cambio.fecha}) · ${archivos.length} secciones · ${fuentes.length} fuentes`);
