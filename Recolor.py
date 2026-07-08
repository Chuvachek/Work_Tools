import fitz  # PyMuPDF
import re
from pathlib import Path
import sys

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
        return b'0 0 0 ' + op if is_near_red_rgb(rf, gf, bf, tol) else m.group(0)

    def replace_cmyk(m):
        c, mm, y, k, op = m.groups()
        try:
            cf, mf, yf, kf = float(c), float(mm), float(y), float(k)
        except ValueError:
            return m.group(0)
        return b'0 0 0 1 ' + op if is_near_red_cmyk(cf, mf, yf, kf, tol) else m.group(0)

    return replace_rgb, replace_cmyk

def recolor_stream_bytes(stream: bytes, replace_rgb, replace_cmyk) -> bytes:
    new_stream = rgb_pattern.sub(replace_rgb, stream)
    new_stream = cmyk_pattern.sub(replace_cmyk, new_stream)
    return new_stream

def recolor_all_streams(doc, replace_rgb, replace_cmyk):
    """Проходит по ВСЕМ объектам документа (не только content stream страницы
    и не только XObjects страницы) и патчит любой поток с операторами цвета.
    Это закрывает в том числе Appearance Streams (/AP /N) аннотаций и виджетов."""
    for xref in range(1, doc.xref_length()):
        if not doc.xref_is_stream(xref):
            continue
        stream = doc.xref_stream(xref)
        if not stream:
            continue
        new_stream = recolor_stream_bytes(stream, replace_rgb, replace_cmyk)
        if new_stream != stream:
            doc.update_stream(xref, new_stream)

def recolor_annotation_dict_colors(page, tol=0.15):
    """/C и /IC у обычных аннотаций (Highlight, Line, Square и т.д.)"""
    for annot in page.annots() or []:
        colors = annot.colors
        changed = False
        new_colors = {}
        for key in ("stroke", "fill"):
            c = colors.get(key)
            if c and is_near_red_rgb(*c, tol):
                new_colors[key] = (0, 0, 0)
                changed = True
            else:
                new_colors[key] = c
        if changed:
            annot.set_colors(new_colors)
            annot.update()

def recolor_widget_mk(doc, page, tol=0.15):
    """/MK/BC и /MK/BG у полей форм (Widget) — рамка и фон текстового поля."""
    for annot in page.annots() or []:
        if annot.type[0] != 20:  # 20 = PDF_ANNOT_WIDGET
            continue
        xref = annot.xref
        mk_raw = doc.xref_get_key(xref, "MK")
        if mk_raw[0] != "dict":
            continue
        mk_str = mk_raw[1]

        def repl_color_array(m):
            nums = [float(x) for x in m.group(1).split()]
            if len(nums) == 3 and is_near_red_rgb(*nums, tol):
                return "[0 0 0]"
            return m.group(0)

        new_mk_str = re.sub(r'\[([\d.\s]+)\]', repl_color_array, mk_str)
        if new_mk_str != mk_str:
            doc.xref_set_key(xref, "MK", new_mk_str)

def recolor_widget_da(doc, page, tol=0.15):
    """/DA — строка с цветом текста внутри текстового поля, например '1 0 0 rg /Helv 12 Tf'."""
    for annot in page.annots() or []:
        if annot.type[0] != 20:  # Widget
            continue
        xref = annot.xref
        da_raw = doc.xref_get_key(xref, "DA")
        if da_raw[0] != "string":
            continue
        da_str = da_raw[1]
        da_bytes = da_str.encode("latin-1", errors="ignore")

        replace_rgb, replace_cmyk = make_replacer(tol)
        new_da_bytes = recolor_stream_bytes(da_bytes, replace_rgb, replace_cmyk)

        if new_da_bytes != da_bytes:
            new_da_str = new_da_bytes.decode("latin-1", errors="ignore")
            doc.xref_set_key(xref, "DA", f"({new_da_str})")

def recolor_red_to_black(input_path: str, output_path: str, tol: float = 0.15):
    doc = fitz.open(input_path)
    replace_rgb, replace_cmyk = make_replacer(tol)

    # 1) Все потоки документа разом: content streams страниц, Form XObjects,
    #    appearance streams аннотаций и виджетов
    recolor_all_streams(doc, replace_rgb, replace_cmyk)

    # 2) Явные цветовые ключи в словарях аннотаций/полей
    for page in doc:
        recolor_annotation_dict_colors(page, tol)
        recolor_widget_mk(doc, page, tol)
        recolor_widget_da(doc, page, tol)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

def find_pdfs(folder: Path):
    return sorted(f for f in folder.glob("*.pdf") if not f.stem.endswith("_bw"))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = Path(r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12523-00\03.Result\blyat")

    pdf_files = find_pdfs(folder)
    if not pdf_files:
        print("PDF-файлы не найдены в указанной папке.")

    failed = []
    for input_path in pdf_files:
        output_path = folder / f"{input_path.stem}_bw{input_path.suffix}"
        print(f"Обработка: {input_path.name}")
        try:
            recolor_red_to_black(str(input_path), str(output_path))
        except Exception as e:
            print(f"  ОШИБКА: {e}")
            failed.append(input_path.name)

    print("\nГотово.")
    if failed:
        print(f"\nНе удалось обработать ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")