# -*- coding: utf-8 -*-
"""Generador de páginas estáticas de climabaires.es.
Uso: python3 web-es/tools/generar.py   (desde la raíz del repo)
Regenera todos los .html a partir del layout y el contenido de PAGINAS.
Los .html generados son el artefacto desplegable: no requieren build en el hosting.

Este generador es hermano del de web/ (climabaires.com, Argentina) pero NO es una
traducción: es otro negocio, otro país y otro marco legal. Las dos diferencias de
fondo, que explican casi todos los cambios:

  · Aquí la empresa lleva años operando, con obras, clientes y reseñas reales. El
    sitio argentino tiene prohibido mostrar trabajos locales porque todavía no los
    hay; este los muestra con su ubicación real.
  · Aquí manda el RGPD, la LOPDGDD, la LSSI-CE y el TRLGDCU. Eso trae aviso legal
    obligatorio, consentimiento previo de cookies y 14 días de desistimiento.

Y una regla que va en la dirección contraria a la del sitio argentino: **este
sitio no menciona Argentina ni Buenos Aires**. Son dos marcas separadas.
"""
import os, re, sys, json
from datetime import date, datetime, timezone
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog as _blog          # noqa: E402  (necesita el sys.path de arriba)

RAIZ = os.path.join(os.path.dirname(__file__), '..')
DOMINIO = 'https://climabaires.es'

# ---------------- ENLACES DE WHATSAPP SIN JS ----------------
# El número sigue teniendo UN solo punto de configuración (objeto CB en
# assets/js/main.js). Aquí lo leemos para hornear un href real en cada CTA: si el
# JS no carga, los botones siguen abriendo WhatsApp con su mensaje preparado.
# main.js después reescribe esos mismos href (y añade la medición) sin cambiar el
# destino, así que no hay dato de contacto duplicado a mano.
AGENDA_FALLBACK = 'Hola Clima Baires, quiero concertar una visita técnica.'

# Identidad legal del prestador. En España la exige el artículo 10 de la LSSI-CE
# (Ley 34/2002) en toda web comercial, y sin ella no hay aviso legal válido.
# Mientras diga PENDIENTE, publicar.py no arma el paquete: son datos que sólo
# puede completar el titular del negocio.
EMPRESA = {
    'razon_social': 'PENDIENTE — denominación social',
    'cif': 'PENDIENTE — CIF/NIF',
    'domicilio': 'PENDIENTE — domicilio social',
    'registro': 'PENDIENTE — datos registrales (Registro Mercantil de Málaga, tomo, folio, hoja)',
    'responsable_datos': 'PENDIENTE — responsable del tratamiento (nombre y email de contacto)',
}

# Lo que aquí sí se puede decir y en el sitio argentino no: la antigüedad. Es un
# dato real del negocio, así que lo pone el titular; inventarlo sería justo el
# error que el proyecto evita.
#
# Lo que se quitó a propósito: el número de instalaciones y el número de registro
# como empresa instaladora habilitada. Se probaron como sellos en la franja de
# confianza y no convencieron —además obligaban a pedir dos datos más antes de
# publicar—, así que el sitio se apoya en lo que ya tiene: antigüedad, obra propia
# con foto, reseñas reales y cobertura. Si algún día se quieren de vuelta, es una
# entrada más en franja_confianza().
ANIOS_EXPERIENCIA = 'PENDIENTE — años de experiencia'

# Cobertura. El negocio da servicio en toda la Costa del Sol, no sólo en los seis
# municipios que tienen página propia: esos seis son donde más se trabaja y son
# las landings de Ads, pero el sitio no puede dar a entender que fuera de ellos no
# se va. De aquí salen la franja de confianza, la sección de zonas, el pie y las
# áreas de servicio de los datos estructurados.
COBERTURA = 'toda la Costa del Sol, de Manilva a Nerja'
# Las siete con página propia son las grandes ciudades de la costa entre Málaga y
# Estepona: es donde está el volumen y donde tiene sentido gastar campaña. Éstas
# son las demás, que se sirven igual pero no justifican una landing.
OTRAS_ZONAS = [
    'Manilva', 'Casares', 'Benahavís', 'Ojén', 'Alhaurín de la Torre', 'Cártama',
    'Coín', 'Rincón de la Victoria', 'Vélez-Málaga', 'Torrox', 'Nerja',
]

# Metros de tubería que entran en el precio cerrado (bloque «qué entra y qué se
# cobra aparte» de servicios.html). Es el único número del bloque y la promesa
# más concreta del sitio: publicarlo mal es peor que no publicarlo, así que
# publicar.py se niega a compilar mientras siga en PENDIENTE.
METROS_INCLUIDOS = 'PENDIENTE'

# Plazo de garantía de la mano de obra. El mínimo legal de conformidad del
# TRLGDCU (3 años para bienes desde 2022) cubre el equipo; esto es lo que
# garantiza la instalación, y lo decide la empresa.
GARANTIA_INSTALACION = 'PENDIENTE — plazo de garantía de la instalación'


def _json_contenido(nombre, por_defecto):
    ruta = os.path.join(RAIZ, 'contenido', nombre)
    if not os.path.exists(ruta):
        return por_defecto
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


FAQ_ZONAS = _json_contenido('faq-zonas.json', {}).get('zonas', {})

# Reseñas transcritas a mano desde la ficha de Google: nombre y fecha reales, y
# el enlace al perfil para que cualquiera las verifique. Es la única forma de
# mostrar el texto de las reseñas sin clave de API, sin coste y sin meter un
# widget de terceros (ver web-es/README.md → «Reseñas de Google»).
RESENAS = _json_contenido('resenas.json', {})


def _numero(valor):
    """Devuelve el número si el dato ya está cargado, o None si sigue PENDIENTE."""
    if isinstance(valor, (int, float)):
        return valor
    return None


RESENAS_PUNTUACION = _numero(RESENAS.get('puntuacion'))
RESENAS_TOTAL = _numero(RESENAS.get('total'))
RESENAS_LISTA = [r for r in RESENAS.get('resenas', []) if r.get('texto')]
# Google penaliza el marcado que no coincide con lo visible: el aggregateRating
# sólo sale si la puntuación y el número de reseñas son datos reales cargados.
HAY_RESENAS = bool(RESENAS_PUNTUACION and RESENAS_TOTAL and RESENAS_LISTA)


def _config_de_main_js():
    ruta = os.path.join(RAIZ, 'assets', 'js', 'main.js')
    with open(ruta, encoding='utf-8') as f:
        js = f.read()
    cfg = {}
    for clave in ('whatsapp', 'whatsappVisible', 'email', 'horario', 'instagram', 'linkedin', 'placeId'):
        m = re.search(r"%s:\s*'([^']*)'" % clave, js)
        if m is None:
            raise SystemExit('No pude leer CB.%s de assets/js/main.js' % clave)
        cfg[clave] = m.group(1)
    return cfg


CB = _config_de_main_js()
WSP_NUM = CB['whatsapp']
PLACE_ID = CB['placeId']

# Los tres enlaces que Google publica para una ficha, a partir del Place ID.
# Sin Place ID no se pintan: un enlace a una ficha inexistente es peor que nada.
URL_RESENAS = 'https://search.google.com/local/reviews?placeid=' + PLACE_ID if PLACE_ID else ''
URL_ESCRIBIR = 'https://search.google.com/local/writereview?placeid=' + PLACE_ID if PLACE_ID else ''
URL_MAPS = 'https://www.google.com/maps/place/?q=place_id:' + PLACE_ID if PLACE_ID else ''


def hornear_enlaces(html):
    """Reemplaza los href='#' de los CTA por enlaces reales de wa.me."""
    def enlace(mensaje):
        return 'https://wa.me/%s?text=%s' % (WSP_NUM, quote(mensaje))

    # target/rel horneados: el clic abre WhatsApp en otra pestaña y el documento
    # no se descarga, así el evento de conversión llega a salir hacia GTM
    html = re.sub(
        r'data-wsp="([^"]*)"([^>]*?)href="#"',
        lambda m: 'data-wsp="%s"%shref="%s" target="_blank" rel="noopener"' % (
            m.group(1), m.group(2), enlace(m.group(1))),
        html)
    html = re.sub(
        r'(data-agenda\b[^>]*?)href="#"',
        lambda m: '%shref="%s"' % (m.group(1), enlace(AGENDA_FALLBACK)),
        html)
    # email y redes: mismo criterio (main.js los reescribe con asunto por contexto)
    html = re.sub(r'(<a data-email[^>]*?)href="#"([^>]*)>(\s*)</a>',
                  lambda m: '%shref="mailto:%s"%s>%s</a>' % (m.group(1), CB['email'], m.group(2), CB['email']),
                  html)
    html = html.replace('<a data-ig href="#"', '<a data-ig href="%s"' % CB['instagram'])
    html = html.replace('<a data-li href="#"', '<a data-li href="%s"' % CB['linkedin'])
    # textos de contacto que hoy sólo escribe el JS
    html = html.replace('<span data-wsp-num></span>', '<span data-wsp-num>%s</span>' % CB['whatsappVisible'])
    html = html.replace('<strong data-wsp-num></strong>', '<strong data-wsp-num>%s</strong>' % CB['whatsappVisible'])
    html = html.replace('<span data-horario></span>', '<span data-horario>%s</span>' % CB['horario'])
    return html

# ---------------- FOTOS DE OBRAS ----------------
# Índice generado por tools/fotos.py (ver web-es/README.md → "Cómo añadir fotos").
# Si no existe, el sitio se genera igual con el hero de degradado y sin galería.
RUTA_INDICE_OBRAS = os.path.join(RAIZ, 'assets', 'img', 'obras', 'index.json')
try:
    with open(RUTA_INDICE_OBRAS, encoding='utf-8') as _f:
        _idx = json.load(_f)
    FOTOS, ZONAS_FOTO, TIPOS_FOTO = _idx['fotos'], _idx['zonas'], _idx['tipos']
except FileNotFoundError:
    FOTOS, ZONAS_FOTO, TIPOS_FOTO = [], {}, {}
HAY_FOTOS = bool(FOTOS)
DESTACADAS = [f for f in FOTOS if f.get('destacada')][:6]
PARES_AD = {}
for _f in FOTOS:
    if _f.get('par'):
        PARES_AD.setdefault(_f['par'], []).append(_f)
PARES_AD = {k: v for k, v in PARES_AD.items() if len(v) == 2}


def img_obra(foto, p='', sizes='(max-width: 560px) 100vw, (max-width: 900px) 50vw, 350px', lazy=True):
    """<img> responsive de una obra: srcset 800/1600, width/height (sin CLS), lazy."""
    base = f'{p}assets/img/obras/{foto["slug"]}'
    lz = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return (f'<img src="{base}-800.webp" srcset="{base}-800.webp 800w, {base}-1600.webp 1600w" '
            f'sizes="{sizes}" width="{foto["w800"]}" height="{foto["h800"]}" alt="{foto["alt"]}"{lz}>')


def pie_foto(foto):
    """Pie de foto. Aquí, a diferencia del sitio argentino, la obra lleva su
    ubicación real: es trabajo hecho en la Costa del Sol y decirlo es media
    venta. Mientras `fotos.py` no tenga la zona de esa foto, sale sólo la
    descripción técnica —nunca una ciudad inventada."""
    zona = foto.get('zona')
    if zona and zona in ZONAS_FOTO:
        return f'{foto["alt"]} · {ZONAS_FOTO[zona]}'
    return foto['alt']


# slug, nombre, comarca, intro, barrios, párrafo «especial»
ZONAS = [
    ('malaga-capital', 'Málaga capital', 'Málaga',
     'Del Centro Histórico a Teatinos: fincas antiguas con patio de luces, áticos con toda la fachada al sur y obra nueva en el este de la ciudad. Cada una pide una solución distinta.',
     ['Centro Histórico', 'La Malagueta', 'El Limonar', 'Pedregalejo', 'El Palo', 'Teatinos', 'Carretera de Cádiz'],
     'Trabajamos con la comunidad de propietarios desde el primer día: pedimos el acuerdo por escrito, respetamos las normas de fachada del edificio —en el centro protegido son estrictas— y protegemos zaguán, ascensor y escalera. En finca antigua estudiamos antes por dónde puede ir la tubería sin tocar elementos comunes.'),
    ('marbella', 'Marbella', 'Costa del Sol occidental',
     'De Nueva Andalucía a Elviria, pasando por San Pedro Alcántara: urbanizaciones con normas de estética propias, villas con mucha superficie acristalada y viviendas que se usan sólo parte del año.',
     ['Casco antiguo', 'Golden Mile', 'Puerto Banús', 'Nueva Andalucía', 'San Pedro Alcántara', 'Elviria', 'Las Chapas'],
     'Nos leemos la normativa de la urbanización antes de presupuestar: dónde admite la comunidad la unidad exterior, si exige celosía o cubrición y con qué acabado. Y si la vivienda se usa por temporadas, dejamos programado el mantenimiento para que el equipo no arranque en julio después de nueve meses parado.'),
    ('torremolinos', 'Torremolinos', 'Costa del Sol occidental',
     'La Carihuela, Playamar, Los Álamos: primera línea de playa casi todo. El aire salino no perdona una instalación hecha con material corriente, y aquí se nota en dos temporadas.',
     ['Centro', 'La Carihuela', 'Playamar', 'Los Álamos', 'Montemar', 'El Calvario'],
     'A pie de playa montamos con soportes galvanizados o de acero inoxidable y tornillería del mismo material, nunca hierro pintado, y recomendamos equipos con tratamiento anticorrosivo en la batería. En pisos de alquiler turístico, que trabajan todo el año, ajustamos la frecuencia de mantenimiento a ese uso y no al de una vivienda habitual.'),
    ('benalmadena', 'Benalmádena', 'Costa del Sol occidental',
     'Del pueblo a Benalmádena Costa hay trescientos metros de desnivel y dos climas distintos. Arroyo de la Miel concentra los bloques de vivienda; la costa, las torres con patio interior y la comunidad grande.',
     ['Arroyo de la Miel', 'Benalmádena Costa', 'Benalmádena Pueblo', 'Torrequebrada', 'Puerto Marina'],
     'En las torres de la costa la unidad exterior suele acabar en el patio interior o en una terraza compartida, y ahí la ventilación y el ruido son el problema real, no la potencia. Medimos el hueco antes de pedir el equipo y presentamos a la comunidad lo que nos pida: peso, medidas y nivel sonoro.'),
    ('fuengirola', 'Fuengirola', 'Costa del Sol occidental',
     'Los Boliches, Torreblanca, el centro: mucho bloque de los años setenta y ochenta con la instalación eléctrica justa y equipos que ya han cumplido su ciclo. Sustituir bien vale más que sustituir rápido.',
     ['Centro', 'Los Boliches', 'Torreblanca', 'Carvajal', 'El Boquetillo', 'Miramar'],
     'Antes de tocar nada miramos el cuadro eléctrico: en estos edificios es habitual que no haya circuito propio para el aire, con su magnetotérmico y su diferencial. Si hay que adecuarlo, se dice en la visita y va al presupuesto. Cuando la comunidad tiene la ITE en marcha, coordinamos para no montar sobre una fachada que se va a intervenir.'),
    ('estepona', 'Estepona', 'Costa del Sol occidental',
     'Del casco antiguo encalado a la Nueva Milla de Oro: mucha obra nueva pegada al mar, comunidades recién constituidas y un centro donde el ayuntamiento cuida la imagen de la calle hasta el último detalle.',
     ['Casco antiguo', 'Puerto deportivo', 'Nueva Milla de Oro', 'Cancelada', 'El Padrón', 'Selwo', 'Costalita'],
     'Estepona ha crecido a base de obra nueva junto a la playa, y eso cambia dos cosas. Muchas viviendas se entregan con preinstalación hecha por la promotora, que conviene revisar antes de comprar el equipo: no siempre está dimensionada para la potencia que vas a necesitar. Y casi todas están en comunidades con normas de fachada, a menudo recién estrenadas. Pedimos los planos a la promotora o a la administración antes de presupuestar. En el casco antiguo, donde las calles encaladas son parte del atractivo, buscamos siempre una salida que no se vea desde la vía pública.'),
    ('mijas', 'Mijas', 'Costa del Sol occidental',
     'Mijas Pueblo, Las Lagunas, La Cala, Calahonda y Riviera del Sol: villas y adosados repartidos por urbanizaciones con mucha parcela, donde el tendido entre las dos unidades casi nunca es corto.',
     ['Mijas Pueblo', 'Las Lagunas', 'La Cala de Mijas', 'Riviera del Sol', 'Calahonda', 'Mijas Golf'],
     'En vivienda unifamiliar con parcela el recorrido de tubería manda sobre el presupuesto, así que lo medimos en la visita y no por teléfono. Acompañamos obra nueva y reforma desde la preinstalación —tubería, desagüe y línea eléctrica antes del enlucido— hasta la puesta en marcha. Y como muchas de estas casas se usan también en invierno, dimensionamos mirando el rendimiento en modo calor y no sólo el frío.'),
]

