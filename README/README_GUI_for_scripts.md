
🧩 GUI-фреймворки
Фреймворк	Сложность	Фишки	Вердикт
CustomTkinter	Низкая	Dark Mode, современный вид, быстро	✅ Старт здесь
PyQt6/PySide6	Сред/Выс	Проф. нативный вид	Для крупных проектов
Flet	Низкая	React-стиль, веб-интерфейс	Экспериментально
📁 Структура проекта
text
PDF_Manager/
├── main.py                # Точка входа, запуск GUI
├── gui/
│   ├── __init__.py
│   └── app_window.py      # Вкладки, кнопки, поля
└── modules/
    ├── __init__.py
    ├── excel_parser.py    # Creating_tables_in_Excelpy7.py + Output file names
    ├── pdf_recolor.py     # Recolor.py
    ├── pdf_replace.py     # Replace_Revision_pdf_code.py
    └── pdf_scanner.py     # ScannerPDF.py
🗂️ Вкладки интерфейса
Парсер и Отчеты — выбор папки → генерация Excel-таблиц

Перекраска PDF — выбор файлов/папки, чекбоксы (потоки/аннотации/виджеты) → recolor_all_streams

Замена ревизий — таблица OLD_TEXTS ↔ NEW_TEXT, выбор .ttf → замена

Анализ PDF — сканер структуры + рекомендации по инструментам (qpdf, pdfplumber...)

⚠️ Критично: Threading
Тяжёлые задачи обязательно в отдельный поток (threading)

Иначе GUI зависает → система выдаёт «Не отвечает»

прогресс-бар для юзер-френдли