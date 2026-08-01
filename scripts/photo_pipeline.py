"""Motor de mejora de fotografia de producto para tortas.

Pensado para fotos tomadas con celular sobre fondo claro (pared/mantel) que llegan
comprimidas por WhatsApp: fondo grisaceo y desparejo, dominante calida, negros
levantados y poca microdefinicion.

Etapas (en este orden):
  1. Balance de blancos tomando el fondo como referencia de neutro.
  2. Mascara de sujeto (color + textura + luminancia relativa al fondo).
  3. Aplanado de campo (flat-field): modela la iluminacion del fondo con una
     convolucion normalizada que ignora al sujeto, y la corrige. Deja el fondo
     parejo y luminoso sin halos ni recortes duros.
  4. Suavizado del ruido JPEG que queda visible al levantar el fondo.
  5. Punto negro / punto blanco, recuperacion de altas luces y apertura de sombras.
  6. Curva S de contraste sobre la luminancia (no desplaza el color).
  7. Vibrance (satura mas lo que esta apagado y respeta lo que ya esta saturado).
  8. Claridad (contraste local) y enfoque enmascarado al sujeto.

Todo el trabajo tonal se hace en luz lineal y float32; el color se maneja en
CIELAB para no correr los tonos al ajustar contraste.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

Image.MAX_IMAGE_PIXELS = None


# --------------------------------------------------------------------------
# Conversiones de espacio de color
# --------------------------------------------------------------------------

def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


_M_RGB2XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
], dtype=np.float32)
_M_XYZ2RGB = np.linalg.inv(_M_RGB2XYZ).astype(np.float32)
_WHITE = np.array([0.95047, 1.00000, 1.08883], dtype=np.float32)


def linear_to_lab(rgb: np.ndarray) -> np.ndarray:
    xyz = rgb @ _M_RGB2XYZ.T / _WHITE
    eps, kappa = 216 / 24389, 24389 / 27
    f = np.where(xyz > eps, np.cbrt(np.maximum(xyz, 1e-12)), (kappa * xyz + 16) / 116)
    return np.stack([
        116 * f[..., 1] - 16,
        500 * (f[..., 0] - f[..., 1]),
        200 * (f[..., 1] - f[..., 2]),
    ], axis=-1)


def lab_to_linear(lab: np.ndarray) -> np.ndarray:
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    eps, kappa = 216 / 24389, 24389 / 27
    def inv(t):
        t3 = t ** 3
        return np.where(t3 > eps, t3, (116 * t - 16) / kappa)
    xyz = np.stack([inv(fx), inv(fy), inv(fz)], axis=-1) * _WHITE
    return xyz @ _M_XYZ2RGB.T


def luminance(rgb_lin: np.ndarray) -> np.ndarray:
    return rgb_lin @ np.array([0.2126729, 0.7151522, 0.0721750], dtype=np.float32)


# --------------------------------------------------------------------------
# Parametros
# --------------------------------------------------------------------------

@dataclass
class Params:
    """Ajustes por foto. Los valores por defecto ya dan un resultado publicable."""

    # Balance de blancos
    wb_strength: float = 0.92      # 0 = sin correccion, 1 = fondo perfectamente neutro
    warmth: float = 0.03           # calidez que se devuelve despues del WB (-0.3..0.3)

    # Fondo
    bg_target: float = 0.955       # nivel al que se lleva el fondo (0-1, sRGB)
    bg_strength: float = 0.92      # cuanto del aplanado se aplica (0-1)
    bg_smooth: float = 0.35        # alisado del telon lejos de la pieza (0-1)
    bg_clean: float = 0.88         # uniformado extra lejos de la pieza (0-1)
    bg_max_gain: float = 3.2       # tope de ganancia para no quemar
    bg_min_gain: float = 0.80      # permite bajar zonas del fondo mas claras que el objetivo
    bg_scale: float = 0.055        # detalle del modelo de luz (fraccion del lado corto)
    bg_denoise: float = 0.75       # suavizado del grano/bloques JPEG en el fondo
    bg_keep_shadow: float = 0.45   # sombra de apoyo que se conserva junto a la pieza

    # Mascara de sujeto
    subject_sensitivity: float = 1.0   # >1 detecta mas sujeto (util si se come detalle)
    subject_feather: float = 0.010     # difuminado del borde, fraccion del ancho

    # Tono
    black_point: float = 0.30      # percentil del sujeto que se manda a negro
    black_lift: float = 0.012      # negro filmico, evita el negro plano
    shadow_lift: float = 0.10      # apertura de sombras
    highlight_recovery: float = 0.30   # devuelve textura a cremas y merengues
    exposure: float = 0.0          # stops extra
    contrast: float = 0.13         # curva S sobre el sujeto

    # Color
    vibrance: float = 0.26
    saturation: float = 1.02

    # Detalle
    clarity: float = 0.22          # contraste local (radio grande)
    sharpen: float = 0.62          # enfoque (radio chico)
    sharpen_radius: float = 1.05

    # Geometria
    rotate: float = 0.0            # grados, positivo = antihorario
    crop_bias_y: float = 0.0       # -1 sube el encuadre, +1 lo baja

    def merged(self, overrides: dict) -> "Params":
        valid = {f.name for f in fields(self)}
        data = asdict(self)
        for k, v in (overrides or {}).items():
            if k in valid:
                data[k] = v
        return Params(**data)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def _gauss(a: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return a
    if a.ndim == 3:
        return np.stack([ndi.gaussian_filter(a[..., c], sigma, mode="nearest")
                         for c in range(a.shape[-1])], axis=-1)
    return ndi.gaussian_filter(a, sigma, mode="nearest")


def _smoothstep(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    t = np.clip((x - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _fill_small_holes(m: np.ndarray, max_frac: float) -> np.ndarray:
    """Rellena huecos chicos y deja los grandes.

    binary_fill_holes a secas rellenaria el pedazo de pared que queda encerrado
    entre el topper y la torta, que es justo lo que hay que dejar afuera.
    """
    inv = ~m
    lbl, n = ndi.label(inv)
    if not n:
        return m
    edge = np.unique(np.concatenate([lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]]))
    sizes = ndi.sum(inv, lbl, index=np.arange(1, n + 1))
    out = m.copy()
    for i, s in enumerate(sizes, start=1):
        if i not in edge and s < max_frac * m.size:
            out[lbl == i] = True
    return out


def _border_ring(shape, frac: float = 0.045) -> np.ndarray:
    """Mascara del anillo perimetral, que en estas tomas siempre es fondo."""
    h, w = shape
    m = np.zeros((h, w), dtype=bool)
    ty, tx = max(2, int(h * frac)), max(2, int(w * frac))
    m[:ty, :] = True
    m[-ty:, :] = True
    m[:, :tx] = True
    m[:, -tx:] = True
    return m


# --------------------------------------------------------------------------
# 1. Balance de blancos
# --------------------------------------------------------------------------

def white_balance(rgb_lin: np.ndarray, subj: np.ndarray, p: Params) -> tuple[np.ndarray, dict]:
    """Neutraliza la dominante con el metodo del parche blanco.

    La referencia son los pixeles claros y poco saturados: merengue, crema, platos,
    puntillas y mantel iluminado. No sirve promediar el fondo entero, porque mezcla
    la pared calida con la parte del mantel en sombra, que es azulada, y termina
    calentando toda la foto. El filtro de croma tambien evita que una bandeja o un
    lazo dorado pasen por blanco.
    """
    h, w, _ = rgb_lin.shape
    lum = luminance(rgb_lin)
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    chroma = np.hypot(lab[..., 1], lab[..., 2])

    band = (lum >= np.percentile(lum, 90)) & (lum <= np.percentile(lum, 99.3))
    sel = band & (chroma <= np.percentile(chroma[band], 55)) if band.any() else band
    if sel.sum() < 500:
        sel = subj < 0.30
    if sel.sum() < 500:
        sel = _border_ring((h, w))

    ref = np.maximum(np.array([rgb_lin[..., c][sel].mean() for c in range(3)],
                              dtype=np.float32), 1e-4)
    gray = float(ref.mean())
    # Tope duro: una foto puede no tener ningun blanco real y no queremos que una
    # correccion salvaje se lleve puesto el color de la torta.
    gains = np.clip(gray / ref, 0.87, 1.15)
    gains = 1.0 + (gains - 1.0) * float(np.clip(p.wb_strength, 0, 1))

    # Calidez controlada: sube rojo y baja azul de forma sutil, sin tocar el verde.
    wm = float(p.warmth)
    gains = gains * np.array([1 + 0.09 * wm, 1.0, 1 - 0.11 * wm], dtype=np.float32)

    out = rgb_lin * gains.astype(np.float32)
    info = {
        "wb_ref_srgb": [round(float(v), 1) for v in linear_to_srgb(ref) * 255],
        "wb_gains": [round(float(g), 4) for g in gains],
    }
    return np.clip(out, 0, 4), info


# --------------------------------------------------------------------------
# 2. Mascara de sujeto
# --------------------------------------------------------------------------

def subject_mask(rgb_lin: np.ndarray, p: Params) -> np.ndarray:
    """Separa la pieza del fondo con watershed sobre el gradiente.

    Un umbral global no sirve: el fondo son dos cosas distintas (pared gris arriba,
    mantel blanco abajo) y la pared es mas oscura que la torta iluminada. El
    watershed parte de marcadores seguros -el perimetro es fondo, el centro con
    color o textura fuerte es pieza- y deja que los bordes decidan el limite.
    """
    h, w, _ = rgb_lin.shape
    scale = 420 / max(h, w)
    sh, sw = max(48, int(round(h * scale))), max(48, int(round(w * scale)))
    small = np.asarray(
        Image.fromarray((linear_to_srgb(np.clip(rgb_lin, 0, 1)) * 255).astype(np.uint8))
        .resize((sw, sh), Image.LANCZOS)
    ).astype(np.float32) / 255.0
    lab = linear_to_lab(srgb_to_linear(small))
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)

    Ls = ndi.gaussian_filter(L, 1.2, mode="nearest")
    grad = np.hypot(ndi.sobel(Ls, 0), ndi.sobel(Ls, 1))
    grad += 0.6 * np.hypot(ndi.sobel(ndi.gaussian_filter(a, 1.2), 0),
                           ndi.sobel(ndi.gaussian_filter(a, 1.2), 1))
    grad += 0.6 * np.hypot(ndi.sobel(ndi.gaussian_filter(b, 1.2), 0),
                           ndi.sobel(ndi.gaussian_filter(b, 1.2), 1))

    m1 = ndi.uniform_filter(L, 7, mode="nearest")
    m2 = ndi.uniform_filter(L * L, 7, mode="nearest")
    tex = np.sqrt(np.maximum(m2 - m1 * m1, 0))

    ring = _border_ring((sh, sw), 0.028)
    C_bg = float(np.percentile(C[ring], 80))
    T_bg = float(np.percentile(tex[ring], 96))

    s = float(max(0.3, p.subject_sensitivity))
    inner = np.zeros((sh, sw), dtype=bool)
    inner[int(sh * 0.10):int(sh * 0.97), int(sw * 0.06):int(sw * 0.94)] = True
    seed = inner & (((C - C_bg) > 7.0 / s) | ((tex - T_bg) > 2.2 / s))
    seed = ndi.binary_opening(seed, np.ones((3, 3)), border_value=0)
    seed = ndi.binary_closing(seed, np.ones((7, 7)), border_value=0)
    if seed.sum() < 0.004 * sh * sw:   # pieza muy clara y lisa: bajamos la vara
        seed = inner & (((C - C_bg) > 3.5 / s) | ((tex - T_bg) > 1.0 / s))
        seed = ndi.binary_closing(seed, np.ones((7, 7)), border_value=0)

    # Marcadores de fondo. Con el anillo solo no alcanza: la pared es una meseta
    # lisa y la inundacion que sale del topper la reclama entera, y despues esa
    # pared marcada como pieza queda sin limpiar y se ve como un halo gris.
    # Marcando tambien lo liso, claro y sin color, la inundacion del fondo llega
    # primero a donde tiene que llegar.
    calm = (tex < max(T_bg * 1.15, 1.2)) & (C < C_bg + 4.0) & (L > 35.0)
    calm &= ~ndi.binary_dilation(seed, np.ones((15, 15)), border_value=0)
    calm = ndi.binary_opening(calm, np.ones((5, 5)), border_value=0)

    markers = np.zeros((sh, sw), dtype=np.int32)
    markers[calm] = 1
    markers[ring] = 1
    markers[seed] = 2
    if (markers == 2).sum() < 30:
        markers[int(sh * 0.42):int(sh * 0.62), int(sw * 0.40):int(sw * 0.60)] = 2

    from skimage.segmentation import watershed  # import diferido: solo se usa aca
    lab_ws = watershed(grad, markers)
    m = lab_ws == 2

    m = ndi.binary_closing(m, np.ones((7, 7)), border_value=0)
    m = _fill_small_holes(m, 0.02)

    # Poda: lo que quedo dentro de la mascara pero se parece al fondo que tiene
    # alrededor es pared que la inundacion se llevo puesta. Se compara contra un
    # modelo local del fondo, no contra un valor global, porque el fondo son dos
    # superficies distintas: pared arriba, mantel abajo.
    if m.any() and not m.all():
        bgm = (~m).astype(np.float32)
        sig = max(6.0, 0.14 * max(sh, sw))
        ref = np.stack([ndi.gaussian_filter(lab[..., c] * bgm, sig, mode="nearest") /
                        np.maximum(ndi.gaussian_filter(bgm, sig, mode="nearest"), 1e-4)
                        for c in range(3)], axis=-1)
        dist = np.sqrt(((lab - ref) ** 2 * np.array([1.0, 2.0, 2.0])).sum(axis=-1))
        m &= ~((dist < 7.0) & (tex < max(T_bg * 1.3, 1.5)))
        m = ndi.binary_opening(m, np.ones((3, 3)), border_value=0)
        m = ndi.binary_closing(m, np.ones((7, 7)), border_value=0)

    lbl, n = ndi.label(m)
    if n:
        areas = ndi.sum(m, lbl, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[int(np.argmax(areas)) + 1] = True
        # Cintas, toppers y velas pueden quedar sueltos: conservamos lo grande.
        for i, ar in enumerate(areas, start=1):
            if ar > 0.008 * sh * sw:
                keep[i] = True
        m = keep[lbl]
    m = _fill_small_holes(m, 0.02)
    m = ndi.binary_dilation(m, np.ones((5, 5)), border_value=0)

    soft = np.clip(_gauss(m.astype(np.float32), max(1.0, sw * 0.010)) * 1.20, 0, 1)
    full = np.asarray(
        Image.fromarray((soft * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    ).astype(np.float32) / 255.0
    return _gauss(full, max(1.0, w * max(p.subject_feather, 0.002)))


# --------------------------------------------------------------------------
# 3. Aplanado de fondo
# --------------------------------------------------------------------------

def flatten_background(rgb_lin: np.ndarray, subj: np.ndarray, p: Params) -> tuple[np.ndarray, dict]:
    """Modela la luz del fondo ignorando al sujeto y la corrige a un tono parejo.

    El modelo se calcula a dos escalas con convolucion normalizada. La escala fina
    sigue las sombras de la pared, pero cerca de la pieza casi no tiene muestras de
    fondo: ahi la confianza cae y manda la escala gruesa, que extrapola sin halos.
    """
    h, w, _ = rgb_lin.shape
    short = float(min(h, w))
    bgw = np.clip(1.0 - subj, 0, 1)

    def field_at(sigma: float) -> tuple[np.ndarray, np.ndarray]:
        num = _gauss(rgb_lin * bgw[..., None], sigma)
        den = _gauss(bgw, sigma)
        return num / np.maximum(den, 1e-4)[..., None], den

    s_fine = max(8.0, short * float(np.clip(p.bg_scale, 0.02, 0.30)))
    s_coarse = max(s_fine * 3.0, short * 0.22)
    f_fine, d_fine = field_at(s_fine)
    f_coarse, _ = field_at(s_coarse)
    conf = _smoothstep(d_fine, 0.07, 0.38)[..., None]
    field = np.maximum(_gauss(f_fine * conf + f_coarse * (1 - conf), s_fine * 0.6), 1e-4)

    target_lin = float(srgb_to_linear(np.array([p.bg_target], dtype=np.float32))[0])
    gain = np.clip(target_lin / field, float(p.bg_min_gain), float(p.bg_max_gain))

    # Dos vecindades distintas. La estrecha solo evita artefactos justo contra el
    # borde de la pieza. La de apoyo mira hacia abajo: ahi vive la sombra de
    # contacto, la unica que conviene conservar. Las sombras de pared se van.
    prox = np.clip(_gauss(subj, short * 0.015) * 1.5, 0, 1)
    shift = max(1, int(short * 0.020))
    below = np.zeros_like(subj)
    below[shift:, :] = subj[:-shift, :]
    prox_base = np.clip(_gauss(below, short * 0.035) * 1.6, 0, 1) * (1.0 - subj)

    lum, lum_field = luminance(rgb_lin), luminance(field)
    shadow = _smoothstep(lum / np.maximum(lum_field, 1e-4), 0.45, 0.92)
    keep = 1.0 - (1.0 - shadow) * float(np.clip(p.bg_keep_shadow, 0, 1)) * prox_base

    strength = float(np.clip(p.bg_strength, 0, 1)) * bgw * keep
    out = rgb_lin * (1.0 + (gain - 1.0) * strength[..., None])

    # Alisado del fondo: borra arrugas del telon, manchas de pared y bloques de
    # compresion. Otra convolucion normalizada, para que la pieza no se derrame
    # sobre el fondo al desenfocar.
    if p.bg_smooth > 0:
        sig = max(6.0, short * 0.045)
        num = _gauss(out * bgw[..., None], sig)
        den = _gauss(bgw, sig)[..., None]
        smooth = num / np.maximum(den, 1e-4)
        wgt = (bgw * (1.0 - prox) * (1.0 - 0.75 * prox_base)
               * float(np.clip(p.bg_smooth, 0, 1)))[..., None]
        out = out * (1 - wgt) + smooth * wgt

    # Uniformado final. En vez de pintar el fondo de un color plano, se le cambia
    # solo la base: se separa la parte de baja frecuencia (la mancha de pared, la
    # caida de luz) y se la reemplaza por el tono objetivo, dejando el detalle.
    # Asi el borde de un plato o el relieve de una puntilla sobreviven aunque la
    # mascara los haya contado como fondo, y un fondo parejo ademas comprime mucho
    # mejor en AVIF y WebP.
    if p.bg_clean > 0:
        sig = max(4.0, short * 0.030)
        num = _gauss(out * bgw[..., None], sig)
        den = _gauss(bgw, sig)[..., None]
        base = num / np.maximum(den, 1e-4)
        det = out - base
        # Nucleo muerto: lo de amplitud chica es ruido de compresion y se va; lo
        # de amplitud grande es estructura real y queda.
        coring = _smoothstep(np.abs(det).max(axis=-1), 0.008, 0.040)[..., None]
        flat_color = np.array([target_lin, target_lin * 0.997, target_lin * 0.982],
                              dtype=np.float32)
        clean = flat_color + det * coring
        far = bgw * (1.0 - prox_base) * float(np.clip(p.bg_clean, 0, 1))
        out = out * (1 - far[..., None]) + clean * far[..., None]

    # El sujeto recibe solo la parte cromatica de la correccion (uniformar el color
    # de la luz), nunca la ganancia completa, para no lavar la torta.
    chroma_gain = gain / np.maximum(gain.mean(axis=-1, keepdims=True), 1e-4)
    out = out * (1.0 + (chroma_gain - 1.0) * (subj * 0.30)[..., None])

    if p.bg_denoise > 0:
        sm = _gauss(out, max(0.8, short * 0.0022))
        flat = bgw * (1.0 - _smoothstep(np.abs(out - sm).max(axis=-1), 0.006, 0.05))
        wgt = (flat * float(np.clip(p.bg_denoise, 0, 1)))[..., None]
        out = out * (1 - wgt) + sm * wgt

    info = {"bg_gain_median": round(float(np.median(gain)), 3)}
    return np.clip(out, 0, 8), info


# --------------------------------------------------------------------------
# 5-6. Tono
# --------------------------------------------------------------------------

def tone(rgb_lin: np.ndarray, subj: np.ndarray, p: Params) -> np.ndarray:
    rgb = np.clip(rgb_lin, 0, 8)
    if abs(p.exposure) > 1e-3:
        rgb = rgb * (2.0 ** float(p.exposure))

    srgb = linear_to_srgb(np.clip(rgb, 0, 1))
    # El punto negro se mide sobre el sujeto: el fondo claro sesgaria la medicion.
    # El punto blanco no se estira, ya lo fijo el aplanado del fondo; estirarlo aca
    # quemaria merengues y cremas.
    wsub = subj > 0.35
    sample = srgb[..., 1][wsub] if wsub.sum() > 500 else srgb[..., 1].ravel()
    lo = min(float(np.percentile(sample, p.black_point)), 0.35)

    x = np.clip((srgb - lo) / (1.0 - lo), 0, 1)
    x = float(p.black_lift) + x * (1.0 - float(p.black_lift))

    lin = srgb_to_linear(x)

    # Recuperacion de altas luces: curva de potencia sobre el tramo alto. Deja el
    # blanco puro donde estaba y baja apenas lo que venia sin textura.
    if p.highlight_recovery > 0:
        knee = 0.68
        Ln = luminance(lin)
        t = np.clip((Ln - knee) / (1.0 - knee), 0, 1)
        y = knee + (1.0 - knee) * np.power(t, 1.0 + 0.55 * float(p.highlight_recovery))
        scale = np.where(Ln > knee, y / np.maximum(Ln, 1e-6), 1.0)
        lin = lin * scale[..., None]

    # Apertura de sombras, ponderada al sujeto para no ensuciar el fondo.
    if p.shadow_lift > 0:
        Ln = luminance(lin)
        t = 1.0 - _smoothstep(Ln, 0.0, 0.42)
        amt = float(p.shadow_lift) * t * (0.30 + 0.70 * subj)
        lin = lin + amt[..., None] * (0.10 + 0.30 * lin)

    lab = linear_to_lab(np.clip(lin, 0, 1))
    if abs(p.contrast) > 1e-3:
        L = lab[..., 0] / 100.0
        # Curva S centrada en el gris medio, atenuada en el fondo.
        k = float(p.contrast) * (0.35 + 0.65 * subj)
        lab[..., 0] = np.clip(L - k * np.sin(2 * math.pi * np.clip(L, 0, 1)) * 0.5,
                              0, 1) * 100.0
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# 7. Color
# --------------------------------------------------------------------------

def color(rgb_lin: np.ndarray, p: Params) -> np.ndarray:
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    a, b = lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    if abs(p.vibrance) > 1e-3:
        # Sube lo apagado y deja quieto lo que ya esta saturado (frutillas, m&m).
        # Los blancos altos quedan afuera: si no, cremas y merengues se van a beige.
        white_guard = 1.0 - _smoothstep(lab[..., 0], 82.0, 95.0)
        f = 1.0 + float(p.vibrance) * (1.0 - _smoothstep(C, 8.0, 55.0)) * white_guard
        lab[..., 1] = a * f
        lab[..., 2] = b * f
    if abs(p.saturation - 1.0) > 1e-3:
        lab[..., 1] *= float(p.saturation)
        lab[..., 2] *= float(p.saturation)
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# 8. Detalle
# --------------------------------------------------------------------------

def detail(rgb_lin: np.ndarray, subj: np.ndarray, p: Params) -> np.ndarray:
    h, w, _ = rgb_lin.shape
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    L = lab[..., 0]

    if p.clarity > 0:
        base = _gauss(L, max(3.0, min(h, w) * 0.022))
        d = L - base
        # El contraste local se aplica sobre el sujeto y se atenua en altas luces.
        prot = 1.0 - _smoothstep(L, 82.0, 97.0)
        L = L + d * float(p.clarity) * (0.25 + 0.75 * subj) * prot

    if p.sharpen > 0:
        r = max(0.6, float(p.sharpen_radius) * (min(h, w) / 1000.0) * 1.15)
        blur = _gauss(L, r)
        d = L - blur
        # Umbral suave: no amplifica el ruido de las zonas planas.
        gate = _smoothstep(np.abs(d), 0.5, 2.2)
        L = L + d * float(p.sharpen) * gate * (0.3 + 0.7 * subj)

    lab[..., 0] = np.clip(L, 0, 100)
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def enhance(img: Image.Image, p: Params) -> tuple[np.ndarray, np.ndarray, dict]:
    """Devuelve (rgb sRGB float 0-1, mascara de sujeto, info)."""
    img = img.convert("RGB")
    if abs(p.rotate) > 0.01:
        img = img.rotate(p.rotate, resample=Image.BICUBIC, expand=False, fillcolor=None)

    arr = np.asarray(img).astype(np.float32) / 255.0
    lin = srgb_to_linear(arr)

    # La mascara va primero: el balance de blancos necesita saber que es fondo.
    subj = subject_mask(lin, p)
    lin, info = white_balance(lin, subj, p)
    lin, bginfo = flatten_background(lin, subj, p)
    info.update(bginfo)
    lin = tone(lin, subj, p)
    lin = color(lin, p)
    lin = detail(lin, subj, p)

    out = linear_to_srgb(np.clip(lin, 0, 1))
    info["subject_coverage"] = round(float((subj > 0.5).mean()), 3)
    return out, subj, info


def to_pil(rgb01: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(rgb01 * 255.0 + 0.5, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------
# Encuadre y extension de lienzo
# --------------------------------------------------------------------------

def subject_bbox(subj: np.ndarray, thr: float = 0.45) -> tuple[int, int, int, int]:
    m = subj > thr
    if not m.any():
        h, w = subj.shape
        return 0, 0, w, h
    ys, xs = np.where(m)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def extend_canvas(rgb01: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Recorta segun box, que puede salirse del lienzo, sintetizando el fondo.

    Como despues del aplanado el fondo es casi uniforme, replicar el borde y
    fundirlo hacia el color plano del perimetro no deja costura visible.
    """
    x0, y0, x1, y1 = box
    h, w, _ = rgb01.shape
    pl, pt = max(0, -x0), max(0, -y0)
    pr, pb = max(0, x1 - w), max(0, y1 - h)
    if pl or pt or pr or pb:
        ext = np.pad(rgb01, ((pt, pb), (pl, pr), (0, 0)), mode="edge")
        # Color plano de referencia: promedio del anillo perimetral original.
        ring = _border_ring((h, w), 0.03)
        flat = rgb01[ring].mean(axis=0)
        eh, ew, _ = ext.shape
        yy = np.arange(eh)[:, None]
        xx = np.arange(ew)[None, :]
        dist = np.maximum.reduce([
            (pt - yy) / max(pt, 1) if pt else np.zeros((eh, 1)) + 0.0,
            (yy - (eh - pb - 1)) / max(pb, 1) if pb else np.zeros((eh, 1)) + 0.0,
            (pl - xx) / max(pl, 1) if pl else np.zeros((1, ew)) + 0.0,
            (xx - (ew - pr - 1)) / max(pr, 1) if pr else np.zeros((1, ew)) + 0.0,
        ])
        t = _smoothstep(np.clip(dist, 0, 1), 0.0, 0.85)[..., None]
        blurred = _gauss(ext, max(6.0, min(eh, ew) * 0.02))
        ext = ext * (1 - t) + (blurred * (1 - t * 0.6) + flat * (t * 0.6)) * t
        x0 += pl; x1 += pl; y0 += pt; y1 += pt
        rgb01 = ext
    return rgb01[y0:y1, x0:x1]


