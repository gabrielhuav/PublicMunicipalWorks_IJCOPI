"""Restore the source imagery beneath the old yellow location annotations.

The immutable manuscript in SOURCE_COMMIT supplies the original screenshot.
Only two 37 x 37 pixel rectangles are restored from the exact archived Esri
tiles used in that screenshot. The tiles are registered to the screenshot;
ordinary bilinear scaling reproduces the browser's display, without generating
or inferring scenery. Red rings mark the tank, as requested by the author.
Dates, credits, all other photograph pixels and the 1529 x 731 frame are retained.

Requires Pillow and numpy. Run with the configured bundled Python runtime.
"""

import concurrent.futures
import hashlib
import io
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE_COMMIT = "5601412c9166881307f19bfe06c926deea54a523"
SOURCE_DOCX = "paper/ijcopi/Paper37_IJCOPI_v1_extendida.docx"
OUTPUT = HERE / "figura_ejemplo_satelite_limpia.png"
CACHE = Path(tempfile.gettempdir()) / "ijcopi_esri_source_tiles"
URL = ("https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/"
       "WMTS/1.0.0/default028mm/MapServer/tile/{version}/17/{row}/{col}")

# Original bytes of the published archive tiles, not a current basemap.
HASHES = {
    ("25521", 58291, 29390): "0cd2de8788f8b783c3e01d2aa1eac6ad46b4c6de4399ecd7ca0d848ec20fe602",
    ("25521", 58291, 29391): "5c5d7cf18f88f1db1673fdd94a8f7a6348c44fe4d666551bf669bf719310b2fa",
    ("25521", 58292, 29390): "9319f1fbb643b5988f5eb5982445e6a0831bbadfed5b564222e3898cbdcec6eb",
    ("25521", 58292, 29391): "9bebe8a739b617aa8127e6faa31d652ee797859bb38ea11434d8a54bb077f521",
    ("43291", 58291, 29390): "84fe0e639240f799fd88ab6ccc8e7a667a252e41be5da1bafe8454b83aaa1f34",
    ("43291", 58291, 29391): "034583c188bcdf4aed397925170b0f822866775371ece20878a7f3ac89db15ef",
    ("43291", 58292, 29390): "d64a43138f8a9022f13788fd5934cd28b53aef96f76e2547b0f43c2211ca1ec1",
    ("43291", 58292, 29391): "41f43ace03bfe85a1fd618853ef3f8906a8b64506127565eb149d89f0bffb9ab",
}

# Scale and subpixel screen coordinates determined by registration against a
# 220 x 220 pixel region around each annotation, excluding its 25-pixel radius.
# Mean absolute channel residuals are below 2.4/255 on both archived views.
ALIGNMENTS = [
    ("25521", (384, 330), (1.99952, 384.70, 329.75)),
    ("43291", (1143, 329), (1.99952, 1143.60, 329.75)),
]


def original_capture():
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Git is required to read the immutable source capture.")
    data = subprocess.check_output(
        [git, "-C", str(ROOT), "show", f"{SOURCE_COMMIT}:{SOURCE_DOCX}"])
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        rels = ET.fromstring(package.read("word/_rels/document.xml.rels"))
        target = next(r.attrib["Target"] for r in rels if r.attrib["Id"] == "rId40")
        capture = Image.open(io.BytesIO(package.read("word/" + target))).convert("RGB")
    assert capture.size == (1529, 731), capture.size
    return capture


def fetch_tile(key):
    version, row, col = key
    path = CACHE / f"esri_{version}_17_{row}_{col}.jpg"
    if not path.exists():
        payload = urllib.request.urlopen(
            URL.format(version=version, row=row, col=col), timeout=30).read()
        assert hashlib.sha256(payload).hexdigest() == HASHES[key], key
        path.write_bytes(payload)
    payload = path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == HASHES[key], key
    return key, Image.open(io.BytesIO(payload)).convert("RGB")


def main():
    CACHE.mkdir(exist_ok=True)
    original = original_capture()
    result = original.copy()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        tiles = dict(pool.map(fetch_tile, HASHES))

    lat, lon = 19.5083, -99.27495
    n = 2 ** 17
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat))
         + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    cx, cy = (x - 29390) * 256, (y - 58291) * 256
    changed = np.zeros((731, 1529), dtype=bool)

    for version, (px, py), (scale, offx, offy) in ALIGNMENTS:
        mosaic = Image.new("RGB", (512, 512))
        for row in [58291, 58292]:
            for col in [29390, 29391]:
                mosaic.paste(tiles[version, row, col],
                             ((col - 29390) * 256, (row - 58291) * 256))

        def render(area):
            return mosaic.transform(
                (area[2] - area[0], area[3] - area[1]), Image.Transform.AFFINE,
                (1 / scale, 0, cx + (area[0] - offx) / scale,
                 0, 1 / scale, cy + (area[1] - offy) / scale),
                resample=Image.Resampling.BILINEAR)

        check = (px - 110, py - 120, px + 110, py + 100)
        baseline = np.asarray(original.crop(check), dtype=float)[::3, ::3]
        restored = np.asarray(render(check), dtype=float)[::3, ::3]
        yy, xx = np.indices(baseline.shape[:2])
        mask = (xx * 3 - 110) ** 2 + (yy * 3 - 120) ** 2 > 25 ** 2
        error = np.mean(np.abs(restored[mask] - baseline[mask]))
        assert error < 2.5, (version, error)

        area = (px - 18, py - 18, px + 19, py + 19)
        result.paste(render(area), area[:2])
        changed[area[1]:area[3], area[0]:area[2]] = True
        print(f"Esri {version}: patch={area}, registration MAE={error:.4f}/255")

    draw = ImageDraw.Draw(result)
    for px, py in [(404, 300), (1160, 300)]:
        draw.ellipse((px - 25, py - 25, px + 25, py + 25),
                     outline=(255, 0, 0), width=5)
        changed[py - 25:py + 26, px - 25:px + 26] = True

    # No changes to imagery, dates, credits or layout outside those annotations.
    assert np.array_equal(np.asarray(original)[~changed], np.asarray(result)[~changed])
    result.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
