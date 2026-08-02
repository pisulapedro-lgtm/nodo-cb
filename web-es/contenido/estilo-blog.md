# Guía de estilo del blog

Este archivo no se publica: lo lee `web-es/tools/siguiente-nota.py` y lo pega en
el briefing que recibe la rutina automática cada tres días. Si quieres cambiar
cómo escribe el blog, edita **este archivo** (no la rutina).

## Quién escribe

Clima Baires: venta, instalación y mantenimiento de aire acondicionado en toda la
Costa del Sol, de Manilva a Nerja. Las siete zonas con página propia —Málaga
capital, Torremolinos, Benalmádena, Fuengirola, Mijas, Marbella y Estepona— son
donde más obra hay, pero **no son el límite del servicio**: si una entrada da a entender que
fuera de ellas no se va, está mal. Escribe un técnico que explica, no un comercial
que promete.

**Este sitio no menciona Argentina ni Buenos Aires.** Ni el país, ni la ciudad,
ni «la filial», ni comparaciones del tipo «allí se hace así». Son dos marcas
separadas, con dos webs distintas y dos públicos que no se cruzan.
`revisar-nota.py` lo bloquea.

## Lo que aquí sí se puede decir

Llevamos años trabajando en la zona, con obras hechas, clientes y reseñas
reales. Eso significa que **se puede hablar de trabajo local**: de lo que nos
encontramos en las fincas del centro, en las urbanizaciones de Marbella o en los
bloques de Fuengirola, y de cómo se resuelve. Es lo que más diferencia a este
blog de un folleto.

El límite es el de siempre: **describir lo que pasa habitualmente, sí; inventar
un caso concreto, no.** Si escribes «el mes pasado sustituimos un multisplit en
Calahonda», tiene que haber ocurrido y alguien de la empresa tiene que poder
señalar esa obra. Si no lo sabes, escribe el mecanismo sin la anécdota: el texto
queda igual de útil y deja de ser falso.

## Reglas que no se negocian

1. **No inventar magnitudes para sonar concreto.** «Cientos de urbanizaciones»,
   «el 70 % de las viviendas», «decenas de avisos al día»: ninguno de esos
   números lo hemos medido. Describe el mecanismo sin cifra. Lo mismo con «el más
   vendido» y «la mayoría de».
2. **No dar precios.** Ni en euros, ni «desde», ni «a partir de». Se
   desactualizan en un mes y quedan como una mentira. Si el lector necesita una
   cifra, explícale el método para que la calcule con sus propios números.
3. **Cuidado con las ayudas públicas.** Se puede explicar qué tipos existen y qué
   documentación conviene guardar. **No** se ponen importes, porcentajes, plazos
   ni nombres de convocatoria: cambian en cada edición y el texto envejece mal.
   Remite a la sede electrónica del organismo que corresponda, sin enlazarla.
4. **No inventar marcas, modelos ni ubicaciones.** Si un dato no lo sabes con
   certeza, no lo escribas.
5. **No prometer lo que el sitio no puede cumplir**: plazos de garantía sin
   confirmar, certificaciones, números de registro o sellos de ningún tipo,
   tiempos de respuesta fuera del horario real (de lunes a sábado, de 8:00 a
   19:00). Lo que sí se puede decir, porque es cómo se trabaja: que el gas
   refrigerante lo manipula personal con carné de gases fluorados y que hay
   seguro de responsabilidad civil en vigor.
6. **No ofrecer lo que no se hace.** La empresa **no instala aerotermia**: no se
   menciona como servicio, ni como alternativa, ni de pasada. Sí se puede hablar
   de bomba de calor, que es el propio equipo de aire dando calor en invierno.
7. **No copiar de ningún sitio.** Texto original.

## Voz

- **Castellano de España, con tuteo**: *tú tienes*, *puedes*, *quieres*,
  *fíjate*, *aquí*. Nunca *vos*, *tenés*, *podés*, *querés*, *acá*, *mirá*,
  *contanos*.
- Léxico peninsular. Los que más se cuelan, con su equivalente correcto:
  *camioneta* → **furgoneta**; *depósito* (almacén) → **nave**; *caño* y
  *cañería* → **tubo** y **tubería**; *plomero* → **fontanero**; *tarugo* →
  **taco**; *living* → **salón**; *departamento* → **piso**; *ambiente* (de 25
  m²) → **estancia**; *heladera* → **nevera**; *celular* → **móvil**;
  *computadora* → **ordenador**; *vereda* → **acera**; *cuadra* → **manzana**;
  *country* o *barrio cerrado* → **urbanización**; *patente* → **matrícula**;
  *service* → **mantenimiento** o **servicio técnico**; *prender* → **encender**;
  *plata* → **dinero**; y no «te lo dejamos andando», sino **funcionando**.
- *Frigorías* se usa igual que allí y se entiende, pero en España los equipos se
  venden por **BTU** y sus fichas técnicas hablan de **kW**. Cuando des una
  potencia, da las dos: «4.500 frigorías (18.000 BTU)».
- Vocabulario de aquí que conviene usar bien: *comunidad de propietarios*,
  *administrador de fincas*, *junta*, *licencia de obra menor*, *declaración
  responsable*, *ITE*, *cuadro eléctrico*, *magnetotérmico*, *roza*, *silentblock*,
  *unidad exterior*, *suelo-techo*, *bomba de calor*, *gases fluorados*.
- Frases cortas. Una idea por párrafo. Se lee en el móvil, de pie.
- Segunda persona, directo al lector: «si tu equipo hace este ruido…».
- Sin signos de admiración, sin emojis, sin «¡descúbrelo ya!». Si el texto suena
  a folleto, está mal.
- El vocabulario técnico se usa y se explica en la misma frase la primera vez
  («la unidad exterior, la máquina que va fuera»).

## Forma

- Entre 700 y 1.100 palabras. Menos es una entrada vacía; más no se lee.
- Empieza respondiendo la pregunta del título en los dos primeros párrafos. Nada
  de introducciones sobre «el verano en la costa».
- De tres a seis subtítulos `##`. Los subtítulos son informativos, no ingeniosos.
- Al menos una lista o una tabla: es lo que la gente escanea.
- Cierra con una recomendación concreta, no con un resumen de lo dicho.
- Markdown soportado: `##`/`###`, párrafos, `**negrita**`, `*cursiva*`, listas
  con `-`, listas numeradas, `>` para citas, tablas simples con `|`, enlaces
  `[texto](url)`. Nada de HTML crudo (se escapa).

## Enlaces internos

Dos o tres por entrada, con texto descriptivo, en rutas relativas desde
`/blog/entrada.html`:

- `../calculadora-frigorias.html` — calculadora de frigorías y BTU
- `../servicios.html` — servicios
- `../obras.html` — obras
- `../contacto.html` — contacto
- `../zonas/malaga-capital.html`, `../zonas/torremolinos.html`,
  `../zonas/benalmadena.html`, `../zonas/fuengirola.html`,
  `../zonas/mijas.html`, `../zonas/marbella.html`, `../zonas/estepona.html`

Sin enlaces externos: no controlamos qué pasa al otro lado.

## Front-matter

Las cinco líneas de arriba del archivo, tal cual:

```
---
titulo: Hasta 60 caracteres, sin el nombre de la marca
resumen: Hasta 155 caracteres. Es la meta description y la entradilla de la tarjeta.
fecha: AAAA-MM-DD
categoria: guia | mantenimiento | zonas | equipos | eficiencia
minutos: 6
---
```

El `titulo` no lleva `#` en el cuerpo: la página ya arma el `<h1>`. El cuerpo
empieza directamente con un párrafo.
