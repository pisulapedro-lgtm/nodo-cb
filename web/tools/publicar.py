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
import shutil

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DESTINO = os.path.normpath(os.path.join(RAIZ, '..', 'dist', 'sitio'))

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
