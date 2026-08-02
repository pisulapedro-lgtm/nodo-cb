# -*- coding: utf-8 -*-
"""Decide sobre qué escribe el blog la próxima vez.

Es lo primero que corre la rutina automática de publicación (cada tres días):
mira el calendario editorial, descarta los temas que ya tienen su archivo .md y
devuelve un briefing completo del siguiente —tema, ángulo, ruta donde guardarlo
y la guía de estilo entera— para que quien escriba no tenga que adivinar nada.

    python3 web/tools/siguiente-nota.py            briefing en texto
    python3 web/tools/siguiente-nota.py --json     lo mismo, para scripts
    python3 web/tools/siguiente-nota.py --estado   qué se publicó y qué falta

Códigos de salida: 0 hay tema · 3 se acabaron los temas pendientes.

El estado real lo manda el disco, no el JSON: un tema está publicado si existe
su archivo en web/contenido/blog/. El campo «estado» del calendario se
sincroniza solo en cada corrida, así que si la rutina se cae después de escribir
el .md pero antes de commitear, la próxima no repite el tema.
"""
import json
import os
import re
import sys
from datetime import date

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
CALENDARIO = os.path.join(RAIZ, 'contenido', 'calendario.json')
ESTILO = os.path.join(RAIZ, 'contenido', 'estilo-blog.md')
BLOG = os.path.join(RAIZ, 'contenido', 'blog')

SIN_TEMAS = 3


def _slugs_publicados():
    """Slugs que ya tienen archivo, sin el prefijo numérico (05-ruido.md → ruido)."""
    if not os.path.isdir(BLOG):
        return set()
    return {re.sub(r'^\d+-', '', a[:-3]) for a in os.listdir(BLOG) if a.endswith('.md')}


def _proximo_numero():
    """Prefijo del próximo archivo: mantiene el orden cronológico en el listado."""
    if not os.path.isdir(BLOG):
        return 1
    numeros = [int(m.group(1)) for a in os.listdir(BLOG)
               if a.endswith('.md') and (m := re.match(r'(\d+)-', a))]
    return max(numeros, default=0) + 1


def cargar():
    """Devuelve (calendario, temas) con el estado ya sincronizado contra el disco."""
    with open(CALENDARIO, encoding='utf-8') as f:
        cal = json.load(f)
    publicados = _slugs_publicados()
    cambio = False
    for t in cal['temas']:
        real = 'publicado' if t['slug'] in publicados else 'pendiente'
        if t.get('estado') != real:
            t['estado'] = real
            cambio = True
    if cambio:
        with open(CALENDARIO, 'w', encoding='utf-8') as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
            f.write('\n')
    return cal, cal['temas']


def siguiente(temas):
    for t in temas:
        if t['estado'] == 'pendiente':
            return t
    return None


def briefing(tema):
    numero = _proximo_numero()
    archivo = f'{numero:02d}-{tema["slug"]}.md'
    ruta = os.path.relpath(os.path.join(BLOG, archivo), os.path.join(RAIZ, '..'))
    estilo = open(ESTILO, encoding='utf-8').read() if os.path.exists(ESTILO) else ''
    return {
        'slug': tema['slug'],
        'titulo': tema['titulo'],
        'categoria': tema['categoria'],
        'angulo': tema['angulo'],
        'archivo': archivo,
        'ruta': ruta,
        'fecha': date.today().isoformat(),
        'estilo': estilo,
    }


def texto(b):
    return f"""TEMA DE ESTA PUBLICACIÓN
------------------------
Título orientativo : {b['titulo']}
Categoría          : {b['categoria']}
Fecha a poner      : {b['fecha']}
Archivo a crear    : {b['ruta']}

Ángulo:
{b['angulo']}

El título orientativo se puede mejorar, mientras respete el ángulo y no pase de
60 caracteres.

{b['estilo']}"""


def main():
    args = sys.argv[1:]
    cal, temas = cargar()

    if '--estado' in args:
        hechos = [t for t in temas if t['estado'] == 'publicado']
        faltan = [t for t in temas if t['estado'] == 'pendiente']
        print(f'Calendario editorial: {len(hechos)} publicados · {len(faltan)} pendientes\n')
        for t in temas:
            marca = '·' if t['estado'] == 'publicado' else '→'
            print(f'  {marca} {t["slug"]:<34} {t["titulo"]}')
        if not faltan:
            print('\nNo quedan temas. Agregá más en web/contenido/calendario.json.')
            return SIN_TEMAS
        return 0

    tema = siguiente(temas)
    if tema is None:
        aviso = ('SIN TEMAS PENDIENTES.\n'
                 'El calendario editorial (web/contenido/calendario.json) se quedó sin temas '
                 'con estado «pendiente». No inventes uno: avisá y no publiques nada.')
        if '--json' in args:
            print(json.dumps({'agotado': True, 'aviso': aviso}, ensure_ascii=False, indent=2))
        else:
            print(aviso)
        return SIN_TEMAS

    b = briefing(tema)
    print(json.dumps(b, ensure_ascii=False, indent=2) if '--json' in args else texto(b))
    return 0


if __name__ == '__main__':
    sys.exit(main())
