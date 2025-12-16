import numpy as np
import matplotlib.pyplot as plt

pts = np.loadtxt("NACA0012.dat")

plt.figure(figsize=(8,4))
plt.plot(pts[:,0], pts[:,1], "-o", markersize=2)
plt.axis("equal")
plt.grid(True)
plt.show()

print("Primero:", pts[0])
print("Último :", pts[-1])
print("Distancia entre primero y último:", np.linalg.norm(pts[0] - pts[-1]))
