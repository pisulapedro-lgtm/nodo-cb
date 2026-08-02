# -*- coding: utf-8 -*-
"""Compone el PDF de revisión de climabaires.com, **en versión móvil**.

Uso: npm run web:shots && python3 web/tools/preview-pdf.py
Salida: dist/Web-climabaires-com-Preview_v0.9.pdf

El móvil es la vista que importa (la mayoría del tráfico y de los clics de
WhatsApp llega de ahí), así que el PDF recorre cada página del sitio con la
captura de 390 px troceada en columnas contiguas: se lee la página entera de
corrido, de izquierda a derecha, sin cortes a mitad de sección. Al final se
agregan las mismas páginas en desktop, como anexo.
"""
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(__file__)
SHOTS = os.path.join(AQUI, 'shots')
SALIDA = os.path.join(AQUI, '..', '..', 'dist', 'Web-climabaires-com-Preview_v0.9.pdf')

AZUL, NAVY, CELESTE = (0, 88, 179), (0, 40, 90), (0, 168, 252)
BLANCO, HIELO, GRIS = (255, 255, 255), (242, 247, 252), (90, 102, 117)

# hoja A4 apaisada a 150 dpi: entran cuatro columnas de teléfono cómodas
HOJA = (1754, 1240)
BANDA = 92                      # alto de la banda de título
MARGEN = 34
COLS = 4
ANCHO_TEL = 366                 # ancho de cada columna de teléfono en la hoja


def fuente(tam, negrita=False):
    ruta = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if negrita else '')
    try:
        return ImageFont.truetype(ruta, tam)
    except Exception:
        return ImageFont.load_default()


NOMBRES = {
    'index': 'Inicio', 'servicios': 'Servicios', 'obras': 'Obras recientes',
    'calculadora-frigorias': 'Calculadora de frigorías',
    'sobre-nosotros': 'Sobre nosotros', 'contacto': 'Contacto', '404': 'Página 404',
    'zonas_nunez': 'Zona · Núñez', 'zonas_vicente-lopez': 'Zona · Vicente López',
    'zonas_san-isidro': 'Zona · San Isidro', 'zonas_tigre': 'Zona · Tigre',
    'zonas_nordelta': 'Zona · Nordelta', 'zonas_pilar': 'Zona · Pilar',
    'chatbot': 'Asistente de WhatsApp', 'privacidad': 'Política de privacidad', 'terminos': 'Términos y condiciones',
    'blog_index': 'Blog · índice',
}


def nota_de_muestra():
    """El QA captura el índice del blog y la nota más nueva. Cuál es la más nueva
    cambia sola cada tres días, así que acá se busca en vez de nombrarla."""
    for f in sorted(os.listdir(SHOTS)):
        if f.startswith('blog_') and f.endswith('-movil.png') and not f.startswith('blog_index'):
            clave = f[:-len('-movil.png')]
            NOMBRES[clave] = 'Blog · una entrada completa'
            return [clave]
    return []


ORDEN = ['index', 'servicios', 'obras', 'calculadora-frigorias', 'contacto',
         'zonas_nordelta', 'zonas_nunez', 'zonas_vicente-lopez', 'zonas_san-isidro',
         'zonas_tigre', 'zonas_pilar', 'sobre-nosotros', 'blog_index'] + nota_de_muestra() + [
         'privacidad', 'terminos', '404']


def banda(lienzo, titulo, sub=''):
    d = ImageDraw.Draw(lienzo)
    d.rectangle([0, 0, HOJA[0], BANDA], fill=NAVY)
    d.rectangle([0, BANDA - 4, HOJA[0], BANDA], fill=CELESTE)
    d.text((MARGEN, 24), titulo, fill=BLANCO, font=fuente(34, True))
    if sub:
        d.text((HOJA[0] - MARGEN, 36), sub, fill=(159, 212, 255), font=fuente(22), anchor='ra')
    return d


def columnas_de(captura, titulo):
    """Trocea una captura móvil en columnas y las maqueta en hojas apaisadas."""
    im = Image.open(captura).convert('RGB')
    escala = ANCHO_TEL / im.width
    im = im.resize((ANCHO_TEL, round(im.height * escala)), Image.LANCZOS)

    alto_col = HOJA[1] - BANDA - MARGEN * 2
    trozos = []
    y = 0
    while y < im.height:
        trozos.append(im.crop((0, y, im.width, min(y + alto_col, im.height))))
        y += alto_col

    hojas = []
    for i in range(0, len(trozos), COLS):
        grupo = trozos[i:i + COLS]
        hoja = Image.new('RGB', HOJA, HIELO)
        sub = 'móvil 390 px' + (f' · parte {i // COLS + 1}' if len(trozos) > COLS else '')
        d = banda(hoja, titulo, sub)
        hueco = (HOJA[0] - MARGEN * 2 - ANCHO_TEL * len(grupo)) // max(len(grupo) - 1, 1) if len(grupo) > 1 else 0
        hueco = min(hueco, 46)
        ancho_total = ANCHO_TEL * len(grupo) + hueco * (len(grupo) - 1)
        x = (HOJA[0] - ancho_total) // 2
        for t in grupo:
            marco = [x - 3, BANDA + MARGEN - 3, x + ANCHO_TEL + 2, BANDA + MARGEN + t.height + 2]
            d.rectangle(marco, outline=(203, 220, 236), width=2)
            hoja.paste(t, (x, BANDA + MARGEN))
            x += ANCHO_TEL + hueco
        hojas.append(hoja)
    return hojas


