import math


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

    # --- MITIGACIÓN SEGURIDAD: Protección contra DoS Algorítmico ---
    # El algoritmo de Laplace tiene complejidad O(n!). Dimensiones superiores a 8
    # saturan el uso de CPU provocando una denegación de servicio en el servidor.
    if len(m) > 8:
        raise ValueError("Por seguridad y protección contra denegación de servicio (DoS), el tamaño máximo para determinante es 8x8.")

    n = len(m)
    if n == 1:
        return float(m[0][0])
    if n == 2:
        return float(m[0][0]*m[1][1] - m[0][1]*m[1][0])

    det = 0
    for c in range(n):
        det += ((-1)**c) * m[0][c] * determinante(_get_minor(m, 0, c))
    return float(det)


def vertice_dona(u: float, v: float, R: float = 10.0, r: float = 5.0) -> list[float]:
    """Calcula un vértice del Toroide (Dona) en el dominio paramétrico (u, v)."""
    x = (R + r * math.cos(v)) * math.cos(u)
    y = (R + r * math.cos(v)) * math.sin(u)
    z = r * math.sin(v)
    return [x, y, z]


def vertice_taza(u: float, v: float) -> list[float]:
    """Calcula un vértice de una Taza con asa sobre el mismo dominio (u, v) en [0, 2*pi)."""
    fraccion_asa = 0.25 * 2 * math.pi
    if u < fraccion_asa:
        # Asa lateral de la taza
        s = u / fraccion_asa
        ang = math.pi / 2 - math.pi * s
        cx = 5.5 + 4.5 * math.cos(ang)
        cy = 4.0 * math.sin(ang)
        r_asa = 1.2
        return [
            cx + r_asa * math.cos(v) * math.cos(ang),
            cy + r_asa * math.cos(v) * math.sin(ang),
            r_asa * math.sin(v),
        ]
    else:
        # Cuerpo cilíndrico hueco de la taza
        s = (u - fraccion_asa) / (2 * math.pi - fraccion_asa)
        r_cuerpo = 6.5
        altura = 12.0
        if s < 0.25:
            # Base inferior
            rad = (s / 0.25) * r_cuerpo
            y = -altura / 2
        elif s < 0.65:
            # Pared exterior
            rad = r_cuerpo
            y = -altura / 2 + ((s - 0.25) / 0.40) * altura
        else:
            # Pared interior hueca
            rad = r_cuerpo - 0.8
            y = altura / 2 - ((s - 0.65) / 0.35) * (altura - 1.2)
        return [
            -2.0 + rad * math.cos(v),
            y,
            rad * math.sin(v),
        ]


def calcular_morph(t: float, resolucion: int = 50) -> list[list[float]]:
    """Interpola linealmente P(u,v,t) = (1 - t)*D(u,v) + t*T(u,v)."""
    if not math.isfinite(t) or not (0.0 <= t <= 1.0):
        raise ValueError("El parámetro t debe ser finito y estar entre 0.0 y 1.0.")
    if not isinstance(resolucion, int) or not (4 <= resolucion <= 100):
        raise ValueError("La resolución debe ser un entero entre 4 y 100.")
    paso = (2 * math.pi) / resolucion
    vertices = []
    for i in range(resolucion):
        u = i * paso
        for j in range(resolucion):
            v = j * paso
            d = vertice_dona(u, v)
            c = vertice_taza(u, v)
            px = round((1.0 - t) * d[0] + t * c[0], 4)
            py = round((1.0 - t) * d[1] + t * c[1], 4)
            pz = round((1.0 - t) * d[2] + t * c[2], 4)
            vertices.append([px, py, pz])
    return vertices

