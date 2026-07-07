import fitz  # PyMuPDF
from pathlib import Path
import shutil
import re
import easyocr  # pip install easyocr

# ========== НАСТРОЙКИ ==========
FOLDER_PATH = r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12490-00\03.Result2"

# Регулярное выражение для поиска шифра чертежа.
# Жёстко фиксируем только "GLE-RD-(xx-xx-xxx)" — это всегда одинаковый формат.
# Всё после закрывающей скобки — переменное (буквы/цифры/дефисы + опционально число через пробел).
PATTERN = re.compile(
    r"GLE-RD-\([A-Za-z0-9]{2,3}-[A-Za-z0-9]{2,3}-[A-Za-z0-9]{2,4}\)[\w\-]*(?:\s+\S+)?"
)

# Якорь для поиска через page.search_for (используется, если текстового слоя нет / он не читается)
ANCHOR_TEXT = "GLE-RD-"

# Насколько расширять область вокруг найденного якоря для OCR (в точках PDF, 1pt ≈ 1/72 дюйма)
EXPAND_RIGHT = 400
EXPAND_UP = 10
EXPAND_DOWN = 10
# =================================

# Инициализируем EasyOCR один раз (для скорости)
reader = easyocr.Reader(['ru', 'en'], gpu=False)


def try_extract_from_page_text(page: "fitz.Page") -> str:
    """
    Пытается найти шифр в текстовом слое страницы (без OCR).
    Возвращает найденный шифр или пустую строку.
    """
    text = page.get_text("text")
    match = PATTERN.search(text)
    return match.group(0) if match else ""


def try_extract_via_ocr_anchor(page: "fitz.Page") -> str:
    """
    Ищет якорь "GLE-RD-" на странице через page.search_for (устойчиво к сдвигу,
    повороту и разному формату листа), затем вырезает область вокруг найденного
    места и распознаёт её через OCR.
    """
    anchors = page.search_for(ANCHOR_TEXT)
    if not anchors:
        return ""

    page_rect = page.rect

    for anchor_rect in anchors:
        # Расширяем область вокруг найденного якоря, но не выходим за границы страницы
        clip = fitz.Rect(
            anchor_rect.x0,
            max(page_rect.y0, anchor_rect.y0 - EXPAND_UP),
            min(page_rect.x1, anchor_rect.x1 + EXPAND_RIGHT),
            min(page_rect.y1, anchor_rect.y1 + EXPAND_DOWN),
        )

        pix = page.get_pixmap(clip=clip, dpi=300)
        img_bytes = pix.tobytes("png")
        result = reader.readtext(img_bytes, detail=0, paragraph=True)
        ocr_text = " ".join(result).strip()

        match = PATTERN.search(ocr_text)
        if match:
            return match.group(0)

    return ""


def extract_designation(pdf_path: str) -> str:
    """
    Проходит по всем страницам PDF и ищет шифр чертежа.
    Порядок для каждой страницы:
      1. Обычный текстовый слой (быстро, без OCR).
      2. Поиск якоря "GLE-RD-" через search_for + OCR вырезанной области (если текстовый слой не дал результата).
    Останавливается на первой странице, где шифр найден.
    """
    doc = fitz.open(pdf_path)
    designation = ""

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]

            # 1. Пробуем стандартный текстовый слой
            designation = try_extract_from_page_text(page)
            if designation:
                break

            # 2. Если не нашли — ищем якорь и делаем OCR вокруг него
            designation = try_extract_via_ocr_anchor(page)
            if designation:
                break
    finally:
        doc.close()

    return designation


def clean_filename(text: str) -> str:
    """
    Очищает строку от недопустимых символов для имени файла.
    """
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        text = text.replace(char, '_')
    text = ' '.join(text.split())
    return text


def process_all_pdfs(folder_path: str):
    """
    Обрабатывает все PDF в папке:
    - ищет шифр по всем страницам (текстовый слой -> OCR-якорь)
    - создаёт копию файла, названную согласно найденному шифру
    - не перезаписывает уже существующие файлы (добавляет суффикс)
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Папка не найдена: {folder_path}")
        return

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print("PDF-файлы не найдены.")
        return

    print(f"Найдено PDF: {len(pdf_files)}")
    print("-" * 60)

    processed = 0
    skipped = 0
    errors = 0

    for pdf_file in pdf_files:
        print(f"\nОбработка: {pdf_file.name}")
        try:
            designation = extract_designation(str(pdf_file))

            if not designation:
                print("  ⚠️ Шифр не найден ни на одной странице. Пропускаем.")
                skipped += 1
                continue

            print(f"  ✅ Найден шифр: '{designation}'")

            clean_name = clean_filename(designation)
            if not clean_name:
                print("  ⚠️ Имя после очистки пустое. Пропускаем.")
                skipped += 1
                continue

            new_path = folder / f"{clean_name}.pdf"

            # Защита от перезаписи — добавляем суффикс, если файл уже существует
            counter = 1
            while new_path.exists():
                new_path = folder / f"{clean_name}_{counter}.pdf"
                counter += 1

            shutil.copy2(pdf_file, new_path)
            print(f"  ✅ Сохранён как: {new_path.name}")
            processed += 1

        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            errors += 1

    print("\n" + "=" * 60)
    print(f"ГОТОВО!")
    print(f"  ✅ Успешно переименовано: {processed}")
    print(f"  ⚠️ Пропущено (нет шифра): {skipped}")
    print(f"  ❌ Ошибок: {errors}")
    print(f"  📁 Всего обработано: {len(pdf_files)}")


if __name__ == "__main__":
    process_all_pdfs(FOLDER_PATH)