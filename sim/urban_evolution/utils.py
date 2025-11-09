# Funciones utilitarias pequeñas y libres de dependencias de otros módulos del modelo


def manhattan_dist(a, b):
    # Distancia Manhattan entre coordenadas de grilla (tupla o lista de 2 ints)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
