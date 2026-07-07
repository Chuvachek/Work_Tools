import fitz  # PyMuPDF
from pathlib import Path


def find_font_info(page, blocks, rect):
    """Подбирает размер шрифта и цвет текста в месте прямоугольника rect."""
    fontsize = 9
    color = (0, 0, 0)
    for b in blocks:
        rotation = page.rotation
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                if fitz.Rect(s["bbox"]).intersects(rect):
                    fontsize = s["size"]
                    c = s["color"]
                    color = ((c >> 16 & 255) / 255,
                             (c >> 8 & 255) / 255,
                             (c & 255) / 255)
    return fontsize, color


def replace_text_in_pdf(input_path: str, output_path: str, old_texts: list, new_text: str, font_path: str = None, new_font_size: float = 8) -> int:
    """
    Заменяет все вхождения нескольких старых строк из списка old_texts на new_text в PDF.
    Принимает необязательный путь к файлу шрифта (.ttf) и фиксированный размер для новой надписи
    (по умолчанию `new_font_size=8` pt). Также вставляет текст в прямоугольник, чтобы избежать
    поворота надписи (иногда появлялся поворот на 90 градусов).
    """
    doc = fitz.open(input_path)
    total = 0

    for page in doc:
        for old_text in old_texts:
            text_instances = page.search_for(old_text)
            if not text_instances:
                continue

            blocks = page.get_text("dict")["blocks"]
            infos = [(inst, *find_font_info(page, blocks, inst)) for inst in text_instances]
            saved_infos = []

            for inst, fontsize, color in infos:
                saved_infos.append((
                    fitz.Rect(inst),
                    fontsize,
                    color
                ))

            for inst, fontsize, color in infos:
                page.add_redact_annot(inst, fill=(1, 1, 1))
            page.apply_redactions()

            for inst, _, color in saved_infos:
                font_kwargs = {}
                if font_path and Path(font_path).exists():
                    font_kwargs["fontname"] = Path(font_path).stem
                    font_kwargs["fontfile"] = str(font_path)

                fs = new_font_size

                # Координата вставки
                p = fitz.Point(inst.x0, inst.y1 - 1)

                # Если страница повернута, переводим координаты
                if page.rotation != 0:
                    p = p * page.derotation_matrix

                shape = page.new_shape()

                shape.insert_text(
                    p,
                    new_text,
                    fontsize=fs,
                    color=color,
                    render_mode=0,
                    rotate=0,
                    **font_kwargs
                )

                shape.commit(overlay=True)
                total += 1

    doc.save(output_path)
    doc.close()
    return total


def find_pdfs(folder: Path, suffix: str):
    """Все PDF в папке, кроме уже готовых результатов (с заданным суффиксом)."""
    return sorted(
        f for f in folder.glob("*.pdf")
        if not f.stem.endswith(suffix)
    )


if __name__ == "__main__":
    folder = Path(r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12488-00\03.Result — копия (test)")

    # ==== НАСТРОЙКИ ====
    # Перечисляем нужные варианты через запятую внутри списка []
    OLD_TEXTS = ["XX_X"]     # что ищем на штампе
    NEW_TEXT = "07.07.26"                            # на что заменяем
    SUFFIX = "_r"                            # суффикс для новых файлов

    # Указываем ваш файл шрифта
    FONT_PATH = "GOST2304A.ttf"
    # ====================

    pdf_files = find_pdfs(folder, SUFFIX)

    if not pdf_files:
        print("PDF-файлы не найдены в указанной папке.")

    for input_path in pdf_files:
        output_path = folder / f"{input_path.stem}{SUFFIX}{input_path.suffix}"
        print(f"Обработка: {input_path.name}")
        count = replace_text_in_pdf(str(input_path), str(output_path), OLD_TEXTS, NEW_TEXT, font_path=FONT_PATH)
        if count:
            print(f"  -> заменено {count} вхождений, сохранено в {output_path.name}")
        else:
            print(f"  -> Ни один из текстов {OLD_TEXTS} не найден, файл сохранён как копия")

    print("Готово.")
