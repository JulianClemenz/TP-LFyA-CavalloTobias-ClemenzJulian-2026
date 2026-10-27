# Casos de prueba:
# 1. inicializar_usuario_v2: clon de 'inicializar_usuario_v1' con líneas independientes reordenadas.

def inicializar_usuario_v2(nombre, edad):
    activo = True
    es_mayor = edad >= 18
    saludo = f"Hola, {nombre}"
    return saludo, es_mayor, activo

