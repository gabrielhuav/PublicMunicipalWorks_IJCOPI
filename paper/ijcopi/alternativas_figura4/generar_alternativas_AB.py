"""Author two original, editable SVG figure alternatives; rasterise with MuPDF.

All values are loaded from the retained measurement evidence. The alternatives
do not alter the selected manuscript figure, the Word document or satellite maps.
"""

from html import escape
from pathlib import Path
import json
import pymupdf


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAVY = "#17394D"
INK = "#1D2D36"
MUTED = "#46616D"
BRONZE = "#9A6229"
SILVER = "#5B6E7A"
GOLD = "#967209"
TEAL = "#006D74"
W, H = 1800, 480


class Canvas:
    def __init__(self, title):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<title>{escape(title)}</title>',
            '<desc>Original vector diagram. Counts specify record units and are not additive across stages. Municipal context also loads directly from Silver to PostgreSQL. Official records remain separate from the synthetic demonstration.</desc>',
            f'<rect width="{W}" height="{H}" fill="white"/>',
        ]

    def rect(self, x, y, w, h, fill="white", stroke="#C8D5DD", radius=12, sw=2.2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def label(self, x, y, value, size=30, colour=INK, bold=False, anchor="middle"):
        self.parts.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{colour}">{escape(value)}</text>')

    def path(self, points, colour=NAVY, width=3.8, dash=None):
        d = "M " + " L ".join(f"{x} {y}" for x, y in points)
        dashed = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{dashed}/>')

    def arrow(self, points, colour=NAVY):
        self.path(points, colour)
        x, y = points[-1]
        px, py = points[-2]
        if x > px:
            triangle = [(x, y), (x-12, y-8), (x-12, y+8)]
        elif y < py:
            triangle = [(x, y), (x-8, y+12), (x+8, y+12)]
        else:
            triangle = [(x, y), (x-8, y-12), (x+8, y-12)]
        self.parts.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in triangle)}" fill="{colour}"/>')

    def badge(self, x, y, number, colour):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="19" fill="{colour}"/>')
        self.label(x, y+10, str(number), 30, "white", True)

    def icon(self, x, y, kind, colour):
        # Simple line icons are authored directly; they contain no external assets.
        if kind == "file":
            self.rect(x, y, 26, 32, "white", colour, 2, 2.5)
            self.path([(x+6,y+11),(x+20,y+11)], colour, 2.5)
            self.path([(x+6,y+19),(x+20,y+19)], colour, 2.5)
        elif kind == "grid":
            self.rect(x, y, 32, 30, "white", colour, 2, 2.5)
            self.path([(x,y+10),(x+32,y+10)], colour, 2.5)
            self.path([(x,y+20),(x+32,y+20)], colour, 2.5)
            self.path([(x+11,y),(x+11,y+30)], colour, 2.5)
            self.path([(x+22,y),(x+22,y+30)], colour, 2.5)
        elif kind == "chart":
            self.path([(x,y),(x,y+32),(x+33,y+32)], colour, 2.5)
            self.path([(x+7,y+25),(x+16,y+16),(x+23,y+20),(x+33,y+5)], colour, 3)
        else:
            self.parts.append(f'<ellipse cx="{x+17}" cy="{y+6}" rx="17" ry="6" fill="white" stroke="{colour}" stroke-width="2.5"/>')
            self.path([(x,y+6),(x,y+27)], colour, 2.5)
            self.path([(x+34,y+6),(x+34,y+27)], colour, 2.5)
            self.parts.append(f'<path d="M {x} {y+27} C {x} {y+35} {x+34} {y+35} {x+34} {y+27}" fill="none" stroke="{colour}" stroke-width="2.5"/>')

    def finish(self, name):
        svg = HERE / f"{name}.svg"
        png = HERE / f"{name}.png"
        svg.write_text("\n".join(self.parts + ["</svg>"]) + "\n", encoding="utf-8")
        document = pymupdf.open(svg)
        document[0].get_pixmap(matrix=pymupdf.Matrix(2,2), alpha=False).save(png)
        print(f"{name}: {W}×{H} SVG; {W*2}×{H*2} PNG")


