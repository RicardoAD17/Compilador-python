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

    def _subir_atributos(self, padre, hijo):
        if hijo is None:
            return

        padre.tipo_dato = getattr(hijo, "tipo_dato", None)
        padre.valor_constante = getattr(hijo, "valor_constante", None)

        if getattr(hijo, "conversion", None) is not None:
            padre.conversion = hijo.conversion

    def _lookup(self, nombre):
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def _registrar_uso(self, simbolo, nodo):
        linea = getattr(nodo, "linea", None)
        if linea is not None:
            simbolo["lineas"].append(linea)

    def _declarar(self, ident, tipo):
        nombre = ident.valor
        actual = self._ambitos[-1].get(nombre)
        if actual:
            # Redeclaración: se reporta el error, pero GANA LA ÚLTIMA declaración.
            self._error(ident, f"El identificador '{nombre}' ya fue declarado en este ámbito "
                               f"(ahora se trata como {tipo})")
            actual["lineas"].append(ident.linea)
            if tipo != actual["tipo"]:
                actual["tipo"] = tipo
                actual["desplazamiento"] = self._desplazamiento
                self._desplazamiento += self.TAMANOS.get(tipo, 0)
            actual["valor"] = None
            ident.tipo_dato = tipo
            ident.desplazamiento = actual["desplazamiento"]
            ident.error_semantico = True
            return
        registro = {
            "nombre": nombre, "tipo": tipo, "lineas": [ident.linea],
            "desplazamiento": self._desplazamiento,
            "ambito": len(self._ambitos) - 1,
            "valor": None,
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

    # ------------------------------------------------------------------
    # Utilidades para el seguimiento de valores (propagación de constantes)
    # ------------------------------------------------------------------

    def _modificadas(self, nodo, acc=None):
        """Nombres de variables que el subárbol puede modificar."""
        acc = set() if acc is None else acc
        if (nodo.tipo in ("asignacion", "sent_cin", "inc_dec",
                          "inc_dec_prefijo", "inc_dec_postfijo")
                and nodo.hijos and nodo.hijos[0].tipo == "id"):
            acc.add(nodo.hijos[0].valor)
        for h in nodo.hijos:
            self._modificadas(h, acc)
        return acc

    def _invalidar(self, nombres):
        """Marca como desconocido el valor de las variables indicadas."""
        for n in nombres:
            s = self._lookup(n)
            if s:
                s["valor"] = None

    def _snapshot(self):
        return [(s, s["valor"]) for s in self.tabla_simbolos]

    def _restaurar(self, snap):
        for s, v in snap:
            s["valor"] = v

    def _control(self, nodo):
        """if / while / do-while: analiza cuerpos y sube el booleano a la raíz."""
        if not nodo.hijos:
            return None

        if nodo.tipo == "seleccion_if":
            cond = nodo.hijos[0]
            self._condicion(cond)
            base = self._snapshot()
            for cuerpo in nodo.hijos[1:]:      # cada rama parte del mismo estado
                self._bloque(cuerpo)
                self._restaurar(base)
            mod = set()
            for cuerpo in nodo.hijos[1:]:
                self._modificadas(cuerpo, mod)
            self._invalidar(mod)
        elif nodo.tipo == "iteracion_while":
            mod = self._modificadas(nodo)
            self._invalidar(mod)               # en un ciclo el valor previo ya no es seguro
            cond = nodo.hijos[0]
            self._condicion(cond)
            for cuerpo in nodo.hijos[1:]:
                self._bloque(cuerpo)
            self._invalidar(mod)
        else:                                   # do-while: hijos = [cuerpo..., cond]
            mod = self._modificadas(nodo)
            self._invalidar(mod)
            for cuerpo in nodo.hijos[:-1]:
                self._bloque(cuerpo)
            cond = nodo.hijos[-1]
            self._condicion(cond)
            self._invalidar(mod)

        # subir el resultado booleano al nodo de control
        nodo.tipo_dato = "bool" if cond.tipo_dato == "bool" else None
        nodo.valor_constante = cond.valor_constante
        return None

    # ------------------------------------------------------------------
    # Visitante principal
    # ------------------------------------------------------------------

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
            self._registrar_uso(simbolo, nodo)
            nodo.tipo_dato = simbolo["tipo"]
            nodo.desplazamiento = simbolo["desplazamiento"]
            nodo.valor_constante = simbolo["valor"]
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

            return self._asignacion(
                nodo,
                destino,
                fuente,
                nodo.hijos[0] if nodo.hijos else nodo
            )
        if tipo == "sent_cin":
            self._visitar_hijos(nodo)
            self._invalidar(self._modificadas(nodo))     # cin cambia la variable
            return None
        if tipo in ("sent_expresion", "expresion_suelta"):
            return self._visitar_hijos(nodo)
        if tipo in ("then", "else", "cuerpo_while", "cuerpo_do"):
            self._bloque(nodo)
            return None
        if tipo in ("seleccion_if", "iteracion_while", "repeticion_do_while"):
            return self._control(nodo)
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
            objetivo = nodo.hijos[0] if nodo.hijos else None
            t = self._visitar(objetivo) if objetivo else None
            if objetivo is not None and objetivo.tipo == "error":
                return None
            if objetivo is None or objetivo.tipo != "id":
                self._error(nodo, f"El operador '{nodo.valor}' solo se aplica a una variable")
                return None
            if t is None:            # ya se reportó "no declarado"
                return None
            if t not in ("int", "float"):
                self._error(nodo, f"El operador '{nodo.valor}' requiere una variable numérica")
                return None
            nodo.tipo_dato = t
            simbolo = self._lookup(objetivo.valor)
            anterior = simbolo["valor"]
            if anterior is not None:
                nuevo = anterior + 1 if nodo.valor == "++" else anterior - 1
                simbolo["valor"] = nuevo                  # la variable cambia
                nodo.valor_constante = anterior if tipo == "inc_dec_postfijo" else nuevo
            return t
        return self._visitar_hijos(nodo)

    def _visitar_hijos(self, nodo):
        resultados = []

        for hijo in nodo.hijos:
            resultado = self._visitar(hijo)
            resultados.append(resultado)

        # Si el nodo funciona únicamente como envoltorio de una expresión,
        # hacemos subir los atributos semánticos.
        if len(nodo.hijos) == 1:
            self._subir_atributos(nodo, nodo.hijos[0])

        if nodo.tipo_dato is not None:
            return nodo.tipo_dato

        # Para nodos con varios hijos que no representan una expresión,
        # devolvemos el último resultado útil.
        for resultado in reversed(resultados):
            if resultado is not None:
                return resultado

        return None

    def _asignacion(self, nodo, destino, fuente, ident):
        if not destino or not fuente:
            return None

        # El resultado semántico de la asignación corresponde
        # al tipo de la variable destino.
        nodo.tipo_dato = destino

        fuente_nodo = nodo.hijos[1] if len(nodo.hijos) > 1 else None
        valor = getattr(fuente_nodo, "valor_constante", None)

        if destino == "float" and fuente == "int":
            nodo.conversion = "int→float"
            if fuente_nodo is not None:
                fuente_nodo.conversion = "int→float"
                for h in fuente_nodo.hijos:
                    if getattr(h, "tipo_dato", None) == "int":
                        h.conversion = "int→float"
            if valor is not None:
                valor = float(valor)
        elif destino != fuente:
            self._error(
                nodo,
                f"No se puede asignar un valor de tipo {fuente} "
                f"a una variable de tipo {destino}"
            )
            nodo.error_semantico = True
            return nodo.tipo_dato

        nodo.valor_constante = valor
        simbolo = self._lookup(ident.valor)
        if simbolo is not None:
            simbolo["valor"] = valor       # la tabla de símbolos guarda el valor
        return nodo.tipo_dato

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

        # Promoción: el operando int conserva su tipo, pero se marca la conversión.
        if "float" in tipos and "int" in tipos:
            nodo.conversion = "int→float"
            for h, t in zip(nodo.hijos, tipos):
                if t == "int":
                    h.conversion = "int→float"

        resultado = "float" if "float" in tipos else "int"
        valores = [h.valor_constante for h in nodo.hijos]
        nodo.tipo_dato = resultado
        if len(valores) == 2 and all(v is not None for v in valores):
            try:
                op = nodo.valor
                calculo = {"+": lambda a,b:a+b, "-":lambda a,b:a-b,
                    "*":lambda a,b:a*b, "/":lambda a,b:a/b,
                    "%":lambda a,b:a%b, "^":lambda a,b:a**b}[op]
                nodo.valor_constante = calculo(*valores)
                if op == "/" and resultado == "int":
                    nodo.valor_constante = int(nodo.valor_constante)
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
        vals = [h.valor_constante for h in nodo.hijos]
        if vals and all(v is not None for v in vals):
            if nodo.valor == "!" and len(vals) == 1:
                nodo.valor_constante = not vals[0]
            elif nodo.valor == "&&" and len(vals) == 2:
                nodo.valor_constante = vals[0] and vals[1]
            elif nodo.valor == "||" and len(vals) == 2:
                nodo.valor_constante = vals[0] or vals[1]
        return "bool"