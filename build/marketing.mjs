/**
 * Motor de cálculo del plan de marketing — Clima Baires Argentina.
 *
 * Fuente única de supuestos: src/datos.json → claves `marketing` y `financiero`.
 * El reparto de pauta por canal **tiene que sumar** la serie `financiero.marketing_ars`
 * del modelo financiero: si no cuadra, el build aborta. Es la misma disciplina que
 * mantiene alineados el PDF y la planilla, aplicada al presupuesto publicitario.
 *
 * Funciones puras: reciben `datos` y devuelven objetos.
 */

import { etiquetaMes } from './financiero.mjs';

/** Comprueba que la pauta por canal reproduce exactamente el presupuesto del modelo. */
export function cuadre(datos) {
  const fin = datos.financiero, mk = datos.marketing;
  const meses = mk.canales[0].ars.length;
  const desvios = [];
  for (let i = 0; i < meses; i++) {
    const suma = mk.canales.reduce((s, c) => s + c.ars[i], 0);
    if (suma !== fin.marketing_ars[i]) {
      desvios.push({ mes: etiquetaMes(fin, i), canales: suma, modelo: fin.marketing_ars[i] });
    }
  }
  return { ok: desvios.length === 0, desvios, meses };
}

/**
 * Embudo mes a mes: de pesos de pauta a instalaciones cerradas.
 *
 * La cadena de Search es clic → conversación → instalación; la de Meta arranca en el lead
 * (el formulario nativo se paga por lead, no por clic). Lo que la pauta no alcanza a
 * cubrir tiene que salir de los canales propios, y ese hueco es el dato de gestión:
 * dice cuánto depende el plan del SEO, del perfil de Google y de las reseñas.
 */
export function embudo(datos, cpcMult = 1) {
  const fin = datos.financiero, mk = datos.marketing, e = mk.embudo;
  const canal = (c) => mk.canales.find((x) => x.clave === c);
  const g = canal('google').ars, m = canal('meta').ars;
  const meses = [];

  for (let i = 0; i < g.length; i++) {
    const cpc = mk.cpc_ars[i] * cpcMult;
    const clics = g[i] / cpc;
    const leadsGoogle = clics * e.conv_clic_lead;
    const instalacionesGoogle = leadsGoogle * e.conv_lead_instalacion_google;

    const leadsMeta = m[i] / (e.cpl_meta_ars * cpcMult);
    const instalacionesMeta = leadsMeta * e.conv_lead_instalacion_meta;

    const plan = fin.instalaciones_mes[i];
    const pagas = instalacionesGoogle + instalacionesMeta;
    meses.push({
      i, etiqueta: etiquetaMes(fin, i), cpc,
      inversionGoogle: g[i], clics, leadsGoogle, instalacionesGoogle,
      inversionMeta: m[i], leadsMeta, instalacionesMeta,
      leads: leadsGoogle + leadsMeta,
      plan, pagas, propias: plan - pagas,
      cubiertoPct: plan > 0 ? pagas / plan : 0,
    });
  }

  const a1 = meses.slice(0, 12);
  const sum = (f) => a1.reduce((s, x) => s + f(x), 0);
  const inversion = sum((x) => x.inversionGoogle) + sum((x) => x.inversionMeta);
  const totales = {
    inversion,
    inversionTotal: fin.marketing_ars.slice(0, 12).reduce((s, x) => s + x, 0),
    leads: sum((x) => x.leads),
    instalacionesPagas: sum((x) => x.pagas),
    instalacionesPlan: sum((x) => x.plan),
    instalacionesPropias: sum((x) => x.plan - x.pagas),
    cpl: inversion / sum((x) => x.leads),
    cac: inversion / sum((x) => x.pagas),
    cacSobrePlan: fin.marketing_ars.slice(0, 12).reduce((s, x) => s + x, 0) / sum((x) => x.plan),
  };
  totales.cubiertoPct = totales.instalacionesPagas / totales.instalacionesPlan;

  return { meses, totales };
}

/** Coste por canal, para decidir dónde poner el peso. */
export function porCanal(datos) {
  const { meses } = embudo(datos);
  const a1 = meses.slice(0, 12);
  const sum = (f) => a1.reduce((s, x) => s + f(x), 0);
  const e = datos.marketing.embudo;

  const g = { nombre: 'Google Search', inversion: sum((x) => x.inversionGoogle), leads: sum((x) => x.leadsGoogle), instalaciones: sum((x) => x.instalacionesGoogle) };
  const m = { nombre: 'Meta (IG y FB)', inversion: sum((x) => x.inversionMeta), leads: sum((x) => x.leadsMeta), instalaciones: sum((x) => x.instalacionesMeta) };
  const c = datos.marketing.canales.find((x) => x.clave === 'countries');
  const co = { nombre: 'Medios de countries', inversion: c.ars.slice(0, 12).reduce((s, x) => s + x, 0), leads: null, instalaciones: null };

  for (const f of [g, m]) {
    f.cpl = f.inversion / f.leads;
    f.cac = f.inversion / f.instalaciones;
    f.convLeadInstalacion = f.instalaciones / f.leads;
  }
  return [g, m, co];
}

/** Qué pasa si el clic sale más caro de lo previsto. */
export function sensibilidad(datos) {
  return datos.marketing.sensibilidad_cpc.map((mult) => {
    const { totales } = embudo(datos, mult);
    return {
      mult,
      cpl: totales.cpl,
      cac: totales.cac,
      instalacionesPagas: totales.instalacionesPagas,
      cubiertoPct: totales.cubiertoPct,
      instalacionesPropias: totales.instalacionesPropias,
    };
  });
}

/** Volcado para inspección rápida: `node build/marketing.mjs`. */
if (process.argv[1] && process.argv[1].endsWith('marketing.mjs')) {
  const { readFileSync } = await import('node:fs');
  const { dirname, join, resolve } = await import('node:path');
  const { fileURLToPath } = await import('node:url');
  const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  const datos = JSON.parse(readFileSync(join(ROOT, 'src', 'datos.json'), 'utf8'));
  console.log(JSON.stringify({ cuadre: cuadre(datos), embudo: embudo(datos), porCanal: porCanal(datos), sensibilidad: sensibilidad(datos) }, null, 2));
}
