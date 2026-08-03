# 9. El mercado y el go-to-market

Lanzamiento septiembre → rodaje octubre-noviembre → pico diciembre-febrero (la temporada concentra 40-50% de la facturación anual del rubro). El hueco competitivo detectado: **nadie en el corredor combina marca premium para countries + transparencia de precios online + posventa con contrato.** Ese es el posicionamiento.

## 9.1 Cuánto mercado hay

Antes de decidir tácticas conviene saber contra qué tamaño se está jugando. No hay una estadística publicada del mercado de climatización del corredor norte, así que se construye de abajo hacia arriba, **con la aritmética a la vista** para que se puedan discutir los supuestos en lugar de tener que creer la conclusión:

{{tabla_mercado}}

Tres lecturas, y la tercera cambia cómo se lee todo el resto del documento:

- **El corredor mueve unos {{eur:_cm.tam_eur}} al año** en equipos e instalación. De eso, la porción a la que de verdad le hablamos —vivienda premium con instalación certificada y factura— son unos {{eur:_cm.sam_eur}}.
- **La demanda es mayoritariamente de recambio, no de primera compra.** Con una penetración ya alta y un parque de {{_cm.parque}} equipos que dura una docena de años [F50], la mayor parte de los {{_cm.trabajos_anuales}} trabajos anuales son equipos que se mueren y hay que reemplazar. Eso es una buena noticia: el cliente de recambio ya sabe lo que quiere, compara menos y decide más rápido que el que compra por primera vez. Por eso la campaña de recambio de la sección 18 tiene la intención más alta de todas.
- **El plan captura el {{_cm.som_tam_pct}} % del mercado.** Las {{financiero.instalaciones_mes.0}} instalaciones de septiembre y las 161 del año no son una cuota de mercado: son lo que puede ejecutar una cuadrilla subcontratada. **La restricción de este negocio no es la demanda, es la capacidad de instalar** — lo mismo que dice el modelo financiero por otro camino en la sección 6.5. Para llegar a un 2 % del corredor harían falta {{_cm.instalaciones_al_2pct}} instalaciones al año, y ese número no lo limita el mercado sino cuántas cuadrillas se puedan coordinar con calidad.

> **Qué NO dice esto.** Que haya mercado no significa que esté disponible. Está repartido entre cadenas de retail que venden el equipo sin instalar bien, instaladores informales que compiten por precio y unas pocas empresas serias (sección 9.7). Lo que el dimensionamiento demuestra es que **no hace falta quitarle clientes a nadie** para llegar al plan: alcanza con capturar una fracción del recambio anual que ya existe.

## 9.2 SEO local por localidad (costo: $ 0 + constancia)

- **Google Business Profile como «empresa de área de servicio»**: se registra y verifica con el domicilio real de Ignacio (Calle Maure, Belgrano) — lo que facilita la verificación y ancla el perfil en el eje Belgrano-Núñez — pero con la **dirección oculta** al público y las 6 zonas de servicio cargadas (formato correcto para negocios a domicilio). Categorías de climatización, servicios con precio «desde», fotos geolocalizadas de cada instalación, mensajería con respuesta < 5 min.
- **La web ya está construida** (carpeta `/web` del repo, lista para publicar): landing por localidad — Núñez, Vicente López, San Isidro, Tigre, Nordelta, Pilar — con schema.org, calculadora de frigorías como imán de leads y botón WhatsApp en todo el sitio. Publicarla es tarea del día 8-10 del cronograma.
- Táctica copiada del competidor que mejor lo hace (Genz Clima): **publicar precios orientativos** — captura la búsqueda informacional y filtra curiosos.
- Objetivo 90 días: top 3 del «map pack» en ≥ 2 municipios antes del pico.

## 9.3 Estrategia countries y Nordelta (el canal de margen alto)

