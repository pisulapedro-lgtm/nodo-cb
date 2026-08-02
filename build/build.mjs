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
import * as MK from './marketing.mjs';
import * as CM from './comercial.mjs';

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
  'tabla_escenarios', 'tabla_sena', 'indice', 'miniaturas_web',
  'tabla_reparto_pauta', 'tabla_embudo', 'tabla_canales', 'tabla_sensibilidad_cpc', 'tabla_campanas_google',
  'tabla_mercado', 'tabla_tarifario', 'tabla_adicionales', 'tabla_horizonte', 'tabla_valoracion',
  'semana_ignacio',
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
    // Piso de caja operativo: tres meses de estructura + el equipo de tres instalaciones tipo.
    piso_caja: datos.financiero.fijos_mensuales_ars.reduce((s, f) => s + f.ars, 0) * 3 + ue.blended.costoEquipo * 3,
  };
}

// Cifras del plan de marketing que se citan en la prosa de las secciones 17 a 19.
// Mismo criterio que las del modelo financiero: las calcula el motor, no la mano.
{
  const emb = MK.embudo(datos);
  const canales = MK.porCanal(datos);
  const sens = MK.sensibilidad(datos);
  const [g, m, co] = canales;
  const t = emb.totales;
  const un = (n) => n.toFixed(0);

  datos._mk = {
    inversion_total: t.inversionTotal,
    inversion_total_eur: t.inversionTotal / TC,
    inversion_medible: t.inversion,
    inversion_countries: co.inversion,
    leads: un(t.leads),
    instalaciones_pagas: un(t.instalacionesPagas),
    instalaciones_propias: un(t.instalacionesPropias),
    cubierto_pct: un(t.cubiertoPct * 100),
    cpl: t.cpl,
    cac: t.cac,
    // Techo de tolerancia del CPL: el del escenario en que el clic se encarece un 30 %.
    cpl_techo: sens[1].cpl,
    pct_google: un((g.inversion / t.inversion) * 100),
    pct_instalaciones_google: un((g.instalaciones / t.instalacionesPagas) * 100),
    cac_google: g.cac,
    cac_meta: m.cac,
    google_anual: g.inversion,
    meta_anual: m.inversion,
  };
}

