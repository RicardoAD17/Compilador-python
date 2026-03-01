from PyQt6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QTextEdit, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from editor import CodeEditor
from status_bar import actualizar_posicion
from tool_bar import crear_toolbar
from menu_bar import crear_menu

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Python - Compilador")
        self.resize(1000, 700) # Un tamaño base ligeramente más grande

        # --- Variable para rastrear el archivo actual ---
        self.current_file = None

        # 1. Instanciar el Editor
        self.editor = CodeEditor()
        self.editor.cursorPositionChanged.connect(
            lambda: actualizar_posicion(self.editor, self.statusBar())
        )

        # 2. Panel Superior Derecho: Fases de Análisis y Tabla de Símbolos
        self.tabs_derechos = QTabWidget()
        self.tabs_derechos.addTab(QTextEdit(), "Análisis Léxico")
        self.tabs_derechos.addTab(QTextEdit(), "Análisis Sintáctico")
        self.tabs_derechos.addTab(QTextEdit(), "Análisis Semántico")
        self.tabs_derechos.addTab(QTextEdit(), "Código Intermedio")
        self.tabs_derechos.addTab(QTextEdit(), "Tabla de Símbolos")

        # 3. Panel Inferior (Ancho completo): Ejecución y Errores
        self.tabs_inferiores = QTabWidget()
        self.tabs_inferiores.addTab(QTextEdit(), "Ejecución / Salida")
        self.tabs_inferiores.addTab(QTextEdit(), "Errores Léxicos")
        self.tabs_inferiores.addTab(QTextEdit(), "Errores Sintácticos")
        self.tabs_inferiores.addTab(QTextEdit(), "Errores Semánticos")

        # 4. Configurar las divisiones (QSplitter)
        # Primero dividimos la parte superior: Editor (Izquierda) vs Análisis (Derecha)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.editor)
        top_splitter.addWidget(self.tabs_derechos)
        top_splitter.setSizes([600, 400]) # Damos más espacio inicial al editor

        # Luego dividimos la ventana principal: Parte Superior vs Panel Inferior
        # Al poner el top_splitter arriba y los tabs inferiores abajo, 
        # el panel inferior ocupará todo el ancho de la ventana.
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.tabs_inferiores)
        main_splitter.setSizes([500, 200]) # La consola inferior es más pequeña

        # 5. Establecer el layout principal
        self.setCentralWidget(main_splitter)

        # Barras
        crear_toolbar(self)
        crear_menu(self)

        # Estado
        self.statusBar()

    def run_lexico(self):
        print("Ejecutando Análisis Léxico...")
        # Aquí más adelante harás la llamada al sistema (system call)

    def run_sintactico(self):
        print("Ejecutando Análisis Sintáctico...")

    def run_semantico(self):
        print("Ejecutando Análisis Semántico...")

    def run_intermedio(self):
        print("Generando Código Intermedio...")

    def run_ejecucion(self):
        print("Ejecutando el programa...")

    
    # ==========================================
    # MÉTODOS DE GESTIÓN DE ARCHIVOS (NUEVOS)
    # ==========================================
    def nuevo_archivo(self):
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("IDE Python - Compilador (Nuevo Archivo)")

    def abrir_archivo(self):
        # Abre el diálogo nativo para buscar archivos
        archivo_ruta, _ = QFileDialog.getOpenFileName(
            self, 
            "Abrir Archivo", 
            "", 
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
        
        if archivo_ruta:
            try:
                with open(archivo_ruta, 'r', encoding='utf-8') as archivo:
                    contenido = archivo.read()
                    self.editor.setPlainText(contenido)
                    self.current_file = archivo_ruta
                    self.setWindowTitle(f"IDE Python - Compilador ({archivo_ruta})")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{str(e)}")

    def guardar_archivo(self):
        # Si ya hay un archivo abierto, lo sobreescribe
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as archivo:
                    archivo.write(self.editor.toPlainText())
                    QMessageBox.information(self, "Éxito", "Archivo guardado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")
        else:
            # Si no hay archivo previo, llama a "Guardar Como"
            self.guardar_como()

    def guardar_como(self):
        archivo_ruta, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Como", 
            "", 
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
        
        if archivo_ruta:
            try:
                with open(archivo_ruta, 'w', encoding='utf-8') as archivo:
                    archivo.write(self.editor.toPlainText())
                    self.current_file = archivo_ruta
                    self.setWindowTitle(f"IDE Python - Compilador ({archivo_ruta})")
                    QMessageBox.information(self, "Éxito", "Archivo guardado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")