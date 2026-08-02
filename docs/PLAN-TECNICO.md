# Plan técnico — Ecommerce de climatización (España / UE)

**Versión:** 1.0 · **Estado:** propuesta para validar

---

## 1. Resumen ejecutivo

**Recomendación: Shopify** como plataforma de tienda, más un **servicio de sincronización de catálogo propio** desarrollado a medida.

Para España/UE, Shopify es la opción correcta: Shopify Payments está disponible, el ecosistema de apps es el más maduro, y el time-to-market es de semanas y no de meses. Frente a WooCommerce y PrestaShop, se paga una cuota mensual a cambio de no mantener infraestructura, seguridad ni actualizaciones.

Pero la plataforma es la parte fácil y commodity. **El proyecto real son tres piezas:**

1. **El sincronizador multi-proveedor.** Varios proveedores, cada uno con su Excel y su formato. Sin una capa de normalización, precios y stock se desactualizan y se venden equipos que no existen.
2. **El cumplimiento normativo.** Vender aire acondicionado en España activa obligaciones específicas que no aplican a un ecommerce genérico: gases fluorados, RAEE, etiquetado energético con registro EPREL. Ver sección 7 — hay un punto que **condiciona el modelo de negocio entero**.
3. **La ficha técnica y las herramientas de decisión.** En este rubro el cliente no sabe qué comprar. Quien le resuelve la duda, se lleva la venta.

El sincronizador es código propio y portable. Si mañana se migra de plataforma, se conserva.

---

## 2. Contexto y supuestos

| Variable | Valor |
|---|---|
| Mercado | España, con posible expansión UE |
| Modelo | Venta sin stock propio: se compra al proveedor tras la venta |
| Proveedores | Varios, catálogo extenso, entrega vía Excel (objetivo: migrar a API) |
| Producto | Equipos de climatización (split, multisplit, conductos, aerotermia) |
| Ticket medio estimado | 400 € – 2.500 € + instalación |
| Moneda | EUR |

**Supuestos a validar antes de la Fase 1:**
- Volumen aproximado de SKUs por proveedor.
- Frecuencia de actualización de las listas (¿diaria, semanal, mensual?).
- Si los proveedores hacen envío directo al cliente final (dropshipping) o si hay paso por almacén propio.
- Si se dispone de instalador propio, red de instaladores, o ninguno. **Crítico — ver 7.1.**

---

## 3. Decisión de plataforma

### Comparativa para el caso español

| Criterio | Shopify | WooCommerce | PrestaShop |
|---|---|---|---|
| Coste mensual base | 29–89 €/mes | Hosting 20–60 €/mes | Hosting 20–60 €/mes |
| Coste real de propiedad | Bajo (gestionado) | Alto (mantenimiento, seguridad) | Alto |
| Time-to-market | 3–4 semanas | 6–10 semanas | 8–12 semanas |
| Shopify Payments / Stripe | Nativo | Vía plugin | Vía módulo |
| Bizum | App / vía Redsys | Plugin Redsys | Módulo Redsys |
| Financiación (SeQura, Klarna) | Apps oficiales | Plugins oficiales | Módulos |
| Catálogo grande + filtros | Requiere app de pago | Nativo mejorable | Nativo bueno |
| API para sincronización | Excelente (GraphQL Admin) | Buena (REST) | Aceptable |
| Metafields / ficha técnica | Excelente | Vía ACF u otros | Características nativas |
| Riesgo técnico | Bajo | Medio | Medio-alto |

### Veredicto

**Shopify.** El argumento decisivo no es el precio, es que el equipo puede concentrarse en catálogo, contenido y conversión en vez de en mantener un servidor. Con un modelo sin stock, el margen es ajustado y el tiempo del equipo vale más que 30 €/mes.

**WooCommerce tendría sentido si:** ya existe una web WordPress consolidada con tráfico y SEO que no conviene tocar, o si hay perfil técnico interno con ganas de mantenerla.

**Desarrollo propio (Next.js + Medusa/Saleor): no.** Al menos no hasta tener demanda validada y un volumen que lo justifique. Añade meses al lanzamiento para resolver problemas que Shopify ya resolvió.

### Nota sobre el plan de Shopify

Empezar en **Basic**. El salto a Grow/Advanced se justifica solo cuando el ahorro en comisión por transacción supere la diferencia de cuota — es decir, con facturación alta. No adelantar ese gasto.

---

