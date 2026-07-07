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


def replace_text_in_pdf(input_path: str, output_path: str, old_texts: list, new_text: str | list | tuple | dict | None = None, font_path: str = None, new_font_size: float = 11) -> int:
    """
    Заменяет все вхождения нескольких старых строк из списка old_texts на новые значения в PDF.
    Поддерживаются варианты:
    - старый API: old_texts=["XX_X"], new_text="02_3"
    - новый API: old_texts=[("XX_X.X", "02_3.X"), ("XX_X", "02_3")]
    - либо old_texts=["XX_X.X", "XX_X"], new_text=["02_3.X", "02_3"]
    """
    doc = fitz.open(input_path)
    total = 0

    if old_texts and all(isinstance(item, (list, tuple)) and len(item) == 2 for item in old_texts):
        replacements = [(str(old), str(new)) for old, new in old_texts]
    elif isinstance(new_text, dict):
        replacements = [(str(old), str(new_text[str(old)])) for old in old_texts]
    elif isinstance(new_text, (list, tuple)) and not isinstance(new_text, str):
        replacements = [(str(old), str(new)) for old, new in zip(old_texts, new_text)]
    else:
        replacements = [(str(old), str(new_text)) for old in old_texts]

    for page in doc:
        for old_text, replacement_text in replacements:
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
                if font_path:
                    font_path_obj = Path(font_path).expanduser()
                    if not font_path_obj.is_absolute():
                        font_path_obj = (Path(__file__).resolve().parent / font_path_obj).resolve()
                    if font_path_obj.exists():
                        font_kwargs["fontname"] = font_path_obj.stem
                        font_kwargs["fontfile"] = str(font_path_obj)

                fs = new_font_size

                # Координата вставки
                p = fitz.Point(inst.x0, inst.y1 - 1)

                # Если страница повернута, переводим координаты
                if page.rotation != 0:
                    p = p * page.derotation_matrix

                shape = page.new_shape()

                shape.insert_text(
                    p,
                    replacement_text,
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
    folder = Path(r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12490-00\03.Result2")

    # ==== НАСТРОЙКИ ====
    # Здесь задаются замены: сначала то, что ищем в PDF, затем то, на что меняем.
    # Формат: ("старый_текст", "новый_текст")
    # Пример:
    #   ("XX_X.X", "02_3.X")  -> меняем "XX_X.X" на "02_3.X"
    #   ("XX_X", "02_3")      -> меняем "XX_X" на "02_3"
    REPLACEMENTS = [
        ("03.10.23", "07.07.26")
    ]
    SUFFIX = "_r"  # суффикс имени выходного PDF-файла

    # Указываем ваш файл шрифта
    FONT_PATH = str((Path(__file__).resolve().parent / "GOST2304A.ttf").resolve())
    NEW_FONT_SIZE = 9
    # ====================

    pdf_files = find_pdfs(folder, SUFFIX)

    if not pdf_files:
        print("PDF-файлы не найдены в указанной папке.")

    for input_path in pdf_files:
        output_path = folder / f"{input_path.stem}{SUFFIX}{input_path.suffix}"
        print(f"Обработка: {input_path.name}")
        count = replace_text_in_pdf(str(input_path), str(output_path), REPLACEMENTS, None, font_path=FONT_PATH, new_font_size=NEW_FONT_SIZE)
        if count:
            print(f"  -> заменено {count} вхождений, сохранено в {output_path.name}")
        else:
            print(f"  -> Ни один из текстов {REPLACEMENTS} не найден, файл сохранён как копия")

    print("Готово.")
