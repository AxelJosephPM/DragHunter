import os
import numpy as np
from mesh_generator import generate_su2_mesh
from Airfoil_Generator import Airfoil


# ============================================================
# 1) Generar un perfil NACA 0012 .dat
# ============================================================

print("[TEST] Generando perfil NACA 0012...")
foil = Airfoil.naca00xx(t_rel=0.12, c=1.0, normalize=True)

dat_file = "NACA0012.dat"
foil.save_dat(dat_file, non_dim=True)

print(f"[OK] Archivo .dat generado correctamente: {dat_file}")

# ============================================================
# 2) Generar malla SU2
# ============================================================

mesh_file = "NACA0012.su2"
generate_su2_mesh(dat_file, mesh_file)

# ============================================================
# 3) Verificar existencia y tamaño del archivo
# ============================================================

print("\n[TEST] Comprobando archivo SU2...")

if not os.path.exists(mesh_file):
    print("[ERROR] El archivo de malla no existe.")
    exit()

size = os.path.getsize(mesh_file)
print(f"Tamaño del archivo: {size} bytes")

if size < 200:
    print("[WARN] Archivo SU2 demasiado pequeño: probablemente vacío.")
else:
    print("[OK] La malla SU2 parece tener contenido válido.")

# ============================================================
# 4) Mostrar las primeras líneas del archivo .su2
# ============================================================

print("\n[TEST] Primeras líneas del archivo SU2:\n")

with open(mesh_file, "r") as f:
    for _ in range(15):
        line = f.readline()
        if not line:
            break
        print(line.strip())

print("\n[TEST] Fin del test.")