def measures():
    folder = ROOT / "lakehouse/verificacion"
    lake = json.loads((folder / "evidencia_lago.json").read_text(encoding="utf-8"))["almacenamiento"]
    gold = json.loads((folder / "evidencia_oro.json").read_text(encoding="utf-8"))
    audit = json.loads((folder / "evidencia_auditoria.json").read_text(encoding="utf-8"))
    silver = lake["filas_plata"]
    assert sum(silver.values()) == 11_014_660
    assert silver["proyectos"] == 2_008_738
    assert silver["localidades"] == 189_432
    assert silver["cngmd_contratos"] == 4_950
    assert silver["rezago_municipal"] == 2_469
    assert gold["proyecto_ciclo"]["filas"] == 1_537_019
    assert audit["poblacion"]["folios"] == 967_495
    warehouse = lake["postgresql_tablas"]
    assert warehouse["fact_proyecto_ciclo"]["filas"] == 1_537_019
    assert warehouse["dim_proyecto_federal"]["filas"] == 1_157_395
    assert warehouse["dim_municipio"]["filas"] == 2_469
    return {
        "silver": f"{sum(silver.values()):,}",
        "reports": f"{silver['proyectos']:,}",
        "localities": f"{silver['localidades']:,}",
        "categories": f"{silver['cngmd_contratos']:,}",
        "municipalities": f"{silver['rezago_municipal']:,}",
        "years": f"{gold['proyecto_ciclo']['filas']:,}",
        "ids": f"{audit['poblacion']['folios']:,}",
        "versions": f"{warehouse['dim_proyecto_federal']['filas']:,}",
        "mb": f"{lake['capas']['bronce']['bytes']/1_000_000:,.1f}",
    }


def alternative_a(m):
    c = Canvas("Alternative A: sources above a horizontal data pipeline")
    c.badge(30, 22, 1, NAVY)
    c.label(62, 32, "Official sources", 32, NAVY, True, "start")
    sources = [
        (10, "SHCP · 2020–2025", f"{m['reports']} project-report rows", "6 ZIP/CSV files"),
        (460, "INEGI · Census 2020", f"{m['localities']} localities", "1 ZIP/CSV file"),
        (910, "INEGI · CNGMD 2023", f"{m['categories']} municipality–category rows", "2022 reference · 1 ZIP/CSV file"),
        (1360, "CONEVAL · Social lag 2020", f"{m['municipalities']} municipal index records", "1 CSV file · datos.gob.mx"),
    ]
    for x, heading, number, detail in sources:
        c.rect(x, 49, 430, 112, "#F3F7FA", "#C8D5DD")
        c.label(x+215, 80, heading, 31, NAVY, True)
        c.label(x+215, 115, number, 30)
        c.label(x+215, 148, detail, 30, MUTED)
        c.path([(x+215,161),(x+215,179)], "#6B8593", 3)
    c.path([(225,179),(1575,179)], "#6B8593", 3)
    c.arrow([(375,179),(375,229)], "#6B8593")
    headers = [
        (10, 2, "Store originals", BRONZE, "file"),
        (460, 3, "Align records", SILVER, "grid"),
        (910, 4, "Build indicators", GOLD, "chart"),
        (1360, 5, "Load warehouse", TEAL, "database"),
    ]
    for x, number, title, colour, icon in headers:
        c.badge(x+20,209,number,colour)
        c.label(x+52,220,title,32,NAVY,True,"start")
        c.icon(x+391,192,icon,colour)
        c.rect(x,230,430,178,"white","#C8D5DD")
        c.path([(x+12,231),(x+418,231)],colour,5)
    for a,b in [(440,460),(890,910),(1340,1360)]:
        c.arrow([(a,302),(b,302)])
    c.label(225,280,"9 official files",44,BRONZE,True)
    c.label(225,323,f"{m['mb']} MB · unchanged",32)
    c.label(225,365,"Bronze · SHA-256 verified",30,MUTED)
    c.label(675,280,m["silver"],46,NAVY,True)
    c.label(675,323,"rows · 10 harmonised tables",30)
    c.label(675,365,"Silver · Iceberg",30,MUTED)
    c.label(1125,280,m["years"],46,NAVY,True)
    c.label(1125,323,"project–year rows",32)
    c.label(1125,365,f"{m['ids']} project IDs · Gold",30,MUTED)
    c.label(1575,273,f"{m['years']} project–year facts",30,NAVY,True)
    c.label(1575,314,f"{m['versions']} historical versions",30)
    c.label(1575,355,f"{m['municipalities']} municipalities",31)
    c.label(1575,393,"3 additive PostgreSQL tables",30,MUTED)
    c.arrow([(675,408),(675,441),(1575,441),(1575,408)],TEAL)
    c.label(1125,432,"Municipal context",30,TEAL)
    c.label(900,471,"Official and synthetic records are kept separate. Counts are not additive across stages.",30,MUTED)
    c.finish("figura4_A")