paginas = []

# ---- portada ----
port = Image.new('RGB', HOJA, NAVY)
d = ImageDraw.Draw(port)
d.rectangle([0, HOJA[1] - 10, HOJA[0], HOJA[1]], fill=CELESTE)
logo = Image.open(os.path.join(AQUI, '..', '..', 'kit-digital', 'assets', 'portada-facebook-820x312.png'))
port.paste(logo.resize((700, 266)), ((HOJA[0] - 700) // 2, 210))
d.text((HOJA[0] // 2, 580), 'climabaires.com', fill=BLANCO, font=fuente(64, True), anchor='mm')
d.text((HOJA[0] // 2, 660), 'Vista previa — versión móvil', fill=(159, 212, 255), font=fuente(34), anchor='mm')
d.text((HOJA[0] // 2, 730), '17 páginas capturadas en 390 px · el orden de lectura es de izquierda a derecha',
       fill=(159, 212, 255), font=fuente(24), anchor='mm')
d.text((HOJA[0] // 2, 790), 'Anexo al final: las mismas páginas en escritorio (1440 px)',
       fill=(159, 212, 255), font=fuente(24), anchor='mm')
paginas.append(port)

# ---- cuerpo: cada página en móvil ----
for clave in ORDEN:
    f = os.path.join(SHOTS, f'{clave}-movil.png')
    if os.path.exists(f):
        paginas.extend(columnas_de(f, NOMBRES.get(clave, clave)))

# ---- el asistente de WhatsApp, con una conversación completa ----
f = os.path.join(SHOTS, 'chatbot-desktop.png')
if os.path.exists(f):
    im = Image.open(f).convert('RGB')
    hoja = Image.new('RGB', HOJA, HIELO)
    d = banda(hoja, 'Asistente de WhatsApp', 'cuatro preguntas y el chat queda armado')
    an = HOJA[0] - MARGEN * 2
    im = im.resize((an, round(im.height * an / im.width)), Image.LANCZOS)
    if im.height > HOJA[1] - BANDA - MARGEN * 2:
        im = im.crop((0, 0, im.width, HOJA[1] - BANDA - MARGEN * 2))
    hoja.paste(im, (MARGEN, BANDA + MARGEN))
    paginas.append(hoja)

# ---- anexo: escritorio ----
sep = Image.new('RGB', HOJA, NAVY)
d = ImageDraw.Draw(sep)
d.text((HOJA[0] // 2, HOJA[1] // 2 - 20), 'Anexo · escritorio', fill=BLANCO, font=fuente(56, True), anchor='mm')
d.text((HOJA[0] // 2, HOJA[1] // 2 + 50), 'Inicio, obras, servicios, una zona y contacto en 1440 px',
       fill=(159, 212, 255), font=fuente(28), anchor='mm')
paginas.append(sep)

# el anexo es de referencia: sólo las páginas donde el escritorio cambia el diseño
ANEXO = ['index', 'obras', 'servicios', 'zonas_nordelta', 'blog_index', 'contacto']
for clave in ANEXO:
    f = os.path.join(SHOTS, f'{clave}-desktop.png')
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert('RGB')
    an = HOJA[0] - MARGEN * 2
    im = im.resize((an, round(im.height * an / im.width)), Image.LANCZOS)
    alto_util = HOJA[1] - BANDA - MARGEN * 2
    y, parte = 0, 1
    while y < im.height:
        trozo = im.crop((0, y, im.width, min(y + alto_util, im.height)))
        hoja = Image.new('RGB', HOJA, HIELO)
        banda(hoja, NOMBRES.get(clave, clave), 'escritorio 1440 px' + (f' · parte {parte}' if im.height > alto_util else ''))
        hoja.paste(trozo, (MARGEN, BANDA + MARGEN))
        paginas.append(hoja)
        y += alto_util
        parte += 1

paginas[0].save(SALIDA, save_all=True, append_images=paginas[1:], resolution=150)
print(f'OK {os.path.normpath(SALIDA)} · {len(paginas)} hojas (móvil primero)')
