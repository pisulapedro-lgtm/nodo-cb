# -*- coding: utf-8 -*-
"""Pipeline de fotos de obras de climabaires.es.
Uso: python3 web-es/tools/fotos.py [--force]

Lee originales de web-es/assets/img/originales/, corrige la orientación EXIF,
elimina los metadatos (privacidad: hay domicilios de clientes) y exporta a
web-es/assets/img/obras/ en WebP calidad 80, en dos tamaños:
  {slug}-1600.webp  → lado mayor máx. 1600 px (lightbox / hero)
  {slug}-800.webp   → lado mayor máx. 800 px (tarjetas / rejillas)
Además genera:
  hero-card-{1600,800}.webp  → recorte 4:5 de la foto HERO para la portada
  og-home.jpg / og-obras.jpg → 1200×630 para Open Graph (JPEG: WhatsApp y
                               Facebook no siempre renderizan WebP en la vista previa)
  index.json                 → índice que consume tools/generar.py

Es idempotente: si los derivados existen y el original no ha cambiado, no rehace
nada (ejecutarlo dos veces no duplica). --force regenera todo.

LA ZONA ES OBLIGATORIA, y esta es la diferencia de fondo con el sitio argentino.
Allí la empresa todavía no tiene obras hechas, así que las fotos van con pie
técnico y sin ciudad. Aquí las obras son reales y locales: decir dónde se hizo
cada una es media venta y es lo que posiciona las páginas de zona. Una foto sin
`zona` se publica igual —no se rompe nada— pero sale listada como pendiente al
final de cada ejecución y publicar.py no deja compilar el paquete hasta que
todas la tengan. Lo que NO se hace nunca es inventarla.

Cómo añadir fotos nuevas: copiar los originales a originales/ y añadir una
entrada en MAPEO (slug descriptivo en kebab-case, alt de lo que se ve, zona,
tipo, destacada). Un original sin entrada en MAPEO no se publica: el script lo
lista al final para que alguien lo describa. Fotos inservibles: entrada en
DESCARTES con el motivo → se mueven a originales/descartadas/.

Pares antes/después: usar el campo "par" con el mismo identificador en las dos
fotos y tipo "antes-despues"; el slug debe empezar por "antes-" o "despues-".
El generador arma el bloque comparativo solo.
"""
import json
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
ORIGINALES = os.path.join(RAIZ, 'assets', 'img', 'originales')
DESCARTADAS = os.path.join(ORIGINALES, 'descartadas')
OBRAS = os.path.join(RAIZ, 'assets', 'img', 'obras')
INDICE = os.path.join(OBRAS, 'index.json')

CALIDAD_WEBP = 80
CALIDAD_JPG = 82
TAMANOS = (1600, 800)          # lado mayor máximo de cada derivado
PESO_MAX = 350 * 1024          # ninguna imagen publicada puede superar 350 KB

# Zonas válidas (slug → etiqueta visible). Son las mismas seis que las páginas de
# zona de tools/generar.py: si aquí aparece una que allí no existe, la galería
# genera un filtro que no lleva a ninguna landing.
ZONAS = {
    'malaga-capital': 'Málaga capital', 'marbella': 'Marbella',
    'torremolinos': 'Torremolinos', 'benalmadena': 'Benalmádena',
    'fuengirola': 'Fuengirola', 'mijas': 'Mijas',
}
TIPOS = {
    'instalacion': 'Instalación', 'sustitucion': 'Sustitución', 'mantenimiento': 'Mantenimiento',
    'suelo-techo': 'Suelo-techo', 'conductos': 'Cassette y conductos',
    'antes-despues': 'Antes / después', 'equipo': 'Equipo en obra',
}

# ---------------------------------------------------------------------------
# MAPEO: archivo original → foto publicada. El orden define la galería.
# alt: describe lo que se ve, sin relleno de palabras clave.
# zona: municipio real donde se hizo el trabajo. Vacío = todavía sin confirmar.
# ---------------------------------------------------------------------------
# Originales que a propósito NO se publican, con el motivo. Sin esta lista el
# script los reporta como «pendientes de descripción» en cada ejecución.
EXCLUIDAS = {}

