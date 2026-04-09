import re

TOKEN_ESPECIFICATION = [
    ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),
    ('COMENTARIO_LINEA', r'//.*'),
    ('STRING',           r'"[^"]*"'),
    ('CHAR',             r"'[^']*'"),
    ('FLOTANTE',         r'\d+\.\d+'),
    ('ENTERO',           r'\d+'),
    ('PALABRAS_RESERVADAS', r'\b(if|else|while|do|end|switch|case|int|float|main|cin|cout|then|until)\b'),
    ('IDENTIFICADORES',  r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('OP_RELACIONAL',    r'==|!=|<=|>=|<|>'),
    ('OP_LOG',           r'&&|\|\||!'),
    ('OP_ARIT',          r'\+\+|--|\+|-|\*|/|%|\^'),
    ('ASIGNACION',       r'='),
    ('SIMBOLOS',         r'[(){},;]'),
    ('SALTOLINEA',       r'\n'),
    ('SALTOS',           r'[ \t]+'),
    ('EXCEPCION',        r'.')  # <-- ¡La coma faltante estaba aquí!
]

TOK_REGEX = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_ESPECIFICATION)
GET_TOKEN = re.compile(TOK_REGEX)

def analizar(codigo_fuente):
    """
    Recibe el código fuente como texto y devuelve dos listas:
    1. tokens_validos: Lista de diccionarios con info de cada token.
    2. errores: Lista de diccionarios con info de cada error léxico.
    """
    tokens_validos = []
    errores = []
    
    line_num = 1
    line_start = 0
    
    for match in GET_TOKEN.finditer(codigo_fuente):
        kind = match.lastgroup
        value = match.group()
        # Calcular columna (se suma 1 para que visualmente empiece en la columna 1, no 0)
        column = match.start() - line_start + 1 
        
        # Nombres actualizados para coincidir con TOKEN_ESPECIFICATION
        if kind == 'SALTOLINEA':
            line_start = match.end()
            line_num += 1
            continue
        elif kind == 'SALTOS':
            continue
        elif kind == 'COMENTARIO_LINEA':
            continue
            
        elif kind == 'COMENTARIO_MULTI':
            line_num += value.count('\n')
            if '\n' in value:
                line_start = match.start() + value.rfind('\n') + 1
            continue
        elif kind == 'EXCEPCION':
            errores.append({
                'caracter': value, 
                'linea': line_num, 
                'columna': column,
                'mensaje': f"ERROR LÉXICO: Caracter no reconocido '{value}' en Línea {line_num}, Col. {column}"
            })
            continue
            
        # Para el resto de tokens válidos
        tokens_validos.append({'tipo': kind, 'lexema': value, 'linea': line_num, 'columna': column})
        
    return tokens_validos, errores