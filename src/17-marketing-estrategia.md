# 17. Estrategia de marketing y embudo

La sección 9 fija **dónde** competir. Esta fija **con qué plata, en qué canal y con qué números**, y las dos siguientes bajan a las campañas concretas.

El presupuesto no se decide acá: sale del modelo financiero de la sección 6, que reserva **{{ars:_mk.inversion_total}} ({{eur:_mk.inversion_total_eur}}) para el año 1**. Todo lo que sigue se reparte dentro de esa cifra. El build del documento aborta si el reparto por canal deja de cuadrar con el modelo — no hay pauta que se escape del presupuesto.

## 17.1 El posicionamiento en una frase

> **El único proveedor del corredor norte que te dice el precio final antes de empezar, entra a tu country con los papeles al día y sigue atendiendo el teléfono después de cobrar.**

Las tres partes de esa frase no son adornos: cada una ataca un motivo real por el que la gente desconfía del rubro.

| Lo que ataca | El dolor concreto | Cómo se demuestra |
|---|---|---|
| **Precio cerrado** | El adicional que aparece a mitad de obra | Presupuesto escrito con equipo, materiales, instalación e IVA desglosados. Calculadora pública en la web |
| **Acceso a countries** | El instalador que se queda en la barrera por un seguro vencido | Seguros AP y RC con cláusula de no repetición, alta de proveedor previa, personal identificado |
| **Posventa real** | El «te llamo mañana» que no llega nunca | Garantía escrita, checklist firmado en obra y WhatsApp que responde en horario |

Lo que **no** somos: los más baratos. Competir por precio contra el instalador informal es una pelea perdida —él no paga IVA, ni cargas, ni seguros— y además destruye el margen que sostiene la posventa. Cuando entra un lead que solo pregunta precio y no valora nada más, se le pasa el presupuesto y se lo deja ir sin regatear.

## 17.2 A quién le hablamos

Cuatro segmentos, muy distinto valor y muy distinto costo de captación:

| Segmento | Ticket típico | Cómo llega | Peso en el plan |
|---|---|---|---|
| **Residencial premium** (casa o depto propio, 35-65 años, Núñez a San Isidro) | {{ars:financiero.mix.0.ticket_ars}} – {{ars:financiero.mix.1.ticket_ars}} | Google Search, sobre todo. Busca cuando aprieta el calor | El volumen: 8 de cada 10 obras |
| **Countries y barrios cerrados** (Nordelta, Tigre, Pilar) | Hasta {{ars:financiero.mix.2.ticket_ars}} | Recomendación, administración del barrio, medios barriales | El margen y la reputación |
| **Administraciones, arquitectos y desarrolladores** | Obra repetida | LinkedIn, presentación directa, dossier | El canal que estabiliza el invierno |
| **Service y mantenimiento** | {{ars:financiero.mix.3.ticket_ars}} | Base propia de clientes + búsqueda de urgencia | 55 % de margen y la puerta de entrada al recambio |

El cuarto segmento merece más atención de la que suele recibir: es el único que **no depende del verano**. Cada instalación que se hace en diciembre es un cliente de mantenimiento en marzo, y esa base es lo que separa a una empresa de un instalador con temporada alta.

## 17.3 El embudo, con números

De pesos de pauta a obras cerradas, mes a mes:

{{tabla_embudo}}

Tres lecturas que cambian decisiones:

- **La pauta sola no gana diciembre.** En el pico cubre menos de la mitad del plan. No es un error de presupuesto: es que en diciembre y enero el clic se encarece justo cuando todos lo quieren. **Las {{_mk.obras_propias}} obras que la pauta no paga tienen que venir de canales propios** —posicionamiento en Google, el perfil de empresa, las reseñas y la recomendación—, y esos canales tardan tres meses en madurar. De ahí el plazo que fija la sección 9: top 3 del bloque de mapas **antes del 30 de noviembre**. No es una meta de vanidad; es el 55 % de la facturación del pico.
- **En invierno sobra pauta y falta demanda.** De mayo a agosto el presupuesto compra más consultas de las que el plan necesita vender. La respuesta no es apagar la pauta —perder visibilidad cuesta más recuperarla que mantenerla— sino **cambiarle el objetivo**: en el valle, la inversión se corre a mantenimiento y service, que es el negocio que sí existe en julio.
- **El CAC real queda por debajo del que asume el modelo.** {{ars:_mk.cac}} contra los {{ars:financiero.costos_obra.cac_ars}} que descuenta el punto de equilibrio de la sección 6. Ese colchón es la tolerancia: hasta {{ars:financiero.costos_obra.cac_ars}} por obra el negocio sigue cerrando como está proyectado.

## 17.4 Reparto de la inversión

{{tabla_reparto_pauta}}

Y lo que rinde cada canal en el año:

{{tabla_canales}}

**Google se lleva {{_mk.pct_google}} % del presupuesto medible y produce {{_mk.pct_obras_google}} % de las obras de pauta.** Es la consecuencia de un hecho simple: quien busca «instalación aire acondicionado San Isidro» ya decidió que quiere uno; quien ve un reel todavía no. Meta cuesta menos por lead y bastante más por obra — sirve para llenar el embudo y construir marca, no para cerrar la temporada.

Los medios de countries son el gasto que no se puede medir con un CPL y hay que sostener igual: {{ars:_mk.inversion_countries}} en el año compran presencia en el canal de mayor ticket del negocio, donde la decisión se toma por confianza y no por buscador.

## 17.5 Qué pasa si el clic sale más caro

{{tabla_sensibilidad_cpc}}

Es la sensibilidad que importa, porque el CPC es el precio que no controlamos. La regla que sale de esta tabla: **si en dos meses seguidos el CPL supera {{ars:_mk.cpl_techo}}, no se sube el presupuesto — se corta el canal más caro y se traslada a mantenimiento y contenido**. Perseguir un clic que se encareció es la forma más rápida de quemar el presupuesto del pico en noviembre.

## 17.6 La regla del presupuesto

Cuatro decisiones fijadas de antemano, para no tener que improvisar en plena temporada:

1. **El presupuesto mensual es un techo, no una meta.** Si un mes no se gasta —típico en el valle, donde no hay demanda que comprar—, el remanente se acumula para noviembre y diciembre, que es cuando cada peso rinde más obras.
2. **Nada de tarjeta al exterior.** Google y Meta se configuran con facturación local en ARS: suma un 24 % con IVA recuperable, contra más de 50 % no recuperable si se paga desde fuera [F21]. Es la decisión de configuración más cara de equivocar.
3. **Ningún canal sin conversión medida.** Si un canal no puede atribuir chats o citas, no recibe presupuesto — con la excepción declarada de los medios de countries, que se justifican por acceso.
4. **El tope por obra es {{ars:financiero.costos_obra.cac_ars}}.** Por encima de eso la obra sigue dejando plata, pero se come el colchón con el que está construido el punto de equilibrio.