SVC_ICONS = {
    'venta': '<svg viewBox="0 0 24 24"><path d="M12 2 2 7v2h20V7L12 2zm-8 9v8h4v-8H4zm6 0v8h4v-8h-4zm6 0v8h4v-8h-4zM2 21h20v2H2z"/></svg>',
    'instalacion': '<svg viewBox="0 0 24 24"><path d="M22.7 19-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L8 6 6 8 1.6 3.6C.4 6 .9 9 2.9 11c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.3z"/></svg>',
    'mantenimiento': '<svg viewBox="0 0 24 24"><path d="M12 1 3 5v6c0 5.6 3.8 10.7 9 12 5.2-1.3 9-6.4 9-12V5l-9-4zm-1.1 15.4-3.5-3.5 1.4-1.4 2.1 2.1 4.9-4.9 1.4 1.4-6.3 6.3z"/></svg>',
}

def layout(depth, titulo, descripcion, contenido, canonical, jsonld=None, activo='',
           og_image=None, pagina_id='', zona_nombre='', wsp_barra=None):
    p = '../' * depth
    def act(k):
        return ' class="activo"' if activo == k else ''
    ld = ('<script type="application/ld+json">%s</script>' % json.dumps(jsonld, ensure_ascii=False)) if jsonld else ''
    # WhatsApp es el canal nº1: al compartir un enlace tiene que verse una obra,
    # no el isotipo. Si la página no trae uno propio, cae en la foto de portada.
    por_defecto = f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else f'{DOMINIO}/assets/img/icon-512.png'
    og = og_image or por_defecto
    barra_msj = wsp_barra or 'Hola Clima Baires, quiero pedir presupuesto.'
    redes = ''
    if CB['instagram'] or CB['linkedin']:
        enlaces = []
        if CB['instagram']:
            enlaces.append('<a data-ig href="#" rel="noopener">Instagram</a>')
        if CB['linkedin']:
            enlaces.append('<a data-li href="#" rel="noopener">LinkedIn</a>')
        redes = '<li>%s</li>' % ' · '.join(enlaces)
    zonas_pie = ''.join(f'<li><a href="{p}zonas/{s}.html">{n}</a></li>' for s, n, *_ in ZONAS)
    return f'''<!DOCTYPE html>
<html lang="es-ES">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="Clima Baires">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0058B3">
<meta name="color-scheme" content="light">
<link rel="icon" type="image/png" sizes="48x48" href="{p}assets/img/favicon-48.png">
<link rel="apple-touch-icon" href="{p}assets/img/icon-192.png">
<link rel="stylesheet" href="{p}assets/css/styles.css">
<link rel="alternate" type="application/rss+xml" title="Blog de Clima Baires" href="{p}blog/rss.xml">
<script>window.dataLayer = window.dataLayer || [];</script>
{ld}
</head>
<body data-pagina="{pagina_id}" data-zona="{zona_nombre}">
<header class="top">
  <div class="contenedor top-inner">
    <a class="logo" href="{p}index.html" aria-label="Clima Baires — inicio">
      <img src="{p}assets/img/logo.webp" alt="Clima Baires" width="145" height="44">
    </a>
    <nav class="nav">
      <a href="{p}index.html"{act('inicio')}>Inicio</a>
      <a href="{p}servicios.html"{act('servicios')}>Servicios</a>
      <a href="{p}obras.html"{act('obras')}>Obras</a>
      <a href="{p}blog/"{act('blog')}>Blog</a>
      <a href="{p}index.html#zonas"{act('zonas')}>Zonas</a>
      <a href="{p}calculadora-frigorias.html"{act('calc')}>Calculadora</a>
      <a href="{p}sobre-nosotros.html"{act('nosotros')}>Nosotros</a>
      <a href="{p}contacto.html"{act('contacto')}>Contacto</a>
      <a class="boton celeste" data-wsp="Hola Clima Baires, quiero pedir presupuesto." data-origen="menu" href="#">Pedir presupuesto</a>
    </nav>
    <button class="hamburguesa" aria-label="Abrir menú"><span></span><span></span><span></span></button>
  </div>
</header>

{contenido}

<footer class="pie">
  <div class="contenedor">
    <div class="pie-grilla">
      <div>
        <img class="logo-pie" src="{p}assets/img/logo-blanco.webp" alt="Clima Baires" width="151" height="46" loading="lazy">
        <p>Venta, instalación y posventa de aire acondicionado en {COBERTURA}. Tu confort, nuestra prioridad.</p>
      </div>
      <div>
        <h2>Servicios</h2>
        <ul>
          <li><a href="{p}servicios.html#venta">Venta de equipos</a></li>
          <li><a href="{p}servicios.html#instalacion">Instalación</a></li>
          <li><a href="{p}servicios.html#mantenimiento">Mantenimiento y posventa</a></li>
          <li><a href="{p}obras.html">Obras recientes</a></li>
          <li><a href="{p}blog/">Blog</a></li>
          <li><a href="{p}calculadora-frigorias.html">Calculadora de frigorías</a></li>
        </ul>
      </div>
      <div>
        <h2>Zonas</h2>
        <ul>
          {zonas_pie}
        </ul>
      </div>
      <div>
        <h2>Contacto</h2>
        <ul>
          <li>WhatsApp: <span data-wsp-num></span></li>
          <li><a data-email href="#"></a></li>
          <li><span data-horario></span></li>
          {redes}
        </ul>
      </div>
    </div>
    <div class="legal">
      <span>© <span data-anio></span> Clima Baires · {EMPRESA['razon_social']} · CIF {EMPRESA['cif']}</span>
      <span><a href="{p}aviso-legal.html">Aviso legal</a> · <a href="{p}privacidad.html">Privacidad</a> · <a href="{p}cookies.html">Cookies</a> · <a href="{p}terminos.html">Términos y condiciones</a> · <button class="pie-cookies" type="button" data-cookies-abrir>Preferencias de cookies</button></span>
    </div>
    <div class="legal" style="border:0;padding-top:8px">
      <span>Damos servicio en {COBERTURA}. Donde más trabajamos: Málaga capital · Marbella · Torremolinos · Benalmádena · Fuengirola · Mijas · {' · '.join(OTRAS_ZONAS)}</span>
    </div>
  </div>
</footer>

<div class="barra-movil">
  <a class="bm-wsp" data-wsp="{barra_msj}" data-chat data-origen="barra" href="#">WhatsApp</a>
  <a class="bm-agenda" data-agenda data-origen="barra" href="#">Agendar visita</a>
</div>

<div class="nudge" id="nudge" hidden>
  <button class="nudge-texto" type="button">¿Te pasamos presupuesto hoy?</button>
  <button class="nudge-cerrar" type="button" aria-label="Cerrar aviso">×</button>
</div>

<div class="chat" id="chat" hidden role="dialog" aria-label="Asistente de Clima Baires">
  <div class="chat-cabecera">
    <img src="{p}assets/img/avatar-chat.png" alt="" width="34" height="34" loading="lazy">
    <div><strong>Clima Baires</strong><span data-respuesta>Respondemos en minutos</span></div>
    <button class="chat-cerrar" type="button" aria-label="Cerrar chat">×</button>
  </div>
  <div class="chat-mensajes" id="chat-mensajes" aria-live="polite"></div>
  <div class="chat-pie" id="chat-pie"></div>
</div>

<button class="wsp-flotante" type="button" data-origen="flotante" aria-label="Habla con nosotros por WhatsApp">
  <svg viewBox="0 0 32 32"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.1.6 4.2 1.7 6L4 29l8.2-1.6c1.2.6 2.5.9 3.8.9 6.6 0 12-5.4 12-12S22.6 3 16 3zm6.1 16.9c-.3.8-1.5 1.5-2.1 1.6-.6.1-1.3.2-3.6-.8-3-1.2-4.9-4.3-5.1-4.5-.1-.2-1.2-1.6-1.2-3.1s.8-2.2 1-2.5c.3-.3.6-.4.8-.4h.6c.2 0 .4 0 .7.5.3.6.9 2.1.9 2.3.1.2.1.3 0 .5-.1.2-.1.3-.3.5l-.4.5c-.2.2-.3.4-.1.7.2.3.9 1.5 2 2.4 1.4 1.2 2.5 1.6 2.9 1.8.3.2.5.1.7-.1l1.1-1.3c.2-.3.5-.2.8-.1l2.3 1.1c.3.2.5.2.6.4 0 .1 0 .8-.3 1.5z"/></svg>
  <span class="wsp-texto">Escríbenos</span>
</button>

<div class="cookies" id="cookies" hidden role="dialog" aria-label="Consentimiento de cookies">
  <div class="cookies-in">
    <p>Usamos cookies propias para que el sitio funcione y, sólo si nos das permiso, cookies de Google para medir el tráfico y la publicidad. Ese mismo permiso es el que carga el mapa y la agenda de citas. Puedes cambiar de idea cuando quieras desde el pie de página. Todo el detalle, en la <a href="{p}cookies.html">política de cookies</a>.</p>
    <div class="cookies-botones">
      <button class="ck-rechazar" type="button">Rechazar</button>
      <button class="ck-aceptar" type="button">Aceptar</button>
    </div>
  </div>
</div>

<script src="{p}assets/js/main.js"></script>
</body>
</html>
'''

def tarjeta_servicio(anchor, icono, titulo, texto, items, p=''):
    lista = ''
    if items:
        lista = '<ul class="lista-check">%s</ul>' % ''.join(f'<li>{i}</li>' for i in items)
    return f'''<div class="tarjeta" id="{anchor}">
      <div class="icono">{SVC_ICONS[icono]}</div>
      <h3>{titulo}</h3>
      <p>{texto}</p>
      {lista}
    </div>'''

def jsonld_local(nombre, url, zona=None, con_rating=False):
    """Ficha del negocio. Siempre el MISMO @id: sin él, Google leía una empresa
    distinta por página en vez de una con muchas páginas.

    `con_rating` sólo lo activan las páginas que además MUESTRAN las reseñas.
    Google exige que la puntuación marcada esté visible en esa misma página: un
    aggregateRating en las trece sería marcado sin respaldo, que es motivo de
    penalización, no de estrellas."""
    # areaServed: cuando la página no es de una zona concreta se declaran los seis
    # municipios con landing, los demás en los que se trabaja y la comarca entera.
    # Declarar sólo seis contradiría lo que dice el propio texto de la página.
    areas = ([z[1] for z in ZONAS] + OTRAS_ZONAS + ['Costa del Sol', 'Provincia de Málaga']
             if zona is None else [zona])
    ficha = {
        '@context': 'https://schema.org',
        '@type': 'HVACBusiness',
        '@id': DOMINIO + '/#negocio',
        'name': 'Clima Baires',
        'url': DOMINIO + '/',
        'image': DOMINIO + '/assets/img/obras/og-home.jpg' if HAY_FOTOS else DOMINIO + '/assets/img/icon-512.png',
        'description': nombre,
        'email': CB['email'],
        'priceRange': '$$',
        'areaServed': [{'@type': 'Place', 'name': a} for a in areas],
        'knowsAbout': ['aire acondicionado', 'instalación de split', 'mantenimiento de climatización',
                       'bomba de calor', 'climatización residencial'],
        'openingHours': 'Mo-Sa 08:00-19:00',
    }
    # Datos que sólo entran cuando son reales: un marcado que no coincide con lo
    # visible es una penalización, no una ventaja.
    if 'PENDIENTE' not in EMPRESA['razon_social']:
        ficha['legalName'] = EMPRESA['razon_social']
    if 'PENDIENTE' not in EMPRESA['cif']:
        ficha['taxID'] = EMPRESA['cif']
    if 'PENDIENTE' not in EMPRESA['domicilio']:
        ficha['address'] = {'@type': 'PostalAddress', 'streetAddress': EMPRESA['domicilio'],
                            'addressCountry': 'ES'}
    if HAY_RESENAS and con_rating:
        ficha['aggregateRating'] = {
            '@type': 'AggregateRating',
            'ratingValue': RESENAS_PUNTUACION,
            'reviewCount': RESENAS_TOTAL,
            'bestRating': 5,
            'worstRating': 1,
        }
    return ficha


def jsonld_migas(items):
    """BreadcrumbList: Google la usa para mostrar la ruta en vez de la URL cruda."""
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n,
             **({'item': DOMINIO + u} if u else {})}
            for i, (n, u) in enumerate(items)
        ],
    }


def jsonld_faq(pares):
    """FAQPage: habilita el desplegable de preguntas en los resultados."""
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {'@type': 'Question', 'name': p,
             'acceptedAnswer': {'@type': 'Answer', 'text': r}}
            for p, r in pares
        ],
    }


def jsonld_servicio(nombre, descripcion, zona=None):
    """Service: describe qué se presta y dónde, atado al mismo negocio."""
    areas = ([z[1] for z in ZONAS] + OTRAS_ZONAS + ['Costa del Sol']
             if zona is None else [zona])
    return {
        '@context': 'https://schema.org',
        '@type': 'Service',
        'serviceType': nombre,
        'description': descripcion,
        'provider': {'@id': DOMINIO + '/#negocio'},
        'areaServed': [{'@type': 'Place', 'name': a} for a in areas],
        'availableChannel': {
            '@type': 'ServiceChannel',
            'serviceUrl': DOMINIO + '/contacto.html',
            'servicePhone': {'@type': 'ContactPoint', 'contactType': 'sales', 'url': 'https://wa.me/' + WSP_NUM},
        },
    }


