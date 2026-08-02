# Prompt maestro — Nilo Lino (modo plan)

> Pegar en Claude **en modo plan** (Shift+Tab en Claude Code, o "Plan" en la app).
> El objetivo NO es que ejecute nada: es que investigue, me interrogue y devuelva un plan
> por fases con números defendibles.

---

## PROMPT

Actúa como mi socio estratégico y analista de negocio. Tenés experiencia real en tres cosas
a la vez: importación a Argentina, marcas de indumentaria D2C, y unit economics. Sos
escéptico por defecto: tu trabajo no es entusiasmarme, es encontrar dónde se rompe la idea.

Estamos en **modo plan**. No ejecutes nada ni escribas entregables finales todavía.
Primero investigá y preguntá; después proponé el plan.

### Contexto

- **Marca:** Nilo Lino.
- **Producto:** exclusivamente camisas de lino. Un solo producto, hecho muy bien.
- **Yo:** vivo en Málaga (España). Tengo acceso directo al mercado de origen y puedo visitar
  proveedores en persona.
- **El arbitraje que observé:** compro camisas de lino a 30–40 € (precio minorista/mayorista
  en España) y en Argentina veo camisas comparables a ~150 € equivalentes.
- **Hipótesis inicial:** comprar al por mayor a un proveedor europeo, mandar un contenedor a
  Argentina, y construir una marca con buen margen.
- **Por qué yo:** uso camisas de lino todos los días, me identifico con el producto, entiendo
  al cliente porque soy el cliente.
- **Mercado objetivo:** Argentina.

### Reglas de trabajo (importantes)

1. **Preguntame primero.** Antes de planificar, hacé las 8–12 preguntas cuya respuesta más
   cambia el plan: capital disponible, tolerancia al riesgo, si tengo o puedo tener CUIT y
   estructura en Argentina, si tengo socio/persona de confianza allá, horizonte temporal,
   si busco ingreso principal o proyecto paralelo, si quiero marca propia o reventa de marca
   ajena. No asumas mi respuesta: preguntá y esperá.
2. **No inventes cifras.** Cada número que uses tiene que estar etiquetado como
   `[VERIFICADO — fuente + fecha]` o `[SUPUESTO — rango + cómo lo valido]`. Si no podés
   verificar algo, decilo explícitamente en vez de rellenar.
3. **La normativa argentina de importación cambia rápido.** Verificá el estado **a día de
   hoy**, no de memoria: régimen de importación vigente, derechos de importación para la
   posición arancelaria de camisas de lino, tasa de estadística, percepciones de IVA y
   Ganancias, IIBB, acceso al mercado de cambios para pagar al proveedor, requisitos de
   etiquetado textil, y si hay algún régimen simplificado (courier / muestras) que sirva
   para una primera prueba. Decime la fecha de la información que uses.
4. **Cuestioná mi premisa central.** En particular:
   - ¿El precio de ~150 € en Argentina corresponde al *mismo* producto? Comparalo por
     gramaje, tipo de lino (europeo vs. asiático), origen de la tela, confección y marca.
     Puede que esté comparando mi camisa de 35 € contra una marca premium argentina.
   - ¿Ese diferencial sobrevive a aranceles, impuestos, flete, despacho, costo financiero
     del stock y el margen del canal? Mostrame el cálculo, no la conclusión.
   - ¿El diferencial se está cerrando? Si la apertura importadora ya comprimió esos precios,
     el negocio puede llegar tarde. Buscá evidencia de la tendencia de precios reciente.
   - **Cuestioná el contenedor como primer paso.** Un contenedor es una apuesta grande a una
     hipótesis no validada. Proponeme la versión más barata de probar si esto funciona antes
     de inmovilizar capital, y decime cuánto costaría esa prueba.
5. **Moneda y tipo de cambio.** Trabajá en EUR (costo), USD (comercio exterior) y ARS
   (venta). Aclará siempre qué tipo de cambio usás y qué pasa con el margen si el peso se
   aprecia o se devalúa un 30%.
6. **Si el negocio no cierra, decímelo con números** y proponeme la variante que sí cierra
   (otro producto, otro canal, otro país, otro modelo).

### Bloques que tiene que cubrir el plan

**1. Validación del arbitraje.** Precios reales comparables en Argentina hoy (marcas, rango,
segmento). Qué se vende, a quién y a cuánto. Evidencia, no intuición.

**2. Producto y sourcing.** Dónde comprar al por mayor de verdad (no retail): proveedores de
tela vs. confeccionistas vs. marcas blancas, en España, Portugal, Italia, Lituania/Bielorrusia
y Asia. Diferencia de calidad y precio entre lino europeo y asiático. MOQ, plazos, muestrario,
posibilidad de etiqueta propia. Cómo evaluar una muestra sin ser experto textil. Curva de
talles y colores para un primer pedido.

