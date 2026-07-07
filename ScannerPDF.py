import fitz  # pip install pymupdf

pdf_path = r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12488-00\03.Result\Test\файл.pdf"

doc = fitz.open(pdf_path)
page = doc[0]

# 1) Векторная графика (линии, прямоугольники, кривые)
print("=== ВЕКТОРНАЯ ГРАФИКА ===")
drawings = page.get_drawings()
print(f"Найдено объектов: {len(drawings)}\n")
for i, obj in enumerate(drawings[:20]):
    color, fill, obj_type = obj["color"], obj["fill"], obj["type"]
    if color or fill:
        print(f"№{i} [{obj_type}] контур={color} заливка={fill}")

# 2) Текст со стилями и цветом
print("\n=== ТЕКСТ ===")
text_dict = page.get_text("dict")
for block in text_dict["blocks"]:
    for line in block.get("lines", []):
        for span in line["spans"]:
            color_int = span["color"]  # цвет как int, конвертируем в RGB
            r = ((color_int >> 16) & 255) / 255
            g = ((color_int >> 8) & 255) / 255
            b = (color_int & 255) / 255
            if r > 0.6 and g < 0.3 and b < 0.3:  # похоже на красный
                print(f"Текст: '{span['text']}' цвет=({r:.2f},{g:.2f},{b:.2f}) шрифт={span['font']}")

# 3) Аннотации и виджеты (комментарии, поля форм)
print("\n=== АННОТАЦИИ / ВИДЖЕТЫ ===")
for annot in page.annots() or []:
    print(f"Тип: {annot.type}, цвета: {annot.colors}, xref={annot.xref}")
    if annot.type[0] == 20:  # Widget
        print(f"  MK: {doc.xref_get_key(annot.xref, 'MK')}")
        print(f"  DA: {doc.xref_get_key(annot.xref, 'DA')}")

doc.close()