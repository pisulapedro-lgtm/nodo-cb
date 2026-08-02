# -*- coding: utf-8 -*-
"""Revisa una entrada del blog antes de que se publique sola.

La rutina automática escribe sin que nadie mire, así que este script es el
control: si algo no pasa, el generador no corre y no se sube nada.

    python3 web-es/tools/revisar-nota.py                     revisa todas
    python3 web-es/tools/revisar-nota.py 01-aerotermia.md    revisa una

Códigos de salida: 0 todo bien · 1 hay errores.

Distingue **errores** (bloquean la publicación: promesas falsas, español
rioplatense, enlaces rotos, front-matter mal) de **avisos** (se imprimen y
siguen: longitud fuera de lo ideal, pocos subtítulos). La lista de
prohibiciones sale de web-es/contenido/estilo-blog.md; si cambias las reglas
allí, actualiza aquí.

Este archivo es el espejo del de web/ (el sitio argentino), y las diferencias
son deliberadas:

  · Allí se bloquea el castellano de España; aquí se bloquea el rioplatense.
  · Allí se bloquea cualquier trabajo local, porque todavía no hay obras hechas.
    Aquí NO: la empresa lleva años trabajando en la Costa del Sol y contar cómo
    se resuelve un caso en la zona es la mitad del valor del blog. Lo que sigue
    prohibido es inventarse un caso concreto que nadie pueda señalar.
  · Allí se bloquea mencionar España; aquí se bloquea mencionar Argentina y
    Buenos Aires. Son dos marcas separadas.
  · Lo que NO cambia: magnitudes inventadas, precios, superlativos sin respaldo y
    promesas que la empresa no puede cumplir. Que el negocio tenga historia no
    autoriza a inventar cifras.
"""
import os
import re
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
BLOG = os.path.join(RAIZ, 'contenido', 'blog')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog as _blog  # noqa: E402  (necesita el sys.path de arriba)

# Español rioplatense: el sitio entero está en castellano de España y el
# contraste canta. Es la lista ESPANOLISMOS del sitio argentino, del revés.
ARGENTINISMOS = [
    # --- voseo, que es lo que más se cuela ---
    (r'\bvos\b', 'vos → tú'),
    (r'\b(?:tenés|podés|querés|debés|sabés|hacés|ponés|vivís|escribís|venís|salís|'
     r'elegís|preferís|decís|seguís|necesitás|comprás|usás|mirás|contás|buscás|'
     r'pagás|llamás|dejás|instalás|cambiás|pedís|abrís|medís)\b',
     'voseo → tuteo peninsular (tienes, puedes, quieres, necesitas…)'),
    (r'\b(?:fijate|mirá|contanos|escribinos|llamanos|avisanos|consultanos|pedí|poné|'
     r'mandá|dejá|elegí|revisá|sumá|agregá|andá|tocá|probá|acordate|quedate|fijate)\b',
     'imperativo voseante → fíjate, mira, cuéntanos, escríbenos, pide, pon…'),
    # --- léxico ---
    (r'\bacá\b', 'acá → aquí'),
    (r'\bcamionet\w*', 'camioneta → furgoneta'),
    (r'\bdepósitos?\b(?!\s+de\s+(?:agua|garantía|inercia|combustible|gasoil))',
     'depósito (almacén) → nave'),
    (r'\bcañerí\w*', 'cañería → tubería'),
    (r'\bcaños?\b', 'caño → tubo'),
    (r'\bplomer\w+', 'plomero → fontanero'),
    (r'\btarugos?\b', 'tarugo → taco'),
    (r'\bcomputadora\w*', 'computadora → ordenador'),
    (r'\bcelulares?\b', 'celular → móvil'),
    (r'\bheladeras?\b', 'heladera → nevera'),
    (r'\bliving\b', 'living → salón'),
    (r'\bdepartamentos?\b', 'departamento → piso'),
    (r'\bveredas?\b', 'vereda → acera'),
    (r'\bcuadras?\b', 'cuadra → manzana'),
    (r'\bcountr(?:y|ies)\b|\bbarrios? cerrados?\b', 'country / barrio cerrado → urbanización'),
    (r'\bpatentes?\b(?!\s+de\s+invención)', 'patente (del vehículo) → matrícula'),
    (r'\bservice\b', 'service → mantenimiento / servicio técnico'),
    (r'\bprend(?:er|és|e|iste)\b', 'prender → encender'),
    (r'\bandando\b', '«te lo dejamos andando» → funcionando'),
    (r'\bplata\b(?!\s+(?:de ley|coloidal))', 'plata (dinero) → dinero'),
    (r'\bambientes?\b(?=\s+(?:de\s+\d|chico|grande|integrado))', 'ambiente (habitación) → estancia'),
    (r'\bchic[oa]s?\b', 'chico (pequeño) → pequeño'),
    (r'\bpiletas?\b', 'pileta → piscina'),
    (r'\bplacard\w*', 'placard → armario'),
    (r'\bautos?\b(?!\s*-)', 'auto → coche'),
    (r'\bboletas?\b', 'boleta → factura'),
    (r'\blind[oa]s?\b', 'lindo → bonito'),
    (r'\bamoblad\w+', 'amoblado → amueblado'),
    (r'\bfrigorías?\b(?=\s+por\s+ambiente)', 'frigorías por ambiente → por estancia'),
]

