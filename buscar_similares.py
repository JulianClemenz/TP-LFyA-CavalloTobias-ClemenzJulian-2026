"""Módulo principal y CLI para buscar funciones similares por AST."""

import argparse
import sys
from pathlib import Path

from extraccion import FuncionInfo, extraer_de_directorio
from normalizacion import normalizar
from similitud import es_candidata_duplicado, serializar, similitud_jaccard


def buscar_top_similares(
    funcion_objetivo: FuncionInfo,
    todas_las_funciones: list[FuncionInfo],
    top_k: int = 5,
) -> list[tuple[FuncionInfo, float]]:
    """Compara la función objetivo contra las demás y devuelve las Top-K más similares."""
    # 1. Normalizamos y serializamos la función objetivo
    arbol_obj_norm = normalizar(funcion_objetivo.nodo)
    tokens_objetivo = serializar(arbol_obj_norm)

    resultados: list[tuple[FuncionInfo, float]] = []

    # 2. Recorremos y comparamos contra las demás funciones
    for otra in todas_las_funciones:
        # Omitimos comparar la función consigo misma
        if otra.identificador() == funcion_objetivo.identificador():
            continue

        # Normalizamos y serializamos la otra función
        arbol_otra_norm = normalizar(otra.nodo)
        tokens_otra = serializar(arbol_otra_norm)

        # Calculamos el puntaje de similitud
        score = similitud_jaccard(tokens_objetivo, tokens_otra)
        resultados.append((otra, score))

    # 3. Ordenamos de mayor a menor puntaje
    resultados.sort(key=lambda item: item[1], reverse=True)

    return resultados[:top_k]


def construir_parser() -> argparse.ArgumentParser:
    """Configura los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Buscador de funciones estructuralmente similares mediante AST."
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Ruta a la carpeta con archivos .py a analizar.",
    )
    parser.add_argument(
        "--funcion",
        required=True,
        help="Función objetivo con formato 'archivo.py:nombre_funcion'.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Cantidad de funciones similares a mostrar (por defecto: 5).",
    )
    return parser


def buscar_funcion_objetivo(
    funciones: list[FuncionInfo],
    identificador_buscado: str,
    ruta_base: Path,
) -> FuncionInfo | None:
    """Encuentra la función objetivo tolerando rutas con prefijo de carpeta o separadores del SO."""
    buscado_normalizado = identificador_buscado.replace("\\", "/")

    for f in funciones:
        if f.identificador() == buscado_normalizado:
            return f

        # Caso donde el usuario incluye el directorio base (ej: 'ejemplos/basicos.py:suma')
        if ":" in buscado_normalizado:
            archivo_buscado, nombre_buscado = buscado_normalizado.split(":", 1)
            try:
                archivo_rel = Path(archivo_buscado).relative_to(ruta_base).as_posix()
                if f.identificador() == f"{archivo_rel}:{nombre_buscado}":
                    return f
            except ValueError:
                pass

    return None


def main() -> None:
    """Punto de entrada de la CLI."""
    parser = construir_parser()
    args = parser.parse_args()

    ruta_dir = Path(args.dir)
    if not ruta_dir.is_dir():
        print(f"Error: La carpeta '{args.dir}' no existe o no es válida.", file=sys.stderr)
        sys.exit(1)

    # 1. Extracción de todas las funciones
    funciones = extraer_de_directorio(str(ruta_dir))
    if not funciones:
        print(f"No se encontraron funciones en '{args.dir}'.", file=sys.stderr)
        sys.exit(1)

    # 2. Localización de la función objetivo
    funcion_objetivo = buscar_funcion_objetivo(funciones, args.funcion, ruta_dir)
    if funcion_objetivo is None:
        print(
            f"Error: No se encontró la función '{args.funcion}' en '{args.dir}'.",
            file=sys.stderr,
        )
        print("\nFunciones disponibles:", file=sys.stderr)
        for f in funciones:
            print(f"  - {f.identificador()}", file=sys.stderr)
        sys.exit(1)

    # 3. Cálculo de similitudes y ranking
    top_similares = buscar_top_similares(
        funcion_objetivo=funcion_objetivo,
        todas_las_funciones=funciones,
        top_k=args.top,
    )

    # 4. Presentación de resultados
    print("=" * 70)
    print(f"Función objetivo: {funcion_objetivo.identificador()} (línea {funcion_objetivo.linea})")
    print(f"Top {args.top} funciones más similares:")
    print("=" * 70)

    if not top_similares:
        print("No se encontraron otras funciones para comparar.")
        return

    print(f"{'Ranking':<8} | {'Función':<42} | {'Score':>7} | ¿Candidata?")
    print("-" * 70)

    for i, (f_similar, score) in enumerate(top_similares, start=1):
        candidata = "SÍ" if es_candidata_duplicado(score) else "NO"
        print(f"{i:<8} | {f_similar.identificador():<42} | {score:>7.2f} | {candidata}")


if __name__ == "__main__":
    main()

