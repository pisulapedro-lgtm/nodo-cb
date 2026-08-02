# -*- coding: utf-8 -*-
"""Arma la carpeta publicable de climabaires.com.
Uso: python3 web/tools/publicar.py   → deja el sitio listo en dist/sitio/

La carpeta web/ pesa ~40 MB porque incluye material de trabajo que NO debe
llegar al hosting: los originales de las fotos (sin optimizar y con metadatos),
las capturas de QA y los scripts de Python/Node. Subir web/ tal cual dejaría
esas fotos accesibles por URL y rastreables.

Este script copia sólo lo que el navegador necesita, y de paso escribe:
  _headers   → caché larga para fuentes/imágenes y corta para HTML (Cloudflare
               Pages y Netlify lo leen; en otros hostings es inofensivo)
  _redirects → www → dominio raíz (mismo criterio)
"""
import os
import re
import shutil
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DESTINO = os.path.normpath(os.path.join(RAIZ, '..', 'dist', 'sitio'))

# Puerta de publicación: el QA de desarrollo pasa en verde aunque los datos de
# contacto sigan siendo de mentira. Acá se corta, porque publicar con el WhatsApp
# placeholder deja todos los botones del sitio apuntando a un número inexistente.
PENDIENTES = [
    ('whatsapp', r"whatsapp:\s*'5491100000000'",
     'el número de WhatsApp sigue siendo el placeholder: TODOS los botones del sitio no llevan a ningún lado'),
    ('gtmId', r"gtmId:\s*'GTM-X{7}'",
     'sin contenedor de GTM no se mide ni una conversión (Google Ads queda ciego)'),
    ('agendaUrl', r"agendaUrl:\s*''",
     'sin agenda de Calendar, «Agendar visita» deriva a WhatsApp en vez de reservar'),
]


def revisar_placeholders():
    js = open(os.path.join(RAIZ, 'assets', 'js', 'main.js'), encoding='utf-8').read()
    faltan = [(c, m) for c, patron, m in PENDIENTES if re.search(patron, js)]
    # identidad legal: sin razón social y CUIT no se puede operar ni entrar a un country
    gen = open(os.path.join(RAIZ, 'tools', 'generar.py'), encoding='utf-8').read()
    bloque = gen[gen.index('EMPRESA = {'):gen.index('}', gen.index('EMPRESA = {'))]
    if 'PENDIENTE' in bloque:
        faltan.append(('EMPRESA', 'faltan razón social, CUIT o domicilio: aparecen como PENDIENTE en el pie '
                                  'y en las páginas de privacidad y términos'))
    html = open(os.path.join(RAIZ, 'terminos.html'), encoding='utf-8').read() if os.path.exists(os.path.join(RAIZ, 'terminos.html')) else ''
    if 'PENDIENTE' in html:
        faltan.append(('garantía', 'el plazo de garantía de la instalación sigue como PENDIENTE en terminos.html'))
    # el único número del bloque «qué entra en el precio»: es la promesa más
    # concreta del sitio y la primera que un cliente va a reclamar
    if re.search(r"METROS_INCLUIDOS\s*=\s*'PENDIENTE'", gen):
        faltan.append(('METROS_INCLUIDOS', 'falta cuántos metros de cañería entran en el precio cerrado: '
                                           'servicios.html lo muestra como «Hasta PENDIENTE metros»'))
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

REDIRECTS = """https://www.climabaires.com/* https://climabaires.com/:splat 301!
"""


def excluido(rel):
    rel = rel.replace(os.sep, '/')
    return any(rel == e or rel.startswith(e + '/') for e in EXCLUIR)


def main():
    faltan = revisar_placeholders()
    if faltan and '--force' not in sys.argv:
        print('NO se armó el paquete: hay datos de configuración sin completar.\n')
        for clave, motivo in faltan:
            donde = 'main.js → CB' if clave in ('whatsapp', 'gtmId', 'agendaUrl') else 'generar.py → EMPRESA'
            print(f'  ✗ {clave}  ({donde})')
            print(f'      {motivo}')
        print('\nDespués de completarlos hay que correr  python3 web/tools/generar.py')
        print('para rehornear los datos en el HTML.')
        print('\nSi querés armar el paquete igual (por ejemplo para una demo), agregá --force.')
        raise SystemExit(1)
    if faltan:
        print('AVISO: se arma con placeholders sin resolver (--force):')
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
    print(f'  {copiados} archivos · {peso // 1024} KB   (se omitieron {omitidos}: originales, capturas y scripts)')
    print('  + _headers (caché) y _redirects (www → raíz)')


if __name__ == '__main__':
    main()
