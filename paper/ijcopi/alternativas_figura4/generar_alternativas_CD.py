"""Author two English provenance alternatives as original editable SVGs."""

from html import escape
import json
from pathlib import Path

import pymupdf


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W, H = 1800, 480
INK = "#19384B"
TEXT = "#283B47"
SUB = "#455C69"
TEAL = "#087778"


def counts():
    e = json.loads((ROOT / "lakehouse/verificacion/evidencia_lago.json").read_text(encoding="utf-8"))
    g = json.loads((ROOT / "lakehouse/verificacion/evidencia_oro.json").read_text(encoding="utf-8"))
    a = json.loads((ROOT / "lakehouse/verificacion/evidencia_auditoria.json").read_text(encoding="utf-8"))
    s = e["almacenamiento"]
    p = s["filas_plata"]
    wh = s["postgresql_tablas"]
    c = dict(reports=p["proyectos"], localities=p["localidades"],
             categories=p["cngmd_contratos"], indices=p["rezago_municipal"],
             files=s["capas"]["bronce"]["objetos"],
             mb=s["capas"]["bronce"]["bytes"] / 1_000_000,
             silver=sum(p.values()), annual=g["proyecto_ciclo"]["filas"],
             ids=a["poblacion"]["folios"],
             facts=wh["fact_proyecto_ciclo"]["filas"],
             versions=wh["dim_proyecto_federal"]["filas"],
             municipalities=wh["dim_municipio"]["filas"])
    assert c["reports"] == 2_008_738 and c["categories"] == 4_950
    assert c["silver"] == 11_014_660 and c["annual"] == c["facts"] == 1_537_019
    return c


class Drawing:
    def __init__(self, title, description):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                      f'<title>{escape(title)}</title><desc>{escape(description)}</desc>',
                      '<rect width="1800" height="480" fill="white"/>']

    def rect(self, x, y, w, h, fill="white", stroke="#CBD6DC", radius=10, line=2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{line}"/>')

    def text(self, x, y, value, size=30, color=TEXT, bold=False, anchor="middle", max_width=None):
        assert size >= 30
        if max_width:
            width = pymupdf.get_text_length(value, fontname="hebo" if bold else "helv", fontsize=size)
            assert width < max_width, (value, width, max_width)
        self.parts.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(value)}</text>')

    def line(self, points, color=INK, width=3, dash=None):
        d = "M " + " L ".join(f"{x} {y}" for x, y in points)
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{extra}/>')

    def arrow(self, points, color=INK, width=3, dash=None):
        self.line(points, color, width, dash)
        x, y = points[-1]
        px, py = points[-2]
        if x > px:
            tri = [(x, y), (x - 11, y - 7), (x - 11, y + 7)]
        elif x < px:
            tri = [(x, y), (x + 11, y - 7), (x + 11, y + 7)]
        elif y > py:
            tri = [(x, y), (x - 7, y - 11), (x + 7, y - 11)]
        else:
            tri = [(x, y), (x - 7, y + 11), (x + 7, y + 11)]
        self.parts.append('<polygon points="' + " ".join(f"{a},{b}" for a,b in tri) + f'" fill="{color}"/>')

    def save(self, letter):
        svg = HERE / f"figura4_{letter}.svg"
        png = HERE / f"figura4_{letter}.png"
        svg.write_text("\n".join(self.parts + ["</svg>"]) + "\n", encoding="utf-8")
        doc = pymupdf.open(svg)
        doc[0].get_pixmap(alpha=False).save(png)
        print(f"{letter}: {W} x {H}, minimum text 30 px (8.04 pt at 6.7 inches)")


