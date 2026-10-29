"""Modulo de normalizacion de funciones a partir de su arbol AST."""

import ast
import builtins
import copy


class NormalizadorAST(ast.NodeTransformer):
    """Recorre el arbol de una funcion y reemplaza nombres y literales por tokens genericos."""

    def __init__(self):
        # Guarda que VAR le toco a cada nombre, por ejemplo {"total": "VAR1"}
        self.variables: dict[str, str] = {}

    def obtener_var(self, nombre: str) -> str:
        """Devuelve el VAR de un nombre. Si todavia no tiene uno, le asigna el siguiente."""
        if nombre not in self.variables:
            numero = len(self.variables) + 1
            self.variables[nombre] = f"VAR{numero}"
        return self.variables[nombre]
 
    def _normalizar_funcion(self, nodo: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST:
        """Cambia el nombre de la funcion, saca el docstring y sigue con los hijos."""
        # El nombre de la funcion no debe influir en la comparacion
        nodo.name = "FUNC"

        # Si la primera instruccion es un texto suelto, es el docstring: lo sacamos
        if nodo.body:
            primero = nodo.body[0]
            if (isinstance(primero, ast.Expr)
                    and isinstance(primero.value, ast.Constant)
                    and isinstance(primero.value.value, str)):
                nodo.body = nodo.body[1:]

        # Una funcion no puede tener el cuerpo vacio, asi que ponemos un "pass"
        if not nodo.body:
            nodo.body = [ast.Pass()]

        self.generic_visit(nodo)
        return nodo

    def visit_FunctionDef(self, nodo: ast.FunctionDef) -> ast.AST:
        """Visita funciones normales."""
        return self._normalizar_funcion(nodo)

    def visit_AsyncFunctionDef(self, nodo: ast.AsyncFunctionDef) -> ast.AST:
        """Visita funciones asincronas."""
        return self._normalizar_funcion(nodo)

    def visit_arg(self, nodo: ast.arg) -> ast.AST:
        """Cambia el nombre de un parametro por su VAR."""
        nodo.arg = self.obtener_var(nodo.arg)
        self.generic_visit(nodo)
        return nodo

    def visit_Name(self, nodo: ast.Name) -> ast.AST:
        """Cambia el nombre de una variable por su VAR (salvo funciones propias de Python)."""
        if nodo.id in self.variables:
            # Ya tiene VAR asignado (por ejemplo, es un parametro)
            nodo.id = self.variables[nodo.id]
        elif hasattr(builtins, nodo.id):
            # Es una funcion propia de Python (len, print, range...): se deja igual
            pass
        else:
            nodo.id = self.obtener_var(nodo.id)
        return nodo

    def visit_ExceptHandler(self, nodo: ast.ExceptHandler) -> ast.AST:
        """En 'except Error as e', el nombre 'e' es un texto y no un Name, asi que lo cambiamos aca."""
        if nodo.name is not None:
            nodo.name = self.obtener_var(nodo.name)
        self.generic_visit(nodo)
        return nodo

    def visit_Constant(self, nodo: ast.Constant) -> ast.AST:
        """Reemplaza cualquier literal (numero, texto, True, False, None) por 'LIT'."""
        nodo.value = "LIT"
        return nodo

#1) punto de entrada 
def normalizar(nodo: ast.AST) -> ast.AST:
    """Devuelve una copia normalizada del arbol de una funcion, sin tocar el original."""
    copia = copy.deepcopy(nodo) # genera una copia para no modificar el original
    # Un normalizador nuevo por funcion, asi los VAR empiezan de 1
    normalizador = NormalizadorAST()
    copia = normalizador.visit(copia) # dispara el recorrido y normalizacion
    ast.fix_missing_locations(copia) # python recalcula nro de lineas y columnas
    return copia # arbol normalizado


if __name__ == "__main__":
    from extraccion import extraer_de_directorio

    funciones = extraer_de_directorio("ejemplos")

    # Armamos un diccionario 'archivo:nombre' -> FuncionInfo para buscarlas facil
    por_id = {f.identificador(): f for f in funciones}

    pares = [
        ("basicos.py:sumar_elementos", "sub/clon_renombrado.py:calcular_total"),
        ("basicos.py:inicializar_usuario_v1", "reordenadas.py:inicializar_usuario_v2"),
    ]

    for id_a, id_b in pares:
        print("=" * 60)
        print(f"Comparando {id_a}  vs  {id_b}")
        print("=" * 60)

        normalizados = []
        for identificador in (id_a, id_b):
            info = por_id[identificador]
            normalizado = normalizar(info.nodo)
            normalizados.append(normalizado)

            print(f"\n--- {identificador} (original) ---")
            print(ast.unparse(info.nodo))
            print(f"\n--- {identificador} (normalizado) ---")
            print(ast.unparse(normalizado))

        if ast.dump(normalizados[0]) == ast.dump(normalizados[1]):
            print("\nResultado: los arboles normalizados son IDENTICOS\n")
        else:
            print("\nResultado: los arboles normalizados NO son identicos\n")
