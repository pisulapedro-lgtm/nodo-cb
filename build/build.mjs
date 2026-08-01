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
import * as FIN from './financiero.mjs';

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

// Bloques generados por código: `sustituir()` los deja pasar y se resuelven
// contra el objeto `bloques`. Una sola lista para que no se puedan desincronizar.
const RESERVADOS = [
  'gantt', 'tabla_presupuesto', 'tabla_fuentes', 'tabla_stack',
  'tabla_semana_0', 'tabla_semana_1', 'tabla_semana_2', 'tabla_semana_3', 'tabla_semana_4',
  'tabla_unit_economics', 'tabla_pyl', 'tabla_caja', 'tabla_breakeven',
  'tabla_escenarios', 'tabla_sena',
];

// Cifras del modelo que se citan en la prosa de la sección 6. Se calculan acá,
// desde el mismo motor que alimenta las tablas, para que el texto no pueda quedar
// contando una historia distinta de la que muestran los cuadros.
{
  const ue = FIN.unitEconomics(datos);
  const { meses, anios } = FIN.proyeccion24m(datos);
  const caja = FIN.flujoCaja(datos);
  const be = FIN.breakEven(datos);
  const escs = FIN.escenarios(datos);
  const temporada = meses.slice(2, 6).reduce((s, m) => s + m.ingresos, 0); // nov · dic · ene · feb
  const un = (n) => n.toFixed(1).replace('.', ',');

  datos._fin = {
    caja_minima: caja.minimo.saldo,
    caja_minima_eur: caja.minimo.saldo / TC,
    caja_minima_mes: caja.minimo.etiqueta,
    sena_obra_tipo: ue.blended.ticket_ars * datos.financiero.cobros.sena_pct,
    neto_a1: anios[0].resultadoNeto,
    neto_a1_eur: anios[0].resultadoNeto / TC,
    neto_a1_eur_tc_bajo: anios[0].resultadoNeto / datos.financiero.sensibilidad_tc[0],
    neto_a1_eur_tc_alto: anios[0].resultadoNeto / datos.financiero.sensibilidad_tc[2],
    brecha_escenarios_eur: (escs[2].resultadoNetoAnio1 - escs[0].resultadoNetoAnio1) / TC,
    peso_temporada: un((temporada / anios[0].ingresos) * 100),
    be_pico: un(be.conMarketingPico),
    be_empleado: un(be.conEmpleado),
    // Piso de caja operativo: tres meses de estructura + el equipo de tres obras tipo.
    piso_caja: datos.financiero.fijos_mensuales_ars.reduce((s, f) => s + f.ars, 0) * 3 + ue.blended.costoEquipo * 3,
  };
}

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
    if (RESERVADOS.includes(path)) return m;
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
  let html = '<table class="larga"><thead><tr><th>#</th><th>Partida</th><th>Detalle</th><th class="num">EUR</th><th class="num">ARS</th><th>Carácter</th></tr></thead><tbody>';
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
  let html = '<table class="larga"><thead><tr><th>ID</th><th>Fuente</th><th>URL</th><th>Consulta</th><th>Tipo</th></tr></thead><tbody>';
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

// ---------- generadores financieros ----------
// Todos leen del motor compartido (build/financiero.mjs), nunca de números sueltos:
// es lo que garantiza que el PDF y la planilla cuenten lo mismo.
const pct = (n) => `${(n * 100).toFixed(1).replace('.', ',')} %`;

function renderUnitEconomics() {
  const { filas, blended } = FIN.unitEconomics(datos);
  let html = '<table><thead><tr><th>Categoría</th><th class="num">Mix</th><th class="num">Ticket</th>'
    + '<th class="num">Equipo</th><th class="num">Instalación</th><th class="num">Materiales</th>'
    + '<th class="num">Margen bruto</th><th class="num">Comisión + IIBB</th><th class="num">Contribución</th></tr></thead><tbody>';
  for (const f of filas) {
    html += `<tr><td><strong>${f.tipo}</strong> <small>[${f.fuente}]</small></td><td class="num">${pct(f.peso)}</td>`
      + `<td class="num">${ars(f.ticket_ars)}</td><td class="num">${ars(f.costoEquipo)}</td>`
      + `<td class="num">${ars(f.instalacion)}</td><td class="num">${ars(f.materiales)}</td>`
      + `<td class="num">${ars(f.margenBruto)}<br><small>${pct(f.margenBrutoPct)}</small></td>`
      + `<td class="num">${ars(f.comision + f.iibb)}</td>`
      + `<td class="num">${ars(f.contribucion)}<br><small>${pct(f.contribucionPct)}</small></td></tr>`;
  }
  html += `<tr class="total"><td>OBRA TIPO (promedio ponderado)</td><td class="num">100,0 %</td>`
    + `<td class="num">${ars(blended.ticket_ars)}</td><td class="num">${ars(blended.costoEquipo)}</td>`
    + `<td class="num">${ars(blended.instalacion)}</td><td class="num">${ars(blended.materiales)}</td>`
    + `<td class="num">${ars(blended.margenBruto)}<br><small>${pct(blended.margenBrutoPct)}</small></td>`
    + `<td class="num">${ars(blended.comision + blended.iibb)}</td>`
    + `<td class="num">${ars(blended.contribucion)}<br><small>${pct(blended.contribucionPct)}</small></td></tr>`;
  html += '</tbody></table>';
  html += `<p class="leyenda">† Todas las cifras son estimaciones propias sobre precios de mercado de agosto-2026 en ARS constantes. `
    + `Restando el costo de adquisición de cliente (${ars(datos.financiero.costos_obra.cac_ars)}), cada obra tipo deja `
    + `<strong>${ars(blended.contribucionNeta)}</strong> (${eur(blended.contribucionNeta / TC)}) para cubrir estructura.</p>`;
  return html;
}

