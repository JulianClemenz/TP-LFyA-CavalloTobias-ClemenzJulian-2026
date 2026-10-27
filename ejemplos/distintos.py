# Casos de prueba:
# Funciones con lógica y estructuras distintas entre sí.

def buscar_maximo(elementos):
    mayor = elementos[0]
    for x in elementos:
        if x > mayor:
            mayor = x
    return mayor

def contar_vocales(texto):
    contador = 0
    for letra in texto.lower():
        if letra in "aeiou":
            contador += 1
    return contador

def invertir_cadena(cadena):
    invertida = ""
    for caracter in cadena:
        invertida = caracter + invertida
    return invertida