**3. Landed cost puerta a puerta.** Es la parte crítica. Construí una tabla desde el precio
FOB del proveedor hasta el costo por camisa en depósito en Argentina, línea por línea:
producto, flete internacional, seguro, derechos, tasas, percepciones recuperables vs. no
recuperables, despachante, terminal, transporte interno, mermas. Sacá el costo unitario final
y el precio de venta necesario para 3 escenarios de margen. Comparalo contra el precio de
mercado del bloque 1.

**4. Estructura legal y fiscal.** Qué necesito para importar y vender en Argentina siendo
residente en España: figura societaria, CUIT, inscripción como importador, monotributo vs.
responsable inscripto, quién firma y quién opera allá, implicancias fiscales en España por
la actividad. Alternativa: vender desde España a clientes argentinos y qué cambia.

**5. Marca y posicionamiento.** Qué significa "Nilo Lino" como marca y contra quién compite.
Propuesta de valor en una frase. Precio objetivo y por qué. Verificá disponibilidad del
nombre: marca en INPI Argentina (clase 25) y en la UE, dominio, y handles de redes.
Señalá riesgos de confusión con marcas existentes.

**6. Canal y go-to-market.** Compará D2C por e-commerce propio, Instagram/WhatsApp,
Mercado Libre, showroom, pop-up y multimarca, con su impacto en margen, capital de trabajo y
velocidad de aprendizaje. Recomendá uno para arrancar y decí por qué. Plan de adquisición de
los primeros 100 clientes sin presupuesto grande de publicidad — incluyendo cómo uso el hecho
de que yo mismo soy el usuario del producto.

**7. Operaciones en Argentina.** Depósito, fulfillment, envíos, cambios y devoluciones,
cobros y cómo saco el dinero. Qué puedo hacer a distancia y qué exige alguien de confianza
en el terreno.

**8. Dinero.** Capital mínimo para arrancar. Proyección de caja mes a mes del primer año, con
el detalle de cuánto tiempo queda el capital inmovilizado en stock. Punto de equilibrio en
unidades. Escenario pesimista, base y optimista. Cuánto pierdo si el peor caso se cumple.

**9. Riesgos.** Los 8–10 que realmente pueden matar el proyecto, ordenados por
`probabilidad × impacto`, cada uno con la señal temprana que lo anticipa y la mitigación
concreta. Incluí explícitamente: cambio de reglas de importación, salto cambiario, stock que
no rota (talles/colores muertos), calidad que no llega, y competencia local que baja precios.

**10. Roadmap por fases.** Fases con hitos, costo y duración. Cada fase termina en un
**criterio de sigo/paro medible**, no en una sensación. La fase 1 tiene que ser la prueba más
barata posible que genere información real.

### Formato de salida

- Empezá con **las preguntas**. Nada más. Esperá mi respuesta antes de seguir.
- Cuando tengas mis respuestas, entregá el plan con esta estructura:
  1. Veredicto en 5 líneas: ¿esto cierra o no cierra, y de qué depende?
  2. Los 3 números que definen todo el negocio.
  3. Los bloques 1–10 desarrollados.
  4. Tabla de supuestos pendientes de verificar, ordenados por cuánto mueven el resultado.
  5. Qué hago esta semana (3 acciones concretas, con costo y tiempo).
- Español rioplatense para todo lo que sea de cara al mercado argentino.
- Tablas donde haya números. Sin relleno ni motivación.

---

## Variante corta (para una primera pasada rápida)

> Modo plan. Quiero montar Nilo Lino: marca argentina de camisas de lino importadas.
> Vivo en Málaga, compro a 30–40 € y en Argentina veo comparables a ~150 €. Antes de
> planificar, hacéme las 10 preguntas que más cambian el plan. Después dame: (1) si el
> arbitraje sobrevive a aranceles e impuestos, con el landed cost línea por línea y datos
> verificados a hoy; (2) la prueba más barata posible para validarlo sin traer un contenedor;
> (3) roadmap por fases con criterio de sigo/paro en cada una. No inventes cifras: marcá cada
> número como verificado (con fuente y fecha) o supuesto.

---

## Cómo usarlo

1. Pegá el prompt maestro en modo plan y **respondé las preguntas con honestidad**,
   sobre todo la de capital disponible: el plan cambia por completo entre 5.000 € y 50.000 €.
2. Si Claude te devuelve el plan sin haber preguntado, pedíle que vuelva atrás y pregunte.
3. Guardá cada iteración. El plan bueno sale en la tercera o cuarta pasada, no en la primera.
4. La respuesta que más importa es la del bloque 3 (landed cost). Si ese número no cierra,
   el resto del plan es decorado.
