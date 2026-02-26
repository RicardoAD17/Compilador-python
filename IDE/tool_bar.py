from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction

def crear_toolbar(window):
    toolbar = QToolBar("Barra de Compilación")
    window.addToolBar(toolbar)

    # Acciones de acceso rápido
    accion_lexico = QAction("Léxico", window)
    accion_sintactico = QAction("Sintáctico", window)
    accion_semantico = QAction("Semántico", window)
    accion_intermedio = QAction("C. Intermedio", window)
    accion_ejecucion = QAction("Ejecutar", window)

    toolbar.addAction(accion_lexico)
    toolbar.addAction(accion_sintactico)
    toolbar.addAction(accion_semantico)
    toolbar.addAction(accion_intermedio)
    toolbar.addSeparator()
    toolbar.addAction(accion_ejecucion)

    # Conexiones a los mismos métodos
    accion_lexico.triggered.connect(window.run_lexico)
    accion_sintactico.triggered.connect(window.run_sintactico)
    accion_semantico.triggered.connect(window.run_semantico)
    accion_intermedio.triggered.connect(window.run_intermedio)
    accion_ejecucion.triggered.connect(window.run_ejecucion)