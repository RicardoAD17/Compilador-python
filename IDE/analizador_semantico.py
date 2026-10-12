"""Análisis semántico del AST producido por ``AnalizadorSintactico``.

Las anotaciones se guardan en una copia del AST, sin modificar el árbol base.
El lenguaje usa un ámbito global y ámbitos anidados para los cuerpos de control.
"""

from copy import deepcopy


class AnalizadorSemantico:
    TAMANOS = {"bool": 1, "int": 4, "float": 8}

    def __init__(self, ast):
        self.ast = ast
        self.errores = []
        self.tabla_simbolos = []
        self._ambitos = [{}]
        self._desplazamiento = 0

    def analizar(self):
        anotado = deepcopy(self.ast)
        if anotado is not None:
            self._visitar(anotado)
        return anotado, self.tabla_simbolos, self.errores

    def _error(self, nodo, mensaje):
        linea = getattr(nodo, "linea", None) or 1
        columna = getattr(nodo, "columna", None) or 1
        self.errores.append({
            "linea": linea, "columna": columna,
            "mensaje": f"ERROR SEMÁNTICO: {mensaje} — Línea {linea}, Col. {columna}",
        })

    def _lookup(self, nombre):
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def _declarar(self, ident, tipo):
        nombre = ident.valor
        actual = self._ambitos[-1].get(nombre)
        if actual:
            actual["lineas"].append(ident.linea)
            self._error(ident, f"El identificador '{nombre}' ya fue declarado en este ámbito")
            ident.tipo_dato = tipo
            ident.error_semantico = True
            return
        registro = {
            "nombre": nombre, "tipo": tipo, "lineas": [ident.linea],
            "desplazamiento": self._desplazamiento,
            "ambito": len(self._ambitos) - 1,
        }
        self._desplazamiento += self.TAMANOS.get(tipo, 0)
        self._ambitos[-1][nombre] = registro
        self.tabla_simbolos.append(registro)
        ident.tipo_dato = tipo
        ident.desplazamiento = registro["desplazamiento"]

    def _bloque(self, nodo):
        self._ambitos.append({})
        self._visitar_hijos(nodo)
        self._ambitos.pop()

    def _visitar(self, nodo):
        tipo = nodo.tipo
        nodo.tipo_dato = None
        nodo.valor_constante = None
        nodo.conversion = None

        if tipo == "declaracion_variable":
            if len(nodo.hijos) >= 2:
                declarado = nodo.hijos[0].valor
                nodo.hijos[0].tipo_dato = declarado
                for ident in nodo.hijos[1].hijos:
                    self._declarar(ident, declarado)
            return None
        if tipo == "id":
            simbolo = self._lookup(nodo.valor)
            if simbolo is None:
                self._error(nodo, f"El identificador '{nodo.valor}' no está declarado")
                nodo.error_semantico = True
                return None
            nodo.tipo_dato = simbolo["tipo"]
            nodo.desplazamiento = simbolo["desplazamiento"]
            return nodo.tipo_dato
        if tipo == "numero":
            nodo.tipo_dato = "float" if "." in str(nodo.valor) else "int"
            try:
                nodo.valor_constante = float(nodo.valor) if nodo.tipo_dato == "float" else int(nodo.valor)
            except (ValueError, TypeError):
                pass
            return nodo.tipo_dato
        if tipo == "bool_literal":
            nodo.tipo_dato = "bool"
            nodo.valor_constante = nodo.valor == "true"
            return "bool"
        if tipo == "cadena":
            nodo.tipo_dato = "string"
            nodo.valor_constante = nodo.valor
            return "string"
        if tipo in ("error", "sent_expresion_vacia"):
            return None
        if tipo == "asignacion":
            destino = self._visitar(nodo.hijos[0]) if nodo.hijos else None
            fuente = self._visitar(nodo.hijos[1]) if len(nodo.hijos) > 1 else None
            self._asignacion(nodo, destino, fuente, nodo.hijos[0] if nodo.hijos else nodo)
            return None
        if tipo == "sent_cin":
            self._visitar_hijos(nodo)
            return None
        if tipo in ("sent_expresion", "expresion_suelta"):
            return self._visitar_hijos(nodo)
        if tipo in ("then", "else", "cuerpo_while", "cuerpo_do"):
            self._bloque(nodo)
            return None
        if tipo in ("seleccion_if", "iteracion_while", "repeticion_do_while"):
            if nodo.hijos:
                cond = nodo.hijos[0] if tipo == "seleccion_if" else None
                if tipo == "seleccion_if":
                    self._condicion(cond)
                    for cuerpo in nodo.hijos[1:]: self._bloque(cuerpo)
                elif tipo == "iteracion_while":
                    self._condicion(nodo.hijos[0])
                    for cuerpo in nodo.hijos[1:]: self._bloque(cuerpo)
                else:
                    for cuerpo in nodo.hijos[:-1]: self._bloque(cuerpo)
                    self._condicion(nodo.hijos[-1])
            return None
        if tipo in ("expresion_aditiva", "expresion_multiplicativa", "expresion_potencia"):
            operandos = [self._visitar(h) for h in nodo.hijos]
            return self._aritmetica(nodo, operandos)
        if tipo == "expresion_relacional":
            tipos = [self._visitar(h) for h in nodo.hijos]
            return self._relacional(nodo, tipos)
        if tipo == "op_logico":
            tipos = [self._visitar(h) for h in nodo.hijos]
            return self._logico(nodo, tipos)
        if tipo in ("inc_dec", "inc_dec_prefijo", "inc_dec_postfijo"):
            t = self._visitar(nodo.hijos[0]) if nodo.hijos else None
            if t not in ("int", "float"):
                self._error(nodo, f"El operador '{nodo.valor}' requiere una variable numérica")
                return None
            nodo.tipo_dato = t
            return t
        return self._visitar_hijos(nodo)

    def _visitar_hijos(self, nodo):
        resultado = None
        for hijo in nodo.hijos:
            resultado = self._visitar(hijo)
        return resultado

    def _asignacion(self, nodo, destino, fuente, ident):
        if destino and fuente:
            if destino == "float" and fuente == "int":
                ident.conversion = "int→float"
                nodo.conversion = "int→float"
            elif destino != fuente:
                self._error(nodo, f"No se puede asignar un valor de tipo {fuente} a una variable de tipo {destino}")

    def _condicion(self, nodo):
        t = self._visitar(nodo)
        if t and t != "bool":
            self._error(nodo, f"La condición debe ser bool, se obtuvo {t}")

    def _aritmetica(self, nodo, tipos):
        if not tipos or any(t is None for t in tipos): return None
        if any(t not in ("int", "float") for t in tipos):
            self._error(nodo, f"El operador '{nodo.valor}' solo acepta operandos numéricos")
            return None
        if nodo.valor == "%" and any(t != "int" for t in tipos):
            self._error(nodo, "El operador '%' requiere operandos int")
            return None
        if len(tipos) == 2 and tipos[0] != tipos[1]:
            nodo.conversion = "int→float" if "float" in tipos else None
        resultado = "float" if "float" in tipos or nodo.valor == "/" else "int"
        nodo.tipo_dato = resultado
        valores = [h.valor_constante for h in nodo.hijos]
        if len(valores) == 2 and all(v is not None for v in valores):
            try:
                op = nodo.valor
                calculo = {"+": lambda a,b:a+b, "-":lambda a,b:a-b,
                    "*":lambda a,b:a*b, "/":lambda a,b:a/b,
                    "%":lambda a,b:a%b, "^":lambda a,b:a**b}[op]
                nodo.valor_constante = calculo(*valores)
            except (ArithmeticError, OverflowError):
                self._error(nodo, "La operación constante no está definida (por ejemplo, división entre cero)")
        return resultado

    def _relacional(self, nodo, tipos):
        if not tipos or any(t is None for t in tipos): return None
        op = nodo.valor
        if len(tipos) != 2:
            self._error(nodo, f"El operador relacional '{op}' requiere dos operandos")
        elif op in ("==", "!=") and tipos[0] == tipos[1] and tipos[0] == "bool":
            pass
        elif any(t not in ("int", "float") for t in tipos):
            self._error(nodo, f"El operador relacional '{op}' requiere operandos numéricos compatibles")
        if len(nodo.hijos) == 2 and all(getattr(h, "valor_constante", None) is not None for h in nodo.hijos):
            try:
                nodo.valor_constante = {"<":lambda a,b:a<b, ">":lambda a,b:a>b,
                    "<=":lambda a,b:a<=b, ">=":lambda a,b:a>=b,
                    "==":lambda a,b:a==b, "!=":lambda a,b:a!=b}[op](nodo.hijos[0].valor_constante, nodo.hijos[1].valor_constante)
            except (KeyError, TypeError): pass
        nodo.tipo_dato = "bool"
        return "bool"

    def _logico(self, nodo, tipos):
        if not tipos or any(t is None for t in tipos): return None
        if any(t != "bool" for t in tipos):
            self._error(nodo, f"El operador lógico '{nodo.valor}' requiere operandos bool")
            return None
        nodo.tipo_dato = "bool"
        if nodo.valor == "!" and len(nodo.hijos) == 1 and nodo.hijos[0].valor_constante is not None:
            nodo.valor_constante = not nodo.hijos[0].valor_constante
        return "bool"
