import numpy as np

# cargar archivo ignorando cabecera textual
pts = np.loadtxt("NACA0012.dat", skiprows=1)

xmax = np.max(pts[:,0])

idx = np.where(abs(pts[:,0] - xmax) < 1e-8)[0]

print("Número de puntos con x = xmax:", len(idx))
print("Índices:", idx.tolist())

print("\nPuntos TE encontrados:")
for i in idx:
    print(pts[i])