# ---------------- CONTENIDOS ----------------

def pagina_index():
    chips = ''.join(f'<a href="zonas/{slug}.html">{nombre}</a>' for slug, nombre, *_ in ZONAS)
    escena = ''
    if HAY_FOTOS:
        escena = '''
  <div class="hero-esc" aria-hidden="true">
    <div class="hero-esc-m">
      <div class="hero-esc-int">
        <img class="hero-foto" src="assets/img/obras/instalacion-cassette-oficina-01-800.webp"
             srcset="assets/img/obras/instalacion-cassette-oficina-01-800.webp 648w,
                     assets/img/obras/instalacion-cassette-oficina-01-1600.webp 1295w"
             sizes="(max-width: 900px) 100vw, 64vw"
             width="1295" height="1600" alt="" fetchpriority="high" decoding="async">
      </div>
    </div>
    <span class="hero-chip"><b>38°</b> <i>fuera</i> → <b>24°</b> <i>dentro</i></span>
  </div>

  <div class="hero-halo" aria-hidden="true"></div>
  <div class="hero-dial" aria-hidden="true"><u>24°</u><s>dentro</s><em>38°</em></div>'''
    c = f'''
<section class="hero">
  <div class="contenedor hero-caja">
    <div class="hero-txt">
      <p class="hero-kicker"><span class="hero-copo">❄</span><b>Aire acondicionado · Costa del Sol</b><i></i></p>
      <h1 class="hero-tit">Tu casa a <em>24°</em>,<br>todo el verano.</h1>
      <p class="hero-sub">Equipo, instalación y posventa en {COBERTURA}. <b>Presupuesto cerrado en el día.</b></p>
      <div class="hero-acciones">
        <a class="hero-cta" data-wsp="Hola Clima Baires, quiero presupuesto de equipo más instalación." data-origen="hero" href="#">
          {WSP_SVG_CTA}
          Pedir presupuesto
        </a>
        <a class="hero-cta2" href="calculadora-frigorias.html">Calcular frigorías <span>→</span></a>
      </div>
    </div>
  </div>

  <div class="hero-regla" aria-hidden="true">
    <div class="contenedor hero-regla-in">
      <span class="izq"><b>Obra propia</b> · Cassette de 4 vías en oficina</span>
    </div>
  </div>
{escena}
</section>

{franja_marcas()}
{franja_confianza()}
<section class="seccion" id="servicios">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Qué hacemos</span><h2>Vender, instalar, responder.</h2></div>
    <div class="grilla tres" style="margin-top:30px">
      {tarjeta_servicio('venta', 'venta', 'Venta de equipos', 'La potencia justa para tu estancia. Un solo precio: equipo, materiales e instalación.', [])}
      {tarjeta_servicio('instalacion', 'instalacion', 'Instalación sin atajos', 'Vacío de la tubería, prueba de estanqueidad y obra limpia. Siempre.', [])}
      {tarjeta_servicio('mantenimiento', 'mantenimiento', 'Posventa de verdad', 'Seguimos estando después de cobrar: mantenimiento anual y garantía por escrito.', [])}
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 40px">{cinta_cta('¿Cuál de los tres necesitas? Pregúntanos sin compromiso.', 'Hola Clima Baires, quiero hacer una consulta sobre vuestros servicios.', 'Preguntar por WhatsApp')}
</section>

<section class="seccion alterna" id="zonas">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Dónde trabajamos</span><h2>Toda la Costa del Sol</h2>
    <p class="intro">De Manilva a Nerja, más el interior cercano. Estas seis zonas tienen su propia página porque son donde más obra tenemos:</p></div>
    <div class="zona-chips centrado" style="justify-content:center; margin-top:24px">{chips}</div>
    <p class="centrado nota" style="margin-top:24px">Y damos servicio igualmente en {otras_zonas_texto()}. Si tu municipio no aparece, escríbenos: casi siempre llegamos.</p>
  </div>
</section>

<section class="seccion" style="padding:36px 0 40px">{cinta_cta('Cuéntanos qué quieres climatizar y te pasamos precio hoy.', 'Hola Clima Baires, quiero presupuesto de equipo más instalación.')}
</section>
{seccion_ultimas_obras()}
{seccion_resenas(alterna=False, p='')}
{seccion_ultimas_blog()}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>¿Instalamos antes del calor?</h2><p>Reserva tu instalación con tiempo: en temporada alta los buenos huecos vuelan.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero reservar una instalación antes del verano." data-origen="seccion" href="#">Hablar por WhatsApp</a>
    </div>
  </div>
</section>
'''
    og = f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else None
    return layout(0, 'Aire acondicionado en Málaga y toda la Costa del Sol | Clima Baires',
        'Venta, instalación y posventa de aire acondicionado en toda la Costa del Sol, de Manilva a Nerja. Presupuesto por WhatsApp el mismo día.',
        c, f'{DOMINIO}/', jsonld_local('Venta, instalación y posventa de aire acondicionado en toda la Costa del Sol, de Manilva a Nerja.', DOMINIO + '/', con_rating=True), 'inicio',
        og_image=og, pagina_id='index')


# slug, nombre para el alt, ancho en px a 30 px de alto (evita CLS al cargar)
# Sólo marcas que se venden en España: las argentinas del sitio hermano (BGH,
# Surrey) no pintan nada aquí, y listar una marca que no se sirve es la primera
# promesa que se rompe.
MARCAS = [
    ('daikin', 'Daikin', 142), ('mitsubishi', 'Mitsubishi Electric', 102), ('lg', 'LG', 68),
    ('samsung', 'Samsung', 90), ('midea', 'Midea', 78), ('johnson', 'Johnson', 144),
]

WSP_SVG_CTA = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95'
               'L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2Z'
               'm5.8 14.06c-.25.69-1.44 1.32-1.99 1.37-.53.05-1.02.24-3.44-.72-2.9-1.14-4.74-4.11-4.88-4.3-.14-.19-1.16-1.54-1.16-2.94'
               's.73-2.09 1-2.37c.26-.29.57-.36.76-.36.19 0 .38 0 .55.01.18.01.41-.07.64.49.24.57.81 1.97.88 2.11.07.14.12.31.02.5'
               '-.09.19-.14.31-.28.48-.14.16-.3.37-.42.49-.14.14-.29.29-.12.57.16.29.73 1.2 1.56 1.94 1.07.96 1.98 1.25 2.26 1.39'
               '.28.14.45.12.61-.07.17-.19.71-.83.9-1.11.19-.29.38-.24.64-.14.26.09 1.65.78 1.94.92.28.14.47.21.54.33.07.12.07.69-.18 1.38Z"/></svg>')

WSP_SVG = ('<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.1.6 4.2 1.7 6L4 29l8.2-1.6'
           'c1.2.6 2.5.9 3.8.9 6.6 0 12-5.4 12-12S22.6 3 16 3zm6.1 16.9c-.3.8-1.5 1.5-2.1 1.6-.6.1-1.3.2-3.6-.8-3-1.2-4.9-4.3-5.1-4.5'
           '-.1-.2-1.2-1.6-1.2-3.1s.8-2.2 1-2.5c.3-.3.6-.4.8-.4h.6c.2 0 .4 0 .7.5.3.6.9 2.1.9 2.3.1.2.1.3 0 .5-.1.2-.1.3-.3.5l-.4.5'
           'c-.2.2-.3.4-.1.7.2.3.9 1.5 2 2.4 1.4 1.2 2.5 1.6 2.9 1.8.3.2.5.1.7-.1l1.1-1.3c.2-.3.5-.2.8-.1l2.3 1.1c.3.2.5.2.6.4 0 .1 0 .8-.3 1.5z"/></svg>')


def acciones_cabecera(mensaje, primario='Pedir presupuesto', p='', secundario=None):
    """CTA inmediatamente bajo el título: en móvil tiene que entrar en el primer
    pantallazo (las páginas de zona son las landings de Google Ads)."""
    segundo = secundario or f'<a class="boton fantasma" href="{p}calculadora-frigorias.html">Calcular frigorías</a>'
    return f'''<div class="acciones-cabecera">
      <a class="boton verde" data-wsp="{mensaje}" data-origen="hero" href="#">{primario}</a>
      {segundo}
    </div>'''


def cinta_cta_suelta(titulo, mensaje, boton='Escríbenos por WhatsApp', origen='cinta'):
    """La cinta sin el contenedor: para meterla dentro de un bloque que ya tiene
    su propio ancho (el cuerpo de una entrada del blog, por ejemplo)."""
    return f'''<div class="cinta-cta">
    {WSP_SVG}
    <p>{titulo}</p>
    <a class="boton verde" data-wsp="{mensaje}" data-origen="{origen}" href="#">{boton}</a>
  </div>'''


def cinta_cta(titulo, mensaje, boton='Escríbenos por WhatsApp'):
    """Cinta compacta de conversión: ninguna franja larga de scroll sin CTA."""
    return f'''
<div class="contenedor">
  {cinta_cta_suelta(titulo, mensaje, boton)}
</div>'''


def otras_zonas_texto():
    """«A, B, C y D» — los municipios sin página propia, en prosa."""
    return ', '.join(OTRAS_ZONAS[:-1]) + ' y ' + OTRAS_ZONAS[-1]


def franja_marcas(p=''):
    logos = ''.join(
        f'<img src="{p}assets/img/marcas/{slug}.png" alt="{nombre}" width="{ancho}" height="30" loading="lazy">'
        for slug, nombre, ancho in MARCAS)
    # la pista se duplica para que el bucle no tenga costura; la copia no se
    # anuncia dos veces a los lectores de pantalla
    copia = re.sub(r'alt="[^"]*"', 'alt="" aria-hidden="true"', logos)
    return f'''<div class="franja-marcas" aria-label="Marcas que instalamos">
  <div class="marcas-carrusel">
    <div class="marcas-pista">
      {logos}{copia}
    </div>
  </div>
</div>'''


def franja_confianza():
    """Las tres cosas que este negocio puede afirmar sin pedirle un número a
    nadie: los años que lleva instalando aquí, hasta dónde llega y que la obra
    que enseña es propia.

    Aquí estuvieron el número de instalaciones y el de empresa instaladora
    habilitada. Se quitaron: como sellos no aportaban lo que costaban —dos datos
    más que pedir antes de publicar— y el segundo, sin el número al lado, no
    prueba nada. Lo que queda son afirmaciones que se sostienen solas."""
    items = [
        ('Años instalando en la Costa del Sol', ANIOS_EXPERIENCIA),
        ('De Manilva a Nerja, y el interior cercano', 'Toda la Costa del Sol'),
        ('Las fotos de obra son nuestras, hechas aquí', 'Obra propia'),
    ]
    # El dato va en un <p> con peso, no en un <h3>: esta franja se inserta justo
    # debajo del <h1> de la portada y un encabezado de nivel 3 ahí abre un salto
    # h1→h3 que el QA rechaza, con razón: no es una sección, es un dato suelto.
    tarjetas = ''.join(
        f'<div class="tarjeta"><p class="credencial-valor">{v}</p>'
        f'<p class="credencial-etiqueta">{t}</p></div>' for t, v in items)
    return f'''
<section class="seccion" style="padding:46px 0 10px">
  <div class="contenedor">
    <div class="grilla tres">{tarjetas}</div>
    <p class="centrado nota" style="margin-top:18px">Trabajamos a domicilio en {COBERTURA}. Las seis zonas con página propia son donde más obra tenemos, pero no son un límite: si tu municipio no está, pregúntanos.</p>
  </div>
</section>'''


def estrellas(puntuacion):
    """Estrellas visibles. Se redondea al entero más próximo —no hay media
    estrella: el glifo no existe en Poppins y saldría como un cuadrado— y el
    valor exacto va al lado en texto. La estrella es el adorno, el número es el
    dato."""
    llenas = max(0, min(5, round(puntuacion)))
    return '★' * llenas + '☆' * (5 - llenas)


def seccion_resenas(alterna=True, p=''):
    """Reseñas reales de la ficha de Google, transcritas a mano.

    Google no deja incrustar el texto de las reseñas con un iframe: el mapa
    embebido muestra la puntuación pero no lo que dice la gente, y la Places API
    pide clave y facturación. La opción sin coste ni dependencias es transcribir
    dos o tres con nombre y fecha reales y dejar el enlace al perfil para que
    cualquiera las verifique — que es lo que hace este bloque."""
    if not HAY_RESENAS:
        return f'''
<section class="seccion{' alterna' if alterna else ''}" id="resenas">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Lo que dicen</span><h2>Reseñas de Google</h2></div>
    <div class="tarjeta" style="margin-top:24px">
      <h3>PENDIENTE — reseñas reales de la ficha de Google</h3>
      <p>Aquí van la puntuación, el número de reseñas y dos o tres textos transcritos con nombre y fecha reales, más el enlace al perfil para verificarlas. Se cargan en <code>contenido/resenas.json</code> y el Place ID en <code>CB.placeId</code> (assets/js/main.js).</p>
      <p class="nota" style="margin-top:10px">Hasta entonces no se publica ningún <code>aggregateRating</code>: Google penaliza el marcado que no coincide con lo que se ve en la página.</p>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Quieres que trabajemos igual en tu casa? Cuéntanos qué necesitas.', 'Hola Clima Baires, quiero pedir presupuesto de equipo más instalación.', 'Pedir presupuesto')}
</section>'''
    tarjetas = ''.join(f'''
      <figure class="resena">
        <span class="estrellas" aria-hidden="true">{estrellas(r.get('puntuacion', 5))}</span>
        <blockquote>«{r['texto']}»</blockquote>
        <figcaption>{r['autor']} · {r['fecha']}</figcaption>
      </figure>''' for r in RESENAS_LISTA[:3])
    enlaces = ''
    if URL_RESENAS:
        enlaces = f'''
    <div class="centrado" style="margin-top:28px; display:flex; gap:14px; justify-content:center; flex-wrap:wrap">
      <a class="boton fantasma" href="{URL_RESENAS}" rel="noopener" target="_blank" data-resena="ver">Ver todas las reseñas en Google</a>
      <a class="boton fantasma" href="{URL_ESCRIBIR}" rel="noopener" target="_blank" data-resena="escribir">Dejar una reseña</a>
    </div>'''
    total = f'{RESENAS_TOTAL} reseñas' if RESENAS_TOTAL != 1 else '1 reseña'
    return f'''
<section class="seccion{' alterna' if alterna else ''}" id="resenas">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Lo que dicen</span><h2>Reseñas de Google</h2></div>
    <div class="resenas-cabecera centrado" style="justify-content:center">
      <span class="resenas-nota">{str(RESENAS_PUNTUACION).replace('.', ',')}</span>
      <span class="estrellas" aria-hidden="true">{estrellas(RESENAS_PUNTUACION)}</span>
      <span>{total} en Google</span>
    </div>
    <div class="resenas-grilla">{tarjetas}</div>{enlaces}
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Quieres que trabajemos igual en tu casa? Cuéntanos qué necesitas.', 'Hola Clima Baires, he visto vuestras reseñas y quiero pedir presupuesto.', 'Pedir presupuesto')}
</section>'''