def variant_c(c):
    d = Drawing("Official data provenance in three lanes",
                "The source lane names four official datasets with their record grains. Nine original files enter Bronze, then Silver and Gold. Gold feeds warehouse project facts and history; Silver feeds municipal context directly. Counts at different grains are not additive.")
    d.rect(5, 5, 1790, 158, "#F5F8FA", "#E1E8ED")
    d.rect(5, 190, 1790, 132, "#F5F8FA", "#E1E8ED")
    d.rect(5, 371, 1790, 77, "#EFF8F7", "#C5DFDD")
    d.text(105, 76, "Official", 32, INK, True)
    d.text(105, 116, "sources", 32, INK, True)
    d.text(105, 244, "Traceable", 31, INK, True)
    d.text(105, 284, "layers", 31, INK, True)
    d.text(105, 404, "Warehouse", 30, TEAL, True)
    d.text(105, 439, "PostgreSQL", 30, TEAL)
    source_cards = [
        (215, 380, "SHCP · 2020–2025", f"{c['reports']:,}", "project-report rows", "Federally funded spending"),
        (610, 380, "INEGI · Census 2020", f"{c['localities']:,}", "localities", "Population context"),
        (1005, 380, "INEGI · CNGMD 2023", f"{c['categories']:,} records", "municipality × category", "2022 reference year"),
        (1400, 380, "CONEVAL · 2020", f"{c['indices']:,}", "municipal index records", "Social deprivation"),
    ]
    for x, w, title, number, grain, detail in source_cards:
        d.rect(x, 13, w, 144, "white", "#B9CAD5")
        d.text(x+w/2, 44, title, 30, INK, True, max_width=w-18)
        d.text(x+w/2, 80, number, 34, INK, True)
        d.text(x+w/2, 113, grain, 30, max_width=w-18)
        d.text(x+w/2, 146, detail, 30, SUB, max_width=w-18)
        d.line([(x+w/2,157),(x+w/2,176)], "#79909F", 2.5)
    d.line([(405,176),(1590,176)], "#79909F", 2.5)
    d.arrow([(435,176),(435,198)], "#79909F", 2.5)

    layer_cards = [(215,440,"Bronze", "#A56825"), (700,480,"Silver", "#657784"), (1225,555,"Gold", "#967100")]
    for x,w,title,color in layer_cards:
        d.rect(x,198,w,116,"white",color)
        d.text(x+w/2,230,title,32,color,True)
    d.text(435,268,f"{c['files']} original files · {c['mb']:,.1f} MB",30,max_width=420)
    d.text(435,304,"Unchanged bytes · SHA-256",30,SUB,max_width=420)
    d.text(940,268,f"{c['silver']:,} rows · 10 tables",30,max_width=460)
    d.text(940,304,"Harmonised records · Iceberg",30,SUB,max_width=460)
    d.text(1502.5,268,f"{c['annual']:,} project–year rows",32,INK,True,max_width=535)
    d.text(1502.5,304,f"{c['ids']:,} project IDs · Parquet",30,SUB,max_width=535)
    d.arrow([(655,256),(700,256)])
    d.arrow([(1180,256),(1225,256)])

    # Context does not pass through Gold. Place municipalities first to avoid crossing.
    d.arrow([(940,314),(940,354),(435,354),(435,373)],TEAL,3)
    d.text(685,347,"Municipal context",30,TEAL)
    d.arrow([(1502.5,314),(1502.5,373)],INK,3)
    d.text(1590,355,"Projects",30,INK,anchor="start")
    d.line([(660,381),(660,438)],"#BCD2D2",2)
    d.line([(1175,381),(1175,438)],"#BCD2D2",2)
    d.text(435,404,f"{c['municipalities']:,}",34,TEAL,True)
    d.text(435,439,"municipalities",30)
    d.text(917.5,404,f"{c['facts']:,}",34,TEAL,True)
    d.text(917.5,439,"project–year facts",30)
    d.text(1482.5,404,f"{c['versions']:,}",34,TEAL,True)
    d.text(1482.5,439,"historical project versions",30,max_width=570)
    d.text(900,477,"Official and synthetic data are separate. Counts are not additive.",30,SUB)
    d.save("C")


