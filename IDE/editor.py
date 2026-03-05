from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtGui import QPainter, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QRect

class LineNumberArea(QWidget):
    """Widget que dibuja los números de línea en el margen."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.editor.line_number_area_width(), 0

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True # Por defecto iniciamos en oscuro
        
        # 1. Configurar fuente tipo código (Monoespaciada)
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # 2. Desactivar salto de línea automático (vital para editores de código)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Instanciar el área de números
        self.line_number_area = LineNumberArea(self)

        # Conectar señales
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

    def set_theme(self, is_dark):
        self.is_dark_theme = is_dark
        self.line_number_area.update() # Fuerza a redibujar la barra de números

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        
        # Ajustamos el padding para que respire un poco más
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)

        # --- Lógica de colores según el tema ---
        if self.is_dark_theme:
            bg_color = QColor("#2b2b2b") # Gris oscuro
            text_color = QColor("#858585") # Letras gris claro
        else:
            bg_color = QColor("#f0f0f0") # Gris muy claro
            text_color = QColor("#555555") # Letras gris oscuro

        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                text_color.setAlpha(150) 
                painter.setPen(text_color)
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1