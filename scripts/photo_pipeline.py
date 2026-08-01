"""Revelado de las fotos de tortas: luz, color y nitidez, sin tocar el fondo.

Las fotos vienen de celular y comprimidas por WhatsApp: quedan oscuras, con una
dominante de color distinta en cada una y con poca definicion. El objetivo es que
todas se vean claras, limpias y parecidas entre si, conservando la escena tal
como fue tomada: la pared, el mantel y las sombras quedan donde estaban.

Etapas:
  1. Balance de blancos por parche blanco, para sacar la dominante.
  2. Exposicion automatica: lleva el blanco de cada foto al mismo nivel. Es lo
     que hace que la serie se vea pareja.
  3. Punto negro, recuperacion de altas luces, apertura de sombras y curva S.
  4. Vibrance, que sube lo apagado y respeta lo que ya esta saturado.
  5. Claridad y enfoque.

Todo el trabajo tonal se hace en luz lineal y float32; el color se maneja en
CIELAB para que ajustar contraste no corra los tonos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, fields

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

    # Color de la luz
    wb_strength: float = 0.85      # 0 = sin correccion, 1 = neutro total
    warmth: float = 0.04           # calidez que se devuelve despues (-0.3 a 0.3)

    # Exposicion. El objetivo es el nivel al que se lleva el blanco de la escena
    # (mantel, pared iluminada, crema). Igual para todas: es lo que empareja la serie.
    white_target: float = 0.93     # 0-1 en sRGB
    exposure: float = 0.0          # correccion manual extra, en pasos
    max_lift: float = 2.1          # tope de la subida automatica

    # Tono
    black_point: float = 0.20      # percentil que se manda a negro
    black_lift: float = 0.010      # negro filmico, evita el negro plano
    shadow_lift: float = 0.16      # apertura de sombras
    highlight_recovery: float = 0.35   # devuelve textura a cremas y merengues
    contrast: float = 0.11         # curva S

    # Color
    vibrance: float = 0.24
    saturation: float = 1.02

    # Detalle
    clarity: float = 0.20          # contraste local (radio grande)
    sharpen: float = 0.60          # enfoque (radio chico)
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


# --------------------------------------------------------------------------
# 1. Balance de blancos
# --------------------------------------------------------------------------

def white_balance(rgb_lin: np.ndarray, p: Params) -> tuple[np.ndarray, dict]:
    """Neutraliza la dominante con el metodo del parche blanco.

    La referencia son los pixeles claros y poco saturados: mantel, pared
    iluminada, crema, merengue, platos. El filtro de croma evita que una bandeja
    o un lazo dorado pasen por blanco y terminen enfriando toda la foto.
    """
    lum = luminance(rgb_lin)
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    chroma = np.hypot(lab[..., 1], lab[..., 2])

    band = (lum >= np.percentile(lum, 90)) & (lum <= np.percentile(lum, 99.3))
    sel = band & (chroma <= np.percentile(chroma[band], 55)) if band.any() else band
    if sel.sum() < 500:
        sel = lum >= np.percentile(lum, 90)

    ref = np.maximum(np.array([rgb_lin[..., c][sel].mean() for c in range(3)],
                              dtype=np.float32), 1e-4)
    # Tope duro: una foto puede no tener ningun blanco real y no queremos que una
    # correccion salvaje se lleve puesto el color de la torta.
    gains = np.clip(float(ref.mean()) / ref, 0.87, 1.15)
    gains = 1.0 + (gains - 1.0) * float(np.clip(p.wb_strength, 0, 1))

    wm = float(p.warmth)
    gains = gains * np.array([1 + 0.09 * wm, 1.0, 1 - 0.11 * wm], dtype=np.float32)

    out = np.clip(rgb_lin * gains.astype(np.float32), 0, 4)
    info = {
        "referencia_blanco": [round(float(v), 1) for v in linear_to_srgb(ref) * 255],
        "ganancias_wb": [round(float(g), 3) for g in gains],
    }
    return out, info


# --------------------------------------------------------------------------
# 2. Exposicion
# --------------------------------------------------------------------------

def auto_exposure(rgb_lin: np.ndarray, p: Params) -> tuple[np.ndarray, dict]:
    """Lleva el blanco de la escena al mismo nivel en todas las fotos.

    Se mide el percentil 96 de la luminancia, que en estas tomas cae siempre
    sobre el mantel o la pared iluminada, y se escala para que aterrice en
    white_target. Es una multiplicacion pareja sobre toda la imagen: no hay
    mascaras ni recortes, la escena se mantiene igual, solo mejor expuesta.
    """
    lum = luminance(rgb_lin)
    actual = float(np.percentile(lum, 96))
    target = float(srgb_to_linear(np.array([p.white_target], dtype=np.float32))[0])
    lift = np.clip(target / max(actual, 1e-4), 0.7, float(p.max_lift))
    lift *= 2.0 ** float(p.exposure)

    out = rgb_lin * lift
    # Hombro suave arriba: sin esto, subir la exposicion recorta el mantel y las
    # cremas de golpe y se pierde la textura.
    knee = 0.80
    Ln = luminance(out)
    t = np.clip((Ln - knee) / max(1.6 - knee, 1e-4), 0, 1)
    comp = knee + (1.6 - knee) * (1 - np.exp(-t * 1.9)) / (1 - math.exp(-1.9))
    scale = np.where(Ln > knee, comp / np.maximum(Ln, 1e-6), 1.0)
    out = out * scale[..., None]

    info = {"blanco_medido": round(float(linear_to_srgb(np.array([actual]))[0] * 255), 1),
            "factor_exposicion": round(float(lift), 3)}
    return np.clip(out, 0, 1), info


# --------------------------------------------------------------------------
# 3. Tono
# --------------------------------------------------------------------------

def tone(rgb_lin: np.ndarray, p: Params) -> np.ndarray:
    srgb = linear_to_srgb(np.clip(rgb_lin, 0, 1))
    lo = min(float(np.percentile(srgb[..., 1], p.black_point)), 0.30)
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
        lin = lin * np.where(Ln > knee, y / np.maximum(Ln, 1e-6), 1.0)[..., None]

    if p.shadow_lift > 0:
        Ln = luminance(lin)
        t = 1.0 - _smoothstep(Ln, 0.0, 0.45)
        lin = lin + (float(p.shadow_lift) * t)[..., None] * (0.10 + 0.30 * lin)

    lab = linear_to_lab(np.clip(lin, 0, 1))
    if abs(p.contrast) > 1e-3:
        L = lab[..., 0] / 100.0
        k = float(p.contrast)
        lab[..., 0] = np.clip(L - k * np.sin(2 * math.pi * np.clip(L, 0, 1)) * 0.5,
                              0, 1) * 100.0
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# 4. Color
# --------------------------------------------------------------------------

def color(rgb_lin: np.ndarray, p: Params) -> np.ndarray:
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    a, b = lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    if abs(p.vibrance) > 1e-3:
        # Sube lo apagado y deja quieto lo que ya esta saturado (frutillas, m&m).
        # Los blancos altos quedan afuera: si no, cremas y merengues se van a beige.
        guard = 1.0 - _smoothstep(lab[..., 0], 82.0, 95.0)
        f = 1.0 + float(p.vibrance) * (1.0 - _smoothstep(C, 8.0, 55.0)) * guard
        lab[..., 1], lab[..., 2] = a * f, b * f
    if abs(p.saturation - 1.0) > 1e-3:
        lab[..., 1] *= float(p.saturation)
        lab[..., 2] *= float(p.saturation)
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# 5. Detalle
# --------------------------------------------------------------------------

def detail(rgb_lin: np.ndarray, p: Params) -> np.ndarray:
    h, w, _ = rgb_lin.shape
    lab = linear_to_lab(np.clip(rgb_lin, 0, 1))
    L = lab[..., 0]

    if p.clarity > 0:
        base = _gauss(L, max(3.0, min(h, w) * 0.022))
        # Se atenua en las altas luces para no ensuciar cremas y merengues.
        prot = 1.0 - _smoothstep(L, 84.0, 97.0)
        L = L + (L - base) * float(p.clarity) * prot

    if p.sharpen > 0:
        r = max(0.6, float(p.sharpen_radius) * (min(h, w) / 1000.0) * 1.15)
        d = L - _gauss(L, r)
        # Umbral suave: no amplifica el ruido de compresion de las zonas planas.
        L = L + d * float(p.sharpen) * _smoothstep(np.abs(d), 0.5, 2.2)

    lab[..., 0] = np.clip(L, 0, 100)
    return np.clip(lab_to_linear(lab), 0, 1)


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def enhance(img: Image.Image, p: Params) -> tuple[np.ndarray, dict]:
    """Devuelve (imagen sRGB en float 0-1, datos del revelado)."""
    img = img.convert("RGB")
    if abs(p.rotate) > 0.01:
        img = img.rotate(p.rotate, resample=Image.BICUBIC, expand=False)

    lin = srgb_to_linear(np.asarray(img).astype(np.float32) / 255.0)
    lin, info = white_balance(lin, p)
    lin, expinfo = auto_exposure(lin, p)
    info.update(expinfo)
    lin = tone(lin, p)
    lin = color(lin, p)
    lin = detail(lin, p)
    return linear_to_srgb(np.clip(lin, 0, 1)), info


def to_pil(rgb01: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(rgb01 * 255.0 + 0.5, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------
# Encuadre
# --------------------------------------------------------------------------

def subject_box(rgb01: np.ndarray) -> tuple[int, int, int, int]:
    """Ubica la torta para encuadrar. Solo se usa para recortar, no toca pixeles.

    La pieza es lo que tiene color o textura; la pared y el mantel son lisos y
    grises. Con eso alcanza para saber donde esta y encuadrar alrededor.
    """
    h, w, _ = rgb01.shape
    sc = 300 / max(h, w)
    sh, sw = max(32, int(round(h * sc))), max(32, int(round(w * sc)))
    small = np.asarray(to_pil(rgb01).resize((sw, sh), Image.LANCZOS)).astype(np.float32) / 255
    lab = linear_to_lab(srgb_to_linear(small))
    L, C = lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])
    Ls = ndi.gaussian_filter(L, 1.0, mode="nearest")
    m1 = ndi.uniform_filter(Ls, 7, mode="nearest")
    m2 = ndi.uniform_filter(Ls * Ls, 7, mode="nearest")
    tex = np.sqrt(np.maximum(m2 - m1 * m1, 0))

    borde = np.zeros((sh, sw), bool)
    b = max(2, int(min(sh, sw) * 0.04))
    borde[:b, :] = borde[-b:, :] = True
    borde[:, :b] = borde[:, -b:] = True
    m = ((C > np.percentile(C[borde], 85) + 6) |
         (tex > np.percentile(tex[borde], 95) + 1.5) |
         (L < np.percentile(L[borde], 30) - 12))
    m = ndi.binary_closing(m, np.ones((5, 5)), border_value=0)
    m = ndi.binary_opening(m, np.ones((3, 3)), border_value=0)
    lbl, n = ndi.label(m)
    if n:
        areas = ndi.sum(m, lbl, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[int(np.argmax(areas)) + 1] = True
        for i, ar in enumerate(areas, start=1):
            if ar > 0.02 * sh * sw:
                keep[i] = True
        m = keep[lbl]
    if not m.any():
        return int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)
    ys, xs = np.where(m)
    k = 1.0 / sc
    return (int(xs.min() * k), int(ys.min() * k),
            int((xs.max() + 1) * k), int((ys.max() + 1) * k))


def smart_crop(rgb01: np.ndarray, box: tuple[int, int, int, int], aspect: float,
               p: Params, margin: float = 0.10) -> np.ndarray:
    """Encuadra al aspecto pedido dejando la pieza entera y con aire.

    El recorte nunca sale del cuadro: si al ajustar la proporcion no entra, se
    achica y se corre hacia adentro. Rellenar el borde replicando pixeles deja
    unas rayas muy feas en los formatos altos, asi que preferimos ceder aire.
    """
    h, w, _ = rgb01.shape
    x0, y0, x1, y1 = box
    mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    x0, x1, y0, y1 = x0 - mx, x1 + mx, y0 - my * 1.2, y1 + my
    cx, cy, cw, ch = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0

    if cw / ch < aspect:
        cw = ch * aspect
    else:
        ch = cw / aspect
    cy += ch * 0.10 * float(np.clip(p.crop_bias_y, -1, 1))

    # Que quepa: se achica manteniendo la proporcion y despues se corre adentro.
    k = min(1.0, w / cw, h / ch)
    cw, ch = cw * k, ch * k
    cx = min(max(cx, cw / 2), w - cw / 2)
    cy = min(max(cy, ch / 2), h - ch / 2)

    bx0 = max(0, int(round(cx - cw / 2)))
    by0 = max(0, int(round(cy - ch / 2)))
    bx1 = min(w, bx0 + int(round(cw)))
    by1 = min(h, by0 + int(round(ch)))
    return rgb01[by0:by1, bx0:bx1]


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
    lab[..., 0] = np.clip(L + d * amount * _smoothstep(np.abs(d), 0.4, 2.0), 0, 100)
    return to_pil(linear_to_srgb(np.clip(lab_to_linear(lab), 0, 1)))
