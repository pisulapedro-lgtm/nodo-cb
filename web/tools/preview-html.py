# -*- coding: utf-8 -*-
"""Arma una vista previa navegable de climabaires.com en un solo archivo HTML.

Uso: python3 web/tools/preview-html.py
Salida: dist/preview-climabaires.html

Para qué: el PDF muestra cómo se ve; esto deja *usarlo*. Se abre en el celular,
se toca el botón de WhatsApp, se contestan las cuatro preguntas del asistente,
se filtran las obras, se abre el lightbox. Todo el sitio entra en un archivo
—sin servidor, sin conexión— porque se publica como artifact y ahí no se puede
cargar nada de afuera.

Cómo funciona: cada página se muestra dentro de un iframe con su HTML completo,
el CSS, el JS y las fuentes embebidos. Va en iframe y no inyectado en la página
por dos razones que importan:

  · el JS del sitio corre de cero en cada página, igual que en el sitio real,
    sin tener que re-enganchar nada a mano;
  · las media queries miden el ancho del iframe, así que un marco de 390 px
    rinde el sitio como un celular de verdad, no como un escritorio angosto.

Las imágenes y el CSS viajan una sola vez en el documento padre y se sustituyen
al vuelo al armar cada página, así no se repite el mismo WebP en base64 veinte
veces.
"""
import base64
import io
import json
import os
import re

from PIL import Image

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SALIDA = os.path.normpath(os.path.join(RAIZ, '..', 'dist', 'preview-climabaires.html'))
SALIDA_MOVIL = os.path.normpath(os.path.join(RAIZ, '..', 'dist', 'preview-movil-climabaires.html'))

# Las fotos se recomprimen para la vista previa: a 640 px se ven bien en el marco
# de teléfono y el archivo entero baja de 4 MB a menos de 1.
ANCHO_PREVIEW = 640
CALIDAD_PREVIEW = 70

NOMBRES = {
    'index.html': 'Inicio',
    'servicios.html': 'Servicios',
    'obras.html': 'Obras',
    'calculadora-frigorias.html': 'Calculadora',
    'sobre-nosotros.html': 'Nosotros',
    'contacto.html': 'Contacto',
    'blog/index.html': 'Blog',
    'privacidad.html': 'Privacidad',
    'terminos.html': 'Términos',
    '404.html': 'Página 404',
}
GRUPOS = [
    ('El sitio', ['index.html', 'servicios.html', 'obras.html', 'calculadora-frigorias.html',
                  'sobre-nosotros.html', 'contacto.html']),
    ('Zonas', []),      # se llenan solas más abajo
    ('Blog', []),
    ('Legales', ['privacidad.html', 'terminos.html', '404.html']),
]


def leer(rel):
    with open(os.path.join(RAIZ, rel), encoding='utf-8') as f:
        return f.read()


def b64(datos, mime):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(datos).decode('ascii'))


# ------------------------------------------------------------------ imágenes

def imagenes():
    """Todo lo que el sitio muestra —fotos de obra, logos de marca, el avatar del
    asistente— indexado por su ruta tal como aparece en el HTML. Las fotos de
    obra se achican; los PNG y SVG chicos viajan tal cual."""
    mapa = {}
    base = os.path.join(RAIZ, 'assets', 'img')
    mimes = {'.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
             '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml'}
    for carpeta, _, archivos in os.walk(base):
        if 'originales' in carpeta:
            continue
        for archivo in sorted(archivos):
            ext = os.path.splitext(archivo)[1].lower()
            if ext not in mimes:
                continue
            ruta = os.path.join(carpeta, archivo)
            clave = os.path.relpath(ruta, RAIZ).replace(os.sep, '/')
            if ext == '.webp' and '/obras/' in clave:
                im = Image.open(ruta).convert('RGB')
                if im.width > ANCHO_PREVIEW:
                    im = im.resize((ANCHO_PREVIEW, round(im.height * ANCHO_PREVIEW / im.width)),
                                   Image.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, 'WEBP', quality=CALIDAD_PREVIEW, method=6)
                mapa[clave] = b64(buf.getvalue(), 'image/webp')
            elif ext == '.svg' and os.path.getsize(ruta) > 40000:
                continue          # los logos SVG pesados ya tienen su versión WebP
            else:
                mapa[clave] = b64(open(ruta, 'rb').read(), mimes[ext])
    return mapa


# ------------------------------------------------------------------ css + js

def css_con_fuentes():
    css = leer('assets/css/styles.css')
    for peso in (400, 500, 600, 800):
        ruta = os.path.join(RAIZ, 'assets', 'fonts', f'poppins-{peso}.woff2')
        if os.path.exists(ruta):
            css = css.replace(f"url('../fonts/poppins-{peso}.woff2')",
                              "url('%s')" % b64(open(ruta, 'rb').read(), 'font/woff2'))
    return css


