# 6. Modelo financiero — 24 meses

La sección 5 cierra cuánto cuesta arrancar. Esta responde las tres preguntas que siguen: **cuánto deja cada instalación**, **cuántas instalaciones hacen falta para no perder plata** y **si los {{eur:capital.total_eur}} alcanzan para llegar a diciembre sin quedarse sin caja**. Todo lo que sigue sale de un único juego de supuestos editables: la planilla `Modelo-Financiero-Clima-Baires-Argentina_v{{meta.version}}.xlsx` que acompaña a este documento recalcula estas mismas tablas con las fórmulas a la vista.

> **Convención metodológica.** {{financiero.convencion}} En Argentina los precios de venta y los de compra se indexan casi en paralelo, de modo que el margen porcentual se sostiene mientras que los valores nominales solo agregarían ruido. Las conversiones a euros usan el TC de portada (1.760 ARS/EUR) y en 6.6 se muestra qué pasa si se mueve. **Todas las cifras de esta sección son proyecciones sobre supuestos, no compromisos**: cambian los supuestos, cambian los resultados.

## 6.1 Unit economics — qué deja cada instalación

{{tabla_unit_economics}}

Tres lecturas que condicionan las decisiones del mes 1:

- **El equipo es el 57–60 % del ticket y se paga antes de cobrar el saldo.** No es un negocio de margen sobre producto: es un negocio de margen sobre servicio. Pelear dos puntos de descuento al mayorista mueve más resultado que subir el precio de venta, porque el cliente compara equipo contra MercadoLibre pero no sabe comparar instalación.
- **La instalación grande factura más pero deja proporcionalmente menos.** Un piso-techo de {{ars:financiero.mix.2.ticket_ars}} deja 19,6 % de contribución contra 25,6 % de un split de {{ars:financiero.mix.1.ticket_ars}}: la instalación de conductos consume la diferencia. Sirven para llenar la agenda de temporada baja y para reputación en countries, no para sostener el margen.
- **El mantenimiento es el margen escondido.** 54,6 % de contribución sobre un ticket chico, sin equipo que financiar y con la agenda de marzo-agosto vacía. Es la palanca natural para los meses valle y la razón para empezar a construir la base de clientes desde la primera instalación.

## 6.2 Punto de equilibrio — cuántas instalaciones hay que hacer

{{tabla_breakeven}}

En temporada alta el negocio empata con **{{_fin.be_pico}} instalaciones al mes**, y el plan proyecta 30 para diciembre: el riesgo no es no llegar al equilibrio, es no poder ejecutar lo que se venda. Pero la última fila es la que hay que tener presente todo el año: **con un técnico en relación de dependencia el equilibrio salta a {{_fin.be_empleado}} instalaciones/mes**, y el modelo proyecta 4 instalaciones en los meses de invierno. Contratar en planta con la estacionalidad de este negocio significa pagar sueldo en junio con la facturación de junio, y no da. De ahí la decisión de la sección 10: subcontratar hasta que la base de mantenimiento sostenga el valle.

## 6.3 Estado de resultados proyectado

{{tabla_pyl}}

La estacionalidad manda: **entre noviembre y febrero se hace el {{_fin.peso_temporada}} % de la facturación del año**. Diciembre y enero solos aportan más resultado operativo que los siete meses de marzo a septiembre juntos. Esto tiene una consecuencia de gestión que no es obvia: los errores de diciembre no se corrigen en enero, se pagan doce meses. Todo lo que dependa de estar listo —stock comprometido con el mayorista, cuadrillas reservadas, campañas cargadas, la web indexada— tiene que estar cerrado en noviembre, no en diciembre.

## 6.4 Flujo de caja — el mes que hay que sobrevivir

{{tabla_caja}}

**El mínimo de caja es {{ars:_fin.caja_minima}} ({{eur:_fin.caja_minima_eur}}) y ocurre en el primer mes**, no en el pico: septiembre paga la constitución, la marca, la identidad y el equipamiento mientras factura cinco instalaciones. A partir de octubre el negocio se autofinancia. La estructura que lo hace posible es la política de cobro:

- **Seña del 50 % al firmar, saldo al terminar.** La seña de una instalación tipo ({{ars:_fin.sena_obra_tipo}}) cubre el equipo antes de pedirlo al mayorista. Sin esa seña el capital de trabajo pasa a financiar equipos que todavía no son de nadie.
- **El mayorista cobra contado hasta que haya historial.** Los primeros 60-90 días no hay cuenta corriente. Conseguirla en octubre —con tres meses de compras cumplidas— es el objetivo comercial más rentable del trimestre y no cuesta un euro.
- **El salto de septiembre del año 2** es el pago de Ganancias del primer ejercicio. Está previsto y la caja lo absorbe, pero es la razón para no repartir dividendos antes de esa fecha.

