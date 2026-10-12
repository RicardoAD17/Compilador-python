import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTabWidget, QTextEdit, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from editor import CodeEditor
from status_bar import actualizar_posicion
from tool_bar import crear_toolbar
from menu_bar import crear_menu
from analizador_lexico.analizador import analizar
from analizador_sintactico import AnalizadorSintactico, NodoAST


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Python - Compilador")
        self.resize(1000, 700)

        self.contador_sin_nombre = 1
        self.is_dark_theme = True

        # Guardar últimos resultados para exportar
        self._ultimo_ast       = None
        self._ultimos_errores_sint = []

        # ── Pestañas del Editor ───────────────────────────────────────
        self.tabs_editor = QTabWidget()
        self.tabs_editor.setTabsClosable(True)
        self.tabs_editor.tabCloseRequested.connect(self.cerrar_pestana)
        self.tabs_editor.currentChanged.connect(self.update_status)

        # ── Panel derecho ─────────────────────────────────────────────
        self.tabs_derechos = QTabWidget()

        # Pestaña Léxico
        self.tabla_lexico = QTableWidget()
        self.tabla_lexico.setColumnCount(4)
        self.tabla_lexico.setHorizontalHeaderLabels(["Tipo de Token", "Lexema", "Línea", "Columna"])
        header = self.tabla_lexico.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_lexico.verticalHeader().setVisible(False)

        # Pestaña Sintáctico: árbol + botón exportar
        self.arbol_sintactico = QTreeWidget()
        self.arbol_sintactico.setHeaderLabel("Árbol Sintáctico Abstracto (AST)")
        self.arbol_sintactico.setFont(QFont("Consolas", 10))

        btn_exportar_arbol = QPushButton("💾  Exportar árbol a archivo...")
        btn_exportar_arbol.setFixedHeight(32)
        btn_exportar_arbol.clicked.connect(self.exportar_arbol)

        panel_sint = QWidget()
        layout_sint = QVBoxLayout(panel_sint)
        layout_sint.setContentsMargins(0, 0, 0, 0)
        layout_sint.setSpacing(4)
        layout_sint.addWidget(btn_exportar_arbol)
        layout_sint.addWidget(self.arbol_sintactico)

        self.tabs_derechos.addTab(self.tabla_lexico, "Análisis Léxico")
        self.tabs_derechos.addTab(panel_sint,        "Análisis Sintáctico")
        self.tabs_derechos.addTab(QTextEdit(),       "Análisis Semántico")
        self.tabs_derechos.addTab(QTextEdit(),       "Código Intermedio")
        self.tabs_derechos.addTab(QTextEdit(),       "Tabla de Símbolos")

        # ── Panel inferior ────────────────────────────────────────────
        self.tabs_inferiores = QTabWidget()
        self.tabs_inferiores.addTab(QTextEdit(), "Ejecución / Salida")
        self.tabs_inferiores.addTab(QTextEdit(), "Errores Léxicos")

        # Errores sintácticos: consola + botón exportar
        consola_sint_widget = QWidget()
        layout_err_sint = QVBoxLayout(consola_sint_widget)
        layout_err_sint.setContentsMargins(0, 0, 0, 0)
        layout_err_sint.setSpacing(4)

        btn_exportar_errores = QPushButton("💾  Exportar errores a archivo...")
        btn_exportar_errores.setFixedHeight(32)
        btn_exportar_errores.clicked.connect(self.exportar_errores_sint)

        self.consola_errores_sint = QTextEdit()
        layout_err_sint.addWidget(btn_exportar_errores)
        layout_err_sint.addWidget(self.consola_errores_sint)

        self.tabs_inferiores.addTab(consola_sint_widget, "Errores Sintácticos")
        self.tabs_inferiores.addTab(QTextEdit(),         "Errores Semánticos")

        # ── Layout principal ──────────────────────────────────────────
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.tabs_editor)
        top_splitter.addWidget(self.tabs_derechos)
        top_splitter.setSizes([600, 400])

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.tabs_inferiores)
        main_splitter.setSizes([500, 200])

        self.setCentralWidget(main_splitter)

        crear_toolbar(self)
        crear_menu(self)
        self.statusBar()
        self.nuevo_archivo()

    # ================================================================
    # UTILIDADES DE PESTAÑAS
    # ================================================================
    def get_current_editor(self):
        return self.tabs_editor.currentWidget()

    def update_status(self):
        editor = self.get_current_editor()
        if editor:
            actualizar_posicion(editor, self.statusBar())
        else:
            self.statusBar().clearMessage()

    # ================================================================
    # ANÁLISIS LÉXICO
    # ================================================================
    def run_lexico(self):
        editor = self.get_current_editor()
        if not editor:
            return

        codigo = editor.toPlainText()
        consola_errores = self.tabs_inferiores.widget(1)

        self.tabla_lexico.setRowCount(0)
        consola_errores.clear()

        tokens, errores = analizar(codigo)

        for row_index, t in enumerate(tokens):
            self.tabla_lexico.insertRow(row_index)
            item_tipo    = QTableWidgetItem(t['tipo'])
            item_lexema  = QTableWidgetItem(repr(t['lexema']))
            item_linea   = QTableWidgetItem(str(t['linea']))
            item_columna = QTableWidgetItem(str(t['columna']))
            item_linea.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_columna.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_lexico.setItem(row_index, 0, item_tipo)
            self.tabla_lexico.setItem(row_index, 1, item_lexema)
            self.tabla_lexico.setItem(row_index, 2, item_linea)
            self.tabla_lexico.setItem(row_index, 3, item_columna)

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

        self.tabs_derechos.setCurrentIndex(0)
        self.tabs_inferiores.setCurrentIndex(1 if errores else 0)

    # ================================================================
    # ANÁLISIS SINTÁCTICO
    # ================================================================
    def run_sintactico(self):
        editor = self.get_current_editor()
        if not editor:
            return

        codigo = editor.toPlainText()

        # Paso 1: léxico
        tokens, _ = analizar(codigo)

        # Actualizar tabla léxica
        self.tabla_lexico.setRowCount(0)
        for row_index, t in enumerate(tokens):
            self.tabla_lexico.insertRow(row_index)
            li = QTableWidgetItem(str(t['linea']))
            co = QTableWidgetItem(str(t['columna']))
            li.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            co.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_lexico.setItem(row_index, 0, QTableWidgetItem(t['tipo']))
            self.tabla_lexico.setItem(row_index, 1, QTableWidgetItem(repr(t['lexema'])))
            self.tabla_lexico.setItem(row_index, 2, li)
            self.tabla_lexico.setItem(row_index, 3, co)

        # Paso 2: sintáctico
        parser = AnalizadorSintactico(tokens)
        ast, errores_sint = parser.parsear()

        # Guardar resultados para exportar
        self._ultimo_ast            = ast
        self._ultimos_errores_sint  = errores_sint

        # Paso 3: mostrar árbol
        self.arbol_sintactico.clear()
        if ast:
            self.arbol_sintactico.addTopLevelItem(self._construir_item_arbol(ast))
            self.arbol_sintactico.expandAll()
        else:
            self.arbol_sintactico.addTopLevelItem(
                QTreeWidgetItem(["(sin árbol — revisa los errores)"])
            )

        # Paso 4: mostrar errores
        self.consola_errores_sint.clear()
        if errores_sint:
            self.consola_errores_sint.setTextColor(Qt.GlobalColor.red)
            self.consola_errores_sint.append(
                f"Se encontraron {len(errores_sint)} errores sintácticos:\n"
            )
            for e in errores_sint:
                self.consola_errores_sint.append(e['mensaje'])
        else:
            self.consola_errores_sint.setTextColor(Qt.GlobalColor.green)
            self.consola_errores_sint.append("Análisis Sintáctico completado sin errores. ✅")

        self.consola_errores_sint.setTextColor(
            Qt.GlobalColor.white if self.is_dark_theme else Qt.GlobalColor.black
        )

        self.tabs_derechos.setCurrentIndex(1)
        self.tabs_inferiores.setCurrentIndex(2 if errores_sint else 0)

    # ================================================================
    # EXPORTAR ÁRBOL
    # ================================================================
    def exportar_arbol(self):
        """Guarda el AST como archivo de texto con estructura de árbol visual."""
        if self._ultimo_ast is None:
            QMessageBox.warning(self, "Sin árbol",
                                "Primero ejecuta el Análisis Sintáctico.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar árbol sintáctico", "arbol_sintactico.txt",
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return

        try:
            lineas = []
            lineas.append("=" * 60)
            lineas.append("  ÁRBOL SINTÁCTICO ABSTRACTO (AST)")
            lineas.append("=" * 60)
            lineas.append("")
            self._ast_a_texto(self._ultimo_ast, lineas, prefijo="", es_ultimo=True)
            lineas.append("")
            lineas.append("=" * 60)

            with open(ruta, 'w', encoding='utf-8') as f:
                f.write("\n".join(lineas))

            QMessageBox.information(self, "Exportado",
                                    f"Árbol guardado en:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")

    def _ast_a_texto(self, nodo: NodoAST, lineas: list, prefijo: str, es_ultimo: bool):
        """
        Convierte el AST a texto con estilo de árbol de carpetas:
            programa  [L1]
            ├── main → main  [L1]
            └── lista_declaracion  [L2]
                ├── declaracion_variable  [L2]
                │   ├── tipo → int  [L2]
        """
        conector = "└── " if es_ultimo else "├── "

        # Etiqueta del nodo
        if nodo.valor:
            etiqueta = f"{nodo.tipo}  →  {nodo.valor}"
        else:
            etiqueta = nodo.tipo
        if nodo.linea is not None:
            etiqueta += f"   [L{nodo.linea}]"

        lineas.append(prefijo + conector + etiqueta)

        # Prefijo para los hijos
        extension = "    " if es_ultimo else "│   "
        nuevo_prefijo = prefijo + extension

        for idx, hijo in enumerate(nodo.hijos):
            ultimo_hijo = (idx == len(nodo.hijos) - 1)
            self._ast_a_texto(hijo, lineas, nuevo_prefijo, ultimo_hijo)

    # ================================================================
    # EXPORTAR ERRORES SINTÁCTICOS
    # ================================================================
    def exportar_errores_sint(self):
        """Guarda la lista de errores sintácticos en un archivo de texto."""
        if not self._ultimos_errores_sint and self._ultimo_ast is None:
            QMessageBox.warning(self, "Sin datos",
                                "Primero ejecuta el Análisis Sintáctico.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar errores sintácticos", "errores_sintacticos.txt",
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return

        try:
            lineas = []
            lineas.append("=" * 60)
            lineas.append("  REPORTE DE ERRORES SINTÁCTICOS")
            lineas.append("=" * 60)
            lineas.append("")

            if self._ultimos_errores_sint:
                lineas.append(f"Total de errores encontrados: {len(self._ultimos_errores_sint)}")
                lineas.append("")
                for i, e in enumerate(self._ultimos_errores_sint, 1):
                    lineas.append(f"  [{i:02d}]  {e['mensaje']}")
            else:
                lineas.append("  ✅ Análisis Sintáctico completado sin errores.")

            lineas.append("")
            lineas.append("=" * 60)

            with open(ruta, 'w', encoding='utf-8') as f:
                f.write("\n".join(lineas))

            QMessageBox.information(self, "Exportado",
                                    f"Errores guardados en:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")

    # ================================================================
    # ÁRBOL VISUAL (QTreeWidget)
    # ================================================================
    def _construir_item_arbol(self, nodo: NodoAST) -> QTreeWidgetItem:
        if nodo.valor:
            etiqueta = f"{nodo.tipo}  →  {nodo.valor}"
        else:
            etiqueta = nodo.tipo
        if nodo.linea is not None:
            etiqueta += f"   [L{nodo.linea}]"

        item = QTreeWidgetItem([etiqueta])
        item.setForeground(0, QBrush(QColor(self._color_nodo(nodo.tipo))))

        if nodo.tipo in ("programa", "lista_declaracion"):
            f = QFont()
            f.setBold(True)
            item.setFont(0, f)

        for hijo in nodo.hijos:
            item.addChild(self._construir_item_arbol(hijo))

        return item

    def _color_nodo(self, tipo: str) -> str:
        colores = {
            "programa":                  "#C678DD",
            "lista_declaracion":         "#C678DD",
            "declaracion_variable":      "#E5C07B",
            "identificadores":           "#E5C07B",
            "tipo":                      "#56B6C2",
            "id":                        "#ABB2BF",
            "asignacion":                "#61AFEF",
            "sent_expresion":            "#61AFEF",
            "sent_expresion_vacia":      "#61AFEF",
            "expresion_suelta":          "#61AFEF",
            "seleccion_if":              "#D19A66",
            "then":                      "#D19A66",
            "else":                      "#D19A66",
            "iteracion_while":           "#D19A66",
            "cuerpo_while":              "#D19A66",
            "repeticion_do_while":       "#D19A66",
            "cuerpo_do":                 "#D19A66",
            "sent_cin":                  "#98C379",
            "sent_cout":                 "#98C379",
            "salida":                    "#98C379",
            "expresion_relacional":      "#E06C75",
            "expresion_aditiva":         "#E06C75",
            "expresion_multiplicativa":  "#E06C75",
            "expresion_potencia":        "#E06C75",
            "op_logico":                 "#E06C75",
            "numero":                    "#D19A66",
            "cadena":                    "#98C379",
            "bool_literal":              "#56B6C2",
            "inc_dec":                   "#E5C07B",
            "inc_dec_postfijo":          "#E5C07B",
            "inc_dec_prefijo":           "#E5C07B",
            "error":                     "#FF0000",
        }
        return colores.get(tipo, "#FFFFFF")

    # ================================================================
    # FASES PENDIENTES
    # ================================================================
    def run_semantico(self):
        print("Ejecutando Análisis Semántico...")

    def run_intermedio(self):
        print("Generando Código Intermedio...")

    def run_ejecucion(self):
        print("Ejecutando el programa...")

    # ================================================================
    # GESTIÓN DE ARCHIVOS
    # ================================================================
    def nuevo_archivo(self):
        nuevo_editor = CodeEditor()
        nuevo_editor.set_theme(self.is_dark_theme)
        nuevo_editor.file_path = None
        nuevo_editor.document().setModified(False)
        nuevo_editor.cursorPositionChanged.connect(self.update_status)
        titulo = f"Sin Nombre {self.contador_sin_nombre}"
        self.contador_sin_nombre += 1
        index = self.tabs_editor.addTab(nuevo_editor, titulo)
        self.tabs_editor.setCurrentIndex(index)

    def abrir_archivo(self):
        archivo_ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir Archivo", "",
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
        if archivo_ruta:
            for i in range(self.tabs_editor.count()):
                if getattr(self.tabs_editor.widget(i), 'file_path', None) == archivo_ruta:
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
                index = self.tabs_editor.addTab(nuevo_editor, os.path.basename(archivo_ruta))
                self.tabs_editor.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{str(e)}")

    def guardar_archivo(self):
        editor = self.get_current_editor()
        if not editor:
            return False
        if getattr(editor, 'file_path', None):
            try:
                with open(editor.file_path, 'w', encoding='utf-8') as archivo:
                    archivo.write(editor.toPlainText())
                editor.document().setModified(False)
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
        if not editor:
            return False
        archivo_ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Como", "",
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
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
        index = self.tabs_editor.currentIndex()
        if index != -1:
            self.cerrar_pestana(index)

    def cerrar_pestana(self, index):
        editor = self.tabs_editor.widget(index)
        if editor.document().isModified():
            self.tabs_editor.setCurrentIndex(index)
            titulo = self.tabs_editor.tabText(index)
            respuesta = QMessageBox.warning(
                self, "Cambios sin guardar",
                f"El archivo '{titulo}' tiene cambios.\n¿Desea guardarlos?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if respuesta == QMessageBox.StandardButton.Save:
                if not self.guardar_archivo():
                    return
            elif respuesta == QMessageBox.StandardButton.Cancel:
                return
        self.tabs_editor.removeTab(index)

    def closeEvent(self, event):
        while self.tabs_editor.count() > 0:
            index = self.tabs_editor.currentIndex()
            editor = self.tabs_editor.widget(index)
            if editor.document().isModified():
                self.tabs_editor.setCurrentIndex(index)
                titulo = self.tabs_editor.tabText(index)
                respuesta = QMessageBox.warning(
                    self, "Cambios sin guardar",
                    f"El archivo '{titulo}' tiene cambios.\n¿Desea guardarlos antes de salir?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )
                if respuesta == QMessageBox.StandardButton.Save:
                    if not self.guardar_archivo():
                        event.ignore()
                        return
                elif respuesta == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
            self.tabs_editor.removeTab(index)
        event.accept()

    def toggle_tema(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
                QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #ffffff; border: 1px solid #444; }
                QTabBar::tab { background: #333333; color: white; padding: 6px; }
                QTabBar::tab:selected { background: #1e1e1e; font-weight: bold; border-top: 2px solid #007acc; }
                QTreeWidget { background-color: #1e1e1e; color: #ffffff; border: 1px solid #444; }
                QHeaderView::section { background-color: #333333; color: white; }
                QPushButton { background-color: #3a3a3a; color: white; border: 1px solid #555; padding: 4px 10px; border-radius: 3px; }
                QPushButton:hover { background-color: #007acc; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #f0f0f0; color: #000000; }
                QTextEdit, QPlainTextEdit { background-color: #ffffff; color: #000000; border: 1px solid #ccc; }
                QTabBar::tab { background: #e0e0e0; color: black; padding: 6px; }
                QTabBar::tab:selected { background: #ffffff; font-weight: bold; border-top: 2px solid #007acc; }
                QTreeWidget { background-color: #ffffff; color: #000000; border: 1px solid #ccc; }
                QHeaderView::section { background-color: #e0e0e0; color: black; }
                QPushButton { background-color: #e0e0e0; color: black; border: 1px solid #aaa; padding: 4px 10px; border-radius: 3px; }
                QPushButton:hover { background-color: #007acc; color: white; }
            """)
        for i in range(self.tabs_editor.count()):
            self.tabs_editor.widget(i).set_theme(self.is_dark_theme)