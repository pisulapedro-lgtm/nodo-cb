# -*- coding: utf-8 -*-
"""Arma la carpeta publicable de climabaires.es.
Uso: python3 web-es/tools/publicar.py   → deja el sitio listo en dist/sitio-es/

La carpeta web-es/ pesa unos 20 MB porque incluye material de trabajo que NO
debe llegar al hosting: los originales de las fotos (sin optimizar y con
metadatos), las capturas de QA y los scripts de Python y Node. Subir web-es/ tal
cual dejaría esas fotos accesibles por URL y rastreables.

Este script copia sólo lo que el navegador necesita y, de paso, escribe:
  _headers   → caché larga para tipografías e imágenes y corta para HTML
               (Cloudflare Pages y Netlify lo leen; en otros hostings es inocuo)
  _redirects → www → dominio raíz (mismo criterio)

Y antes de nada, hace de puerta: mientras queden datos en PENDIENTE no arma el
paquete. La lista de abajo es exactamente lo que sólo puede aportar el titular
del negocio, y cada línea explica qué se rompe si se publica sin ella.
"""
import json
import os
import re
import shutil
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DESTINO = os.path.normpath(os.path.join(RAIZ, '..', 'dist', 'sitio-es'))

# Puerta de publicación: el QA de desarrollo pasa en verde aunque los datos de
# contacto sigan siendo de mentira. Aquí se corta, porque publicar con el
# WhatsApp de ejemplo deja todos los botones del sitio apuntando a un número que
# no existe.
PENDIENTES_JS = [
    ('whatsapp', r"whatsapp:\s*'34600000000'",
     'el número de WhatsApp sigue siendo el de ejemplo: TODOS los botones del sitio no llevan a ningún sitio'),
    ('gtmId', r"gtmId:\s*'GTM-X{7}'",
     'sin contenedor de GTM no se mide ni una conversión (Google Ads queda ciego). '
     'El contenedor argentino no vale: son propiedades distintas'),
    ('agendaUrl', r"agendaUrl:\s*''",
     'sin agenda de Calendar, «Concertar visita» deriva a WhatsApp en vez de reservar'),
    ('placeId', r"placeId:\s*''",
     'sin Place ID no hay mapa en contacto ni enlaces a las reseñas de Google'),
]

# Bloques de generar.py que se publican tal cual en el pie, en los legales y en
# la franja de credenciales.
PENDIENTES_GEN = [
    ('EMPRESA', r'EMPRESA = \{.*?\n\}',
     'faltan denominación social, CIF, domicilio o datos registrales: aparecen como '
     'PENDIENTE en el pie y en el aviso legal, que es obligatorio por la LSSI-CE art. 10'),
    ('RITE', r"^RITE = '[^']*'",
     'falta el número de empresa instaladora habilitada RITE: en España es obligatorio '
     'para instalar climatización y es el mejor sello de confianza que hay'),
    ('TRAYECTORIA', r'TRAYECTORIA = \{.*?\n\}',
     'faltan los años de experiencia y el número de instalaciones: son los datos que '
     'este sitio sí puede mostrar y hoy salen como PENDIENTE en la portada'),
    ('METROS_INCLUIDOS', r"^METROS_INCLUIDOS = '[^']*'",
     'falta cuántos metros de tubería entran en el precio cerrado: servicios.html lo '
     'muestra como «Hasta PENDIENTE metros»'),
    ('GARANTIA_INSTALACION', r"^GARANTIA_INSTALACION = '[^']*'",
     'falta el plazo de garantía de la instalación: sale en servicios.html y en los términos'),
]


