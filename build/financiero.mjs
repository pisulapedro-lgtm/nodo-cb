/**
 * Motor de cálculo financiero — Clima Baires Argentina.
 *
 * Fuente única de supuestos: src/datos.json → clave `financiero`.
 * Lo consumen el build del PDF (build/build.mjs) y el generador de la planilla
 * (build/modelo-excel.py, vía `node build/financiero.mjs --json`), de modo que
 * el documento y el Excel no puedan divergir.
 *
 * Convención: ARS constantes de agosto-2026 (ver `financiero.convencion`).
 * Funciones puras: no leen archivos ni imprimen — reciben `datos` y devuelven objetos.
 */

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

/** Etiqueta «sep-26» para el índice i contando desde financiero.mes_inicio. */
export function etiquetaMes(fin, i) {
  const [a0, m0] = fin.mes_inicio.split('-').map(Number);
  const total = (m0 - 1) + i;
  const anio = a0 + Math.floor(total / 12);
  return `${MESES[total % 12]}-${String(anio).slice(2)}`;
}

/** Desembolsos de una sola vez del presupuesto (bloques A y B) llevados a ARS. */
export function puestaEnMarcha(datos) {
  const bloques = datos.financiero.puesta_en_marcha.bloques;
  const eur = datos.presupuesto.partidas
    .filter((p) => bloques.includes(p.bloque.trim()[0]))
    .reduce((s, p) => s + p.eur, 0);
  return { eur, ars: eur * datos.cambio.eur_ars };
}

/** Desglose de una instalación por categoría del mix + el promedio ponderado (blended). */
export function unitEconomics(datos) {
  const fin = datos.financiero;
  const c = fin.costos_instalacion;

  const filas = fin.mix.map((m) => {
    const costoEquipo = m.ticket_ars * m.costo_equipo_pct;
    const montaje = m.montaje_ars;
    const materiales = m.materiales_ars;
    const margenBruto = m.ticket_ars - costoEquipo - montaje - materiales;
    const comision = m.ticket_ars * c.comision_cobro_pct;
    const iibb = m.ticket_ars * c.iibb_pct;
    const contribucion = margenBruto - comision - iibb;
    return {
      ...m, costoEquipo, montaje, materiales, margenBruto, comision, iibb, contribucion,
      margenBrutoPct: margenBruto / m.ticket_ars,
      contribucionPct: contribucion / m.ticket_ars,
    };
  });

  const pond = (campo) => filas.reduce((s, f) => s + f[campo] * f.peso, 0);
  const blended = {
    tipo: 'Promedio ponderado (instalación tipo)',
    peso: filas.reduce((s, f) => s + f.peso, 0),
    ticket_ars: pond('ticket_ars'),
    costoEquipo: pond('costoEquipo'),
    montaje: pond('montaje'),
    materiales: pond('materiales'),
    margenBruto: pond('margenBruto'),
    comision: pond('comision'),
    iibb: pond('iibb'),
    contribucion: pond('contribucion'),
  };
  blended.margenBrutoPct = blended.margenBruto / blended.ticket_ars;
  blended.contribucionPct = blended.contribucion / blended.ticket_ars;
  blended.contribucionNeta = blended.contribucion - c.cac_ars; // tras adquirir el cliente

  return { filas, blended };
}

/** Estado de resultados mes a mes (24 meses). */
export function proyeccion24m(datos, escenario = { instalaciones_mult: 1, ticket_mult: 1 }) {
  const fin = datos.financiero;
  const { blended } = unitEconomics(datos);
  const fijosMes = fin.fijos_mensuales_ars.reduce((s, f) => s + f.ars, 0);

  const meses = [];
  for (let i = 0; i < fin.meses; i++) {
    const instalaciones = fin.instalaciones_mes[i] * escenario.instalaciones_mult;
    const ticket = blended.ticket_ars * escenario.ticket_mult;
    const ingresos = instalaciones * ticket;

    // Los costos variables escalan con el ticket salvo instalación y materiales,
    // que son costos físicos por instalación y no se mueven con el precio de venta.
    const costoEquipo = instalaciones * blended.costoEquipo * escenario.ticket_mult;
    const montaje = instalaciones * blended.montaje;
    const materiales = instalaciones * blended.materiales;
    const margenBruto = ingresos - costoEquipo - montaje - materiales;

    const comision = ingresos * fin.costos_instalacion.comision_cobro_pct;
    const iibb = ingresos * fin.costos_instalacion.iibb_pct;
    const marketing = fin.marketing_ars[i];
    const empleado = i >= fin.empleado.mes_alta_indice ? fin.empleado.costo_empleador_ars : 0;

    const resultadoOperativo = margenBruto - comision - iibb - fijosMes - marketing - empleado;
    meses.push({
      i, etiqueta: etiquetaMes(fin, i), instalaciones, ingresos,
      costoEquipo, montaje, materiales, margenBruto,
      comision, iibb, fijos: fijosMes, marketing, empleado, resultadoOperativo,
    });
  }

  // Ganancias se devenga por año fiscal del modelo (12 meses corridos desde el inicio).
  const anios = [0, 1].map((a) => {
    const tramo = meses.slice(a * 12, a * 12 + 12);
    const resultado = tramo.reduce((s, m) => s + m.resultadoOperativo, 0);
    const impuesto = ganancias(datos, resultado);
    return {
      anio: a + 1,
      ingresos: tramo.reduce((s, m) => s + m.ingresos, 0),
      instalaciones: tramo.reduce((s, m) => s + m.instalaciones, 0),
      margenBruto: tramo.reduce((s, m) => s + m.margenBruto, 0),
      fijos: tramo.reduce((s, m) => s + m.fijos, 0),
      marketing: tramo.reduce((s, m) => s + m.marketing, 0),
      empleado: tramo.reduce((s, m) => s + m.empleado, 0),
      resultadoOperativo: resultado,
      impuesto,
      resultadoNeto: resultado - impuesto,
    };
  });

  return { meses, anios };
}

