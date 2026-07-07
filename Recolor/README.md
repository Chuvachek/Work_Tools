Итого 4 новых механизма:

recolor_all_streams — вместо page.get_contents() + page.get_xobjects() (которые видят только content stream страницы и явные XObjects), теперь проходим по всем объектам PDF (doc.xref_length()) и патчим любой поток. Это закрывает appearance streams аннотаций/виджетов (/AP /N) — то, что раньше пропускалось.
recolor_annotation_dict_colors — было и раньше (просто вынесено отдельно), /C и /IC.
recolor_widget_mk — новое, для текстовых полей: /MK/BC, /MK/BG.
recolor_widget_da — новое, для текстовых полей: /DA (цвет текста как строка).