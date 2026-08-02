# -*- coding: utf-8 -*-
"""Blog de climabaires.es: lee los .md de web-es/contenido/blog/ y devuelve las
entradas listas para que generar.py arme las páginas.

Los posts se escriben en Markdown con un front-matter de cinco campos:

    ---
    titulo: Cuántas frigorías necesito
    resumen: Una frase de hasta 155 caracteres, que va como meta description.
    fecha: 2026-08-01
    categoria: guia
    minutos: 6
    ---

El conversor soporta a propósito un subconjunto chico de Markdown —encabezados,
párrafos, listas, negrita, itálica, enlaces, citas y tablas simples—: alcanza
para un blog de servicios y evita meter una dependencia sólo para esto.
"""
import html
import os
import re
from datetime import date

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FUENTE = os.path.join(RAIZ, 'contenido', 'blog')

CATEGORIAS = {
    'guia': 'Guías',
    'mantenimiento': 'Mantenimiento',
    'zonas': 'Costa del Sol',
    'equipos': 'Equipos',
    'eficiencia': 'Eficiencia y ayudas',
}

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def fecha_larga(f):
    return f'{f.day} de {MESES[f.month - 1]} de {f.year}'


# ---------------------------------------------------------------- conversor

def _en_linea(t):
    """Marcas dentro de un párrafo. El texto se escapa primero: nada de HTML
    crudo en los posts, aunque los escriba un proceso automático."""
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def markdown_a_html(md):
    salida = []
    lista = None          # 'ul' | 'ol' | None
    parrafo = []
    tabla = []

    def cerrar_parrafo():
        nonlocal parrafo
        if parrafo:
            salida.append('<p>%s</p>' % _en_linea(' '.join(parrafo)))
            parrafo = []

    def cerrar_lista():
        nonlocal lista
        if lista:
            salida.append(f'</{lista}>')
            lista = None

    def cerrar_tabla():
        nonlocal tabla
        if not tabla:
            return
        celdas = [[c.strip() for c in f.strip().strip('|').split('|')] for f in tabla]
        cuerpo = [f for f in celdas[1:] if not all(set(c) <= set('-: ') for c in f)]
        salida.append('<table class="simple"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
            ''.join(f'<th>{_en_linea(c)}</th>' for c in celdas[0]),
            ''.join('<tr>%s</tr>' % ''.join(f'<td>{_en_linea(c)}</td>' for c in f) for f in cuerpo),
        ))
        tabla = []

    for linea in md.split('\n'):
        s = linea.rstrip()

        if s.lstrip().startswith('|') and s.rstrip().endswith('|'):
            cerrar_parrafo(); cerrar_lista()
            tabla.append(s)
            continue
        cerrar_tabla()

        if not s.strip():
            cerrar_parrafo(); cerrar_lista()
            continue

        m = re.match(r'(#{2,4})\s+(.*)', s)
        if m:
            cerrar_parrafo(); cerrar_lista()
            n = len(m.group(1))
            salida.append(f'<h{n}>{_en_linea(m.group(2))}</h{n}>')
            continue

        if s.startswith('> '):
            cerrar_parrafo(); cerrar_lista()
            salida.append(f'<blockquote>{_en_linea(s[2:])}</blockquote>')
            continue

        m = re.match(r'\s*[-*]\s+(.*)', s)
        if m:
            cerrar_parrafo()
            if lista != 'ul':
                cerrar_lista(); salida.append('<ul class="lista-check">'); lista = 'ul'
            salida.append(f'<li>{_en_linea(m.group(1))}</li>')
            continue

        m = re.match(r'\s*\d+\.\s+(.*)', s)
        if m:
            cerrar_parrafo()
            if lista != 'ol':
                cerrar_lista(); salida.append('<ol class="lista-num">'); lista = 'ol'
            salida.append(f'<li>{_en_linea(m.group(1))}</li>')
            continue

        parrafo.append(s.strip())

    cerrar_parrafo(); cerrar_lista(); cerrar_tabla()
    return '\n'.join(salida)


# ---------------------------------------------------------------- lectura

def _front_matter(texto, archivo):
    if not texto.startswith('---'):
        raise SystemExit(f'{archivo}: falta el front-matter')
    _, cabecera, cuerpo = texto.split('---', 2)
    datos = {}
    for linea in cabecera.strip().split('\n'):
        if ':' in linea:
            k, v = linea.split(':', 1)
            datos[k.strip()] = v.strip()
    faltan = {'titulo', 'resumen', 'fecha', 'categoria'} - set(datos)
    if faltan:
        raise SystemExit(f'{archivo}: faltan campos en el front-matter: {", ".join(sorted(faltan))}')
    if datos['categoria'] not in CATEGORIAS:
        raise SystemExit(f'{archivo}: categoría desconocida «{datos["categoria"]}»')
    return datos, cuerpo.strip()


def cargar():
    """Devuelve los posts publicados, del más nuevo al más viejo.
    Un post con fecha futura queda fuera: así se puede dejar material escrito
    esperando su turno."""
    if not os.path.isdir(FUENTE):
        return []
    hoy = date.today()
    posts = []
    for archivo in sorted(os.listdir(FUENTE)):
        if not archivo.endswith('.md'):
            continue
        texto = open(os.path.join(FUENTE, archivo), encoding='utf-8').read()
        datos, cuerpo = _front_matter(texto, archivo)
        f = date.fromisoformat(datos['fecha'])
        if f > hoy:
            continue
        palabras = len(re.sub(r'[#*>\[\]()|-]', ' ', cuerpo).split())
        posts.append({
            'slug': re.sub(r'^\d+-', '', archivo[:-3]),
            'titulo': datos['titulo'],
            'resumen': datos['resumen'],
            'fecha': f,
            'fecha_iso': datos['fecha'],
            'fecha_larga': fecha_larga(f),
            'categoria': datos['categoria'],
            'categoria_label': CATEGORIAS[datos['categoria']],
            'minutos': int(datos.get('minutos') or max(1, round(palabras / 200))),
            'palabras': palabras,
            'html': markdown_a_html(cuerpo),
        })
    posts.sort(key=lambda p: p['fecha'], reverse=True)
    return posts