/**
 * Impuesto a las ganancias por la escala progresiva del art. 73 LIG.
 * A los resultados del modelo les alcanza el primer tramo, pero la escala se
 * aplica igual: si un socio sube los supuestos en la planilla, el impuesto
 * tiene que subir con ellos y no quedarse clavado en el 25 %.
 */
export function ganancias(datos, resultado) {
  if (resultado <= 0) return 0;
  const imp = datos.financiero.impuestos;
  const [t1, t2] = [imp.ganancias_tramo1_ars, imp.ganancias_tramo2_ars];
  const [a1, a2, a3] = imp.ganancias_escala_pct;
  if (resultado <= t1) return resultado * a1;
  if (resultado <= t2) return t1 * a1 + (resultado - t1) * a2;
  return t1 * a1 + (t2 - t1) * a2 + (resultado - t2) * a3;
}

/**
 * Flujo de caja mensual. El descalce real del negocio:
 * el cliente paga una seña al firmar y el saldo al terminar (mes siguiente si la
 * instalación cae a fin de mes), mientras el mayorista cobra contado hasta que haya historial.
 */
export function flujoCaja(datos, escenario = { instalaciones_mult: 1, ticket_mult: 1 }) {
  const fin = datos.financiero;
  const { meses } = proyeccion24m(datos, escenario);
  const sena = fin.cobros.sena_pct;
  const difSaldo = fin.cobros.dias_saldo / 30; // fracción del saldo que se cobra el mes siguiente

  const arranque = puestaEnMarcha(datos).ars;

  let saldo = datos.capital.total_ars;
  const filas = [];
  let minimo = { saldo: Infinity, etiqueta: '' };
  let chequeAcumulado = 0; // computable como pago a cuenta de Ganancias (MiPyME)

  for (let i = 0; i < meses.length; i++) {
    const m = meses[i];
    const ant = meses[i - 1];

    // Cobros: seña de las instalaciones del mes + saldo (parte este mes, parte el siguiente).
    const cobroSena = m.ingresos * sena;
    const cobroSaldoMes = m.ingresos * (1 - sena) * (1 - difSaldo);
    const cobroSaldoAnterior = ant ? ant.ingresos * (1 - sena) * difSaldo : 0;
    const cobros = cobroSena + cobroSaldoMes + cobroSaldoAnterior;

    // Pagos: el equipo se paga al pedirlo (mismo mes que la instalación), el resto también.
    const operativos = m.costoEquipo + m.montaje + m.materiales + m.comision + m.iibb
      + m.fijos + m.marketing + m.empleado;
    // Los desembolsos de una sola vez del presupuesto (constitución, marca, identidad,
    // equipamiento) salen de la caja en el primer mes: es plata que ya no está.
    const puestaMarcha = i === 0 ? arranque : 0;
    const pagos = operativos + puestaMarcha;
    const impCheque = (cobros + pagos) * fin.impuestos.imp_cheque_pct * 0.5; // 0,6 % entrada + 0,6 % salida
    chequeAcumulado += impCheque * fin.impuestos.imp_cheque_computable_pct;

    // Ganancias se paga en el mes 13 y 25 del modelo (simplificación: al cierre del año fiscal),
    // neto del impuesto al cheque acumulado, que como MiPyME es pago a cuenta.
    let impuestoGanancias = 0;
    if (i === 12 || i === 23) {
      const a = i === 12 ? 0 : 1;
      const tramo = meses.slice(a * 12, a * 12 + 12);
      const bruto = ganancias(datos, tramo.reduce((s, x) => s + x.resultadoOperativo, 0));
      const credito = Math.min(bruto, chequeAcumulado);
      impuestoGanancias = bruto - credito;
      chequeAcumulado -= credito;
    }

    const neto = cobros - pagos - impCheque - impuestoGanancias;
    const inicial = saldo;
    saldo += neto;
    if (saldo < minimo.saldo) minimo = { saldo, etiqueta: m.etiqueta, i };

    filas.push({
      i, etiqueta: m.etiqueta, inicial, cobros, operativos, puestaMarcha, pagos,
      impCheque, impuestoGanancias, neto, final: saldo,
    });
  }

  return { filas, minimo, saldoFinal: saldo, arranque };
}

