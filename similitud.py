"""Modulo de similitud: convierte el arbol normalizado de una funcion en una lista de tokens."""

import ast

from extraccion import FuncionInfo
from normalizacion import normalizar

# Cantidad de tokens seguidos en cada pedacito (n-grama) que se compara.
# Elegido con la calibracion. Se descarto n=1 porque ignora el orden de los tokens;
# entre n=2 y n=5, n=2 dio el mayor margen entre clones y no clones (0.08).
# Con n>=4 los clones ya no se distinguen.
N_GRAMA = 2

# Puntaje minimo para que dos funciones sean "candidatas a duplicado".
# Punto medio entre el clon con menor puntaje (0.73) y el no clon con mayor
# puntaje (0.65), usando n=2.
UMBRAL = 0.69


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


def obtener_ngramas(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    """Devuelve el conjunto de pedacitos de n tokens seguidos."""
    # Si la lista es mas corta que n, usamos toda la lista como un solo pedacito
    if len(tokens) < n:
        return {tuple(tokens)}

    ngramas: set[tuple[str, ...]] = set()
    for i in range(len(tokens) - n + 1):
        pedacito = tuple(tokens[i:i + n])
        ngramas.add(pedacito)
    return ngramas


def similitud_jaccard(tokens_a: list[str], tokens_b: list[str], n: int = N_GRAMA) -> float:
    """Devuelve un puntaje de 0 (nada en comun) a 1 (iguales) usando Jaccard sobre n-gramas."""
    # Dos listas vacias se consideran iguales
    if not tokens_a and not tokens_b:
        return 1.0

    ngramas_a = obtener_ngramas(tokens_a, n)
    ngramas_b = obtener_ngramas(tokens_b, n)

    en_comun = ngramas_a & ngramas_b
    todos = ngramas_a | ngramas_b
    return len(en_comun) / len(todos)


def es_candidata_duplicado(puntaje: float) -> bool:
    """Devuelve True si el puntaje llega al umbral."""
    return puntaje >= UMBRAL


if __name__ == "__main__":
    from extraccion import extraer_de_directorio

    funciones = extraer_de_directorio("ejemplos")

    # Tokens de cada funcion, guardados por su 'archivo:nombre'
    tokens_por_id: dict[str, list[str]] = {}
    for f in funciones:
        tokens_por_id[f.identificador()] = tokens_de_funcion(f)

    # Pares que sabemos de antemano que son clones
    clones = [
        ("basicos.py:sumar_elementos", "sub/clon_renombrado.py:calcular_total"),
        ("basicos.py:inicializar_usuario_v1", "reordenadas.py:inicializar_usuario_v2"),
    ]

    def es_clon(id_a: str, id_b: str) -> bool:
        """Dice si el par esta en la lista de clones (en cualquier orden)."""
        return (id_a, id_b) in clones or (id_b, id_a) in clones

    # Armamos todos los pares posibles, sin repetir y sin comparar una funcion consigo misma
    ids = list(tokens_por_id.keys())
    pares: list[tuple[str, str]] = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            pares.append((ids[i], ids[j]))

    # --- Calibracion: probamos n de 2 a 5 ---
    print("\n--- Calibracion de n ---")
    print("Se descarta n=1 porque ignora el orden de los tokens.")
    print(f"{'n':>2} | {'clon mas bajo':>13} | {'no clon mas alto':>16} | {'margen':>7}")

    mejor_n = 0
    mejor_margen = -1.0
    mejor_umbral = 0.0

    for n in range(2, 6):
        puntajes_clones: list[float] = []
        puntajes_no_clones: list[float] = []
        for id_a, id_b in pares:
            puntaje = similitud_jaccard(tokens_por_id[id_a], tokens_por_id[id_b], n)
            if es_clon(id_a, id_b):
                puntajes_clones.append(puntaje)
            else:
                puntajes_no_clones.append(puntaje)

        clon_mas_bajo = min(puntajes_clones)
        no_clon_mas_alto = max(puntajes_no_clones)
        margen = clon_mas_bajo - no_clon_mas_alto
        print(f"{n:>2} | {clon_mas_bajo:>13.2f} | {no_clon_mas_alto:>16.2f} | {margen:>7.2f}")

        # Nos quedamos con el mayor margen. Con ">" estricto, en un empate gana el n mas chico
        if margen > mejor_margen:
            mejor_n = n
            mejor_margen = margen
            # El umbral es el punto medio entre los dos valores
            mejor_umbral = round((clon_mas_bajo + no_clon_mas_alto) / 2, 2)

    print(f"\nn elegido: {mejor_n} (margen {mejor_margen:.2f})")
    print(f"Umbral propuesto: {mejor_umbral:.2f}")

    # --- Tabla de todos los pares con el n y el umbral elegidos ---
    resultados: list[tuple[float, str, str]] = []
    for id_a, id_b in pares:
        puntaje = similitud_jaccard(tokens_por_id[id_a], tokens_por_id[id_b], mejor_n)
        resultados.append((puntaje, id_a, id_b))

    # Ordenamos de mayor a menor puntaje
    resultados.sort(reverse=True)

    print(f"\n--- Todos los pares (n={mejor_n}, umbral={mejor_umbral:.2f}) ---")
    print(f"{'par de funciones':<80} | {'puntaje':>7} | {'tipo':>7} | supera")
    for puntaje, id_a, id_b in resultados:
        par = f"{id_a}  vs  {id_b}"
        tipo = "CLON" if es_clon(id_a, id_b) else "NO CLON"
        supera = "SI" if puntaje >= mejor_umbral else "NO"
        print(f"{par:<80} | {puntaje:>7.2f} | {tipo:>7} | {supera}")

    # Avisamos si las constantes del archivo no coinciden con la calibracion
    if N_GRAMA == mejor_n and UMBRAL == mejor_umbral:
        print("\nLas constantes N_GRAMA y UMBRAL coinciden con la calibracion.")
    else:
        print("\nAviso: actualizar N_GRAMA y UMBRAL con los valores de la calibracion.")
