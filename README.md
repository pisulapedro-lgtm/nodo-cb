# Fotos de tortas — Cucina di Marce

Revelado y export de las fotos de producto para la web y las redes.

Las fotos originales son de celular y llegaron comprimidas por WhatsApp: oscuras,
con una dominante de color distinta en cada una y con poca definicion. El
procesamiento corrige **luz, color y nitidez**, y nada mas. La escena queda como
fue tomada: la pared, el mantel y las sombras no se tocan.

## Que hay en `fotos/`

| Carpeta | Que es | Para que |
|---|---|---|
| `originales/` | las fotos como llegaron | respaldo, no se tocan |
| `master/` | JPEG calidad 95, resolucion nativa, sin recortar | archivo de trabajo |
| `web/` | AVIF + WebP + JPEG en 4:5, 1:1 y 16:9, de 400 a 1600 px | la web |
| `social/` | 1080x1350 feed, 1080x1080 grilla, 1080x1920 historias | Instagram y Facebook |
| `comparativas/` | antes y despues lado a lado | revisar el trabajo |
| `galeria.html` | las diez comparativas en una pagina | revisar todo de un vistazo |
| `manifest.json` | rutas, medidas y peso de cada archivo | armar la web |
| `snippet.html` | el `<picture>` con `srcset` ya escrito | pegar en la web |

## Como se ve en la web

En `snippet.html` esta el bloque listo para cada foto. El navegador elige solo el
formato y la medida que le sirve: AVIF si puede, si no WebP, y JPEG como ultimo
recurso. Una tarjeta de catalogo en 4:5 a 800 px pesa unos **88 kB en AVIF**
contra 194 kB del JPEG equivalente.

```html
<picture>
  <source type="image/avif" srcset="/web/4x5/torta-merengue-dorada-400.avif 400w, ..." sizes="...">
  <source type="image/webp" srcset="/web/4x5/torta-merengue-dorada-400.webp 400w, ..." sizes="...">
  <img src="/web/4x5/torta-merengue-dorada-1200.jpg" width="1200" height="1500"
       alt="..." loading="lazy" decoding="async">
</picture>
```

Los `alt` ya estan escritos en `scripts/photos.json`, descriptivos y en castellano.

## Volver a generar

```bash
pip install pillow numpy scipy
python3 scripts/enhance_photos.py                      # todo el catalogo
python3 scripts/enhance_photos.py --only torta-brownie-frutos-rojos
python3 scripts/enhance_photos.py --only X --preview --outdir /tmp/prueba
python3 scripts/enhance_photos.py --only X --set contrast=0.08 --set vibrance=0.3
```

`--preview` genera solo el master y la comparativa: sirve para probar ajustes
rapido, sin esperar los 39 archivos de cada foto.

## Agregar fotos nuevas

1. Copiar la foto a `fotos/originales/` con un nombre descriptivo en minusculas
   y con guiones (`torta-limon-merengue.jpg`). Ese nombre es la URL.
2. Agregar la entrada en `scripts/photos.json` con su titulo y su texto `alt`.
3. Correr `python3 scripts/enhance_photos.py --only <slug> --preview` y mirar la
   comparativa.
4. Si hace falta, ajustar en `params` y repetir. Si esta bien, correr sin
   `--preview`.

## Los ajustes

Todo vive en `scripts/photo_pipeline.py`, en la clase `Params`. Los valores por
defecto ya dan un resultado publicable; en `photos.json` solo se anota lo que
cada foto pide distinto. Los que mas se usan:

- `white_target` — el nivel al que se lleva el blanco de la escena. **Es el que
  empareja la serie**: todas las fotos terminan con la misma luz. Cambiarlo en
  una sola foto la saca del conjunto.
- `contrast`, `shadow_lift` — si una torta de chocolate queda muy cerrada,
  subir `shadow_lift` y bajar `contrast`.
- `vibrance` — sube el color apagado sin tocar lo que ya esta saturado.
- `clarity`, `sharpen` — definicion. Ojo con pasarse: las fuentes son de 720 a
  960 px y el ruido de compresion se nota enseguida.
- `crop_bias_y` — corre el encuadre para arriba o para abajo si un topper alto
  queda justo.

## Limites

Las fuentes miden entre 720x1280 y 960x1280. El export nunca amplia mas de 1.35x
(`MAX_UPSCALE`), asi que las medidas que no se pueden alcanzar con calidad
simplemente no se generan. Para fotos nuevas conviene sacarlas del celular sin
mandarlas por WhatsApp: con el archivo original se puede llegar a 2000 px y las
tarjetas grandes ganan bastante.