def seccion_ultimas_blog():
    """Las entradas más nuevas, en la portada.

    Un blog al que sólo se llega por el menú no lo lee nadie: la portada es la
    página que recibe el tráfico de Ads y la que más se comparte. Aquí además
    hace un trabajo de venta —muestra que sabemos de lo que hablamos— antes de
    pedir nada."""
    if not POSTS:
        return ''
    tarjetas = ''.join(tarjeta_post(p, 'blog/', 3) for p in POSTS[:3])
    return f"""
<section class="seccion" id="blog">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Para saber más</span><h2>Últimas del blog</h2>
    <p class="intro">Lo que explicamos en cada visita, escrito: cómo elegir la potencia, qué mirar en una instalación y cómo cuidar el equipo.</p></div>
    <div class="post-grilla">{tarjetas}</div>
    <div class="centrado" style="margin-top:30px">
      <a class="boton fantasma" href="blog/">Ver todo el blog</a>
    </div>
  </div>
</section>"""


def seccion_ultimas_obras():
    if not HAY_FOTOS:
        return ''
    slides = ''.join(
        f'''<a class="obra-slide" href="obras.html" aria-label="Ver obras recientes">{img_obra(f, sizes='320px')}</a>'''
        for f in DESTACADAS)
    return f'''
<section class="seccion alterna" id="obras">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Trabajo real</span><h2>Últimas obras</h2>
    <p class="intro">Instalaciones, mantenimientos y trabajo en altura hechos por nuestro equipo aquí, en la Costa del Sol. Así trabajamos, y así vamos a trabajar en tu casa.</p></div>
  </div>
  <div class="obras-carrusel-marco">
    <button class="car-flecha car-prev" type="button" aria-label="Anteriores">‹</button>
    <div class="obras-carrusel" id="obras-carrusel">{slides}</div>
    <button class="car-flecha car-next" type="button" aria-label="Siguientes">›</button>
  </div>
  <div class="contenedor centrado" style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:28px">
    <a class="boton" href="obras.html">Ver todas las obras</a>
    <a class="boton fantasma" data-wsp="Hola Clima Baires, he visto vuestras obras y quiero presupuesto." data-origen="seccion" href="#">Quiero algo así en casa</a>
  </div>
</section>'''

def pagina_servicios():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Servicios</nav>
    <h1>Servicios de climatización</h1>
    <p class="bajada">Un solo proveedor, de la compra al mantenimiento.</p>
    {acciones_cabecera('Hola Clima Baires, quiero pedir presupuesto.')}
  </div>
</section>

<section class="seccion" style="padding-top:20px">
  <div class="contenedor">
    <h2 class="centrado" style="margin-bottom:30px">Qué incluye cada servicio</h2>
  </div>
  <div class="contenedor grilla tres">
    {tarjeta_servicio('venta', 'venta', 'Venta de equipos', 'La potencia y la marca adecuadas para cada estancia. Precio cerrado en una sola cifra.', ['Split inverter, multisplit, suelo-techo, cassette y conductos', 'Bomba de calor: el mismo equipo enfría en verano y calienta en invierno', 'Marcas: Daikin, Mitsubishi Electric, LG, Samsung, Midea y Johnson'])}
    {tarjeta_servicio('instalacion', 'instalacion', 'Instalación sin atajos', 'La instalación define la vida útil del equipo. Lista de comprobación de calidad en cada obra.', ['Vacío de la tubería y prueba de estanqueidad, siempre', 'Gas manipulado por personal con carné de gases fluorados', 'Trabajo en altura con medios y equipos de protección homologados', 'Coordinación con la comunidad de propietarios y con la urbanización'])}
    {tarjeta_servicio('mantenimiento', 'mantenimiento', 'Posventa y mantenimiento', 'Un equipo limpio enfría más y gasta menos. Te avisamos nosotros cuando toca.', ['Limpieza a fondo, control de gas y de consumo', 'Reparación multimarca con recambios originales', 'Prioridad de agenda para clientes con plan de mantenimiento'])}
  </div>
</section>

<section class="seccion" style="padding:0 0 50px">{cinta_cta('Cuéntanos qué necesitas y te preparamos el presupuesto hoy.', 'Hola Clima Baires, quiero pedir presupuesto.')}
</section>
{bloque_que_incluye()}
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Cómo trabajamos</span><h2>Cuatro pasos, cero sorpresas</h2></div>
    <div class="grilla dos" style="margin-top:26px">
      <div class="tarjeta"><h3>1 · Cuéntanos qué necesitas</h3><p>Por WhatsApp, con fotos de la estancia. Presupuesto orientativo el mismo día.</p></div>
      <div class="tarjeta"><h3>2 · Visita técnica sin coste</h3><p>Confirmamos todo en tu casa y el presupuesto pasa a ser cerrado.</p></div>
      <div class="tarjeta"><h3>3 · Instalación con lista de comprobación</h3><p>Protegemos, instalamos, probamos y te lo dejamos funcionando delante de ti.</p></div>
      <div class="tarjeta"><h3>4 · Posventa que responde</h3><p>Garantía por escrito y un WhatsApp que contesta cuando lo necesitas.</p></div>
    </div>
    <div class="centrado" style="margin-top:30px; display:flex; gap:14px; justify-content:center; flex-wrap:wrap">
      <a class="boton" data-agenda data-origen="seccion" href="#">Concertar visita técnica</a>
      <a class="boton fantasma" data-wsp="Hola Clima Baires, quiero concertar una visita técnica." data-origen="seccion" href="#">Consultar por WhatsApp</a>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>Pide tu presupuesto hoy</h2><p>Respondemos en menos de 5 minutos en horario comercial.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero presupuesto de instalación." data-origen="seccion" href="#">Pedir presupuesto</a>
    </div>
  </div>
</section>
'''
    return layout(0, 'Servicios de climatización | Clima Baires',
        'Venta de split, multisplit, cassette y conductos, instalación cuidada y mantenimiento anual en toda la Costa del Sol, de Manilva a Nerja.',
        c, f'{DOMINIO}/servicios.html', [
            jsonld_local('Servicios de venta, instalación y mantenimiento de aire acondicionado.', DOMINIO + '/servicios.html'),
            jsonld_migas([('Inicio', '/'), ('Servicios', '/servicios.html')]),
            jsonld_servicio('Venta e instalación de aire acondicionado',
                            'Venta de equipos split, multisplit, suelo-techo y conductos con instalación y puesta en marcha medida.'),
            jsonld_servicio('Mantenimiento y reparación de aire acondicionado',
                            'Limpieza a fondo, control de gas y reparación multimarca con recambios originales.'),
        ], 'servicios',
        pagina_id='servicios')

def pagina_calculadora():
    # mismos coeficientes y misma escalera comercial que main.js: la tabla nunca
    # contradice al widget. En España los equipos se venden por BTU, así que cada
    # escalón lleva su equivalencia (1 frigoría/h ≈ 3,97 BTU/h).
    comerciales = [(2250, 9000), (3000, 12000), (4500, 18000), (6000, 24000), (7500, 30000),
                   (9000, 36000), (12000, 48000), (15000, 60000), (18000, 72000)]
    filas = ''
    for m2, uso in [(10, 'dormitorio pequeño'), (15, 'dormitorio'), (20, 'dormitorio grande o despacho'),
                    (25, 'salón comedor'), (30, 'salón amplio'), (40, 'salón comedor integrado'),
                    (50, 'planta baja diáfana')]:
        f = m2 * 100
        rec = next((c for c in comerciales if c[0] >= f), comerciales[-1])
        filas += (f'<tr><td>{m2} m²</td><td>{uso}</td><td>{f:,}</td>'
                  f'<td><strong>{rec[0]:,}</strong> frigorías · {rec[1]:,} BTU</td></tr>').replace(',', '.')
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Calculadora de frigorías</nav>
    <h1>Calculadora de frigorías</h1>
    <p class="bajada">Rellena los datos y en 30 segundos sabes qué equipo necesitas, en frigorías y en BTU.</p>
    {acciones_cabecera('Hola Clima Baires, quiero saber qué equipo necesito para mi estancia.', 'Que lo calculéis vosotros', secundario='<a class="boton fantasma" data-agenda data-origen="hero" href="#">Concertar visita</a>')}
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
    <form class="calc" id="calc-frigorias">
      <label for="m2">Superficie de la estancia (m²)</label>
      <input type="number" id="m2" name="m2" min="4" max="200" step="0.5" placeholder="Ej.: 25" required>

      <label for="altura">Altura del techo (m)</label>
      <select id="altura" name="altura">
        <option value="2.6" selected>Estándar (2,6 m)</option>
        <option value="3">Alta (3 m)</option>
        <option value="3.5">Muy alta o doble altura (3,5 m o más)</option>
      </select>

      <label for="orientacion">Orientación predominante</label>
      <select id="orientacion" name="orientacion">
        <option value="norte" selected>Norte o este (menos sol)</option>
        <option value="sur">Sur (sol gran parte del día)</option>
        <option value="oeste">Oeste (sol fuerte de tarde)</option>
      </select>

      <label for="ventanales">¿Ventanales grandes o cubierta expuesta al sol?</label>
      <select id="ventanales" name="ventanales">
        <option value="no" selected>No</option>
        <option value="si">Sí</option>
      </select>

      <label for="personas">Personas que usan la estancia habitualmente</label>
      <select id="personas" name="personas">
        <option value="2" selected>1 – 2</option>
        <option value="4">3 – 4</option>
        <option value="6">5 o más</option>
      </select>

      <button class="boton" type="submit" style="margin-top:22px;width:100%">Calcular frigorías</button>

      <div class="resultado" id="calc-resultado">
        <div class="cifra"></div>
        <p class="equipo" style="margin:8px 0 16px"></p>
        <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap">
          <a class="boton celeste" data-wsp-calc href="#">Pedir presupuesto con este cálculo</a>
          <a class="boton fantasma" data-agenda data-origen="calculadora" href="#">Concertar visita técnica</a>
        </div>
      </div>

      <p class="nota">El cálculo parte de 100 frigorías/m² de referencia y lo ajusta por altura, orientación, ganancia solar y ocupación. Aquí, en el hemisferio norte, la fachada sur es la que se lleva el sol todo el día y la oeste, el golpe de calor de la tarde: por eso suman potencia. Cocinas, áticos bajo cubierta y estancias con muchos electrodomésticos pueden pedir más: lo verificamos en la visita técnica.</p>
    </form>
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Te sale un número raro? Mándanos las medidas y lo revisamos.', 'Hola Clima Baires, he usado la calculadora y quiero verificar el resultado.', 'Consultar')}
</section>

<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Tabla de referencia</span><h2>¿Cuántas frigorías por metro cuadrado?</h2>
    <p class="intro">Valores orientativos para techo estándar de 2,6 m y orientación norte o este. Si la estancia tiene ventanales grandes, recibe sol de tarde o la usan varias personas, suma potencia: eso lo ajusta la calculadora de arriba.</p></div>
    <table class="simple">
      <thead><tr><th>Superficie</th><th>Estancia típica</th><th>Frigorías necesarias</th><th>Equipo comercial</th></tr></thead>
      <tbody>{filas}</tbody>
    </table>
    <p class="nota centrado" style="margin-top:18px">La equivalencia es directa: 1 frigoría/h son unas 3,97 BTU/h. Cuando en la tienda te hablen de un 3×1 de 12.000 BTU, son 3.000 frigorías.</p>
  </div>
</section>

<section class="seccion" style="padding:0 0 70px">{cinta_cta('¿Prefieres que lo veamos nosotros? Mándanos las medidas por WhatsApp.', 'Hola Clima Baires, quiero saber qué equipo necesito para mi estancia.', 'Consultar por WhatsApp')}
</section>
'''
    return layout(0, 'Calculadora de frigorías y BTU | Clima Baires',
        'Calcula cuántas frigorías y cuántos BTU necesita tu estancia y qué split te conviene. Herramienta gratuita de Clima Baires, instaladores en la Costa del Sol.',
        c, f'{DOMINIO}/calculadora-frigorias.html', jsonld_migas([('Inicio', '/'), ('Calculadora de frigorías', '/calculadora-frigorias.html')]), 'calc',
        pagina_id='calculadora-frigorias',
        wsp_barra='Hola Clima Baires, quiero saber qué equipo necesito para mi estancia.')

def bloque_antes_despues(par):
    antes = next(f for f in par if f['slug'].startswith('antes-'))
    despues = next(f for f in par if f['slug'].startswith('despues-'))
    return f'''<div class="antes-despues">
      <figure>{img_obra(antes, sizes='(max-width: 560px) 100vw, 45vw')}<figcaption>Antes</figcaption></figure>
      <figure>{img_obra(despues, sizes='(max-width: 560px) 100vw, 45vw')}<figcaption>Después</figcaption></figure>
    </div>'''


def pagina_obras():
    # Aquí sí hay obras locales, así que la zona es parte del contenido y no un
    # dato que haya que esconder. Una foto sin zona es una foto cuya ubicación
    # todavía no está cargada en fotos.py: no genera botón de filtro.
    zonas_presentes = sorted({f['zona'] for f in FOTOS if f.get('zona')})
    tipos_presentes = sorted({f['tipo'] for f in FOTOS})
    fila_zona = ''
    if zonas_presentes:
        fila_zona = '''
    <div class="filtros" role="group" aria-label="Filtrar por zona">
      <span class="etiqueta">Zona:</span>
      <button class="filtro" data-grupo="zona" data-valor="todas" aria-pressed="true">Todas</button>
      %s
    </div>''' % ''.join(
            f'<button class="filtro" data-grupo="zona" data-valor="{z}" aria-pressed="false">{ZONAS_FOTO[z]}</button>'
            for z in zonas_presentes)
    filtros_tipo = ''.join(
        f'<button class="filtro" data-grupo="tipo" data-valor="{t}" aria-pressed="false">{TIPOS_FOTO[t]}</button>'
        for t in tipos_presentes)

    # tarjetas de CTA intercaladas cada 3 fotos: en móvil el mosaico es de una
    # columna y sin esto quedan pantallas enteras de scroll sin invitación a chatear
    ganchos = [
        ('¿Quieres algo así en tu casa?', 'Mándanos una foto de la estancia y te pasamos precio hoy.',
         'Hola Clima Baires, he visto vuestras obras y quiero presupuesto.'),
        ('Instalamos esta semana', 'Cuéntanos qué necesitas y organizamos la visita técnica.',
         'Hola Clima Baires, quiero concertar una visita técnica.'),
        ('¿Tienes un equipo para cambiar?', 'Te presupuestamos la sustitución con retirada del antiguo incluida.',
         'Hola Clima Baires, quiero presupuesto para sustituir un equipo.'),
        ('Presupuesto el mismo día', 'Sin coste y sin compromiso, de Manilva a Nerja.',
         'Hola Clima Baires, quiero presupuesto sin coste.'),
    ]
    trozos, gancho = [], 0
    for i, f in enumerate(FOTOS):
        trozos.append(f'''
      <figure class="obra" data-zona="{f['zona']}" data-tipo="{f['tipo']}">
        <button class="obra-abrir" type="button" data-full="assets/img/obras/{f['slug']}-1600.webp"
                data-alt="{pie_foto(f)}" data-slug="{f['slug']}" aria-label="Ampliar: {pie_foto(f)}">
          {img_obra(f)}
        </button>
        <figcaption>{pie_foto(f)}</figcaption>
      </figure>''')
        if (i + 1) % 3 == 0 and gancho < len(ganchos):
            t, s, m = ganchos[gancho]
            gancho += 1
            trozos.append(f'''
      <div class="obra-cta">
        {WSP_SVG}
        <p class="obra-cta-titulo">{t}</p>
        <p>{s}</p>
        <a class="boton verde" data-wsp="{m}" data-origen="cinta" href="#">Escríbenos por WhatsApp</a>
      </div>''')
    if gancho < 1:                      # galerías cortas: al menos una tarjeta
        t, s, m = ganchos[0]
        trozos.append(f'''
      <div class="obra-cta">
        {WSP_SVG}
        <p class="obra-cta-titulo">{t}</p>
        <p>{s}</p>
        <a class="boton verde" data-wsp="{m}" data-origen="cinta" href="#">Escríbenos por WhatsApp</a>
      </div>''')
    items = ''.join(trozos)

    pares = ''
    if PARES_AD:
        bloques = ''.join(bloque_antes_despues(par) for par in PARES_AD.values())
        pares = f'''
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">El cambio se nota</span><h2>Antes y después</h2></div>
    {bloques}
  </div>
</section>'''

    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Obras recientes</nav>
    <h1>Obras recientes</h1>
    <p class="bajada">Nuestro equipo en obra por toda la Costa del Sol: instalación, mantenimiento y trabajo en altura, con el detalle que después se nota.</p>
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
{fila_zona}
    <div class="filtros" role="group" aria-label="Filtrar por tipo de trabajo">
      <span class="etiqueta">Trabajo:</span>
      <button class="filtro" data-grupo="tipo" data-valor="todos" aria-pressed="true">Todos</button>
      {filtros_tipo}
    </div>
    <div style="margin:22px 0 4px">{cinta_cta('Mira cómo trabajamos. ¿Quieres lo mismo en tu casa?', 'Hola Clima Baires, he visto vuestras obras y quiero presupuesto.', 'Pedir presupuesto')}</div>
    <div class="obras-grilla" id="obras-grilla">{items}
    </div>
    <p id="obras-vacio" hidden>No hay obras con ese filtro todavía. Prueba con otra zona u otro tipo de trabajo.</p>
  </div>
