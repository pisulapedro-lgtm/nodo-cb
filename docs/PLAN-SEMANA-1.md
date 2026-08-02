# Clima Baires — Plan de ejecución, semana 1

**Sprint:** lunes 3 → domingo 9 de agosto de 2026
**Hito:** viernes 7/8 — tienda completa y navegable en modo privado, lista para revisar
**Ejecuta:** 1 persona, dedicación completa

---

## Contexto confirmado

Esto reemplaza los supuestos del [plan técnico](PLAN-TECNICO.md), que se escribió antes de saber que Clima Baires es una empresa instaladora en activo.

| | |
|---|---|
| Negocio | Empresa que **vende e instala** equipos de climatización |
| Zona | Costa del Sol (provincia de Málaga) |
| Instaladores | **Propios y habilitados** |
| Proveedor | Alta cerrada, tarifa, fotos y fichas técnicas disponibles |
| Administrativo | Empresa, CIF, banco y gestor resueltos |
| Marca | Nombre, dominio y logo listos |
| Catálogo inicial | Split 1x1, multisplit, conductos y cassette |
| Objetivo semana 1 | Tienda lista para revisar (modo privado) |

### Lo que este contexto cambia

**1. El problema de gases fluorados desaparece.** Instaladores propios habilitados: se vende con instalación propia y el requisito legal se cumple solo. Deja de ser un riesgo y pasa a ser la ventaja competitiva.

**2. El producto no es el equipo, es el equipo instalado y funcionando.** El precio que se muestra debe ser **"equipo + instalación estándar, IVA incluido"**. Amazon, MediaMarkt y Leroy venden una caja que el cliente todavía tiene que resolver quién le monta. Clima Baires vende el aire acondicionado funcionando el jueves. Competir por precio de caja es una guerra perdida; competir por precio final instalado es una guerra ganada de entrada.

**3. Catálogo pequeño y bien hecho.** No hacen falta 300 SKUs. Hacen falta **30-40 equipos** — los que ya se instalan hoy, con stock y servicio técnico conocido. Un catálogo corto y bien documentado convierte más que uno enorme y pobre, y se carga en dos días en vez de dos semanas.

**4. Inglés no es opcional.** La Costa del Sol tiene una proporción altísima de residentes británicos, escandinavos, alemanes y holandeses, con capacidad de compra y con la costumbre de buscar y comprar online. Un competidor local que solo esté en español está dejando ese mercado libre. **ES + EN desde el lanzamiento.**

**5. El SEO local vale más que el catálogo.** "Aire acondicionado Marbella", "instalación aire acondicionado Fuengirola", "air conditioning installation Estepona". Volumen decente, intención altísima y competencia floja. Una colección por municipio bien trabajada rinde más que 200 productos extra.

**6. Tratamiento anticorrosión — el detalle que nadie cuenta.** En primera línea de costa la brisa marina destroza las unidades exteriores en pocos años. Los equipos con tratamiento anticorrosión (Blue Fin, Gold Fin y equivalentes) duran mucho más. Casi ninguna tienda online lo menciona porque lo desconoce. Una empresa instaladora de la Costa del Sol sí lo sabe, y decirlo demuestra criterio técnico real. **Va como filtro del catálogo, como campo de la ficha y como artículo de contenido.**

---

## Supuestos abiertos

No bloquean el arranque. Confirmar el lunes por la mañana:

1. **Precio de instalación estándar** por tipo de equipo (1x1, 2x1, 3x1). Necesario el miércoles.
2. **Municipios cubiertos** con su código postal, para validar en el checkout.
3. **Listado de los 30-40 equipos más instalados** hoy. Es la base del catálogo.
4. **Formato del Excel del proveedor** — pasame un archivo de muestra y preparo el importador.
5. **Presupuesto mensual para apps** (asumo 0-50 €/mes; el plan usa solo apps gratuitas).

---

## Reglas del sprint

- **Modo privado toda la semana.** La tienda no se indexa ni se publica hasta que el pedido de prueba funcione punta a punta.
- **Nada a mano que se pueda importar.** Un producto piloto se carga a mano para validar el molde; el resto entra por CSV.
- **El inglés se deja para el fin de semana.** Primero que el español esté cerrado; traducir sobre contenido que aún cambia es trabajo tirado.
- **Si un día se atrasa, se recorta alcance, no calidad.** Al final del documento está el orden de sacrificio.

---

# DÍA 1 — Lunes 3/8 · Cimientos

