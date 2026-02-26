from PyQt6.QtGui import QAction

def crear_menu(window):
    menubar = window.menuBar()

    menu_archivo = menubar.addMenu("Archivo")
    menu_compilar = menubar.addMenu("Compilar")
    menu_ayuda = menubar.addMenu("Ayuda")

    # --- Menú Archivo ---
    accion_nuevo = QAction("Nuevo", window)
    accion_abrir = QAction("Abrir", window)
    accion_cerrar = QAction("Cerrar", window)
    accion_guardar = QAction("Guardar", window)
    accion_guardar_como = QAction("Guardar Como", window)
    accion_salir = QAction("Salir", window)

    menu_archivo.addAction(accion_nuevo)
    menu_archivo.addAction(accion_abrir)
    menu_archivo.addAction(accion_cerrar)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_guardar)
    menu_archivo.addAction(accion_guardar_como)
    menu_archivo.addSeparator()
    menu_archivo.addAction(accion_salir)
    
    accion_salir.triggered.connect(window.close)

    # --- Menú Compilar ---
    accion_lexico = QAction("Análisis Léxico", window)
    accion_sintactico = QAction("Análisis Sintáctico", window)
    accion_semantico = QAction("Análisis Semántico", window)
    accion_intermedio = QAction("Código Intermedio", window)
    accion_ejecucion = QAction("Ejecución", window)

    menu_compilar.addAction(accion_lexico)
    menu_compilar.addAction(accion_sintactico)
    menu_compilar.addAction(accion_semantico)
    menu_compilar.addAction(accion_intermedio)
    menu_compilar.addSeparator()
    menu_compilar.addAction(accion_ejecucion)

    # Conexiones a los métodos de la ventana
    accion_lexico.triggered.connect(window.run_lexico)
    accion_sintactico.triggered.connect(window.run_sintactico)
    accion_semantico.triggered.connect(window.run_semantico)
    accion_intermedio.triggered.connect(window.run_intermedio)
    accion_ejecucion.triggered.connect(window.run_ejecucion)