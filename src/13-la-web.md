# 13. La web climabaires.com

La web no es un folleto: es **la máquina de iniciar conversaciones de WhatsApp**. Todo lo que sigue está construido y funcionando en el repositorio; falta un solo dato para publicarla —el número real de WhatsApp— y las decisiones de la sección 14.

Son **21 páginas** de HTML estático: sin framework, sin base de datos, sin servidor que mantener. Eso importa por dos razones de negocio. La primera es el costo: alojarla cuesta cero y no hay nada que se caiga un sábado de diciembre. La segunda es la velocidad, que en captación paga: la portada carga en **1,3 segundos** en móvil, y cada décima de más es gente que se va antes de ver el botón.

## 13.1 El mapa del sitio

| Página | Qué hace en el negocio |
|---|---|
| **Inicio** | Propuesta de valor en una frase, foto de instalación real y presupuesto por WhatsApp arriba de todo |
| **Servicios** | Venta, instalación y posventa como un solo proveedor — el encuadre que sostiene el IIBB de la sección 7 |
| **Instalaciones** | Galería filtrable por zona y tipo, con ampliación de cada foto. Es la prueba de que sabemos hacerlo |
| **Calculadora de frigorías** | Herramienta de captación: resuelve una duda real y termina en un chat |
| **6 páginas de zona** | Núñez, Vicente López, San Isidro, Tigre, Nordelta y Pilar. SEO local **y** landings de Google Ads |
| **Blog** | Índice y notas. El motor de tráfico orgánico que no depende de la pauta |
| **Sobre nosotros** | La historia Málaga → Buenos Aires: el argumento de confianza de una marca sin historial local |
| **Contacto** | WhatsApp, agenda de visita técnica y formulario, en ese orden de prioridad |
| **Privacidad y Términos** | Requisito legal para publicar y **condición para anunciar en Google Ads** |
| **404** | Con salida a WhatsApp: un error no debería ser un callejón sin salida |

Las páginas de zona merecen un párrafo aparte porque son la pieza de mayor retorno. Cada una habla de su municipio con sus barrios y sus tiempos de respuesta, y sirve para dos cosas a la vez: posicionar en «instalación aire acondicionado + [zona]» sin pagar, y recibir el clic pago de esa misma búsqueda. **No hay landings duplicadas para Ads**: la página de zona es la landing, así que cada mejora de SEO mejora también la calidad del anuncio y baja el costo por clic.

## 13.2 Conversión: todo camino termina en WhatsApp

La regla editorial del sitio es que **ninguna franja larga de scroll queda sin un botón de WhatsApp** — y no es una buena intención, es una prueba automática: el control de calidad falla si alguna página deja más de dos pantallas y media sin un llamado a la acción. Sobre esa base:

- **Mensajes prellenados por contexto.** El botón no abre un chat vacío. Desde Nordelta escribe «estoy en Nordelta y quiero presupuesto de instalación»; desde la galería, «vi esta instalación en su web»; desde la calculadora, con los metros y las frigorías ya calculadas. Ignacio recibe el chat sabiendo de qué hablan.
- **Asistente de cuatro preguntas.** El botón flotante abre un cuestionario corto —nombre, zona, servicio, tipo de equipo— que arma el mensaje y lo pasa a WhatsApp. Convierte a quien no sabe qué escribir, que es la mitad de la gente. Sin backend y sin librerías: son unas líneas de JavaScript.
- **Barra fija en móvil** con «WhatsApp» y «Agendar visita», siempre a un pulgar de distancia.
- **Funcionan sin JavaScript.** Los enlaces de WhatsApp, el email y las redes están escritos en el HTML: si el JavaScript no carga, los botones siguen llevando al chat. Un lead perdido por un script que no cargó es un lead que se pagó y no llegó.

## 13.3 Las fotos son reales, y de dónde salen

La galería tiene **10 instalaciones propias con 6 destacadas en la portada**, y todas son de **Málaga**: instalaciones, conductos, mantenimiento y equipo en la nave. Es una decisión consciente y hay que decirla en voz alta antes de que la pregunte un socio: **no hay ni una foto de archivo, y no hay ni una instalación argentina, porque todavía no existe**. La primera instalación en el corredor norte entra a la galería el día que se haga.

Esto no es una debilidad del sitio: es exactamente lo que lo separa de la competencia local, que ilustra con catálogos del fabricante. Y está protegido por el proceso: el pipeline de fotos **borra los metadatos** de cada imagen antes de publicarla —hay domicilios de clientes ahí dentro— y el control de calidad del blog bloquea cualquier texto que invente un trabajo argentino que no ocurrió.

## 13.4 El blog que se publica solo

Cada tres días, una rutina programada elige el siguiente tema del calendario, escribe la nota siguiendo la guía de estilo, la pasa por un control de calidad y la publica. Hay **5 notas publicadas y 8 temas en cola**.

El control de calidad es lo que hace que esto sea utilizable y no un generador de relleno: rechaza castellano de España, instalaciones argentinas inventadas, precios en pesos que envejecen mal, plazos de garantía sin confirmar, enlaces rotos y notas demasiado cortas. Si el calendario se queda sin temas, **avisa y no publica nada** — no se inventa uno.

Para los socios la gobernanza es simple: para dirigir de qué habla el blog se edita el temario; para cambiar el tono, la guía de estilo. El SEO de contenidos es el único canal de captación cuyo costo marginal es cero y cuyo efecto se acumula: la nota que se publica en septiembre sigue trayendo consultas en diciembre, cuando el clic pago está en su precio más caro del año [F26].

## 13.5 El ecosistema Google, cableado de fábrica

El sitio ya está preparado para medir y para vender, con **Google Tag Manager como única puerta de medición**: GA4, Google Ads y el píxel de Meta se configuran como etiquetas dentro del contenedor, nunca pegando código suelto en las páginas. Eso significa que cambiar una medición no requiere tocar la web.

Cada clic que importa empuja su evento:

| Evento | Cuándo se dispara |
|---|---|
| `whatsapp_click` | Todo botón de WhatsApp, con el origen (hero, sección, menú, barra, galería, calculadora, asistente) |
| `agenda_click` | «Agendar visita técnica» |
| `calculadora_uso` | Con los metros, las frigorías y el equipo recomendado |
| `form_envio` · `tel_click` · `email_click` | Formulario y enlaces de contacto |
| `chatbot_inicio` · `chatbot_paso` | Apertura y cada respuesta del asistente — **el nombre no se envía**: sin datos personales en la medición |

`whatsapp_click` y `agenda_click` son las **conversiones principales de Google Ads**; `calculadora_uso`, la secundaria. Con eso, cada peso de pauta queda atribuido a chats y citas reales, no a visitas. Es la condición para poder aplicar de verdad el aprendizaje de los más de € 16.000 invertidos en la cuenta de Málaga: sin conversiones bien definidas, el algoritmo de Google optimiza hacia el clic barato en lugar de hacia el cliente.

**Las citas van a Calendar.** Los botones «Agendar visita» abren la página de reservas de Google Calendar de Ignacio; la reserva entra sola en su agenda y le llega por Gmail. En la página de contacto, además, está embebido el calendario de reservas. No hay que tocar código para que funcione el circuito de confirmación: es Workspace haciendo el trabajo de un CRM de agenda que no hay que pagar.

## 13.6 Cómo se ve

{{miniaturas_web}}
