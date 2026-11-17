import csv
import math
import os
import shutil

OUTPUT_DIR = "modelos_3d"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Toroide / Dona
# Copiar el modelo existente o regenerar con los mismos parámetros
if os.path.exists("modelo_3d.csv"):
    shutil.copy("modelo_3d.csv", os.path.join(OUTPUT_DIR, "dona.csv"))
    shutil.copy("modelo_3d.csv", os.path.join(OUTPUT_DIR, "toroide.csv"))
    shutil.copy("modelo_3d.csv", os.path.join(OUTPUT_DIR, "modelo_3d.csv"))
    print("Dona copiada con éxito desde modelo_3d.csv")
else:
    R = 10.0
    r = 5.0
    theta_steps = 100
    phi_steps = 100
    with open(os.path.join(OUTPUT_DIR, "dona.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "z"])
        for i in range(theta_steps):
            theta = i * 2 * math.pi / theta_steps
            for j in range(phi_steps):
                phi = j * 2 * math.pi / phi_steps
                x = (R + r * math.cos(phi)) * math.cos(theta)
                y = (R + r * math.cos(phi)) * math.sin(theta)
                z = r * math.sin(phi)
                writer.writerow([round(x, 4), round(y, 4), round(z, 4)])

# 2. Esfera
R_esfera = 10.0
lat_steps = 100  # Latitud (polo norte a sur)
lon_steps = 100  # Longitud (vuelta completa)

esfera_path = os.path.join(OUTPUT_DIR, "esfera.csv")
with open(esfera_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y", "z"])
    for i in range(lat_steps):
        phi = (i + 0.5) * math.pi / lat_steps  # Evitar singularidad exacta en polos
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        for j in range(lon_steps):
            theta = j * 2 * math.pi / lon_steps
            x = R_esfera * sin_phi * math.cos(theta)
            y = R_esfera * cos_phi
            z = R_esfera * sin_phi * math.sin(theta)
            writer.writerow([round(x, 4), round(y, 4), round(z, 4)])

print(f"Esfera generada con éxito ({lat_steps * lon_steps} puntos) en {esfera_path}")

# 3. Pirámide (Base cuadrada de 16x16, altura 16, centrada en el origen)
# Vértice superior (Ápice): (0, 8, 0)
# Base en y = -8 con esquinas en (+-8, -8, +-8)
piramide_path = os.path.join(OUTPUT_DIR, "piramide.csv")
puntos_piramide = []

# Muestreo de las 4 caras laterales triangulares
# Hacemos 65 niveles horizontales desde el ápice (y=8) hasta la base (y=-8)
levels = 65
for l in range(levels + 1):
    t = l / levels  # 0 en el ápice, 1 en la base
    y = 8.0 - t * 16.0
    half_w = 8.0 * t
    if half_w == 0:
        puntos_piramide.append([0.0, round(y, 4), 0.0])
        continue
    
    # Perímetro en este nivel t: 4 lados
    # Cantidad de puntos por lado proporcional a t
    pts_per_side = max(1, int(t * 35))
    
    # Lado 1: (-half_w, y, -half_w) a (half_w, y, -half_w)
    for s in range(pts_per_side):
        f = s / pts_per_side
        x = -half_w + f * (2 * half_w)
        z = -half_w
        puntos_piramide.append([round(x, 4), round(y, 4), round(z, 4)])
    # Lado 2: (half_w, y, -half_w) a (half_w, y, half_w)
    for s in range(pts_per_side):
        f = s / pts_per_side
        x = half_w
        z = -half_w + f * (2 * half_w)
        puntos_piramide.append([round(x, 4), round(y, 4), round(z, 4)])
    # Lado 3: (half_w, y, half_w) a (-half_w, y, half_w)
    for s in range(pts_per_side):
        f = s / pts_per_side
        x = half_w - f * (2 * half_w)
        z = half_w
        puntos_piramide.append([round(x, 4), round(y, 4), round(z, 4)])
    # Lado 4: (-half_w, y, half_w) a (-half_w, y, -half_w)
    for s in range(pts_per_side):
        f = s / pts_per_side
        x = -half_w
        z = half_w - f * (2 * half_w)
        puntos_piramide.append([round(x, 4), round(y, 4), round(z, 4)])

# Muestreo de la base inferior (y = -8)
base_grid = 45
for i in range(base_grid):
    x = -8.0 + (i / (base_grid - 1)) * 16.0
    for j in range(base_grid):
        z = -8.0 + (j / (base_grid - 1)) * 16.0
        puntos_piramide.append([round(x, 4), -8.0, round(z, 4)])

with open(piramide_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y", "z"])
    for pt in puntos_piramide:
        writer.writerow(pt)

print(f"Pirámide generada con éxito ({len(puntos_piramide)} puntos) en {piramide_path}")