### Sensibilidad a la seña

{{tabla_sena}}

## 6.5 Escenarios

{{tabla_escenarios}}

Tres conclusiones de comité:

1. **El aporte se recupera dentro del primer verano incluso en el caso conservador.** Con un 35 % menos de instalaciones y un 10 % menos de ticket, el negocio sigue devolviendo los {{eur:capital.total_eur}} y cerrando el año en positivo. Es el escenario sobre el que hay que tomar las decisiones de caja; el base es sobre el que hay que tomar las decisiones de capacidad.
2. **Crecer más rápido no mejora la caja mínima: la empeora.** El escenario optimista tiene una caja mínima *inferior* a la del base, porque cada instalación adicional compra su equipo antes de cobrar el saldo. Es la paradoja clásica de morir de éxito, y acá aparece con números: si en noviembre la demanda supera lo previsto, la restricción no será la agenda sino el efectivo para comprar equipos. La contramedida está identificada y es gratuita: cuenta corriente con el mayorista negociada en octubre.
3. **La diferencia entre conservador y optimista es de {{eur:_fin.brecha_escenarios_eur}} de resultado en el año 1**, y depende casi enteramente de cuántos leads convierta la máquina de captación. Con el histórico de más de € 16.000 invertidos en Google Ads en Málaga —campañas, términos de búsqueda, creatividades y curvas de conversión ya aprendidas— Clima Baires arranca esa curva con ventaja sobre cualquier competidor local que empiece de cero.

## 6.6 Sensibilidad cambiaria y límites del modelo

El modelo trabaja en pesos constantes, así que el tipo de cambio no afecta a la operación argentina: afecta a **cuánto vale el resultado para los socios en España**. El resultado neto del año 1 ({{ars:_fin.neto_a1}}) equivale a {{eur:_fin.neto_a1_eur}} al TC de portada, a {{eur:_fin.neto_a1_eur_tc_bajo}} si el peso se aprecia a 1.500 ARS/EUR y a {{eur:_fin.neto_a1_eur_tc_alto}} si se deprecia a 2.100. Ninguno de los tres cambia una sola decisión operativa del plan; los tres cambian la conversación sobre dividendos.

Cuatro límites que conviene tener explícitos antes de usar estos números para decidir:

- **La curva de instalaciones es el supuesto más frágil de todo el modelo.** Todo lo demás —márgenes, costos, alícuotas— está anclado en precios de mercado verificables. Cuántas instalaciones se venden el primer verano es un pronóstico, y no hay forma de verificarlo hasta hacerlo. Por eso la planilla lo pone en la primera fila editable.
- **La capacidad de Ignacio es el techo real.** El modelo asume que una persona puede vender, presupuestar, coordinar cuadrillas y facturar 30 instalaciones en diciembre. Es exigente pero factible con el stack de la sección 8; a partir de ~35 instalaciones/mes ya no lo es, y esa es la señal objetiva para incorporar apoyo comercial.
- **No hay morosidad ni instalaciones que se caen.** Con seña del 50 % y saldo contra entrega, el riesgo de incobrable es bajo, pero no es cero.
- **Se supone inflación neutral sobre el margen.** Si los equipos suben más rápido que los precios de instalación —lo que ocurre cuando el dólar se mueve de golpe—, el margen bruto se comprime hasta que se ajuste la lista.

## 6.7 Qué hacer con esto

| Decisión | Regla que sale del modelo |
|---|---|
| **Política de cobro** | Seña del 50 % innegociable en instalación con provisión de equipo. Sin seña no se pide el equipo. |
| **Cuenta corriente con el mayorista** | Objetivo de octubre, antes del pico. Es la única palanca gratuita contra el riesgo de caja de diciembre. |
| **Primera contratación** | No antes de que la base de mantenimiento cubra {{_fin.be_empleado}} instalaciones-equivalente en el mes valle. Hasta entonces, subcontratación. |
| **Dividendos** | No repartir antes de pagar Ganancias del primer ejercicio (mes 13). |
| **Reserva de caja** | No bajar de {{ars:_fin.piso_caja}} de saldo. Si se proyecta cruzar ese piso, se frena pauta antes que ninguna otra cosa. |
| **Revisión de supuestos** | Mensual, con el real cargado en la planilla. El modelo sirve mientras se lo compare con lo que pasó. |

> **Cómo se regenera**: `npm run modelo` reconstruye la planilla desde `src/datos.json`; `npm run build` reconstruye este PDF con las mismas cifras. Los dos leen el mismo motor de cálculo (`build/financiero.mjs`), de modo que documento y planilla no pueden divergir. Detalle en 13.5.