> El día de las decisiones estructurales. Nada de lo que se hace hoy se ve bonito, y todo lo de los próximos cuatro días depende de que esté bien.

### 1.1 · Alta y configuración regional — 1 h

- [ ] Crear cuenta Shopify, plan **Basic** (arrancar con la prueba gratuita)
- [ ] País España · moneda EUR · zona horaria Europe/Madrid
- [ ] Impuestos: IVA **21 %**
- [ ] **Activar "todos los precios incluyen impuestos"** — en venta B2C en España el precio mostrado debe ser con IVA. Si esto se configura mal y ya hay productos cargados, corregirlo después es un lío.
- [ ] Unidades métricas (kg, cm)
- [ ] Datos fiscales de la empresa en la configuración de la tienda

### 1.2 · Dominio — 45 min · **primero del día**

- [ ] Apuntar el dominio a Shopify (registro A + CNAME de www)
- [ ] Activar SSL

Se hace a primera hora porque la propagación DNS puede tardar horas y no se quiere descubrir el viernes que algo falla.

### 1.3 · Tema y apps base — 1 h

- [ ] Instalar el tema **Dawn** (gratuito, oficial, rápido y accesible)
- [ ] App **Search & Discovery** (gratis, de Shopify) — habilita filtros por metacampos
- [ ] App **Translate & Adapt** (gratis, de Shopify) — para el inglés del fin de semana
- [ ] Aplicar logo, colores de marca y tipografía

> **Sobre el tema:** la tentación es comprar uno de pago de 300 $. No hace falta. Dawn es rápido, accesible y se personaliza bien. La conversión en este rubro la mueven la ficha técnica y el precio con instalación, no el carrusel de la home. Si más adelante se quiere invertir en diseño, se hace con datos.

### 1.4 · Definir la ficha técnica — 2 h · **la tarea clave de la semana**

Esto es el esqueleto de todo el catálogo. Definirlo bien hoy evita rehacer 40 productos el jueves.

Metacampos de producto, namespace `ficha`:

| Campo | Tipo | Nota |
|---|---|---|
| `potencia_frio_kw` | Decimal | |
| `potencia_calor_kw` | Decimal | |
| `frigorias` | Entero | Derivado: kW × 860 |
| `m2_min` / `m2_max` | Entero | Superficie recomendada |
| `seer` | Decimal | Eficiencia en frío |
| `scop` | Decimal | Eficiencia en calor |
| `clase_frio` | Texto | A+++ … D |
| `clase_calor` | Texto | |
| `consumo_anual_kwh` | Entero | Alimenta el estimador de coste |
| `eprel_id` | Texto | **Obligatorio legalmente** — sin esto no se publica |
| `refrigerante` | Texto | R32, R410A, R290 |
| `carga_kg` | Decimal | Carga de refrigerante |
| `inverter` | Booleano | |
| `bomba_calor` | Booleano | Frío + calor |
| `wifi` | Booleano | |
| `anticorrosion` | Booleano | **El diferencial Costa del Sol** |
| `db_interior_min` | Entero | Nivel sonoro mínimo |
| `db_exterior` | Entero | |
| `dim_ui` / `dim_ue` | Texto | "800 × 293 × 230 mm" |
| `peso_ui` / `peso_ue` | Decimal | Alimenta tarifas de envío |
| `garantia_meses` | Entero | |

- [ ] Crearlos en **Configuración → Metacampos → Productos**
- [ ] Marcar como visibles en el storefront (necesario para filtros y para mostrarlos en la ficha)

### 1.5 · Colecciones y navegación — 2 h

Doble función: navegación **y** páginas de aterrizaje para SEO. Cada colección es una URL que puede posicionar.

**Por tipo**
- [ ] Split pared 1x1
- [ ] Multisplit (2x1, 3x1, 4x1)
- [ ] Conductos
- [ ] Cassette

**Por superficie** — así es como el cliente piensa realmente:
- [ ] Hasta 15 m² (dormitorio)
- [ ] 15–25 m² (salón pequeño)
- [ ] 25–40 m² (salón grande)
- [ ] Más de 40 m²

**Por característica**
- [ ] Con tratamiento anticorrosión — "Equipos para primera línea de playa"
- [ ] Clase A+++
- [ ] Con wifi

> Las colecciones por superficie se hacen automáticas con condiciones sobre los metacampos, y son las que mejor van a posicionar: la gente busca "aire acondicionado para salón de 30 metros", no "3000 frigorías".

