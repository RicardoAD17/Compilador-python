# =============================================================================
# ANALIZADOR SINTÁCTICO DESCENDENTE RECURSIVO
# Fase 2 - Compiladores I
# =============================================================================

class NodoAST:
    """Representa un nodo en el Árbol Sintáctico Abstracto."""
    def __init__(self, tipo, valor=None, linea=None, columna=None):
        self.tipo    = tipo
        self.valor   = valor
        self.linea   = linea
        self.columna = columna
        self.hijos   = []

    def agregar_hijo(self, hijo):
        if hijo is not None:
            self.hijos.append(hijo)

    def __repr__(self):
        if self.valor:
            return f"NodoAST({self.tipo}: {self.valor})"
        return f"NodoAST({self.tipo})"


class AnalizadorSintactico:
    """Parser descendente recursivo."""

    def __init__(self, tokens):
        self.tokens  = tokens
        self.pos     = 0
        self.errores = []

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    def token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return {'tipo': 'EOF', 'lexema': '', 'linea': -1, 'columna': -1}

    def avanzar(self):
        tok = self.token_actual()
        self.pos += 1
        return tok

    def es(self, tipo=None, lexema=None):
        tok = self.token_actual()
        tipo_ok   = (tipo   is None) or (tok['tipo']   == tipo)
        lexema_ok = (lexema is None) or (tok['lexema'] == lexema)
        return tipo_ok and lexema_ok

    def consumir(self, tipo=None, lexema=None):
        tok = self.token_actual()
        tipo_ok   = (tipo   is None) or (tok['tipo']   == tipo)
        lexema_ok = (lexema is None) or (tok['lexema'] == lexema)
        if tipo_ok and lexema_ok:
            self.avanzar()
            return tok
        esperado  = lexema if lexema else tipo
        encontrado = tok['lexema'] if tok['lexema'] else tok['tipo']
        self.registrar_error(
            f"Se esperaba '{esperado}' pero se encontró '{encontrado}'",
            tok['linea'], tok['columna']
        )
        return None

    def registrar_error(self, mensaje, linea, columna):
        self.errores.append({
            'mensaje': f"ERROR SINTÁCTICO: {mensaje} — Línea {linea}, Col. {columna}",
            'linea': linea,
            'columna': columna
        })

    def _es_inicio_bloque_nuevo(self):
        """Tokens que arrancan una declaración o sentencia legítima."""
        tok = self.token_actual()
        if tok['tipo'] == 'PALABRAS_RESERVADAS' and tok['lexema'] in (
            'int', 'float', 'bool', 'if', 'while', 'do', 'cin', 'cout'
        ):
            return True
        if tok['tipo'] == 'IDENTIFICADORES':
            return True
        return False

    def sincronizar_linea(self):
        """
        Recuperación SUAVE: consume tokens hasta el ';' más cercano o
        hasta el inicio de una nueva sentencia/declaración válida.
        Así NO se salta líneas enteras.
        """
        tok = self.token_actual()
        linea_error = tok['linea']

        while not self.es('EOF'):
            tok = self.token_actual()
            # Parar en ';' y consumirlo
            if tok['tipo'] == 'SIMBOLOS' and tok['lexema'] == ';':
                self.avanzar()
                return
            # Parar si llegamos a una línea nueva con inicio de sentencia válida
            if tok['linea'] > linea_error and self._es_inicio_bloque_nuevo():
                return
            # Parar en delimitadores de bloque
            if tok['tipo'] == 'SIMBOLOS' and tok['lexema'] == '}':
                return
            if tok['tipo'] == 'PALABRAS_RESERVADAS' and tok['lexema'] in ('end', 'else'):
                return
            self.avanzar()

    # ------------------------------------------------------------------
    # PUNTO DE ENTRADA
    # ------------------------------------------------------------------

    def parsear(self):
        if not self.tokens:
            self.registrar_error("El programa está vacío", 1, 1)
            return None, self.errores
        ast = self.parse_programa()
        if not self.es('EOF'):
            tok = self.token_actual()
            self.registrar_error(
                f"Tokens inesperados al final del programa '{tok['lexema']}'",
                tok['linea'], tok['columna']
            )
        return ast, self.errores

    # ------------------------------------------------------------------
    # REGLAS GRAMATICALES
    # ------------------------------------------------------------------

    # programa → main { lista_declaracion }
    def parse_programa(self):
        nodo = NodoAST("programa")
        tok  = self.token_actual()
        nodo.linea   = tok['linea']
        nodo.columna = tok['columna']

        tk_main = self.consumir('PALABRAS_RESERVADAS', 'main')
        if tk_main:
            nodo.agregar_hijo(NodoAST("main", "main", tk_main['linea'], tk_main['columna']))

        self.consumir('SIMBOLOS', '{')
        nodo.agregar_hijo(self.parse_lista_declaracion())
        self.consumir('SIMBOLOS', '}')
        return nodo

    # lista_declaracion → declaracion lista_declaracion | declaracion
    def parse_lista_declaracion(self):
        nodo = NodoAST("lista_declaracion")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        while not self.es('EOF') and not self.es('SIMBOLOS', '}') \
              and not self.es('PALABRAS_RESERVADAS', 'end') \
              and not self.es('PALABRAS_RESERVADAS', 'else'):
            decl = self.parse_declaracion()
            if decl:
                nodo.agregar_hijo(decl)

        return nodo

    # declaracion → declaracion_variable | sentencia | expresion_suelta
    def parse_declaracion(self):
        tok = self.token_actual()

        # ── Declaración de variable ──────────────────────────────────
        if tok['tipo'] == 'PALABRAS_RESERVADAS' and tok['lexema'] in ('int', 'float', 'bool'):
            return self.parse_declaracion_variable()

        # ── Sentencias con palabra reservada ────────────────────────
        if tok['tipo'] == 'PALABRAS_RESERVADAS':
            if tok['lexema'] == 'if':
                return self.parse_seleccion()
            if tok['lexema'] == 'while':
                return self.parse_iteracion()
            if tok['lexema'] == 'do':
                return self.parse_repeticion()
            if tok['lexema'] == 'cin':
                return self.parse_sent_in()
            if tok['lexema'] == 'cout':
                return self.parse_sent_out()

        # ── Identificador: puede ser asignación (id = ...) ──────────
        if tok['tipo'] == 'IDENTIFICADORES':
            # Miramos el siguiente token para decidir
            sig = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if sig and sig['tipo'] == 'ASIGNACION':
                return self.parse_asignacion()
            # Si NO hay '=' es una expresión suelta (ej: c--, y+1, etc.)
            return self.parse_expresion_suelta()

        # ── Números u operadores solos: expresión suelta ─────────────
        # (ej: "9+6-7", "a+", "c--")
        if tok['tipo'] in ('ENTERO', 'FLOTANTE', 'OP_ARIT', 'OP_LOG', 'OP_RELACIONAL'):
            return self.parse_expresion_suelta()

        # ── Token completamente desconocido en este contexto ─────────
        self.registrar_error(
            f"Token inesperado '{tok['lexema']}'",
            tok['linea'], tok['columna']
        )
        # Recuperación SUAVE: solo consume hasta el ';' de esa línea
        self.sincronizar_linea()
        return None

    # expresion_suelta → expresion ;
    # Para líneas como "9+6-7;", "c--;", "a+" (con error), etc.
    def parse_expresion_suelta(self):
        tok  = self.token_actual()
        nodo = NodoAST("expresion_suelta")
        nodo.linea   = tok['linea']
        nodo.columna = tok['columna']

        expr = self.parse_expresion()
        nodo.agregar_hijo(expr)

        if self.es('SIMBOLOS', ';'):
            self.avanzar()
        else:
            tok_act = self.token_actual()
            # Solo reportar error de ';' si seguimos en la misma línea
            # y lo que sigue no es un inicio de bloque nuevo
            if tok_act['tipo'] != 'EOF' \
               and tok_act['lexema'] not in ('}', 'end', 'else') \
               and not (tok_act['tipo'] == 'PALABRAS_RESERVADAS'
                        and tok_act['lexema'] in ('int','float','bool','if','while','do','cin','cout')):
                self.registrar_error(
                    f"Se esperaba ';' después de la expresión",
                    tok_act['linea'], tok_act['columna']
                )
        return nodo

    # declaracion_variable → tipo identificador ;
    def parse_declaracion_variable(self):
        nodo = NodoAST("declaracion_variable")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        nodo.agregar_hijo(self.parse_tipo())
        nodo.agregar_hijo(self.parse_identificador_lista())
        self.consumir('SIMBOLOS', ';')
        return nodo

    # tipo → int | float | bool
    def parse_tipo(self):
        tok = self.token_actual()
        if tok['tipo'] == 'PALABRAS_RESERVADAS' and tok['lexema'] in ('int', 'float', 'bool'):
            self.avanzar()
            return NodoAST("tipo", tok['lexema'], tok['linea'], tok['columna'])
        self.registrar_error(
            f"Se esperaba un tipo (int, float, bool), se encontró '{tok['lexema']}'",
            tok['linea'], tok['columna']
        )
        return NodoAST("tipo", "?", tok['linea'], tok['columna'])

    # identificador → id | identificador , id
    def parse_identificador_lista(self):
        nodo = NodoAST("identificadores")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        id_tok = self.consumir('IDENTIFICADORES')
        if id_tok:
            nodo.agregar_hijo(NodoAST("id", id_tok['lexema'], id_tok['linea'], id_tok['columna']))

        while self.es('SIMBOLOS', ','):
            self.avanzar()
            id_tok = self.consumir('IDENTIFICADORES')
            if id_tok:
                nodo.agregar_hijo(NodoAST("id", id_tok['lexema'], id_tok['linea'], id_tok['columna']))

        return nodo

    # asignacion → id = sent_expresion
    def parse_asignacion(self):
        nodo = NodoAST("asignacion")
        tok  = self.token_actual()
        nodo.linea   = tok['linea']
        nodo.columna = tok['columna']

        id_tok = self.consumir('IDENTIFICADORES')
        if id_tok:
            nodo.agregar_hijo(NodoAST("id", id_tok['lexema'], id_tok['linea'], id_tok['columna']))

        self.consumir('ASIGNACION', '=')
        nodo.agregar_hijo(self.parse_sent_expresion())
        return nodo

    # sent_expresion → expresion ; | ;
    def parse_sent_expresion(self):
        if self.es('SIMBOLOS', ';'):
            self.avanzar()
            return NodoAST("sent_expresion_vacia")

        nodo = NodoAST("sent_expresion")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        expr = self.parse_expresion()
        nodo.agregar_hijo(expr)

        if self.es('SIMBOLOS', ';'):
            self.avanzar()
        else:
            tok_act = self.token_actual()
            self.registrar_error(
                f"Se esperaba ';' al final de la asignación, se encontró '{tok_act['lexema']}'",
                tok_act['linea'], tok_act['columna']
            )
        return nodo

    # ------------------------------------------------------------------
    # SENTENCIAS DE CONTROL
    # ------------------------------------------------------------------

    # seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end
    def parse_seleccion(self):
        nodo   = NodoAST("seleccion_if")
        tok_if = self.consumir('PALABRAS_RESERVADAS', 'if')
        if tok_if:
            nodo.linea   = tok_if['linea']
            nodo.columna = tok_if['columna']

        # La condición puede venir con o sin paréntesis
        if self.es('SIMBOLOS', '('):
            self.avanzar()
            cond = self.parse_expresion()
            self.consumir('SIMBOLOS', ')')
        else:
            cond = self.parse_expresion()
        nodo.agregar_hijo(cond)

        self.consumir('PALABRAS_RESERVADAS', 'then')

        cuerpo_then = NodoAST("then")
        tok = self.token_actual()
        cuerpo_then.linea = tok['linea']
        cuerpo_then.agregar_hijo(self.parse_lista_declaracion())
        nodo.agregar_hijo(cuerpo_then)

        if self.es('PALABRAS_RESERVADAS', 'else'):
            self.avanzar()
            cuerpo_else = NodoAST("else")
            tok = self.token_actual()
            cuerpo_else.linea = tok['linea']
            cuerpo_else.agregar_hijo(self.parse_lista_declaracion())
            nodo.agregar_hijo(cuerpo_else)

        if self.es('PALABRAS_RESERVADAS', 'end'):
            self.avanzar()
            # Consumir ';' opcional después de end
            if self.es('SIMBOLOS', ';'):
                self.avanzar()
        else:
            tok_act = self.token_actual()
            self.registrar_error(
                f"Se esperaba 'end' para cerrar el 'if'",
                tok_act['linea'], tok_act['columna']
            )
        return nodo

    # iteracion → while expresion lista_sentencias end
    def parse_iteracion(self):
        nodo  = NodoAST("iteracion_while")
        tok_w = self.consumir('PALABRAS_RESERVADAS', 'while')
        if tok_w:
            nodo.linea   = tok_w['linea']
            nodo.columna = tok_w['columna']

        # Condición con o sin paréntesis
        if self.es('SIMBOLOS', '('):
            self.avanzar()
            cond = self.parse_expresion()
            self.consumir('SIMBOLOS', ')')
        else:
            cond = self.parse_expresion()
        nodo.agregar_hijo(cond)

        # Cuerpo: puede venir entre { } o sin llaves (usa end)
        if self.es('SIMBOLOS', '{'):
            self.avanzar()
            cuerpo = NodoAST("cuerpo_while")
            tok = self.token_actual()
            cuerpo.linea = tok['linea']
            cuerpo.agregar_hijo(self.parse_lista_declaracion())
            nodo.agregar_hijo(cuerpo)
            if self.es('SIMBOLOS', '}'):
                self.avanzar()
            else:
                tok_act = self.token_actual()
                self.registrar_error("Se esperaba '}' para cerrar el while",
                                     tok_act['linea'], tok_act['columna'])
        else:
            cuerpo = NodoAST("cuerpo_while")
            tok = self.token_actual()
            cuerpo.linea = tok['linea']
            cuerpo.agregar_hijo(self.parse_lista_declaracion())
            nodo.agregar_hijo(cuerpo)
            if self.es('PALABRAS_RESERVADAS', 'end'):
                self.avanzar()
                if self.es('SIMBOLOS', ';'):
                    self.avanzar()
            else:
                tok_act = self.token_actual()
                self.registrar_error("Se esperaba 'end' para cerrar el 'while'",
                                     tok_act['linea'], tok_act['columna'])
        return nodo

    # repeticion → do lista_sentencias while expresion
    # El cuerpo del do se parsea usando parse_lista_declaracion_do() que
    # se detiene SOLO cuando encuentra el 'while' que cierra el do,
    # ignorando los 'while' que pudieran estar DENTRO del cuerpo.
    def parse_repeticion(self):
        nodo   = NodoAST("repeticion_do_while")
        tok_do = self.consumir('PALABRAS_RESERVADAS', 'do')
        if tok_do:
            nodo.linea   = tok_do['linea']
            nodo.columna = tok_do['columna']

        # El cuerpo termina en el 'while' que está al mismo nivel del 'do'.
        # Usamos un contador de profundidad para no confundir whiles internos.
        cuerpo = NodoAST("cuerpo_do")
        tok    = self.token_actual()
        cuerpo.linea = tok['linea']
        cuerpo.agregar_hijo(self._parse_lista_hasta_while_cierre())
        nodo.agregar_hijo(cuerpo)

        # Consumir el 'while' o 'until' de cierre del do
        if self.es('PALABRAS_RESERVADAS', 'until'):
            self.avanzar()   # consumir 'until'
        else:
            self.consumir('PALABRAS_RESERVADAS', 'while')

        # Condición: con o sin paréntesis
        if self.es('SIMBOLOS', '('):
            self.avanzar()
            cond = self.parse_expresion()
            self.consumir('SIMBOLOS', ')')
        else:
            cond = self.parse_expresion()
        nodo.agregar_hijo(cond)

        # Consumir SOLO el ';' de cierre, nada más
        if self.es('SIMBOLOS', ';'):
            self.avanzar()

        return nodo

    def _parse_lista_hasta_while_cierre(self):
        """
        Parsea sentencias del cuerpo del do-while.
        Lleva la cuenta de cuántos while/do anidados hay para saber
        cuál 'while' es el que cierra el do y no confundirlo con
        whiles internos.
        
        Lógica:
          - Cada 'while' con cuerpo { } o con 'end' es un while completo → no afecta al do.
          - El 'while' que cierra el do NO tiene cuerpo propio: viene después del cuerpo del do.
          - Cuando vemos 'while' y el siguiente token es '(' o una expresión (no '{'),
            ese ES el while de cierre → paramos.
        """
        nodo = NodoAST("lista_declaracion")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        while not self.es('EOF') and not self.es('SIMBOLOS', '}') \
              and not self.es('PALABRAS_RESERVADAS', 'else') \
              and not self.es('PALABRAS_RESERVADAS', 'until'):

            # ¿Es un 'while'? Hay que decidir si es interno o el cierre del do.
            if self.es('PALABRAS_RESERVADAS', 'while'):
                # Miramos qué viene después del 'while (cond)':
                # Si tiene cuerpo propio (termina en end o {}) → es un while INTERNO
                # Si no tiene cuerpo (le sigue ';' o 'until' o EOF) → es el cierre del do
                if self._while_tiene_cuerpo():
                    nodo.agregar_hijo(self.parse_iteracion())
                else:
                    # Es el while de cierre del do → salimos sin consumirlo
                    break
            # 'end' solo detiene el bucle si NO hay un while pendiente de cerrar
            # (ese caso ya lo maneja parse_iteracion internamente)
            elif self.es('PALABRAS_RESERVADAS', 'end'):
                break
            else:
                decl = self.parse_declaracion()
                if decl:
                    nodo.agregar_hijo(decl)

        return nodo

    def _while_tiene_cuerpo(self):
        """
        Determina si el 'while' actual tiene cuerpo propio (while interno)
        o es el cierre de un do-while.

        Estrategia: busca hacia adelante si entre este 'while' y el siguiente
        'end', 'until', '}' o EOF hay tokens en líneas POSTERIORES a la
        condición. Si los hay → tiene cuerpo. Si no → es cierre del do.

        NO modifica self.pos.
        """
        n    = len(self.tokens)
        i    = self.pos + 1   # saltar el 'while'

        # ── Determinar la línea donde termina la condición ───────────
        # Avanzamos saltando la condición (con o sin paréntesis) para
        # saber en qué línea queda el último token de la condición.
        if i < n and self.tokens[i]['lexema'] == '(':
            profundidad = 0
            while i < n:
                lex = self.tokens[i]['lexema']
                if lex == '(': profundidad += 1
                elif lex == ')':
                    profundidad -= 1
                    i += 1
                    if profundidad == 0:
                        break
                    continue
                i += 1
        else:
            # Sin paréntesis: la condición termina cuando hay un salto de
            # línea seguido de algo que no sea parte de la expresión,
            # o cuando encontramos un token de inicio de sentencia.
            linea_while = self.tokens[self.pos]['linea']
            while i < n:
                t = self.tokens[i]
                # Si el token ya está en una línea distinta Y es inicio
                # de sentencia → la condición terminó en la línea anterior
                if t['linea'] > linea_while:
                    if (t['tipo'] == 'IDENTIFICADORES'
                            or (t['tipo'] == 'PALABRAS_RESERVADAS'
                                and t['lexema'] in ('int','float','bool',
                                    'if','while','do','cin','cout',
                                    'end','else','until'))
                            or t['lexema'] == '}'):
                        break
                # Fin explícito de expresión
                if t['lexema'] in (';', '{', '}') or t['tipo'] == 'EOF':
                    break
                if (t['tipo'] == 'PALABRAS_RESERVADAS'
                        and t['lexema'] in ('end','else','until')):
                    break
                i += 1

        # ── Ahora i apunta al primer token DESPUÉS de la condición ───
        if i >= n:
            return False

        tok_sig = self.tokens[i]

        # Si es 'end', '{' o inicio de sentencia → tiene cuerpo
        tiene_cuerpo = (
            tok_sig['lexema'] == '{'
            or tok_sig['lexema'] == 'end'
            or tok_sig['tipo'] == 'IDENTIFICADORES'
            or (tok_sig['tipo'] == 'PALABRAS_RESERVADAS'
                and tok_sig['lexema'] in ('int','float','bool',
                    'if','do','cin','cout'))
        )
        return tiene_cuerpo

    # sent_in → cin >> id ;
    def parse_sent_in(self):
        nodo    = NodoAST("sent_cin")
        tok_cin = self.consumir('PALABRAS_RESERVADAS', 'cin')
        if tok_cin:
            nodo.linea   = tok_cin['linea']
            nodo.columna = tok_cin['columna']

        # '>>' tokenizado como uno o dos tokens
        if self.es('OP_RELACIONAL', '>>'):
            self.avanzar()
        elif self.es('OP_RELACIONAL', '>'):
            self.avanzar()
            if self.es('OP_RELACIONAL', '>'):
                self.avanzar()
        # Si no hay '>>' simplemente reportamos error pero continuamos
        else:
            tok_act = self.token_actual()
            self.registrar_error(
                f"Se esperaba '>>' después de 'cin', se encontró '{tok_act['lexema']}'",
                tok_act['linea'], tok_act['columna']
            )

        id_tok = self.consumir('IDENTIFICADORES')
        if id_tok:
            nodo.agregar_hijo(NodoAST("id", id_tok['lexema'], id_tok['linea'], id_tok['columna']))

        if self.es('SIMBOLOS', ';'):
            self.avanzar()
        else:
            tok_act = self.token_actual()
            self.registrar_error(
                f"Se esperaba ';' al final de 'cin'",
                tok_act['linea'], tok_act['columna']
            )
        return nodo

    # sent_out → cout << salida
    def parse_sent_out(self):
        nodo     = NodoAST("sent_cout")
        tok_cout = self.consumir('PALABRAS_RESERVADAS', 'cout')
        if tok_cout:
            nodo.linea   = tok_cout['linea']
            nodo.columna = tok_cout['columna']

        # '<<' tokenizado de varias formas posibles
        self._consumir_op_salida()

        salida = self.parse_salida()
        nodo.agregar_hijo(salida)
        return nodo

    # salida → cadena | expresion | cadena << expresion | expresion << cadena
    def parse_salida(self):
        nodo = NodoAST("salida")
        tok  = self.token_actual()
        nodo.linea = tok['linea']

        if tok['tipo'] == 'STRING':
            cadena_tok = self.avanzar()
            nodo.agregar_hijo(NodoAST("cadena", cadena_tok['lexema'],
                                      cadena_tok['linea'], cadena_tok['columna']))
            if self._es_op_salida():
                self._consumir_op_salida()
                nodo.agregar_hijo(self.parse_expresion())
        else:
            nodo.agregar_hijo(self.parse_expresion())
            if self._es_op_salida():
                self._consumir_op_salida()
                if self.token_actual()['tipo'] == 'STRING':
                    cadena_tok = self.avanzar()
                    nodo.agregar_hijo(NodoAST("cadena", cadena_tok['lexema'],
                                              cadena_tok['linea'], cadena_tok['columna']))

        if self.es('SIMBOLOS', ';'):
            self.avanzar()

        return nodo

    def _es_op_salida(self):
        """True si el token actual es '<<'."""
        if self.es('OP_ARIT', '<<'):
            return True
        # Dos '<' consecutivos
        if self.es('OP_RELACIONAL', '<'):
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos+1]['lexema'] == '<':
                return True
        return False

    def _consumir_op_salida(self):
        if self.es('OP_ARIT', '<<'):
            self.avanzar()
        elif self.es('OP_RELACIONAL', '<'):
            self.avanzar()
            if self.es('OP_RELACIONAL', '<'):
                self.avanzar()
        else:
            tok_act = self.token_actual()
            self.registrar_error(
                f"Se esperaba '<<' después de 'cout', se encontró '{tok_act['lexema']}'",
                tok_act['linea'], tok_act['columna']
            )

    # ------------------------------------------------------------------
    # EXPRESIONES (precedencia ascendente)
    # ------------------------------------------------------------------

    # expresion → expresion_simple [ rel_op expresion_simple ]
    def parse_expresion(self):
        nodo_izq = self.parse_expresion_simple()
        tok      = self.token_actual()

        if tok['tipo'] == 'OP_RELACIONAL':
            op_tok  = self.avanzar()
            nodo_op = NodoAST("expresion_relacional", op_tok['lexema'],
                               op_tok['linea'], op_tok['columna'])
            nodo_op.agregar_hijo(nodo_izq)

            # Si después del operador hay algo parseable, lo parseamos
            tok_sig = self.token_actual()
            if tok_sig['tipo'] not in ('EOF',) and tok_sig['lexema'] not in (';', ')', '}', 'end', 'else', 'then'):
                nodo_op.agregar_hijo(self.parse_expresion_simple())
            else:
                self.registrar_error(
                    f"Falta operando derecho después de '{op_tok['lexema']}'",
                    tok_sig['linea'], tok_sig['columna']
                )
                nodo_op.agregar_hijo(NodoAST("error", "?", tok_sig['linea'], tok_sig['columna']))

            # Puede seguir otro rel_op (ej: && o ||)
            if self.token_actual()['tipo'] == 'OP_LOG':
                op_log  = self.avanzar()
                nodo_log = NodoAST("op_logico", op_log['lexema'], op_log['linea'], op_log['columna'])
                nodo_log.agregar_hijo(nodo_op)
                nodo_log.agregar_hijo(self.parse_expresion())
                return nodo_log

            return nodo_op

        # Puede haber un operador lógico &&/|| entre expresiones simples
        if tok['tipo'] == 'OP_LOG' and tok['lexema'] in ('&&', '||'):
            op_tok  = self.avanzar()
            nodo_op = NodoAST("op_logico", op_tok['lexema'], op_tok['linea'], op_tok['columna'])
            nodo_op.agregar_hijo(nodo_izq)
            nodo_op.agregar_hijo(self.parse_expresion())
            return nodo_op

        return nodo_izq

    # expresion_simple → termino { suma_op termino }
    def parse_expresion_simple(self):
        nodo = self.parse_termino()

        while self.token_actual()['tipo'] == 'OP_ARIT' and \
              self.token_actual()['lexema'] in ('+', '-', '++', '--'):
            op_tok  = self.avanzar()
            # Si '++' o '--' aparece como operador POSTFIJO sin operando derecho, es un inc/dec
            tok_sig = self.token_actual()
            if op_tok['lexema'] in ('++', '--') and \
               (tok_sig['lexema'] in (';', ')', '}', 'end', 'else') or tok_sig['tipo'] == 'EOF'):
                nodo_op = NodoAST("inc_dec", op_tok['lexema'], op_tok['linea'], op_tok['columna'])
                nodo_op.agregar_hijo(nodo)
                nodo = nodo_op
            else:
                nodo_op = NodoAST("expresion_aditiva", op_tok['lexema'],
                                   op_tok['linea'], op_tok['columna'])
                nodo_op.agregar_hijo(nodo)
                # Verificar que haya operando derecho
                tok_sig = self.token_actual()
                if tok_sig['lexema'] in (';', ')', '}', 'end', 'else', 'then') or tok_sig['tipo'] == 'EOF':
                    self.registrar_error(
                        f"Falta operando derecho después de '{op_tok['lexema']}'",
                        tok_sig['linea'], tok_sig['columna']
                    )
                    nodo_op.agregar_hijo(NodoAST("error", "?", tok_sig['linea'], tok_sig['columna']))
                else:
                    nodo_op.agregar_hijo(self.parse_termino())
                nodo = nodo_op

        return nodo

    # termino → factor { mult_op factor }
    def parse_termino(self):
        nodo = self.parse_factor()

        while self.token_actual()['tipo'] == 'OP_ARIT' and \
              self.token_actual()['lexema'] in ('*', '/', '%'):
            op_tok  = self.avanzar()
            nodo_op = NodoAST("expresion_multiplicativa", op_tok['lexema'],
                               op_tok['linea'], op_tok['columna'])
            nodo_op.agregar_hijo(nodo)
            nodo_op.agregar_hijo(self.parse_factor())
            nodo = nodo_op

        return nodo

    # factor → componente { pot_op componente }
    def parse_factor(self):
        nodo = self.parse_componente()

        while self.token_actual()['tipo'] == 'OP_ARIT' and \
              self.token_actual()['lexema'] == '^':
            op_tok  = self.avanzar()
            nodo_op = NodoAST("expresion_potencia", op_tok['lexema'],
                               op_tok['linea'], op_tok['columna'])
            nodo_op.agregar_hijo(nodo)
            nodo_op.agregar_hijo(self.parse_componente())
            nodo = nodo_op

        return nodo

    # componente → ( expresion ) | número | id | bool | op_logico componente
    def parse_componente(self):
        tok = self.token_actual()

        # Operador lógico unario: ! componente
        if tok['tipo'] == 'OP_LOG':
            op_tok  = self.avanzar()
            nodo_op = NodoAST("op_logico", op_tok['lexema'], op_tok['linea'], op_tok['columna'])
            nodo_op.agregar_hijo(self.parse_componente())
            return nodo_op

        # ( expresion )
        if tok['tipo'] == 'SIMBOLOS' and tok['lexema'] == '(':
            self.avanzar()
            nodo = self.parse_expresion()
            self.consumir('SIMBOLOS', ')')
            return nodo

        # Número
        if tok['tipo'] in ('ENTERO', 'FLOTANTE'):
            self.avanzar()
            return NodoAST("numero", tok['lexema'], tok['linea'], tok['columna'])

        # Cadena
        if tok['tipo'] == 'STRING':
            self.avanzar()
            return NodoAST("cadena", tok['lexema'], tok['linea'], tok['columna'])

        # Identificador (con posible ++ o -- postfijo)
        if tok['tipo'] == 'IDENTIFICADORES':
            self.avanzar()
            nodo = NodoAST("id", tok['lexema'], tok['linea'], tok['columna'])
            # ++ o -- postfijo pegado al identificador
            if self.token_actual()['tipo'] == 'OP_ARIT' and \
               self.token_actual()['lexema'] in ('++', '--'):
                op_tok  = self.avanzar()
                nodo_pp = NodoAST("inc_dec_postfijo", op_tok['lexema'],
                                   op_tok['linea'], op_tok['columna'])
                nodo_pp.agregar_hijo(nodo)
                return nodo_pp
            return nodo

        # true / false
        if tok['tipo'] == 'PALABRAS_RESERVADAS' and tok['lexema'] in ('true', 'false'):
            self.avanzar()
            return NodoAST("bool_literal", tok['lexema'], tok['linea'], tok['columna'])

        # ++ o -- prefijo solo (ej: ++x)
        if tok['tipo'] == 'OP_ARIT' and tok['lexema'] in ('++', '--'):
            self.avanzar()
            nodo_pp = NodoAST("inc_dec_prefijo", tok['lexema'], tok['linea'], tok['columna'])
            # Si hay un identificador después lo incluimos
            if self.es('IDENTIFICADORES'):
                id_tok = self.avanzar()
                nodo_pp.agregar_hijo(NodoAST("id", id_tok['lexema'],
                                              id_tok['linea'], id_tok['columna']))
            return nodo_pp

        # Operador aritmético inesperado (ej: "+" al inicio)
        if tok['tipo'] == 'OP_ARIT':
            self.registrar_error(
                f"Operador '{tok['lexema']}' inesperado en expresión",
                tok['linea'], tok['columna']
            )
            self.avanzar()
            return NodoAST("error", tok['lexema'], tok['linea'], tok['columna'])

        # Cualquier otra cosa no reconocida
        self.registrar_error(
            f"Expresión inesperada '{tok['lexema']}'",
            tok['linea'], tok['columna']
        )
        return NodoAST("error", tok['lexema'], tok['linea'], tok['columna'])