# ------------------------------------------------------------------ páginas

def paginas():
    orden = []
    for archivo in sorted(os.listdir(RAIZ)):
        if archivo.endswith('.html'):
            orden.append(archivo)
    orden += ['zonas/' + f for f in sorted(os.listdir(os.path.join(RAIZ, 'zonas')))]
    orden += ['blog/' + f for f in sorted(os.listdir(os.path.join(RAIZ, 'blog'))) if f.endswith('.html')]

    out = {}
    for rel in orden:
        html = leer(rel)
        profundidad = rel.count('/')
        prefijo = '../' * profundidad

        # el CSS y el JS los inyecta el padre al armar el iframe
        html = re.sub(r'<link rel="stylesheet"[^>]*>', '<!--CSS-->', html)
        html = re.sub(r'<script src="[^"]*main\.js"></script>', '<!--JS-->', html)
        # lo que apunta afuera o a archivos que no viajan
        html = re.sub(r'<link rel="(?:icon|manifest|alternate|preload|apple-touch-icon)"[^>]*>', '', html)

        # rutas de imagen → clave del mapa (se resuelven al armar el iframe)
        def ruta_img(m):
            valor = m.group(2)
            partes = []
            for trozo in valor.split(','):
                trozo = trozo.strip()
                if not trozo:
                    continue
                url, _, descriptor = trozo.partition(' ')
                clave = os.path.normpath(os.path.join(os.path.dirname(rel), url)).replace(os.sep, '/')
                partes.append(('IMG:' + clave + (' ' + descriptor if descriptor else '')).strip())
            return '%s="%s"' % (m.group(1), ', '.join(partes))
        html = re.sub(r'\b(src|srcset)="([^"]*\.(?:webp|jpg|png)[^"]*)"', ruta_img, html)

        # enlaces internos → los intercepta el router del padre
        def enlace(m):
            destino = m.group(1)
            if destino.startswith(('http', 'mailto:', 'tel:', '#')):
                return m.group(0)
            limpio = destino.split('#')[0] or 'index.html'
            if limpio.endswith('/'):
                limpio += 'index.html'
            clave = os.path.normpath(os.path.join(os.path.dirname(rel), limpio)).replace(os.sep, '/')
            ancla = destino.split('#', 1)[1] if '#' in destino else ''
            return 'href="PAGE:%s%s"' % (clave, '#' + ancla if ancla else '')
        html = re.sub(r'href="([^"]+)"', enlace, html)

        out[rel] = html
    return out, prefijo


MAPA_IMG = imagenes()
PAGINAS, _ = paginas()
CSS = css_con_fuentes()
JS = leer('assets/js/main.js')

for rel in PAGINAS:
    if rel.startswith('zonas/'):
        GRUPOS[1][1].append(rel)
    elif rel.startswith('blog/'):
        GRUPOS[2][1].append(rel)
GRUPOS[2][1].sort(key=lambda r: (r != 'blog/index.html', r))


def etiqueta(rel):
    """El nombre del archivo pierde las tildes y no se lee («San isidro»), así que
    la etiqueta sale del <h1> real de la página."""
    if rel in NOMBRES:
        return NOMBRES[rel]
    m = re.search(r'<h1[^>]*>(.*?)</h1>', PAGINAS[rel], re.S)
    if not m:
        base = os.path.basename(rel)[:-5].replace('-', ' ')
        return base[:1].upper() + base[1:]
    texto = re.sub(r'<[^>]+>', '', m.group(1))
    texto = re.sub(r'\s+', ' ', texto).strip()
    if rel.startswith('zonas/'):
        return texto.split(' en ')[-1]            # «Aire acondicionado en Tigre» → Tigre
    return texto if len(texto) <= 36 else texto[:35].rstrip(' ,:') + '…' 


menu = ''.join(
    '<div class="grupo"><p class="grupo-t">%s</p><div class="chips">%s</div></div>' % (
        titulo,
        ''.join('<button class="chip" data-p="%s">%s</button>' % (r, etiqueta(r)) for r in rels))
    for titulo, rels in GRUPOS if rels)

DATOS = json.dumps({'paginas': PAGINAS, 'img': MAPA_IMG}, ensure_ascii=False)

