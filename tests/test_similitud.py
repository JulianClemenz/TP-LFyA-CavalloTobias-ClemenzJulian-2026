"""Tests de la herramienta que busca funciones similares."""

from pathlib import Path

from buscar_similares import buscar_top_similares
from extraccion import FuncionInfo, extraer_de_directorio
from similitud import UMBRAL, es_candidata_duplicado, similitud_jaccard, tokens_de_funcion

# La carpeta de ejemplos se ubica desde este archivo, asi funciona desde cualquier lugar
CARPETA_EJEMPLOS = Path(__file__).parent.parent / "ejemplos"


def obtener_funcion(identificador: str) -> FuncionInfo:
    """Devuelve la funcion de ejemplos que tiene ese 'archivo:nombre'."""
    for funcion in extraer_de_directorio(str(CARPETA_EJEMPLOS)):
        if funcion.identificador() == identificador:
            return funcion
    raise ValueError(f"No se encontro la funcion {identificador}")


def obtener_puntaje(identificador_a: str, identificador_b: str) -> float:
    """Devuelve el puntaje de similitud entre dos funciones de ejemplos."""
    funcion_a = obtener_funcion(identificador_a)
    funcion_b = obtener_funcion(identificador_b)
    return similitud_jaccard(tokens_de_funcion(funcion_a), tokens_de_funcion(funcion_b))


# Prueba que un clon que solo cambia los nombres de las variables da puntaje perfecto
def test_clon_con_variables_renombradas():
    puntaje = obtener_puntaje("basicos.py:sumar_elementos", "sub/clon_renombrado.py:calcular_total")
    assert puntaje == 1.0
    assert es_candidata_duplicado(puntaje) is True


# Prueba que un clon con las lineas en otro orden sigue llegando a ser mayor que 0.69
def test_clon_con_lineas_reordenadas():
    puntaje = obtener_puntaje("basicos.py:inicializar_usuario_v1", "reordenadas.py:inicializar_usuario_v2")
    assert puntaje >= UMBRAL
    assert es_candidata_duplicado(puntaje) is True


# Prueba que las funciones distintas que mas se parecen quedan debajo del umbral
def test_funciones_distintas_parecidas():
    puntaje = obtener_puntaje("basicos.py:sumar_elementos", "distintos.py:invertir_cadena")
    assert puntaje < UMBRAL
    assert es_candidata_duplicado(puntaje) is False


# Prueba que dos funciones con logica distinta quedan debajo del umbral
def test_funciones_claramente_distintas():
    puntaje = obtener_puntaje("distintos.py:buscar_maximo", "distintos.py:contar_vocales")
    assert puntaje < UMBRAL
    assert es_candidata_duplicado(puntaje) is False


# Prueba que la busqueda completa devuelve primero al clon de la funcion objetivo
def test_busqueda_encuentra_el_clon_primero():
    todas_las_funciones = extraer_de_directorio(str(CARPETA_EJEMPLOS))
    objetivo = obtener_funcion("basicos.py:sumar_elementos")

    resultados = buscar_top_similares(objetivo, todas_las_funciones, top_k=1)

    primera_funcion, _ = resultados[0]
    assert primera_funcion.identificador() == "sub/clon_renombrado.py:calcular_total"
