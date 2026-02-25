def actualizar_posicion(editor, status_bar):
    cursor = editor.textCursor()
    linea = cursor.blockNumber() + 1
    columna = cursor.positionInBlock() + 1
    status_bar.showMessage(f"Línea: {linea} | Columna: {columna}")