MAPEO = {
    '38429ddc-a593b1865ff44481b16de2d161cd2227.jpeg': {
        'slug': 'instalacion-unidad-exterior-fachada-01',
        'alt': 'Instalación de una unidad exterior en fachada desde plataforma elevadora: trabajo en altura con equipos de protección',
        'zona': '', 'tipo': 'instalacion', 'destacada': True,
    },
    'e8bd4a26-WhatsApp_Image_20250915_at_1.46.04_PM_4.jpeg': {
        'slug': 'instalacion-unidad-exterior-azotea-01',
        'alt': 'Técnico de Clima Baires montando una unidad exterior inverter en la azotea de un edificio, sobre los tejados de la ciudad',
        'zona': '', 'tipo': 'instalacion', 'destacada': True,
    },
    '3be9b340-e023e88fa3c54f3c8826498dc8860a7d.jpeg': {
        'slug': 'puesta-en-marcha-unidad-exterior-comercial-01',
        'alt': 'Puesta en marcha de una unidad exterior comercial: control de presiones con manómetros antes de entregar el equipo',
        'zona': '', 'tipo': 'instalacion', 'destacada': True,
    },
    '114275a4-WhatsApp_Image_20250915_at_1.46.04_PM_7.jpeg': {
        'slug': 'instalacion-cassette-oficina-01',
        'alt': 'Instalación de un aire acondicionado tipo cassette en el falso techo de una oficina',
        'zona': '', 'tipo': 'conductos', 'destacada': True,
    },
    '98d87089-WhatsApp_Image_20250811_at_12.37.45_PM.jpeg': {
        'slug': 'instalacion-cassette-oficina-02',
        'alt': 'Montaje de una unidad interior tipo cassette con elevador de carga en una oficina',
        'zona': '', 'tipo': 'conductos', 'destacada': False,
    },
    '0c6e5653-WhatsApp_Image_20250915_at_1.46.04_PM_6.jpeg': {
        'slug': 'mantenimiento-split-oficina-01',
        'alt': 'Mantenimiento de un split de pared en una oficina, por un técnico de Clima Baires',
        'zona': '', 'tipo': 'mantenimiento', 'destacada': True,
    },
    '40a8ec06-IMG_1684.jpeg': {
        'slug': 'nave-flota-stock-01',
        'alt': 'La nave de Clima Baires: furgonetas rotuladas y stock de equipos listos para instalar',
        'zona': '', 'tipo': 'equipo', 'destacada': True,
    },
    '57977141-IMG_1666.jpeg': {
        'slug': 'nave-furgoneta-rotulada-01',
        'alt': 'Furgoneta rotulada de Clima Baires en la nave, junto al stock de equipos de aire acondicionado',
        'zona': '', 'tipo': 'equipo', 'destacada': False,
    },
    '39aa3365-WhatsApp_Image_20250915_at_1.46.04_PM.jpeg': {
        'slug': 'equipo-obra-local-comercial-01',
        'alt': 'Técnico de Clima Baires preparando el acceso para climatizar un local comercial',
        'zona': '', 'tipo': 'equipo', 'destacada': False,
    },
    '6e0aee55-WhatsApp_Image_20250915_at_1.46.04_PM_1.jpeg': {
        'slug': 'equipo-llegada-obra-01',
        'alt': 'El equipo de Clima Baires llegando a una obra con escaleras y herramientas',
        'zona': '', 'tipo': 'equipo', 'destacada': False,
    },
}

# ---------------------------------------------------------------------------
# MEJORAS: edición fotográfica por archivo, aplicada antes de los derivados.
# crop = ventana (izq, arriba, der, abajo) en fracciones de la foto ya orientada:
# acerca el sujeto y saca cielo muerto, carteles ajenos y zonas vacías.
# Los demás campos ajustan el revelado; si faltan, se usan los valores base.
# ---------------------------------------------------------------------------
MEJORAS_BASE = {'cutoff': 1, 'color': 1.10, 'contraste': 1.05, 'brillo': 1.0}
MEJORAS = {
    # fachada con plataforma: se recorta el velo de sol del ángulo superior y,
    # abajo, el teléfono rotulado en la plataforma elevadora. Ese número no es
    # nuestro, es de la empresa que la alquila: publicar el teléfono de un
    # tercero en nuestra galería no procede, aquí ni en ningún país.
    '38429ddc-a593b1865ff44481b16de2d161cd2227.jpeg': {
        'crop': (0.05, 0.15, 1.0, 0.545), 'cutoff': 2, 'contraste': 1.10,
    },
    # azotea: se recorta algo de cielo por arriba y el borde inferior con la
    # herramienta suelta, para dejar al técnico, el equipo y los tejados
    'e8bd4a26-WhatsApp_Image_20250915_at_1.46.04_PM_4.jpeg': {
        'crop': (0.0, 0.05, 1.0, 0.88), 'contraste': 1.08, 'color': 1.08,
    },
    # cassette abierto: fuera el desorden de oficina del borde inferior
    '114275a4-WhatsApp_Image_20250915_at_1.46.04_PM_7.jpeg': {
        'crop': (0.05, 0.0, 1.0, 0.88), 'brillo': 1.03, 'color': 1.08,
    },
    # elevador de carga: quitar la escalera del borde izquierdo
    '98d87089-WhatsApp_Image_20250811_at_12.37.45_PM.jpeg': {
        'crop': (0.12, 0.02, 0.95, 0.98), 'brillo': 1.03, 'color': 1.08,
    },
    # split de pared: acercar técnico y equipo, menos falso techo vacío
    '0c6e5653-WhatsApp_Image_20250915_at_1.46.04_PM_6.jpeg': {
        'crop': (0.0, 0.15, 0.88, 0.92), 'brillo': 1.03, 'color': 1.08,
    },
    # escalera en local: menos rótulo del comercio, foco en el técnico
    '39aa3365-WhatsApp_Image_20250915_at_1.46.04_PM.jpeg': {
        'crop': (0.05, 0.18, 0.95, 1.0),
    },
    # equipo llegando a obra: foco en la camiseta de Clima Baires
    '6e0aee55-WhatsApp_Image_20250915_at_1.46.04_PM_1.jpeg': {
        'crop': (0.30, 0.25, 1.0, 0.95),
    },
    # nave con flota y stock: menos techo y menos suelo vacío
    '40a8ec06-IMG_1684.jpeg': {
        'crop': (0.0, 0.08, 1.0, 0.90), 'brillo': 1.05, 'color': 1.08,
    },
    # frente de la furgoneta en la nave: aquí entra entera, matrícula incluida.
    # En el sitio argentino se cortaba justo antes porque el formato de matrícula
    # delataba el origen; en el sitio español es nuestro vehículo rotulado en
    # nuestra nave, y verlo completo suma en vez de restar.
    '57977141-IMG_1666.jpeg': {
        'crop': (0.0, 0.04, 0.96, 0.94), 'brillo': 1.05, 'color': 1.08,
    },
    # puesta en marcha comercial: menos cielo lavado, foco en técnico y manómetros
    '3be9b340-e023e88fa3c54f3c8826498dc8860a7d.jpeg': {
        'crop': (0.02, 0.08, 1.0, 0.96), 'contraste': 1.08,
    },
}

