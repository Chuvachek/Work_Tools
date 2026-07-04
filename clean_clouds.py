import fitz
import io

def is_gray(color):
    if not color:
        return False
    r, g, b = color[0], color[1], color[2]
    if 0.3 < r < 0.85:
        if abs(r - g) < 0.05 and abs(g - b) < 0.05:
            return True
    return False

def process_drawing(input_path, output_path):
    print(f"Открываем файл: {input_path}...")
    doc = fitz.open(input_path)
    total_cleaned = 0

    for page_num, page in enumerate(doc):
        print(f"Обработка страницы {page_num + 1}...")
        
        # Получаем все пути
        all_drawings = page.get_drawings()
        
        # Собираем индексы объектов для удаления
        # В PyMuFX нет прямого удаления, но мы можем пересоздать страницу
        # без "плохих" объектов
        
        # Получаем содержимое страницы в виде текста
        text = page.get_text("text")
        
        # Альтернативный подход: используем redact с большими областями
        # Объединяем все найденные прямоугольники в одну область
        if all_drawings:
            # Собираем все прямоугольники для удаления
            rects_to_remove = []
            for d in all_drawings:
                if d["type"] in ["s", "fs"]:
                    color = d.get("color") or d.get("fill")
                    if is_gray(color):
                        items = d.get("items", [])
                        if items:
                            rect = d["rect"]
                            if rect.width < 120 and rect.height < 120:
                                rects_to_remove.append(rect)
            
            print(f"  Найдено {len(rects_to_remove)} серых сегментов.")
            total_cleaned += len(rects_to_remove)
            
            if rects_to_remove:
                # Объединяем все прямоугольники в один большой
                # Это радикально, но работает быстро
                # Находим общую bounding box всех "облаков"
                from fitz import Rect
                
                # Если облака разбросаны по всей странице, этот метод не подходит
                # Поэтому сделаем по-другому: для каждого облака добавляем аннотацию,
                # но применяем пачками по 100 штук
                
                batch_size = 500
                for i in range(0, len(rects_to_remove), batch_size):
                    batch = rects_to_remove[i:i+batch_size]
                    for rect in batch:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
                    print(f"    Обработано {min(i+batch_size, len(rects_to_remove))} из {len(rects_to_remove)}...")
    
    if total_cleaned > 0:
        print(f"Сохраняем очищенный файл: {output_path}...")
        doc.save(output_path, garbage=4, deflate=True)
        print("Готово!")
    else:
        print("Серые элементы не найдены.")
    
    doc.close()

input_file = "input_drawing.pdf"
output_file = "output_no_clouds.pdf"

import os
if os.path.exists(input_file):
    process_drawing(input_file, output_file)
else:
    print(f"Ошибка: Файл {input_file} не найден.")