### 1.6 · Estructura de páginas — 30 min

Crear vacías, se rellenan el viernes:
- [ ] Inicio · Catálogo · Cómo funciona la instalación · Calculadora · Sobre nosotros · Contacto · Presupuesto a medida (conductos y cassette) · Legales (4 páginas)

**Fin del día 1:** tienda existiendo con dominio propio, estructura definida y ficha técnica modelada.

---

# DÍA 2 — Martes 4/8 · Catálogo

> Día de producción pura. El objetivo es tener 30-40 equipos cargados con ficha completa.

### 2.1 · Selección de equipos — 1 h

- [ ] Listar los **30-40 equipos más instalados** en los últimos 12 meses
- [ ] Verificar que todos tengan stock y tarifa vigente
- [ ] Agrupar por familia y por rango de superficie

Criterio: si no se instaló nunca, no entra. El catálogo inicial debe ser lo que se sabe montar, con recambios accesibles y comportamiento conocido.

### 2.2 · Producto piloto a mano — 1,5 h

- [ ] Cargar **un** equipo completo manualmente: título, descripción, imágenes, los 22 metacampos, precio, peso, colecciones
- [ ] Revisarlo en el storefront y validar que la ficha se ve bien

Este producto es el molde. Si algo está mal en el modelo, se descubre ahora con uno cargado y no con cuarenta.

### 2.3 · Preparar el CSV — 2,5 h

- [ ] Volcar el Excel del proveedor a la plantilla de importación de Shopify
- [ ] Completar los metacampos desde las fichas del fabricante
- [ ] **Obtener el ID EPREL de cada modelo** (base de datos pública de la UE) — es obligatorio para venta online
- [ ] Aplicar el margen y calcular el PVP con IVA
- [ ] Revisar títulos: formato `Marca Modelo — X frigorías — Split 1x1 Inverter A+++`

> Te preparo el script que convierte el Excel del proveedor en el CSV listo para importar. Pasame el archivo de muestra y lo tenés funcionando el lunes.

### 2.4 · Importar — 1 h

- [ ] Importar el CSV
- [ ] Verificar 5 productos al azar contra la fuente
- [ ] Revisar que las colecciones automáticas se hayan poblado solas

### 2.5 · Imágenes — 2 h

- [ ] Descargar el material del proveedor
- [ ] Renombrar con la referencia del modelo antes de subir (ayuda al SEO de imagen)
- [ ] Comprimir a ~1600 px de ancho
- [ ] Texto alternativo descriptivo en cada una

**Fin del día 2:** catálogo cargado, navegable y con fichas completas.

---

# DÍA 3 — Miércoles 5/8 · Instalación, precios y envíos

> El día que convierte la tienda en el negocio real. Aquí está el diferencial.

### 3.1 · Modelar los packs de instalación — 2 h

**Instalación estándar** — precio cerrado, incluye:
- Hasta 3 m de tubería frigorífica
- Unidad exterior en la misma pared o balcón, sin elevación
- Vacío, carga y puesta en marcha
- Retirada del embalaje
- Certificado de instalación

**Suplementos** (variantes o productos adicionales):
- [ ] Metro adicional de tubería
- [ ] Trabajo en altura / andamio
- [ ] Bomba de condensados
- [ ] Canaleta decorativa
- [ ] Retirada del equipo antiguo — **gratuita** (obligación RAEE de recogida uno por uno; conviene comunicarlo como ventaja)

Ser explícito sobre **qué NO incluye** (obra, canalización empotrada, refuerzo eléctrico). La principal fuente de conflicto post-venta en este sector son los extras no anticipados, y anticiparlos genera más confianza que ocultarlos.

### 3.2 · Precio con instalación incluida — 1,5 h

- [ ] Configurar cada producto para que el precio principal sea **equipo + instalación estándar, IVA incluido**
- [ ] Desglose visible en la ficha: "Equipo 749 € + Instalación 290 € = **1.039 € IVA incluido**"

> El desglose importa. Un precio único alto asusta; el mismo precio desglosado se lee como transparencia. Y deja ver que la instalación está incluida, que es justo lo que la competencia no ofrece.

### 3.3 · Cobertura por código postal — 1,5 h

- [ ] Cargar los CP cubiertos de la Costa del Sol
- [ ] Zonas de envío en Shopify restringidas a esos CP
- [ ] Mensaje claro para el resto: "Todavía no llegamos a tu zona — dejanos tu email y te avisamos"