function renderPyL() {
  const { meses, anios } = FIN.proyeccion24m(datos);
  const cols = [
    ['Obras', (m) => fmtARS.format(Math.round(m.obras)), (a) => fmtARS.format(Math.round(a.obras))],
    ['Facturación', (m) => ars(m.ingresos), (a) => ars(a.ingresos)],
    ['Margen bruto', (m) => ars(m.margenBruto), (a) => ars(a.margenBruto)],
    ['Estructura', (m) => ars(m.fijos), (a) => ars(a.fijos)],
    ['Marketing', (m) => ars(m.marketing), (a) => ars(a.marketing)],
    ['Empleado', (m) => (m.empleado ? ars(m.empleado) : '—'), (a) => (a.empleado ? ars(a.empleado) : '—')],
    ['Resultado operativo', (m) => ars(m.resultadoOperativo), (a) => ars(a.resultadoOperativo)],
  ];

  let html = '';
  for (const a of [0, 1]) {
    const tramo = meses.slice(a * 12, a * 12 + 12);
    html += `<p class="grupo">Año ${a + 1} del modelo — ${tramo[0].etiqueta} a ${tramo[11].etiqueta}</p>`;
    html += '<table class="larga compacta"><thead><tr><th>Concepto</th>';
    for (const m of tramo) html += `<th class="num">${m.etiqueta}</th>`;
    html += '<th class="num">Año</th></tr></thead><tbody>';
    for (const [nombre, fm, fa] of cols) {
      const esTotal = nombre === 'Resultado operativo';
      html += `<tr${esTotal ? ' class="total"' : ''}><td>${nombre}</td>`;
      for (const m of tramo) html += `<td class="num">${fm(m)}</td>`;
      html += `<td class="num">${fa(anios[a])}</td></tr>`;
    }
    html += `<tr class="subtotal"><td>Impuesto a las ganancias</td><td class="num" colspan="12">devengado al cierre del año</td>`
      + `<td class="num">${ars(anios[a].impuesto)}</td></tr>`;
    html += `<tr class="total"><td>RESULTADO NETO</td><td class="num" colspan="12">${eur(anios[a].resultadoNeto / TC)} al TC de portada</td>`
      + `<td class="num">${ars(anios[a].resultadoNeto)}</td></tr>`;
    html += '</tbody></table>';
  }
  return html;
}

function renderCaja() {
  const { filas, minimo } = FIN.flujoCaja(datos);
  const max = Math.max(...filas.map((f) => f.final));
  let html = '<table class="larga caja"><thead><tr><th>Mes</th><th class="num">Cobros</th>'
    + '<th class="num">Pagos</th><th class="num">Impuestos</th><th class="num">Saldo final</th>'
    + '<th>Curva de caja</th></tr></thead><tbody>';
  for (const f of filas) {
    const ancho = Math.max(1, Math.round((f.final / max) * 100));
    const esMin = f.i === minimo.i;
    html += `<tr${esMin ? ' class="subtotal"' : ''}><td>${f.etiqueta}${esMin ? ' ◄ mínimo' : ''}</td>`
      + `<td class="num">${ars(f.cobros)}</td><td class="num">${ars(f.pagos)}</td>`
      + `<td class="num">${ars(f.impCheque + f.impuestoGanancias)}</td>`
      + `<td class="num">${ars(f.final)}</td>`
      + `<td><div class="barra" style="width:${ancho}%"></div></td></tr>`;
  }
  html += '</tbody></table>';
  html += `<p class="leyenda">La caja arranca con el capital de ${eur(datos.capital.total_eur)} (${ars(datos.capital.total_ars)}) y `
    + `descuenta en el primer mes los ${eur(FIN.puestaEnMarcha(datos).eur)} de desembolsos únicos del presupuesto `
    + `(bloques A y B: constitución, legal, marca, identidad y equipamiento). Los bloques C y D del presupuesto no se suman `
    + `aparte: son los mismos costos fijos y de marketing que ya corren mes a mes en esta tabla.</p>`;
  return html;
}

