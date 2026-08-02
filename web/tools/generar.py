# -*- coding: utf-8 -*-
"""Generador de páginas estáticas de climabaires.com.
Uso: python3 web/tools/generar.py   (desde la raíz del repo)
Regenera todos los .html a partir del layout y el contenido de PAGINAS.
Los .html generados son el artefacto desplegable: no requieren build en el hosting.
"""
import os, re, sys, json
from datetime import date, datetime, timezone
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog as _blog          # noqa: E402  (necesita el sys.path de arriba)

RAIZ = os.path.join(os.path.dirname(__file__), '..')
DOMINIO = 'https://climabaires.com'

# ---------------- ENLACES DE WHATSAPP SIN JS ----------------
# El número sigue teniendo UN solo punto de configuración (objeto CB en
# assets/js/main.js). Acá lo leemos para hornear un href real en cada CTA: si el
# JS no carga, los botones siguen abriendo WhatsApp con su mensaje prellenado.
# main.js después reescribe esos mismos href (y agrega la medición) sin cambiar
# el destino, así que no hay dato de contacto duplicado a mano.
AGENDA_FALLBACK = 'Hola Clima Baires, quiero agendar una visita técnica.'

# Identidad legal del proveedor. Obligatoria en Argentina para operar (Ley 24.240
# y RG de ARCA) y además la piden las administraciones de countries para habilitar
# el ingreso de un contratista. Mientras diga PENDIENTE, publicar.py no arma el
# paquete: son datos que sólo puede completar el dueño.
EMPRESA = {
    'razon_social': 'PENDIENTE — razón social inscripta',
    'cuit': 'PENDIENTE — CUIT',
    'domicilio': 'PENDIENTE — domicilio fiscal',
    'inicio_actividades': 'PENDIENTE — fecha de inicio de actividades',
    'responsable_datos': 'Ignacio (responsable de la base de datos)',
}

# Metros de cañería que entran en el precio cerrado (bloque «qué entra y qué se
# cobra aparte» de servicios.html). Es el único número del bloque y la promesa
# más concreta del sitio: publicarlo mal es peor que no publicarlo, así que
# publicar.py se niega a compilar mientras siga en PENDIENTE.
METROS_INCLUIDOS = 'tres'


def _faq_zonas():
    """Preguntas frecuentes por zona, desde contenido/faq-zonas.json."""
    ruta = os.path.join(RAIZ, 'contenido', 'faq-zonas.json')
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding='utf-8') as f:
        return json.load(f).get('zonas', {})


FAQ_ZONAS = _faq_zonas()


def _config_de_main_js():
    ruta = os.path.join(RAIZ, 'assets', 'js', 'main.js')
    with open(ruta, encoding='utf-8') as f:
        js = f.read()
    cfg = {}
    for clave in ('whatsapp', 'whatsappVisible', 'email', 'horario', 'instagram', 'linkedin'):
        m = re.search(r"%s:\s*'([^']*)'" % clave, js)
        if not m:
            raise SystemExit('No pude leer CB.%s de assets/js/main.js' % clave)
        cfg[clave] = m.group(1)
    return cfg


CB = _config_de_main_js()
WSP_NUM = CB['whatsapp']


def hornear_enlaces(html):
    """Reemplaza los href='#' de los CTA por enlaces reales de wa.me."""
    def enlace(mensaje):
        return 'https://wa.me/%s?text=%s' % (WSP_NUM, quote(mensaje))

    # target/rel horneados: el clic abre WhatsApp en otra pestaña y el documento
    # no se descarga, así el evento de conversión alcanza a salir hacia GTM
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
# Índice generado por tools/fotos.py (ver web/README.md → "Cómo añadir fotos").
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