</section>
{pares}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>¿Quieres algo así en tu casa?</h2><p>Cuéntanos qué estancia quieres climatizar y te pasamos presupuesto hoy.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, he visto vuestras obras recientes y quiero presupuesto." data-origen="seccion" href="#">Pedir presupuesto</a>
    </div>
  </div>
</section>

<div class="lightbox" id="lightbox" hidden role="dialog" aria-modal="true" aria-label="Foto ampliada">
  <button class="lb-cerrar" type="button" aria-label="Cerrar (Escape)">×</button>
  <button class="lb-prev" type="button" aria-label="Foto anterior">‹</button>
  <img class="lb-img" src="" alt="">
  <button class="lb-next" type="button" aria-label="Foto siguiente">›</button>
  <p class="lb-cap"></p>
  <a class="boton celeste lb-wsp" data-wsp="He visto vuestras obras en la web y quiero algo así en casa." data-origen="lightbox" href="#">Quiero algo así en casa</a>
</div>
'''
    ld = [
        jsonld_local('Galería de obras: instalación, sustitución y mantenimiento de aire acondicionado.', f'{DOMINIO}/obras.html'),
        jsonld_migas([('Inicio', '/'), ('Obras recientes', '/obras.html')]),
        {
            '@context': 'https://schema.org',
            '@type': 'ItemList',
            'name': 'Obras recientes de Clima Baires',
            'itemListElement': [{
                '@type': 'ListItem', 'position': i + 1,
                'item': {
                    '@type': 'ImageObject',
                    'contentUrl': f'{DOMINIO}/assets/img/obras/{f["slug"]}-1600.webp',
                    'name': pie_foto(f),
                    'representativeOfPage': i == 0,
                },
            } for i, f in enumerate(FOTOS)],
        },
    ]
    return layout(0, 'Obras recientes | Clima Baires',
        'Galería de obras de Clima Baires en toda la Costa del Sol: instalación de split, cassette y unidades exteriores, sustituciones y mantenimiento. Fotos reales de nuestro equipo.',
        c, f'{DOMINIO}/obras.html', ld, 'obras',
        og_image=f'{DOMINIO}/assets/img/obras/og-obras.jpg' if HAY_FOTOS else None,
        pagina_id='obras', wsp_barra='Hola Clima Baires, he visto vuestras obras recientes y quiero presupuesto.')


def faq_de_zona(slug, nombre):
    """Las preguntas de cada zona viven en contenido/faq-zonas.json, no aquí: son
    contenido editable y son lo que Google levanta como FAQPage. Si falta una
    zona no se rompe el build, pero se avisa: publicar las genéricas en una
    landing de Ads es desperdiciarla."""
    propias = FAQ_ZONAS.get(slug)
    if propias:
        return [(p, r) for p, r in propias]
    print(f'  ! {slug}: sin preguntas propias en contenido/faq-zonas.json, van las genéricas')
    return [
        (f'¿Cuánto tardáis en venir a {nombre}?', 'Concertamos la visita técnica dentro de las 72 horas siguientes.'),
        ('¿El presupuesto tiene coste?', 'No: la visita técnica y el presupuesto son sin coste.'),
        ('¿Atendéis equipos que no habéis instalado vosotros?', 'Sí, somos multimarca: limpieza, carga de gas y reparación.'),
    ]


def pagina_zona(slug, nombre, comarca, intro, barrios, especial):
    faq = faq_de_zona(slug, nombre)
    # acordeón nativo: la respuesta está en el HTML (Google la lee aunque esté
    # plegada) y la página no se convierte en un muro de texto
    faq_html = ''.join(
        f'<details class="faq-item"><summary>{p}</summary><p>{r}</p></details>'
        for p, r in faq)
    otras = ' · '.join(f'<a href="{s}.html">{n}</a>' for s, n, *_ in ZONAS if s != slug)
    lista_barrios = ', '.join(barrios)
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="../index.html">Inicio</a> › <a href="../index.html#zonas">Zonas</a> › {nombre}</nav>
    <h1>Aire acondicionado en {nombre}</h1>
    <p class="bajada">{intro}</p>
    {acciones_cabecera(f'Hola, estoy en {nombre} y quiero presupuesto de instalación.', f'Presupuesto en {nombre}', '../')}
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor grilla dos">
    <div>
      <h2>Instalación, venta y mantenimiento en {nombre}</h2>
      <p>Split, multisplit, suelo-techo y conductos en {lista_barrios}. Presupuesto por WhatsApp en el día y precio cerrado: lo que ves es lo que pagas.</p>
      <ul class="lista-check">
        <li>Equipo propio, con seguro de responsabilidad civil al día</li>
        <li>Vacío de la tubería y prueba de estanqueidad, siempre</li>
        <li>Garantía por escrito y mantenimiento anual</li>
      </ul>
      <div style="margin-top:22px; display:flex; gap:12px; flex-wrap:wrap">
        <a class="boton" data-wsp="Hola Clima Baires, estoy en {nombre} y quiero pedir presupuesto." data-origen="seccion" href="#">Pedir presupuesto en {nombre}</a>
        <a class="boton fantasma" data-agenda data-origen="seccion" href="#">Concertar visita</a>
      </div>
    </div>
    <div>
      <div class="tarjeta tarjeta-zona">
        <h3>Cómo trabajamos en {nombre}</h3>
        <p>{especial}</p>
        <a class="boton fantasma" data-wsp="Hola, estoy en {nombre} y quiero consultar por una instalación." data-origen="tarjeta" href="#">Consultar por WhatsApp</a>
      </div>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 60px">{cinta_cta(f'¿Concertamos una visita técnica en {nombre}? Sin coste y sin compromiso.', f'Hola, estoy en {nombre} y quiero presupuesto de instalación.')}
</section>

<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Dudas de la zona</span><h2>Preguntas frecuentes en {nombre}</h2></div>
    <div class="faq-lista">{faq_html}</div>
    <p class="centrado" style="margin-top:26px"><a class="boton verde" data-wsp="Hola, estoy en {nombre} y tengo una consulta que no está en las preguntas frecuentes." data-origen="faq" href="#">Preguntar lo que no está aquí</a></p>
  </div>
</section>
{bloque_quien_entra(alterna=False, p='../')}
<section class="seccion alterna">
  <div class="contenedor centrado">
    <h2>También trabajamos en</h2>
    <p style="margin-top:10px">{otras}</p>
    <p class="nota" style="margin-top:14px">Y en el resto de la costa: {otras_zonas_texto()}. Damos servicio en {COBERTURA}.</p>
  </div>
</section>
'''
    ld = [
        jsonld_local(f'Venta, instalación y mantenimiento de aire acondicionado en {nombre} ({comarca}).',
                     f'{DOMINIO}/zonas/{slug}.html', nombre),
        jsonld_migas([('Inicio', '/'), ('Zonas', '/#zonas'), (nombre, f'/zonas/{slug}.html')]),
        jsonld_faq(faq),
        jsonld_servicio(f'Instalación de aire acondicionado en {nombre}',
                        f'Venta, instalación y posventa de aire acondicionado en {nombre}.', nombre),
    ]
    return layout(1, f'Aire acondicionado en {nombre} | Clima Baires',
        f'Instalación de aire acondicionado en {nombre}: split, multisplit y conductos. Presupuesto el mismo día y posventa de verdad.',
        c, f'{DOMINIO}/zonas/{slug}.html', ld, 'zonas',
        pagina_id=f'zonas/{slug}', zona_nombre=nombre,
        wsp_barra=f'Hola, estoy en {nombre} y quiero presupuesto de instalación.')

def pagina_nosotros():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Sobre nosotros</nav>
    <h1>Climatización en toda la Costa del Sol</h1>
    <p class="bajada">Un equipo dedicado al aire acondicionado, con un estándar de trabajo que se sostiene obra tras obra.</p>
    {acciones_cabecera('Hola Clima Baires, quiero concertar una visita técnica.', 'Hablar con nosotros', secundario='<a class="boton fantasma" href="obras.html">Ver obras</a>')}
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor grilla dos">
    <div>
      <h2>Nuestra historia</h2>
      <p>Llevamos años instalando aire acondicionado en {COBERTURA}, y en ese tiempo aprendimos que el negocio no es vender un aparato: es que el cliente vuelva a llamarte al año siguiente. Todo lo que hacemos sale de ahí.</p>
      <ul class="lista-check">
        <li><strong>Transparencia</strong>: precio cerrado, sin letra pequeña.</li>
        <li><strong>Rapidez</strong>: respuesta en minutos, presupuesto en el día.</li>
        <li><strong>Posventa de verdad</strong>: seguimos estando después de cobrar.</li>
      </ul>
      <p style="margin-top:14px">Equipo propio, con procesos y listas de comprobación de obra escritas: lo que se promete es lo que se hace. Y trabajo hecho aquí, que puedes ver en la <a href="obras.html">galería de obras</a> y comprobar en nuestras reseñas de Google.</p>
    </div>
    <div>
      <div class="tarjeta">
        <h3>Nuestros valores</h3>
        <p><strong>Misión:</strong> ofrecer soluciones de climatización eficientes, seguras y duraderas, adaptadas a cada vivienda.</p>
        <p><strong>Visión:</strong> ser la referencia de la Costa del Sol por transparencia, agilidad y calidad humana.</p>
        <p><strong>Lema:</strong> «Tu confort, nuestra prioridad».</p>
      </div>
      <div class="tarjeta" style="margin-top:20px">
        <h3>Datos que importan</h3>
        <ul class="lista-check">
          <li>Seguro de responsabilidad civil en vigor</li>
          <li>Gas refrigerante manipulado por personal con carné de gases fluorados</li>
          <li>Lista de comprobación de calidad con fotos en cada obra</li>
          <li>Gestión de residuos y recuperación del gas refrigerante con máquina</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 60px">{cinta_cta('¿Te contamos cómo lo haríamos en tu casa?', 'Hola Clima Baires, quiero que me aseséis para climatizar mi casa.')}
</section>
{seccion_resenas(alterna=True)}
{bloque_quien_entra(alterna=False)}
{seccion_asi_trabajamos()}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>Conócenos trabajando</h2><p>La mejor carta de presentación es una instalación bien hecha.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero concertar una visita técnica." data-origen="seccion" href="#">Concertar visita</a>
    </div>
  </div>
</section>
'''
    return layout(0, 'Sobre nosotros | Clima Baires',
        'Clima Baires: venta, instalación y posventa de aire acondicionado en toda la Costa del Sol, de Manilva a Nerja. Transparencia, rapidez y posventa de verdad.',
        c, f'{DOMINIO}/sobre-nosotros.html', [
            jsonld_local('Empresa de climatización en toda la Costa del Sol.', DOMINIO + '/sobre-nosotros.html', con_rating=True),
            jsonld_migas([('Inicio', '/'), ('Sobre nosotros', '/sobre-nosotros.html')]),
        ], 'nosotros', pagina_id='sobre-nosotros')


def bloque_quien_entra(alterna=True, p=''):
    """La objeción que nadie escribe en el formulario: meter en tu casa a dos
    desconocidos con un taladro. Va en «sobre nosotros» y en las seis zonas —sin
    datos locales dentro, así se inserta igual en las siete páginas."""
    pasos = [
        ('Nombre y foto por delante',
         'El día anterior te llega por WhatsApp el nombre, la foto y el DNI del técnico que va a tu '
         'casa, más la matrícula de la furgoneta, para que lo dejes anotado en la garita o se lo pases '
         'al conserje sin tener que llamar a nadie.'),
        ('Franja de dos horas',
         'No te decimos «por la mañana»: te damos una franja de dos horas, el equipo llega en furgoneta '
         'rotulada y con ropa de trabajo, y si nos retrasamos te avisamos antes de que se cumpla la '
         'franja, no después.'),
        ('Protección antes de empezar',
         'Antes de abrir la primera caja tapamos el suelo, los muebles y el paso hasta la estancia con '
         'mantas y plástico, y el aspirador lo traemos nosotros: no se pide prestada ninguna herramienta '
         'de la casa.'),
        ('Se prueba contigo delante',
         'El equipo se enciende contigo al lado y no nos vamos hasta que lo veas funcionar: frío, calor, '
         'mando a distancia, cómo se sacan y se lavan los filtros y qué hacer si algún día no arranca.'),
        ('Nos lo llevamos todo',
         'Cartones, recortes de tubería, restos de obra y el equipo antiguo si lo había se van en nuestra '
         'furgoneta el mismo día, no al contenedor de la comunidad ni al cubo del vecino. El gas del '
         'equipo retirado se recupera con máquina y se entrega a gestor autorizado.'),
    ]
    tarjetas = ''.join(
        '<div class="tarjeta"%s><h3>%d · %s</h3><p>%s</p></div>' % (
            ' style="grid-column:1/-1"' if i == len(pasos) - 1 else '', i + 1, t, d)
        for i, (t, d) in enumerate(pasos))
    return f'''
