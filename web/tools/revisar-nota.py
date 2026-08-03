# -*- coding: utf-8 -*-
"""Revisa una nota del blog antes de que se publique sola.

La rutina automática escribe sin que nadie mire, así que este script es el
control: si algo no pasa, el generador no corre y no se sube nada.

    python3 web/tools/revisar-nota.py                    revisa todas las notas
    python3 web/tools/revisar-nota.py 01-multisplit.md   revisa una

Códigos de salida: 0 todo bien · 1 hay errores.

Distingue **errores** (bloquean la publicación: promesas falsas, castellano de
España, enlaces rotos, front-matter mal) de **avisos** (se imprimen y siguen:
largo fuera de lo ideal, pocos subtítulos). La lista de prohibiciones sale de
web/contenido/estilo-blog.md; si cambiás las reglas allá, actualizá acá.
"""
import os
import re
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
BLOG = os.path.join(RAIZ, 'contenido', 'blog')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog as _blog  # noqa: E402  (necesita el sys.path de arriba)

# Castellano peninsular: el sitio entero está en rioplatense y el contraste canta.
ESPANOLISMOS = [
    (r'\bfurgonet\w*', 'furgoneta → camioneta'),
    (r'\bnaves?\b', 'nave → depósito'),
    (r'\bordenador\w*', 'ordenador → computadora'),
    (r'\bvosotros\b|\bvuestr\w+', 'vosotros/vuestro → ustedes/su'),
    (r'\bcoger\b|\bcoge\b|\bcogé\b', 'coger → agarrar, tomar'),
    (r'\bgrifo\b', 'grifo → canilla'),
    (r'\bmóvil\b(?!\s*(?:390|\d))', 'móvil → celular'),
    (r'\bfontaner\w+', 'fontanero → plomero'),
    (r'\balbañiler\w*a\b', 'albañilería está bien, pero revisá el contexto peninsular'),
    (r'\bzumo\b|\bordenar el piso\b', 'léxico peninsular'),
    (r'\bpisos?\b(?=\s+(?:de\s+\d|con\s+\d|pequeñ|grand))', 'piso → departamento'),
    (r'\btú\b|\bcontigo\b|\btu casa tienes\b|\btienes\b|\bpuedes\b|\bdebes\b|\bquieres\b|\bnecesitas\b(?<!\bvos)',
     'tuteo peninsular → voseo (tenés, podés, debés, querés, necesitás)'),
]

# Cosas que el negocio todavía no puede afirmar.
PROMESAS = [
    (r'(?:instalamos|colocamos|hicimos|trabajamos|estuvimos)\s+(?:\w+\s+){0,3}'
     r'(?:en|para)\s+(?:Núñez|Nunez|Vicente López|San Isidro|Tigre|Nordelta|Pilar)',
     'trabajo argentino inventado: todavía no hay obras hechas acá'),
    (r'(?:un|una|nuestro|nuestra)\s+client\w+\s+de\s+'
     r'(?:Núñez|Nunez|Vicente López|San Isidro|Tigre|Nordelta|Pilar)',
     'cliente argentino inventado'),
    (r'garantía\s+de\s+\d+\s*(?:año|mes)', 'plazo de garantía sin confirmar'),
    (r'\bcertificad\w+\s+(?:por|en)\s+\w', 'certificación sin confirmar'),
    (r'\$\s?\d|\bAR\$|\bpesos\b\s*\d|\b\d+\s*(?:mil|millones)\s+de\s+pesos',
     'importe en pesos: se desactualiza y queda como mentira'),
    (r'respondemos\s+(?:siempre|24|las 24)', 'disponibilidad fuera del horario real'),
    (r'\bel mejor\b|\blíder\w*\s+(?:del|en)\b|\bnúmero uno\b', 'superlativo no demostrable'),
]

RUTAS_VALIDAS = None


def _rutas():
    """Archivos .html que existen en el sitio, en rutas relativas desde /blog/."""
    global RUTAS_VALIDAS
    if RUTAS_VALIDAS is None:
        RUTAS_VALIDAS = set()
        for base, _, archivos in os.walk(RAIZ):
            if any(p in base for p in ('tools', 'contenido', 'assets')):
                continue
            for a in archivos:
                if a.endswith('.html'):
                    rel = os.path.relpath(os.path.join(base, a), RAIZ).replace(os.sep, '/')
                    RUTAS_VALIDAS.add('../' + rel)
    return RUTAS_VALIDAS


