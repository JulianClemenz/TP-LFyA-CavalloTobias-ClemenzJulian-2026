# Casos de prueba:
# 1. sumar_elementos: función base para clon con variables renombradas.
# 2. inicializar_usuario_v1: función base para clon con líneas reordenadas.

def sumar_elementos(numeros):
    total = 0
    for elemento in numeros:
        total += elemento
    return total

def inicializar_usuario_v1(nombre, edad):
    saludo = f"Hola, {nombre}"
    es_mayor = edad >= 18
    activo = True
    return saludo, es_mayor, activo