1. **Alta de proveedor en AVN Nordelta** (formulario online): exige AFIP al día, IIBB/CM, seguros con **cláusula de no repetición** y **cartera mínima de 2 clientes** [F25] → por eso las 2-3 instalaciones fundacionales de septiembre son un requisito de ingreso, no una promoción.
2. **Administraciones**: la AVN administra 56 consorcios; presentación formal con dossier (seguros, garantía escrita, checklist de instalación) + el contenido B2B de LinkedIn pensado para que las administraciones lo compartan.
3. **Arquitectos y estudios** de Tigre/Pilar: ronda de 10 presentaciones en octubre con propuesta de fee de recomendación / precio preferente de instalación.
4. **Instalación nueva**: el corredor entrega torres y barrios en 2026-2027 (Nordelta jul-2026 y dic-2027; corredor Remeros: Remeros Beach, Brickell, Sunny). Producto específico: **«pack unidad a estrenar»** — el departamento se entrega con preinstalación y el comprador necesita equipo + instalación el día de la mudanza.
5. **Medios de countries**: Revista Nordelta (bimestral, oficial) y guías barriales — pauta en octubre-noviembre (mediakit por pedir; presupuestado € 200 †) o, mejor, nota de caso de instalación a costo cero.
6. Requisito operativo no negociable: instaladores con AP vigente + no repetición cargados en los sistemas de acceso de cada barrio **antes** de agendar — un certificado vencido frena la instalación en la barrera.

## 9.4 Publicidad paga — dónde está el detalle

La inversión publicitaria del bloque D de la sección 5 y su continuación con cargo a la operación se planifican por completo en la **Parte V**: el embudo con números y el reparto por canal en la sección 17, las campañas de Google Ads listas para cargar en la 18, y Meta, los canales propios y el tablero de control en la 19.

Lo que conviene retener acá, porque condiciona todo el go-to-market: **la pauta cubre el {{_mk.cubierto_pct}} % de las instalaciones del plan y en el pico de diciembre menos de la mitad.** Las {{_mk.instalaciones_propias}} instalaciones restantes del año dependen del posicionamiento local, del perfil de empresa y de las reseñas — que tardan tres meses en madurar y por eso arrancan en septiembre.

## 9.5 MercadoLibre

Rol acotado: 3-5 publicaciones de equipos gama media/alta con «instalación premium incluida» como test (comisión 13-16% + IVA [F40]). Sirve de vidriera y para capturar demanda de equipos que luego compra instalación; no es el canal principal — el margen vive en la instalación, no en el marketplace.

## 9.6 Reseñas — el activo que decide el pico

Meta: **15-20 reseñas antes del 30 de noviembre**, a una o dos por semana. Es lo que empuja el perfil al top 3 del bloque de mapas justo antes de la temporada, y de ahí sale buena parte de las instalaciones que la pauta no paga. El procedimiento completo —enlace corto, QR en el remito, el pedido por WhatsApp a las 24-48 h, y qué está prohibido hacer— está en la sección 15.2; el papel que cumple dentro del embudo, en la 19.2.

Cada instalación genera además un reel, dos historias y una foto geolocalizada para el perfil de Google.

## 9.7 Competencia de referencia (auditada 01-08-2026)

| Competidor | Zona/foco | Su fuerte | Nuestro ángulo |
|---|---|---|---|
| Climadesign (Martínez) | Premium Pilar/Nordelta/Tigre | Termomecánica integral, marcas top | Es también nuestro mayorista candidato; su web no captura leads — nosotros somos digital-first |
| Genz Clima | CABA + GBA Norte | SEO + precios publicados | Copiar transparencia, superar en posventa con contrato |
| Aire Acondicionado SC | Zona norte | Respuesta 24 h, WhatsApp | Igualar velocidad + marca premium + countries |
| Climatización Norte (IG) | San Isidro | Instagram activo | Contenido de instalación real con mejor producción de marca |
| Instaladores individuales (ML/directorios) | Todo el corredor | Precio | No competimos por precio: competimos por confianza y posventa |