## 4. Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────┐
│  PROVEEDORES                                                │
│  Prov. A (xlsx)   Prov. B (csv)   Prov. C (API futura)      │
└────────┬──────────────┬───────────────────┬─────────────────┘
         │              │                   │
         ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│  1. INGESTA                                                 │
│  Un adaptador por proveedor. Config declarativa (YAML):     │
│  mapeo de columnas → campos canónicos                       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. NORMALIZACIÓN Y VALIDACIÓN                              │
│  Modelo canónico. Limpieza de tipos, unidades, marcas.      │
│  Rechazo de filas inválidas → informe de errores            │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. DEDUPLICACIÓN MULTI-PROVEEDOR                           │
│  Match por EAN → referencia fabricante → fuzzy sobre título │
│  Un producto puede tener N ofertas de N proveedores         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. SELECCIÓN DE OFERTA + MOTOR DE PRECIOS                  │
│  Elige proveedor por reglas. Aplica markup, redondeo, IVA   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. PUBLICADOR (Shopify Admin GraphQL API)                  │
│  Diff contra estado actual → solo escribe lo que cambió     │
└─────────────────────────────────────────────────────────────┘
                         ▼
              ┌──────────────────────┐
              │  Shopify (storefront)│
              └──────────────────────┘
```

### Stack propuesto para el sincronizador

| Componente | Elección | Motivo |
|---|---|---|
| Lenguaje | **Python 3.12** | Es la herramienta correcta para ETL sobre datos tabulares sucios |
| Excel / CSV | `pandas` + `openpyxl` | Estándar, tolerante a formatos irregulares |
| Validación | `pydantic v2` | Modelo canónico tipado, errores legibles |
| Matching difuso | `rapidfuzz` | Rápido y con buenas heurísticas de similitud |
| Base de datos | **PostgreSQL** | Histórico de precios, estado de sincronización, auditoría |
| Cliente Shopify | `httpx` sobre GraphQL Admin API | Menos llamadas que REST, control fino |
| Orquestación | Cron o APScheduler | No hace falta Airflow para esto |
| Hosting | Railway / Fly.io / VPS | 10–20 €/mes es suficiente |

**Por qué Python y no TypeScript:** el 80% del trabajo es limpiar Excels inconsistentes. `pandas` + `rapidfuzz` ahorran semanas frente a hacerlo en Node. El sincronizador es un servicio independiente; el lenguaje no condiciona nada del storefront.

### Frecuencia de sincronización

| Dato | Frecuencia | Motivo |
|---|---|---|
| Stock | 2–4 veces/día | Es el que causa cancelaciones |
| Precio | 1 vez/día | Cambios de tarifa son menos frecuentes |
| Alta de productos nuevos | Semanal, con revisión manual | Requiere fichas y fotos |
| Baja / descatalogados | Diario | Ocultar, nunca borrar (rompe SEO y pedidos históricos) |

---

## 5. Modelo de datos canónico

Este es el contrato interno. Todo adaptador de proveedor debe producir esto.

```python
class OfertaProveedor(BaseModel):
    proveedor_id: str
    sku_proveedor: str
    ean: str | None              # clave primaria de matching
    referencia_fabricante: str | None
    marca: str
    titulo_original: str
    precio_coste: Decimal        # sin IVA
    stock: int
    plazo_entrega_dias: int | None
    fecha_actualizacion: datetime

class ProductoCanonico(BaseModel):
    ean: str
    marca: str
    modelo: str
    familia: Literal["split", "multisplit", "conductos",
                     "cassette", "aerotermia", "portatil"]

    # --- Ficha técnica ---
    potencia_frigorifica_kw: Decimal
    potencia_calorifica_kw: Decimal | None
    frigorias_h: int              # derivado, para búsqueda del usuario
    superficie_recomendada_m2: tuple[int, int]
    tecnologia_inverter: bool
    bomba_calor: bool

    # --- Eficiencia (obligatorio legalmente, ver 7.3) ---
    seer: Decimal
    scop: Decimal | None
    clase_energetica_frio: str    # A+++ … D
    clase_energetica_calor: str | None
    consumo_anual_kwh: int | None
    eprel_id: str                 # OBLIGATORIO para venta online

    # --- Gases fluorados (ver 7.1) ---
    refrigerante: str             # R32, R410A, R290...
    carga_refrigerante_kg: Decimal
    pca_gwp: int
    toneladas_co2_equivalente: Decimal

    # --- Datos de uso ---
    nivel_sonoro_interior_db: int | None
    nivel_sonoro_exterior_db: int | None
    wifi: bool
    dimensiones_ui_mm: tuple[int, int, int]
    dimensiones_ue_mm: tuple[int, int, int]
    peso_ui_kg: Decimal | None
    peso_ue_kg: Decimal | None
    garantia_meses: int

    # --- Comercial ---
    ofertas: list[OfertaProveedor]
