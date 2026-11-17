def sumar(m1: list, m2: list) -> list:
    if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
        raise ValueError("Las matrices deben tener la misma dimensión para sumarse.")
    
    return [[m1[i][j] + m2[i][j] for j in range(len(m1[0]))] for i in range(len(m1))]

def multiplicar(m1: list, m2: list) -> list:
    if len(m1[0]) != len(m2):
        raise ValueError("El número de columnas de la matriz 1 debe ser igual al número de filas de la matriz 2.")
    
    result = [[0.0 for _ in range(len(m2[0]))] for _ in range(len(m1))]
    for i in range(len(m1)):
        for j in range(len(m2[0])):
            for k in range(len(m2)):
                result[i][j] += m1[i][k] * m2[k][j]
    return result

def transponer(m: list) -> list:
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]

def _get_minor(m, i, j):
    return [row[:j] + row[j+1:] for row in (m[:i]+m[i+1:])]

def determinante(m: list) -> float:
    if not m:
        raise ValueError("Matriz vacía.")
    if len(m) != len(m[0]):
        raise ValueError("La matriz debe ser cuadrada para calcular el determinante.")
    
    n = len(m)
    if n == 1:
        return float(m[0][0])
    if n == 2:
        return float(m[0][0]*m[1][1] - m[0][1]*m[1][0])
    
    det = 0
    for c in range(n):
        det += ((-1)**c) * m[0][c] * determinante(_get_minor(m, 0, c))
    return float(det)