DOC = """<title>climabaires.com — vista previa navegable</title>
<style>
%(css_shell)s
</style>

<header class="barra">
  <div class="marca">
    <img src="%(logo)s" alt="Clima Baires">
    <span>vista previa</span>
  </div>
  <div class="anchos" role="group" aria-label="Ancho de pantalla">
    <button class="ancho activo" data-w="390">Celular</button>
    <button class="ancho" data-w="1280">Escritorio</button>
  </div>
</header>

<nav class="paginas">%(menu)s</nav>

<p class="aviso">Es el sitio real, funcionando. Tocá el botón verde de WhatsApp para probar el asistente de cuatro preguntas. Los números de contacto todavía son de prueba, así que los enlaces a WhatsApp no llevan a ningún chat.</p>

<div class="escena">
  <div class="marco telefono" id="marco">
    <iframe id="vista" title="Vista previa del sitio"></iframe>
  </div>
</div>

<script id="datos" type="application/json">%(datos)s</script>
<script id="css-sitio" type="text/plain">%(css_sitio)s</script>
<script id="js-sitio" type="text/plain">%(js_sitio)s</script>
"""

# El router es el mismo en las dos salidas: la única diferencia entre ellas es
# lo que rodea al iframe.
ROUTER = """<script>
(function () {
  var D = JSON.parse(document.getElementById('datos').textContent);
  var CSS = document.getElementById('css-sitio').textContent;
  var JS = document.getElementById('js-sitio').textContent;
  var vista = document.getElementById('vista');
  var marco = document.getElementById('marco');
  var actual = '';

  function resolver(html) {
    return html
      .replace('<!--CSS-->', function () { return '<style>' + CSS + '</style>'; })
      .replace('<!--JS-->', function () { return '<scr' + 'ipt>' + JS + '<\\/scr' + 'ipt>'; })
      .replace(/IMG:([^"'\\s,]+)/g, function (_, clave) { return D.img[clave] || ''; });
  }

  function ir(destino) {
    var partes = String(destino).split('#');
    var rel = partes[0], ancla = partes[1] || '';
    if (!D.paginas[rel]) { rel = 'index.html'; ancla = ''; }
    actual = destino;
    document.querySelectorAll('.chip').forEach(function (c) {
      c.classList.toggle('activo', c.dataset.p === rel);
    });
    if (ancla) {
      vista.addEventListener('load', function bajar() {
        vista.removeEventListener('load', bajar);
        var t = vista.contentDocument && vista.contentDocument.getElementById(ancla);
        if (t) t.scrollIntoView();
      });
    }
    vista.srcdoc = resolver(D.paginas[rel]) +
      '<scr' + 'ipt>document.addEventListener("click",function(e){' +
      'var a=e.target.closest(\\'a[href^="PAGE:"]\\');if(!a)return;e.preventDefault();' +
      'parent.postMessage({cbIr:a.getAttribute("href").slice(5)},"*");});<\\/scr' + 'ipt>';
    if (location.hash.slice(2) !== destino) location.hash = '#/' + destino;
  }

  addEventListener('message', function (e) { if (e.data && e.data.cbIr) ir(e.data.cbIr); });
  addEventListener('hashchange', function () { var r = location.hash.slice(2); if (r && r !== actual) ir(r); });
  document.querySelectorAll('.chip').forEach(function (c) {
    c.addEventListener('click', function () { ir(c.dataset.p); });
  });
  document.querySelectorAll('.ancho').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.ancho').forEach(function (o) { o.classList.remove('activo'); });
      b.classList.add('activo');
      marco.style.width = b.dataset.w + 'px';
      marco.classList.toggle('telefono', b.dataset.w === '390');
    });
  });

  ir(location.hash.slice(2) || 'index.html');
})();
</script>
"""

DOC = DOC + ROUTER