function renderBreakEven() {
  const be = FIN.breakEven(datos);
  const filas = [
    ['Solo estructura fija', be.fijos, be.contribucionPorObra, be.soloFijos, 'Contador, stack, seguros, autónomos, movilidad y bancarios.'],
    ['Estructura + marketing de valle', be.fijos + Math.min(...datos.financiero.marketing_ars.slice(0, 12)), be.contribucionNetaPorObra, be.conMarketingValle, 'Meses de invierno, con la pauta al mínimo de sostenimiento.'],
    ['Estructura + marketing de temporada', be.fijos + Math.max(...datos.financiero.marketing_ars.slice(0, 12)), be.contribucionNetaPorObra, be.conMarketingPico, 'Pico de diciembre-enero, con la pauta al máximo.'],
    ['… + primer técnico en relación de dependencia', be.fijos + Math.max(...datos.financiero.marketing_ars.slice(0, 12)) + datos.financiero.empleado.costo_empleador_ars, be.contribucionNetaPorObra, be.conEmpleado, 'Costo empleador completo (Rama 17 UOM + cargas + ART).'],
  ];
  let html = '<table><thead><tr><th>Escenario de estructura</th><th class="num">Costo a cubrir/mes</th>'
    + '<th class="num">Contribución por obra</th><th class="num">Obras/mes para empatar</th><th>Lectura</th></tr></thead><tbody>';
  for (const [nombre, costo, contrib, obras, nota] of filas) {
    html += `<tr><td><strong>${nombre}</strong></td><td class="num">${ars(costo)}</td>`
      + `<td class="num">${ars(contrib)}</td><td class="num"><strong>${obras.toFixed(1).replace('.', ',')}</strong></td><td>${nota}</td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

function renderEscenarios() {
  const escs = FIN.escenarios(datos);
  const defs = datos.financiero.escenarios;
  let html = '<table><thead><tr><th>Métrica</th>';
  for (const e of escs) html += `<th class="num">${e.nombre}</th>`;
  html += '</tr></thead><tbody>';
  const filas = [
    ['Supuesto', (e, i) => `${pct(defs[i].obras_mult)} obras · ${pct(defs[i].ticket_mult)} ticket`],
    ['Obras año 1', (e) => fmtARS.format(Math.round(e.obrasAnio1))],
    ['Facturación año 1', (e) => ars(e.ingresosAnio1)],
    ['Resultado neto año 1', (e) => `${ars(e.resultadoNetoAnio1)}<br><small>${eur(e.resultadoNetoAnio1Eur)}</small>`],
    ['Resultado neto año 2', (e) => `${ars(e.resultadoNetoAnio2)}<br><small>${eur(e.resultadoNetoAnio2 / TC)}</small>`],
    ['Caja mínima', (e) => `${ars(e.cajaMinima)}<br><small>${e.cajaMinimaMes}</small>`],
    ['Caja a 24 meses', (e) => ars(e.cajaFinal)],
    ['Recupero del aporte', (e) => e.paybackEtiqueta],
  ];
  for (const [nombre, fn] of filas) {
    const esTotal = nombre === 'Recupero del aporte';
    html += `<tr${esTotal ? ' class="total"' : ''}><td><strong>${nombre}</strong></td>`;
    escs.forEach((e, i) => { html += `<td class="num">${fn(e, i)}</td>`; });
    html += '</tr>';
  }
  html += '</tbody></table>';
  return html;
}

function renderSena() {
  const filas = FIN.sensibilidadSena(datos);
  let html = '<table><thead><tr><th class="num">Seña cobrada al firmar</th><th class="num">Caja mínima</th>'
    + '<th>Mes del mínimo</th><th>Lectura</th></tr></thead><tbody>';
  const lectura = ['Política recomendada: la seña paga el equipo antes de pedirlo al mayorista.',
    'Sigue siendo sostenible, pero el colchón se adelgaza en el arranque.',
    'El capital de trabajo pasa a financiar equipos ajenos: hay que negociar cuenta corriente antes de aceptarlo.'];
  filas.forEach((f, i) => {
    html += `<tr><td class="num"><strong>${pct(f.sena)}</strong></td><td class="num">${ars(f.minimo)}</td>`
      + `<td>${f.mes}</td><td>${lectura[i] ?? ''}</td></tr>`;
  });
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
  tabla_unit_economics: renderUnitEconomics(),
  tabla_pyl: renderPyL(),
  tabla_caja: renderCaja(),
  tabla_breakeven: renderBreakEven(),
  tabla_escenarios: renderEscenarios(),
  tabla_sena: renderSena(),
};

// Red de seguridad de la doble registración: si un bloque queda solo en un sitio,
// el error salta acá y no como un `{{placeholder}}` impreso en el PDF.
for (const k of RESERVADOS) {
  if (!(k in bloques)) throw new Error(`Bloque reservado sin generador: {{${k}}}`);
}
for (const k of Object.keys(bloques)) {
  if (!RESERVADOS.includes(k)) throw new Error(`Generador sin registrar en RESERVADOS: {{${k}}}`);
}

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
