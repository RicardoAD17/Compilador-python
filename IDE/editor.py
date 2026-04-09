from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtGui import QPainter, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression
from analizador_lexico.analizador import TOKEN_ESPECIFICATION
class LineNumberArea(QWidget):
    """Widget que dibuja los números de línea en el margen."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.editor.line_number_area_width(), 0

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)
class ResaltadorLexico(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.reglas = []

        # 1. Definimos un "Diccionario de Colores" basado en los NOMBRES de tus tokens
        colores = {
            'ENTERO': QColor("#D19A66"),               # Color 1
            'FLOTANTE': QColor("#D19A66"),             # Color 1
            'IDENTIFICADORES': QColor("#E06C75"),      # Color 2
            'COMENTARIO_LINEA': QColor("#98C379"),     # Color 3
            'PALABRAS_RESERVADAS': QColor("#C678DD"),  # Color 4
            'OP_ARIT': QColor("#56B6C2"),              # Color 5
            'OP_RELACIONAL': QColor("#E5C07B"),        # Color 6
            'OP_LOG': QColor("#E5C07B"),               # Color 6
            'STRING': QColor("#ABB2BF"),               # Cadenas
            'CHAR': QColor("#ABB2BF"),                 # Caracteres
            'SIMBOLOS': QColor("#ABB2BF"),             # Símbolos
            'ASIGNACION': QColor("#ABB2BF")            # Asignación
        }

        # 2. Recorremos TU lista del analizador para crear las reglas visuales.
        # Usamos reversed() porque en la interfaz gráfica, la última regla aplicada 
        # sobreescribe a las anteriores. Así aseguramos que Palabras Reservadas pinte
        # sobre Identificadores, y no al revés.
        for nombre, patron in reversed(TOKEN_ESPECIFICATION):
            if nombre in colores:
                formato = QTextCharFormat()
                formato.setForeground(colores[nombre])
                
                # Darle formato extra a ciertos tokens
                if nombre == 'PALABRAS_RESERVADAS':
                    formato.setFontWeight(QFont.Weight.Bold)
                elif nombre == 'COMENTARIO_LINEA':
                    formato.setFontItalic(True)
                    
                # Convertir tu Regex de Python (r'') a Regex de PyQt (QRegularExpression)
                self.reglas.append((QRegularExpression(patron), formato))

        # 3. Configuración manual solo para los comentarios Multilínea 
        # (Porque PyQt necesita tratarlos diferente visualmente debido a los saltos de línea)
        self.formato_coment_multi = QTextCharFormat()
        self.formato_coment_multi.setForeground(QColor("#98C379")) # Color 3
        self.formato_coment_multi.setFontItalic(True)
        self.inicio_comentario = QRegularExpression(r'/\*')
        self.fin_comentario = QRegularExpression(r'\*/')

    def highlightBlock(self, text):
        # Aplicar las reglas de una línea
        for patron, formato in self.reglas:
            iterador = patron.globalMatch(text)
            while iterador.hasNext():
                match = iterador.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), formato)

        # Aplicar comentarios multilínea
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            match_inicio = self.inicio_comentario.match(text)
            start_index = match_inicio.capturedStart()

        while start_index >= 0:
            match_fin = self.fin_comentario.match(text, start_index)
            end_index = match_fin.capturedStart()
            comentario_length = 0

            if end_index == -1:
                self.setCurrentBlockState(1) 
                comentario_length = len(text) - start_index
            else:
                comentario_length = end_index - start_index + match_fin.capturedLength()

            self.setFormat(start_index, comentario_length, self.formato_coment_multi)
            start_index = self.inicio_comentario.match(text, start_index + comentario_length).capturedStart()

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
        self.resaltador = ResaltadorLexico(self.document())

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