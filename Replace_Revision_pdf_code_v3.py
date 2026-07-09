import re
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


def replace_text_in_pdf(input_path: str, output_path: str, old_texts: list, new_text: str | list | tuple | dict | None = None, font_path: str = None, new_font_size: float = 11, redact_fill=(1, 1, 1)) -> int:
    """
    Заменяет все вхождения нескольких старых строк из списка old_texts на новые значения в PDF.
    Поддерживаются варианты:
    - старый API: old_texts=["XX_X"], new_text="02_3"
    - новый API: old_texts=[("XX_X.X", "02_3.X"), ("XX_X", "02_3")]
    - либо old_texts=["XX_X.X", "XX_X"], new_text=["02_3.X", "02_3"]

    redact_fill: цвет заливки места старого текста после удаления.
        (1, 1, 1) - закрасить белым (безопасно, если под текстом могут быть
                     линии/штриховка - гарантированно перекроет их).
        None      - не закрашивать вообще, просто удалить старый текст и
                     оставить то, что было под ним (чисто, если там только
                     белая бумага без пересекающих линий).
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
                page.add_redact_annot(inst, fill=redact_fill)
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

def replace_sequence_in_pdf(
    input_path: str,
    output_path: str,
    search_text: str = "XX_X.X",
    prefix: str = "05_1",
    start: int = 1,
    font_path: str = None,
    new_font_size: float = 9,
    redact_fill=(1, 1, 1)
) -> int:
    """
    Последовательно заменяет все вхождения search_text.

    Пример:
        XX_X.X →
        05_1.1
        05_1.2
        05_1.3
        ...

    Порядок соответствует страницам PDF и расположению текста на странице.

    redact_fill: см. описание в replace_text_in_pdf.
        (1, 1, 1) - закрасить белым (безопасный вариант по умолчанию).
        None      - не закрашивать, только удалить старый текст.
    """

    doc = fitz.open(input_path)

    counter = start
    total = 0

    for page in doc:

        text_instances = page.search_for(search_text)

        if not text_instances:
            continue

        # Сортировка:
        # сначала сверху вниз,
        # затем слева направо.
        text_instances.sort(key=lambda r: (round(r.y0, 1), r.x0))

        blocks = page.get_text("dict")["blocks"]

        infos = []

        for inst in text_instances:
            fontsize, color = find_font_info(page, blocks, inst)
            infos.append((fitz.Rect(inst), fontsize, color))

        # Закрашиваем (или просто удаляем) старый текст
        for rect, _, _ in infos:
            page.add_redact_annot(rect, fill=redact_fill)

        page.apply_redactions()

        # Записываем новый
        for rect, _, color in infos:

            replacement = f"{prefix}.{counter}"

            counter += 1

            font_kwargs = {}

            if font_path:
                font_path_obj = Path(font_path).expanduser()

                if not font_path_obj.is_absolute():
                    font_path_obj = (
                        Path(__file__).resolve().parent /
                        font_path_obj
                    ).resolve()

                if font_path_obj.exists():
                    font_kwargs["fontname"] = font_path_obj.stem
                    font_kwargs["fontfile"] = str(font_path_obj)

            p = fitz.Point(rect.x0, rect.y1 - 1)

            if page.rotation != 0:
                p = p * page.derotation_matrix

            shape = page.new_shape()

            shape.insert_text(
                p,
                replacement,
                fontsize=new_font_size,
                color=color,
                render_mode=0,
                rotate=0,
                **font_kwargs
            )

            shape.commit(overlay=True)

            total += 1

    input_file = Path(input_path)
    output_file = Path(output_path)
    output_tmp = None

    if input_file.resolve() == output_file.resolve():
        output_tmp = output_file.with_stem(output_file.stem + "_tmp")
        save_path = output_tmp
    else:
        save_path = output_file

    doc.save(save_path)
    doc.close()

    if output_tmp is not None:
        if output_file.exists():
            output_file.unlink()
        output_tmp.rename(output_file)

    return total

def reset_to_template(
    input_path: str,
    output_path: str,
    pattern_prefix: str,
    template: str = "XX_X.X",
    font_path: str = None,
    new_font_size: float = 9,
    redact_fill=(1, 1, 1)
) -> int:
    """
    Находит в PDF весь текст вида "<pattern_prefix>.<число>"
    (например, "04_5.1", "04_5.2", ... "04_5.37") и заменяет его
    обратно на шаблон-заглушку (по умолчанию "XX_X.X"), чтобы можно
    было запустить replace_sequence_in_pdf заново.

    В отличие от replace_text_in_pdf / replace_sequence_in_pdf, здесь не
    задаётся точная строка для поиска через page.search_for() — вместо
    этого сканируются все "слова" на странице (page.get_text("words")) и
    через regex отбираются те, что соответствуют шаблону нумерации.
    Поэтому не нужно перечислять каждый номер (04_5.1, 04_5.2, ...)
    вручную - достаточно указать префикс.

    pattern_prefix: префикс номера без точки, например "04_5".
                     Будут найдены "04_5.1", "04_5.2", "04_5.100" и т.д.
    template:        на что заменить найденные номера (по умолчанию "XX_X.X").
    redact_fill:     см. описание в replace_text_in_pdf.
    """
    doc = fitz.open(input_path)

    # Ищем "<prefix>.<одна или более цифр>" целиком, без хвостов/префиксов
    pattern = re.compile(rf"^{re.escape(pattern_prefix)}\.\d+$")

    total = 0

    for page in doc:

        # get_text("words") -> список (x0, y0, x1, y1, text, block_no, line_no, word_no)
        words = page.get_text("words")
        matches = [w for w in words if pattern.fullmatch(w[4])]

        if not matches:
            continue

        blocks = page.get_text("dict")["blocks"]

        infos = []
        for w in matches:
            rect = fitz.Rect(w[:4])
            fontsize, color = find_font_info(page, blocks, rect)
            infos.append((rect, fontsize, color))

        # Закрашиваем (или просто удаляем) текущую нумерацию
        for rect, _, _ in infos:
            page.add_redact_annot(rect, fill=redact_fill)

        page.apply_redactions()

        # Возвращаем шаблон-заглушку на место
        for rect, _, color in infos:

            font_kwargs = {}

            if font_path:
                font_path_obj = Path(font_path).expanduser()

                if not font_path_obj.is_absolute():
                    font_path_obj = (
                        Path(__file__).resolve().parent /
                        font_path_obj
                    ).resolve()

                if font_path_obj.exists():
                    font_kwargs["fontname"] = font_path_obj.stem
                    font_kwargs["fontfile"] = str(font_path_obj)

            p = fitz.Point(rect.x0, rect.y1 - 1)

            if page.rotation != 0:
                p = p * page.derotation_matrix

            shape = page.new_shape()

            shape.insert_text(
                p,
                template,
                fontsize=new_font_size,
                color=color,
                render_mode=0,
                rotate=0,
                **font_kwargs
            )

            shape.commit(overlay=True)

            total += 1

    input_file = Path(input_path)
    output_file = Path(output_path)
    output_tmp = None

    if input_file.resolve() == output_file.resolve():
        output_tmp = output_file.with_stem(output_file.stem + "_tmp")
        save_path = output_tmp
    else:
        save_path = output_file

    doc.save(save_path)
    doc.close()

    if output_tmp is not None:
        if output_file.exists():
            output_file.unlink()
        output_tmp.rename(output_file)

    return total


def find_pdfs(folder: Path, suffix: str):
    """Все PDF в папке, кроме уже готовых результатов (с заданным суффиксом)."""
    return sorted(
        f for f in folder.glob("*.pdf")
        if not f.stem.endswith(suffix)
    )


if __name__ == "__main__":
    folder = Path(r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12520-00\03.Result3\Replace")

    # ==== РЕЖИМ РАБОТЫ ====
    # "NUMBER" - новая нумерация: XX_X.X -> 04_5.1, 04_5.2, ...
    # "RESET"  - откат нумерации обратно к шаблону: 04_5.1, 04_5.2, ... -> XX_X.X
    MODE = "NUMBER"  # "NUMBER" или "RESET"
    # =======================

    # ==== ОБЩИЕ НАСТРОЙКИ ====
    SUFFIX = "_r"  # суффикс имени выходного PDF-файла

    # Заливка места старого текста после его удаления:
    #   (1, 1, 1) - закрасить белым (надёжно, если под текстом могут быть
    #                линии рамки/штампа/штриховка - гарантированно их перекроет)
    #   None      - не закрашивать вообще, только удалить старый текст
    #                (чисто, если под текстом просто белая бумага без линий)
    REDACT_FILL = (1, 1, 1)

    # Указываем ваш файл шрифта
    FONT_PATH = str((Path(__file__).resolve().parent / "GOST2304A.ttf").resolve())
    NEW_FONT_SIZE = 9
    # ==========================

    # ==== НАСТРОЙКИ ДЛЯ РЕЖИМА "NUMBER" ====
    # Простые точечные замены (например, дата), если нужны.
    # Формат: ("старый_текст", "новый_текст")
    # ВАЖНО: сюда НЕ нужно добавлять шаблон нумерации (XX_X.X) —
    # он обрабатывается отдельно, через SEQUENCE_*, одним проходом,
    # чтобы не закрашивать одно и то же место дважды.
    REPLACEMENTS = [
        # ("03.10.23", "07.07.26"),
    ]

    # Нумерация вида 04_5.1, 04_5.2, 04_5.3 ...
    SEQUENCE_SEARCH = "XX_X.X"   # шаблон-заглушка, который ищем в исходном PDF
    SEQUENCE_PREFIX = "05_6"     # префикс для итогового номера
    SEQUENCE_START = 1           # с какого номера начинать нумерацию
    # =========================================

    # ==== НАСТРОЙКИ ДЛЯ РЕЖИМА "RESET" ====
    # Префикс уже проставленной нумерации, которую нужно найти и откатить.
    # Например, если в PDF сейчас "04_5.1", "04_5.2" ... - укажите "04_5".
    RESET_PATTERN_PREFIX = "05_6"  # префикс уже проставленной нумерации, которую нужно откатить
    RESET_TEMPLATE = "XX_X.X"    # на что откатываем найденные номера
    # =========================================

    pdf_files = find_pdfs(folder, SUFFIX)

    if not pdf_files:
        print("PDF-файлы не найдены в указанной папке.")

    for input_path in pdf_files:
        output_path = folder / f"{input_path.stem}{SUFFIX}{input_path.suffix}"
        print(f"Обработка: {input_path.name}")

        if MODE == "RESET":
            # Режим отката: <RESET_PATTERN_PREFIX>.<число> -> RESET_TEMPLATE
            count_reset = reset_to_template(
                input_path=str(input_path),
                output_path=str(output_path),
                pattern_prefix=RESET_PATTERN_PREFIX,
                template=RESET_TEMPLATE,
                font_path=FONT_PATH,
                new_font_size=NEW_FONT_SIZE,
                redact_fill=REDACT_FILL
            )
            if count_reset:
                print(f"  -> откат нумерации: {count_reset} вхождений '{RESET_PATTERN_PREFIX}.*' заменено на '{RESET_TEMPLATE}'")
            else:
                print(f"  -> нумерация с префиксом '{RESET_PATTERN_PREFIX}' не найдена")

        elif MODE == "NUMBER":
            # Шаг 1: простые точечные замены (например, дата), если заданы.
            if REPLACEMENTS:
                count = replace_text_in_pdf(str(input_path), str(output_path), REPLACEMENTS, None, font_path=FONT_PATH, new_font_size=NEW_FONT_SIZE, redact_fill=REDACT_FILL)
                if count:
                    print(f"  -> заменено {count} вхождений, сохранено в {output_path.name}")
                else:
                    print(f"  -> Ни один из текстов {REPLACEMENTS} не найден, файл сохранён как копия")
                seq_input = str(output_path)
            else:
                seq_input = str(input_path)

            # Шаг 2: нумерация — ОДИН проход по оригинальному шаблону XX_X.X,
            # сразу пишем финальный номер (04_5.1, 04_5.2, ...) без промежуточной
            # закраски, чтобы под текстом не накапливались лишние белые прямоугольники.
            count_seq = replace_sequence_in_pdf(
                input_path=seq_input,
                output_path=str(output_path),
                search_text=SEQUENCE_SEARCH,
                prefix=SEQUENCE_PREFIX,
                start=SEQUENCE_START,
                font_path=FONT_PATH,
                new_font_size=NEW_FONT_SIZE,
                redact_fill=REDACT_FILL
            )
            if count_seq:
                print(f"  -> последовательная нумерация: {count_seq} вхождений ({SEQUENCE_PREFIX}.{SEQUENCE_START}...)")
            else:
                print(f"  -> шаблон '{SEQUENCE_SEARCH}' для нумерации не найден")

        else:
            print(f"  -> Неизвестный MODE = '{MODE}'. Используйте 'NUMBER' или 'RESET'.")
            break

    print("Готово.")
