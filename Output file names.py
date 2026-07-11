import re
from pathlib import Path

# === Укажите путь к директории с файлами ===
DIRECTORY = r"C:\Users\I8741~1.DAN\Desktop\В работе\вахта 3\TQ-12477-00\01.Info\DXF"  # замените на нужный путь

EXTENSIONS = {".dxf"}  # расширения файлов, которые нужно взять из директории

def natural_key(filename: str):
    """Естественная сортировка по сегментам текста и числам."""
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r'(\d+)', filename)]

def get_filenames(directory: str, extensions: set[str] = EXTENSIONS):
    path = Path(directory)
    if not path.is_dir():
        raise NotADirectoryError(f"Директория не найдена: {directory}")

    files = [f.name for f in path.iterdir() if f.is_file() and f.suffix.lower() in extensions]
    files.sort(key=natural_key)
    return files

if __name__ == "__main__":
    names = get_filenames(DIRECTORY)

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