def revisar_placeholders():
    faltan = []
    js = open(os.path.join(RAIZ, 'assets', 'js', 'main.js'), encoding='utf-8').read()
    faltan += [(c, m) for c, patron, m in PENDIENTES_JS if re.search(patron, js)]

    gen = open(os.path.join(RAIZ, 'tools', 'generar.py'), encoding='utf-8').read()
    for clave, patron, motivo in PENDIENTES_GEN:
        m = re.search(patron, gen, re.S | re.M)
        if m and 'PENDIENTE' in m.group(0):
            faltan.append((clave, motivo))

    # Reseñas: la puntuación y el número tienen que ser los reales de la ficha,
    # porque de ahí sale el aggregateRating de los datos estructurados y Google
    # penaliza el marcado que no coincide con lo visible.
    ruta_res = os.path.join(RAIZ, 'contenido', 'resenas.json')
    if os.path.exists(ruta_res):
        with open(ruta_res, encoding='utf-8') as f:
            res = json.load(f)
        if not isinstance(res.get('puntuacion'), (int, float)) or not isinstance(res.get('total'), (int, float)):
            faltan.append(('resenas', 'faltan la puntuación y el número de reseñas reales de la ficha de Google '
                                      '(contenido/resenas.json): sin ellos no hay estrellas en el resultado de búsqueda'))
        elif not res.get('resenas'):
            faltan.append(('resenas', 'hay puntuación pero ninguna reseña transcrita (contenido/resenas.json): '
                                      'el aggregateRating tiene que corresponderse con texto visible en la página'))

    # Zona de cada foto: aquí las obras son locales y decir dónde se hicieron es
    # media venta. Una galería sin zonas es la galería del sitio argentino.
    ruta_idx = os.path.join(RAIZ, 'assets', 'img', 'obras', 'index.json')
    if os.path.exists(ruta_idx):
        with open(ruta_idx, encoding='utf-8') as f:
            fotos = json.load(f).get('fotos', [])
        sin_zona = [f['slug'] for f in fotos if not f.get('zona')]
        if sin_zona:
            faltan.append(('fotos', 'estas fotos no tienen el municipio donde se hizo el trabajo, así que la '
                                    'galería sale sin filtro de zona y los pies pierden el dato que más vende '
                                    '(tools/fotos.py → MAPEO): ' + ', '.join(sin_zona)))
    return faltan

# lo que sí se publica
INCLUIR_ARCHIVOS = ('.html', '.xml', '.txt', '.webmanifest')
INCLUIR_CARPETAS = {
    'assets/css', 'assets/js', 'assets/fonts',
    'assets/img',           # se filtra abajo: sin originales
    'zonas',
}
# lo que nunca se publica
EXCLUIR = {'tools', 'assets/img/originales'}

HEADERS = """/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/assets/img/*
  Cache-Control: public, max-age=31536000, immutable
/assets/css/*
  Cache-Control: public, max-age=604800
/assets/js/*
  Cache-Control: public, max-age=604800
/*.html
  Cache-Control: public, max-age=600, must-revalidate
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
"""

REDIRECTS = """https://www.climabaires.es/* https://climabaires.es/:splat 301!
"""


def excluido(rel):
    rel = rel.replace(os.sep, '/')
    return any(rel == e or rel.startswith(e + '/') for e in EXCLUIR)


def main():
    faltan = revisar_placeholders()
    if faltan and '--force' not in sys.argv:
        print('NO se ha armado el paquete: hay datos de configuración sin completar.\n')
        for clave, motivo in faltan:
            donde = {
                'whatsapp': 'main.js → CB', 'gtmId': 'main.js → CB',
                'agendaUrl': 'main.js → CB', 'placeId': 'main.js → CB',
                'resenas': 'contenido/resenas.json', 'fotos': 'tools/fotos.py → MAPEO',
            }.get(clave, 'generar.py')
            print(f'  ✗ {clave}  ({donde})')
            print(f'      {motivo}')
        print('\nDespués de completarlos hay que ejecutar  python3 web-es/tools/generar.py')
        print('para volver a hornear los datos en el HTML.')
        print('\nSi quieres armar el paquete igualmente (por ejemplo para una demo), añade --force.')
        raise SystemExit(1)
    if faltan:
        print('AVISO: se arma con datos sin resolver (--force):')
        for clave, motivo in faltan:
            print(f'  ! {clave}: {motivo}')
        print()

    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)
    os.makedirs(DESTINO)

    copiados = omitidos = 0
    peso = 0
    for base, carpetas, archivos in os.walk(RAIZ):
        rel_base = os.path.relpath(base, RAIZ)
        rel_base = '' if rel_base == '.' else rel_base
        carpetas[:] = [c for c in carpetas if not excluido(os.path.join(rel_base, c))]
        for a in archivos:
            rel = os.path.join(rel_base, a) if rel_base else a
            if excluido(rel):
                omitidos += 1
                continue
            en_raiz = not rel_base
            if en_raiz and not a.endswith(INCLUIR_ARCHIVOS):
                omitidos += 1
                continue
            destino = os.path.join(DESTINO, rel)
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copy2(os.path.join(base, a), destino)
            copiados += 1
            peso += os.path.getsize(destino)

    with open(os.path.join(DESTINO, '_headers'), 'w', encoding='utf-8') as f:
        f.write(HEADERS)
    with open(os.path.join(DESTINO, '_redirects'), 'w', encoding='utf-8') as f:
        f.write(REDIRECTS)

    print(f'Sitio publicable en {DESTINO}')
    print(f'  {copiados} archivos · {peso // 1024} KB   (se han omitido {omitidos}: originales, capturas y scripts)')
    print('  + _headers (caché) y _redirects (www → raíz)')


if __name__ == '__main__':
    main()