def variant_d(c):
    d = Drawing("From official evidence to usable project records",
                "Three reader-oriented zones show the evidence, traceable preparation and usable results. The warehouse holds annual facts, historical project versions and municipal context. The dashed line shows municipal context entering PostgreSQL directly from Silver. Official and synthetic records remain separate; counts at different grains are not additive.")
    d.text(285,39,"1  Official evidence",34,INK,True)
    d.text(810,39,"2  Traceable layers",34,INK,True)
    d.text(1435,39,"3  Usable results",34,TEAL,True)
    rows = [
        (66,77,"SHCP · 2020–2025",f"{c['reports']:,} project-report rows",None),
        (151,77,"INEGI · Census 2020",f"{c['localities']:,} localities",None),
        (236,110,"INEGI · CNGMD 2023",f"{c['categories']:,} records · reference 2022","municipality × category"),
        (354,77,"CONEVAL · Social lag 2020",f"{c['indices']:,} municipal index records",None),
    ]
    for y,h,heading,detail,third in rows:
        d.rect(20,y,520,h,"#F4F7FA","#CED9E1",8)
        d.text(40,y+31,heading,30,INK,True,"start",max_width=480)
        d.text(40,y+66,detail,30,TEXT,False,"start",max_width=480)
        if third:d.text(40,y+100,third,30,SUB,False,"start",max_width=480)
        d.line([(540,y+h/2),(557,y+h/2)],"#79909F",2.5)
    d.line([(557,104.5),(557,392.5)],"#79909F",2.5)
    d.arrow([(557,114),(580,114)],"#79909F",2.5)

    layers=[(66,"Original files · Bronze","#A56825",f"{c['files']} files · {c['mb']:,.1f} MB"),
            (184,"Aligned records · Silver","#657784",f"{c['silver']:,} rows · 10 tables"),
            (302,"Annual records · Gold","#967100",f"{c['annual']:,} project–years")]
    for y,title,color,number in layers:
        d.rect(580,y,460,94,"white",color,10,2.5)
        d.text(810,y+34,title,31,color,True,max_width=430)
        d.text(810,y+77,number,31,INK,True,max_width=430)
    d.arrow([(810,160),(810,184)])
    d.arrow([(810,278),(810,302)])

    d.rect(1090,66,680,76,"#E8F4F3","#B6D9D5")
    d.text(1110,120,f"{c['ids']:,}",49,TEAL,True,"start")
    d.text(1420,117,"distinct project IDs",31,TEAL,False,"start",max_width=340)
    d.rect(1090,184,680,220,"white","#6DA7A3",10,2.5)
    d.text(1430,218,"PostgreSQL warehouse · 3 tables",30,TEAL,True,max_width=650)
    d.line([(1110,233),(1750,233)],"#D5E6E4",2)
    d.text(1110,272,f"{c['facts']:,}",40,TEAL,True,"start")
    d.text(1370,271,"project–year facts",31,TEXT,False,"start",max_width=370)
    d.text(1110,326,f"{c['versions']:,}",40,TEAL,True,"start")
    d.text(1370,325,"historical project versions",31,TEXT,False,"start",max_width=370)
    d.text(1110,383,f"{c['municipalities']:,}",40,TEAL,True,"start")
    d.text(1370,382,"municipalities",31,TEXT,False,"start",max_width=370)

    # Direct context branch passes above the output box and enters on its right.
    d.arrow([(1040,231),(1055,231),(1055,180),(1790,180),(1790,373),(1770,373)],TEAL,3,"7 5")
    d.text(1410,174,"Municipal context from Silver",30,TEAL)
    # Gold project data reach the warehouse separately, below the direct branch.
    d.arrow([(1040,349),(1068,349),(1068,273),(1090,273)],INK,3)
    d.text(810,435,"SHA-256 provenance",30,SUB)
    d.text(900,477,"Official and synthetic data are separate. Counts are not additive.",30,SUB)
    d.save("D")


if __name__ == "__main__":
    values=counts()
    variant_c(values)
    variant_d(values)