Fuera de zona no se puede garantizar instalación, y prometerla sería el peor error posible en la primera semana.

### 3.4 · Flujo de presupuesto para conductos y cassette — 1,5 h

Estos no se venden con un clic: necesitan visita previa y proyecto.

- [ ] Ficha en modo **"Solicitar presupuesto"** en vez de "Añadir al carrito"
- [ ] Formulario: superficie, nº de estancias, tipo de vivienda, fotos, teléfono
- [ ] Aviso de plazo de respuesta ("te contestamos en 24-48 h laborables")

### 3.5 · Envíos — 1 h

- [ ] Tarifas por peso y zona usando los pesos reales del catálogo
- [ ] Envío + instalación como un único proceso: el cliente elige día, no un método de envío
- [ ] Plazos realistas — mejor prometer 7 días y cumplir que prometer 48 h en plena temporada

**Fin del día 3:** se puede comprar un equipo instalado, con precio cerrado y fecha.

---

# DÍA 4 — Jueves 6/8 · Herramientas de conversión

> El día del asesoramiento automatizado. El cliente no sabe qué comprar; hoy se lo resolvemos.

### 4.1 · Calculadora de frigorías — 3 h

La herramienta de mayor retorno del proyecto: capta tráfico orgánico de altísima intención y convierte visitas en pedidos ya cualificados.

- [ ] Entradas: m², altura de techo, orientación, planta, superficie acristalada, aislamiento, ocupantes, uso frío/calor
- [ ] Salida: potencia recomendada en kW y frigorías, con rango
- [ ] **Botón directo a los equipos de ese rango** — es lo que la convierte en herramienta de venta y no en juguete
- [ ] Página propia (`/calculadora`) y bloque embebido en la home

> Esto lo desarrollo yo como componente autónomo. Se pega en Shopify y también sirve para landings y campañas.

### 4.2 · Filtros del catálogo — 1,5 h

- [ ] Configurar filtros en Search & Discovery: superficie, tipo, frigorías, marca, clase energética, bomba de calor, wifi, **anticorrosión**, precio
- [ ] Probar en móvil — la mayor parte del tráfico va a ser móvil

### 4.3 · Ficha de producto — 2 h

Orden pensado para la decisión de compra:

1. Imagen · título · **precio con instalación incluida** y su desglose
2. **"Ideal para estancias de 20 a 30 m²"** — la traducción que el cliente entiende
3. Botón de compra + fecha estimada de instalación
4. Qué incluye la instalación (desplegable)
5. Ficha técnica completa (tabla de metacampos)
6. **Etiqueta energética + enlace EPREL** — obligatorio legalmente
7. Estimación de coste eléctrico anual
8. Preguntas frecuentes

- [ ] Maquetar la plantilla con los metacampos
- [ ] Añadir el estimador de consumo (SEER + consumo anual × precio del kWh)

### 4.4 · Comparador — 1,5 h · *opcional, primero en soltarse*

- [ ] Comparar hasta 3 equipos lado a lado

**Fin del día 4:** un visitante que no sabe nada de climatización puede llegar solo hasta el equipo correcto.

---

# DÍA 5 — Viernes 7/8 · Legal, pagos, contenido · **HITO**

### 5.1 · Páginas legales — 2 h

- [ ] Aviso legal (LSSI-CE) con datos completos de la empresa
- [ ] Política de privacidad (RGPD)
- [ ] Política de cookies + banner conforme a la guía de la AEPD
- [ ] Condiciones de venta: **garantía legal de 3 años**, desistimiento de 14 días con las particularidades del equipo ya instalado, plazos, formas de pago
- [ ] Información RAEE visible

> Te dejo los borradores. **Que los revise el gestor antes de publicar** — yo identifico las obligaciones y su impacto, pero esto necesita validación profesional.

### 5.2 · Pagos — 1,5 h

- [ ] Activar **Shopify Payments** (tarjeta)
- [ ] **Bizum** — muy extendido en España, buena conversión
- [ ] **Financiación (SeQura / Klarna / Aplazame)** — con ticket de 1.000-2.500 € instalado es la mayor palanca de conversión del proyecto
- [ ] Mostrar la cuota mensual **en la ficha y en el listado**, no solo en el checkout: "desde 45 €/mes" convierte mucho mejor que "1.039 €"
- [ ] Transferencia para pedidos grandes

### 5.3 · Home y páginas de servicio — 2,5 h

