# Create book in fb2 format from text file

import sys, os
from pathlib import Path
from typing import Union

from fb2_converter import parse_txt_to_book_structure, create_fb2
from models import Book
from storage import load_books, save_books
from widgets import Label, EditBox, PlainText, Button, ComboList, Window

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt

TEXT_COLOR = '#3E4E22'  # тёмно-зеленый
DATA_DIR = Path("data")
BOOKS_FILE = DATA_DIR / "books.json"


class BookWindow(Window):
    def __init__(self):
        super().__init__('Книги', width=800, height=600)
        self.books = load_books(BOOKS_FILE)
        if self.books:
            self.current_book = self.books[list(self.books.keys())[-1]].copy()
        else:
            self.current_book = Book.empty_book()

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # Список книг
        book_list_layout = QHBoxLayout()
        self.book_name_combo = ComboList(fixed_width=350, editable=True)
        self.book_name_combo.addItems(self.books.keys())
        self.book_name_combo.setCurrentText(self.current_book.name)
        self.book_name_combo.currentTextChanged.connect(self._on_book_list_changed)

        book_list_layout.addWidget(Label('Список книг'))
        book_list_layout.addSpacing(29)
        book_list_layout.addWidget(self.book_name_combo)
        book_list_layout.addStretch()

        # Название книги
        book_title_layout = QHBoxLayout()
        self.book_title_editbox = EditBox()
        self.book_title_editbox.textChanged.connect(self._on_book_title_changed)

        book_title_layout.addWidget(Label('Название книги'))
        book_title_layout.addWidget(self.book_title_editbox)

        # Автор
        book_author_layout = QHBoxLayout()
        self.author_firstname_editbox = EditBox(fixed_width=200)
        self.author_firstname_editbox.textChanged.connect(self._on_author_firstname_changed)

        self.author_lastname_editbox = EditBox(fixed_width=200)
        self.author_lastname_editbox.textChanged.connect(self._on_author_lastname_changed)

        book_author_layout.addWidget(Label('Имя автора'))
        book_author_layout.addSpacing(34)
        book_author_layout.addWidget(self.author_firstname_editbox)
        book_author_layout.addSpacing(20)
        book_author_layout.addWidget(Label('Фамилия автора'))
        book_author_layout.addWidget(self.author_lastname_editbox)
        book_author_layout.addStretch()

        # Аннотация
        book_annotation_layout = QHBoxLayout()
        annotation_label = Label('Аннотация')
        self.book_annotation_text = PlainText(fixed_height=240)
        self.book_annotation_text.textChanged.connect(self._on_annotation_changed)

        book_annotation_layout.addWidget(annotation_label)
        book_annotation_layout.addSpacing(40)
        book_annotation_layout.addWidget(self.book_annotation_text)
        book_annotation_layout.setAlignment(annotation_label, Qt.AlignmentFlag.AlignTop)

        # Папка
        folder_layout = QHBoxLayout()
        self.folder_editbox = EditBox(enabled=False)

        btn_assign_folder = Button('...', fixed_width=30, fixed_height=30)
        btn_assign_folder.clicked.connect(self.on_assign_folder)

        folder_layout.addWidget(Label('Папка с книгой'))
        folder_layout.addSpacing(5)
        folder_layout.addWidget(self.folder_editbox)
        folder_layout.addWidget(btn_assign_folder)

        # Файл txt
        txt_file_layout = QHBoxLayout()
        self.txt_file_editbox = EditBox(enabled=False)

        btn_assign_txt_file = Button('...', fixed_width=30, fixed_height=30)
        btn_assign_txt_file.clicked.connect(self.on_assign_txt_file)

        txt_file_layout.addWidget(Label('Текстовый файл'))
        txt_file_layout.addWidget(self.txt_file_editbox)
        txt_file_layout.addWidget(btn_assign_txt_file)

        # Титульная картинка
        image_file_layout = QHBoxLayout()
        self.image_file_editbox = EditBox(enabled=False, optional=True)

        btn_assign_image_file = Button('...', fixed_width=30, fixed_height=30)
        btn_assign_image_file.clicked.connect(self.on_assign_image_file)

        image_file_layout.addWidget(Label('Картинка'))
        image_file_layout.addSpacing(52)
        image_file_layout.addWidget(self.image_file_editbox)
        image_file_layout.addWidget(btn_assign_image_file)

        # Полное название файла
        self.fullname_label = Label('')

        # Кнопки
        bottom_buttons_layout = QHBoxLayout()
        btn_create = Button("Создать fb2")
        btn_create.clicked.connect(self.on_create_fb2)
        bottom_buttons_layout.addWidget(btn_create)

        btn_open = Button("Открыть")
        btn_open.clicked.connect(self.on_open)
        bottom_buttons_layout.addWidget(btn_open)

        btn_save = Button("Сохранить")
        btn_save.clicked.connect(self.on_save)
        bottom_buttons_layout.addWidget(btn_save)

        btn_delete = Button("Удалить")
        btn_delete.clicked.connect(self.on_delete)
        bottom_buttons_layout.addWidget(btn_delete)

        btn_close = Button("Закрыть")
        btn_close.clicked.connect(self.on_close)
        bottom_buttons_layout.addWidget(btn_close)

        # main layout
        main_layout.addLayout(book_list_layout)
        main_layout.addLayout(book_title_layout)
        main_layout.addLayout(book_author_layout)
        main_layout.addLayout(book_annotation_layout)
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(txt_file_layout)
        main_layout.addLayout(image_file_layout)
        main_layout.addWidget(self.fullname_label)
        main_layout.addStretch()
        main_layout.addLayout(bottom_buttons_layout)
        self.setLayout(main_layout)

        self.update_book_data()
        self.update_fullname_label()
        self.check_files_and_folders_exists()

    def update_book_data(self):
        self.book_title_editbox.setText(self.current_book.title_book)
        self.author_firstname_editbox.setText(self.current_book.author_first)
        self.author_lastname_editbox.setText(self.current_book.author_last)
        self.book_annotation_text.setPlainText(self.current_book.annotation)
        self.folder_editbox.setText(str(self.relative_path(self.current_book.folder)))
        self.txt_file_editbox.setText(self.current_book.book_name_txt)
        self.image_file_editbox.setText(self.current_book.book_image)

    def update_fullname_label(self):
        text = ''
        if self.current_book.is_valid():
            text = f'Полное название книги: {self.current_book.fullname}.fb2'
        self.fullname_label.setText(text)

    def _on_book_list_changed(self):
        name = self.book_name_combo.currentText().strip()
        if name in self.books:
            self.current_book = self.books[name].copy()
        else:
            self.current_book = Book.empty_book()
            self.current_book.name = name
        self.update_book_data()
        self.update_fullname_label()
        self.check_files_and_folders_exists()

    def _on_book_title_changed(self):
        self.current_book.title_book = self.book_title_editbox.text()
        self.update_fullname_label()

    def _on_author_firstname_changed(self):
        self.current_book.author_first = self.author_firstname_editbox.text()
        self.update_fullname_label()

    def _on_author_lastname_changed(self):
        self.current_book.author_last = self.author_lastname_editbox.text()
        self.update_fullname_label()

    def _on_annotation_changed(self):
        self.current_book.annotation = self.book_annotation_text.toPlainText()

    @staticmethod
    def relative_path(folder: Union[str, Path]) -> Path:
        script_dir = Path(__file__).resolve().parent
        if isinstance(folder, str):
            folder = Path(folder)
        if not folder.exists() or not folder.is_dir():
            return Path('')
        try:
            rel_path = folder.relative_to(script_dir)
            return rel_path
        except ValueError:
            if folder.exists() and folder.is_dir():
                return folder
            return Path('')

    def on_assign_folder(self):
        folder = Path(QFileDialog.getExistingDirectory(self, "Выберите папку с книгой"))
        if not folder or str(folder) == '.':
            return
        try:
            rel_path = self.relative_path(folder)
            folder_str = str(rel_path.resolve()) if str(rel_path) == '.' else str(rel_path)
        except ValueError:
            folder_str = str(folder)
        self.folder_editbox.setText(folder_str)
        self.current_book.folder = str(folder.as_posix())
        self.update_fullname_label()
        self.check_files_and_folders_exists()

    def on_assign_txt_file(self):
        temp = self.current_book.book_name_txt
        try:
            filename, _ = QFileDialog.getOpenFileName(self, 'Выберите текстовый файл с книгой', '',
                                                      'Text files (*.txt)')
            filename = Path(filename).name
            filename = temp if not filename else filename
        except Exception:
            filename = ''
        self.txt_file_editbox.setText(filename)
        self.current_book.book_name_txt = filename
        self.update_fullname_label()
        self.check_files_and_folders_exists()

    def on_assign_image_file(self):
        temp = self.current_book.book_image
        try:
            filename, _ = QFileDialog.getOpenFileName(self, 'Выберите титульную картинку', '',
                                                      'Image files (*.jpeg *.jpg *.png *.gif);;All files (*)')
            filename = Path(filename).name
            filename = temp if not filename else filename
        except Exception:
            filename = ''
        self.image_file_editbox.setText(filename)
        self.current_book.book_image = filename
        self.check_files_and_folders_exists()

    def _refresh_list(self):
        self.book_name_combo.blockSignals(True)
        self.book_name_combo.clear()
        self.book_name_combo.addItems(self.books.keys())
        self.book_name_combo.setCurrentText(self.current_book.name)
        self.book_name_combo.blockSignals(False)

    def check_files_and_folders_exists(self):
        folder = Path(self.current_book.folder)
        book_txt = Path(self.current_book.book_name_txt)
        book_image = Path(self.current_book.book_image)

        self.folder_editbox.update_border_color(forced=not folder.exists())
        self.txt_file_editbox.update_border_color(forced=not (folder / book_txt).exists())
        self.image_file_editbox.update_border_color(forced=book_image and not (folder / book_image).exists())

    def check_book_data(self) -> bool:
        if self.current_book.is_valid():
            return True
        error = []
        if not self.current_book.name:
            error.append('Название книги для списка не указано')
        if not self.current_book.title_book:
            error.append('Название книги не указано')
        if not self.current_book.author_first:
            error.append('Имя автора не указано')
        if not self.current_book.author_last:
            error.append('Фамилия автора не указана')
        if not self.current_book.folder:
            error.append('Папка с файлами книги не указана')
        if not self.current_book.book_name_txt:
            error.append('Текстовый файл книги не указан')
        if not (Path(self.current_book.folder) / Path(self.current_book.book_name_txt)).exists():
            error.append('Текстовый файл книги не найден')
        QMessageBox.warning(self, "Отсутствуют данные", f"Укажите корректные данные:\n{'\n'.join(error)}")
        return False

    def on_create_fb2(self):
        if not self.check_book_data():
            return
        folder = Path(self.current_book.folder)
        book_name_txt = Path(self.current_book.book_name_txt)
        chapters = parse_txt_to_book_structure(folder / book_name_txt, self.current_book)
        create_fb2(chapters, self.current_book)
        QMessageBox.information(self, "Успешно", f"Файл сохранён в\n{self.current_book.fullname}.fb2")

    def on_open(self):
        file = Path(self.current_book.folder) / (self.current_book.fullname + '.fb2')
        if file.exists():
            os.startfile(file)
        else:
            QMessageBox.warning(self, "Невозможно открыть файл", f"Файл не найден!\nФайл: {file}")

    def on_save(self):
        if not self.check_book_data():
            return
        self.books[self.current_book.name] = self.current_book.copy()
        save_books(BOOKS_FILE, self.books)
        self._refresh_list()
        QMessageBox.information(self, "Успешно", f"Результат сохранён в {BOOKS_FILE}")

    def on_delete(self):
        name = self.current_book.name
        if not name:
            QMessageBox.warning(self, "Невозможно удалить", "Книга не выбрана!")
            return
        if name not in self.books:
            QMessageBox.warning(self, "Невозможно удалить", f"«{name}» -\nнет такой книги в сохраненных!")
            return
        reply = QMessageBox.question(self, "Удаление данных книги",
                                     f"Вы действительно хотите удалить всю информацию по книге\n«{name}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        del self.books[name]
        if self.books:
            self.current_book = self.books[list(self.books.keys())[-1]].copy()
        else:
            self.current_book = Book.empty_book()
        self._refresh_list()
        self.update_book_data()
        self.update_fullname_label()
        self.check_files_and_folders_exists()

    def on_close(self):
        self.close()


# Unhandled exception interceptor
def excepthook(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BookWindow()
    window.show()
    sys.excepthook = excepthook
    sys.exit(app.exec())
