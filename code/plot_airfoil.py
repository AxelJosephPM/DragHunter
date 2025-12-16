import numpy as np
import matplotlib.pyplot as plt

# Carga que ignora líneas que no son datos
pts = np.loadtxt("NACA0012.dat", comments="N", skiprows=1)

print("Primero:", pts[0])
print("Último :", pts[-1])
print("Distancia TE:", np.linalg.norm(pts[0] - pts[-1]))

plt.figure(figsize=(12,4))
plt.plot(pts[:,0], pts[:,1], "-o", markersize=3)
plt.title("Perfil leído desde NACA0012.dat")
plt.axis("equal")
plt.grid(True)
plt.show()
