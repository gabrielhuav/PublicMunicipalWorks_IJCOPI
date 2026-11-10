"""Compose the English national/state map and a comparison of four alternatives.

The maps are application screenshots; headings and a shared legend are drawn
conventionally. The four provenance alternatives remain separate editable SVGs.
"""
from pathlib import Path
import json
import math
from urllib.parse import parse_qs, urlsplit
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT_DIR = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ("arialbd.ttf" if bold else "arial.ttf")), size)


def locator_rectangle(overview, detail, panel):
    """Project the detail viewport into the overview, using the recorded cameras.

    Captures use 900 × 500 CSS pixels at deviceScaleFactor=2. The rectangle
    represents B's map viewport, not an administrative boundary or spatial filter.
    """
    def camera(view):
        return tuple(map(float, parse_qs(urlsplit(view["url"]).query)["c"][0].split(",")))

    def world(lat, lon, zoom):
        size = 256 * 2 ** zoom
        sine = math.sin(math.radians(lat))
        return (lon + 180) / 360 * size, (0.5 - math.log((1 + sine) / (1 - sine)) / (4 * math.pi)) * size

    lat_a, lon_a, zoom_a = camera(overview)
    lat_b, lon_b, zoom_b = camera(detail)
    factor = 2 ** (zoom_b - zoom_a)
    assert factor > 1
    ax, ay = world(lat_a, lon_a, zoom_a)
    bx, by = world(lat_b, lon_b, zoom_a)
    x, y, width, height = panel
    cx = x + width / 2 + (bx - ax) * width / 900
    cy = y + height / 2 + (by - ay) * height / 500
    half_width, half_height = width / (2 * factor), height / (2 * factor)
    return (cx - half_width, cy - half_height, cx + half_width, cy + half_height), factor


def map_figure():
    captures = HERE / "capturas_figura5"
    evidence = json.loads((captures / "evidencia.json").read_text(encoding="utf-8"))
    assert evidence["language"] == "en" and not evidence["errors"]
    views = {view["view"]: view for view in evidence["views"]}
    assert views["national"]["visible"] == views["national"]["total"] == 253_346
    assert views["state_of_mexico"]["total"] == 21_335
    image = Image.new("RGB", (3600, 1310), "white")
    draw = ImageDraw.Draw(image)
    locator, zoom_factor = locator_rectangle(views["national"], views["state_of_mexico"], (20, 160, 1760, 978))
    accent = "#6D4091"
    for x, name, title in [(20, "national", "A  Mexico · Overview"),
                           (1820, "state_of_mexico", f"B  State of Mexico · {zoom_factor:g}× zoom")]:
        view = views[name]
        draw.text((x, 8), title, font=font(68, True), fill="#19364C")
        count = f"{view['visible']:,} georeferenced projects" if name == "national" else f"{view['visible']:,} of {view['total']:,} projects shown"
        draw.text((x, 85), count + " · 2024", font=font(60), fill="#435660")
        with Image.open(captures / view["image"]) as screenshot:
            assert screenshot.size == (1800, 1000), "Recheck locator projection for a different capture size"
            panel = screenshot.convert("RGB").resize((1760, 978), Image.Resampling.LANCZOS)
        image.paste(panel, (x, 160))
        draw.rectangle((x, 160, x + 1759, 1137), outline="#C4CED5", width=3)
    # One routed arrow stays mostly over the Gulf, leaving state names and
    # attribution legible. The matching outline identifies the enlarged panel.
    x0, y0, x1, y1 = locator
    route = [(x1, y0), (1360, 630), (1800, 630)]
    draw.line(route, fill="white", width=15, joint="curve")
    draw.line(route, fill=accent, width=6, joint="curve")
    draw.rectangle((1820, 160, 3579, 1137), outline=accent, width=7)
    draw.polygon([(1820, 630), (1782, 609), (1782, 651)], fill=accent)
    draw.rectangle(locator, outline="white", width=15)
    draw.rectangle(locator, outline=accent, width=6)
    draw.rounded_rectangle((1245, 450, 1760, 595), radius=16, fill="#FFFFFF")
    draw.text((1502, 462), "Zoom to", font=font(58, True), fill=accent, anchor="mt")
    draw.text((1502, 535), "State of Mexico", font=font(52), fill="#19364C", anchor="mt")
    draw.text((60, 1170), "Status", font=font(60, True), fill="#19364C")
    for x, label, colour in [(490, "Completed", "#2e7d32"), (1290, "In progress", "#1565c0"),
                              (2110, "Cancelled", "#c62828"), (2890, "Other status", "#7a7a7a")]:
        draw.ellipse((x, 1184, x + 38, 1222), fill=colour)
        draw.text((x + 58, 1170), label, font=font(60), fill="#18242B")
    draw.text((60, 1260), "Project locations · Generalised state boundaries and names: Natural Earth · Basemap: Esri", font=font(44), fill="#435660")
    output = HERE / "figura5_mexico_estado_mexico.png"
    image.save(output, optimize=True)
    (captures / "acercamiento.json").write_text(json.dumps({
        "overview_camera": views["national"]["url"],
        "detail_camera": views["state_of_mexico"]["url"],
        "locator_rectangle_pixels": [round(v, 3) for v in locator],
        "linear_zoom_factor": zoom_factor,
        "meaning": "Outline in A locates the viewport of B; B retains its State of Mexico filter.",
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
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
