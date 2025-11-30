import os
import numpy as np
from xfoil_runner import run_xfoil

def main():
    # === CONFIGURACIÓN ===
    perfiles_dir = "C:\\Users\\lo1mo\\Documents\\3ro\\Aerodinamica\\Trabajo\\code\\generated_profiles"

    Re = 5e6
    Mach = 0.45
    alphas = [0]  # α que quieres analizar

    files = [f for f in os.listdir(perfiles_dir) if f.endswith(".dat")]

    print("\n=== ANALIZANDO PERFILES (XFOIL DIRECTO) ===\n")

    summary = []

    for f in files:
        filepath = os.path.join(perfiles_dir, f)

        print(f"\n---- {f} ----\n")

        for alpha in alphas:
            result = run_xfoil(filepath, alpha=alpha, Re=Re, Mach=Mach)

            if result is None:
                print(f"[WARN] No converge para α={alpha}°")
                continue

            CL, CD, CM = result
            print(f"α = {alpha:>4}°  →  CL={CL:.4f},  CD={CD:.5f},  CM={CM:.4f}")

            summary.append((f, alpha, CL, CD, CM))

    # Convertimos summary en array para análisis adicional si quieres
    summary = np.array(summary, dtype=object)

    # Mostrar resumen ordenado por CD global
    print("\n\n=== RESUMEN ORDENADO POR CD ===")
    ordenado = sorted(summary, key=lambda x: x[3])

    for entry in ordenado:
        f, alpha, CL, CD, CM = entry
        print(f"{f:25s}  α={alpha:>4}°  CD={CD:.5f}  CL={CL:.4f}  CM={CM:.4f}")

if __name__ == "__main__":
    main()