```

**Nota importante:** los proveedores raramente aportan la ficha técnica completa. El Excel suele traer solo SKU, descripción, precio y stock. El resto (SEER, EPREL, carga de refrigerante) hay que construirlo una vez por modelo desde las fichas del fabricante y **mantenerlo en base propia**. Ese trabajo es lento pero es exactamente lo que crea la barrera de entrada frente a la competencia.

### Configuración de adaptador por proveedor

```yaml
# proveedores/proveedor_a.yaml
proveedor_id: prov_a
formato: xlsx
hoja: "TARIFA"
fila_cabecera: 7          # muchas tarifas traen logo y notas arriba
columnas:
  sku_proveedor: "CÓDIGO"
  ean: "EAN13"
  marca: "MARCA"
  titulo_original: "DESCRIPCIÓN"
  precio_coste: "PVP NETO"
  stock: "DISPO"
transformaciones:
  precio_coste: [quitar_simbolo_euro, coma_a_punto, to_decimal]
  stock: [texto_stock_a_entero]   # "Disponible"/"Consultar" → 10/0
  ean: [solo_digitos, validar_ean13]
descartar_si:
  - precio_coste <= 0
  - marca in ["", "ACCESORIOS"]
```

Añadir un proveedor nuevo = escribir un YAML. Sin tocar código.

---

## 6. Motor de precios

### Reglas

```yaml
markup:
  por_defecto: 1.28
  por_marca:
    Daikin: 1.22          # marca premium, mercado más competido
    Mitsubishi Electric: 1.22
    Haier: 1.35
  por_familia:
    aerotermia: 1.20      # ticket alto, margen porcentual menor
    portatil: 1.40
redondeo:
  modo: psicologico       # 1247,30 → 1249,00
