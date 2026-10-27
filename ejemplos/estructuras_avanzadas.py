# Casos de prueba:
# 1. Clase con método.
# 2. Función con función anidada.
# 3. Función asíncrona (async).

class OperadorMatematico:
    def duplicar(self, numero):
        return numero * 2

def calcular_con_anidada(valor_base):
    def aplicar_descuento(x):
        return x * 0.9
    return aplicar_descuento(valor_base)

async def consultar_servicio_async(direccion):
    mensaje = f"Consultando servicio en {direccion}"
    return mensaje

