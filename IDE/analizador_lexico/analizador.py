import re

TOKEN_ESPECIFICATION = [
    ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),
    ('COMENTARIO_LINEA', r'//.*'),
    ('STRING',           r'"[^"]*"'),
    ('CHAR',             r"'[^']*'"),
    
    # 1. SOLUCIÓN AL 32.algo:
    # Captura un número seguido de un punto, PERO que NO tenga un número después.
    ('NUMERO_MALFORMADO',r'\d+\.(?!\d)'), 
    
    ('FLOTANTE',         r'\d+\.\d+'),
    ('ENTERO',           r'\d+'),
    ('PALABRAS_RESERVADAS', r'\b(if|else|while|do|end|switch|case|int|float|main|cin|cout|then|until)\b'),
    ('IDENTIFICADORES',  r'[a-zA-Z_][a-zA-Z0-9_]*'),
    
    # 2. SOLUCIÓN A SÍMBOLOS SEPARADOS (+ \n +):
    # Agregamos [ \t\n]* en medio de los símbolos dobles para permitir espacios o saltos
    ('OP_RELACIONAL',    r'=[ \t\n]*=|![ \t\n]*=|<[ \t\n]*=|>[ \t\n]*=|<|>'),
    ('OP_LOG',           r'&[ \t\n]*&|\|[ \t\n]*\||!'),
    ('OP_ARIT',          r'\+[ \t\n]*\+|-[ \t\n]*-|\+|-|\*|/|%|\^'),
    
    ('ASIGNACION',       r'='),
    ('SIMBOLOS',         r'[(){},;]'),
    ('SALTOLINEA',       r'\n'),
    ('SALTOS',           r'[ \t]+'),
    ('EXCEPCION',        r'.') 
]

TOK_REGEX = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_ESPECIFICATION)
GET_TOKEN = re.compile(TOK_REGEX)

def analizar(codigo_fuente):
    tokens_validos = []
    errores = []
    
    line_num = 1
    line_start = 0
    
    for match in GET_TOKEN.finditer(codigo_fuente):
        kind = match.lastgroup
        value = match.group()
        column = match.start() - line_start + 1 
        
        if kind == 'SALTOLINEA':
            line_start = match.end()
            line_num += 1
            continue
        elif kind == 'SALTOS' or kind == 'COMENTARIO_LINEA':
            continue
        elif kind == 'COMENTARIO_MULTI':
            line_num += value.count('\n')
            if '\n' in value:
                line_start = match.start() + value.rfind('\n') + 1
            continue
            
 
        elif kind == 'NUMERO_MALFORMADO':
            errores.append({
                'caracter': value, 
                'linea': line_num, 
                'columna': column,
                'mensaje': f"ERROR LÉXICO: Número mal formado '{value}' en Línea {line_num}, Col. {column}"
            })
            continue # Lo reporta como error y no lo guarda como token
            
        elif kind == 'EXCEPCION':
            errores.append({
                'caracter': value, 
                'linea': line_num, 
                'columna': column,
                'mensaje': f"ERROR LÉXICO: Caracter no reconocido '{value}' en Línea {line_num}, Col. {column}"
            })
            continue

        # ====================================================
        # MANEJO DE SÍMBOLOS CON ESPACIOS (+ \n +)
        # ====================================================
        if kind in ['OP_RELACIONAL', 'OP_LOG', 'OP_ARIT']:
            # Limpiamos los espacios internos solo visualmente para mandarlo bonito a la tabla
            lexema_limpio = value.replace(' ', '').replace('\t', '').replace('\n', '')
            tokens_validos.append({'tipo': kind, 'lexema': lexema_limpio, 'linea': line_num, 'columna': column})
            
            # Si el analizador "se tragó" un salto de línea dentro del símbolo, actualizamos el conteo
            if '\n' in value:
                line_num += value.count('\n')
                line_start = match.start() + value.rfind('\n') + 1
            continue
            
        # Para el resto de tokens válidos
        tokens_validos.append({'tipo': kind, 'lexema': value, 'linea': line_num, 'columna': column})
        
    return tokens_validos, errores