def smart_crop(rgb01: np.ndarray, subj: np.ndarray, aspect: float, p: Params,
               margin: float = 0.09) -> np.ndarray:
    """Encuadra al aspecto pedido garantizando que la pieza entera entre completa."""
    h, w, _ = rgb01.shape
    x0, y0, x1, y1 = subject_bbox(subj)
    bw, bh = x1 - x0, y1 - y0
    mx, my = bw * margin, bh * margin
    x0, x1 = x0 - mx, x1 + mx
    y0, y1 = y0 - my * 1.15, y1 + my
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cw, ch = x1 - x0, y1 - y0

    if cw / ch < aspect:
        cw = ch * aspect
    else:
        ch = cw / aspect
    cy += ch * 0.12 * float(np.clip(p.crop_bias_y, -1, 1))

    box = (int(round(cx - cw / 2)), int(round(cy - ch / 2)),
           int(round(cx + cw / 2)), int(round(cy + ch / 2)))
    return extend_canvas(rgb01, box)


def resize_to(rgb01: np.ndarray, width: int, height: int) -> Image.Image:
    im = to_pil(rgb01)
    if (im.width, im.height) == (width, height):
        return im
    return im.resize((width, height), Image.LANCZOS)


def post_resize_sharpen(im: Image.Image, amount: float = 0.32) -> Image.Image:
    """Reenfoque leve despues de reescalar, solo sobre la luminancia."""
    if amount <= 0:
        return im
    a = np.asarray(im).astype(np.float32) / 255.0
    lab = linear_to_lab(srgb_to_linear(a))
    L = lab[..., 0]
    d = L - _gauss(L, 0.9)
    gate = _smoothstep(np.abs(d), 0.4, 2.0)
    lab[..., 0] = np.clip(L + d * amount * gate, 0, 100)
    return to_pil(linear_to_srgb(np.clip(lab_to_linear(lab), 0, 1)))
