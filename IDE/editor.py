from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRect

class LineNumberArea(QWidget):
    """
    Widget personalizado que dibuja los números de línea.
    Se coloca en el margen izquierdo del CodeEditor.
    """
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        # Le pregunta al editor qué tan ancha debe ser esta área
        return self.editor.line_number_area_width(), 0

    def paintEvent(self, event):
        # Delega la tarea de dibujar los números al propio editor
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        
        # Instanciar el área de números de línea
        self.line_number_area = LineNumberArea(self)

        # Conectar señales para actualizar el área cuando el texto cambie o haya scroll
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        # Inicializar el margen izquierdo para hacer espacio para los números
        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        """Calcula el ancho necesario basado en la cantidad total de líneas."""
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        
        # Añade un poco de padding (espacio extra) para que no se vea amontonado
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Establece el margen izquierdo del QPlainTextEdit."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Maneja el scroll para mantener los números sincronizados con el texto."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Ajusta el tamaño del área de números cuando se redimensiona la ventana."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """Dibuja físicamente el fondo y los números en el widget izquierdo."""
        painter = QPainter(self.line_number_area)
        
        # Dibujar el fondo del área de números (un gris muy claro)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))

        # Obtener el primer bloque (línea) visible
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        # Iterar sobre todos los bloques visibles para dibujar su número
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.gray)
                
                # Dibujar el texto alineado a la derecha
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1