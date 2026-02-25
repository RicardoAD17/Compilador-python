from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from editor import CodeEditor
from status_bar import actualizar_posicion
from tool_bar import crear_toolbar
from menu_bar import crear_menu

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Python")

        # Editor
        self.editor = CodeEditor()
        self.editor.cursorPositionChanged.connect(
            lambda: actualizar_posicion(self.editor, self.statusBar())
        )

        layout = QVBoxLayout()
        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Barras
        crear_toolbar(self)
        crear_menu(self)

        # Estado
        self.statusBar()

    def compile_code(self):
        code = self.editor.toPlainText()
        print("Código a compilar:")
        print(code)