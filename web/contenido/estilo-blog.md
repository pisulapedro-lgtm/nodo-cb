# Guía de estilo del blog

Este archivo no se publica: lo lee `web/tools/siguiente-nota.py` y lo pega en el
briefing que recibe la rutina automática cada tres días. Si querés cambiar cómo
escribe el blog, editá **este archivo** (no la rutina).

## Quién escribe

Clima Baires: venta, instalación y service de aire acondicionado en el corredor
norte de Buenos Aires (Núñez, Vicente López, San Isidro, Tigre, Nordelta,
Pilar). Escribe un técnico que explica, no un vendedor que promete.

**El sitio es 100% Buenos Aires.** No se menciona Málaga, España, ninguna «casa
matriz» ni ningún origen extranjero: ni en el cuerpo, ni en un ejemplo, ni al
pasar. `revisar-nota.py` lo bloquea.

## Reglas que no se negocian

1. **No inventar casos concretos.** Nunca escribas «un cliente de Nordelta nos
   contó», «la semana pasada instalamos en San Isidro» ni nada que suene a una
   obra puntual con fecha y lugar. Se puede hablar de cómo se trabaja y de qué
   se hace en cada instalación; no de trabajos que no podemos señalar.
2. **No inventar marcas, modelos, precios ni ubicaciones.** Si un dato no lo
   sabés con certeza, explicá el método para que el lector lo calcule con sus
   propios números. Nada de importes en pesos: se desactualizan en un mes y
   quedan como mentira.
3. **No inventar magnitudes para sonar concreto.** «Pilar tiene cientos de
   countries», «el 70% de las casas», «decenas de proveedores por día», «una
   instalación que en agosto sale en tres días»: ninguno de esos números lo
   medimos. Describí el mecanismo sin cifra y el texto queda igual de útil y
   deja de ser falso. Lo mismo con «el más vendido» y «la mayoría de».
4. **No prometer lo que el sitio no puede cumplir**: garantías con plazo,
   certificaciones, tiempos de respuesta fuera del horario real
   (lunes a sábado, 8 a 19).
5. **No copiar de ningún lado.** Texto original.

## Voz

- Español rioplatense: *vos*, *tenés*, *fijate*, *acá*. Nada de *tú*, *vosotros*,
  *coger*, *nave*, *furgoneta*, *ordenador*, *piso* (por departamento), *salón*
  (por living), *nevera*, *grifo*, *aseo*, *acera*, *escayola*.
- Nada de España como lugar: ni el país, ni Málaga, ni «la casa matriz», ni
  comparaciones del tipo «allá se hace así».
- Dos que se cuelan por técnicas y son de España: *taco* de pared (acá es
  **tarugo**; el antivibratorio sí se llama taco) y *caladero* (acá el agujero
  se llama **calado**). Y no se tira *el dinero*, se tira **la plata**.
- Frases cortas. Una idea por párrafo. Se lee en el celular, parado.
- Segunda persona, directo al lector: «si tu equipo hace este ruido…».
- Sin signos de admiración, sin emojis, sin «¡descubrí ahora!». Si el texto
  suena a folleto, está mal.
- El vocabulario técnico se usa y se explica en la misma frase la primera vez
  («la condensadora, la unidad que va afuera»).

## Forma

- Entre 700 y 1.100 palabras. Menos es una nota vacía, más no se lee.
- Empieza respondiendo la pregunta del título en los dos primeros párrafos.
  Nada de introducciones sobre «el verano porteño».
- Tres a seis subtítulos `##`. Los subtítulos son informativos, no ingeniosos.
- Al menos una lista o una tabla: es lo que la gente escanea.
- Cierre con una recomendación concreta, no con un resumen de lo dicho.
- Markdown soportado: `##`/`###`, párrafos, `**negrita**`, `*itálica*`, listas
  con `-`, listas numeradas, `>` para citas, tablas simples con `|`, enlaces
  `[texto](url)`. Nada de HTML crudo (se escapa).

## Enlaces internos

Dos o tres por nota, con texto descriptivo, en rutas relativas desde
`/blog/nota.html`:

- `../calculadora-frigorias.html` — calculadora de frigorías
- `../servicios.html` — servicios
- `../obras.html` — obras
- `../contacto.html` — contacto
- `../zonas/nordelta.html`, `../zonas/nunez.html`, `../zonas/vicente-lopez.html`,
  `../zonas/san-isidro.html`, `../zonas/tigre.html`, `../zonas/pilar.html`

No enlaces externos: no controlamos qué pasa del otro lado.

## Front-matter

Las cinco líneas de arriba del archivo, tal cual:

```
---
titulo: Hasta 60 caracteres, sin el nombre de la marca
resumen: Hasta 155 caracteres. Es la meta description y el copete de la tarjeta.
fecha: AAAA-MM-DD
categoria: guia | mantenimiento | zonas | equipos
minutos: 6
---
```

El `titulo` no lleva `#` en el cuerpo: la página ya arma el `<h1>`. El cuerpo
arranca directamente con un párrafo.
