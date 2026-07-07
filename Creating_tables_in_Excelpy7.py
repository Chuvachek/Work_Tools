import re


def split_entries(text: str):
    """Разбивает текст на отдельные записи по ';' и переводу строки."""
    entries = []
    for part in re.split(r'[;\n]+', text):
        item = part.strip()
        if item:
            entries.append(item)
    return entries


# === Входные данные (вставьте сюда любое количество строк, ЛЮБОГО из двух форматов) ===
# Формат 1 ("M."-формат):  "3M. Имя (RU)_04_изм_3.pdf"   -> код "04_03"
# Формат 2 (обычный):      "2. Имя (RU)_01.pdf"          -> код "01"
data = """
M4. GLE-RD-(P0-97-010)-N-LB 2600.001 (RU)_02_изм_3.pdf
M5. GLE-RD-(P0-97-020)-N-LB 2600.001 (RU)_02_изм_3.pdf
M6. GLE-RD-(P0-97-040)-N-LB 2600.001 (RU)_01_изм_3.pdf

""".strip()

# Универсальная регулярка (понимает ОБА формата):
#   \d+([MMМм]?)\.\s* -> номер записи + необязательная буква "M"/"М" (запоминаем, чтобы понять формат)
#   (.*?)\s*          -> само имя (нежадно)
#   \(RU\)_(\d+)      -> номер редакции (обязателен всегда)
#   (?:_изм_(\d+))?   -> номер изменения (НЕОБЯЗАТЕЛЬНАЯ часть, есть только у "M."-формата)
#   .*?\.pdf
# re.DOTALL позволяет "имени" (.*?) захватывать и случайные переносы строк,
# если запись оказалась разорвана посреди строки.
pattern = re.compile(r'\d+([MMМм]?)\.\s*(.*?)\s*\(RU\)_(\d+)(?:_изм_(\d+))?.*?\.pdf', re.DOTALL | re.IGNORECASE)

# Две отдельные группы: "M."-формат (с изм) и обычный формат (без изм)
group_m_names, group_m_codes = [], []
group_plain_names, group_plain_codes = [], []

matches = pattern.findall(data)
for is_m, name, num, izm in matches:
    # схлопываем возможные внутренние переносы строк/лишние пробелы в имени
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'\(\s+', '(', name)
    name = re.sub(r'\s+\)', ')', name)

    if is_m and is_m.upper() in ['M', 'М']:  # проверяем и английскую, и русскую М
        group_m_names.append(name)
        group_m_codes.append(f"{num}_{izm.zfill(2)}")
    else:  # обычный формат "2. ... .pdf" без "_изм_"
        group_plain_names.append(name)
        group_plain_codes.append(num)

# Проверка количества найденных записей
expected_count = len(re.findall(r'(?:^|\n)\d+[MМ]?\.\s*', data, re.IGNORECASE))
if expected_count != len(matches):
    print(f"⚠ Внимание: найдено записей {len(matches)}, ожидалось {expected_count}. "
          f"Проверьте исходный текст на разрывы строк внутри записи.")

# === Вывод ПРОСТЫМ ТЕКСТОМ (без "|") — так значения корректно лягут по ячейкам Excel ===
# При копировании из терминала и вставке в Excel: каждая строка -> отдельная ячейка
# в одном столбце (перенос строки Excel воспринимает как разделитель строк).
all_rows = group_m_names + group_m_codes + [""] + group_plain_names + group_plain_codes

print("Данные:")
for row in all_rows:
    print(row)

# === Дополнительный блок: обработка текста вида "name value; name value;" ===
text_block = """LE-RD-(P0-02-150)-N 2600; GLE-RD-(P0-71-020)-N 2600;
GLE-RD-(P0-02-104)-N 2600; GLE-RD-(P0-02-160)-N 2600; GLE-RD-(P0-71-050)-N 2600;
GLE-RD-(P0-02-105)-N 2600; GLE-RD-(P0-02-170)-N 2600; GLE-RD-(P0-71-080)-N 2600
"""

print("\nРезультат для нового текста:")
for entry in split_entries(text_block):
    print(entry)

# === Формат 3: "<Имя>.pdf <код>" (код вида XX_YY, стоит после .pdf через пробел) ===
# Пример: "GLE-RD-(P0-71-090)-N 2600_01.pdf 01_01" -> имя "GLE-RD-(P0-71-090)-N 2600_01", код "01_01"
data3 = """
GLE-RD-(P0-71-090)-N 2600_01.pdf 01_01
GLE-RD-(P0-71-210)-N 2600_03.pdf 03_04
GLE-RD-(P0-71-220)-N 2600_03.pdf 03_03
""".strip()

pattern3 = re.compile(r'^(.+?)\.pdf\s+(\d+_\d+)\s*$', re.MULTILINE)

names3, codes3 = [], []
for name, code in pattern3.findall(data3):
    names3.append(name.strip())
    codes3.append(code.strip())

print("\nРезультат для формата 3:")
for row in names3 + [""] + codes3:
    print(row)

# === data5: объединяем имя и код в одну строку с "(RU)_XX_изм_Y" ===
# Пример: имя "GLE-RD-(P0-71-090)-N 2600_01" + код "01_01"
#         -> "GLE-RD-(P0-71-090)-N 2600_01 (RU)_01_изм_1"
# Второе число в коде (после "_") берётся БЕЗ ведущего нуля (int()).

# 👇 ВСТАВЬТЕ СЮДА свои имена (каждое в кавычках, через запятую, любое количество строк)
names5_input = """

GLE-RD-(P0-93-130)-N 2600_02
GLE-RD-(P0-93-140)-N 2600_03
""".strip().splitlines()

# 👇 ВСТАВЬТЕ СЮДА свои коды (в том же порядке, что и имена выше)
codes5_input = """

02_03
02_03
03_02
""".strip().splitlines()

data5 = []
for name, code in zip(names5_input, codes5_input):
    name = name.strip()
    code = code.strip()
    xx, yy = code.split("_")
    combined = f"{name} (RU)_{xx}_изм_{int(yy)}"
    data5.append(combined)

print("\nРезультат для data5:")
for row in data5:
    print(row)

# === Формат 4: "Страница <N> из <Имя>.pdf" ===
# Пример: "Страница 16 из GLE-RD-(P0-71-090)-N 2600_01.pdf"
# -> имя "GLE-RD-(P0-71-090)-N 2600_01", страница "16"
data4 = """
Страница 16 из GLE-RD-(P0-71-090)-N 2600_01.pdf
Страница 16 из GLE-RD-(P0-85-040)-N 2600_02.pdf
Страница 17 из GLE-RD-(P0-72-110)-N 2600_02.pdf
""".strip()

pattern4 = re.compile(r'Страница\s+(\d+)\s+из\s+(.+?)\.pdf', re.MULTILINE)

pages4, names4 = [], []
for page, name in pattern4.findall(data4):
    pages4.append(page.strip())
    names4.append(name.strip())

print("\nРезультат для формата 4 (имена):")
for row in names4:
    print(row)
print("\nРезультат для формата 4 (страницы):")
for row in pages4:
    print(row)