<section class="seccion{' alterna' if alterna else ''}">
  <div class="contenedor">
    <div class="centrado">
      <span class="kicker">El día de la obra</span>
      <h2>Quién va a entrar en tu casa</h2>
      <p class="intro">Meter en tu casa a dos personas con un taladro no es un trámite menor: estas cinco cosas las hacemos en toda obra, sin que tengas que pedirlas.</p>
    </div>
    <div class="grilla dos" style="margin-top:26px">{tarjetas}</div>
    <p class="centrado nota" style="margin-top:22px">Los papeles que pide la comunidad de propietarios o la urbanización —seguro de responsabilidad civil, datos de la empresa, horarios de obra— los presentamos nosotros. Tú no tienes que bajar a portería a explicar quiénes somos.</p>
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Quieres saber cómo sería en tu casa? Pregúntanos sin compromiso.', 'Hola Clima Baires, quiero saber cómo trabajáis dentro de la casa.', 'Preguntar por WhatsApp')}
</section>'''


def bloque_que_incluye():
    """«Precio cerrado» sin una lista no dice nada. Estas son las dos listas.

    La de la derecha no lleva ✓: un tic en lo que se cobra aparte se lee como si
    también estuviera incluido, que es justo el malentendido que el bloque viene
    a eliminar."""
    incluido = [
        ('Hasta %s metros de tubería de cobre, con aislamiento' % METROS_INCLUIDOS,
         'El tubo que une la unidad de dentro con la de fuera, forrado para que no sude ni pierda frío. El recorrido real se mide en la visita técnica.'),
        ('Soportes, anclajes y silentblocks',
         'Las escuadras de la unidad exterior, con el anclaje que pide esa pared, y los tacos antivibratorios que evitan que el compresor se oiga dentro.'),
        ('El paso de pared para la tubería',
         'La perforación en tabique o pared corriente y su remate. Si hay que picar y rehacer, eso ya es obra civil y está en la otra lista.'),
        ('Vacío de la instalación con bomba',
         'Sacar el aire y la humedad del circuito antes de soltar el gas. Con bomba y vacuómetro, no con una purga de diez segundos. Es lo que decide si el equipo llega a los diez años.'),
        ('Prueba de estanqueidad',
         'Estanqueidad, en cristiano, es que no pierda. Se presuriza con nitrógeno y se comprueba que la aguja no baje, antes de cerrar nada.'),
        ('La carga de refrigerante que pidan esos metros',
         'Los equipos vienen de fábrica con gas para un recorrido corto. Si el tuyo es más largo, hay que añadir. Dentro de los %s metros, va en el precio.' % METROS_INCLUIDOS),
        ('Desagüe con pendiente natural, probado con agua',
         'La salida del agua de condensación, con caída continua y sin barrigas, a un punto que no sea la medianera ni la terraza del vecino. Se prueba antes de cerrar la pared.'),
        ('Puesta en marcha contigo delante',
         'Presiones, consumo en amperios y salto térmico entre el aire que entra y el que sale, medidos y explicados allí mismo. No es «lo encendimos y funcionaba».'),
        ('Protección de la vivienda y retirada de residuos',
         'Cubrimos muebles y suelos antes de empezar, y nos llevamos cajas, recortes de cobre y polvo. La obra termina cuando no queda nada nuestro en tu casa.'),
        ('Garantía por escrito de la instalación',
         'De nuestra mano de obra: uniones, desagüe, fijaciones y puesta en marcha. Va aparte de la garantía del fabricante del equipo, que también te entregamos con la factura. Plazo: %s.' % GARANTIA_INSTALACION),
    ]
    aparte = [
        ('Metro adicional de tubería',
         'Pasados los %s metros, se cobra por metro, con el refrigerante extra que ese tramo necesita. El precio del metro te lo decimos en el presupuesto, no después.' % METROS_INCLUIDOS),
        ('Trabajo en altura con andamio o plataforma elevadora',
         'Cuando la unidad exterior va donde no llega una escalera. El andamio o la plataforma se alquilan por día y eso se presupuesta aparte. Los equipos de protección del personal no se cobran nunca: van siempre.'),
        ('Grúa o elevación mecánica',
         'Equipos pesados o accesos imposibles: suelo-techo grandes, conductos, patios interiores. Lo presta un tercero y se factura tal como lo cobra.'),
        ('Obra civil: rozas, picado y reparación',
         'Abrir la pared para empotrar la tubería, y después enlucir y pintar. Si el recorrido va por canaleta vista, no hace falta. Si lo quieres todo oculto, se presupuesta.'),
        ('Bomba de condensados',
         'Cuando la salida del desagüe queda más alta que el equipo, el agua no baja sola: hace falta una bomba que la empuje. Es un aparato más, con su instalación.'),
        ('Circuito eléctrico nuevo, magnetotérmico o cuadro',
         'El equipo necesita su propia línea con protección. Si en esa pared no hay nada, o el cuadro no tiene sitio para un magnetotérmico más, es trabajo de electricidad.'),
        ('Lo que cobre la comunidad o el ayuntamiento',
         'Algunas comunidades piden fianza o tienen tasas de obra; algunos ayuntamientos exigen licencia de obra menor o declaración responsable para tocar fachada. La gestión con la comunidad la hacemos nosotros; las tasas van detalladas como lo que son, sin recargo nuestro encima.'),
    ]
    def lista(items, clase, corte=None):
        """`corte` parte la lista para colar una cinta en el medio: apilada en
        móvil, la de «entra en el precio» son diez puntos seguidos."""
        li = [f'<li><strong>{t}</strong><span>{d}</span></li>' for t, d in items]
        if corte is None:
            return '<ul class="%s">%s</ul>' % (clase, ''.join(li))
        cinta = cinta_cta_suelta('¿Todo esto entra en tu caso? Mándanos una foto de la estancia y te lo confirmamos.',
                                 'Hola Clima Baires, quiero saber qué entra en el precio en mi caso. Os mando fotos.',
                                 'Consultar', 'seccion')
        return '<ul class="%s">%s</ul><div class="solo-movil corte-lista">%s</div><ul class="%s">%s</ul>' % (
            clase, ''.join(li[:corte]), cinta, clase, ''.join(li[corte:]))
    return f'''
<section class="seccion alterna" id="que-incluye">
  <div class="contenedor">
    <div class="centrado">
      <span class="kicker">Precio cerrado</span>
      <h2>Qué entra en el precio y qué se cobra aparte</h2>
      <p class="intro">Decir «precio cerrado» sin una lista es no decir nada. Esta es la lista: lo que entra siempre en una instalación nuestra, y lo que se cobra aparte cuando la vivienda lo pide. Si algo de la segunda lista aplica en tu caso, lo ves en el presupuesto antes de que empiece la obra.</p>
    </div>
    <div class="grilla dos" style="margin-top:30px; align-items:start">
      <div class="tarjeta">
        <h3>Entra en el precio</h3>
        <p class="nota">Siempre, en toda instalación. No se discute ni se recorta.</p>
        {lista(incluido, 'lista-check lista-detalle', corte=5)}
      </div>
      <div class="solo-movil">{cinta_cta_suelta('¿Quieres saber qué de esto aplica en tu casa? Mándanos una foto de la estancia.', 'Hola Clima Baires, quiero saber qué entra en el precio en mi caso. Os mando fotos.', 'Consultar', 'seccion')}</div>
      <div class="tarjeta">
        <h3>Se cobra aparte</h3>
        <p class="nota">Sólo si tu vivienda lo pide. Sale en el presupuesto, con el importe a la vista, antes de arrancar.</p>
        {lista(aparte, 'lista-mas lista-detalle')}
      </div>
    </div>
    <div class="compromiso">
      <h3>Nuestro compromiso con los extras</h3>
      <p>Casi todo lo de la segunda lista se detecta en la visita técnica y entra en el presupuesto cerrado antes de que compres nada. Si aun así aparece algo durante la obra, hacemos siempre lo mismo: paramos, te lo enseñamos en el sitio, te decimos cuánto suma y seguimos sólo cuando lo apruebas. Basta un «adelante» por WhatsApp, y queda por escrito. Un extra que aparece en la factura y no antes, aquí no existe.</p>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero presupuesto con el detalle de qué entra y qué se cobra aparte." data-origen="seccion" href="#">Pedir el presupuesto detallado</a>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 50px">{cinta_cta('Cuéntanos cómo está tu vivienda y te decimos qué entra y qué no, antes de cobrarte nada.', 'Hola Clima Baires, quiero saber qué entra en el precio y qué se cobra aparte en mi caso.', 'Pedir el detalle por WhatsApp')}
</section>'''


def seccion_asi_trabajamos():
    if not HAY_FOTOS:
        return ''
    equipo = [f for f in FOTOS if f['tipo'] == 'equipo']
    resto = [f for f in FOTOS if f['tipo'] != 'equipo']
    fotos = (equipo + resto)[:3]
    if not fotos:
        return ''
    imgs = ''.join(img_obra(f) for f in fotos)
    return f'''
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Así trabajamos</span><h2>El equipo, en obra</h2>
    <p class="intro">Uniforme, herramienta homologada y obras que quedan limpias. Estas fotos son de nuestro equipo trabajando de verdad — hay más en la <a href="obras.html">galería de obras</a>.</p></div>
    <div class="franja-equipo">{imgs}</div>
  </div>
</section>'''

def bloque_mapa():
    """Mapa de la ficha de Google. Va sólo aquí y sólo con consentimiento: es la
    tercera carga externa del sitio y en la UE un iframe de Google es tratamiento
    de datos, no decoración. Sin Place ID no se pinta nada."""
    if not PLACE_ID:
        return '''
    <div class="tarjeta" style="margin-top:24px">
      <h3>PENDIENTE — Place ID de Google</h3>
      <p>Con el Place ID cargado en <code>CB.placeId</code> (assets/js/main.js) esta tarjeta pasa a ser el mapa de la ficha, con la puntuación visible, más los enlaces para ver todas las reseñas y para dejar una. Se saca del buscador de Place ID de Google Maps Platform.</p>
    </div>'''
    return f'''
    <div class="tarjeta" style="margin-top:24px">
      <h3>Dónde estamos</h3>
      <p>Somos empresa de servicio a domicilio: vamos nosotros. Esta es nuestra ficha en Google, con la puntuación y las reseñas de clientes de la zona.</p>
      <div class="mapa-embed" data-mapa-embed>
        <div class="mapa-sin-consentimiento">
          <p>El mapa lo carga Google. Para verlo aquí hace falta tu permiso de cookies; si prefieres no darlo, puedes abrirlo directamente.</p>
          <p style="margin-top:12px"><a class="boton fantasma" href="{URL_MAPS}" rel="noopener" target="_blank" data-resena="maps">Abrir en Google Maps</a></p>
        </div>
      </div>
      <p style="margin-top:16px"><a href="{URL_RESENAS}" rel="noopener" target="_blank" data-resena="ver">Ver todas las reseñas en Google</a> · <a href="{URL_ESCRIBIR}" rel="noopener" target="_blank" data-resena="escribir">Dejar una reseña</a></p>
    </div>'''


def pagina_contacto():
    opciones_zona = ''.join(f'<option>{n}</option>' for _, n, *_ in ZONAS)
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Contacto</nav>
    <h1>Hablemos de tu clima</h1>
    <p class="bajada">El camino más corto es WhatsApp: fotos de la estancia y presupuesto en el día.</p>
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
    <h2 class="centrado" style="margin-bottom:30px">Elige por dónde te contactamos</h2>
  </div>
  <div class="contenedor grilla dos">
    <div class="tarjeta">
      <h3>Escríbenos directamente</h3>
      <p>WhatsApp: <strong data-wsp-num></strong><br>
      Email: <a data-email href="#"></a><br>
      Horario: <span data-horario></span></p>
      <a class="boton celeste" data-wsp="Hola Clima Baires, quiero hacer una consulta." data-origen="seccion" href="#" style="margin-top:8px">Abrir WhatsApp</a>
      <p style="margin-top:18px"><strong>Zona de trabajo:</strong> {COBERTURA}. Donde más obra tenemos es en Málaga capital, Marbella, Torremolinos, Benalmádena, Fuengirola y Mijas, pero vamos igualmente a {otras_zonas_texto()}. Atendemos a domicilio: no tenemos tienda abierta al público, y eso también lo pagas menos.</p>
    </div>
    <div class="tarjeta">
      <h3>O déjanos tus datos</h3>
      <p>Rellena el formulario y el mensaje se abre listo para enviar por WhatsApp.</p>
      <form class="form-contacto" id="form-contacto">
        <input name="nombre" placeholder="Tu nombre" required>
        <select name="zona" required>
          <option value="" disabled selected>¿En qué zona estás?</option>
          {opciones_zona}<option>Otro municipio de la Costa del Sol</option>
        </select>
        <textarea name="mensaje" placeholder="Cuéntanos qué necesitas: instalación nueva, sustitución, mantenimiento…" required></textarea>
        <button class="boton" type="submit">Enviar por WhatsApp</button>
      </form>
      <p class="nota" style="margin-top:12px">Al enviarlo tratamos tus datos para responderte, según la <a href="privacidad.html">política de privacidad</a>. El formulario no guarda nada en este sitio: abre WhatsApp con el mensaje escrito.</p>
    </div>
  </div>
</section>

<section class="seccion" style="padding-top:0" id="agenda">
  <div class="contenedor">
    <div class="tarjeta">
      <h3>Reserva tu visita técnica</h3>
      <p>Elige día y hora en nuestra agenda y listo: te llega la confirmación por email y a nosotros la cita al calendario. La visita y el presupuesto son sin coste en toda la Costa del Sol.</p>
      <a class="boton" data-agenda data-origen="seccion" href="#" style="margin-top:10px">Reservar visita técnica</a>
      <div data-agenda-embed></div>
    </div>
{bloque_mapa()}
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Prefieres que lo resolvamos por WhatsApp? Es el camino más corto.', 'Hola Clima Baires, quiero hacer una consulta.', 'Escribir por WhatsApp')}
</section>
{seccion_resenas(alterna=True)}'''
    return layout(0, 'Contacto y presupuestos | Clima Baires',
        'Pide tu presupuesto de instalación de aire acondicionado en toda la Costa del Sol, de Manilva a Nerja. Te respondemos por WhatsApp en horario comercial.',
        c, f'{DOMINIO}/contacto.html', [
            jsonld_local('Contacto y presupuestos de climatización en toda la Costa del Sol.', DOMINIO + '/contacto.html', con_rating=True),
            jsonld_migas([('Inicio', '/'), ('Contacto', '/contacto.html')]),
        ], 'contacto', pagina_id='contacto',
        wsp_barra='Hola Clima Baires, quiero hacer una consulta.')

def tarjeta_post(post, base='blog/', nivel=2):
    """`base` es el camino hasta la carpeta del blog desde la página que la usa
    ('blog/' desde la raíz, '' desde una entrada). `nivel` es el del encabezado:
    la jerarquía tiene que quedar sin saltos en cada página donde se inserta."""
    return f'''<article class="post-tarjeta" data-categoria="{post['categoria']}">
        <a href="{base}{post['slug']}.html">
          <span class="post-cat">{post['categoria_label']}</span>
          <h{nivel}>{post['titulo']}</h{nivel}>
          <p>{post['resumen']}</p>
          <span class="post-meta">{post['fecha_larga']} · {post['minutos']} min de lectura</span>
        </a>
      </article>'''


