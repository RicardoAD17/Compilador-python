from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

def crear_toolbar(window):
    # --- BARRA DE ARCHIVOS (Nueva) ---
    file_toolbar = QToolBar("Barra de Archivos")
    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, file_toolbar)
    
    # Obtenemos los iconos estándar del sistema para que se vea profesional
    style = window.style()
    icon_nuevo = style.standardIcon(style.StandardPixmap.SP_FileIcon)
    icon_abrir = style.standardIcon(style.StandardPixmap.SP_DirOpenIcon)
    icon_guardar = style.standardIcon(style.StandardPixmap.SP_DialogSaveButton)
    icon_guardar_como = style.standardIcon(style.StandardPixmap.SP_DriveHDIcon)
    icon_cerrar = style.standardIcon(style.StandardPixmap.SP_BrowserStop)

    # Crear acciones con iconos
    accion_nuevo = QAction(icon_nuevo, "Nuevo", window)
    accion_abrir = QAction(icon_abrir, "Abrir", window)
    accion_guardar = QAction(icon_guardar, "Guardar", window)
    accion_guardar_como = QAction(icon_guardar_como, "Guardar Como", window)
    accion_cerrar = QAction(icon_cerrar, "Cerrar Archivo", window)

    # Añadir a la barra de archivos
    file_toolbar.addAction(accion_nuevo)
    file_toolbar.addAction(accion_abrir)
    file_toolbar.addAction(accion_guardar)
    file_toolbar.addAction(accion_guardar_como)
    file_toolbar.addAction(accion_cerrar)

    # Conectar a los mismos métodos funcionales de ide_window.py
    accion_nuevo.triggered.connect(window.nuevo_archivo)
    accion_abrir.triggered.connect(window.abrir_archivo)
    accion_guardar.triggered.connect(window.guardar_archivo)
    accion_guardar_como.triggered.connect(window.guardar_como)
    accion_cerrar.triggered.connect(window.nuevo_archivo) # "Cerrar" limpia el editor

    # Añadir un espacio o salto para que la de compilación quede abajo o separada
    window.insertToolBarBreak(file_toolbar) 

    # --- BARRA DE COMPILACIÓN (Existente) ---
    compile_toolbar = QToolBar("Barra de Compilación")
    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, compile_toolbar)

    accion_lexico = QAction("Léxico", window)
    accion_sintactico = QAction("Sintáctico", window)
    accion_semantico = QAction("Semántico", window)
    accion_intermedio = QAction("C. Intermedio", window)
    accion_ejecucion = QAction("Ejecutar", window)

    compile_toolbar.addAction(accion_lexico)
    compile_toolbar.addAction(accion_sintactico)
    compile_toolbar.addAction(accion_semantico)
    compile_toolbar.addAction(accion_intermedio)
    compile_toolbar.addSeparator()
    compile_toolbar.addAction(accion_ejecucion)

    # Conexiones de compilación
    accion_lexico.triggered.connect(window.run_lexico)
    accion_sintactico.triggered.connect(window.run_sintactico)
    accion_semantico.triggered.connect(window.run_semantico)
    accion_intermedio.triggered.connect(window.run_intermedio)
    accion_ejecucion.triggered.connect(window.run_ejecucion)