import fitz  # pip install pymupdf

pdf_path = r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12488-00\03.Result\6М.GLE-RD-(P0-72-011)-N 2600_004 (RU)_04_изм_2.pdf"

doc = fitz.open(pdf_path)
page = doc[0]  # Смотрим первую страницу (индекс 0)

# Получаем все векторные объекты
drawings = page.get_drawings()

print(f"Найдено векторных объектов: {len(drawings)}\n")

for i, obj in enumerate(drawings[:20]):  # Выведем первые 20 для оценки
    color = obj["color"]
    fill = obj["fill"]
    obj_type = obj["type"]  # 'l' - линия, 'r' - прямоугольник, 'c' - кривая
    
    # Если у объекта есть цвет контура или заливки
    if color or fill:
        print(f"Объект №{i} [Тип: {obj_type}]:")
        if color:
            print(f"  Цвет контура (RGB/CMYK): {color}")
        if fill:
            print(f"  Цвет заливки (RGB/CMYK): {fill}")