# Foto que alimenta el hero de la portada y los og:image (la mejor toma).
HERO_ORIGEN = '40a8ec06-IMG_1684.jpeg'
# Ventanas de recorte (izq, arriba, der, abajo) sobre la foto YA MEJORADA:
# tarjeta vertical 4:5 del hero (furgoneta rotulada + rótulo) y banda og 1200×630.
HERO_VENTANA_TARJETA = (0.16, 0.0, 1.0, 1.0)
HERO_VENTANA_OG = (0.0, 0.28, 1.0, 0.78)

# Originales inservibles: archivo → motivo. Se mueven a descartadas/.
DESCARTES = {}

EXTENSIONES = ('.jpg', '.jpeg', '.png', '.webp')

# Derivados que no salen de MAPEO y que la limpieza no debe tocar.
FIJOS = {'hero-card-1600.webp', 'hero-card-800.webp', 'og-home.jpg', 'og-obras.jpg', 'index.json'}


def abrir_orientada(ruta):
    im = Image.open(ruta)
    im = ImageOps.exif_transpose(im)  # aplica la orientación EXIF a los píxeles
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    return im


def mejorar(im, archivo):
    """Revelado: recorte de encuadre + niveles + color + contraste por foto."""
    cfg = dict(MEJORAS_BASE)
    cfg.update(MEJORAS.get(archivo, {}))
    if 'crop' in cfg:
        w, h = im.size
        l, t, r, b = cfg['crop']
        im = im.crop((round(l * w), round(t * h), round(r * w), round(b * h)))
    im = ImageOps.autocontrast(im, cutoff=cfg['cutoff'], preserve_tone=True)
    im = ImageEnhance.Color(im).enhance(cfg['color'])
    im = ImageEnhance.Contrast(im).enhance(cfg['contraste'])
    if cfg['brillo'] != 1.0:
        im = ImageEnhance.Brightness(im).enhance(cfg['brillo'])
    return im


def escalar(im, lado_max):
    """Redimensiona al lado mayor pedido y devuelve nítido (unsharp post-resize)."""
    w, h = im.size
    lado = max(w, h)
    if lado > lado_max:
        factor = lado_max / lado
        im = im.resize((round(w * factor), round(h * factor)), Image.LANCZOS)
    else:
        im = im.copy()
    # la nitidez se aplica al tamaño final: realza sin halos visibles
    percent = 90 if lado_max <= 800 else 70
    return im.filter(ImageFilter.UnsharpMask(radius=1.8, percent=percent, threshold=3))


def guardar_webp(im, ruta):
    # sin parámetro exif → los metadatos del original no viajan al derivado;
    # si pesa de más, baja la calidad por escalones hasta cumplir el tope
    for calidad in (CALIDAD_WEBP, 70, 62, 55, 48):
        im.save(ruta, 'WEBP', quality=calidad, method=6)
        peso = os.path.getsize(ruta)
        if peso <= PESO_MAX:
            break
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
    """La receta (recortes, brillo, alt) vive en este archivo, así que también
    cuenta como fuente: si sólo se mira la foto original, cambiar un recorte y
    volver a ejecutar no hace nada y uno se queda mirando la versión antigua
    creyendo que el cambio no funcionó."""
    if force:
        return True
    mt = max(os.path.getmtime(origen), os.path.getmtime(os.path.abspath(__file__)))
    return any(not os.path.exists(d) or os.path.getmtime(d) < mt for d in destinos)


