"""Modulo de similitud: convierte el arbol normalizado de una funcion en una lista de tokens."""

import ast

from extraccion import FuncionInfo
from normalizacion import normalizar


def serializar(nodo: ast.AST) -> list[str]:
    """Recorre el arbol en pre-order y devuelve la lista de tokens."""
    tokens: list[str] = []
    _recorrer_preorder(nodo, tokens)
    return tokens


def _recorrer_preorder(nodo: ast.AST, tokens: list[str]) -> None:
    """Anota el nodo actual y despues recorre sus hijos en orden (recursivo)."""
    # Load, Store y Del solo dicen si la variable se lee o se escribe: los salteamos
    if isinstance(nodo, (ast.Load, ast.Store, ast.Del)):
        return

    # 1) Primero el tipo de nodo
    tokens.append(type(nodo).__name__)

    # 2) Despues su valor normalizado, si tiene uno
    if isinstance(nodo, ast.Name):
        tokens.append(nodo.id)
    elif isinstance(nodo, ast.arg):
        tokens.append(nodo.arg)
    elif isinstance(nodo, ast.Constant):
        tokens.append(str(nodo.value))
    elif isinstance(nodo, ast.Attribute):
        tokens.append(nodo.attr)
    elif isinstance(nodo, ast.ExceptHandler) and nodo.name is not None:
        tokens.append(nodo.name)
    elif isinstance(nodo, ast.keyword) and nodo.arg is not None:
        tokens.append(nodo.arg)
    # El nombre de la funcion ("FUNC") no se agrega porque es igual en todas

    # 3) Por ultimo, cada hijo en orden
    for hijo in ast.iter_child_nodes(nodo):
        _recorrer_preorder(hijo, tokens)


def tokens_de_funcion(info: FuncionInfo) -> list[str]:
    """Normaliza una funcion extraida y devuelve su lista de tokens."""
    arbol_normalizado = normalizar(info.nodo)
    return serializar(arbol_normalizado)


if __name__ == "__main__":
    from extraccion import extraer_de_directorio

    funciones = extraer_de_directorio("ejemplos")

    # Diccionario 'archivo:nombre' -> FuncionInfo para buscarlas facil
    por_id = {f.identificador(): f for f in funciones}

    # Par de clones con variables renombradas
    id_a = "basicos.py:sumar_elementos"
    id_b = "sub/clon_renombrado.py:calcular_total"
    tokens_a = tokens_de_funcion(por_id[id_a])
    tokens_b = tokens_de_funcion(por_id[id_b])

    print(f"\n--- {id_a} ({len(tokens_a)} tokens) ---")
    print(tokens_a)
    print(f"\n--- {id_b} ({len(tokens_b)} tokens) ---")
    print(tokens_b)

    if tokens_a == tokens_b:
        print("\nResultado: las listas de tokens son IGUALES")
    else:
        print("\nResultado: las listas de tokens NO son iguales")

    # Funcion con otra funcion adentro
    id_c = "estructuras_avanzadas.py:calcular_con_anidada"
    tokens_c = tokens_de_funcion(por_id[id_c])
    print(f"\n--- {id_c} ({len(tokens_c)} tokens) ---")
    print(tokens_c)
