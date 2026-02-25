from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction

def crear_toolbar(window):
    toolbar = QToolBar("Barra Principal")
    window.addToolBar(toolbar)

    accion_compilar = QAction("Compilar", window)
    toolbar.addAction(accion_compilar)
    accion_compilar.triggered.connect(window.compile_code)