def intercalar_cta(cuerpo, mensaje):
    """Mete cintas de conversión entre las secciones de una entrada larga.

    Una entrada de 1.400 palabras son diez pantallas de móvil: si el único CTA
    está al final, quien se convence a la mitad no tiene dónde pulsar. Se inserta
    antes de cada tercer `<h2>` (nunca antes del primero, que va pegado a la
    entradilla) para no cortar la lectura más de la cuenta."""
    partes = re.split(r'(?=<h[23]>)', cuerpo)
    if len(partes) < 3:
        return cuerpo
    salida, acumulado = [], 0
    for i, parte in enumerate(partes):
        if i and acumulado > TRAMO_SIN_CTA:
            salida.append('<div class="cta-intercalado">%s</div>' % cinta_cta_suelta(
                'Si prefieres que lo veamos nosotros, escríbenos y concertamos una visita.',
                mensaje, 'Consultar', 'nota'))
            acumulado = 0
        salida.append(parte)
        acumulado += alto_aproximado(parte)
    return ''.join(salida)


# Cuánto texto puede pasar sin un botón de WhatsApp, medido en caracteres
# aproximados. Dos pantallas de móvil: el QA falla si algún tramo pasa de tres.
TRAMO_SIN_CTA = 1250


def alto_aproximado(html_):
    """Los <li> y las filas de tabla ocupan mucho más alto por carácter que un
    párrafo, así que cuentan doble a la hora de decidir dónde va el próximo CTA."""
    texto = re.sub(r'<[^>]+>', '', html_)
    return len(texto) + 45 * len(re.findall(r'<(?:li|tr)\b', html_))


def pagina_blog(posts):
    cats = sorted({p['categoria'] for p in posts})
    filtros = ''.join(
        f'<button class="filtro" data-grupo="cat" data-valor="{c}" aria-pressed="false">{_blog.CATEGORIAS[c]}</button>'
        for c in cats)
    # una cinta cada tres tarjetas: el listado crece solo con la rutina y sin
    # esto queda un tramo largo de scroll sin dónde pulsar
    tarjetas = ''
    for i, p in enumerate(posts):
        if i and i % 3 == 0:
            tarjetas += '<div class="cinta-en-grilla">%s</div>' % cinta_cta_suelta(
                '¿Prefieres preguntarlo directamente? Escríbenos y te respondemos.',
                'Hola Clima Baires, he leído algo en vuestro blog y quiero hacer una consulta.',
                'Preguntar', 'listado')
        tarjetas += tarjeta_post(p, '')
    vacio = '' if posts else '<p class="intro centrado">Estamos escribiendo las primeras entradas. Vuelve en unos días.</p>'
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="../index.html">Inicio</a> › Blog</nav>
    <h1>Blog de climatización</h1>
    <p class="bajada">Lo que hemos aprendido instalando: cómo elegir, qué mirar en una obra y cómo cuidar tu equipo.</p>
    {acciones_cabecera('Hola Clima Baires, he leído algo en vuestro blog y quiero hacer una consulta.', 'Consultar por WhatsApp', '../')}
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor">
    <div class="filtros" role="group" aria-label="Filtrar por tema">
      <span class="etiqueta">Tema:</span>
      <button class="filtro" data-grupo="cat" data-valor="todas" aria-pressed="true">Todos</button>
      {filtros}
    </div>
    <div class="post-grilla" id="post-grilla">{tarjetas}</div>
    <p id="post-vacio" hidden>No hay entradas de ese tema todavía.</p>
    {vacio}
  </div>
</section>

<section class="seccion" style="padding:0 0 70px">{cinta_cta('¿Te ha quedado una duda de lo que has leído? Pregúntanos sin compromiso.', 'Hola Clima Baires, he leído algo en vuestro blog y tengo una consulta.', 'Preguntar')}
</section>
'''
    ld = [
        jsonld_migas([('Inicio', '/'), ('Blog', '/blog/')]),
        {
            '@context': 'https://schema.org', '@type': 'Blog',
            'name': 'Blog de Clima Baires', 'url': f'{DOMINIO}/blog/',
            'publisher': {'@id': DOMINIO + '/#negocio'},
            'blogPost': [{'@type': 'BlogPosting', 'headline': p['titulo'],
                          'url': f'{DOMINIO}/blog/{p["slug"]}.html', 'datePublished': p['fecha_iso']}
                         for p in posts],
        },
    ]
    return layout(1, 'Blog de climatización | Clima Baires',
        'El blog de Clima Baires: cuántas frigorías necesitas, qué mirar en una instalación y cómo mantener tu equipo en la Costa del Sol.',
        c, f'{DOMINIO}/blog/', ld, 'blog', pagina_id='blog',
        wsp_barra='Hola Clima Baires, he leído algo en vuestro blog y quiero hacer una consulta.')


def pagina_post(post, otros):
    relacionadas = [o for o in otros if o['categoria'] == post['categoria']][:2] or otros[:2]
    mas = ''
    if relacionadas:
        mas = f'''
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Seguir leyendo</span><h2>Más del blog</h2></div>
    <div class="post-grilla" style="margin-top:26px">{''.join(tarjeta_post(o, '', 3) for o in relacionadas)}</div>
  </div>
</section>'''
    msj = f'Hola Clima Baires, he leído «{post["titulo"]}» en vuestro blog y quiero pedir presupuesto.'
    c = f'''
<article class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="../index.html">Inicio</a> › <a href="index.html">Blog</a> › {post['categoria_label']}</nav>
    <span class="post-cat">{post['categoria_label']}</span>
    <h1>{post['titulo']}</h1>
    <p class="bajada">{post['resumen']}</p>
    <p class="post-meta">Publicado el {post['fecha_larga']} · {post['minutos']} min de lectura</p>
    {acciones_cabecera(msj, 'Pedir presupuesto', '../')}
  </div>
</article>

<section class="seccion" style="padding-top:30px">
  <div class="contenedor">
    <div class="post-cuerpo">
      {intercalar_cta(post['html'], msj)}
    </div>
  </div>
</section>

{mas}
<section class="seccion" style="padding:34px 0 60px">{cinta_cta('¿Quieres que lo veamos en tu casa? La visita y el presupuesto son sin coste.', msj, 'Pedir presupuesto')}
</section>'''
    ld = [
        jsonld_migas([('Inicio', '/'), ('Blog', '/blog/'), (post['titulo'], f'/blog/{post["slug"]}.html')]),
        {
            '@context': 'https://schema.org', '@type': 'BlogPosting',
            'headline': post['titulo'], 'description': post['resumen'],
            'datePublished': post['fecha_iso'], 'dateModified': post['fecha_iso'],
            'author': {'@type': 'Organization', 'name': 'Clima Baires', '@id': DOMINIO + '/#negocio'},
            'publisher': {'@id': DOMINIO + '/#negocio'},
            'mainEntityOfPage': f'{DOMINIO}/blog/{post["slug"]}.html',
            'image': f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else '',
            'wordCount': post['palabras'],
            'inLanguage': 'es-ES',
        },
    ]
    return layout(1, f'{post["titulo"]} | Clima Baires', post['resumen'],
        c, f'{DOMINIO}/blog/{post["slug"]}.html', ld, 'blog', pagina_id=f'blog/{post["slug"]}',
        wsp_barra=f'Hola Clima Baires, he leído «{post["titulo"]}» en vuestro blog y quiero pedir presupuesto.')


def rss(posts):
    ahora = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    items = ''.join(f'''
    <item>
      <title>{p['titulo']}</title>
      <link>{DOMINIO}/blog/{p['slug']}.html</link>
      <guid isPermaLink="true">{DOMINIO}/blog/{p['slug']}.html</guid>
      <description>{p['resumen']}</description>
      <category>{p['categoria_label']}</category>
      <pubDate>{datetime.combine(p['fecha'], datetime.min.time()).strftime('%a, %d %b %Y')} 09:00:00 +0000</pubDate>
    </item>''' for p in posts)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Blog de Clima Baires</title>
  <link>{DOMINIO}/blog/</link>
  <description>Guías de aire acondicionado para toda la Costa del Sol.</description>
  <language>es-ES</language>
  <lastBuildDate>{ahora}</lastBuildDate>{items}
</channel></rss>
'''


# ---------------- LEGALES (marco español) ----------------
# Estas tres páginas no son la traducción de las argentinas: cambia la ley
# aplicable, cambian los derechos y cambian los plazos. Ver web-es/README.md.

def pagina_aviso_legal():
    e = EMPRESA
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Aviso legal</nav>
    <h1>Aviso legal</h1>
    <p class="bajada">Quién hay detrás de esta web, con los datos que exige la ley.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Datos identificativos del prestador</h2>
    <p>En cumplimiento del artículo 10 de la Ley 34/2002, de servicios de la sociedad de la información y de comercio electrónico (LSSI-CE), se informa de que este sitio web es titularidad de:</p>
    <ul class="lista-check">
      <li><strong>Denominación social:</strong> {e['razon_social']}</li>
      <li><strong>CIF/NIF:</strong> {e['cif']}</li>
      <li><strong>Domicilio social:</strong> {e['domicilio']}</li>
      <li><strong>Datos registrales:</strong> {e['registro']}</li>
      <li><strong>Email de contacto:</strong> <a data-email href="#"></a></li>
      <li><strong>WhatsApp:</strong> <span data-wsp-num></span></li>
      <li><strong>Actividad:</strong> venta, instalación y mantenimiento de instalaciones de climatización</li>
      <li><strong>Ámbito de actuación:</strong> {COBERTURA}</li>
    </ul>

    <h2 style="margin-top:34px">Objeto</h2>
    <p>Este sitio informa de los servicios de climatización que prestamos y permite ponerse en contacto con nosotros para pedir presupuesto o concertar una visita técnica. No es una tienda en línea: aquí no se compra ni se paga nada. La contratación se cierra después, con un presupuesto firmado.</p>

    <h2 style="margin-top:34px">Condiciones de uso</h2>
    <p>Al usar esta web te comprometes a hacerlo conforme a la ley y a no utilizarla para fines ilícitos, ni de forma que pueda dañar el sitio o impedir su uso normal por otras personas. Nos reservamos el derecho de modificar los contenidos sin aviso previo, y de retirar temporalmente el acceso por mantenimiento.</p>

    <h2 style="margin-top:34px">Propiedad intelectual e industrial</h2>
    <p>Los textos, el diseño, el código, las fotografías de obras y los elementos de marca de este sitio son de {e['razon_social']} o se usan con autorización, y están protegidos por la normativa de propiedad intelectual e industrial. Su reproducción, distribución o transformación sin autorización expresa no está permitida.</p>
    <p style="margin-top:12px">Las marcas de fabricantes de equipos que aparecen en el sitio pertenecen a sus titulares y se muestran únicamente para indicar con qué equipos trabajamos.</p>

    <h2 style="margin-top:34px">Responsabilidad</h2>
    <p>La información publicada tiene carácter orientativo. Las herramientas de cálculo del sitio, como la <a href="calculadora-frigorias.html">calculadora de frigorías</a>, dan una estimación y no sustituyen a la visita técnica ni al proyecto de instalación cuando la normativa lo exige.</p>
    <p style="margin-top:12px">Los enlaces a sitios de terceros —Google, WhatsApp— se ofrecen para tu comodidad y no implican que controlemos sus contenidos ni sus políticas.</p>

    <h2 style="margin-top:34px">Protección de datos y cookies</h2>
    <p>El tratamiento de datos personales se detalla en la <a href="privacidad.html">política de privacidad</a> y el uso de cookies, en la <a href="cookies.html">política de cookies</a>.</p>

    <h2 style="margin-top:34px">Legislación aplicable</h2>
    <p>Este aviso legal se rige por la legislación española. Para cualquier controversia derivada del uso del sitio serán competentes los juzgados y tribunales que correspondan según la normativa aplicable; tratándose de personas consumidoras, los de su domicilio.</p>
  </div>
</section>
'''
    return layout(0, 'Aviso legal | Clima Baires',
        'Datos identificativos del titular de climabaires.es conforme al artículo 10 de la LSSI-CE: denominación social, CIF, domicilio y datos registrales.',
        c, f'{DOMINIO}/aviso-legal.html', jsonld_migas([('Inicio', '/'), ('Aviso legal', '/aviso-legal.html')]), '',
        pagina_id='aviso-legal')


def pagina_privacidad():
    e = EMPRESA
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Privacidad</nav>
    <h1>Política de privacidad</h1>
    <p class="bajada">Qué datos te pedimos, con qué base legal los usamos y cómo ejercer tus derechos.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Responsable del tratamiento</h2>
    <p>{e['razon_social']}, CIF {e['cif']}, con domicilio en {e['domicilio']}. Contacto en materia de protección de datos: <a data-email href="#"></a>. Responsable: {e['responsable_datos']}.</p>
    <p style="margin-top:12px">Esta política se ajusta al Reglamento (UE) 2016/679, General de Protección de Datos (RGPD), y a la Ley Orgánica 3/2018, de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD).</p>

    <h2 style="margin-top:34px">Qué datos tratamos, para qué y con qué base legal</h2>
    <table class="simple">
      <thead><tr><th>Datos</th><th>Finalidad</th><th>Base legal</th><th>Conservación</th></tr></thead>
      <tbody>
        <tr>
          <td>Nombre, zona, tipo de servicio y de equipo, y lo que nos cuentes en el asistente o en el formulario</td>
          <td>Preparar tu presupuesto y concertar la visita técnica</td>
          <td>Aplicación de medidas precontractuales a petición tuya (art. 6.1.b RGPD)</td>
          <td>Mientras dure la gestión; si no hay contrato, un año desde el último contacto</td>
        </tr>
        <tr>
          <td>Datos de cliente y de la instalación, y datos de facturación</td>
          <td>Ejecutar el contrato, prestar la garantía y cumplir las obligaciones fiscales y las propias de una instalación térmica</td>
          <td>Ejecución del contrato (art. 6.1.b) y obligación legal (art. 6.1.c)</td>
          <td>Durante la relación y los plazos legales de conservación (mercantil y fiscal)</td>
        </tr>
        <tr>
          <td>Datos de navegación: páginas vistas y clics en los botones de contacto</td>
          <td>Medir qué contenidos funcionan y la eficacia de la publicidad</td>
          <td>Tu consentimiento (art. 6.1.a), que puedes retirar cuando quieras</td>
          <td>Según la retención configurada en Google Analytics (14 meses)</td>
        </tr>
      </tbody>
    </table>
    <p style="margin-top:14px">El asistente del sitio y el formulario de contacto <strong>no guardan nada en esta web</strong>: preparan un mensaje que abres tú en WhatsApp. Desde ese momento la conversación se rige también por las condiciones de WhatsApp (Meta).</p>

    <h2 style="margin-top:34px">Destinatarios</h2>
    <p>No vendemos ni cedemos bases de datos. Acceden a datos, como encargados del tratamiento, los proveedores que necesitamos para funcionar: Google Ireland Ltd. (Analytics, Tag Manager, Maps y Calendar) y WhatsApp Ireland Ltd. (Meta) para la mensajería, además de nuestra asesoría y nuestro proveedor de hosting. Algunos de estos proveedores pueden realizar transferencias internacionales de datos a Estados Unidos, amparadas en el Marco de Privacidad de Datos UE-EE. UU. o en las cláusulas contractuales tipo de la Comisión Europea.</p>

    <h2 style="margin-top:34px">Tus derechos</h2>
    <p>Puedes ejercer en cualquier momento los derechos de <strong>acceso, rectificación, supresión, oposición, limitación del tratamiento, portabilidad</strong> y a <strong>no ser objeto de decisiones automatizadas</strong>, escribiendo a <a data-email href="#"></a> e indicando qué derecho ejerces. Responderemos en el plazo de un mes, ampliable a dos si la solicitud es compleja. Si has dado tu consentimiento para algo, puedes retirarlo cuando quieras sin que eso afecte a lo tratado antes.</p>
    <p style="margin-top:12px">Si crees que no hemos atendido bien tu solicitud, puedes reclamar ante la <strong>Agencia Española de Protección de Datos</strong> (AEPD), C/ Jorge Juan 6, 28001 Madrid, autoridad de control competente.</p>

    <h2 style="margin-top:34px">Seguridad y menores</h2>
    <p>Aplicamos medidas técnicas y organizativas razonables para proteger los datos que tratamos. Este sitio no está dirigido a menores de 14 años y no recogemos sus datos de forma consciente.</p>

    <h2 style="margin-top:34px">Cookies</h2>
    <p>El detalle de las cookies que usamos, para qué sirven y cómo revocar tu consentimiento está en la <a href="cookies.html">política de cookies</a>. Nada que no sea estrictamente necesario se carga antes de que lo aceptes.</p>
  </div>
</section>
'''
    return layout(0, 'Política de privacidad | Clima Baires',
        'Qué datos personales trata climabaires.es, con qué base legal, cuánto se conservan y cómo ejercer tus derechos conforme al RGPD y la LOPDGDD.',
        c, f'{DOMINIO}/privacidad.html', jsonld_migas([('Inicio', '/'), ('Privacidad', '/privacidad.html')]), '',
        pagina_id='privacidad')