ZONAS = [
    ('nunez', 'Núñez', 'CABA',
     'Núñez y el bajo Belgrano: casas, PH y departamentos con instalaciones que exigen prolijidad, silencio y respeto por el edificio.',
     ['Núñez', 'Bajo Núñez', 'Barrio River', 'Saavedra lindero'],
     'Trabajamos coordinando con administraciones y consorcios: pedimos autorizaciones, protegemos espacios comunes y retiramos todos los residuos de obra.'),
    ('vicente-lopez', 'Vicente López', 'zona norte GBA',
     'Olivos, La Lucila, Florida y Munro: el corazón residencial consolidado de la zona norte, donde renovar equipos viejos por inverter eficientes es la obra más pedida.',
     ['Olivos', 'La Lucila', 'Florida', 'Munro', 'Villa Adelina'],
     'Recambio de equipos antiguos con retiro del equipo viejo incluido, y propuestas de multisplit para casas reformadas.'),
    ('san-isidro', 'San Isidro', 'zona norte GBA',
     'Casas grandes, jardines y arboledas: San Isidro, Martínez, Acassuso, Beccar y las Lomas piden potencia bien distribuida y equipos silenciosos.',
     ['San Isidro centro', 'Lomas de San Isidro', 'Martínez', 'Acassuso', 'Beccar', 'Boulogne'],
     'Especialistas en casas de dos plantas: multisplit, piso-techo para livings amplios y ubicación de condensadoras que no arruine la fachada.'),
    ('tigre', 'Tigre', 'zona norte GBA',
     'De Rincón de Milberg a los barrios náuticos: Tigre combina obra nueva acelerada y casas frente al agua donde la salinidad y la humedad exigen instalar bien desde el día uno.',
     ['Tigre centro', 'Rincón de Milberg', 'Troncos del Talar', 'General Pacheco', 'Barrios náuticos'],
     'Instalación pensada para ambientes húmedos: protección anticorrosiva de ménsulas, desagües bien resueltos y mantenimiento preventivo anual.'),
    ('nordelta', 'Nordelta', 'Tigre',
     'La ciudad-pueblo más grande del país merece un servicio a su altura: ingreso con seguros al día, trabajo prolijo y posventa real, barrio por barrio.',
     ['La Isla', 'El Golf', 'Los Castores', 'La Alameda', 'Los Lagos', 'El Palmar', 'Las Caletas', 'Portezuelo'],
     'Cumplimos los requisitos de acceso de la AVN y de cada barrio: seguros con cláusula de no repetición, personal identificado y coordinación con la administración. También trabajamos con unidades a estrenar: si tu departamento o casa se entrega con preinstalación, cotizamos equipo + instalación llave en mano para el día de la mudanza.'),
    ('pilar', 'Pilar', 'km 40-60 Panamericana',
     'Más de 300 countries y barrios cerrados: Pilar es la capital argentina de la casa con parque, y cada casa nueva necesita climatización bien proyectada.',
     ['Pilar centro', 'Manzanares', 'La Lonja', 'Ayres de Pilar', 'Manuel Alberti', 'Del Viso', 'Zelaya'],
     'Acompañamos obras nuevas desde la preinstalación (caños embutidos antes del yeso) hasta la puesta en marcha, y damos servicio posventa sin que tengas que perseguir al instalador.'),
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
    # WhatsApp es el canal nº1: al compartir un link tiene que verse una obra, no
    # el isotipo. Si la página no trae uno propio, cae en la foto de portada.
    por_defecto = f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else f'{DOMINIO}/assets/img/icon-512.png'
    og = og_image or por_defecto
    barra_msj = wsp_barra or 'Hola Clima Baires, quiero pedir un presupuesto.'
    return f'''<!DOCTYPE html>
<html lang="es-AR">
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
<meta property="og:locale" content="es_AR">
<meta property="og:site_name" content="Clima Baires Argentina">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0058B3">
<meta name="color-scheme" content="light">
<link rel="icon" type="image/png" sizes="48x48" href="{p}assets/img/favicon-48.png">
<link rel="apple-touch-icon" href="{p}assets/img/icon-192.png">
<link rel="stylesheet" href="{p}assets/css/styles.css">
<link rel="alternate" type="application/rss+xml" title="Notas de Clima Baires" href="{p}blog/rss.xml">
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
      <a href="{p}blog/"{act('blog')}>Notas</a>
      <a href="{p}index.html#zonas"{act('zonas')}>Zonas</a>
      <a href="{p}calculadora-frigorias.html"{act('calc')}>Calculadora</a>
      <a href="{p}sobre-nosotros.html"{act('nosotros')}>Nosotros</a>
      <a href="{p}contacto.html"{act('contacto')}>Contacto</a>
      <a class="boton celeste" data-wsp="Hola Clima Baires, quiero pedir un presupuesto." data-origen="menu" href="#">Pedir presupuesto</a>
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
        <p>Venta, instalación y posventa de aire acondicionado en el corredor norte de Buenos Aires. Tu confort, nuestra prioridad.</p>
      </div>
      <div>
        <h2>Servicios</h2>
        <ul>
          <li><a href="{p}servicios.html#venta">Venta de equipos</a></li>
          <li><a href="{p}servicios.html#instalacion">Instalación</a></li>
          <li><a href="{p}servicios.html#mantenimiento">Mantenimiento y posventa</a></li>
          <li><a href="{p}obras.html">Obras recientes</a></li>
          <li><a href="{p}blog/">Notas</a></li>
          <li><a href="{p}calculadora-frigorias.html">Calculadora de frigorías</a></li>
        </ul>
      </div>
      <div>
        <h2>Zonas</h2>
        <ul>
          <li><a href="{p}zonas/nunez.html">Núñez</a></li>
          <li><a href="{p}zonas/vicente-lopez.html">Vicente López</a></li>
          <li><a href="{p}zonas/san-isidro.html">San Isidro</a></li>
          <li><a href="{p}zonas/tigre.html">Tigre</a></li>
          <li><a href="{p}zonas/nordelta.html">Nordelta</a></li>
          <li><a href="{p}zonas/pilar.html">Pilar</a></li>
        </ul>
      </div>
      <div>
        <h2>Contacto</h2>
        <ul>
          <li>WhatsApp: <span data-wsp-num></span></li>
          <li><a data-email href="#"></a></li>
          <li><span data-horario></span></li>
          <li><a data-ig href="#" rel="noopener">Instagram</a> · <a data-li href="#" rel="noopener">LinkedIn</a></li>
        </ul>
      </div>
    </div>
    <div class="legal">
      <span>© <span data-anio></span> Clima Baires Argentina · {EMPRESA['razon_social']} · CUIT {EMPRESA['cuit']}</span>
      <span><a href="{p}privacidad.html">Privacidad</a> · <a href="{p}terminos.html">Términos y condiciones</a> · <a href="{p}terminos.html#revocacion">Botón de arrepentimiento</a></span>
    </div>
    <div class="legal" style="border:0;padding-top:8px">
      <span>Corredor norte AMBA: Núñez · Vicente López · San Isidro · Tigre · Nordelta · Pilar</span>
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

<button class="wsp-flotante" type="button" data-origen="flotante" aria-label="Chateá con nosotros por WhatsApp">
  <svg viewBox="0 0 32 32"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.1.6 4.2 1.7 6L4 29l8.2-1.6c1.2.6 2.5.9 3.8.9 6.6 0 12-5.4 12-12S22.6 3 16 3zm6.1 16.9c-.3.8-1.5 1.5-2.1 1.6-.6.1-1.3.2-3.6-.8-3-1.2-4.9-4.3-5.1-4.5-.1-.2-1.2-1.6-1.2-3.1s.8-2.2 1-2.5c.3-.3.6-.4.8-.4h.6c.2 0 .4 0 .7.5.3.6.9 2.1.9 2.3.1.2.1.3 0 .5-.1.2-.1.3-.3.5l-.4.5c-.2.2-.3.4-.1.7.2.3.9 1.5 2 2.4 1.4 1.2 2.5 1.6 2.9 1.8.3.2.5.1.7-.1l1.1-1.3c.2-.3.5-.2.8-.1l2.3 1.1c.3.2.5.2.6.4 0 .1 0 .8-.3 1.5z"/></svg>
  <span class="wsp-texto">Escribinos</span>
</button>

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

def jsonld_local(nombre, url, zona=None):
    """Ficha del negocio. Siempre el MISMO @id: sin él, Google leía una empresa
    distinta por página (13 en total) en vez de una con 13 páginas."""
    areas = [z[1] for z in ZONAS] if zona is None else [zona]
    return {
        '@context': 'https://schema.org',
        '@type': 'HVACBusiness',
        '@id': DOMINIO + '/#negocio',
        'name': 'Clima Baires Argentina',
        'url': DOMINIO + '/',
        'image': DOMINIO + '/assets/img/obras/og-home.jpg' if HAY_FOTOS else DOMINIO + '/assets/img/icon-512.png',
        'description': nombre,
        'email': 'info@climabaires.com',
        'priceRange': '$$',
        'areaServed': [{'@type': 'Place', 'name': a} for a in areas],
        'knowsAbout': ['aire acondicionado', 'instalación de split', 'mantenimiento HVAC', 'climatización residencial'],
        'openingHours': 'Mo-Sa 08:00-19:00',
        'sameAs': ['https://www.climabaires.es'],
    }


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
    areas = [z[1] for z in ZONAS] if zona is None else [zona]
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
        <img class="hero-foto" src="assets/img/obras/instalacion-cassette-oficina-malaga-01-800.webp"
             srcset="assets/img/obras/instalacion-cassette-oficina-malaga-01-800.webp 648w,
                     assets/img/obras/instalacion-cassette-oficina-malaga-01-1600.webp 1295w"
             sizes="(max-width: 900px) 100vw, 64vw"
             width="1295" height="1600" alt="" fetchpriority="high" decoding="async">
      </div>
    </div>
    <span class="hero-chip"><b>38°</b> <i>afuera</i> → <b>24°</b> <i>adentro</i></span>
  </div>

  <div class="hero-halo" aria-hidden="true"></div>
  <div class="hero-dial" aria-hidden="true"><u>24°</u><s>adentro</s><em>38°</em></div>'''
    c = f'''
<section class="hero">
  <div class="contenedor hero-caja">
    <div class="hero-txt">
      <p class="hero-kicker"><span class="hero-copo">❄</span><b>Aire acondicionado · corredor norte</b><i></i></p>
      <h1 class="hero-tit">Tu casa a <em>24°</em>,<br>todo el verano.</h1>
      <p class="hero-sub">Equipo + instalación certificada + posventa. <b>Precio cerrado en el día.</b></p>
      <div class="hero-acciones">
        <a class="hero-cta" data-wsp="Hola Clima Baires, quiero un presupuesto de equipo + instalación." data-origen="hero" href="#">
          {WSP_SVG_CTA}
          Pedir presupuesto
        </a>
        <a class="hero-cta2" href="calculadora-frigorias.html">Calcular frigorías <span>→</span></a>
      </div>
      <p class="hero-nota"><span class="hero-pulso" aria-hidden="true"></span><span data-respuesta>Respondemos en minutos</span> · Aptos countries y barrios cerrados</p>
    </div>
  </div>

  <div class="hero-regla" aria-hidden="true">
    <div class="contenedor hero-regla-in">
      <span class="izq"><b>Obra propia</b> · Cassette 4 vías · Málaga</span>
    </div>
  </div>
{escena}
</section>

{franja_marcas()}

<section class="seccion" id="servicios">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Qué hacemos</span><h2>Vender, instalar, responder.</h2></div>
    <div class="grilla tres" style="margin-top:30px">
      {tarjeta_servicio('venta', 'venta', 'Venta de equipos', 'La potencia justa para tu ambiente. Un solo precio: equipo + materiales + instalación.', [])}
      {tarjeta_servicio('instalacion', 'instalacion', 'Instalación certificada', 'Vacío de cañería, prueba de estanqueidad y obra limpia. Siempre.', [])}
      {tarjeta_servicio('mantenimiento', 'mantenimiento', 'Posventa real', 'Seguimos estando después de cobrar: service anual y garantía escrita.', [])}
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 40px">{cinta_cta('¿Cuál de los tres necesitás? Preguntanos sin compromiso.', 'Hola Clima Baires, quiero hacer una consulta sobre sus servicios.', 'Preguntar por WhatsApp')}
</section>

<section class="seccion alterna" id="zonas">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Dónde trabajamos</span><h2>De Núñez a Pilar</h2></div>
    <div class="zona-chips centrado" style="justify-content:center; margin-top:24px">{chips}</div>
  </div>
</section>

<section class="seccion" style="padding:50px 0">
  <div class="contenedor claims">
    <div class="claim"><strong>Presupuesto</strong><span>en el día</span></div>
    <div class="claim"><strong>Precio cerrado</strong><span>sin letra chica</span></div>
    <div class="claim"><strong>Garantía</strong><span>por escrito</span></div>
    <div class="claim"><strong>Countries</strong><span>seguros al día</span></div>
  </div>
</section>

<section class="seccion" style="padding:0 0 40px">{cinta_cta('Contanos qué ambiente querés climatizar y te pasamos precio hoy.', 'Hola Clima Baires, quiero un presupuesto de equipo + instalación.')}
</section>
{seccion_ultimas_obras()}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>¿Instalamos antes del calor?</h2><p>Agendá tu instalación con tiempo: en temporada alta los buenos horarios vuelan.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero agendar una instalación antes del verano." data-origen="seccion" href="#">Hablar por WhatsApp</a>
    </div>
  </div>
</section>
'''
    og = f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else None
    return layout(0, 'Aire acondicionado en zona norte | Clima Baires',
        'Venta, instalación certificada y posventa de aire acondicionado en el corredor norte del AMBA. Presupuesto por WhatsApp el mismo día.',
        c, f'{DOMINIO}/', jsonld_local('Venta, instalación y posventa de aire acondicionado en el corredor norte del AMBA.', DOMINIO + '/'), 'inicio',
        og_image=og, pagina_id='index')


# slug, nombre para el alt, ancho en px a 30 px de alto (evita CLS al cargar)
MARCAS = [
    ('daikin', 'Daikin', 142), ('mitsubishi', 'Mitsubishi Electric', 102), ('lg', 'LG', 68),
    ('samsung', 'Samsung', 90), ('bgh', 'BGH', 76), ('surrey', 'Surrey', 102), ('midea', 'Midea', 78),
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
    """CTA inmediatamente bajo el título: en móvil tiene que entrar en el fold
    (las páginas de zona son las landings de Google Ads)."""
    segundo = secundario or f'<a class="boton fantasma" href="{p}calculadora-frigorias.html">Calcular frigorías</a>'
    return f'''<div class="acciones-cabecera">
      <a class="boton verde" data-wsp="{mensaje}" data-origen="hero" href="#">{primario}</a>
      {segundo}
    </div>'''


def cinta_cta_suelta(titulo, mensaje, boton='Escribinos por WhatsApp', origen='cinta'):
    """La cinta sin el contenedor: para meterla dentro de un bloque que ya tiene
    su propio ancho (el cuerpo de una nota, por ejemplo)."""
    return f'''<div class="cinta-cta">
    {WSP_SVG}
    <p>{titulo}</p>
    <a class="boton verde" data-wsp="{mensaje}" data-origen="{origen}" href="#">{boton}</a>
  </div>'''


def cinta_cta(titulo, mensaje, boton='Escribinos por WhatsApp'):
    """Cinta compacta de conversión: ninguna franja larga de scroll sin CTA."""
    return f'''
<div class="contenedor">
  {cinta_cta_suelta(titulo, mensaje, boton)}
</div>'''


def franja_marcas(p=''):
    logos = ''.join(
        f'<img src="{p}assets/img/marcas/{slug}.png" alt="{nombre}" width="{ancho}" height="30" loading="lazy">'
        for slug, nombre, ancho in MARCAS)
    # la pista se duplica para que el loop no tenga costura; la copia no se
    # anuncia dos veces a los lectores de pantalla
    copia = re.sub(r'alt="[^"]*"', 'alt="" aria-hidden="true"', logos)
    return f'''<div class="franja-marcas" aria-label="Marcas que instalamos">
  <div class="marcas-carrusel">
    <div class="marcas-pista">
      {logos}{copia}
    </div>
  </div>
</div>'''


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
    <p class="intro">Obras de nuestro equipo en la casa matriz de Málaga. Las primeras del corredor norte se suman apenas las hagamos.</p></div>
  </div>
  <div class="obras-carrusel-marco">
    <button class="car-flecha car-prev" type="button" aria-label="Anteriores">‹</button>
    <div class="obras-carrusel" id="obras-carrusel">{slides}</div>
    <button class="car-flecha car-next" type="button" aria-label="Siguientes">›</button>
  </div>
  <div class="contenedor centrado" style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:28px">
    <a class="boton" href="obras.html">Ver todas las obras</a>
    <a class="boton fantasma" data-wsp="Hola Clima Baires, vi sus obras y quiero un presupuesto." data-origen="seccion" href="#">Quiero algo así en casa</a>
  </div>
</section>'''

def pagina_servicios():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Servicios</nav>
    <h1>Servicios de climatización</h1>
    <p class="bajada">Un solo proveedor, de la compra al mantenimiento.</p>
    {acciones_cabecera('Hola Clima Baires, quiero un presupuesto.')}
  </div>
</section>

<section class="seccion" style="padding-top:20px">
  <div class="contenedor">
    <h2 class="centrado" style="margin-bottom:30px">Qué incluye cada servicio</h2>
  </div>
  <div class="contenedor grilla tres">
    {tarjeta_servicio('venta', 'venta', 'Venta de equipos', 'La potencia y la marca justa para cada ambiente. Precio cerrado en una sola cifra.', ['Split inverter, multisplit, piso-techo y conductos', 'Marcas: Daikin, Mitsubishi, LG, Samsung, BGH, Surrey, Midea'])}
    {tarjeta_servicio('instalacion', 'instalacion', 'Instalación certificada', 'La instalación define la vida útil del equipo. Checklist de calidad en cada obra.', ['Vacío de cañería y prueba de estanqueidad, siempre', 'Trabajo en altura con seguros y elementos certificados', 'Coordinación con consorcios y countries'])}
    {tarjeta_servicio('mantenimiento', 'mantenimiento', 'Posventa y mantenimiento', 'Un aire limpio enfría más y gasta menos. Te avisamos nosotros cuando toca.', ['Limpieza profunda + control de gas y consumo', 'Reparaciones multimarca con repuestos originales', 'Prioridad de agenda para clientes con plan'])}
  </div>
</section>

<section class="seccion" style="padding:0 0 50px">{cinta_cta('Contanos qué necesitás y te armamos el presupuesto hoy.', 'Hola Clima Baires, quiero un presupuesto.')}
</section>
{bloque_que_incluye()}
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Cómo trabajamos</span><h2>Cuatro pasos, cero sorpresas</h2></div>
    <div class="grilla dos" style="margin-top:26px">
      <div class="tarjeta"><h3>1 · Contanos qué necesitás</h3><p>Por WhatsApp, con fotos del ambiente. Presupuesto orientativo el mismo día.</p></div>
      <div class="tarjeta"><h3>2 · Visita técnica sin cargo</h3><p>Confirmamos todo en tu casa y el presupuesto pasa a ser cerrado.</p></div>
      <div class="tarjeta"><h3>3 · Instalación con checklist</h3><p>Protegemos, instalamos, probamos y te mostramos todo funcionando.</p></div>
      <div class="tarjeta"><h3>4 · Posventa que responde</h3><p>Garantía escrita y un WhatsApp que contesta cuando lo necesitás.</p></div>
    </div>
    <div class="centrado" style="margin-top:30px; display:flex; gap:14px; justify-content:center; flex-wrap:wrap">
      <a class="boton" data-agenda data-origen="seccion" href="#">Agendar visita técnica</a>
      <a class="boton fantasma" data-wsp="Hola Clima Baires, quiero coordinar una visita técnica." data-origen="seccion" href="#">Consultar por WhatsApp</a>
    </div>
  </div>
</section>

<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>Pedí tu presupuesto hoy</h2><p>Respondemos en menos de 5 minutos en horario comercial.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero un presupuesto de instalación." data-origen="seccion" href="#">Pedir presupuesto</a>
    </div>
  </div>
</section>
'''
    return layout(0, 'Servicios de climatización | Clima Baires',
        'Venta de split, multisplit y conductos, instalación certificada con checklist de calidad y mantenimiento anual en zona norte de Buenos Aires.',
        c, f'{DOMINIO}/servicios.html', [
            jsonld_local('Servicios de venta, instalación y mantenimiento de aire acondicionado.', DOMINIO + '/servicios.html'),
            jsonld_migas([('Inicio', '/'), ('Servicios', '/servicios.html')]),
            jsonld_servicio('Venta e instalación de aire acondicionado',
                            'Venta de equipos split, multisplit, piso-techo y conductos con instalación certificada.'),
            jsonld_servicio('Mantenimiento y service de aire acondicionado',
                            'Limpieza profunda, control de gas y reparación multimarca con repuestos originales.'),
        ], 'servicios',
        pagina_id='servicios')

def pagina_calculadora():
    # mismos coeficientes que main.js: la tabla nunca contradice al widget
    comerciales = [2250, 3000, 4500, 5500, 6500, 9000, 12000, 15000, 18000]
    filas = ''
    for m2, uso in [(10, 'dormitorio chico'), (15, 'dormitorio'), (20, 'dormitorio grande o escritorio'),
                    (25, 'living comedor'), (30, 'living amplio'), (40, 'living comedor integrado'),
                    (50, 'planta baja abierta')]:
        f = m2 * 100
        rec = next((c for c in comerciales if c >= f), comerciales[-1])
        filas += (f'<tr><td>{m2} m²</td><td>{uso}</td><td>{f:,}</td>'
                  f'<td><strong>{rec:,}</strong> frigorías</td></tr>').replace(',', '.')
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Calculadora de frigorías</nav>
    <h1>Calculadora de frigorías</h1>
    <p class="bajada">Completá los datos y en 30 segundos sabés qué equipo necesitás.</p>
    {acciones_cabecera('Hola Clima Baires, quiero saber qué equipo necesito para mi ambiente.', 'Que lo calculen ustedes', secundario='<a class="boton fantasma" data-agenda data-origen="hero" href="#">Agendar visita</a>')}
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
    <form class="calc" id="calc-frigorias">
      <label for="m2">Superficie del ambiente (m²)</label>
      <input type="number" id="m2" name="m2" min="4" max="200" step="0.5" placeholder="Ej.: 25" required>

      <label for="altura">Altura de techo (m)</label>
      <select id="altura" name="altura">
        <option value="2.6" selected>Estándar (2,6 m)</option>
        <option value="3">Alta (3 m)</option>
        <option value="3.5">Muy alta / doble altura (3,5 m+)</option>
      </select>

      <label for="orientacion">Orientación predominante</label>
      <select id="orientacion" name="orientacion">
        <option value="sur" selected>Sur / Este (menos sol)</option>
        <option value="norte">Norte (sol gran parte del día)</option>
        <option value="oeste">Oeste (sol fuerte de tarde)</option>
      </select>

      <label for="ventanales">¿Ventanales grandes o techo expuesto al sol?</label>
      <select id="ventanales" name="ventanales">
        <option value="no" selected>No</option>
        <option value="si">Sí</option>
      </select>

      <label for="personas">Personas que usan el ambiente habitualmente</label>
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
          <a class="boton fantasma" data-agenda data-origen="calculadora" href="#">Agendar visita técnica</a>
        </div>
      </div>

      <p class="nota">El cálculo usa 100 frigorías/m² de referencia, ajustado por altura, orientación, ganancia solar y ocupación. Cocinas, quinchos y ambientes con muchos electrodomésticos pueden requerir más potencia: lo verificamos en la visita técnica.</p>
    </form>
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Te da un número raro? Mandanos las medidas y lo revisamos.', 'Hola Clima Baires, usé la calculadora y quiero verificar el resultado.', 'Consultar')}
</section>

<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Tabla de referencia</span><h2>¿Cuántas frigorías por metro cuadrado?</h2>
    <p class="intro">Valores orientativos para techo estándar de 2,6 m y orientación sur o este. Si el ambiente tiene ventanales grandes, recibe sol de tarde o se usa entre varias personas, sumá potencia: eso lo ajusta la calculadora de arriba.</p></div>
    <table class="simple">
      <thead><tr><th>Superficie</th><th>Ambiente típico</th><th>Frigorías necesarias</th><th>Equipo comercial</th></tr></thead>
      <tbody>{filas}</tbody>
    </table>
  </div>
</section>

<section class="seccion" style="padding:0 0 70px">{cinta_cta('¿Preferís que lo veamos nosotros? Mandanos las medidas por WhatsApp.', 'Hola Clima Baires, quiero saber qué equipo necesito para mi ambiente.', 'Consultar por WhatsApp')}
</section>
'''
    return layout(0, 'Calculadora de frigorías | Clima Baires',
        'Calculá cuántas frigorías necesita tu ambiente y qué split te conviene. Herramienta gratuita de Clima Baires, instaladores en zona norte.',
        c, f'{DOMINIO}/calculadora-frigorias.html', jsonld_migas([('Inicio', '/'), ('Calculadora de frigorías', '/calculadora-frigorias.html')]), 'calc',
        pagina_id='calculadora-frigorias',
        wsp_barra='Hola Clima Baires, quiero saber qué equipo necesito para mi ambiente.')

def bloque_antes_despues(par):
    antes = next(f for f in par if f['slug'].startswith('antes-'))
    despues = next(f for f in par if f['slug'].startswith('despues-'))
    return f'''<div class="antes-despues">
      <figure>{img_obra(antes, sizes='(max-width: 560px) 100vw, 45vw')}<figcaption>Antes</figcaption></figure>
      <figure>{img_obra(despues, sizes='(max-width: 560px) 100vw, 45vw')}<figcaption>Después</figcaption></figure>
    </div>'''


def pagina_obras():
    zonas_presentes = sorted({f['zona'] for f in FOTOS})
    tipos_presentes = sorted({f['tipo'] for f in FOTOS})
    filtros_zona = ''.join(
        f'<button class="filtro" data-grupo="zona" data-valor="{z}" aria-pressed="false">{ZONAS_FOTO[z]}</button>'
        for z in zonas_presentes)
    filtros_tipo = ''.join(
        f'<button class="filtro" data-grupo="tipo" data-valor="{t}" aria-pressed="false">{TIPOS_FOTO[t]}</button>'
        for t in tipos_presentes)

    # tarjetas de CTA intercaladas cada 4 fotos: en móvil el mosaico es de una
    # columna y sin esto quedan pantallas enteras de scroll sin invitación a chatear
    ganchos = [
        ('¿Querés algo así en tu casa?', 'Mandanos una foto del ambiente y te pasamos precio hoy.',
         'Hola Clima Baires, vi sus obras y quiero un presupuesto.'),
        ('Instalamos esta semana', 'Contanos qué necesitás y coordinamos la visita técnica.',
         'Hola Clima Baires, quiero coordinar una visita técnica.'),
        ('¿Tenés un equipo para cambiar?', 'Te cotizamos el recambio con retiro del viejo incluido.',
         'Hola Clima Baires, quiero cotizar un recambio de equipo.'),
        ('Presupuesto el mismo día', 'Sin cargo y sin compromiso, en todo el corredor norte.',
         'Hola Clima Baires, quiero un presupuesto sin cargo.'),
    ]
    trozos, gancho = [], 0
    for i, f in enumerate(FOTOS):
        trozos.append(f'''
      <figure class="obra" data-zona="{f['zona']}" data-tipo="{f['tipo']}">
        <button class="obra-abrir" type="button" data-full="assets/img/obras/{f['slug']}-1600.webp"
                data-alt="{f['alt']}" data-slug="{f['slug']}" aria-label="Ampliar: {f['alt']}">
          {img_obra(f)}
        </button>
        <figcaption>{f['alt']}</figcaption>
      </figure>''')
        if (i + 1) % 3 == 0 and gancho < len(ganchos):
            t, s, m = ganchos[gancho]
            gancho += 1
            trozos.append(f'''
      <div class="obra-cta">
        {WSP_SVG}
        <p class="obra-cta-titulo">{t}</p>
        <p>{s}</p>
        <a class="boton verde" data-wsp="{m}" data-origen="cinta" href="#">Escribinos por WhatsApp</a>
      </div>''')
    if gancho < 1:                      # galerías cortas: al menos una tarjeta
        t, s, m = ganchos[0]
        trozos.append(f'''
      <div class="obra-cta">
        {WSP_SVG}
        <p class="obra-cta-titulo">{t}</p>
        <p>{s}</p>
        <a class="boton verde" data-wsp="{m}" data-origen="cinta" href="#">Escribinos por WhatsApp</a>
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
    <p class="bajada">Nuestro equipo, en obra. Las primeras son de la casa matriz en Málaga; pronto, las de tu zona.</p>
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
    <div class="filtros" role="group" aria-label="Filtrar por zona">
      <span class="etiqueta">Zona:</span>
      <button class="filtro" data-grupo="zona" data-valor="todas" aria-pressed="true">Todas</button>
      {filtros_zona}
    </div>
    <div class="filtros" role="group" aria-label="Filtrar por tipo de trabajo">
      <span class="etiqueta">Trabajo:</span>
      <button class="filtro" data-grupo="tipo" data-valor="todos" aria-pressed="true">Todos</button>
      {filtros_tipo}
    </div>
    <div style="margin:22px 0 4px">{cinta_cta('Mirá cómo trabajamos. ¿Querés lo mismo en tu casa?', 'Hola Clima Baires, vi sus obras y quiero un presupuesto.', 'Pedir presupuesto')}</div>
    <div class="obras-grilla" id="obras-grilla">{items}
    </div>
    <p id="obras-vacio" hidden>No hay obras con ese filtro todavía. Probá con otra zona u otro tipo de trabajo.</p>
  </div>
</section>
{pares}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>¿Querés algo así en tu casa?</h2><p>Contanos qué ambiente querés climatizar y te pasamos presupuesto hoy.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, vi sus obras recientes y quiero un presupuesto." data-origen="seccion" href="#">Pedir presupuesto</a>
    </div>
  </div>
</section>

<div class="lightbox" id="lightbox" hidden role="dialog" aria-modal="true" aria-label="Foto ampliada">
  <button class="lb-cerrar" type="button" aria-label="Cerrar (Escape)">×</button>
  <button class="lb-prev" type="button" aria-label="Foto anterior">‹</button>
  <img class="lb-img" src="" alt="">
  <button class="lb-next" type="button" aria-label="Foto siguiente">›</button>
  <p class="lb-cap"></p>
  <a class="boton celeste lb-wsp" data-wsp="Vi sus obras en la web, quiero algo así en casa." data-origen="lightbox" href="#">Quiero algo así en casa</a>
</div>
'''
    ld = [
        jsonld_local('Galería de obras: instalación, recambio y mantenimiento de aire acondicionado.', f'{DOMINIO}/obras.html'),
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
                    'name': f['alt'],
                    'representativeOfPage': i == 0,
                },
            } for i, f in enumerate(FOTOS)],
        },
    ]
    return layout(0, 'Obras recientes | Clima Baires',
        'Galería de obras de Clima Baires: instalación de split, cassette y condensadoras, recambios y mantenimiento. Fotos reales de nuestro equipo.',
        c, f'{DOMINIO}/obras.html', ld, 'obras',
        og_image=f'{DOMINIO}/assets/img/obras/og-obras.jpg' if HAY_FOTOS else None,
        pagina_id='obras', wsp_barra='Hola Clima Baires, vi sus obras recientes y quiero un presupuesto.')


def faq_de_zona(slug, nombre):
    """Las preguntas de cada zona viven en contenido/faq-zonas.json, no acá: son
    contenido editable y son lo que Google levanta como FAQPage. Si falta una
    zona no se rompe el build, pero se avisa: publicar las genéricas en una
    landing de Ads es desperdiciarla."""
    propias = FAQ_ZONAS.get(slug)
    if propias:
        return [(p, r) for p, r in propias]
    print(f'  ! {slug}: sin preguntas propias en contenido/faq-zonas.json, van las genéricas')
    return [
        (f'¿Cuánto tardan en venir a {nombre}?', 'Coordinamos la visita técnica dentro de las 72 horas.'),
        ('¿El presupuesto tiene costo?', 'No: la visita técnica y el presupuesto son sin cargo.'),
        ('¿Atienden equipos que no instalaron ustedes?', 'Sí, somos multimarca: limpieza, carga de gas y reparación.'),
    ]


def pagina_zona(slug, nombre, partido, intro, barrios, especial):
    faq = faq_de_zona(slug, nombre)
    # acordeón nativo: la respuesta está en el HTML (Google la lee aunque esté
    # plegada) y la página no se vuelve una pared de texto
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
      <h2>Instalación, venta y service en {nombre}</h2>
      <p>Split, multisplit, piso-techo y conductos en {lista_barrios}. Presupuesto por WhatsApp en el día y precio cerrado: lo que ves es lo que pagás.</p>
      <ul class="lista-check">
        <li>Instaladores certificados, seguros al día</li>
        <li>Vacío de cañería y prueba de estanqueidad, siempre</li>
        <li>Garantía escrita y service anual</li>
      </ul>
      <div style="margin-top:22px; display:flex; gap:12px; flex-wrap:wrap">
        <a class="boton" data-wsp="Hola Clima Baires, estoy en {nombre} y quiero un presupuesto." data-origen="seccion" href="#">Pedir presupuesto en {nombre}</a>
        <a class="boton fantasma" data-agenda data-origen="seccion" href="#">Agendar visita</a>
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

<section class="seccion" style="padding:0 0 60px">{cinta_cta(f'¿Coordinamos una visita técnica en {nombre}? Sin cargo y sin compromiso.', f'Hola, estoy en {nombre} y quiero presupuesto de instalación.')}
</section>

<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Dudas de la zona</span><h2>Preguntas frecuentes en {nombre}</h2></div>
    <div class="faq-lista">{faq_html}</div>
    <p class="centrado" style="margin-top:26px"><a class="boton verde" data-wsp="Hola, estoy en {nombre} y tengo una consulta que no está en las preguntas frecuentes." data-origen="faq" href="#">Preguntar lo que no está acá</a></p>
  </div>
</section>
{bloque_quien_entra(alterna=True, p='../')}
<section class="seccion alterna">
  <div class="contenedor centrado">
    <h2>También trabajamos en</h2>
    <p style="margin-top:10px">{otras}</p>
  </div>
</section>
'''
    ld = [
        jsonld_local(f'Venta, instalación y mantenimiento de aire acondicionado en {nombre} ({partido}).',
                     f'{DOMINIO}/zonas/{slug}.html', nombre),
        jsonld_migas([('Inicio', '/'), ('Zonas', '/#zonas'), (nombre, f'/zonas/{slug}.html')]),
        jsonld_faq(faq),
        jsonld_servicio(f'Instalación de aire acondicionado en {nombre}',
                        f'Venta, instalación certificada y posventa de aire acondicionado en {nombre}.', nombre),
    ]
    return layout(1, f'Aire acondicionado en {nombre} | Clima Baires',
        f'Instalación de aire acondicionado en {nombre}: split, multisplit y conductos. Presupuesto el mismo día y posventa real.',
        c, f'{DOMINIO}/zonas/{slug}.html', ld, 'zonas',
        pagina_id=f'zonas/{slug}', zona_nombre=nombre,
        wsp_barra=f'Hola, estoy en {nombre} y quiero presupuesto de instalación.')

def pagina_nosotros():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Sobre nosotros</nav>
    <h1>De la Costa del Sol al corredor norte</h1>
    <p class="bajada">Nacimos en Málaga instalando climatización. Hoy traemos ese estándar a Buenos Aires.</p>
    {acciones_cabecera('Hola Clima Baires, quiero coordinar una visita técnica.', 'Hablar con nosotros', secundario='<a class="boton fantasma" href="obras.html">Ver obras</a>')}
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor grilla dos">
    <div>
      <h2>Nuestra historia</h2>
      <p>En España aprendimos que el negocio no es vender un aparato: es que el cliente te vuelva a llamar al año siguiente.</p>
      <ul class="lista-check">
        <li><strong>Transparencia</strong>: precio cerrado, cero letra chica.</li>
        <li><strong>Rapidez</strong>: respuesta en minutos, presupuesto en el día.</li>
        <li><strong>Posventa real</strong>: seguimos estando después de cobrar.</li>
      </ul>
      <p style="margin-top:14px">Equipo local en Buenos Aires, procesos de la casa matriz (<a href="https://www.climabaires.es" rel="noopener">climabaires.es</a>).</p>
    </div>
    <div>
      <div class="tarjeta">
        <h3>Nuestros valores</h3>
        <p><strong>Misión:</strong> brindar soluciones de climatización eficientes, seguras y duraderas, adaptadas a cada hogar.</p>
        <p><strong>Visión:</strong> ser la referencia del corredor norte por transparencia, agilidad y calidad humana.</p>
        <p><strong>Eslogan:</strong> «Tu confort, nuestra prioridad».</p>
      </div>
      <div class="tarjeta" style="margin-top:20px">
        <h3>Datos que importan</h3>
        <ul class="lista-check">
          <li>Instaladores con certificación y seguros con cláusula de no repetición</li>
          <li>Aptos para ingresar a Nordelta y barrios cerrados</li>
          <li>Checklist de calidad con fotos en cada obra</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 60px">{cinta_cta('¿Te contamos cómo lo haríamos en tu casa?', 'Hola Clima Baires, quiero que me asesoren para climatizar mi casa.')}
</section>
{bloque_quien_entra(alterna=False)}
{seccion_asi_trabajamos()}
<section class="seccion">
  <div class="contenedor">
    <div class="banda-cta">
      <div><h2>Conocenos trabajando</h2><p>La mejor carta de presentación es una instalación bien hecha.</p></div>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero coordinar una visita técnica." data-origen="seccion" href="#">Coordinar visita</a>
    </div>
  </div>
</section>
'''
    return layout(0, 'Sobre nosotros | Clima Baires Argentina',
        'Clima Baires nació en Málaga instalando climatización. Traemos ese estándar al corredor norte: transparencia, rapidez y posventa real.',
        c, f'{DOMINIO}/sobre-nosotros.html', jsonld_migas([('Inicio', '/'), ('Sobre nosotros', '/sobre-nosotros.html')]), 'nosotros', pagina_id='sobre-nosotros')


def bloque_quien_entra(alterna=True, p=''):
    """La objeción que nadie escribe en el formulario: meter en tu casa a dos
    desconocidos con un taladro. Va en «sobre nosotros» y en las seis zonas —sin
    datos locales adentro, así se inserta igual en las siete páginas."""
    pasos = [
        ('Nombre y foto antes',
         'El día anterior te llega por WhatsApp el nombre, la foto y el documento del técnico que va a tu '
         'casa, más la patente de la camioneta, para que lo dejes anotado en la guardia o se lo pases al '
         'encargado sin tener que llamar a nadie.'),
        ('Franja de dos horas',
         'No te decimos «a la mañana»: te damos una franja de dos horas, el equipo llega en camioneta '
         'rotulada y con ropa de trabajo, y si nos atrasamos te avisamos antes de que se cumpla la franja, '
         'no después.'),
        ('Protección antes de empezar',
         'Antes de abrir la primera caja tapamos el piso, los muebles y el paso hasta el ambiente con '
         'mantas y film, y la aspiradora la traemos nosotros: no se pide prestada ninguna herramienta de '
         'la casa.'),
        ('Se prueba con vos',
         'El equipo se enciende con vos al lado y no nos vamos hasta que lo veas andar: frío, calor, '
         'control remoto, cómo se sacan y se lavan los filtros y qué hacer si algún día no arranca.'),
        ('Nos llevamos todo',
         'Cartones, recortes de caño, restos de obra y el equipo viejo si lo había se van en nuestra '
         'camioneta el mismo día, no al volquete del barrio ni al canasto del vecino.'),
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
      <h2>Quién va a entrar a tu casa</h2>
      <p class="intro">Meter en tu casa a dos personas con un taladro no es un trámite menor: estas cinco cosas las hacemos en toda obra, sin que tengas que pedirlas.</p>
    </div>
    <div class="grilla dos" style="margin-top:26px">{tarjetas}</div>
    <p class="centrado nota" style="margin-top:22px">El alta del contratista y los papeles que pide cada barrio los gestionamos nosotros con la administración: vos no tenés que ir a la guardia a explicar quiénes somos.</p>
  </div>
</section>

<section class="seccion" style="padding:0 0 46px">{cinta_cta('¿Querés saber cómo sería en tu casa? Preguntanos sin compromiso.', 'Hola Clima Baires, quiero saber cómo trabajan dentro de la casa.', 'Preguntar por WhatsApp')}
</section>'''


def bloque_que_incluye():
    """«Precio cerrado» sin una lista no dice nada. Estas son las dos listas.

    La de la derecha no lleva ✓: un tilde en lo que se cobra aparte se lee como
    si también estuviera incluido, que es justo el malentendido que el bloque
    viene a eliminar."""
    incluido = [
        ('Hasta %s metros de cañería de cobre, con aislación' % METROS_INCLUIDOS,
         'El caño que une la unidad de adentro con la de afuera, forrado para que no transpire ni pierda frío. El tendido real se mide en la visita técnica.'),
        ('Ménsulas, anclajes y tacos antivibratorios',
         'Los soportes de la unidad exterior, con el anclaje que pide esa pared, y las gomas que evitan que el compresor se escuche adentro.'),
        ('El paso de pared para la cañería',
         'La perforación en pared común y su terminación. Si hay que romper y rehacer, eso ya es obra civil y está en la otra lista.'),
        ('Vacío de cañería con bomba',
         'Sacar el aire y la humedad del circuito antes de soltar el gas. Con bomba y vacuómetro, no con una purga de diez segundos. Es lo que define si el equipo llega a los diez años.'),
        ('Prueba de estanqueidad',
         'Estanqueidad, en criollo, es que no pierda. Se presuriza con nitrógeno y se controla que la aguja no baje, antes de cerrar nada.'),
        ('La carga de refrigerante que pidan esos metros',
         'Los equipos vienen de fábrica con gas para un tendido corto. Si el tuyo es más largo, hay que agregar. Dentro de los %s metros, va en el precio.' % METROS_INCLUIDOS),
        ('Desagüe con pendiente natural, probado con agua',
         'La salida del agua de condensación, con caída continua y sin panzas, a un lugar que no sea la medianera ni el balcón del vecino. Se prueba antes de cerrar la pared.'),
        ('Puesta en marcha con vos presente',
         'Presiones, consumo en amperes y diferencia de temperatura entre el aire que entra y el que sale, medidos y explicados ahí mismo. No es «lo prendimos y anduvo».'),
        ('Protección del ambiente y retiro de residuos',
         'Cubrimos muebles y pisos antes de empezar, y nos llevamos cajas, recortes de cobre y polvo. La obra termina cuando no queda nada nuestro en tu casa.'),
        ('Garantía escrita de la instalación',
         'De nuestra mano de obra: uniones, desagüe, fijaciones y puesta en marcha. Va aparte de la garantía del fabricante del equipo, que también te entregamos con la factura.'),
    ]
    aparte = [
        ('Metro adicional de cañería',
         'Pasados los %s metros, se cobra por metro, con el refrigerante extra que ese tramo necesita. El valor del metro te lo decimos en el presupuesto, no después.' % METROS_INCLUIDOS),
        ('Trabajo en altura con andamio o plataforma',
         'Cuando la condensadora va donde no llega una escalera. El andamio o la plataforma se alquilan por día y eso se cotiza aparte. Los elementos de seguridad del equipo no se cobran nunca: van siempre.'),
        ('Grúa o izaje',
         'Equipos pesados o accesos sin paso: piso-techo grandes, conductos, patios internos. Lo presta un tercero y se cotiza tal como lo cobra.'),
        ('Obra civil: roturas, canaletas y reparación',
         'Abrir mampostería para embutir la cañería, y después revocar y pintar. Si el tendido va por cablecanal a la vista, no hace falta. Si querés todo escondido, se presupuesta.'),
        ('Bomba de condensado',
         'Cuando la salida del desagüe queda más alta que el equipo, el agua no baja sola: hace falta una bomba que la empuje. Es un aparato más, con su instalación.'),
        ('Punto eléctrico nuevo, térmica o tablero',
         'El equipo necesita su propia línea con protección. Si en esa pared no hay nada, o el tablero no tiene lugar para una térmica más, es trabajo de electricidad.'),
        ('Lo que cobra el barrio o el consorcio',
         'Algunos countries piden derecho de obra, depósito de garantía o seguros. La gestión con la administración la hacemos nosotros; lo que cobra el barrio va detallado como tal, sin recargo nuestro encima.'),
    ]
    def lista(items, clase, corte=None):
        """`corte` parte la lista para colar una cinta en el medio: apilada en
        móvil, la de «entra en el precio» son diez ítems seguidos."""
        li = [f'<li><strong>{t}</strong><span>{d}</span></li>' for t, d in items]
        if corte is None:
            return '<ul class="%s">%s</ul>' % (clase, ''.join(li))
        cinta = cinta_cta_suelta('¿Todo esto entra en tu caso? Mandanos una foto del ambiente y te lo confirmamos.',
                                 'Hola Clima Baires, quiero saber qué entra en el precio en mi caso. Les mando fotos.',
                                 'Consultar', 'seccion')
        return '<ul class="%s">%s</ul><div class="solo-movil corte-lista">%s</div><ul class="%s">%s</ul>' % (
            clase, ''.join(li[:corte]), cinta, clase, ''.join(li[corte:]))
    return f'''
<section class="seccion alterna" id="que-incluye">
  <div class="contenedor">
    <div class="centrado">
      <span class="kicker">Precio cerrado</span>
      <h2>Qué entra en el precio y qué se cobra aparte</h2>
      <p class="intro">Decir «precio cerrado» sin una lista es decir nada. Esta es la lista: lo que entra siempre en una instalación nuestra, y lo que se cobra aparte cuando la casa lo pide. Si algo de la segunda lista aplica en tu caso, lo ves en el presupuesto antes de que empiece la obra.</p>
    </div>
    <div class="grilla dos" style="margin-top:30px; align-items:start">
      <div class="tarjeta">
        <h3>Entra en el precio</h3>
        <p class="nota">Siempre, en toda instalación. No se discute ni se recorta.</p>
        {lista(incluido, 'lista-check lista-detalle', corte=5)}
      </div>
      <div class="solo-movil">{cinta_cta_suelta('¿Querés saber qué de esto aplica en tu casa? Mandanos una foto del ambiente.', 'Hola Clima Baires, quiero saber qué entra en el precio en mi caso. Les mando fotos.', 'Consultar', 'seccion')}</div>
      <div class="tarjeta">
        <h3>Se cobra aparte</h3>
        <p class="nota">Solo si tu casa lo pide. Sale del presupuesto, con el importe a la vista, antes de arrancar.</p>
        {lista(aparte, 'lista-mas lista-detalle')}
      </div>
    </div>
    <div class="compromiso">
      <h3>Nuestro compromiso con los adicionales</h3>
      <p>Casi todo lo de la segunda lista se detecta en la visita técnica y entra al presupuesto cerrado antes de que compres nada. Si aun así aparece algo durante la obra, hacemos siempre lo mismo: paramos, te lo mostramos en el lugar, te decimos cuánto suma y seguimos recién cuando lo aprobás. Alcanza con un «dale» por WhatsApp, y queda escrito. Un adicional que aparece recién en la factura no existe acá.</p>
      <a class="boton blanco" data-wsp="Hola Clima Baires, quiero un presupuesto con el detalle de qué entra y qué se cobra aparte." data-origen="seccion" href="#">Pedir el presupuesto detallado</a>
    </div>
  </div>
</section>

<section class="seccion" style="padding:0 0 50px">{cinta_cta('Contanos cómo está tu casa y te decimos qué entra y qué no, antes de cobrarte nada.', 'Hola Clima Baires, quiero saber qué entra en el precio y qué se cobra aparte en mi caso.', 'Pedir el detalle por WhatsApp')}
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
    <p class="intro">Uniforme, herramientas certificadas y obras que quedan limpias. Estas fotos son de nuestro equipo trabajando de verdad — más en la <a href="obras.html">galería de obras</a>.</p></div>
    <div class="franja-equipo">{imgs}</div>
  </div>
</section>'''

def pagina_contacto():
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Contacto</nav>
    <h1>Hablemos de tu clima</h1>
    <p class="bajada">El camino más corto es WhatsApp: fotos del ambiente y presupuesto en el día.</p>
  </div>
</section>

<section class="seccion" style="padding-top:10px">
  <div class="contenedor">
    <h2 class="centrado" style="margin-bottom:30px">Elegí por dónde te contactamos</h2>
  </div>
  <div class="contenedor grilla dos">
    <div class="tarjeta">
      <h3>Escribinos directo</h3>
      <p>WhatsApp: <strong data-wsp-num></strong><br>
      Email: <a data-email href="#"></a><br>
      Horario: <span data-horario></span></p>
      <a class="boton celeste" data-wsp="Hola Clima Baires, quiero hacer una consulta." data-origen="seccion" href="#" style="margin-top:8px">Abrir WhatsApp</a>
      <p style="margin-top:18px"><strong>Zona de trabajo:</strong> Núñez (CABA), Vicente López, San Isidro, Tigre, Nordelta y Pilar. Atendemos a domicilio: no tenemos local de venta al público, y eso también lo pagás menos.</p>
    </div>
    <div class="tarjeta">
      <h3>O dejanos tus datos</h3>
      <p>Completá el formulario y el mensaje se abre listo para enviar por WhatsApp.</p>
      <form class="form-contacto" id="form-contacto">
        <input name="nombre" placeholder="Tu nombre" required>
        <select name="zona" required>
          <option value="" disabled selected>¿En qué zona estás?</option>
          <option>Núñez</option><option>Vicente López</option><option>San Isidro</option>
          <option>Tigre</option><option>Nordelta</option><option>Pilar</option><option>Otra</option>
        </select>
        <textarea name="mensaje" placeholder="Contanos qué necesitás: instalación nueva, recambio, mantenimiento…" required></textarea>
        <button class="boton" type="submit">Enviar por WhatsApp</button>
      </form>
    </div>
  </div>
</section>

<section class="seccion" style="padding-top:0" id="agenda">
  <div class="contenedor">
    <div class="tarjeta">
      <h3>Agendá tu visita técnica</h3>
      <p>Elegí día y hora en nuestra agenda y listo: te llega la confirmación por email y a nosotros la cita al calendario. La visita y el presupuesto son sin cargo en todo el corredor norte.</p>
      <a class="boton" data-agenda data-origen="seccion" href="#" style="margin-top:10px">Reservar visita técnica</a>
      <div data-agenda-embed></div>
    </div>
  </div>
</section>
'''
    return layout(0, 'Contacto y presupuestos | Clima Baires',
        'Pedí tu presupuesto de instalación de aire acondicionado en el corredor norte de Buenos Aires. Te respondemos por WhatsApp en horario comercial.',
        c, f'{DOMINIO}/contacto.html', jsonld_migas([('Inicio', '/'), ('Contacto', '/contacto.html')]), 'contacto', pagina_id='contacto',
        wsp_barra='Hola Clima Baires, quiero hacer una consulta.')

def tarjeta_post(post, base='blog/', nivel=2):
    """`base` es el camino hasta la carpeta del blog desde la página que la usa
    ('blog/' desde la raíz, '' desde una nota). `nivel` es el del encabezado: la
    jerarquía tiene que quedar sin saltos en cada página donde se inserta."""
    return f'''<article class="post-tarjeta" data-categoria="{post['categoria']}">
        <a href="{base}{post['slug']}.html">
          <span class="post-cat">{post['categoria_label']}</span>
          <h{nivel}>{post['titulo']}</h{nivel}>
          <p>{post['resumen']}</p>
          <span class="post-meta">{post['fecha_larga']} · {post['minutos']} min de lectura</span>
        </a>
      </article>'''


def intercalar_cta(cuerpo, mensaje):
    """Mete cintas de conversión entre las secciones de una nota larga.

    Una nota de 1.400 palabras son diez pantallas de móvil: si el único CTA está
    al final, el que se convence en la mitad no tiene dónde tocar. Se inserta
    antes de cada tercer `<h2>` (nunca antes del primero, que va pegado a la
    entradilla) para no cortar la lectura más de la cuenta."""
    partes = re.split(r'(?=<h[23]>)', cuerpo)
    if len(partes) < 3:
        return cuerpo
    salida, acumulado = [], 0
    for i, parte in enumerate(partes):
        if i and acumulado > TRAMO_SIN_CTA:
            salida.append('<div class="cta-intercalado">%s</div>' % cinta_cta_suelta(
                'Si preferís que lo veamos nosotros, escribinos y coordinamos una visita.',
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
    # esto queda un tramo largo de scroll sin dónde tocar
    tarjetas = ''
    for i, p in enumerate(posts):
        if i and i % 3 == 0:
            tarjetas += '<div class="cinta-en-grilla">%s</div>' % cinta_cta_suelta(
                '¿Preferís preguntarlo directo? Escribinos y te respondemos.',
                'Hola Clima Baires, leí una nota en su web y quiero hacer una consulta.',
                'Preguntar', 'listado')
        tarjetas += tarjeta_post(p, '')
    vacio = '' if posts else '<p class="intro centrado">Estamos escribiendo las primeras notas. Volvé en unos días.</p>'
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="../index.html">Inicio</a> › Notas</nav>
    <h1>Notas sobre climatización</h1>
    <p class="bajada">Lo que aprendimos instalando: cómo elegir, qué mirar en una obra y cómo cuidar tu equipo.</p>
    {acciones_cabecera('Hola Clima Baires, leí una nota en su web y quiero hacer una consulta.', 'Consultar por WhatsApp', '../')}
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
    <p id="post-vacio" hidden>No hay notas de ese tema todavía.</p>
    {vacio}
  </div>
</section>

<section class="seccion" style="padding:0 0 70px">{cinta_cta('¿Te quedó una duda de la nota? Preguntanos sin compromiso.', 'Hola Clima Baires, leí una nota en su web y tengo una consulta.', 'Preguntar')}
</section>
'''
    ld = [
        jsonld_migas([('Inicio', '/'), ('Notas', '/blog/')]),
        {
            '@context': 'https://schema.org', '@type': 'Blog',
            'name': 'Notas de Clima Baires', 'url': f'{DOMINIO}/blog/',
            'publisher': {'@id': DOMINIO + '/#negocio'},
            'blogPost': [{'@type': 'BlogPosting', 'headline': p['titulo'],
                          'url': f'{DOMINIO}/blog/{p["slug"]}.html', 'datePublished': p['fecha_iso']}
                         for p in posts],
        },
    ]
    return layout(1, 'Notas sobre climatización | Clima Baires',
        'Guías prácticas de aire acondicionado: cuántas frigorías necesitás, qué mirar en una instalación y cómo mantener tu equipo.',
        c, f'{DOMINIO}/blog/', ld, 'blog', pagina_id='blog',
        wsp_barra='Hola Clima Baires, leí una nota en su web y quiero hacer una consulta.')


def pagina_post(post, otros):
    relacionadas = [o for o in otros if o['categoria'] == post['categoria']][:2] or otros[:2]
    mas = ''
    if relacionadas:
        mas = f'''
<section class="seccion alterna">
  <div class="contenedor">
    <div class="centrado"><span class="kicker">Seguir leyendo</span><h2>Otras notas</h2></div>
    <div class="post-grilla" style="margin-top:26px">{''.join(tarjeta_post(o, '', 3) for o in relacionadas)}</div>
  </div>
</section>'''
    msj = f'Hola Clima Baires, leí la nota «{post["titulo"]}» y quiero un presupuesto.'
    c = f'''
<article class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="../index.html">Inicio</a> › <a href="index.html">Notas</a> › {post['categoria_label']}</nav>
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
<section class="seccion" style="padding:34px 0 60px">{cinta_cta('¿Querés que lo veamos en tu casa? La visita y el presupuesto son sin cargo.', msj, 'Pedir presupuesto')}
</section>'''
    ld = [
        jsonld_migas([('Inicio', '/'), ('Notas', '/blog/'), (post['titulo'], f'/blog/{post["slug"]}.html')]),
        {
            '@context': 'https://schema.org', '@type': 'BlogPosting',
            'headline': post['titulo'], 'description': post['resumen'],
            'datePublished': post['fecha_iso'], 'dateModified': post['fecha_iso'],
            'author': {'@type': 'Organization', 'name': 'Clima Baires Argentina', '@id': DOMINIO + '/#negocio'},
            'publisher': {'@id': DOMINIO + '/#negocio'},
            'mainEntityOfPage': f'{DOMINIO}/blog/{post["slug"]}.html',
            'image': f'{DOMINIO}/assets/img/obras/og-home.jpg' if HAY_FOTOS else '',
            'wordCount': post['palabras'],
            'inLanguage': 'es-AR',
        },
    ]
    return layout(1, f'{post["titulo"]} | Clima Baires', post['resumen'],
        c, f'{DOMINIO}/blog/{post["slug"]}.html', ld, 'blog', pagina_id=f'blog/{post["slug"]}',
        wsp_barra=f'Hola Clima Baires, leí la nota «{post["titulo"]}» y quiero un presupuesto.')


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
  <title>Notas de Clima Baires</title>
  <link>{DOMINIO}/blog/</link>
  <description>Guías de aire acondicionado para el corredor norte de Buenos Aires.</description>
  <language>es-AR</language>
  <lastBuildDate>{ahora}</lastBuildDate>{items}
</channel></rss>
'''


def pagina_privacidad():
    e = EMPRESA
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Privacidad</nav>
    <h1>Política de privacidad</h1>
    <p class="bajada">Qué datos te pedimos, para qué los usamos y cómo pedir que los borremos.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Quién trata tus datos</h2>
    <p>{e['razon_social']} (CUIT {e['cuit']}), con domicilio en {e['domicilio']}. Consultas sobre tus datos: <a data-email href="#"></a>. Responsable: {e['responsable_datos']}.</p>

    <h2 style="margin-top:34px">Qué datos recogemos y para qué</h2>
    <ul class="lista-check">
      <li><strong>Los que nos escribís vos</strong>: nombre, zona, tipo de servicio y de equipo, a través del asistente del sitio o del formulario de contacto. Sirven para armar tu presupuesto y coordinar la visita. Nada de esto se guarda en este sitio: se arma un mensaje que abrís vos en WhatsApp.</li>
      <li><strong>Datos de navegación</strong>: páginas vistas y clics en los botones de contacto, mediante Google Tag Manager y Google Analytics. Sirven para saber qué contenidos funcionan y medir la publicidad. No usamos esos datos para identificarte por nombre.</li>
      <li><strong>La conversación de WhatsApp</strong> queda en tu cuenta y en la nuestra, con las condiciones de WhatsApp (Meta).</li>
    </ul>

    <h2 style="margin-top:34px">Con quién los compartimos</h2>
    <p>Con nadie, salvo los servicios que usamos para funcionar: WhatsApp (Meta) para la conversación, Google (Analytics, Tag Manager y Calendar) para la medición y la agenda de visitas. No vendemos ni cedemos bases de datos.</p>

    <h2 style="margin-top:34px">Cuánto los conservamos</h2>
    <p>Los mensajes y presupuestos, mientras dure la relación comercial y el plazo de garantía. Los datos de navegación, según la retención configurada en Google Analytics (14 meses).</p>

    <h2 style="margin-top:34px">Tus derechos</h2>
    <p>Podés pedirnos acceso, rectificación, actualización o supresión de tus datos escribiéndonos a <a data-email href="#"></a>. Respondemos dentro de los plazos de la Ley 25.326 de Protección de los Datos Personales: 10 días corridos para el acceso y 5 días hábiles para la rectificación o supresión.</p>
    <p style="margin-top:14px; color:var(--gris); font-size:.92rem">La Agencia de Acceso a la Información Pública, órgano de control de la Ley 25.326, tiene atribuida la atención de las denuncias y reclamos por incumplimiento de las normas sobre protección de datos personales.</p>

    <h2 style="margin-top:34px">Cookies</h2>
    <p>Usamos cookies propias para que el sitio funcione y de Google para medir el tráfico y la publicidad. Podés bloquearlas desde la configuración de tu navegador; el sitio sigue funcionando, pero no vamos a poder medir qué contenidos te sirvieron.</p>
  </div>
</section>
'''
    return layout(0, 'Política de privacidad | Clima Baires',
        'Qué datos personales recoge climabaires.com, para qué se usan y cómo ejercer tus derechos según la Ley 25.326.',
        c, f'{DOMINIO}/privacidad.html', jsonld_migas([('Inicio', '/'), ('Privacidad', '/privacidad.html')]), '',
        pagina_id='privacidad')


def pagina_terminos():
    e = EMPRESA
    c = f'''
<section class="cabecera-pagina">
  <div class="contenedor">
    <nav class="migas"><a href="index.html">Inicio</a> › Términos</nav>
    <h1>Términos y condiciones</h1>
    <p class="bajada">Cómo contratamos, qué cubre la garantía y cómo arrepentirte de una compra.</p>
  </div>
</section>

<section class="seccion" style="padding-top:34px">
  <div class="contenedor" style="max-width:760px">
    <h2>Quién presta el servicio</h2>
    <p>{e['razon_social']}, CUIT {e['cuit']}, domicilio {e['domicilio']}. Inicio de actividades: {e['inicio_actividades']}.</p>

    <h2 style="margin-top:34px">Presupuestos</h2>
    <p>El presupuesto que enviamos por WhatsApp o email es orientativo hasta la visita técnica. Después de la visita pasa a ser cerrado: incluye equipo, materiales, mano de obra y retiro de residuos de obra, y no cambia salvo que vos pidas algo distinto. Si durante la instalación aparece un imprevisto que suma costo, te lo mostramos y lo autorizás antes de hacerlo.</p>
    <p style="margin-top:12px">La calculadora de frigorías del sitio es una herramienta orientativa y no reemplaza la visita técnica.</p>

    <h2 id="revocacion" style="margin-top:34px">Derecho de revocación (botón de arrepentimiento)</h2>
    <p>Como la contratación se hace fuera de nuestro establecimiento (a domicilio, por WhatsApp o por este sitio), tenés <strong>10 días corridos</strong> desde la firma del presupuesto o desde la entrega del equipo —lo que ocurra después— para arrepentirte sin costo ni justificación, según los artículos 34 de la Ley 24.240 y 1110 del Código Civil y Comercial. Para ejercerlo alcanza con escribirnos a <a data-email href="#"></a> o por WhatsApp. Si el equipo ya fue instalado, coordinamos el retiro; los gastos de devolución corren por nuestra cuenta.</p>

    <h2 style="margin-top:34px">Garantías</h2>
    <ul class="lista-check">
      <li><strong>Del equipo</strong>: la que da el fabricante, según la marca y el modelo. Te entregamos la documentación y la factura, que es lo que la habilita.</li>
      <li><strong>De la instalación</strong>: PENDIENTE — plazo de garantía de la mano de obra. Cubre defectos de montaje: pérdidas en las uniones, fallas de desagüe, fijaciones y puesta en marcha. Se reclama por WhatsApp o email y la atendemos sin cargo.</li>
      <li>Quedan fuera de la garantía los daños por uso indebido, cortes de tensión, falta de mantenimiento o intervención de terceros.</li>
    </ul>

    <h2 style="margin-top:34px">Formas de pago</h2>
    <p>Transferencia bancaria, tarjetas y cuotas. Las condiciones vigentes se detallan junto con el presupuesto.</p>

    <h2 style="margin-top:34px">Marcas</h2>
    <p>Las marcas de los fabricantes que aparecen en el sitio pertenecen a sus titulares y se muestran para indicar con qué equipos trabajamos. Clima Baires es un instalador independiente: salvo que se indique lo contrario, no somos distribuidor oficial ni servicio técnico autorizado de esas marcas.</p>

    <h2 style="margin-top:34px">Reclamos</h2>
    <p>Ante cualquier problema escribinos primero: resolvemos casi todo en el día. Si no llegamos a un acuerdo, podés iniciar un reclamo ante la autoridad de aplicación de Defensa del Consumidor de tu jurisdicción o a través del portal <a href="https://autogestion.produccion.gob.ar/consumidores" rel="noopener" target="_blank">Ventanilla Única Federal</a>.</p>
  </div>
</section>
'''
    return layout(0, 'Términos y condiciones | Clima Baires',
        'Condiciones de contratación, presupuestos cerrados, garantía de instalación y derecho de revocación de 10 días.',
        c, f'{DOMINIO}/terminos.html', jsonld_migas([('Inicio', '/'), ('Términos', '/terminos.html')]), '',
        pagina_id='terminos')


def pagina_404():
    c = '''
<section class="seccion centrado" style="padding:120px 0">
  <div class="contenedor">
    <h1>Uy, esta página se quedó sin frío</h1>
    <p class="intro" style="margin-top:14px">La dirección que buscás no existe o cambió de lugar.</p>
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
    'privacidad.html': pagina_privacidad(),
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

# Notas borradas o renombradas: si el .html viejo se queda, Google lo sigue
# mostrando y el visitante aterriza en una página que ya no está en el índice.
vivas = {os.path.basename(r) for r in paginas if r.startswith('blog/')}
for archivo in sorted(os.listdir(os.path.join(RAIZ, 'blog'))):
    if archivo.endswith('.html') and archivo not in vivas:
        os.remove(os.path.join(RAIZ, 'blog', archivo))
        print('  ✗', f'blog/{archivo}', '(nota que ya no existe)')

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