// Cifras comerciales y de horizonte citadas en la prosa de las secciones 9, 20 y 24.
{
  const a1 = FIN.proyeccion24m(datos).anios[0];
  const mc = CM.cuota(datos, a1.ingresos);
  const h = FIN.horizonte(datos);
  const un = (n, d = 0) => n.toFixed(d).replace('.', ',');

  datos._cm = {
    hogares: Math.round(mc.hogares),
    parque: Math.round(mc.parque),
    trabajos_anuales: Math.round(mc.trabajosAnuales),
    tam: mc.tam, tam_eur: mc.tam / TC,
    sam: mc.sam, sam_eur: mc.sam / TC,
    som_tam_pct: un(mc.somSobreTam * 100, 2),
    som_sam_pct: un(mc.somSobreSam * 100, 1),
    instalaciones_al_2pct: Math.round(mc.instalacionesAl2pct),
    instalaciones_a3: Math.round(h.anio3.instalaciones),
    neto_a3: h.anio3.resultadoNeto,
    neto_a3_eur: h.anio3.resultadoNeto / TC,
    valor_bajo_eur: h.valoracion[0].ajustada / TC,
    valor_alto_eur: h.valoracion[2].ajustada / TC,
    socio30_bajo_eur: (h.valoracion[0].ajustada * 0.30) / TC,
    socio30_alto_eur: (h.valoracion[2].ajustada * 0.30) / TC,
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
      // `porc` recibe una fracción (0,08) y la escribe como porcentaje (8,0 %).
      if (fmt === 'porc') return `${(v * 100).toFixed(1).replace('.', ',')} %`;
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
    + '<th class="num">Equipo</th><th class="num">Montaje</th><th class="num">Materiales</th>'
    + '<th class="num">Margen bruto</th><th class="num">Comisión + IIBB</th><th class="num">Contribución</th></tr></thead><tbody>';
  for (const f of filas) {
    html += `<tr><td><strong>${f.tipo}</strong> <small>[${f.fuente}]</small></td><td class="num">${pct(f.peso)}</td>`
      + `<td class="num">${ars(f.ticket_ars)}</td><td class="num">${ars(f.costoEquipo)}</td>`
      + `<td class="num">${ars(f.montaje)}</td><td class="num">${ars(f.materiales)}</td>`
      + `<td class="num">${ars(f.margenBruto)}<br><small>${pct(f.margenBrutoPct)}</small></td>`
      + `<td class="num">${ars(f.comision + f.iibb)}</td>`
      + `<td class="num">${ars(f.contribucion)}<br><small>${pct(f.contribucionPct)}</small></td></tr>`;
  }
  html += `<tr class="total"><td>INSTALACIÓN TIPO (promedio ponderado)</td><td class="num">100,0 %</td>`
    + `<td class="num">${ars(blended.ticket_ars)}</td><td class="num">${ars(blended.costoEquipo)}</td>`
    + `<td class="num">${ars(blended.montaje)}</td><td class="num">${ars(blended.materiales)}</td>`
    + `<td class="num">${ars(blended.margenBruto)}<br><small>${pct(blended.margenBrutoPct)}</small></td>`
    + `<td class="num">${ars(blended.comision + blended.iibb)}</td>`
    + `<td class="num">${ars(blended.contribucion)}<br><small>${pct(blended.contribucionPct)}</small></td></tr>`;
  html += '</tbody></table>';
  html += `<p class="leyenda">† Todas las cifras son estimaciones propias sobre precios de mercado de agosto-2026 en ARS constantes. `
    + `El conteo mensual de «instalaciones» del modelo incluye las visitas de mantenimiento, que son el `
    + `${pct(datos.financiero.mix[3].peso)} del mix: son trabajos con ticket y margen propios, no instalaciones nuevas. `
    + `Restando el costo de adquisición de cliente (${ars(datos.financiero.costos_instalacion.cac_ars)}), cada instalación tipo deja `
    + `<strong>${ars(blended.contribucionNeta)}</strong> (${eur(blended.contribucionNeta / TC)}) para cubrir estructura.</p>`;
  return html;
}

function renderPyL() {
  const { meses, anios } = FIN.proyeccion24m(datos);
  const cols = [
    ['Instalaciones', (m) => fmtARS.format(Math.round(m.instalaciones)), (a) => fmtARS.format(Math.round(a.instalaciones))],
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
    ['Solo estructura fija', be.fijos, be.contribucionPorInstalacion, be.soloFijos, 'Contador, stack, seguros, autónomos, movilidad y bancarios.'],
    ['Estructura + marketing de valle', be.fijos + Math.min(...datos.financiero.marketing_ars.slice(0, 12)), be.contribucionNetaPorInstalacion, be.conMarketingValle, 'Meses de invierno, con la pauta al mínimo de sostenimiento.'],
    ['Estructura + marketing de temporada', be.fijos + Math.max(...datos.financiero.marketing_ars.slice(0, 12)), be.contribucionNetaPorInstalacion, be.conMarketingPico, 'Pico de diciembre-enero, con la pauta al máximo.'],
    ['… + primer técnico en relación de dependencia', be.fijos + Math.max(...datos.financiero.marketing_ars.slice(0, 12)) + datos.financiero.empleado.costo_empleador_ars, be.contribucionNetaPorInstalacion, be.conEmpleado, 'Costo empleador completo (Rama 17 UOM + cargas + ART).'],
  ];
  let html = '<table><thead><tr><th>Escenario de estructura</th><th class="num">Costo a cubrir/mes</th>'
    + '<th class="num">Contribución por instalación</th><th class="num">Instalaciones/mes para empatar</th><th>Lectura</th></tr></thead><tbody>';
  for (const [nombre, costo, contrib, instalaciones, nota] of filas) {
    html += `<tr><td><strong>${nombre}</strong></td><td class="num">${ars(costo)}</td>`
      + `<td class="num">${ars(contrib)}</td><td class="num"><strong>${instalaciones.toFixed(1).replace('.', ',')}</strong></td><td>${nota}</td></tr>`;
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
    ['Supuesto', (e, i) => `${pct(defs[i].instalaciones_mult)} instalaciones · ${pct(defs[i].ticket_mult)} ticket`],
    ['Instalaciones año 1', (e) => fmtARS.format(Math.round(e.instalacionesAnio1))],
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

// ---------- índice ----------
// Marca que se imprime dentro de cada encabezado en blanco y a 0,6 pt: invisible en
// papel, pero `pdftotext` la lee y con eso sabemos en qué página quedó cada sección.
// Tiene que ser ASCII: los caracteres exóticos no están en la fuente y Chromium los descarta.
const ANCLA = (numero) => `@@${numero}@@`;

// El esquema sale de los propios encabezados de los .md: si se añade una sección,
// el índice la recoge sin tocar nada más.
function leerEsquema(archivos) {
  const esquema = [];
  for (const f of archivos) {
    if (f.startsWith('00')) continue; // portada e índice no se indexan a sí mismos
    const parte = (datos.partes ?? []).find((p) => f.startsWith(p.antes + '-'));
    if (parte) esquema.push({ nivel: 0, titulo: parte.numero ? `Parte ${parte.numero} — ${parte.titulo}` : parte.titulo });
    for (const linea of readFileSync(join(SRC, f), 'utf8').split('\n')) {
      const m = linea.match(/^(#{1,2}) (\d+(?:\.\d+)?)\.? +(.+)$/);
      if (m) esquema.push({ nivel: m[1].length, numero: m[2], titulo: m[3].trim() });
    }
  }
  return esquema;
}

// El número de página se resuelve en la segunda pasada: acá va un hueco del mismo
// ancho, para que la paginación no se mueva entre una pasada y la otra.
function renderIndice(esquema) {
  let html = '<table class="indice"><tbody>';
  for (const e of esquema) {
    if (e.nivel === 0) {
      html += `<tr class="parte"><td colspan="2">${e.titulo}</td></tr>`;
      continue;
    }
    const clase = e.nivel === 1 ? 'sec' : 'sub';
    html += `<tr class="${clase}"><td><span class="n">${e.numero}</span> ${e.titulo}</td>`
      + `<td class="pag"><span class="pag-hueco" data-n="${e.numero}">&nbsp;</span></td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

// ---------- miniaturas de la web ----------
function renderMiniaturas() {
  const dir = join(ROOT, 'build', 'assets', 'web');
  const manifiesto = join(dir, 'manifest.json');
  if (!existsSync(manifiesto)) return '<p><em>Miniaturas pendientes: correr <code>npm run miniaturas</code>.</em></p>';
  const items = JSON.parse(readFileSync(manifiesto, 'utf8'));
  let html = '<div class="miniaturas">';
  for (const it of items) {
    html += `<figure><img src="../build/assets/web/${it.archivo}" alt="${it.titulo}">`
      + `<figcaption><strong>${it.titulo}</strong><br>${it.pie}</figcaption></figure>`;
  }
  html += '</div>';
  html += `<p class="leyenda">Capturas del sitio tal como está hoy en el repositorio (${items.length} vistas de 21 páginas). `
    + `Se regeneran con <code>npm run web:shots &amp;&amp; npm run miniaturas</code>.</p>`;
  return html;
}

// ---------- generadores de marketing ----------
const nEs = (n, d = 1) => n.toFixed(d).replace('.', ',');

function renderRepartoPauta() {
  const mk = datos.marketing, n = mk.canales[0].ars.length;
  const et = (i) => FIN.etiquetaMes(datos.financiero, i);
  let html = '<table class="larga compacta"><thead><tr><th>Canal</th>';
  for (let i = 0; i < n; i++) html += `<th class="num">${et(i)}</th>`;
  html += '<th class="num">Año 1</th></tr></thead><tbody>';
  for (const c of mk.canales) {
    const tot = c.ars.reduce((s, x) => s + x, 0);
    html += `<tr><td><strong>${c.nombre}</strong>${c.fuente ? ` <small>[${c.fuente}]</small>` : ''}</td>`;
    for (const v of c.ars) html += `<td class="num">${v ? ars(v) : '—'}</td>`;
    html += `<td class="num">${ars(tot)}</td></tr>`;
  }
  const totMes = Array.from({ length: n }, (_, i) => mk.canales.reduce((s, c) => s + c.ars[i], 0));
  const tot = totMes.reduce((s, x) => s + x, 0);
  html += '<tr class="total"><td>TOTAL</td>';
  for (const v of totMes) html += `<td class="num">${ars(v)}</td>`;
  html += `<td class="num">${ars(tot)}</td></tr></tbody></table>`;
  html += `<p class="leyenda">Suma exactamente la serie de marketing del modelo financiero (${eur(tot / TC)} en el año 1): `
    + `no hay pauta fuera del presupuesto de la sección 6. El build aborta si dejan de cuadrar.</p>`;
  return html;
}

function renderEmbudo() {
  const { meses, totales } = MK.embudo(datos);
  let html = '<table class="larga"><thead><tr><th>Mes</th><th class="num">CPC †</th><th class="num">Clics</th>'
    + '<th class="num">Leads</th><th class="num">Instalaciones de pauta</th><th class="num">Plan</th>'
    + '<th class="num">De canales propios</th><th class="num">Cubierto por pauta</th></tr></thead><tbody>';
  for (const m of meses.slice(0, 12)) {
    const falta = m.propias > 0.5;
    html += `<tr${falta ? '' : ' class="subtotal"'}><td><strong>${m.etiqueta}</strong></td>`
      + `<td class="num">${ars(m.cpc)}</td><td class="num">${fmtARS.format(Math.round(m.clics))}</td>`
      + `<td class="num">${nEs(m.leads, 0)}</td><td class="num">${nEs(m.pagas)}</td>`
      + `<td class="num">${m.plan}</td><td class="num">${m.propias > 0 ? nEs(m.propias) : '—'}</td>`
      + `<td class="num">${nEs(m.cubiertoPct * 100, 0)} %</td></tr>`;
  }
  html += `<tr class="total"><td>AÑO 1</td><td class="num">—</td><td class="num">—</td>`
    + `<td class="num">${nEs(totales.leads, 0)}</td><td class="num">${nEs(totales.instalacionesPagas, 0)}</td>`
    + `<td class="num">${totales.instalacionesPlan}</td><td class="num">${nEs(totales.instalacionesPropias, 0)}</td>`
    + `<td class="num">${nEs(totales.cubiertoPct * 100, 0)} %</td></tr></tbody></table>`;
  html += `<p class="leyenda">† CPC estimado con estacionalidad: en diciembre y enero puja todo el rubro a la vez [F46]. `
    + `Las filas sombreadas son los meses en que la pauta cubre el plan por sí sola. `
    + `CPL medio ${ars(totales.cpl)} y CAC medio ${ars(totales.cac)} — por debajo de los ${ars(datos.financiero.costos_instalacion.cac_ars)} `
    + `que asume el modelo financiero, que queda así como el techo tolerable.</p>`;
  return html;
}

function renderCanales() {
  const canales = MK.porCanal(datos);
  let html = '<table><thead><tr><th>Canal</th><th class="num">Inversión año 1</th><th class="num">Leads</th>'
    + '<th class="num">CPL</th><th class="num">Lead → instalación</th><th class="num">Instalaciones</th><th class="num">CAC</th></tr></thead><tbody>';
  for (const c of canales) {
    html += `<tr><td><strong>${c.nombre}</strong></td><td class="num">${ars(c.inversion)}</td>`;
    if (c.leads === null) {
      html += '<td class="num" colspan="5">No genera leads medibles: compra acceso y credibilidad</td></tr>';
    } else {
      html += `<td class="num">${nEs(c.leads, 0)}</td><td class="num">${ars(c.cpl)}</td>`
        + `<td class="num">${nEs(c.convLeadInstalacion * 100, 0)} %</td><td class="num">${nEs(c.instalaciones, 0)}</td>`
        + `<td class="num">${ars(c.cac)}</td></tr>`;
    }
  }
  html += '</tbody></table>';
  return html;
}

function renderSensibilidadCPC() {
  const filas = MK.sensibilidad(datos);
  const lectura = ['Escenario base: el clic sale a lo previsto.',
    'El clic se encarece un 30 %: entra más competencia o sube la puja de temporada.',
    'El clic se encarece un 60 %: guerra de pujas en diciembre. Es el escenario que hay que poder aguantar.'];
  let html = '<table><thead><tr><th>Escenario</th><th class="num">CPL</th><th class="num">CAC</th>'
    + '<th class="num">Instalaciones de pauta</th><th class="num">Cubierto</th><th class="num">A cubrir con canales propios</th></tr></thead><tbody>';
  filas.forEach((f, i) => {
    html += `<tr><td><strong>${lectura[i]}</strong></td><td class="num">${ars(f.cpl)}</td>`
      + `<td class="num">${ars(f.cac)}</td><td class="num">${nEs(f.instalacionesPagas, 0)}</td>`
      + `<td class="num">${nEs(f.cubiertoPct * 100, 0)} %</td><td class="num">${nEs(f.instalacionesPropias, 0)} instalaciones</td></tr>`;
  });
  html += '</tbody></table>';
  return html;
}

function renderCampanasGoogle() {
  const mk = datos.marketing;
  // Mes de referencia: el pico, que es cuando el reparto importa de verdad.
  const iPico = mk.canales.find((c) => c.clave === 'google').ars.indexOf(
    Math.max(...mk.canales.find((c) => c.clave === 'google').ars));
  const presupuesto = mk.canales.find((c) => c.clave === 'google').ars[iPico];
  let html = '<table class="larga"><thead><tr><th>Campaña</th><th class="num">% del Search</th>'
    + `<th class="num">Diario en ${FIN.etiquetaMes(datos.financiero, iPico)}</th><th>Estrategia de puja</th><th>Para qué está</th></tr></thead><tbody>`;
  let suma = 0;
  for (const c of mk.campanas_google) {
    suma += c.pct;
    html += `<tr><td><code>${c.campana}</code></td><td class="num">${nEs(c.pct * 100, 0)} %</td>`
      + `<td class="num">${ars((presupuesto * c.pct) / 30)}</td><td>${c.puja}</td><td>${c.nota}</td></tr>`;
  }
  html += `<tr class="total"><td>TOTAL SEARCH</td><td class="num">${nEs(suma * 100, 0)} %</td>`
    + `<td class="num">${ars(presupuesto / 30)}</td><td colspan="2">Presupuesto mensual de ${ars(presupuesto)}</td></tr>`;
  html += '</tbody></table>';
  return html;
}


// ---------- generadores comerciales y de horizonte ----------
function renderMercado() {
  const m = CM.cuota(datos, FIN.proyeccion24m(datos).anios[0].ingresos);
  const k = datos.mercado;
  const n = (x) => fmtARS.format(Math.round(x));
  const filas = [
    ['Población de las seis localidades', n(m.poblacion), 'Censo 2022 [F49]; Nordelta va dentro de Tigre, no se suma aparte', ''],
    ['Personas por hogar', nEs(k.personas_por_hogar, 1), 'Promedio del AMBA', '†'],
    ['<strong>Hogares del corredor</strong>', `<strong>${n(m.hogares)}</strong>`, 'Población dividida por el tamaño del hogar', ''],
    ['Penetración de split', pct(k.penetracion_split), 'Por encima del 61,7 % del quintil de mayores ingresos de 2017-18 [F48]: el dato es viejo y el corredor está sobrerrepresentado en ese quintil', '†'],
    ['Equipos por hogar equipado', nEs(k.equipos_por_hogar_equipado, 1), 'En vivienda premium rara vez hay uno solo', '†'],
    ['<strong>Parque instalado</strong>', `<strong>${n(m.parque)} equipos</strong>`, 'Lo que hay hoy funcionando en el corredor', ''],
    ['Vida útil del equipo', `${k.vida_util_anios} años`, 'Recambio conveniente a partir de los 10-12 [F50]', ''],
    ['Recambio anual', n(m.recambioAnual), 'El parque dividido por su vida útil', ''],
    ['Altas anuales', n(m.altasAnuales), `Hogares que se equipan por primera vez (${pct(k.crecimiento_penetracion_anual)} de penetración al año)`, '†'],
    ['Equipos por trabajo', nEs(k.equipos_por_trabajo, 1), 'Un multisplit es un solo trabajo con varios equipos', '†'],
    ['<strong>Trabajos al año en el corredor</strong>', `<strong>${n(m.trabajosAnuales)}</strong>`, 'La demanda anual de instalación y recambio', ''],
    ['Ticket medio del mercado', ars(k.ticket_medio_mercado_ars), 'Por debajo del nuestro: incluye gama baja e instalación informal', '†'],
  ];
  let html = '<table class="larga"><thead><tr><th>Paso</th><th class="num">Valor</th><th>De dónde sale</th><th class="num">†</th></tr></thead><tbody>';
  for (const [c, v, d, e] of filas) {
    html += `<tr><td>${c}</td><td class="num">${v}</td><td>${d}</td><td class="num"><span class="estimacion">${e}</span></td></tr>`;
  }
  html += `<tr class="total"><td>TAM — todo el gasto anual del corredor</td><td class="num">${ars(m.tam)}</td>`
    + `<td colspan="2">${eur(m.tam / TC)} al año en equipos e instalación</td></tr>`;
  html += `<tr class="total"><td>SAM — el segmento premium con instalación certificada (${pct(k.sam_pct)})</td><td class="num">${ars(m.sam)}</td>`
    + `<td colspan="2">${eur(m.sam / TC)} — al que de verdad le hablamos</td></tr>`;
  html += `<tr class="subtotal"><td>SOM — lo que factura el plan en el año 1</td><td class="num">${ars(m.som)}</td>`
    + `<td colspan="2"><strong>${nEs(m.somSobreTam * 100, 2)} % del TAM</strong> y ${nEs(m.somSobreSam * 100, 1)} % del SAM</td></tr>`;
  html += '</tbody></table>';
  html += `<p class="leyenda">† = supuesto propio, no dato verificable. La aritmética queda a la vista a propósito: `
    + `cambiar la penetración o la vida útil mueve el TAM, y es más honesto discutir los supuestos que la conclusión.</p>`;
  return html;
}

function renderTarifario() {
  const t = CM.tarifario(datos);
  let html = '<table class="larga"><thead><tr><th>Categoría</th><th class="num">Lista (tarjeta 1 pago)</th>'
    + '<th class="num">Transferencia</th>';
  for (const c of datos.precios.cuotas) html += `<th class="num">${c.cuotas} cuotas</th>`;
  html += '</tr></thead><tbody>';
  for (const f of t.filas) {
    html += `<tr><td><strong>${f.tipo}</strong> <small>[${f.fuente}]</small></td>`
      + `<td class="num">${ars(f.lista)}</td>`
      + `<td class="num">${ars(f.transferencia)}<br><small>−${pct(datos.precios.descuento_transferencia)}</small></td>`;
    for (const c of f.cuotas) {
      html += `<td class="num">${ars(c.total)}<br><small>${c.cuotas} × ${ars(c.porCuota)}</small></td>`;
    }
    html += '</tr>';
  }
  html += '</tbody></table>';
  html += `<p class="leyenda">Precios finales con IVA incluido, en ARS de agosto-2026. El de lista ya contempla el costo de cobrar `
    + `con tarjeta en un pago; por eso la transferencia baja ${pct(datos.precios.descuento_transferencia)} y las cuotas suman `
    + `su costo financiero real [F28] neto de esa comisión, que no se cobra dos veces. `
    + `<strong>Estos precios son los tickets del modelo financiero</strong>: no se escriben aparte, se derivan de él, `
    + `así que no pueden contradecirlo. Lo que sí vigila el build es que ningún descuento deje el precio por debajo del costo.</p>`;
  return html;
}

function renderAdicionales() {
  let html = '<table><thead><tr><th>Adicional</th><th class="num">Precio</th><th>Unidad</th></tr></thead><tbody>';
  for (const a of datos.precios.adicionales) {
    html += `<tr><td>${a.concepto}</td><td class="num">${ars(a.ars)}</td><td>${a.unidad}</td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

function renderHorizonte() {
  const h = FIN.horizonte(datos);
  const filas = [
    ['Instalaciones', (a) => fmtARS.format(Math.round(a.instalaciones))],
    ['Facturación', (a) => ars(a.ingresos)],
    ['Margen bruto', (a) => ars(a.margenBruto)],
    ['Estructura fija', (a) => ars(a.fijos)],
    ['Marketing', (a) => ars(a.marketing)],
    ['Personal en planta', (a) => ars(a.empleado)],
    ['Resultado operativo', (a) => ars(a.resultadoOperativo)],
    ['Resultado neto', (a) => ars(a.resultadoNeto)],
    ['Resultado neto en euros', (a) => eur(a.resultadoNeto / TC)],
  ];
  // La variación se calcula sobre el valor crudo, no sobre el texto formateado.
  const crudo = {
    'Instalaciones': (a) => a.instalaciones, 'Facturación': (a) => a.ingresos,
    'Margen bruto': (a) => a.margenBruto, 'Estructura fija': (a) => a.fijos,
    'Marketing': (a) => a.marketing, 'Personal en planta': (a) => a.empleado,
    'Resultado operativo': (a) => a.resultadoOperativo, 'Resultado neto': (a) => a.resultadoNeto,
    'Resultado neto en euros': (a) => a.resultadoNeto,
  };
  let html = '<table><thead><tr><th>Concepto</th><th class="num">Año 2 (del modelo)</th><th class="num">Año 3 (proyectado †)</th><th class="num">Variación</th></tr></thead><tbody>';
  for (const [nombre, fn] of filas) {
    const esTotal = nombre === 'Resultado operativo' || nombre === 'Resultado neto';
    const c2 = crudo[nombre](h.anio2), c3 = crudo[nombre](h.anio3);
    const v = c2 ? `${c3 >= c2 ? '+' : ''}${nEs(((c3 / c2) - 1) * 100, 0)} %` : '—';
    html += `<tr${esTotal ? ' class="total"' : ''}><td>${nombre}</td><td class="num">${fn(h.anio2)}</td>`
      + `<td class="num">${fn(h.anio3)}</td><td class="num">${v}</td></tr>`;
  }
  html += '</tbody></table>';
  return html;
}

function renderValoracion() {
  const h = FIN.horizonte(datos);
  const d = datos.horizonte.descuento_empresa_joven;
  let html = '<table><thead><tr><th>Múltiplo sobre resultado operativo</th><th class="num">Valor bruto</th>'
    + `<th class="num">Ajustado (−${pct(d)})</th><th class="num">En euros</th><th class="num">El 30 % de un socio</th></tr></thead><tbody>`;
  const lectura = ['Extremo bajo: es donde cotiza una empresa de tres años, dependiente del fundador',
    'Punto medio del rango de mercado [F51]',
    'Extremo alto: exige cartera de mantenimiento consolidada y equipo que no dependa de una persona'];
  h.valoracion.forEach((v, i) => {
    html += `<tr${i === 0 ? ' class="subtotal"' : ''}><td><strong>× ${nEs(v.multiplo, 1)}</strong> — ${lectura[i]}</td>`
      + `<td class="num">${ars(v.bruta)}</td><td class="num">${ars(v.ajustada)}</td>`
      + `<td class="num">${eur(v.ajustada / TC)}</td><td class="num">${eur((v.ajustada * 0.30) / TC)}</td></tr>`;
  });
  html += '</tbody></table>';
  html += `<p class="leyenda">† Ejercicio de rangos, no una tasación. El descuento del ${pct(d)} recoge dos castigos reales: `
    + `la iliquidez de una pyme sin mercado comprador y la dependencia del fundador. `
    + `Se aplica sobre el resultado operativo del año 3, que es a su vez una proyección.</p>`;
  return html;
}


// La semana de Ignacio vive en src/anexos/, fuera del glob de secciones, para que
// el mismo archivo alimente esta subsección y la hoja suelta de build/semana.mjs.
function renderSemanaIgnacio() {
  const ruta = join(SRC, 'anexos', 'semana-ignacio.md');
  if (!existsSync(ruta)) return '<p><em>Hoja de la semana pendiente.</em></p>';
  return marked.parse(readFileSync(ruta, 'utf8'), { gfm: true });
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
  semana_ignacio: renderSemanaIgnacio(),
  tabla_mercado: renderMercado(),
  tabla_tarifario: renderTarifario(),
  tabla_adicionales: renderAdicionales(),
  tabla_horizonte: renderHorizonte(),
  tabla_valoracion: renderValoracion(),
  tabla_reparto_pauta: renderRepartoPauta(),
  tabla_embudo: renderEmbudo(),
  tabla_canales: renderCanales(),
  tabla_sensibilidad_cpc: renderSensibilidadCPC(),
  tabla_campanas_google: renderCampanasGoogle(),
  indice: renderIndice(leerEsquema(archivos)),
  miniaturas_web: renderMiniaturas(),
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

  // Antetítulo de parte sobre el H1 de la primera sección de cada una.
  const parte = (datos.partes ?? []).find((p) => f.startsWith(p.antes + '-'));
  if (parte) {
    const etiqueta = parte.numero ? `Parte ${parte.numero} · ${parte.titulo}` : parte.titulo;
    html = `<p class="antetitulo">${etiqueta}</p>\n${html}`;
  }

  // Anclaje invisible en cada encabezado numerado: es lo que permite localizar en
  // qué página cayó cada sección leyendo el PDF ya paginado. Va sólo en el cuerpo,
  // nunca en el índice, para que la búsqueda no se encuentre a sí misma.
  if (!f.startsWith('00')) {
    html = html.replace(/<h([12])([^>]*)>((\d+(?:\.\d+)?)\.?\s)/g,
      (m, n, attrs, literal, num) => `<h${n}${attrs}><span class="ancla" aria-hidden="true">${ANCLA(num)}</span>${literal}`);
  }

  const esPortada = f === '00-portada.md';
  contenido += `<section class="capitulo${esPortada ? ' portada' : ''}" id="sec-${f.split('-')[0]}">\n${html}\n</section>\n`;
}

// ---------- validaciones ----------
const errores = [], avisos = [];
// Un número que no se pudo calcular no puede llegar impreso al PDF. Pasó una vez:
// un renombrado dejó una clave de datos.json sin actualizar y el embudo entero salió
// en NaN sin que ninguna validación se quejara.
const nan = contenido.match(/\bNaN\b|\bInfinity\b|\bundefined\b/g);
if (nan) errores.push(`Valores sin calcular en el documento: ${nan.length} apariciones de ${[...new Set(nan)].join(', ')}`);

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

// El plan de marketing no puede gastar lo que el modelo financiero no previó.
if (datos.marketing) {
  const c = MK.cuadre(datos);
  for (const d of c.desvios) {
    errores.push(`Pauta de ${d.mes}: los canales suman ${ars(d.canales)} pero el modelo prevé ${ars(d.modelo)}`);
  }
  const p = datos.marketing.campanas_google.reduce((s, x) => s + x.pct, 0);
  if (Math.abs(p - 1) > 0.005) errores.push(`Las campañas de Google reparten el ${(p * 100).toFixed(1)}% del presupuesto, no el 100%`);
}

// Los descuentos y recargos del tarifario no pueden romper el margen.
if (datos.precios) {
  for (const p of CM.guardasPrecios(datos).problemas) errores.push(p);
}

if (avisos.length) console.warn('AVISOS:\n - ' + avisos.join('\n - '));
if (errores.length) {
  console.error('ERRORES DE VALIDACIÓN:\n - ' + errores.join('\n - '));
  process.exit(1);
}

// ---------- HTML final ----------
const template = readFileSync(join(ROOT, 'build', 'template.html'), 'utf8');
const TITULO = `${datos.meta.titulo} (v${VERSION})`;
const htmlPath = join(DIST, 'plan.html');
const pdfPath = join(DIST, `${datos.meta.slug}_v${VERSION}.pdf`);
const logoB64 = readFileSync(join(ROOT, 'build', 'assets', 'logo-header.png')).toString('base64');

const escribirHtml = (cuerpo) => {
  writeFileSync(htmlPath, template.replace('{{TITULO}}', TITULO).replace('{{CONTENIDO}}', cuerpo));
};

const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage();

async function generarPDF(cuerpo, salida) {
  escribirHtml(cuerpo);
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  await page.pdf({
    path: salida,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    margin: { top: '24mm', bottom: '16mm', left: '15mm', right: '15mm' },
    headerTemplate: `
      <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:4mm 15mm 0; display:flex; align-items:center; justify-content:space-between;">
        <img src="data:image/png;base64,${logoB64}" style="height:8mm"/>
        <span style="text-align:right;">${datos.meta.titulo} · v${VERSION}</span>
      </div>`,
    footerTemplate: `
      <div style="width:100%; font-size:7.5px; font-family:Helvetica,Arial,sans-serif; color:#5a6675; padding:0 15mm 4mm; display:flex; justify-content:space-between;">
        <span>Clima Baires · confidencial — uso interno de los socios</span>
        <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
      </div>`,
  });
}

// Primera pasada: el índice sale maquetado pero con los números en blanco.
await generarPDF(contenido, pdfPath);

// Segunda pasada: se lee el PDF ya paginado, se busca el anclaje de cada sección y
// se rellenan los huecos. El alto del índice no cambia (los huecos tienen ancho fijo),
// así que la paginación de la segunda pasada es idéntica a la de la primera.
let numerado = 0;
try {
  const { execFileSync } = await import('node:child_process');
  const texto = execFileSync('pdftotext', ['-layout', pdfPath, '-'], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  const paginas = texto.split('\f');
  const mapa = new Map();
  paginas.forEach((t, i) => {
    // A 0,6 pt pdftotext intercala espacios entre glifos («@ @ 1@ @»): se quitan todos
    // antes de buscar, que para localizar la marca da igual.
    const plano = t.replace(/\s+/g, '');
    for (const m of plano.matchAll(/@@([\d.]+)@@/g)) if (!mapa.has(m[1])) mapa.set(m[1], i + 1);
  });

  const conNumeros = contenido.replace(
    /<span class="pag-hueco" data-n="([\d.]+)">&nbsp;<\/span>/g,
    (m, n) => {
      if (!mapa.has(n)) return m;
      numerado += 1;
      return `<span class="pag-hueco" data-n="${n}">${mapa.get(n)}</span>`;
    });

  const huecos = (contenido.match(/pag-hueco/g) ?? []).length;
  if (numerado < huecos) console.warn(`AVISO: ${huecos - numerado} entradas del índice quedaron sin número de página.`);
  if (numerado > 0) await generarPDF(conNumeros, pdfPath);
} catch (e) {
  // Un número de página no vale romper el entregable: se emite el PDF sin ellos.
  console.warn(`AVISO: no se pudo paginar el índice (${e.message.split('\n')[0]}); sale sin números.`);
}

await browser.close();

console.log(`OK  ${pdfPath}`);
console.log(`    versión ${VERSION} · TC ${fmtARS.format(TC)} ARS/EUR (${datos.cambio.fecha}) · ${archivos.length} secciones · ${fuentes.length} fuentes · ${numerado} entradas de índice paginadas`);