Home, en este orden:
1. Propuesta de valor sin rodeos: **"Aire acondicionado instalado en la Costa del Sol. Precio cerrado, instaladores propios."**
2. Calculadora de frigorías embebida
3. Acceso por superficie ("¿Cuántos m² tenés que climatizar?")
4. Los 6-8 equipos más vendidos
5. Cómo funciona: elegís → instalamos → funcionando (3 pasos)
6. Prueba social: años de experiencia, instalaciones realizadas, reseñas de Google
7. Zonas de cobertura

- [ ] Página "Cómo funciona la instalación" con fotos de trabajos reales
- [ ] Página "Sobre nosotros" — que sea una empresa real con instaladores propios es el mayor activo de confianza; hay que enseñarlo, con caras y con obra hecha

### 5.4 · SEO local — 1,5 h

- [ ] Títulos y meta descripciones de colecciones y páginas principales
- [ ] Datos estructurados de producto (precio, disponibilidad, valoraciones)
- [ ] Ficha de Google Business Profile enlazada
- [ ] Esbozar las landings por municipio para la semana 2: Marbella, Fuengirola, Estepona, Torremolinos, Benalmádena, Mijas, Málaga capital

**HITO DEL VIERNES:** tienda completa, navegable y funcional en modo privado, lista para revisar.

---

# Fin de semana 8-9/8 · Pruebas e inglés

### Sábado — Pruebas punta a punta

- [ ] **Pedido de prueba real**: comprar un equipo con instalación, pagar de verdad, verificar el email de confirmación, y reembolsar
- [ ] Probar el flujo completo en móvil
- [ ] Probar un CP fuera de zona y verificar que se bloquea bien
- [ ] Enviar el formulario de presupuesto de conductos y comprobar que llega
- [ ] Revisar el pedido: ¿queda claro qué equipo, qué instalación y qué suplementos?
- [ ] Velocidad de carga (PageSpeed) — atención al peso de las imágenes

### Domingo — Inglés

- [ ] Traducir con Translate & Adapt: navegación, colecciones, páginas legales, fichas
- [ ] Revisar a mano la traducción de las páginas clave — la automática en textos técnicos comete errores caros
- [ ] Selector de idioma visible en la cabecera

---

## Semana 2 (10-14/8) — vista previa

1. **Sincronizador de catálogo** — automatizar precio y stock del proveedor
2. **Landings por municipio** — el motor de captación de tráfico
3. **Ampliar catálogo** a 80-100 SKUs una vez validado el molde
4. **Contenido**: guía de compra, artículo sobre corrosión marina, mantenimiento
5. **Reseñas** (Judge.me gratuito) — pedirlas a clientes ya instalados
6. **Analítica** y publicación

---

## Si un día se atrasa — orden de sacrificio

Se recorta desde abajo:

1. **Comparador** (día 4) — prescindible sin drama
2. **Estimador de coste eléctrico** (día 4) — se añade después
3. **Colecciones por característica** (día 1) — quedan las de tipo y superficie
4. **Inglés** (domingo) — se pasa a la semana 2
5. **Catálogo a 20 SKUs** en vez de 40 — mejor 20 bien hechos que 40 a medias

**Nunca se recorta:**
- Ficha técnica con EPREL — obligación legal
- Páginas legales — obligación legal
- Validación de CP — prometer instalación fuera de zona es el peor error posible
- Pedido de prueba punta a punta — publicar sin probar el checkout es garantía de perder los primeros pedidos

---

## Qué desarrollo yo

Decime por cuál arranco y lo tenés antes del lunes:

| Entregable | Cuándo lo necesitás |
|---|---|
| **Calculadora de frigorías** — componente autónomo embebible | Día 4 |
| **Importador Excel → CSV de Shopify** — necesito el archivo de muestra | Día 2 |
| **Definición de metacampos** lista para importar | Día 1 |
| **Plantilla Liquid de ficha técnica** | Día 4 |
| **Borradores de páginas legales** | Día 5 |
| **Estimador de coste eléctrico** | Día 4 |

---

## Métricas desde el primer día

- Conversión global y por familia
- **% de pedidos con financiación** — indica si la palanca funciona
- Uso de la calculadora → conversión de quien la usa frente a quien no
- Solicitudes de presupuesto de conductos y su tasa de cierre
- CP fuera de cobertura — **dice hacia dónde conviene expandir la red**
- Margen real por pedido, con instalación y portes incluidos