def limpiar_huerfanos(slugs):
    """Borra derivados de slugs que ya no existen. Al renombrar una foto, el
    archivo antiguo se queda en disco, entra en el paquete de publicación y sigue
    accesible por URL. Con el cambio de nombres al pasar al sitio español esto no
    es hipotético: pasa en la primera ejecución."""
    vivos = {f'{s}-{t}.webp' for s in slugs for t in TAMANOS} | FIJOS
    for archivo in sorted(os.listdir(OBRAS)):
        if archivo not in vivos and archivo.endswith(('.webp', '.jpg')):
            os.remove(os.path.join(OBRAS, archivo))
            print(f'  ✗ {archivo} (derivado huérfano)')


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

    indice, procesadas = [], 0
    peso_original = peso_final = 0

    # 2. derivados por foto (el orden de MAPEO define la galería)
    for archivo, meta in MAPEO.items():
        ruta = os.path.join(ORIGINALES, archivo)
        if not os.path.exists(ruta):
            print(f'  ⚠ falta el original {archivo} (se omite)')
            continue
        assert not meta['zona'] or meta['zona'] in ZONAS, \
            f'zona desconocida en {archivo}: {meta["zona"]}'
        assert meta['tipo'] in TIPOS, f'tipo desconocido en {archivo}: {meta["tipo"]}'
        slug = meta['slug']
        destinos = [os.path.join(OBRAS, f'{slug}-{t}.webp') for t in TAMANOS]
        entrada = dict(meta)
        if necesita_rehacer(ruta, destinos, force):
            im = mejorar(abrir_orientada(ruta), archivo)
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
        destinos_hero = [os.path.join(OBRAS, f'hero-card-{t}.webp') for t in TAMANOS]
        destinos_og = [os.path.join(OBRAS, 'og-home.jpg'), os.path.join(OBRAS, 'og-obras.jpg')]
        if necesita_rehacer(ruta_hero, destinos_hero + destinos_og, force):
            im = mejorar(abrir_orientada(ruta_hero), HERO_ORIGEN)
            tarjeta = recorte_proporcional(im, HERO_VENTANA_TARJETA, 4 / 5)
            for lado, destino in zip(TAMANOS, destinos_hero):
                der = escalar(tarjeta, lado)
                peso = guardar_webp(der, destino)
                print(f'  ✓ {os.path.basename(destino)} {der.size[0]}×{der.size[1]} · {peso // 1024} KB')
            og = recorte_proporcional(im, HERO_VENTANA_OG, 1200 / 630).resize((1200, 630), Image.LANCZOS)
            for destino in destinos_og:
                og.save(destino, 'JPEG', quality=CALIDAD_JPG, optimize=True)
                print(f'  ✓ {os.path.basename(destino)} 1200×630 · {os.path.getsize(destino) // 1024} KB')

    # 4. limpieza de derivados que ya no corresponden a ninguna entrada
    limpiar_huerfanos([m['slug'] for m in MAPEO.values()])

    # 5. índice para el generador
    with open(INDICE, 'w', encoding='utf-8') as f:
        json.dump({'zonas': ZONAS, 'tipos': TIPOS, 'fotos': indice}, f, ensure_ascii=False, indent=2)
    print(f'  ✓ index.json ({len(indice)} fotos publicadas)')

    # 6. originales sin clasificar → pedir descripción, no inventar
    conocidos = set(MAPEO) | set(DESCARTES) | set(EXCLUIDAS)
    pendientes = [f for f in originales if f not in conocidos]
    if pendientes:
        print('\nPENDIENTES de descripción (añadir a MAPEO en tools/fotos.py):')
        for f in pendientes:
            print(f'  ? {f}')

    # 7. fotos sin zona: aquí la ubicación es contenido, no un dato opcional
    sin_zona = [e['slug'] for e in indice if not e.get('zona')]
    if sin_zona:
        print('\nPENDIENTES de zona (el municipio real donde se hizo el trabajo).')
        print('Sin ella la galería no muestra el filtro por zona y el pie de foto')
        print('pierde el dato que más vende. Zonas válidas: %s' % ', '.join(sorted(ZONAS)))
        for s in sin_zona:
            print(f'  ? {s}')

    print(f'\nResumen: {procesadas} fotos (re)procesadas · '
          f'original {peso_original // 1024} KB → publicado {peso_final // 1024} KB')


if __name__ == '__main__':
    main()
