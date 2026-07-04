import fitz  # PyMuPDF
import re
from pathlib import Path

def is_near_red_rgb(r, g, b, tol=0.15):
    return r > 1 - tol and g < tol and b < tol

def is_near_red_cmyk(c, m, y, k, tol=0.15):
    return c < tol and m > 1 - tol and y > 1 - tol and k < tol

rgb_pattern = re.compile(rb'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(rg|RG)')
cmyk_pattern = re.compile(rb'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(k|K)')

def make_replacer(tol):
    def replace_rgb(m):
        r, g, b, op = m.groups()
        try:
            rf, gf, bf = float(r), float(g), float(b)
        except ValueError:
            return m.group(0)
        if is_near_red_rgb(rf, gf, bf, tol):
            return b'0 0 0 ' + op
        return m.group(0)

    def replace_cmyk(m):
        c, mm, y, k, op = m.groups()
        try:
            cf, mf, yf, kf = float(c), float(mm), float(y), float(k)
        except ValueError:
            return m.group(0)
        if is_near_red_cmyk(cf, mf, yf, kf, tol):
            return b'0 0 0 1 ' + op
        return m.group(0)

    return replace_rgb, replace_cmyk

def recolor_stream(doc, xref, replace_rgb, replace_cmyk):
    stream = doc.xref_stream(xref)
    if not stream:
        return
    new_stream = rgb_pattern.sub(replace_rgb, stream)
    new_stream = cmyk_pattern.sub(replace_cmyk, new_stream)
    if new_stream != stream:
        doc.update_stream(xref, new_stream)

def recolor_annotations(page, tol=0.15):
    """Перекрашивает цвет обводки (/C) и заливки (/IC) у аннотаций/разметки."""
    for annot in page.annots() or []:
        colors = annot.colors  # {'stroke': (r,g,b) или None, 'fill': (r,g,b) или None}
        changed = False
        new_colors = {}

        stroke = colors.get("stroke")
        if stroke and is_near_red_rgb(*stroke, tol):
            new_colors["stroke"] = (0, 0, 0)
            changed = True
        else:
            new_colors["stroke"] = stroke

        fill = colors.get("fill")
        if fill and is_near_red_rgb(*fill, tol):
            new_colors["fill"] = (0, 0, 0)
            changed = True
        else:
            new_colors["fill"] = fill

        if changed:
            annot.set_colors(new_colors)
            annot.update()

def recolor_red_to_black(input_path: str, output_path: str, tol: float = 0.15):
    doc = fitz.open(input_path)
    replace_rgb, replace_cmyk = make_replacer(tol)

    for page in doc:
        # 1) основной content stream страницы
        for xref in page.get_contents():
            recolor_stream(doc, xref, replace_rgb, replace_cmyk)

        # 2) вложенные Form XObject (формы/векторная графика)
        for xobj in page.get_xobjects():
            xref = xobj[0]
            recolor_stream(doc, xref, replace_rgb, replace_cmyk)

        # 3) аннотации / разметка (линии, фигуры, добавленные как markup)
        recolor_annotations(page, tol)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

def find_pdfs(folder: Path):
    """Все PDF в папке, кроме уже готовых результатов (_bw)."""
    return sorted(
        f for f in folder.glob("*.pdf")
        if not f.stem.endswith("_bw")
    )

if __name__ == "__main__":
    folder = Path(r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12488-00\03.Result — копия (2)")

    pdf_files = find_pdfs(folder)

    if not pdf_files:
        print("PDF-файлы не найдены в указанной папке.")

    for input_path in pdf_files:
        output_path = folder / f"{input_path.stem}_bw{input_path.suffix}"
        print(f"Обработка: {input_path.name}")
        recolor_red_to_black(str(input_path), str(output_path))

    print("Готово.")