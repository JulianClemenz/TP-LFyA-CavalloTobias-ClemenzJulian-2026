# Casos de prueba en subcarpeta:
# 1. calcular_total: clon estructural de 'sumar_elementos' con nombres cambiados.

def calcular_total(lista_valores):
    acumulador = 0
    for valor in lista_valores:
        acumulador += valor
    return acumulador

