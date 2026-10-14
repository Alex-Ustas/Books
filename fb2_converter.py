# fb2_converter.py
# Markers in text:
#   #### - chapter
#   ### - subtitle
#   ** - bold text
#   __ - italic text (strong sequence: bold marker, then italic marker if both)
#   several (2+) empty lines in sequence in text transformed to one empty line in fb2

import re, os, html
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict, Any

from models import Book

EMPTY_LINE = '__EMPTY_LINE__'
CHAPTER_MARKER = '####'
SUBSECTION_MARKER = '###'

BOLD_PATTERN = re.compile(r'\*\*(.*?)\*\*')
ITALIC_PATTERN = re.compile(r'__(.*?)__')
NOTE_PATTERN = re.compile(r'\[(\d+)]')
FOOTNOTE_PATTERN = re.compile(r'^(\d+)\)\s*(.*)')


def prettify(elem):
    rough_string = ET.tostring(elem, encoding='utf-8').decode('utf-8')
    rough_string = rough_string.replace('ns0:', 'l:')
    rough_string = rough_string.replace(' xmlns:ns0="http://www.w3.org/1999/xlink"', '')
    reparsed = minidom.parseString(rough_string.encode('utf-8'))
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')


def parse_txt_to_book_structure(filepath: Path, book_metadata: 'Book') -> List[Dict[str, Any]]:
    """
    Возвращает структуру:
    [
      {
        "title": "Глава 1",
        "subsections": [
          {"title": "Подглава 1.1", "paragraphs": [...]},
          ...
        ],
        "paragraphs": [...]  # текст до первой подглавы (если есть)
      },
      ...
    ]
    Маркеры:
      #### - глава
      ### - подглава
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Разбиваем на главы по ####
    parts = text.split(CHAPTER_MARKER)

    book_structure = []

    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue

        lines = [line.rstrip(' ') for line in part.splitlines()]

        # Сначала нормализуем пустые строки: 2+ пустых → один маркер
        normalized_lines = []
        j = 0
        while j < len(lines):
            if lines[j].strip():
                normalized_lines.append(lines[j])
                j += 1
            else:
                # считаем подряд идущие пустые строки
                empty_count = 0
                while j < len(lines) and not lines[j].strip():
                    empty_count += 1
                    j += 1
                if empty_count >= 2:
                    normalized_lines.append(EMPTY_LINE)
                # если 1 пустая строка — оставляем как есть (в FB2 это просто перенос)

        # Теперь разбираем главы и подглавы внутри части
        # Первая непустая строка после #### — заголовок главы
        chapter_title = None
        subsection_stack = []  # для хранения текущей подглавы
        current_paragraphs = []

        for line in normalized_lines:
            if line.strip() == SUBSECTION_MARKER:
                # Если есть накопленные параграфы — сохраняем их в текущую подглаву или главу
                if current_paragraphs:
                    if subsection_stack:
                        subsection_stack[-1]["paragraphs"].extend(current_paragraphs)
                    else:
                        # До первой подглавы — это текст главы
                        pass  # пока не сохраняем, будем собирать до конца или до следующей подглавы
                current_paragraphs = []
                # Начинаем новую подглаву
                subsection_stack.append({"title": None, "paragraphs": []})
                continue

            if line == EMPTY_LINE:
                if current_paragraphs and current_paragraphs[-1] != EMPTY_LINE:
                    current_paragraphs.append(EMPTY_LINE)
                continue

            # Проверяем, не является ли строка заголовком подглавы (на случай, если маркер ### был удалён при нормализации)
            # Но у нас маркер ### обрабатывается выше, так что тут просто текст
            if not chapter_title:
                # Первая непустая строка — заголовок главы
                chapter_title = line.strip()
                continue

            current_paragraphs.append(line)

        # Если остались накопленные параграфы
        if current_paragraphs:
            if subsection_stack:
                subsection_stack[-1]["paragraphs"].extend(current_paragraphs)
            else:
                # Текст главы до первой подглавы
                pass

        # Формируем главу
        chapter = {
            "title": chapter_title or book_metadata.fullname,
            "subsections": subsection_stack,
            "paragraphs_before_subsections": []
        }

        # ПЕРЕСОБЕРЁМ главу правильно
        chapter = _build_chapter_from_lines(normalized_lines, book_metadata)
        book_structure.append(chapter)

    return book_structure


def _build_chapter_from_lines(lines, book_metadata: 'Book') ->  Dict[str, Any]:
    """
    Строит одну главу с подглавами из списка строк.
    """
    footnotes = {}
    body_lines = []

    for line in lines:
        m = FOOTNOTE_PATTERN.match(line.strip())
        if m:
            num = int(m.group(1))
            footnotes[num] = m.group(2)
        else:
            body_lines.append(line)

    chapter = {
        "title": None,
        "paragraphs": [],
        "subsections": [],
        "footnotes": footnotes
    }
    current_subsection = None
    current_paragraphs = []

    idx = 0
    while idx < len(body_lines):
        line = body_lines[idx]

        if line.strip() == SUBSECTION_MARKER:
            # Сохраняем накопленные параграфы в главу (до первой подглавы) или в предыдущую подглаву
            if current_subsection:
                current_subsection["paragraphs"].extend(current_paragraphs)
            else:
                chapter["paragraphs"] = current_paragraphs

            current_paragraphs = []
            # Начинаем новую подглаву: заголовок будет на следующей строке
            idx += 1
            if idx < len(lines) and lines[idx].strip():
                sub_title = lines[idx].strip()
                idx += 1
            else:
                sub_title = f"Подглава {len(chapter['subsections']) + 1}"
                idx += 1

            current_subsection = {"title": sub_title, "paragraphs": []}
            chapter["subsections"].append(current_subsection)
            continue

        if line == EMPTY_LINE:
            if current_paragraphs and current_paragraphs[-1] != EMPTY_LINE:
                current_paragraphs.append(EMPTY_LINE)
            idx += 1
            continue

        if not chapter["title"]:
            # Первая непустая строка — заголовок главы
            chapter["title"] = line.strip()
            idx += 1
            continue

        current_paragraphs.append(line)
        idx += 1

    # Сохраняем оставшиеся параграфы
    if current_subsection:
        current_subsection["paragraphs"].extend(current_paragraphs)
    else:
        chapter["paragraphs"].extend(current_paragraphs)

    if not chapter["title"]:
        chapter["title"] = book_metadata.fullname

    return chapter


def create_fb2(book_structure, book_metadata: 'Book'):
    root = ET.Element("FictionBook", {
        "xmlns:l": "http://www.w3.org/1999/xlink",
        "xmlns": "http://www.gribuser.ru/xml/fictionbook/2.0"
    })

    title_book = book_metadata.title_book
    author_first = book_metadata.author_first
    author_last = book_metadata.author_last
    annotation = book_metadata.annotation
    subtitle = book_metadata.fullname
    output_path = Path(book_metadata.folder) / f'{subtitle}.fb2'

    description = ET.SubElement(root, "description")
    title_info = ET.SubElement(description, "title-info")

    book_title = ET.SubElement(title_info, "book-title")
    book_title.text = title_book

    # Обложка
    if book_metadata.book_image:
        image_path = Path(book_metadata.folder) / book_metadata.book_image
        if os.path.isfile(image_path):
            _, ext = os.path.splitext(image_path)
            ext = ext.lower().replace('.', '')
            mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif'}
            mime = mime_map.get(ext, 'image/jpeg')

            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('ascii')

            binary = ET.SubElement(root, "binary", {"id": "cover", "content-type": mime})
            binary.text = image_base64

            coverpage = ET.SubElement(title_info, "coverpage")
            ET.SubElement(coverpage, "image", {"l:href": "#cover"})

    # Аннотация
    if annotation:
        annotation_text = ET.SubElement(title_info, "annotation")
        p = ET.SubElement(annotation_text, "p")
        p.text = subtitle
        ET.SubElement(annotation_text, 'empty-line')
        p = ET.SubElement(annotation_text, "p")
        p.text = annotation

    # Автор
    author = ET.SubElement(title_info, "author")
    first_name = ET.SubElement(author, "first-name")
    first_name.text = author_first
    last_name = ET.SubElement(author, "last-name")
    last_name.text = author_last

    lang = ET.SubElement(title_info, "lang")
    lang.text = "ru"

    body = ET.SubElement(root, "body")

    # Шаблоны разметки
    def apply_markup(txt: str) -> str:
        escaped = html.escape(txt)
        with_bold = BOLD_PATTERN.sub(r'<strong>\1</strong>', escaped)
        with_italic = ITALIC_PATTERN.sub(r'<emphasis>\1</emphasis>', with_bold)
        with_notes = NOTE_PATTERN.sub(r'<a l:href="#n_\1" type="note">[\1]</a>', with_italic)
        return with_notes

    def add_paragraphs_to_parent(parent_elem, paragraphs):
        for para in paragraphs:
            if para == EMPTY_LINE:
                ET.SubElement(parent_elem, 'empty-line')
                continue

            formatted_text = apply_markup(para)
            # Безопасный разбор HTML-фрагмента
            temp_root = ET.fromstring(f'<root xmlns:l="http://www.w3.org/1999/xlink">{formatted_text}</root>')
            p_elem = ET.SubElement(parent_elem, "p")
            if temp_root.text and temp_root.text.strip():
                p_elem.text = temp_root.text
            for child in temp_root:
                p_elem.append(child)

    # Создаём главы и подглавы
    for chap in book_structure:
        section = ET.SubElement(body, "section")
        title = ET.SubElement(section, "title")
        p_title = ET.SubElement(title, "p")
        p_title.text = chap["title"]

        # Текст до подглав
        if chap["paragraphs"]:
            add_paragraphs_to_parent(section, chap["paragraphs"])

        # Подглавы
        for sub_idx, sub in enumerate(chap["subsections"]):
            # Каждая следующая (или первая, если был текст до неё) подглава —
            # отдельная вложенная <section> → новая страница
            sub_section = ET.SubElement(section, "section")
            sub_title = ET.SubElement(sub_section, "title")
            p_sub = ET.SubElement(sub_title, "p")
            p_sub.text = sub["title"]
            add_paragraphs_to_parent(sub_section, sub["paragraphs"])

    # Собираем все сноски из всех глав
    all_footnotes = {}
    for chap in book_structure:
        for num, text in chap.get("footnotes", {}).items():
            all_footnotes[num] = text

    if all_footnotes:
        notes_body = ET.SubElement(root, "body", {"name": "notes"})
        notes_title = ET.SubElement(notes_body, "title")
        notes_title_p = ET.SubElement(notes_title, "p")
        notes_title_p.text = "Примечания"

        for num in sorted(all_footnotes):
            note_section = ET.SubElement(notes_body, "section", {"id": f"n_{num}"})
            note_title = ET.SubElement(note_section, "title")
            note_title_p = ET.SubElement(note_title, "p")
            note_title_p.text = str(num)
            note_p = ET.SubElement(note_section, "p")
            note_p.text = all_footnotes[num]

    xml_str = prettify(root)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
