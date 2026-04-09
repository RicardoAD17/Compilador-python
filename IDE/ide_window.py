import os
from PyQt6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QTextEdit, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from editor import CodeEditor
from status_bar import actualizar_posicion
from tool_bar import crear_toolbar
from menu_bar import crear_menu
from analizador_lexico.analizador import analizar
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Python - Compilador")
        self.resize(1000, 700)

        self.contador_sin_nombre = 1 # Para nombrar "Sin Nombre 1", "Sin Nombre 2"...
        self.is_dark_theme = True # Rastrear el tema actual de la ventana

        # 1. Instanciar el Contenedor de Pestañas del Editor
        self.tabs_editor = QTabWidget()
        self.tabs_editor.setTabsClosable(True) # Activar la 'X' en cada pestaña
        self.tabs_editor.tabCloseRequested.connect(self.cerrar_pestana) # Conectar la 'X'
        self.tabs_editor.currentChanged.connect(self.update_status) # Actualizar línea/columna al cambiar de pestaña

        # 2. Panel Superior Derecho: Fases de Análisis
        self.tabs_derechos = QTabWidget()
        # --- NUEVA TABLA PARA LÉXICO ---
        self.tabla_lexico = QTableWidget()
        self.tabla_lexico.setColumnCount(4) # 4 columnas
        self.tabla_lexico.setHorizontalHeaderLabels(["Tipo de Token", "Lexema", "Línea", "Columna"])
        
        # Hacer que las columnas se expandan para llenar el espacio
        header = self.tabla_lexico.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Tipo
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Lexema
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Linea
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Columna
        
        # Quitar los números de fila de la izquierda (opcional, se ve más limpio)
        self.tabla_lexico.verticalHeader().setVisible(False)
        
        # Agregar la tabla como la primera pestaña
        self.tabs_derechos.addTab(self.tabla_lexico, "Análisis Léxico")
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
        if not editor: 
            return 

        codigo = editor.toPlainText()
        consola_errores = self.tabs_inferiores.widget(1) 

        # 1. Limpiar la tabla y la consola de errores
        self.tabla_lexico.setRowCount(0) # Borra todas las filas anteriores
        consola_errores.clear()

        # 2. Llamar al analizador
        tokens, errores = analizar(codigo)

        # 3. LLENAR LA TABLA CON LOS TOKENS
        for row_index, t in enumerate(tokens):
            # Insertar una nueva fila en la posición row_index
            self.tabla_lexico.insertRow(row_index)
            
            # Crear los items para cada celda (PyQt exige que sean QTableWidgetItem)
            item_tipo = QTableWidgetItem(t['tipo'])
            item_lexema = QTableWidgetItem(repr(t['lexema'])) # repr() ayuda a que los saltos de línea se vean bien
            item_linea = QTableWidgetItem(str(t['linea']))
            item_columna = QTableWidgetItem(str(t['columna']))
            
            # (Opcional) Alinear los números al centro
            item_linea.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_columna.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Colocar los items en su celda correspondiente (fila, columna, item)
            self.tabla_lexico.setItem(row_index, 0, item_tipo)
            self.tabla_lexico.setItem(row_index, 1, item_lexema)
            self.tabla_lexico.setItem(row_index, 2, item_linea)
            self.tabla_lexico.setItem(row_index, 3, item_columna)

        # 4. Imprimir Errores (Esto se queda igual que antes)
        if errores:
            consola_errores.setTextColor(Qt.GlobalColor.red)
            consola_errores.append(f"Se encontraron {len(errores)} errores léxicos:\n")
            for e in errores:
                consola_errores.append(e['mensaje'])
            consola_errores.setTextColor(Qt.GlobalColor.white if self.is_dark_theme else Qt.GlobalColor.black)
        else:
            consola_errores.setTextColor(Qt.GlobalColor.green)
            consola_errores.append("Análisis Léxico completado sin errores. ✅")
            consola_errores.setTextColor(Qt.GlobalColor.white if self.is_dark_theme else Qt.GlobalColor.black)

        # Cambiar el foco
        self.tabs_derechos.setCurrentIndex(0)
        self.tabs_inferiores.setCurrentIndex(1 if errores else 0)
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
        nuevo_editor.set_theme(self.is_dark_theme)
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
                nuevo_editor.set_theme(self.is_dark_theme)
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

    def toggle_tema(self):
        """Cambia la hoja de estilos de toda la aplicación entre claro y oscuro."""
        self.is_dark_theme = not self.is_dark_theme

        if self.is_dark_theme:
            # QSS para Tema Oscuro
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
                QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #ffffff; border: 1px solid #444; }
                QTabBar::tab { background: #333333; color: white; padding: 6px; }
                QTabBar::tab:selected { background: #1e1e1e; font-weight: bold; border-top: 2px solid #007acc; }
            """)
        else:
            # QSS para Tema Claro
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #f0f0f0; color: #000000; }
                QTextEdit, QPlainTextEdit { background-color: #ffffff; color: #000000; border: 1px solid #ccc; }
                QTabBar::tab { background: #e0e0e0; color: black; padding: 6px; }
                QTabBar::tab:selected { background: #ffffff; font-weight: bold; border-top: 2px solid #007acc; }
            """)

        # Actualizar la barra de números en todas las pestañas abiertas
        for i in range(self.tabs_editor.count()):
            editor = self.tabs_editor.widget(i)
            editor.set_theme(self.is_dark_theme)