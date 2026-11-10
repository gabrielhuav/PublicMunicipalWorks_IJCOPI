"""Compose the English national/state map and a comparison of four alternatives.

The maps are application screenshots; headings and a shared legend are drawn
conventionally. The four provenance alternatives remain separate editable SVGs.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT_DIR = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ("arialbd.ttf" if bold else "arial.ttf")), size)


def map_figure():
    captures = HERE / "capturas_figura5"
    evidence = json.loads((captures / "evidencia.json").read_text(encoding="utf-8"))
    assert evidence["language"] == "en" and not evidence["errors"]
    views = {view["view"]: view for view in evidence["views"]}
    assert views["national"]["visible"] == views["national"]["total"] == 253_346
    assert views["state_of_mexico"]["total"] == 21_335
    image = Image.new("RGB", (3600, 1310), "white")
    draw = ImageDraw.Draw(image)
    for x, name, title in [(20, "national", "A  Mexico"), (1820, "state_of_mexico", "B  State of Mexico")]:
        view = views[name]
        draw.text((x, 8), title, font=font(68, True), fill="#19364C")
        count = f"{view['visible']:,} georeferenced projects" if name == "national" else f"{view['visible']:,} of {view['total']:,} projects shown"
        draw.text((x, 85), count + " · 2024", font=font(60), fill="#435660")
        with Image.open(captures / view["image"]) as screenshot:
            panel = screenshot.convert("RGB").resize((1760, 978), Image.Resampling.LANCZOS)
        image.paste(panel, (x, 160))
        draw.rectangle((x, 160, x + 1759, 1137), outline="#C4CED5", width=3)
    draw.text((60, 1170), "Status", font=font(60, True), fill="#19364C")
    for x, label, colour in [(490, "Completed", "#2e7d32"), (1290, "In progress", "#1565c0"),
                              (2110, "Cancelled", "#c62828"), (2890, "Other status", "#7a7a7a")]:
        draw.ellipse((x, 1184, x + 38, 1222), fill=colour)
        draw.text((x + 58, 1170), label, font=font(60), fill="#18242B")
    draw.text((60, 1260), "Project locations · Generalised state boundaries and names: Natural Earth · Basemap: Esri", font=font(44), fill="#435660")
    output = HERE / "figura5_mexico_estado_mexico.png"
    image.save(output, optimize=True)
    print(output)


def alternatives_sheet():
    folder = HERE / "alternativas_figura4"
    image = Image.new("RGB", (3680, 1210), "#EEF3F6")
    draw = ImageDraw.Draw(image)
    names = {"A": "Guided process", "B": "Architecture groups", "C": "Data lanes", "D": "Outcomes first"}
    for index, letter in enumerate("ABCD"):
        x = 20 + (index % 2) * 1840
        y = 15 + (index // 2) * 600
        draw.text((x + 20, y), f"{letter} · {names[letter]}", font=font(50, True), fill="#19364C")
        with Image.open(folder / f"figura4_{letter}.png") as source:
            panel = source.convert("RGB").resize((1800, 480), Image.Resampling.LANCZOS)
        image.paste(panel, (x, y + 85))
    output = folder / "comparacion_A_B_C_D.png"
    image.save(output, optimize=True)
    print(output)


if __name__ == "__main__":
    map_figure()
    alternatives_sheet()