CSS_SHELL = """
:root{
  --tinta:#0b1b2e; --papel:#eef3f8; --panel:#ffffff; --linea:#d7e3ef;
  --navy:#00285A; --celeste:#00A8FC; --suave:#5d6e82;
}
@media (prefers-color-scheme: dark){
  :root{ --tinta:#e8eef6; --papel:#08141f; --panel:#0f2133; --linea:#1e3550; --suave:#9bb0c6; }
}
:root[data-theme="dark"]{ --tinta:#e8eef6; --papel:#08141f; --panel:#0f2133; --linea:#1e3550; --suave:#9bb0c6; }
:root[data-theme="light"]{ --tinta:#0b1b2e; --papel:#eef3f8; --panel:#ffffff; --linea:#d7e3ef; --suave:#5d6e82; }
*{box-sizing:border-box}
body{
  margin:0; background:var(--papel); color:var(--tinta);
  font-family:'Poppins',system-ui,-apple-system,'Segoe UI',sans-serif;
  -webkit-font-smoothing:antialiased;
}
.barra{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:14px 20px; background:var(--navy); color:#fff; flex-wrap:wrap;
}
.marca{display:flex; align-items:center; gap:12px}
.marca img{height:30px; width:auto; display:block}
.marca span{
  font-size:.7rem; letter-spacing:.18em; text-transform:uppercase; color:#9fd4ff;
}
.anchos{display:flex; gap:8px}
.ancho{
  border:1px solid rgba(255,255,255,.32); background:transparent; color:#fff;
  padding:7px 15px; border-radius:999px; font:inherit; font-size:.83rem; cursor:pointer;
}
.ancho.activo{background:var(--celeste); border-color:var(--celeste); color:var(--navy); font-weight:600}
.ancho:focus-visible,.chip:focus-visible{outline:3px solid var(--celeste); outline-offset:2px}

.paginas{
  display:flex; gap:22px; flex-wrap:wrap; align-items:flex-start;
  padding:16px 20px 6px; background:var(--panel); border-bottom:1px solid var(--linea);
}
.grupo-t{
  margin:0 0 7px; font-size:.66rem; letter-spacing:.16em; text-transform:uppercase;
  color:var(--suave);
}
.chips{display:flex; gap:7px; flex-wrap:wrap}
.chip{
  border:1px solid var(--linea); background:transparent; color:var(--tinta);
  padding:6px 13px; border-radius:999px; font:inherit; font-size:.83rem; cursor:pointer;
}
.chip:hover{border-color:var(--celeste)}
.chip.activo{background:var(--navy); border-color:var(--navy); color:#fff; font-weight:600}

.aviso{
  margin:0; padding:11px 20px; background:var(--panel); color:var(--suave);
  font-size:.82rem; line-height:1.55; border-bottom:1px solid var(--linea);
}
.escena{display:flex; justify-content:center; padding:26px 16px 40px}
.marco{
  width:390px; max-width:100%; height:78vh; min-height:520px;
  background:#fff; border:1px solid var(--linea); border-radius:14px; overflow:hidden;
  box-shadow:0 18px 50px rgba(0,40,90,.16);
}
.marco.telefono{border-radius:30px; border:9px solid #10233a; box-shadow:0 20px 55px rgba(0,40,90,.28)}
.marco iframe{width:100%; height:100%; border:0; display:block; background:#fff}
@media (prefers-reduced-motion: reduce){*{animation:none!important; transition:none!important}}
"""

# ----------------------------------------------------------------- salidas

DOC_MOVIL = """<title>climabaires.com</title>
<meta name="theme-color" content="#00285A">
<style>
%(css_movil)s
</style>

<div class="pantalla">
  <iframe id="vista" title="climabaires.com"></iframe>
</div>

<script id="datos" type="application/json">%(datos)s</script>
<script id="css-sitio" type="text/plain">%(css_sitio)s</script>
<script id="js-sitio" type="text/plain">%(js_sitio)s</script>
""" + ROUTER

# En el celular el sitio va a sangre, sin nada alrededor: es la simulación.
# En una pantalla ancha se centra una columna del ancho de un teléfono, porque
# si no el navegador rendiría la versión de escritorio y dejaría de simular
# justamente lo que se quiere ver.
CSS_MOVIL = """
:root{ --fondo:#dfe7f0; }
@media (prefers-color-scheme: dark){ :root{ --fondo:#0a1622; } }
:root[data-theme="dark"]{ --fondo:#0a1622; }
:root[data-theme="light"]{ --fondo:#dfe7f0; }
html,body{margin:0;height:100%;background:var(--fondo);overflow:hidden}
.pantalla{
  width:100vw; height:100vh; height:100dvh;
  display:flex; align-items:center; justify-content:center;
}
#vista{width:100%; height:100%; border:0; display:block; background:#fff}

/* de 760 px para arriba ya no es un celular: se acota a un teléfono centrado */
@media (min-width:760px){
  .pantalla{padding:22px}
  #vista{
    width:412px; height:min(880px, calc(100dvh - 44px));
    border-radius:34px; border:10px solid #0d1f33;
    box-shadow:0 24px 60px rgba(0,30,70,.34);
  }
}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}
"""

comun = {
    'datos': DATOS.replace('</', '<\\/'),
    'css_sitio': CSS.replace('</', '<\\/'),
    'js_sitio': JS.replace('</', '<\\/'),
}

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)

with open(SALIDA, 'w', encoding='utf-8') as f:
    f.write(DOC % dict(comun, css_shell=CSS_SHELL, menu=menu,
                       logo=MAPA_IMG.get('assets/img/logo-blanco.webp', '')))
with open(SALIDA_MOVIL, 'w', encoding='utf-8') as f:
    f.write(DOC_MOVIL % dict(comun, css_movil=CSS_MOVIL))

for ruta in (SALIDA, SALIDA_MOVIL):
    print('OK %s · %d páginas · %.1f MB' % (
        os.path.normpath(ruta), len(PAGINAS), os.path.getsize(ruta) / 1e6))
