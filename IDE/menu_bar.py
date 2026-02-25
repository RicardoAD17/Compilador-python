from PyQt6.QtGui import QAction

def crear_menu(window):
    menubar = window.menuBar()

    menu_archivo = menubar.addMenu("Archivo")
    menu_compilar = menubar.addMenu("Compilar")
    menu_ayuda = menubar.addMenu("Ayuda")

    accion_nuevo = QAction("Nuevo", window)
    accion_salir = QAction("Salir", window)
    accion_abrir = QAction("Abrir", window)
    accion_cerrar = QAction("Cerrar",window)
    accion_guardar = QAction("Guardar", window)
    accion_guardar_como = QAction("Guardar Como", window)

    menu_archivo.addAction(accion_nuevo)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_salir)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_abrir)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_cerrar)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_guardar)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_guardar_como)
    accion_salir.triggered.connect(window.close)