def revisar(archivo):
    errores, avisos = [], []
    texto = open(os.path.join(BLOG, archivo), encoding='utf-8').read()

    try:
        datos, cuerpo = _blog._front_matter(texto, archivo)
    except SystemExit as e:
        return [str(e)], []

    # --- front-matter ---
    if len(datos['titulo']) > 60:
        errores.append(f'título de {len(datos["titulo"])} caracteres (máximo 60): Google lo corta')
    if len(datos['resumen']) > 155:
        errores.append(f'resumen de {len(datos["resumen"])} caracteres (máximo 155): la meta description se corta')
    if len(datos['resumen']) < 60:
        avisos.append(f'resumen de {len(datos["resumen"])} caracteres: queda corto para la tarjeta')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', datos['fecha']):
        errores.append(f'fecha «{datos["fecha"]}» no está en formato AAAA-MM-DD')
    if datos['titulo'].lower().startswith('clima baires'):
        avisos.append('el título arranca con la marca: se come caracteres útiles')

    # --- prohibiciones ---
    plano = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cuerpo)
    for patron, motivo in ESPANOLISMOS + PROMESAS:
        for m in re.finditer(patron, plano, re.IGNORECASE):
            ctx = plano[max(0, m.start() - 40):m.end() + 40].replace('\n', ' ')
            errores.append(f'{motivo} → «…{ctx.strip()}…»')

    # --- enlaces ---
    enlaces = re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', cuerpo)
    internos = [u for _, u in enlaces if not u.startswith(('http://', 'https://'))]
    for t, u in enlaces:
        if u.startswith(('http://', 'https://')):
            errores.append(f'enlace externo a {u}: la guía no los permite')
        elif u.split('#')[0] not in _rutas():
            errores.append(f'enlace roto: {u} no existe en el sitio')
        if t.strip().lower() in ('acá', 'aquí', 'click', 'este enlace', 'ver más'):
            avisos.append(f'texto de enlace poco descriptivo: «{t}»')
    if len(internos) < 2:
        errores.append(f'{len(internos)} enlaces internos (mínimo 2): la nota queda aislada del sitio')

    # --- forma ---
    palabras = len(re.sub(r'[#*>\[\]()|-]', ' ', cuerpo).split())
    if palabras < 600:
        errores.append(f'{palabras} palabras: por debajo de 600 la nota no aporta nada')
    elif palabras > 1400:
        avisos.append(f'{palabras} palabras: por arriba de 1.400 no se lee entera')
    elif not 700 <= palabras <= 1100:
        avisos.append(f'{palabras} palabras (lo ideal es 700 a 1.100)')

    h2 = len(re.findall(r'^## ', cuerpo, re.M))
    if h2 < 3:
        errores.append(f'{h2} subtítulos ## (mínimo 3): el texto se lee como un ladrillo')
    elif h2 > 7:
        avisos.append(f'{h2} subtítulos: demasiado picado')
    if re.search(r'^# ', cuerpo, re.M):
        errores.append('hay un # en el cuerpo: el h1 lo pone la página, los subtítulos van con ##')

    if not re.search(r'^\s*[-*]\s+|^\s*\d+\.\s+|^\s*\|', cuerpo, re.M):
        errores.append('sin listas ni tablas: es lo primero que la gente escanea')
    if '!' in cuerpo or '¡' in cuerpo:
        avisos.append('signos de admiración: el tono del sitio no los usa')
    if re.search(r'[\U0001F300-\U0001FAFF☀-➿]', cuerpo):
        errores.append('hay emojis en el cuerpo')
    if re.search(r'<[a-z]+[\s>]', cuerpo, re.I):
        avisos.append('parece haber HTML crudo: el conversor lo va a escapar y se va a ver el tag')

    return errores, avisos


def main():
    objetivo = sys.argv[1:] or sorted(a for a in os.listdir(BLOG) if a.endswith('.md'))
    fallo = False
    for archivo in objetivo:
        archivo = os.path.basename(archivo)
        errores, avisos = revisar(archivo)
        estado = 'ERROR' if errores else ('aviso' if avisos else 'OK')
        print(f'{estado:>5}  {archivo}')
        for e in errores:
            print(f'         ✗ {e}')
        for a in avisos:
            print(f'         · {a}')
        fallo = fallo or bool(errores)
    if fallo:
        print('\nHay errores: corregí la nota y volvé a revisar antes de generar el sitio.')
    return 1 if fallo else 0


if __name__ == '__main__':
    sys.exit(main())