def alternative_b(m):
    c = Canvas("Alternative B: grouped sources, lakehouse and warehouse")
    # Clear group boundaries distinguish provenance from processing and delivery.
    c.label(20,42,"Official sources",35,NAVY,True,"start")
    sources = [
        (70,"SHCP · 2020–2025 · 6 files",f"{m['reports']} project-report rows"),
        (150,"INEGI · Census 2020 · 1 file",f"{m['localities']} localities"),
        (230,"INEGI · CNGMD 2023 · 1 file",f"{m['categories']} municipality–category rows"),
        (310,"CONEVAL · Social lag 2020 · 1 file",f"{m['municipalities']} municipal index records"),
    ]
    for y,title,count in sources:
        c.rect(10,y,510,72,"#F3F7FA","#D2DDE4",8)
        c.label(28,y+28,title,30,NAVY,True,"start")
        c.label(28,y+61,count,30,INK,False,"start")
        c.path([(520,y+36),(550,y+36)],"#6B8593",3)
    c.label(265,414,"CNGMD 2023 reports on 2022.",30,MUTED)
    c.path([(550,106),(550,346)],"#6B8593",3)
    c.arrow([(550,227),(600,227)],"#6B8593")

    c.rect(580,10,820,393,"#F4F8FA","#D5E1E7",16)
    c.label(607,47,"Lakehouse",35,NAVY,True,"start")
    c.label(1378,47,"Originals → aligned data → analysis",30,MUTED,False,"end")
    columns = [(600,BRONZE,"Bronze"),(870,SILVER,"Silver"),(1140,GOLD,"Gold")]
    for x,colour,title in columns:
        c.rect(x,81,240,300,"white","#CBD8DF",10)
        c.path([(x+12,82),(x+228,82)],colour,5)
        c.label(x+120,123,title,34,colour,True)
    c.arrow([(840,226),(870,226)])
    c.arrow([(1110,226),(1140,226)])
    c.label(720,190,"9",56,BRONZE,True)
    c.label(720,227,"official files",31)
    c.label(720,292,f"{m['mb']} MB",34,NAVY,True)
    c.label(720,338,"Unchanged",30)
    c.label(720,369,"SHA-256 verified",30,MUTED)
    c.label(990,190,m["silver"],42,NAVY,True)
    c.label(990,227,"rows · 10 tables",30)
    c.label(990,292,"Common fields",30)
    c.label(990,338,"Source-linked",30)
    c.label(990,369,"Snapshots",30,MUTED)
    c.label(1260,190,m["years"],42,NAVY,True)
    c.label(1260,227,"project–years",30)
    c.label(1260,292,m["ids"],37,NAVY,True)
    c.label(1260,329,"project IDs",30)
    c.label(1260,369,"Parquet indicators",30,MUTED)

    c.label(1625,42,"Warehouse",35,TEAL,True)
    c.rect(1440,70,350,333,"#F1F8F7","#B5D4D2",14)
    c.arrow([(1380,226),(1440,226)])
    c.label(1615,121,"PostgreSQL · 3 tables",30,TEAL,True)
    c.label(1615,180,m["years"],45,NAVY,True)
    c.label(1615,216,"project–year facts",30)
    c.label(1615,276,m["versions"],41,NAVY,True)
    c.label(1615,311,"historical versions",30)
    c.label(1615,370,f"{m['municipalities']} municipalities",31,NAVY,True)
    c.arrow([(990,381),(990,438),(1615,438),(1615,403)],TEAL)
    c.label(1285,429,"Municipal context",30,TEAL)
    c.label(900,471,"Official and synthetic records are kept separate. Counts are not additive across stages.",30,MUTED)
    c.finish("figura4_B")


if __name__ == "__main__":
    values = measures()
    alternative_a(values)
    alternative_b(values)
