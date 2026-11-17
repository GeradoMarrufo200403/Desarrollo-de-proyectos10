import math
import csv

R = 10.0  # Radio principal (distancia del centro al centro del tubo)
r = 5.0   # Radio del tubo (grosor de la dona)
theta_steps = 100  # Resolución a lo largo del anillo principal
phi_steps = 100    # Resolución a lo largo del tubo

with open('modelo_3d.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['x', 'y', 'z'])
    
    for i in range(theta_steps):
        theta = i * 2 * math.pi / theta_steps
        for j in range(phi_steps):
            phi = j * 2 * math.pi / phi_steps
            
            # Ecuaciones paramétricas del Toroide
            x = (R + r * math.cos(phi)) * math.cos(theta)
            y = (R + r * math.cos(phi)) * math.sin(theta)
            z = r * math.sin(phi)
            
            # Redondear a 4 decimales para optimizar tamaño
            writer.writerow([round(x, 4), round(y, 4), round(z, 4)])

print("Toroide de alta resolución generado con éxito en modelo_3d.csv")
