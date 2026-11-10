"""Replay the authorised revision on the latest reviewed Word manuscript.

The historical extender_v1.py in PublicMunicipalWorks_DWH predates the editorial
corrections of 9 November. This revision therefore starts from the reviewed
manuscript in commit 5601412, preserving those corrections and native equations.
Run from any directory with the bundled Python runtime (python-docx required).
The frozen v0 is never written.
"""

from copy import deepcopy
from io import BytesIO
from pathlib import Path
import argparse
import re
import subprocess

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Pt
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE_COMMIT = "5601412c9166881307f19bfe06c926deea54a523"
SOURCE_FILE = "paper/ijcopi/Paper37_IJCOPI_v1_extendida.docx"
FIGURE = HERE / "figura_fuentes_oficiales.png"
MAP_FIGURE = HERE / "figura5_mexico_estado_mexico.png"
SATELLITE = HERE / "figura_ejemplo_satelite_corregida.png"
CLEAN_SATELLITE = HERE / "figura_ejemplo_satelite_limpia.png"
OUTPUT = HERE / "Paper37_IJCOPI_v1_extendida.docx"
REPOSITORY = "https://github.com/gabrielhuav/PublicMunicipalWorks_IJCOPI"

FUTURE = (
    "Future work will assess changes in residents' perceptions through paired surveys "
    "before and after selected public works, measuring satisfaction, perceived usefulness "
    "and accessibility. An LLM-based agent could analyse anonymised responses alongside "
    "official records and dated visual evidence. Its interpretations would be evaluated "
    "against independent human coding using agreement measures and review of disagreements. "
    "Sampling and attrition would be documented. "
    "LLM-simulated respondents could support questionnaire design and agent testing; these "
    "experiments would be labelled as simulations and would not substitute for evidence "
    "from real residents."
)

SOURCES = (
    "Figure 4 traces nine official files: federal spending, 2020–2025 (SHCP, n.d.); "
    "Census 2020 localities (INEGI, n.d.-a); CNGMD 2023 procurement (INEGI, n.d.-b); "
    "and municipal deprivation (CONEVAL, n.d.). Ingestion checks manifest file sizes "
    "and SHA-256 hashes (2,136.3 MB in total), stopping on mismatches."
)

LAYERS = (
    "Bronze keeps source bytes in S3-compatible SeaweedFS (Lu, 2025); R2 was not "
    "benchmarked. PyIceberg (Apache Software Foundation, 2025) builds ten Iceberg tables "
    "in silver (11.0 million rows; about 200 s), partitioned by year and state where "
    "applicable. Annual snapshots preserve source hashes for historical reads. DuckDB "
    "(DuckDB Foundation, 2025) queries Iceberg directly to produce gold Parquet datasets, "
    "one per SQL file, without Spark."
)

SITE = (
    "The static map and queries (Fig. 5; Hurtado Avilés, 2026) publish six SQL-result "
    "layers, separate from the conference demonstration. Points are partitioned by state; "
    "details by municipality. All Mexico combines 32 point files, retaining filters "
    "across country/state views. Grouped overviews retain every record and preserve "
    "status shares. Verification reruns queries and fails on byte discrepancies. "
    "Municipalities and projects identify source files and SHA-256. Of 253,346 "
    "georeferenced records in 2024, 158,919 carry agency-reported links (37,682 include "
    "PDF; 45 an image), preserved in an annex. Status, flags and evidence can be filtered; "
    "search includes OpenStreetMap geocoding. Esri comparisons use the last pre-project "
    "release and the latest. State display uses nearest municipal seats rather than "
    "polygons and reports omissions. A national outline works offline."
)

CAPTION = (
    "Fig. 4. Official data provenance and warehouse integration. SHCP: Ministry of "
    "Finance and Public Credit; INEGI: National Institute of Statistics and Geography; "
    "CNGMD: National Census of Municipal Governments and Territorial Demarcations of "
    "Mexico City (2023 edition; 2022 data); CONEVAL: National "
    "Council for the Evaluation of Social Development Policy. SHA-256: Secure Hash "
    "Algorithm with a 256-bit digest; MB: megabytes (one million bytes); IDs: identifiers."
)


def text(element):
    return "".join(n.text or "" for n in element.iter(qn("w:t")))


def find(doc, prefix):
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    assert len(matches) == 1, (prefix, len(matches))
    return matches[0]


