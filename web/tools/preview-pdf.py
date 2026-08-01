# -*- coding: utf-8 -*-
"""Compone un PDF de revisión con las capturas de la web (desktop + móvil).
Uso: npm run web:shots && python3 web/tools/preview-pdf.py
Salida: dist/Web-climabaires-com-Preview_v0.9.pdf (una página del PDF por página del sitio)
"""
import glob, os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(__file__)
SHOTS = os.path.join(AQUI, 'shots')
SALIDA = os.path.join(AQUI, '..', '..', 'dist', 'Web-climabaires-com-Preview_v0.9.pdf')

AZUL, NAVY, BLANCO = (0, 88, 179), (0, 40, 90), (255, 255, 255)
ANCHO = 1440  # lienzo base (px)

def fuente(tam, peso='600'):
    # PIL no lee woff2: usamos DejaVu del sistema (el texto de banda es utilitario)
    ruta = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if peso in ('600', '800') else '')
    try:
        return ImageFont.truetype(ruta, tam)
    except Exception:
        return ImageFont.load_default()

NOMBRES = {
    'index': 'Inicio', 'servicios': 'Servicios', 'obras': 'Obras recientes',
    'calculadora-frigorias': 'Calculadora de frigorías',
    'sobre-nosotros': 'Sobre nosotros', 'contacto': 'Contacto', '404': 'Página 404',
    'zonas_nunez': 'Zona: Núñez', 'zonas_vicente-lopez': 'Zona: Vicente López',
    'zonas_san-isidro': 'Zona: San Isidro', 'zonas_tigre': 'Zona: Tigre',
    'zonas_nordelta': 'Zona: Nordelta', 'zonas_pilar': 'Zona: Pilar',
}
ORDEN = ['index', 'servicios', 'obras', 'calculadora-frigorias', 'zonas_nunez', 'zonas_vicente-lopez',
         'zonas_san-isidro', 'zonas_tigre', 'zonas_nordelta', 'zonas_pilar',
         'sobre-nosotros', 'contacto', '404']

def con_banda(path, titulo):
    """Devuelve la captura con una banda superior de identificación."""
    im = Image.open(path).convert('RGB')
    if im.width != ANCHO:
        im = im.resize((ANCHO, int(im.height * ANCHO / im.width)), Image.LANCZOS)
    banda = 64
    lienzo = Image.new('RGB', (ANCHO, im.height + banda), BLANCO)
    d = ImageDraw.Draw(lienzo)
    d.rectangle([0, 0, ANCHO, banda], fill=NAVY)
    d.text((28, 18), f'climabaires.com — {titulo}', fill=BLANCO, font=fuente(28))
    lienzo.paste(im, (0, banda))
    return lienzo

paginas = []

# Portada del preview
port = Image.new('RGB', (ANCHO, 1000), NAVY)
d = ImageDraw.Draw(port)
logo = Image.open(os.path.join(AQUI, '..', '..', 'kit-digital', 'assets', 'portada-facebook-820x312.png'))
port.paste(logo.resize((820, 312)), ((ANCHO - 820) // 2, 160))
d.text((ANCHO // 2, 580), 'Vista previa de climabaires.com', fill=BLANCO, font=fuente(52, '800'), anchor='mm')
d.text((ANCHO // 2, 660), 'v0.9 — 12 páginas en desktop (1440 px) + 3 vistas móviles (390 px)', fill=(191, 228, 255), font=fuente(28, '400'), anchor='mm')
d.text((ANCHO // 2, 720), 'Sitio estático listo para desplegar · guía en web/README.md', fill=(191, 228, 255), font=fuente(28, '400'), anchor='mm')
paginas.append(port)

for clave in ORDEN:
    f = os.path.join(SHOTS, f'{clave}-desktop.png')
    if os.path.exists(f):
        paginas.append(con_banda(f, NOMBRES.get(clave, clave) + ' · desktop'))

for clave in ['index', 'zonas_nordelta', 'contacto']:
    f = os.path.join(SHOTS, f'{clave}-movil.png')
    if os.path.exists(f):
        im = Image.open(f).convert('RGB')
        im = im.resize((560, int(im.height * 560 / im.width)), Image.LANCZOS)
        banda = 64
        lienzo = Image.new('RGB', (ANCHO, im.height + banda), (242, 247, 252))
        d = ImageDraw.Draw(lienzo)
        d.rectangle([0, 0, ANCHO, banda], fill=NAVY)
        d.text((28, 18), f'climabaires.com — {NOMBRES.get(clave, clave)} · móvil (390 px)', fill=BLANCO, font=fuente(28))
        lienzo.paste(im, ((ANCHO - 560) // 2, banda))
        paginas.append(lienzo)

# límite de alto razonable por página del PDF (las capturas largas se trocean)
MAXH = 4000
finales = []
for im in paginas:
    if im.height <= MAXH:
        finales.append(im)
    else:
        y = 0
        while y < im.height:
            finales.append(im.crop((0, y, ANCHO, min(y + MAXH, im.height))))
            y += MAXH

finales[0].save(SALIDA, save_all=True, append_images=finales[1:], resolution=150)
print(f'OK {SALIDA} · {len(finales)} páginas')
