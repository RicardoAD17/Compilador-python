import os
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
        self.resize(1000, 700)

        self.contador_sin_nombre = 1 # Para nombrar "Sin Nombre 1", "Sin Nombre 2"...

        # 1. Instanciar el Contenedor de Pestañas del Editor
        self.tabs_editor = QTabWidget()
        self.tabs_editor.setTabsClosable(True) # Activar la 'X' en cada pestaña
        self.tabs_editor.tabCloseRequested.connect(self.cerrar_pestana) # Conectar la 'X'
        self.tabs_editor.currentChanged.connect(self.update_status) # Actualizar línea/columna al cambiar de pestaña

        # 2. Panel Superior Derecho: Fases de Análisis
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

        # 4. Configurar las divisiones
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.tabs_editor) # Ahora agregamos las pestañas, no un solo editor
        top_splitter.addWidget(self.tabs_derechos)
        top_splitter.setSizes([600, 400]) 

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.tabs_inferiores)
        main_splitter.setSizes([500, 200]) 

        self.setCentralWidget(main_splitter)

        # Barras y Estado
        crear_toolbar(self)
        crear_menu(self)
        self.statusBar()

        # Iniciar con un archivo en blanco por defecto
        self.nuevo_archivo()

    # ==========================================
    # UTILIDADES DE PESTAÑAS
    # ==========================================
    def get_current_editor(self):
        """Retorna el CodeEditor de la pestaña activa."""
        return self.tabs_editor.currentWidget()

    def update_status(self):
        """Actualiza la barra de estado según la pestaña seleccionada."""
        editor = self.get_current_editor()
        if editor:
            actualizar_posicion(editor, self.statusBar())
        else:
            self.statusBar().clearMessage()

    # ==========================================
    # MÉTODOS DE COMPILACIÓN
    # ==========================================
    def run_lexico(self):
        editor = self.get_current_editor()
        if not editor: return
        print("Ejecutando Léxico en el archivo actual...")

    def run_sintactico(self):
        print("Ejecutando Análisis Sintáctico...")

    def run_semantico(self):
        print("Ejecutando Análisis Semántico...")

    def run_intermedio(self):
        print("Generando Código Intermedio...")

    def run_ejecucion(self):
        print("Ejecutando el programa...")

    # ==========================================
    # MÉTODOS DE GESTIÓN DE ARCHIVOS
    # ==========================================
    def nuevo_archivo(self):
        nuevo_editor = CodeEditor()
        nuevo_editor.file_path = None # Variable dinámica para rastrear su ruta
        nuevo_editor.document().setModified(False)
        nuevo_editor.cursorPositionChanged.connect(self.update_status)

        titulo = f"Sin Nombre {self.contador_sin_nombre}"
        self.contador_sin_nombre += 1

        index = self.tabs_editor.addTab(nuevo_editor, titulo)
        self.tabs_editor.setCurrentIndex(index) # Enfocar la nueva pestaña

    def abrir_archivo(self):
        archivo_ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        
        if archivo_ruta:
            # Evitar abrir el mismo archivo dos veces
            for i in range(self.tabs_editor.count()):
                editor_existente = self.tabs_editor.widget(i)
                if getattr(editor_existente, 'file_path', None) == archivo_ruta:
                    self.tabs_editor.setCurrentIndex(i)
                    return

            try:
                with open(archivo_ruta, 'r', encoding='utf-8') as archivo:
                    contenido = archivo.read()
                
                nuevo_editor = CodeEditor()
                nuevo_editor.file_path = archivo_ruta
                nuevo_editor.setPlainText(contenido)
                nuevo_editor.document().setModified(False)
                nuevo_editor.cursorPositionChanged.connect(self.update_status)

                titulo = os.path.basename(archivo_ruta) # Solo el nombre del archivo, no toda la ruta
                index = self.tabs_editor.addTab(nuevo_editor, titulo)
                self.tabs_editor.setCurrentIndex(index)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{str(e)}")

    def guardar_archivo(self):
        editor = self.get_current_editor()
        if not editor: return False

        if getattr(editor, 'file_path', None):
            try:
                with open(editor.file_path, 'w', encoding='utf-8') as archivo:
                    archivo.write(editor.toPlainText())
                editor.document().setModified(False)
                
                # Actualizar el nombre de la pestaña por si tenía algún indicador
                index = self.tabs_editor.indexOf(editor)
                self.tabs_editor.setTabText(index, os.path.basename(editor.file_path))
                
                QMessageBox.information(self, "Éxito", "Archivo guardado.")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")
                return False
        else:
            return self.guardar_como()

    def guardar_como(self):
        editor = self.get_current_editor()
        if not editor: return False

        archivo_ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Como", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        
        if archivo_ruta:
            try:
                with open(archivo_ruta, 'w', encoding='utf-8') as archivo:
                    archivo.write(editor.toPlainText())
                editor.file_path = archivo_ruta
                editor.document().setModified(False)
                
                index = self.tabs_editor.indexOf(editor)
                self.tabs_editor.setTabText(index, os.path.basename(archivo_ruta))
                
                QMessageBox.information(self, "Éxito", "Archivo guardado.")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")
                return False
        return False

    def cerrar_archivo(self):
        """Llamado desde el menú/toolbar para cerrar la pestaña actual."""
        index = self.tabs_editor.currentIndex()
        if index != -1:
            self.cerrar_pestana(index)

    def cerrar_pestana(self, index):
        """Cierra una pestaña específica, verificando si hay cambios."""
        editor = self.tabs_editor.widget(index)
        
        if editor.document().isModified():
            self.tabs_editor.setCurrentIndex(index) # Nos movemos a la pestaña para que el usuario vea qué va a cerrar
            titulo = self.tabs_editor.tabText(index)
            respuesta = QMessageBox.warning(
                self, "Cambios sin guardar",
                f"El archivo '{titulo}' tiene cambios.\n¿Desea guardarlos?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if respuesta == QMessageBox.StandardButton.Save:
                if not self.guardar_archivo():
                    return # Si cancela el guardado, no cerramos
            elif respuesta == QMessageBox.StandardButton.Cancel:
                return # Detiene el cierre

        self.tabs_editor.removeTab(index)

    # ==========================================
    # EVENTOS DE LA VENTANA
    # ==========================================
    def closeEvent(self, event):
        """Al cerrar el IDE, intentamos cerrar todas las pestañas una por una."""
        while self.tabs_editor.count() > 0:
            index = self.tabs_editor.currentIndex()
            editor = self.tabs_editor.widget(index)
            
            if editor.document().isModified():
                self.tabs_editor.setCurrentIndex(index)
                titulo = self.tabs_editor.tabText(index)
                respuesta = QMessageBox.warning(
                    self, "Cambios sin guardar",
                    f"El archivo '{titulo}' tiene cambios.\n¿Desea guardarlos antes de salir?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
                )
                
                if respuesta == QMessageBox.StandardButton.Save:
                    if not self.guardar_archivo():
                        event.ignore()
                        return
                elif respuesta == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
            
            # Si se guardó o se eligió "Descartar", removemos la pestaña
            self.tabs_editor.removeTab(index)
            
        event.accept()