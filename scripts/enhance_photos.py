#!/usr/bin/env python3
"""Procesa el catalogo de fotos y genera todas las piezas para web y redes.

Uso:
    python3 scripts/enhance_photos.py                      # todo el catalogo
    python3 scripts/enhance_photos.py --only torta-brownie-frutos-rojos
    python3 scripts/enhance_photos.py --only X --preview --outdir /tmp/prueba
    python3 scripts/enhance_photos.py --only X --set vibrance=0.34 --set clarity=0.3

Salidas (dentro de fotos/):
    master/       JPEG de maxima calidad, resolucion nativa, sin recortar
    web/          AVIF + WebP + JPEG en 4:5, 1:1 y 16:9, varios anchos
    social/       1080x1350 (feed), 1080x1080 (grilla), 1080x1920 (historias)
    comparativas/ antes y despues lado a lado
    manifest.json + galeria.html + snippet.html
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from photo_pipeline import (  # noqa: E402
    Params, enhance, to_pil, smart_crop, resize_to, post_resize_sharpen, subject_bbox,
)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = Path(__file__).resolve().parent / "photos.json"

# Ancho maximo que aceptamos ampliar respecto del original. Las fuentes vienen
# comprimidas por WhatsApp (720-960 px), forzar mas solo agrega papilla.
MAX_UPSCALE = 1.35

ASPECTS = {
    "4x5": 4 / 5,
    "1x1": 1.0,
    "16x9": 16 / 9,
    "9x16": 9 / 16,
}

WEB_WIDTHS = {
    "4x5": [400, 600, 800, 1000, 1200],
    "1x1": [400, 600, 800, 1000, 1200],
    "16x9": [800, 1200, 1600],
}

SOCIAL = {
    "instagram-feed-4x5": ("4x5", 1080, 1350),
    "instagram-grilla-1x1": ("1x1", 1080, 1080),
    "historias-9x16": ("9x16", 1080, 1920),
}


def save_variants(im: Image.Image, base: Path, formats=("avif", "webp", "jpg")) -> dict:
    base.parent.mkdir(parents=True, exist_ok=True)
    out = {}
    if "avif" in formats:
        f = base.with_suffix(".avif")
        im.save(f, "AVIF", quality=58, speed=4, subsampling="4:2:0")
        out["avif"] = f
    if "webp" in formats:
        f = base.with_suffix(".webp")
        im.save(f, "WEBP", quality=82, method=6)
        out["webp"] = f
    if "jpg" in formats:
        f = base.with_suffix(".jpg")
        im.save(f, "JPEG", quality=86, optimize=True, progressive=True, subsampling="4:2:0")
        out["jpg"] = f
    return out


def build_comparison(orig: Image.Image, done: Image.Image, out: Path,
                     height: int = 1000) -> None:
    def fit(im):
        w = int(round(im.width * height / im.height))
        return im.resize((w, height), Image.LANCZOS)
    a, b = fit(orig.convert("RGB")), fit(done.convert("RGB"))
    gap = 16
    canvas = Image.new("RGB", (a.width + b.width + gap, height), (255, 255, 255))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width + gap, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "JPEG", quality=88, optimize=True, progressive=True)


def process(entry: dict, outdir: Path, preview: bool, overrides: dict) -> dict:
    src = Path(entry["src"])
    if not src.is_absolute():
        src = ROOT / src
    slug = entry["slug"]
    params = Params().merged(entry.get("params", {})).merged(overrides)

    orig = Image.open(src)
    rgb, subj, info = enhance(orig, params)
    master = to_pil(rgb)

    result = {
        "slug": slug,
        "titulo": entry.get("titulo", slug),
        "alt": entry.get("alt", entry.get("titulo", slug)),
        "origen": {"archivo": src.name, "px": list(orig.size),
                   "kb": round(src.stat().st_size / 1024)},
        "diagnostico": info,
        "params": {k: v for k, v in params.__dict__.items()},
        "archivos": {},
    }

    # --- master -------------------------------------------------------------
    mdir = outdir / "master"
    mdir.mkdir(parents=True, exist_ok=True)
    mpath = mdir / f"{slug}.jpg"
    master.save(mpath, "JPEG", quality=95, optimize=True, progressive=True,
                subsampling="4:4:4")
    result["archivos"]["master"] = {
        "ruta": str(mpath.relative_to(outdir)), "px": list(master.size),
        "kb": round(mpath.stat().st_size / 1024),
    }

    # --- antes y despues ----------------------------------------------------
    cpath = outdir / "comparativas" / f"{slug}.jpg"
    build_comparison(orig, master, cpath)
    result["archivos"]["comparativa"] = str(cpath.relative_to(outdir))

    if preview:
        # Mascara de sujeto en verde sobre la foto: sirve para ver si el pipeline
        # esta separando bien la pieza del fondo.
        dbg = np.asarray(master).astype(np.float32) / 255.0
        dbg[..., 1] = np.clip(dbg[..., 1] * (1 - subj * 0.55) + subj * 0.55, 0, 1)
        dpath = outdir / "debug" / f"{slug}-mascara.jpg"
        dpath.parent.mkdir(parents=True, exist_ok=True)
        to_pil(dbg).save(dpath, "JPEG", quality=80, optimize=True)
        result["archivos"]["mascara"] = str(dpath.relative_to(outdir))
        return result

    crops: dict[str, np.ndarray] = {}
    for name, ratio in ASPECTS.items():
        crops[name] = smart_crop(rgb, subj, ratio, params)

    # --- web ----------------------------------------------------------------
    web = {}
    for aspect, widths in WEB_WIDTHS.items():
        c = crops[aspect]
        ch, cw = c.shape[:2]
        items = []
        for wpx in widths:
            if wpx / cw > MAX_UPSCALE:
                continue
            hpx = int(round(wpx / ASPECTS[aspect]))
            im = post_resize_sharpen(resize_to(c, wpx, hpx), 0.30 if wpx < cw else 0.42)
            files = save_variants(im, outdir / "web" / aspect / f"{slug}-{wpx}")
            items.append({
                "ancho": wpx, "alto": hpx,
                **{k: {"ruta": str(v.relative_to(outdir)),
                       "kb": round(v.stat().st_size / 1024, 1)} for k, v in files.items()},
            })
        web[aspect] = items
    result["archivos"]["web"] = web

    # --- redes --------------------------------------------------------------
    social = {}
    for name, (aspect, wpx, hpx) in SOCIAL.items():
        c = crops[aspect]
        im = post_resize_sharpen(resize_to(c, wpx, hpx), 0.34)
        d = outdir / "social" / name
        d.mkdir(parents=True, exist_ok=True)
        jf = d / f"{slug}.jpg"
        im.save(jf, "JPEG", quality=92, optimize=True, progressive=True,
                subsampling="4:2:0")
        wf = d / f"{slug}.webp"
        im.save(wf, "WEBP", quality=88, method=6)
        social[name] = {
            "jpg": {"ruta": str(jf.relative_to(outdir)),
                    "kb": round(jf.stat().st_size / 1024, 1)},
            "webp": {"ruta": str(wf.relative_to(outdir)),
                     "kb": round(wf.stat().st_size / 1024, 1)},
            "px": [wpx, hpx],
        }
    result["archivos"]["social"] = social
    return result


def picture_snippet(r: dict) -> str:
    items = r["archivos"]["web"]["4x5"]
    if not items:
        return ""
    def srcset(fmt):
        return ", ".join(f'/{i[fmt]["ruta"]} {i["ancho"]}w' for i in items if fmt in i)
    big = items[-1]
    return (
        '<picture>\n'
        f'  <source type="image/avif" srcset="{srcset("avif")}"\n'
        '          sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 380px">\n'
        f'  <source type="image/webp" srcset="{srcset("webp")}"\n'
        '          sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 380px">\n'
        f'  <img src="/{big["jpg"]["ruta"]}" width="{big["ancho"]}" height="{big["alto"]}"\n'
        f'       alt="{r["alt"]}" loading="lazy" decoding="async">\n'
        '</picture>'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=str(CATALOG))
    ap.add_argument("--outdir", default=str(ROOT / "fotos"))
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--preview", action="store_true",
                    help="solo master + comparativa (iteracion rapida)")
    ap.add_argument("--set", action="append", default=[],
                    help="override de parametro, ej: --set vibrance=0.3")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    entries = catalog["fotos"]
    if args.only:
        entries = [e for e in entries if e["slug"] in args.only]
        if not entries:
            print(f"sin coincidencias para {args.only}", file=sys.stderr)
            return 1

    overrides = {}
    for kv in args.set:
        k, _, v = kv.partition("=")
        overrides[k.strip()] = float(v)

    outdir = Path(args.outdir)
    if args.clean and outdir.exists() and not args.only:
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for e in entries:
        print(f"-> {e['slug']}", flush=True)
        results.append(process(e, outdir, args.preview, overrides))

    if not args.preview:
        total = sum(
            i["avif"]["kb"] for r in results for lst in r["archivos"]["web"].values()
            for i in lst if "avif" in i
        )
        manifest = {
            "generado_por": "scripts/enhance_photos.py",
            "fotos": results,
            "peso_total_avif_kb": round(total, 1),
        }
        (outdir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (outdir / "snippet.html").write_text(
            "\n\n".join(f"<!-- {r['titulo']} -->\n{picture_snippet(r)}" for r in results),
            encoding="utf-8")
    print(f"listo: {len(results)} fotos -> {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
