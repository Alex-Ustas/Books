from PyQt6.QtWidgets import QStyleOptionFrame, QWidget, QLabel, QPushButton, QComboBox, QPlainTextEdit, QLineEdit
from PyQt6.QtGui import QIcon, QPainter, QColor
from PyQt6.QtCore import QSize

TEXT_COLOR = '#3E4E22'  # тёмно-зеленый


class Label(QLabel):
    def __init__(self, text: str, fixed_width=0, fixed_height=30):
        super().__init__(text)
        self.setStyleSheet(f'color: {TEXT_COLOR}; font-size: 16px; font-weight: bold')
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)


class EditBox(QLineEdit):
    def __init__(self, text='', fixed_width=0, fixed_height=30, enabled=True, optional=False):
        super().__init__(text)
        self.optional = optional
        self.setEnabled(enabled)
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)

        self._base_style = f'color: {TEXT_COLOR}; font-size: 16px; font-weight: bold'

        self._border_color = None
        self.update_border_color()

        self.textChanged.connect(self.update_border_color)

    def update_border_color(self, txt='', forced=False):
        is_empty = self.text().strip() == ''
        self._border_color = 'red' if is_empty and not self.optional or forced else 'black'
        bg_color = 'white' if self.isEnabled() else '#ddd'

        if not self.isEnabled():
            self._border_color = 'red' if is_empty and not self.optional or forced else '#aaaaaa'

        style = f'{self._base_style}; background-color: {bg_color}'
        self.setStyleSheet(style)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionFrame()
        opt.initFrom(self)
        opt.lineWidth = 2
        opt.midLineWidth = 0

        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.setPen(QColor(self._border_color))
        painter.drawRect(rect)


class PlainText(QPlainTextEdit):
    def __init__(self, text='', fixed_width=0, fixed_height=0):
        super().__init__(text)
        self.setStyleSheet(f'color: {TEXT_COLOR}; font-size: 14px; border: 2px solid black')
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)


class Button(QPushButton):
    def __init__(self, text: str, fixed_width=0, fixed_height=40, icon_size=16):
        super().__init__()
        self.setText(text)
        self.setStyleSheet(f"""
            QPushButton {{font-size: 16px; font-weight: bold; color: {TEXT_COLOR}; border: 2px groove #c0c0c0; border-radius: 6px;
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #f0f0f0, stop: 1 #d0d0d0)}}
            QPushButton::disabled {{background-color: #D9D9D9; color: gray; font-weight: bold}}
            QPushButton::hover {{background-color: {TEXT_COLOR}; color: white; font-weight: bold}}
            """)
        self.setIconSize(QSize(icon_size, icon_size))
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)


class ComboList(QComboBox):
    def __init__(self, fixed_width=0, fixed_height=30, editable=False):
        super().__init__()
        self.setMaxVisibleItems(10)
        self.setEditable(editable)
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)

        self._base_style = f'color: {TEXT_COLOR}; font-size: 16px'
        self.setStyleSheet(self._base_style)

        self._border_color = None
        self.update_border_color()

        self.currentTextChanged.connect(self.update_border_color)

    def update_border_color(self):
        is_empty = self.currentText().strip() == ''
        self._border_color = 'red' if is_empty else 'black'
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionFrame()
        opt.initFrom(self)
        opt.lineWidth = 2

        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.setPen(QColor(self._border_color))
        painter.drawRect(rect)


class Window(QWidget):
    def __init__(self, text: str, width=300, height=300):
        super().__init__()
        self.setMinimumSize(width, height)
        self.setWindowTitle(text)
        self.setWindowIcon(QIcon('images/book.png'))

    def delete_widgets(self, layout):
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            child_layout = item.layout()
            if child_layout is not None:
                self.delete_widgets(child_layout)
                child_layout.deleteLater()