def replace_text(paragraph, value):
    """Keep the paragraph properties; all replacement prose is highlighted."""
    rpr = next((deepcopy(r._r.rPr) for r in paragraph.runs if r._r.rPr is not None), None)
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    run = paragraph.add_run(value)
    if rpr is not None:
        run._r.insert(0, rpr)
    run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    frozen = HERE / "Paper37_IJCOPI_v0_fiel.docx"
    frozen_bytes = frozen.read_bytes()
    source = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_FILE}"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    doc = Document(BytesIO(source))
    equations = len(doc.element.xpath(".//m:oMath"))
    assert equations == 7, equations
    assert FIGURE.is_file(), FIGURE

    # The clean source restores the pixels hidden by the old yellow rings from
    # the same official Esri imagery and retains only the user's red tank rings.
    # No generated or interpolated scenery is used to remove the annotation.
    old_caption = find(doc, "Fig. 5.")
    satellite_paragraph = old_caption._p.getprevious()
    assert CLEAN_SATELLITE.is_file(), CLEAN_SATELLITE
    with Image.open(CLEAN_SATELLITE) as clean:
        assert clean.size == (1529, 731), clean.size
    SATELLITE.write_bytes(CLEAN_SATELLITE.read_bytes())
    # Keep the existing placement and frame, and replace the image relationship.
    new_id, _ = doc.part.get_or_add_image(str(SATELLITE))
    satellite_paragraph.xpath(".//a:blip")[0].set(qn("r:embed"), new_id)

    # Move Roberto's existing name and affiliation runs intact to last place.
    authors = doc.paragraphs[1]
    assert "Gabriel Hurtado Avilés1, Roberto Eswart Zagal Flores1, Uriel" in authors.text
    runs = list(authors._p.findall(qn("w:r")))
    index = next(i for i, run in enumerate(runs) if text(run) == "Roberto Eswart Zagal Flores")
    for run in runs[index:index + 3]:
        authors._p.remove(run)
    for run in (deepcopy(runs[index + 2]), runs[index], runs[index + 1]):
        authors._p.append(run)
    assert authors.text.rstrip().endswith("Roberto Eswart Zagal Flores1")

    # One line per author, in the same order as the author block.
    replace_text(doc.paragraphs[3], (
        "ghurtadoa@ipn.mx, gabrielhuav@gmail.com\n"
        "ugonzalezc2400@alumno.ipn.mx, gonzalezcasianouriel@gmail.com\n"
        "mmaldonadom2200@alumno.ipn.mx, marcotuliomm.s45@gmail.com\n"
        "rzagalf@ipn.mx"
    ))
    assert doc.paragraphs[3].text.splitlines()[-1] == "rzagalf@ipn.mx"

    # Cite the project's main URL; retain the evaluated version in Availability.
    reference = find(doc, "Hurtado Avilés, G. (2026).")
    for node in reference._p.iter(qn("w:t")):
        if node.text:
            node.text = node.text.replace(" (Commit 661e7da)", "")
            if node.text.startswith(REPOSITORY + "/tree/"):
                node.text = REPOSITORY
    for link in reference._p.findall(qn("w:hyperlink")):
        link.set(qn("r:id"), doc.part.relate_to(REPOSITORY, RT.HYPERLINK, is_external=True))
    availability = find(doc, "The lakehouse code, queries, projections and measurement outputs")
    availability.add_run(
        " The reported measurements correspond to code commit 661e7da."
    ).font.highlight_color = WD_COLOR_INDEX.YELLOW

    # Renumber existing figures 4 and 5 before adding the new provenance figure.
    for paragraph in doc.paragraphs:
        for node in paragraph._p.iter(qn("w:t")):
            if node.text:
                node.text = re.sub(r"Fig\. ([45])", lambda m: f"Fig. {int(m[1]) + 1}", node.text)
                node.text = node.text.replace(
                    "shows its point in two releases of Esri's archive",
                    "compares the site in two releases of Esri's archive",
                )
                node.text = node.text.replace(
                    "Fig. 5 opens one flagged project:", "The example project is"
                )
    for prop in doc.element.xpath(".//wp:docPr"):
        if prop.get("name") in ("Figure 4", "Figure 5"):
            old = int(prop.get("name").split()[-1])
            prop.set("name", f"Figure {old + 1}")
    replace_text(find(doc, "Fig. 6."), (
        "Fig. 6. Esri captures of 21 January 2016 (left) and 10 February 2025 (right) "
        "(Esri, 2017, 2026). Red circles mark the tank location before and after "
        "the reported construction period."
    ))
    map_caption = find(doc, "Fig. 5.")
    map_picture = map_caption._p.getprevious()
    assert MAP_FIGURE.is_file(), MAP_FIGURE
    map_id, _ = doc.part.get_or_add_image(str(MAP_FIGURE))
    map_picture.xpath(".//a:blip")[0].set(qn("r:embed"), map_id)
    with Image.open(MAP_FIGURE) as image:
        map_width = int(Inches(6.7))
        map_height = round(map_width * image.height / image.width)
    for extent in map_picture.xpath(".//wp:extent | .//a:xfrm/a:ext"):
        extent.set("cx", str(map_width))
        extent.set("cy", str(map_height))
    map_picture.xpath(".//wp:docPr")[0].set("descr", (
        "English application views of all 253,346 georeferenced projects reported "
        "for 2024 in Mexico and a closer view of the State of Mexico with 20,552 "
        "of 21,335 records. The state view omits 783 records under the nearest-seat "
        "approximation. Both panels use the same four project-status colours."
    ))
    replace_text(map_caption, (
        "Fig. 5. Projects in 2024. (A) All 253,346 records grouped by location: sectors "
        "show status shares; size is logarithmic. (B) 20,552 of 21,335 State of Mexico "
        "records as individual points (783 omitted by nearest-seat approximation). "
        "Basemap: Esri (n.d.)."
    ))

    sources = find(doc, "The layer starts from nine files")
    replace_text(sources, SOURCES)
    layers = find(doc, "The layers follow the bronze")
    replace_text(layers, LAYERS)
    replace_text(find(doc, "The results are published as a static map"), SITE)

    # The heading supplies the spacing after Table 3; remove the redundant empty
    # paragraph so the extra contact line does not force a sixteenth page.
    properties = find(doc, "9.2 Lakehouse Properties")
    spacer = properties._p.getprevious()
    assert spacer.tag == qn("w:p") and not text(spacer).strip()
    spacer.getparent().remove(spacer)
    # Compact only the extension's Table 3 padding; keep its font and every
    # measured value unchanged while making room for the acronym definitions.
    analytical_table = doc.tables[-1]
    assert analytical_table.cell(0, 0).text == "Question"
    for row in analytical_table.rows:
        for cell in row.cells:
            margins = cell._tc.get_or_add_tcPr().find(qn("w:tcMar"))
            assert margins is not None
            for edge in ("top", "bottom"):
                margins.find(qn("w:" + edge)).set(qn("w:w"), "40")
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(1)

    # Full-width image and caption remain together, with the required yellow frame.
    picture = doc.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.keep_with_next = True
    picture.paragraph_format.space_before = Pt(3)
    picture.paragraph_format.space_after = Pt(3)
    shape = picture.add_run().add_picture(str(FIGURE), width=Inches(6.7))
    shape._inline.docPr.set("name", "Figure 4")
    shape._inline.docPr.set("descr", (
        "Five steps show official sources, nine original files, 11,014,660 rows in "
        "ten harmonised tables, 1,537,019 analytical project-year records and three "
        "PostgreSQL tables with 1,537,019 facts, 1,157,395 historical project versions "
        "and 2,469 municipalities. Counts have distinct units and are not additive "
        "across stages. Municipal context also flows directly from silver to the "
        "warehouse. Official and synthetic records remain separate."
    ))
    sppr = shape._inline.xpath(".//pic:spPr")[0]
    border = OxmlElement("a:ln")
    border.set("w", "38100")
    fill = OxmlElement("a:solidFill")
    colour = OxmlElement("a:srgbClr")
    colour.set("val", "FFFF00")
    fill.append(colour)
    border.append(fill)
    sppr.append(border)
    caption = doc.add_paragraph(style="IJCOPI Caption")
    caption.paragraph_format.keep_together = True
    caption.add_run(CAPTION).font.highlight_color = WD_COLOR_INDEX.YELLOW
    layers._p.addnext(picture._p)
    picture._p.addnext(caption._p)

    future = find(doc, "The extension implements the conference lakehouse")
    future.add_run(" " + FUTURE).font.highlight_color = WD_COLOR_INDEX.YELLOW
    assert len(doc.element.xpath(".//m:oMath")) == equations
    assert len(doc.inline_shapes) == 7
    assert frozen.read_bytes() == frozen_bytes
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output)
    print(args.output)
    print(f"Native equations: {equations}; inline images including correspondence icon: 7")


if __name__ == "__main__":
    main()
