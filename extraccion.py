"""Módulo de extracción de funciones a partir de código Python y archivos AST."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FuncionInfo:
    """Representa los datos extraídos de una función y su subárbol AST."""
    nombre: str
    archivo: str
    linea: int
    nodo: ast.AST

    def identificador(self) -> str:
        """Devuelve una identificación con formato 'archivo:nombre'."""
        return f"{self.archivo}:{self.nombre}"


class RecolectorFunciones(ast.NodeVisitor):
    """Recorre el árbol AST buscando definiciones de funciones y métodos."""

    def __init__(self, archivo: str):
        self.archivo = archivo
        self.funciones: list[FuncionInfo] = []

    def _guardar_funcion(self, nodo: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Extrae la información de un nodo de función y continúa el recorrido."""
        info = FuncionInfo(
            nombre=nodo.name,
            archivo=self.archivo,
            linea=nodo.lineno,
            nodo=nodo,
        )
        self.funciones.append(info)
        # generic_visit permite encontrar funciones anidadas y métodos dentro de clases
        self.generic_visit(nodo)

    def visit_FunctionDef(self, nodo: ast.FunctionDef) -> None:
        """Visita funciones normales."""
        self._guardar_funcion(nodo)

    def visit_AsyncFunctionDef(self, nodo: ast.AsyncFunctionDef) -> None:
        """Visita funciones asíncronas."""
        self._guardar_funcion(nodo)


def extraer_de_codigo(codigo: str, archivo: str = "<codigo pegado>") -> list[FuncionInfo]:
    """Parsea código Python en texto plano y extrae sus funciones."""
    arbol = ast.parse(codigo)
    recolector = RecolectorFunciones(archivo)
    recolector.visit(arbol)
    return recolector.funciones


def extraer_de_directorio(directorio: str) -> list[FuncionInfo]:
    """Busca recursivamente archivos .py y extrae todas sus funciones."""
    ruta_base = Path(directorio)
    todas_las_funciones: list[FuncionInfo] = []

    # sorted garantiza un orden de recorrido consistente
    for ruta_archivo in sorted(ruta_base.rglob("*.py")):
        # Guardamos la ruta relativa con barras normales '/'
        ruta_relativa = ruta_archivo.relative_to(ruta_base).as_posix()

        try:
            contenido = ruta_archivo.read_text(encoding="utf-8")
            funciones = extraer_de_codigo(contenido, archivo=ruta_relativa)
            todas_las_funciones.extend(funciones)
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"Aviso: no se pudo procesar '{ruta_relativa}': {error}")

    return todas_las_funciones


if __name__ == "__main__":
    funciones = extraer_de_directorio("ejemplos")

    print("\n--- Funciones encontradas ---")
    for f in funciones:
        print(f"{f.identificador()} (línea {f.linea})")

    print(f"\nTotal de funciones encontradas: {len(funciones)}")

