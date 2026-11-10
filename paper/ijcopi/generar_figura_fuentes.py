"""Regenerate the author's selected C diagram as the canonical Figure 4.

The editable source and its measured counts live with the four alternatives.
All drawing and rasterisation use conventional SVG and MuPDF rendering.
"""
from pathlib import Path
import runpy
from shutil import copyfile


HERE = Path(__file__).resolve().parent


def main():
    alternatives = HERE / "alternativas_figura4"
    runpy.run_path(str(alternatives / "generar_alternativas_CD.py"), run_name="__main__")
    for extension in ("svg", "png"):
        output = HERE / f"figura_fuentes_oficiales.{extension}"
        copyfile(alternatives / f"figura4_C.{extension}", output)
        print(output)


if __name__ == "__main__":
    main()