/**
 * Caja mínima según la seña que se consiga cobrar. Es la sensibilidad que más
 * importa: la seña es lo que financia la compra del equipo al mayorista.
 */
export function sensibilidadSena(datos) {
  return datos.financiero.cobros.sena_sensibilidad.map((s) => {
    const clon = { ...datos, financiero: { ...datos.financiero, cobros: { ...datos.financiero.cobros, sena_pct: s } } };
    const caja = flujoCaja(clon);
    return { sena: s, minimo: caja.minimo.saldo, mes: caja.minimo.etiqueta, final: caja.saldoFinal };
  });
}

/** Instalaciones/mes necesarias para cubrir los costos de estructura. */
export function breakEven(datos) {
  const fin = datos.financiero;
  const { blended } = unitEconomics(datos);
  const fijos = fin.fijos_mensuales_ars.reduce((s, f) => s + f.ars, 0);
  const marketingTemporada = Math.max(...fin.marketing_ars.slice(0, 12));
  const marketingValle = Math.min(...fin.marketing_ars.slice(0, 12));

  return {
    contribucionPorInstalacion: blended.contribucion,
    contribucionNetaPorInstalacion: blended.contribucion - fin.costos_instalacion.cac_ars,
    fijos,
    soloFijos: fijos / blended.contribucion,
    conMarketingValle: (fijos + marketingValle) / (blended.contribucion - fin.costos_instalacion.cac_ars),
    conMarketingPico: (fijos + marketingTemporada) / (blended.contribucion - fin.costos_instalacion.cac_ars),
    conEmpleado: (fijos + marketingTemporada + fin.empleado.costo_empleador_ars) / (blended.contribucion - fin.costos_instalacion.cac_ars),
    facturacionEquilibrioMes: (fijos / blended.contribucionPct),
  };
}

/** Los tres escenarios con sus métricas de decisión. */
export function escenarios(datos) {
  const fin = datos.financiero;
  const TC = datos.cambio.eur_ars;

  return fin.escenarios.map((e) => {
    const { anios } = proyeccion24m(datos, e);
    const caja = flujoCaja(datos, e);
    const a1 = anios[0], a2 = anios[1];

    // Payback: primer mes en que la caja acumulada supera el capital aportado.
    const payback = caja.filas.findIndex((f) => f.final >= datos.capital.total_ars);

    return {
      nombre: e.nombre,
      instalacionesAnio1: a1.instalaciones,
      ingresosAnio1: a1.ingresos,
      resultadoNetoAnio1: a1.resultadoNeto,
      resultadoNetoAnio1Eur: a1.resultadoNeto / TC,
      resultadoNetoAnio2: a2.resultadoNeto,
      cajaMinima: caja.minimo.saldo,
      cajaMinimaMes: caja.minimo.etiqueta,
      cajaFinal: caja.saldoFinal,
      paybackMeses: payback >= 0 ? payback + 1 : null,
      paybackEtiqueta: payback >= 0 ? caja.filas[payback].etiqueta : 'no alcanza en 24 meses',
    };
  });
}

/** Volcado completo para el generador de Excel (`node build/financiero.mjs --json`). */
export function resumen(datos) {
  return {
    unitEconomics: unitEconomics(datos),
    proyeccion: proyeccion24m(datos),
    caja: flujoCaja(datos),
    breakEven: breakEven(datos),
    escenarios: escenarios(datos),
    sensibilidadSena: sensibilidadSena(datos),
    puestaEnMarcha: puestaEnMarcha(datos),
  };
}

// CLI: emite el caso base en JSON para que Python lo consuma sin reimplementar nada.
if (process.argv[1] && process.argv[1].endsWith('financiero.mjs')) {
  const { readFileSync } = await import('node:fs');
  const { dirname, join, resolve } = await import('node:path');
  const { fileURLToPath } = await import('node:url');
  const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  const datos = JSON.parse(readFileSync(join(ROOT, 'src', 'datos.json'), 'utf8'));
  console.log(JSON.stringify(resumen(datos), null, 2));
}
