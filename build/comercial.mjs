/**
 * Motor comercial — Clima Baires Argentina.
 *
 * Dos cosas que el documento prometía y no calculaba:
 *   1. El **tarifario publicable**, derivado del mismo `financiero.mix` que alimenta
 *      el modelo. El precio de lista de una categoría ES su ticket: si alguien toca
 *      uno y no el otro, `coherenciaPrecios()` lo detecta y el build aborta.
 *   2. El **dimensionamiento de mercado**, construido de abajo hacia arriba y
 *      mostrando la aritmética, para que los supuestos se discutan en vez de creerse.
 *
 * Funciones puras: reciben `datos` y devuelven objetos.
 */

/** Precio de lista, de transferencia y en cuotas para cada categoría del mix. */
export function tarifario(datos) {
  const p = datos.precios;
  const iva = p.iva_pct;
  const comisionIncluida = datos.financiero.costos_instalacion.comision_cobro_pct;

  const filas = datos.financiero.mix.map((m) => {
    const lista = m.ticket_ars; // ya lleva dentro el costo de cobrar con tarjeta
    const transferencia = lista * (1 - p.descuento_transferencia);
    // En cuotas se suma el costo financiero real con su IVA, neto de la comisión
    // que el precio de lista ya contemplaba: no se cobra dos veces lo mismo.
    const cuotas = p.cuotas.map((c) => {
      const recargo = c.tasa * (1 + iva) - comisionIncluida;
      const total = lista * (1 + recargo);
      return { cuotas: c.cuotas, tasa: c.tasa, fuente: c.fuente, total, porCuota: total / c.cuotas, recargo };
    });
    return { tipo: m.tipo, fuente: m.fuente, lista, transferencia, cuotas };
  });

  return { filas, ivaIncluido: true };
}

/**
 * Guardas del tarifario.
 *
 * El precio de lista **no puede** divergir del modelo porque se deriva de él: eso
 * está garantizado por construcción, no por una validación. Lo que sí puede romperse
 * a mano son los descuentos y los recargos, y eso es lo que se comprueba:
 *   1. Ningún precio con descuento puede quedar por debajo del costo directo.
 *   2. Pagar en cuotas no puede salir más barato que pagar en un pago.
 */
export function guardasPrecios(datos) {
  const p = datos.precios;
  const { filas } = unitEconomicsMin(datos);
  const problemas = [];

  for (const f of tarifario(datos).filas) {
    const costo = filas.find((x) => x.tipo === f.tipo).costoDirecto;
    if (f.transferencia <= costo) {
      problemas.push(`El precio de transferencia de «${f.tipo}» (${Math.round(f.transferencia)}) no cubre su costo directo (${Math.round(costo)}): el descuento del ${(p.descuento_transferencia * 100).toFixed(1)} % es demasiado alto`);
    }
    for (const c of f.cuotas) {
      if (c.recargo <= 0) {
        problemas.push(`Pagar «${f.tipo}» en ${c.cuotas} cuotas saldría más barato que en un pago: revisar la tasa o la comisión de cobro`);
      }
    }
  }
  return { ok: problemas.length === 0, problemas };
}

/** Costo directo por categoría, sin depender de financiero.mjs. */
function unitEconomicsMin(datos) {
  return {
    filas: datos.financiero.mix.map((m) => ({
      tipo: m.tipo,
      costoDirecto: m.ticket_ars * m.costo_equipo_pct + m.montaje_ars + m.materiales_ars,
    })),
  };
}

/**
 * Mercado del corredor, de abajo hacia arriba: población → hogares → parque
 * instalado → recambio anual + altas → trabajos al año → pesos.
 */
export function mercado(datos) {
  const k = datos.mercado;
  const poblacion = k.localidades.reduce((s, l) => s + l.poblacion, 0);
  const hogares = poblacion / k.personas_por_hogar;
  const hogaresConEquipo = hogares * k.penetracion_split;
  const parque = hogaresConEquipo * k.equipos_por_hogar_equipado;

  const recambioAnual = parque / k.vida_util_anios;
  const altasAnuales = hogares * k.crecimiento_penetracion_anual * k.equipos_por_hogar_equipado;
  const equiposAnuales = recambioAnual + altasAnuales;
  const trabajosAnuales = equiposAnuales / k.equipos_por_trabajo;

  const tam = trabajosAnuales * k.ticket_medio_mercado_ars;
  const sam = tam * k.sam_pct;

  // SOM: lo que el plan captura de verdad el primer año.
  const instalacionesPlan = datos.financiero.instalaciones_mes.slice(0, 12).reduce((s, x) => s + x, 0);
  return {
    poblacion, hogares, hogaresConEquipo, parque,
    recambioAnual, altasAnuales, equiposAnuales, trabajosAnuales,
    tam, sam,
    instalacionesPlan,
    trabajosPct: instalacionesPlan / trabajosAnuales,
  };
}

/** El SOM en pesos necesita el ticket del modelo, que vive en financiero.mjs. */
export function cuota(datos, facturacionAnio1) {
  const m = mercado(datos);
  return {
    ...m,
    som: facturacionAnio1,
    somSobreTam: facturacionAnio1 / m.tam,
    somSobreSam: facturacionAnio1 / m.sam,
    // Cuántas instalaciones harían falta para llegar al 2 % del mercado.
    instalacionesAl2pct: m.trabajosAnuales * 0.02,
  };
}

/** Volcado para inspección: `node build/comercial.mjs`. */
if (process.argv[1] && process.argv[1].endsWith('comercial.mjs')) {
  const { readFileSync } = await import('node:fs');
  const { dirname, join, resolve } = await import('node:path');
  const { fileURLToPath } = await import('node:url');
  const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  const datos = JSON.parse(readFileSync(join(ROOT, 'src', 'datos.json'), 'utf8'));
  const FIN = await import('./financiero.mjs');
  const a1 = FIN.proyeccion24m(datos).anios[0].ingresos;
  console.log(JSON.stringify({
    tarifario: tarifario(datos),
    coherencia: coherenciaPrecios(datos),
    mercado: cuota(datos, a1),
  }, null, 2));
}
