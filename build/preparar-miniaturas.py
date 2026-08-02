# -*- coding: utf-8 -*-
"""Prepara las miniaturas de climabaires.com que se incrustan en el PDF.

    npm run miniaturas    →    build/assets/web/*.jpg + manifest.json

Entrada: las capturas de QA de `web/tools/shots/` (se regeneran con `npm run web:shots`).
Salida: miniaturas livianas de ~30 KB, porque las capturas de origen pesan hasta
3,5 MB cada una y el PDF tiene que seguir siendo un archivo que se manda por mail.

De cada página se recorta la parte de arriba —lo que se ve sin hacer scroll—: una
miniatura de una captura de 6.000 px de alto no se lee, y lo que comunica el diseño
es el primer pantallazo.
"""
import json, os
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(RAIZ, 'web', 'tools', 'shots')
SALIDA = os.path.join(RAIZ, 'build', 'assets', 'web')

ANCHO = 560          # px de la miniatura; a 3 columnas en A4 sobra resolución
PROPORCION = 0.78    # alto/ancho del recorte: algo más alto que 4:3, como un pantallazo
CALIDAD = 80

# Orden de lectura del sitio, no orden alfabético.
PAGINAS = [
    ('index',                'Inicio',                  'Hero con foto de instalación real, marcas con las que trabajamos y últimos trabajos'),
    ('servicios',            'Servicios',               'Venta, instalación y posventa, con el encuadre de «instalación con provisión de equipo»'),
    ('obras',                'Obras',                   'La galería del sitio: filtrable por zona y tipo, con ampliación y pares antes/después'),
    ('calculadora-frigorias', 'Calculadora de frigorías', 'La herramienta de captación: calcula y pasa el resultado a WhatsApp'),
    ('zonas_nunez',          'Zona · Núñez',            'Página local de CABA; cada zona es además una landing de Google Ads'),
    ('zonas_vicente-lopez',  'Zona · Vicente López',    'Página local de la primera corona del corredor norte'),
    ('zonas_san-isidro',     'Zona · San Isidro',       'Página local orientada a vivienda unifamiliar'),
    ('zonas_tigre',          'Zona · Tigre',            'Página local con foco en countries y barrios cerrados'),
    ('zonas_nordelta',       'Zona · Nordelta',         'La página de mayor ticket esperado del sitio'),
    ('zonas_pilar',          'Zona · Pilar',            'Página local del extremo norte del corredor'),
    ('blog_index',           'Blog',                    'Índice de notas: el motor de SEO que publica solo cada tres días'),
    ('blog_cuantas-frigorias-necesito', 'Nota del blog', 'Cada nota se escribe en Markdown y se publica cuando llega su fecha'),
    ('sobre-nosotros',       'Sobre nosotros',          'La historia Málaga → Buenos Aires y la franja «así trabajamos»'),
    ('contacto',             'Contacto',                'WhatsApp primero, agenda de Calendar después, formulario al final'),
    ('privacidad',           'Privacidad',              'Política de privacidad: requisito para publicar y para anunciar en Google'),
    ('terminos',             'Términos',                'Condiciones de servicio, garantías y derecho de arrepentimiento'),
    ('404',                  'Página 404',              'Error con salida a WhatsApp en lugar de callejón sin salida'),
]

# Vistas complementarias. Cada una declara de qué captura sale: el asistente vive
# en la captura de escritorio aunque se muestre junto a las móviles.
OTRAS = [
    ('index',   'movil',   'Inicio · móvil',   'El grueso del tráfico llega por móvil: es la vista que más importa'),
    ('obras',   'movil',   'Obras · móvil',    'La galería en móvil, con la barra inferior fija de WhatsApp y agenda'),
    ('chatbot', 'desktop', 'Asistente',        'El asistente de 4 preguntas arma el mensaje y deriva el chat a WhatsApp'),
]


def miniatura(clave, vista):
    origen = os.path.join(SHOTS, f'{clave}-{vista}.png')
    if not os.path.exists(origen):
        return None
    im = Image.open(origen).convert('RGB')
    alto_recorte = min(im.height, int(im.width * PROPORCION))
    im = im.crop((0, 0, im.width, alto_recorte))
    im = im.resize((ANCHO, int(alto_recorte * ANCHO / im.width)), Image.LANCZOS)
    nombre = f'{clave}-{vista}.jpg'
    im.save(os.path.join(SALIDA, nombre), 'JPEG', quality=CALIDAD, optimize=True)
    return nombre


os.makedirs(SALIDA, exist_ok=True)
manifiesto, faltan = [], []

entradas = [(c, 'desktop', t_, p_) for c, t_, p_ in PAGINAS] + OTRAS
for clave, vista, titulo, pie in entradas:
    nombre = miniatura(clave, vista)
    if nombre is None:
        faltan.append(f'{clave}-{vista}')
        continue
    manifiesto.append({'archivo': nombre, 'titulo': titulo, 'pie': pie, 'vista': vista})

with open(os.path.join(SALIDA, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifiesto, f, ensure_ascii=False, indent=2)

peso = sum(os.path.getsize(os.path.join(SALIDA, m['archivo'])) for m in manifiesto)
print(f'OK  {SALIDA}')
print(f'    {len(manifiesto)} miniaturas · {peso // 1024} KB en total')
if faltan:
    print(f'    FALTAN capturas ({", ".join(faltan)}): correr `npm run web:shots` primero')
