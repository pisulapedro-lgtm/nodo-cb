# -*- coding: utf-8 -*-
"""Pipeline de fotos de obras de climabaires.com.
Uso: python3 web/tools/fotos.py [--force]

Lee originales de web/assets/img/originales/, corrige orientación EXIF,
elimina metadatos (privacidad: hay domicilios de clientes) y exporta a
web/assets/img/obras/ en WebP calidad 80, en dos tamaños:
  {slug}-1600.webp  → lado mayor máx. 1600 px (lightbox / hero)
  {slug}-800.webp   → lado mayor máx. 800 px (tarjetas / grillas)
Además genera:
  hero-home-{1600,800}.webp  → recorte 16:9 de la foto HERO para la portada
  og-home.jpg / og-obras.jpg → 1200×630 para Open Graph (JPEG: WhatsApp/FB
                               no siempre renderizan WebP en previews)
  index.json                 → índice consumido por tools/generar.py

Es idempotente: si los derivados existen y el original no cambió, no rehace
nada (correrlo dos veces no duplica). --force regenera todo.

Cómo añadir fotos nuevas: copiar los originales a originales/ y agregar una
entrada en MAPEO (slug descriptivo kebab-case, alt con zona real, tipo,
destacada). Un original sin entrada en MAPEO no se publica: el script lo
lista al final para que alguien lo describa (no inventamos ubicaciones ni
marcas). Fotos inutilizables: entrada en DESCARTES con el motivo → se mueven
a originales/descartadas/.

Pares antes/después: usar el campo "par" con el mismo identificador en las
dos fotos y tipo "antes-despues"; el slug debe empezar con "antes-" o
"despues-". El generador arma el bloque comparativo solo.
"""
import json
import os
import sys

from PIL import Image, ImageOps

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
ORIGINALES = os.path.join(RAIZ, 'assets', 'img', 'originales')
DESCARTADAS = os.path.join(ORIGINALES, 'descartadas')
OBRAS = os.path.join(RAIZ, 'assets', 'img', 'obras')
INDICE = os.path.join(OBRAS, 'index.json')

CALIDAD_WEBP = 80
CALIDAD_JPG = 82
TAMANOS = (1600, 800)          # lado mayor máximo de cada derivado
PESO_MAX = 350 * 1024          # ninguna imagen publicada puede superar 350 KB

# Zonas válidas (slug → etiqueta visible). "malaga" es la casa matriz: las
# fotos de España se publican como tales, nunca disfrazadas de zona AMBA.
ZONAS = {
    'nunez': 'Núñez', 'vicente-lopez': 'Vicente López', 'san-isidro': 'San Isidro',
    'tigre': 'Tigre', 'nordelta': 'Nordelta', 'pilar': 'Pilar',
    'malaga': 'Málaga (casa matriz)',
}
TIPOS = {
    'instalacion': 'Instalación', 'recambio': 'Recambio', 'mantenimiento': 'Mantenimiento',
    'piso-techo': 'Piso-techo', 'conductos': 'Cassette y conductos',
    'antes-despues': 'Antes / después', 'equipo': 'Equipo en obra',
}

