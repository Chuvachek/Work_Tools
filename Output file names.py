import re
from pathlib import Path

# === Укажите путь к директории с файлами ===
DIRECTORY = r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12490-00\03.Result2"  # замените на нужный путь

def natural_key(filename: str):
    """Естественная сортировка: '2.', '3.', '10.' идут в правильном порядке."""
    match = re.match(r'^(\d+)\.', filename)
    return int(match.group(1)) if match else float('inf')

def get_pdf_filenames(directory: str):
    path = Path(directory)
    if not path.is_dir():
        raise NotADirectoryError(f"Директория не найдена: {directory}")

    # только файлы в самой папке (без подпапок), только .pdf
    files = [f.name for f in path.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    files.sort(key=natural_key)
    return files

if __name__ == "__main__":
    names = get_pdf_filenames(DIRECTORY)

    print(f"Найдено файлов: {len(names)}\n")
    for name in names:
        print(name)

    # Опционально: скопировать список в буфер обмена
    try:
        import pyperclip
        pyperclip.copy("\n".join(names))
        print("\n✅ Список скопирован в буфер обмена")
    except ImportError:
        print("\nℹ Чтобы копировать в буфер обмена автоматически, установите: pip install pyperclip")