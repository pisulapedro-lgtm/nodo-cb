# Prompt maestro — Clima Baires

Copiar y pegar el bloque completo al inicio de una conversación nueva.

---

```
# CONTEXTO DEL PROYECTO

Soy Clima Baires, una empresa de venta e instalación de equipos de
climatización que opera en toda la Costa del Sol (provincia de Málaga,
España). Somos una empresa en activo, con instaladores propios habilitados
para manipular gases fluorados. No somos un revendedor: instalamos nosotros.

Estoy montando el canal de venta online y necesito que el conjunto funcione
de forma coordinada, no como cuatro herramientas sueltas.

## Lo que ya está resuelto

- Empresa constituida: CIF, alta censal, cuenta bancaria y gestor.
- Proveedor mayorista: alta cerrada, tarifa vigente, fotos y fichas técnicas.
- Instaladores propios habilitados.
- Marca, dominio y logo.
- Cobertura: Costa del Sol (Marbella, Estepona, Fuengirola, Torremolinos,
  Benalmádena, Mijas, Málaga capital, Vélez-Málaga y alrededores).

## Stack que ya tengo contratado

| Herramienta | Rol |
|---|---|
| Shopify | Tienda online — venta del equipo |
| Stripe | Cobros |
| Holded | Facturación, contabilidad y gestión |
| Google Calendar | Coordinación de instalaciones |

## Catálogo inicial

30-40 SKUs de los equipos que ya instalamos habitualmente:
split pared 1x1, multisplit (2x1, 3x1) y conductos/cassette.

Conductos y cassette NO se venden con un clic: requieren visita previa y
proyecto. Van con formulario de solicitud de presupuesto.

# EL MODELO DE NEGOCIO ONLINE

Decisión tomada: **por Shopify se compra exclusivamente la maquinaria.
La instalación no se vende ni se cobra dentro de Shopify.**

La instalación sigue existiendo y la seguimos haciendo nosotros, pero se
gestiona fuera de la tienda: se coordina por Google Calendar y se factura
por Holded.

## Flujo objetivo

1. El cliente compra el equipo en Shopify y paga.
2. Se genera automáticamente el cliente y la factura del equipo en Holded.
3. El cliente recibe la propuesta de instalación y se agenda la cita.
4. La cita se refleja en Google Calendar del equipo instalador.
5. La instalación se factura aparte en Holded y se cobra por Stripe.
6. Tras la instalación: certificado, alta de garantía y solicitud de reseña.

Quiero que ese recorrido se mueva al unísono, con la mínima carga manual
posible y sin que yo tenga que introducir los mismos datos dos veces.

# LO QUE NECESITO DE VOS

1. **Diseñar la arquitectura de integración** entre Shopify, Stripe, Holded
   y Google Calendar: qué sistema es la fuente de verdad de cada dato, qué
   dispara qué, y dónde vive la lógica de orquestación.

2. **Resolver las decisiones abiertas** de la sección siguiente, con una
   recomendación clara en cada una en lugar de una lista de opciones.

3. **Construir la orquestación.** Propone primero si conviene empezar con
   una herramienta de automatización sin código o directamente con un
   servicio propio, justificando la elección para una persona sola que
   necesita esto funcionando en días, no en meses.

4. **Diseñar el flujo de reserva de instalación** que el cliente ve después
   de comprar.

5. **Un plan de ejecución día a día**, con lo que hago yo y lo que
   desarrollás vos separado.

# DECISIONES ABIERTAS QUE NECESITO QUE RESUELVAS

1. **Stripe y Shopify.** Shopify Payments está impulsado por Stripe pero es
   una cuenta distinta de la mía. Necesito saber si me conviene usar Shopify
   Payments para la tienda y reservar mi cuenta Stripe para los cobros de
   instalación, o forzar mi cuenta actual como pasarela externa asumiendo la
   comisión adicional de Shopify. Verificalo, no lo asumas.

2. **Fuente de verdad del stock.** Holded tiene control de inventario y
   Shopify también. Tengo stock real en almacén además del del proveedor.
   Decidí cuál manda y en qué dirección sincroniza.

3. **Reserva de cita: autoservicio o llamada.** Con el volumen inicial quizá
   convenga que llamemos nosotros. Decime a partir de qué volumen compensa
   montar reserva automática, y qué herramienta.

4. **Capacidad de los instaladores en el calendario.** Cómo modelar
   disponibilidad real: cuántas instalaciones por día y por equipo, tiempos
   de desplazamiento entre municipios, y qué pasa en temporada alta.

5. **Qué se factura y cuándo.** Si la factura del equipo sale al comprar y
   la de la instalación al terminar, o si conviene una única factura final.

# RESTRICCIONES QUE NO SE NEGOCIAN

1. **Gases fluorados.** La normativa UE (Reglamento 2024/573) exige que los
   equipos precargados que requieren instalación certificada solo se vendan
   al usuario final si consta que la instalación la hará personal habilitado.
   Como la instalación sale de Shopify, el flujo tiene que dejar constancia
   de que el equipo va instalado por nosotros, o de que el comprador es un
   profesional habilitado. Diseñá el checkout teniendo esto en cuenta y
   señalá dónde queda registrada esa constancia.

2. **EPREL.** La venta online exige mostrar la etiqueta energética y el
   enlace a la ficha del producto en la base de datos EPREL de la UE. Ningún
   producto se publica sin su identificador.

3. **RAEE.** Retirada gratuita del equipo antiguo equivalente (recogida uno
   por uno) e información visible en la web.

4. **IVA.** El equipo va al 21%. La instalación en vivienda de más de dos
   años podría acogerse al tipo reducido del 10% si se cumplen los
   requisitos de obras de renovación. Tenelo en cuenta al separar las
   facturas, y marcá claramente que esto lo tiene que confirmar mi gestor.

5. **Facturación electrónica.** Verificá el calendario de Verifactu vigente
   y que la configuración de Holded lo cumpla.

6. **Precios con IVA incluido** en toda la parte pública de la tienda.

7. **Español e inglés.** La Costa del Sol tiene mucha población residente
   extranjera con capacidad de compra. El inglés no es opcional.

# CÓMO QUIERO QUE TRABAJES

- Recomendación concreta antes que catálogo de alternativas. Si hay que
  elegir, elegí y explicá por qué.
- Decime cuando algo que pido sea mala idea, y proponé la alternativa.
- Trabajo solo y a dedicación completa. Prioridad a lo que se puede tener
  funcionando esta semana.
- Distinguí siempre lo que necesita validación de mi gestor de lo que es
  decisión técnica.
- Lo que construyas, dejalo versionado en el repositorio con documentación.

Empezá analizando la arquitectura de integración y resolviendo las
decisiones abiertas. No escribas código hasta que acordemos el diseño.
```

---

## Notas de contexto para quien lo pegue

El repositorio contiene además:

- [`PLAN-TECNICO.md`](PLAN-TECNICO.md) — arquitectura general, comparativa de
  plataformas, sincronizador multi-proveedor y cumplimiento normativo.
- [`PLAN-SEMANA-1.md`](PLAN-SEMANA-1.md) — plan día a día del sprint de
  lanzamiento. **Nota:** se escribió asumiendo que la instalación se vendía
  dentro de Shopify. Los días 3 y 5 necesitan revisión con el modelo nuevo.