# ---------------------------------------------------------------------------
# MAPEO: archivo original → foto publicada. El orden define la galería.
# alt: descriptivo + zona real, sin keyword stuffing ni datos inventados.
# ---------------------------------------------------------------------------
MAPEO = {
    'e8bd4a26-WhatsApp_Image_20250915_at_1.46.04_PM_4.jpeg': {
        'slug': 'instalacion-condensadora-azotea-malaga-01',
        'alt': 'Técnico de Clima Baires fijando una condensadora inverter A++ en una azotea, con la ciudad de Málaga de fondo',
        'zona': 'malaga', 'tipo': 'instalacion', 'destacada': True,
    },
    '38429ddc-a593b1865ff44481b16de2d161cd2227.jpeg': {
        'slug': 'instalacion-condensadora-fachada-malaga-01',
        'alt': 'Instalación de condensadora en fachada con plataforma elevadora: trabajo en altura con equipos certificados, Málaga',
        'zona': 'malaga', 'tipo': 'instalacion', 'destacada': True,
    },
    '114275a4-WhatsApp_Image_20250915_at_1.46.04_PM_7.jpeg': {
        'slug': 'instalacion-cassette-oficina-malaga-01',
        'alt': 'Instalación de aire acondicionado tipo cassette en el cielorraso de una oficina, Málaga',
        'zona': 'malaga', 'tipo': 'conductos', 'destacada': True,
    },
    '98d87089-WhatsApp_Image_20250811_at_12.37.45_PM.jpeg': {
        'slug': 'instalacion-cassette-oficina-malaga-02',
        'alt': 'Montaje de unidad interior tipo cassette con elevador de carga en una oficina, Málaga',
        'zona': 'malaga', 'tipo': 'conductos', 'destacada': True,
    },
    '0c6e5653-WhatsApp_Image_20250915_at_1.46.04_PM_6.jpeg': {
        'slug': 'mantenimiento-split-oficina-malaga-01',
        'alt': 'Service y mantenimiento de un split mural en una oficina por técnico de Clima Baires, Málaga',
        'zona': 'malaga', 'tipo': 'mantenimiento', 'destacada': True,
    },
    '39aa3365-WhatsApp_Image_20250915_at_1.46.04_PM.jpeg': {
        'slug': 'equipo-obra-local-comercial-malaga-01',
        'alt': 'Técnico de Clima Baires preparando el acceso para climatizar un local comercial, Málaga',
        'zona': 'malaga', 'tipo': 'equipo', 'destacada': True,
    },
    '6e0aee55-WhatsApp_Image_20250915_at_1.46.04_PM_1.jpeg': {
        'slug': 'equipo-llegada-obra-malaga-01',
        'alt': 'El equipo de Clima Baires llegando a una obra con escaleras y herramientas, Málaga',
        'zona': 'malaga', 'tipo': 'equipo', 'destacada': False,
    },
}

# Foto que alimenta el hero de la portada y los og:image (la mejor toma).
HERO_ORIGEN = 'e8bd4a26-WhatsApp_Image_20250915_at_1.46.04_PM_4.jpeg'
# Ventana de recorte del hero, en fracciones (izq, arriba, der, abajo) sobre
# la foto ya orientada: banda con condensadoras + técnico + skyline.
HERO_VENTANA = (0.0, 0.20, 1.0, 0.66)

# Originales inutilizables: archivo → motivo. Se mueven a descartadas/.
DESCARTES = {}

EXTENSIONES = ('.jpg', '.jpeg', '.png', '.webp')


def abrir_orientada(ruta):
    im = Image.open(ruta)
    im = ImageOps.exif_transpose(im)  # aplica la orientación EXIF a los píxeles
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    return im


def escalar(im, lado_max):
    w, h = im.size
    lado = max(w, h)
    if lado <= lado_max:
        return im.copy()
    factor = lado_max / lado
    return im.resize((round(w * factor), round(h * factor)), Image.LANCZOS)


def guardar_webp(im, ruta):
    # sin parámetro exif → los metadatos del original no viajan al derivado
    im.save(ruta, 'WEBP', quality=CALIDAD_WEBP, method=6)
    peso = os.path.getsize(ruta)
    if peso > PESO_MAX:
        im.save(ruta, 'WEBP', quality=65, method=6)
        peso = os.path.getsize(ruta)
    return peso


def recorte_proporcional(im, ventana, relacion):
    """Recorta la ventana fraccional y la ajusta a la relación ancho/alto."""
    w, h = im.size
    x0, y0, x1, y1 = (round(ventana[0] * w), round(ventana[1] * h),
                      round(ventana[2] * w), round(ventana[3] * h))
    caja = im.crop((x0, y0, x1, y1))
    cw, ch = caja.size
    objetivo = cw / relacion
    if objetivo <= ch:            # sobra alto: centrar verticalmente
        extra = (ch - objetivo) / 2
        caja = caja.crop((0, round(extra), cw, round(ch - extra)))
    else:                         # sobra ancho: centrar horizontalmente
        objetivo_w = ch * relacion
        extra = (cw - objetivo_w) / 2
        caja = caja.crop((round(extra), 0, round(cw - extra), ch))
    return caja


def necesita_rehacer(origen, destinos, force):
    if force:
        return True
    mt = os.path.getmtime(origen)
    return any(not os.path.exists(d) or os.path.getmtime(d) < mt for d in destinos)