# Cosas que el negocio no puede afirmar, o que no tocan en este sitio.
PROMESAS = [
    # las dos marcas están separadas: este sitio es 100 % Costa del Sol
    (r'\bargentin\w+|\bbuenos aires\b|\bamba\b|\brioplatens\w+|\bnordelta\b|'
     r'\bvicente lópez\b|\bsan isidro\b|\bcaba\b',
     'el sitio español no menciona Argentina ni Buenos Aires: son dos marcas separadas'),
    (r'garantía\s+de\s+\d+\s*(?:año|mes)', 'plazo de garantía sin confirmar'),
    (r'\bcertificad\w+\s+(?:por|en)\s+\w',
     'certificación o sello sin confirmar: el sitio no exhibe ninguno'),
    (r'€\s?\d|\b\d+\s*€|\b\d+\s*euros?\b|\bpesos\b|\bAR\$|\$\s?\d',
     'importe: se desactualiza en un mes y queda como mentira'),
    # las ayudas cambian en cada convocatoria: ni importes, ni porcentajes, ni plazos
    (r'(?:subvención|subvenciones|ayudas?|deducci\w+|bonificaci\w+)[^.]{0,80}?\d',
     'cifra dentro de una ayuda pública: cambia en cada convocatoria'),
    (r'\baerotermia\b', 'la empresa no instala aerotermia: no se ofrece ni se menciona como alternativa'),
    (r'respondemos\s+(?:siempre|24|las 24)', 'disponibilidad fuera del horario real'),
    (r'\bel mejor\b|\blíder\w*\s+(?:del|en)\b|\bnúmero uno\b', 'superlativo no demostrable'),
    # magnitudes de mercado puestas para sonar concreto: nadie las midió
    (r'\b(?:cientos|decenas|miles)\s+de\b', 'magnitud inventada: si no la hemos medido, descríbela sin número'),
    (r'\b\d+\s*%', 'porcentaje sin fuente'),
]

# No bloquean, pero casi siempre son una afirmación que nadie ha verificado.
SOSPECHAS = [
    (r'\bla mayoría de\b', '«la mayoría de» sin fuente: ¿lo sabemos o lo suponemos?'),
    (r'\bmás vendid\w+|\bmás elegid\w+|\bmás pedid\w+', 'ranking de mercado sin fuente'),
    (r'\btodo el mundo\b|\bnadie\b\s+\w+\s+\bnunca\b', 'generalización absoluta'),
    (r'\bes sabido\b|\bno es (?:un )?secreto\b|\bcomo todos saben\b', 'muletilla de relleno'),
    (r'\bdura\w*\s+\d+\s*años\b', 'vida útil con número: comprueba que sea del fabricante y no nuestra'),
    (r'\bustedes\b', '«ustedes» → en este sitio se tutea; si es plural, «vosotros»'),
    # aquí SÍ se puede hablar de obra local, pero si se nombra una obra concreta
    # tiene que existir y alguien de la empresa tiene que poder señalarla
    (r'(?:instalamos|montamos|sustituimos|cambiamos|estuvimos|hicimos)\s+(?:\w+\s+){0,4}'
     r'(?:en|para)\s+(?:Málaga|Marbella|Torremolinos|Benalmádena|Fuengirola|Mijas|Estepona|'
     r'La Carihuela|Nueva Andalucía|Calahonda|Los Boliches)',
     'obra local concreta: se puede contar si ocurrió de verdad y alguien puede señalarla; si no, describe el mecanismo sin la anécdota'),
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
        avisos.append('el título empieza por la marca: se come caracteres útiles')

    # --- prohibiciones ---
    # El Markdown viene con las líneas cortadas, así que una frase prohibida
    # puede quedar partida por la mitad («…es la\nmayoría de…») y esquivar el
    # patrón sin que nadie se entere. Se aplasta todo el espacio en blanco antes
    # de buscar: si no, media lista de reglas de aquí arriba es decorativa.
    plano = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cuerpo)
    plano = re.sub(r'\s+', ' ', plano)
    def marcar(reglas, destino):
        for patron, motivo in reglas:
            for m in re.finditer(patron, plano, re.IGNORECASE):
                ctx = plano[max(0, m.start() - 40):m.end() + 40].replace('\n', ' ')
                destino.append(f'{motivo} → «…{ctx.strip()}…»')
    marcar(ARGENTINISMOS + PROMESAS, errores)
    marcar(SOSPECHAS, avisos)

    # --- enlaces ---
    enlaces = re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', cuerpo)
    internos = [u for _, u in enlaces if not u.startswith(('http://', 'https://'))]
    for t, u in enlaces:
        if u.startswith(('http://', 'https://')):
            errores.append(f'enlace externo a {u}: la guía no los permite')
        elif u.split('#')[0] not in _rutas():
            errores.append(f'enlace roto: {u} no existe en el sitio')
        if t.strip().lower() in ('aquí', 'acá', 'clic', 'este enlace', 'ver más'):
            avisos.append(f'texto de enlace poco descriptivo: «{t}»')
    if len(internos) < 2:
        errores.append(f'{len(internos)} enlaces internos (mínimo 2): la entrada queda aislada del sitio')

    # --- forma ---
    palabras = len(re.sub(r'[#*>\[\]()|-]', ' ', cuerpo).split())
    if palabras < 600:
        errores.append(f'{palabras} palabras: por debajo de 600 la entrada no aporta nada')
    elif palabras > 1400:
        avisos.append(f'{palabras} palabras: por encima de 1.400 no se lee entera')
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
        avisos.append('parece haber HTML crudo: el conversor lo va a escapar y se va a ver la etiqueta')

    return errores, avisos


def main():
    if not os.path.isdir(BLOG):
        print('No existe contenido/blog: nada que revisar.')
        return 0
    objetivo = sys.argv[1:] or sorted(a for a in os.listdir(BLOG) if a.endswith('.md'))
    if not objetivo:
        print('No hay entradas en contenido/blog todavía: nada que revisar.')
        return 0
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
        print('\nHay errores: corrige la entrada y vuelve a revisar antes de generar el sitio.')
    return 1 if fallo else 0


if __name__ == '__main__':
    sys.exit(main())