margen_minimo_eur: 45     # por debajo de esto no se publica
iva: 0.21
```

### Reglas críticas

1. **Suelo de margen absoluto, no solo porcentual.** Un equipo de 300 € al 28% deja 84 € brutos; si la instalación y el envío se comen 60 €, el pedido no es rentable. Definir margen mínimo en euros.

2. **Histórico de precios en base de datos.** Necesario por dos motivos: detectar subidas anómalas del proveedor (posible error en su Excel) y cumplir la **Directiva Ómnibus** (sección 7.5), que obliga a mostrar el precio más bajo de los 30 días previos al anunciar un descuento.

3. **Salvaguarda contra errores de tarifa.** Si un precio varía más de un ±25% respecto a la sincronización anterior, no publicar: marcar para revisión manual. Un decimal mal puesto en el Excel del proveedor puede vender equipos a pérdida.

4. **Selección de proveedor cuando hay varias ofertas:**
   ```
   1. Filtrar ofertas con stock > 0
   2. Si ninguna tiene stock → publicar "bajo pedido" con el plazo mayor
   3. Entre las que tienen stock → menor coste total (precio + porte)
   4. A igualdad → proveedor con mejor histórico de fiabilidad
   ```

---

## 7. Cumplimiento normativo (España / UE)

Esta sección tiene impacto directo en el modelo de negocio. **No es un anexo legal — el punto 7.1 puede condicionar si se puede vender online tal como está planteado.**

> Todo lo de esta sección debe validarse con un gestor/asesor legal antes de lanzar. Aquí se identifican las obligaciones y su impacto técnico; no sustituye asesoramiento profesional.

### 7.1 Gases fluorados — el punto crítico ⚠️

La normativa europea de gases fluorados (Reglamento UE 2024/573, que sustituye al 517/2014) establece que **los equipos precargados con gases fluorados que requieren instalación por personal certificado solo pueden venderse al usuario final si se acredita que la instalación la realizará una empresa habilitada.**

La práctica totalidad de los splits (R32, R410A) entra en este supuesto.

**Implicación directa:** no se puede simplemente enviar la caja al cliente final y desentenderse.

**Tres salidas posibles:**

| Opción | Descripción | Valoración |
|---|---|---|
| **A. Vender siempre con instalación** | Red de instaladores certificados; la instalación es obligatoria en el carrito | **Recomendada.** Resuelve lo legal y añade margen |
| **B. Acreditación del instalador** | El cliente sube el certificado de su instalador antes de completar el pedido | Fricción alta en checkout, cae la conversión |
| **C. Solo equipos exentos** | Portátiles y equipos con carga por debajo de umbral | Limita muchísimo el catálogo |

**Recomendación: A como opción por defecto, B como alternativa para instaladores profesionales.** Esto convierte una obligación legal en el eje del negocio: no se vende una caja, se vende "aire acondicionado instalado y funcionando". Es mejor producto y mejor margen.

**Impacto técnico:** el flujo de checkout necesita un paso de instalación obligatorio con validación, y un backoffice para gestionar la red de instaladores por código postal.

### 7.2 RAEE — residuos de aparatos eléctricos

Como distribuidor de aparatos eléctricos hay que:
- Inscribirse en el **Registro Integrado Industrial (REI-RAEE)** si se actúa como productor (importación directa; si se compra a distribuidor nacional, la obligación suele recaer en él — verificar por proveedor).
- Adherirse a un **SCRAP** (Ecolec, Ecoasimelec, ERP…) si aplica.
- Ofrecer **recogida "uno por uno"**: al vender un equipo, aceptar la retirada gratuita del equipo antiguo equivalente.
- Informar de ello de forma visible en la web.

**Impacto técnico:** casilla en el checkout — "¿Desea que retiremos su equipo antiguo?" — y su gestión logística.

### 7.3 Etiquetado energético y EPREL

Reglamento Delegado (UE) 626/2011 más el Reglamento (UE) 2017/1369. Para **venta online es obligatorio** mostrar:
- La **etiqueta energética** (el gráfico de flechas de color, no solo la letra).
- La **ficha de información del producto**.
- Enlace a la ficha del producto en la base de datos **EPREL**.

La etiqueta debe verse en la página de producto y, en anuncios visuales con precio, mostrarse la clase energética.

**Impacto técnico:** el campo `eprel_id` es obligatorio en el modelo canónico. Un producto sin EPREL no debería poder publicarse. Se puede automatizar la descarga de la etiqueta desde la API pública de EPREL.

Esto además juega a favor: quien muestra bien las etiquetas transmite profesionalidad y le da al cliente un criterio de comparación real.

### 7.4 Facturación electrónica y Verifactu

España está en plena transición: Ley Antifraude (11/2021), reglamento **Verifactu** y facturación electrónica B2B obligatoria de la Ley Crea y Crece. Los calendarios de entrada en vigor se han modificado varias veces.

**Acción:** confirmar con el gestor el calendario aplicable según la forma jurídica y facturación. Elegir una app de facturación de Shopify que ya esté certificada para Verifactu, no una genérica. En País Vasco y Navarra aplican además TicketBAI/Batuz.

### 7.5 Consumo, GDPR y Ómnibus

| Obligación | Impacto |
|---|---|
| **Desistimiento 14 días** | Política clara. Ojo: un equipo ya instalado tiene matices — documentarlo bien |
| **Garantía legal 3 años** | Desde la Ley 4/2022, para bienes comprados desde 01/01/2022 |
| **Directiva Ómnibus** | Al anunciar descuento, mostrar el precio más bajo de los 30 días previos → requiere el histórico de precios de la sección 6 |
| **RGPD + LSSI** | Banner de cookies conforme a la guía de la AEPD, aviso legal, política de privacidad |
| **Accesibilidad (EAA)** | La Ley 11/2023 traspone la Directiva de Accesibilidad Europea; el comercio electrónico está afectado. Elegir un tema de Shopify accesible desde el principio sale mucho más barato que remediarlo después |

### 7.6 Impuesto sobre gases fluorados

Existe un impuesto especial sobre los gases fluorados. Normalmente ya viene repercutido en el precio del proveedor, pero **hay que confirmarlo por proveedor** para no calcular el margen sobre una base equivocada.

---

## 8. Ficha técnica y herramientas de conversión

### El problema del cliente

Quien busca aire acondicionado no sabe qué necesita. Las preguntas reales son: *¿cuántas frigorías para mi salón? ¿Me sirve para calentar en invierno? ¿Cuánto me va a costar de luz? ¿Cuánto tarda la instalación? ¿Entra en mi pared?*

Un catálogo que solo lista modelos y precios pierde contra quien responde esas preguntas.

### 8.1 Calculadora de frigorías

La herramienta de mayor retorno del proyecto: capta tráfico orgánico de alta intención y convierte visitas en pedidos cualificados.

**Entradas:** superficie (m²), altura de techo, orientación, planta, superficie acristalada, aislamiento, nº de ocupantes, uso frío/calor.

**Salida:** potencia recomendada en kW y frigorías/h, con rango, más un enlace directo a los equipos filtrados de ese rango.

Implementación: componente autónomo (Web Component o script embebible) para poder usarlo dentro de Shopify y también en landings.

### 8.2 Filtros del catálogo

Filtrar por **superficie a climatizar en m²**, no solo por frigorías. El cliente conoce sus metros; las frigorías no.

Filtros: m², frigorías, marca, tipo (split/multisplit/conductos), bomba de calor, clase energética, refrigerante, wifi, nivel sonoro, rango de precio, disponibilidad.

### 8.3 Comparador

Hasta 3 equipos en tabla lado a lado, resaltando diferencias. Reduce la fuga a Amazon/Leroy para comparar.

### 8.4 Estimador de coste eléctrico

A partir del SEER/SCOP y el consumo anual, estimar el coste anual con el precio medio del kWh. Justifica pagar más por un A+++ y sube el ticket medio.

### 8.5 Instalación como producto

Dado el punto 7.1, la instalación es obligatoria — conviene presentarla bien:

- **Instalación estándar** — hasta 3 m de tubería, unidades en la misma pared, sin elevación.
- **Instalación con material adicional** — metro extra de tubería, canaleta, soportes.
- **Instalación compleja** — trabajos en altura, andamio, obra.

Presupuesto por código postal, con visita previa para las complejas. Comunicar con transparencia qué incluye y qué no: la principal fuente de conflictos post-venta en este sector son los extras no previstos.

---

## 9. Pagos y financiación

| Método | Prioridad | Nota |
|---|---|---|
| Tarjeta (Shopify Payments) | Imprescindible | Comisión más baja al ser nativo |
| **Bizum** | Alta | Muy extendido en España, buena conversión |
| **Financiación (SeQura / Klarna / Aplazame)** | **Crítica** | Con ticket de 400–2.500 € + instalación, es la mayor palanca de conversión del proyecto |
| PayPal | Media | Genera confianza, comisión más alta |
| Transferencia | Baja | Útil para pedidos B2B grandes |

**La financiación merece un tratamiento de primer nivel**: mostrar la cuota mensual en la ficha de producto y en el listado, no solo en el checkout. "Desde 45 €/mes" convierte mucho mejor que "1.249 €".

**B2B:** si hay instaladores comprando, plantear un canal con precios diferenciados. Shopify tiene funcionalidad B2B en planes altos; al principio se puede resolver con un catálogo y descuentos por cliente.

---

## 10. Logística

Un split no es un paquete estándar: la unidad exterior de un equipo medio ronda los 30–40 kg y viene en bulto voluminoso.

**Decisiones a cerrar:**
1. ¿Envío directo del proveedor al cliente (dropshipping) o consolidación en almacén propio? El directo evita almacén pero complica los pedidos multi-proveedor y la coordinación con el instalador.
2. **Coordinación entrega + instalación.** Si llegan por separado, el cliente se queda con una caja en el salón. Idealmente el instalador recoge y monta el mismo día.
3. **Portes en el margen.** Un porte de palet a península ronda 30–60 €; a Baleares, Canarias, Ceuta y Melilla cambia todo (Canarias tiene además régimen fiscal propio, IGIC en vez de IVA — plantearse si se sirve o no desde el inicio).
4. **Tarifas por peso y zona** configuradas en Shopify, alimentadas con el peso real del modelo canónico.

---

## 11. Fases y estimación

| Fase | Contenido | Duración |
|---|---|---|
| **0. Definición** | Cerrar proveedores, formatos de Excel, red de instaladores, validación legal con gestor | 1–2 sem |
| **1. Tienda base** | Shopify, tema, estructura de categorías, legales, pagos, 40–60 SKUs cargados a mano de un solo proveedor | 3 sem |
| **2. Sincronizador** | Ingesta, normalización, dedup, motor de precios, publicador. 1 proveedor primero, luego los demás | 4 sem |
| **3. Ficha técnica y herramientas** | Metafields, calculadora de frigorías, comparador, filtros, estimador de consumo | 3 sem |
| **4. Instalación y cumplimiento** | Flujo de instalación en checkout, EPREL, RAEE, backoffice de instaladores | 2–3 sem |
| **5. Lanzamiento** | SEO técnico, analítica, pruebas de pedido real punta a punta, contenido | 2 sem |

**Total estimado: 15–17 semanas** hasta lanzamiento completo.

**Se puede vender antes.** Al final de la Fase 1 ya hay tienda operativa con catálogo reducido cargado a mano. Recomendación: **lanzar ahí, en modo piloto**, con 40–60 equipos de los más vendidos. Se empieza a validar demanda y precios reales mientras se construye el resto, y los primeros pedidos enseñan más sobre el negocio que cualquier planificación.

### Orden de prioridad si hay que recortar

1. Tienda + pagos + flujo de instalación (sin esto no se factura ni se cumple la ley)
2. Sincronizador de precio y stock (sin esto no se escala)
3. Calculadora de frigorías (mayor retorno en captación)
4. Comparador y estimador de consumo
5. Multi-proveedor con deduplicación

---

## 12. Costes recurrentes estimados

| Concepto | Coste mensual |
|---|---|
| Shopify Basic | 29–36 € |
| Apps (filtros, reseñas, facturación) | 60–120 € |
| Hosting del sincronizador (VPS + Postgres) | 15–25 € |
| Dominio y correo | 5 € |
| **Subtotal fijo** | **110–185 €/mes** |
| Comisión pasarela | ~1,5–2% + 0,25 €/transacción |
| Comisión financiación | ~2–4% del pedido financiado |
| SCRAP RAEE | Variable según unidades |

Los precios de Shopify y de las apps cambian con frecuencia — verificar los vigentes al contratar.

**El coste de plataforma es marginal** frente al de adquisición de tráfico. El presupuesto real de este proyecto está en SEO, contenido y campañas, no en software.

---

## 13. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Incumplimiento de gases fluorados** | Muy alto — sanciones y modelo inviable | Resolver en Fase 0 con asesor. Instalación obligatoria (7.1) |
| **Vender sin stock real** | Alto — cancelaciones, reputación | Sincronización ≥2/día; margen de seguridad en stock; nunca publicar disponible con stock 1 |
| **Error en tarifa del proveedor** | Alto — venta a pérdida | Salvaguarda de variación ±25% con revisión manual |
| **Formato de Excel cambia sin aviso** | Medio — sincronización rota | Validación estricta con `pydantic` y alerta si fallan >5% de filas. Nunca publicar una sincronización parcialmente fallida |
| **Estacionalidad** | Medio | Junio-septiembre concentra la demanda de frío. Diversificar con aerotermia y calefacción para equilibrar el invierno |
| **Competencia en precio** | Alto | No competir por precio contra grandes superficies. Competir con asesoramiento, instalación y servicio |
| **Dependencia de un solo proveedor** | Medio | La arquitectura multi-proveedor lo mitiga desde el diseño |

---

## 14. Métricas a instrumentar desde el día 1

- Conversión global y por familia de producto.
- **% de pedidos con instalación** (indicador de salud del margen).
- **% de pedidos con financiación** (indicador de si la palanca funciona).
- Uso de la calculadora de frigorías → conversión de quien la usa vs quien no.
- Tasa de cancelación por falta de stock (**objetivo: <2%**).
- Margen real por pedido, con portes e instalación incluidos.
- Plazo real de entrega vs plazo prometido.

---

## 15. Decisiones pendientes

Estas bloquean el arranque de la Fase 1:

1. **¿Instalación propia, red de colaboradores o marketplace de instaladores?** Condiciona el punto 7.1 y por tanto el modelo entero.
2. **¿Se sirve a Baleares, Canarias, Ceuta y Melilla?** Afecta a fiscalidad y a tarifas de envío.
3. **¿Dropshipping directo del proveedor o almacén propio?**
4. **¿Se contempla canal B2B para instaladores?** Cambia el plan de Shopify necesario.
5. **Confirmar con el gestor:** calendario de Verifactu, obligaciones RAEE según el rol en la cadena, e impuesto de gases fluorados.

---

## Anexo: por qué el sincronizador es la inversión más segura

La tienda es reemplazable: migrar de Shopify a otra plataforma es incómodo pero factible. Lo que no se reemplaza fácil es:

- La base de fichas técnicas normalizadas (SEER, EPREL, cargas de refrigerante) construida modelo a modelo.
- Los adaptadores de cada proveedor, afinados contra sus formatos reales.
- El histórico de precios y de fiabilidad de proveedores.

Ese conjunto es el activo del proyecto. Debe vivir en base de datos propia, no dentro de Shopify.