def main():
    force = '--force' in sys.argv
    if not os.path.isdir(ORIGINALES):
        print(f'No existe {ORIGINALES}; nada que procesar.')
        return
    os.makedirs(OBRAS, exist_ok=True)

    originales = sorted(
        f for f in os.listdir(ORIGINALES)
        if f.lower().endswith(EXTENSIONES) and os.path.isfile(os.path.join(ORIGINALES, f))
    )

    # 1. descartes explícitos
    for archivo, motivo in DESCARTES.items():
        ruta = os.path.join(ORIGINALES, archivo)
        if os.path.exists(ruta):
            os.makedirs(DESCARTADAS, exist_ok=True)
            os.replace(ruta, os.path.join(DESCARTADAS, archivo))
            with open(os.path.join(DESCARTADAS, 'motivos.txt'), 'a', encoding='utf-8') as f:
                f.write(f'{archivo}: {motivo}\n')
            print(f'  ✗ descartada {archivo} ({motivo})')

    indice, pendientes, procesadas = [], [], 0
    peso_original = peso_final = 0

    # 2. derivados por foto (el orden de MAPEO define la galería)
    for archivo, meta in MAPEO.items():
        ruta = os.path.join(ORIGINALES, archivo)
        if not os.path.exists(ruta):
            print(f'  ⚠ falta el original {archivo} (se omite)')
            continue
        assert meta['zona'] in ZONAS, f'zona desconocida en {archivo}: {meta["zona"]}'
        assert meta['tipo'] in TIPOS, f'tipo desconocido en {archivo}: {meta["tipo"]}'
        slug = meta['slug']
        destinos = [os.path.join(OBRAS, f'{slug}-{t}.webp') for t in TAMANOS]
        entrada = dict(meta)
        if necesita_rehacer(ruta, destinos, force):
            im = abrir_orientada(ruta)
            for lado, destino in zip(TAMANOS, destinos):
                der = escalar(im, lado)
                peso = guardar_webp(der, destino)
                entrada[f'w{lado}'], entrada[f'h{lado}'] = der.size
                print(f'  ✓ {os.path.basename(destino)} {der.size[0]}×{der.size[1]} · {peso // 1024} KB')
            procesadas += 1
        else:
            for lado, destino in zip(TAMANOS, destinos):
                with Image.open(destino) as der:
                    entrada[f'w{lado}'], entrada[f'h{lado}'] = der.size
        peso_original += os.path.getsize(ruta)
        peso_final += sum(os.path.getsize(d) for d in destinos)
        indice.append(entrada)

    # 3. hero + og (desde la mejor foto)
    ruta_hero = os.path.join(ORIGINALES, HERO_ORIGEN)
    if os.path.exists(ruta_hero):
        destinos_hero = [os.path.join(OBRAS, f'hero-home-{t}.webp') for t in TAMANOS]
        destinos_og = [os.path.join(OBRAS, 'og-home.jpg'), os.path.join(OBRAS, 'og-obras.jpg')]
        if necesita_rehacer(ruta_hero, destinos_hero + destinos_og, force):
            im = abrir_orientada(ruta_hero)
            banda = recorte_proporcional(im, HERO_VENTANA, 16 / 9)
            for lado, destino in zip(TAMANOS, destinos_hero):
                der = escalar(banda, lado)
                peso = guardar_webp(der, destino)
                print(f'  ✓ {os.path.basename(destino)} {der.size[0]}×{der.size[1]} · {peso // 1024} KB')
            og = recorte_proporcional(im, HERO_VENTANA, 1200 / 630).resize((1200, 630), Image.LANCZOS)
            for destino in destinos_og:
                og.save(destino, 'JPEG', quality=CALIDAD_JPG, optimize=True)
                print(f'  ✓ {os.path.basename(destino)} 1200×630 · {os.path.getsize(destino) // 1024} KB')

    # 4. índice para el generador
    with open(INDICE, 'w', encoding='utf-8') as f:
        json.dump({'zonas': ZONAS, 'tipos': TIPOS, 'fotos': indice}, f, ensure_ascii=False, indent=2)
    print(f'  ✓ index.json ({len(indice)} fotos publicadas)')

    # 5. originales sin clasificar → pedir descripción, no inventar
    conocidos = set(MAPEO) | set(DESCARTES)
    pendientes = [f for f in originales if f not in conocidos]
    if pendientes:
        print('\nPENDIENTES de descripción (añadir a MAPEO en tools/fotos.py):')
        for f in pendientes:
            print(f'  ? {f}')

    print(f'\nResumen: {procesadas} fotos (re)procesadas · '
          f'original {peso_original // 1024} KB → publicado {peso_final // 1024} KB')


if __name__ == '__main__':
    main()