def pagina_cookies():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Cookies</nav>
    <h1>Política de cookies</h1>
    <p class="bajada">Qué se carga, cuándo, y cómo cambiar de idea en dos clics.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Qué es una cookie</h2>
    <p>Una cookie es un archivo pequeño que un sitio guarda en tu navegador para recordar algo entre páginas o entre visitas. Junto a las cookies usamos también el almacenamiento local del navegador, que funciona igual a estos efectos y está sujeto a las mismas reglas.</p>

    <h2 style="margin-top:34px">Qué usamos en este sitio</h2>
    <p>Este sitio es estático y no tiene cuentas de usuario, así que la lista es corta.</p>
    <table class="simple">
      <thead><tr><th>Nombre</th><th>Titular</th><th>Para qué</th><th>Duración</th></tr></thead>
      <tbody>
        <tr><td>cb-cookies</td><td>Propia</td><td>Recordar si has aceptado o rechazado. Es la que evita volver a preguntarte en cada página</td><td>Almacenamiento local, hasta que la borres</td></tr>
        <tr><td>cbNudge</td><td>Propia</td><td>No repetir el aviso del botón flotante en la misma sesión</td><td>Sesión</td></tr>
        <tr><td>_ga, _ga_*</td><td>Google Analytics</td><td>Medir visitas y qué contenidos funcionan</td><td>Hasta 2 años</td></tr>
        <tr><td>_gcl_*</td><td>Google Ads</td><td>Atribuir a la campaña correcta las consultas que llegan desde un anuncio</td><td>Hasta 90 días</td></tr>
        <tr><td>NID, CONSENT y similares</td><td>Google Maps y Google Calendar</td><td>Se instalan al cargar el mapa de nuestra ficha y la agenda de citas</td><td>Variable, fijada por Google</td></tr>
      </tbody>
    </table>
    <p style="margin-top:14px">Las dos primeras son <strong>técnicas o necesarias</strong> y no requieren consentimiento. El resto son <strong>analíticas, publicitarias y de terceros</strong>: no se cargan hasta que las aceptas.</p>

    <h2 style="margin-top:34px">Cómo funciona el consentimiento aquí</h2>
    <ul class="lista-check">
      <li>Al entrar por primera vez verás una banda inferior con dos botones del mismo tamaño: <strong>Aceptar</strong> y <strong>Rechazar</strong>. No hay muro: puedes leer el sitio entero sin decidir.</li>
      <li>Mientras no aceptes, <strong>no se carga Google Tag Manager</strong>, ni el mapa de Google en la página de contacto, ni el iframe de la agenda de citas.</li>
      <li>Si rechazas, el sitio funciona igual. Lo único que pierdes es el mapa incrustado y la reserva desde la propia página; los dos tienen su botón, que abre Google en otra pestaña cuando tú lo decides.</li>
      <li>Usamos el modo de consentimiento de Google, de forma que las etiquetas arrancan con todos los permisos denegados y sólo se actualizan si aceptas.</li>
    </ul>

    <h2 style="margin-top:34px">Cómo cambiar de idea</h2>
    <p>En el pie de cualquier página tienes el enlace <strong>«Preferencias de cookies»</strong>: al pulsarlo se borra tu elección anterior y vuelve a aparecer la banda para que decidas de nuevo. También puedes borrar o bloquear cookies desde la configuración de tu navegador —Chrome, Firefox, Safari y Edge lo permiten—; el sitio seguirá funcionando.</p>

    <h2 style="margin-top:34px">Terceros</h2>
    <p>El tratamiento que hacen Google y Meta de los datos recogidos por sus propias cookies se rige por sus políticas de privacidad, que puedes consultar en sus sitios. Nuestro tratamiento está descrito en la <a href="privacidad.html">política de privacidad</a>.</p>
  </div>
</section>
'''
    return layout(0, 'Política de cookies | Clima Baires',
        'Qué cookies usa climabaires.es, cuáles son necesarias, cuáles requieren tu consentimiento previo y cómo revocarlo en cualquier momento.',
        c, f'{DOMINIO}/cookies.html', jsonld_migas([('Inicio', '/'), ('Cookies', '/cookies.html')]), '',
        pagina_id='cookies')


def pagina_terminos():
    e = EMPRESA
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Términos</nav>
    <h1>Términos y condiciones</h1>
    <p class="bajada">Cómo contratamos, qué cubre la garantía y cómo desistir de una compra.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Quién presta el servicio</h2>
    <p>{e['razon_social']}, CIF {e['cif']}, con domicilio social en {e['domicilio']}. Datos registrales: {e['registro']}. Los datos completos están en el <a href="aviso-legal.html">aviso legal</a>.</p>
    <p style="margin-top:12px">Estas condiciones se rigen por el Real Decreto Legislativo 1/2007, texto refundido de la Ley General para la Defensa de los Consumidores y Usuarios (TRLGDCU), y demás normativa española y europea aplicable.</p>

    <h2 style="margin-top:34px">Presupuestos</h2>
    <p>El presupuesto que enviamos por WhatsApp o por email es orientativo hasta la visita técnica. Después de la visita pasa a ser cerrado: incluye equipo, materiales, mano de obra y retirada de residuos de obra, y no cambia salvo que pidas algo distinto. Si durante la instalación aparece un imprevisto que suma coste, te lo enseñamos y lo autorizas antes de hacerlo.</p>
    <p style="margin-top:12px">Los precios se indican en euros. Salvo que se diga lo contrario, el presupuesto detalla si el IVA está incluido y qué tipo se aplica. La <a href="calculadora-frigorias.html">calculadora de frigorías</a> del sitio es una herramienta orientativa y no sustituye a la visita técnica.</p>

    <h2 id="desistimiento" style="margin-top:34px">Derecho de desistimiento</h2>
    <p>Cuando contratas como persona consumidora fuera de nuestro establecimiento o a distancia —por WhatsApp, por teléfono o a raíz de una visita a tu domicilio—, tienes <strong>14 días naturales</strong> para desistir sin necesidad de justificarlo y sin penalización, conforme a los artículos 102 y siguientes del TRLGDCU. El plazo se cuenta desde la celebración del contrato en el caso de los servicios y desde la entrega del equipo en el caso de los bienes.</p>
    <ul class="lista-check">
      <li>Para ejercerlo basta con comunicárnoslo por cualquier medio que deje constancia: email a <a data-email href="#"></a> o mensaje de WhatsApp. También puedes usar el formulario de desistimiento del anexo A del TRLGDCU, aunque no es obligatorio.</li>
      <li>Te devolveremos lo pagado en un plazo máximo de 14 días naturales desde que recibamos tu comunicación, por el mismo medio de pago que usaste.</li>
      <li>Si pediste expresamente que empezáramos el servicio antes de que terminara el plazo y luego desistes, deberás abonar la parte proporcional al trabajo ya realizado hasta ese momento.</li>
      <li>Si el equipo ya se ha entregado, coordinamos la recogida.</li>
    </ul>

    <h2 style="margin-top:34px">Garantías</h2>
    <ul class="lista-check">
      <li><strong>Garantía legal de conformidad</strong>: como persona consumidora dispones de tres años desde la entrega para las faltas de conformidad del equipo, según los artículos 114 y siguientes del TRLGDCU. Guarda la factura: es lo que acredita la fecha.</li>
      <li><strong>Garantía comercial del fabricante</strong>: la que ofrezca la marca y el modelo, que se suma a la anterior y nunca la sustituye. Te entregamos la documentación con la factura.</li>
      <li><strong>Garantía de la instalación</strong>: {GARANTIA_INSTALACION}. Cubre defectos de montaje —fugas en las uniones, fallos de desagüe, fijaciones y puesta en marcha— y se reclama por WhatsApp o por email; la atendemos sin coste.</li>
      <li>Quedan fuera de la garantía de instalación los daños por uso indebido, sobretensiones, falta del mantenimiento recomendado o intervención de terceros no autorizados.</li>
    </ul>

    <h2 style="margin-top:34px">Obligaciones del cliente</h2>
    <p>Para que podamos trabajar necesitamos acceso a la vivienda el día acordado, y que nos digas si la comunidad de propietarios, la urbanización o el ayuntamiento exigen algún permiso, licencia de obra menor o declaración responsable para la instalación prevista. Nosotros preparamos la documentación técnica que se nos pida; la titularidad de la solicitud, cuando la normativa la atribuye a la propiedad, corresponde al cliente.</p>

    <h2 style="margin-top:34px">Formas de pago</h2>
    <p>Transferencia bancaria, tarjeta y financiación cuando esté disponible. Las condiciones vigentes se detallan junto con el presupuesto.</p>

    <h2 style="margin-top:34px">Marcas</h2>
    <p>Las marcas de los fabricantes que aparecen en el sitio pertenecen a sus titulares y se muestran para indicar con qué equipos trabajamos. Clima Baires es un instalador independiente: salvo que se indique lo contrario, no somos distribuidor oficial ni servicio técnico autorizado de esas marcas.</p>

    <h2 style="margin-top:34px">Reclamaciones y resolución de conflictos</h2>
    <p>Ante cualquier problema escríbenos primero: resolvemos casi todo en el día. Disponemos de hojas de reclamaciones oficiales a disposición de las personas consumidoras. Si no llegamos a un acuerdo, puedes acudir a la Oficina Municipal de Información al Consumidor de tu localidad o a la Dirección General de Consumo de la Junta de Andalucía, y presentar tu reclamación en línea a través de la <a href="https://www.consumo.gob.es" rel="noopener" target="_blank">sede del Ministerio de Consumo</a>.</p>
  </div>
</section>
'''
    return layout(0, 'Términos y condiciones | Clima Baires',
        'Condiciones de contratación, presupuestos cerrados, garantías del TRLGDCU y derecho de desistimiento de 14 días naturales.',
        c, f'{DOMINIO}/terminos.html', jsonld_migas([('Inicio', '/'), ('Términos', '/terminos.html')]), '',
        pagina_id='terminos')


def pagina_404():
    c = '''
<section class="seccion centrado" style="padding:120px 0">
  <div class="contenedor">
    <h1>Vaya, esta página se ha quedado sin frío</h1>
    <p class="intro" style="margin-top:14px">La dirección que buscas no existe o ha cambiado de sitio.</p>
    <a class="boton" href="index.html">Volver al inicio</a>
  </div>
</section>
'''
    return layout(0, 'Página no encontrada | Clima Baires', 'Página no encontrada.', c, f'{DOMINIO}/404.html', None, '', pagina_id='404')

# ---------------- ESCRITURA ----------------

def escribir(ruta, contenido):
    destino = os.path.join(RAIZ, ruta)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if ruta.endswith('.html'):
        contenido = hornear_enlaces(contenido)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print('  ✓', ruta)

POSTS = _blog.cargar()

paginas = {
    'index.html': pagina_index(),
    'servicios.html': pagina_servicios(),
    'obras.html': pagina_obras(),
    'calculadora-frigorias.html': pagina_calculadora(),
    'sobre-nosotros.html': pagina_nosotros(),
    'contacto.html': pagina_contacto(),
    'aviso-legal.html': pagina_aviso_legal(),
    'privacidad.html': pagina_privacidad(),
    'cookies.html': pagina_cookies(),
    'terminos.html': pagina_terminos(),
    '404.html': pagina_404(),
}
for z in ZONAS:
    paginas[f'zonas/{z[0]}.html'] = pagina_zona(*z)

paginas['blog/index.html'] = pagina_blog(POSTS)
for post in POSTS:
    paginas[f'blog/{post["slug"]}.html'] = pagina_post(post, [o for o in POSTS if o is not post])

for ruta, html in paginas.items():
    escribir(ruta, html)

# Zonas borradas o renombradas: el .html viejo se queda huérfano en el disco y
# Google lo sigue mostrando. Al cambiar las seis zonas del AMBA por las de la
# Costa del Sol esto no es teórico: pasa en la primera compilación.
vivas_zonas = {os.path.basename(r) for r in paginas if r.startswith('zonas/')}
carpeta_zonas = os.path.join(RAIZ, 'zonas')
if os.path.isdir(carpeta_zonas):
    for archivo in sorted(os.listdir(carpeta_zonas)):
        if archivo.endswith('.html') and archivo not in vivas_zonas:
            os.remove(os.path.join(carpeta_zonas, archivo))
            print('  ✗', f'zonas/{archivo}', '(zona que ya no existe)')

# Entradas borradas o renombradas: si el .html viejo se queda, Google lo sigue
# mostrando y el visitante aterriza en una página que ya no está en el índice.
vivas = {os.path.basename(r) for r in paginas if r.startswith('blog/')}
for archivo in sorted(os.listdir(os.path.join(RAIZ, 'blog'))):
    if archivo.endswith('.html') and archivo not in vivas:
        os.remove(os.path.join(RAIZ, 'blog', archivo))
        print('  ✗', f'blog/{archivo}', '(entrada que ya no existe)')

# sitemap + robots
urls = [f'{DOMINIO}/'] + [
    f'{DOMINIO}/blog/' if r == 'blog/index.html' else f'{DOMINIO}/{r}'
    for r in paginas if r not in ('index.html', '404.html')
]
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)
sitemap += '</urlset>\n'
escribir('sitemap.xml', sitemap)
escribir('blog/rss.xml', rss(POSTS))
escribir('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n')
print(f'Listo: {len(paginas)} páginas + sitemap + robots.')
