import subprocess
import os
import shutil
import time

def run_xfoil(airfoil_file, alpha, Re=1e6, Mach=0.1, iter_max=200):

    # Ruta de XFOIL
    xfoil_path = r"C:\Users\lo1mo\Documents\3ro\Aerodinamica\Trabajo\code\xfoil.exe"
    xfoil_dir = os.path.dirname(xfoil_path)

    # Copiar el .dat al directorio de XFOIL
    airfoil_name = os.path.basename(airfoil_file)
    airfoil_local = os.path.join(xfoil_dir, airfoil_name)
    shutil.copyfile(airfoil_file, airfoil_local)

    # Archivos de salida
    polar_file = os.path.join(xfoil_dir, "polar_tmp.txt")
    if os.path.exists(polar_file):
        os.remove(polar_file)

    # Script de comandos
    cmds = [
        f"LOAD {airfoil_name}",
        "PANE",
        "OPER",
        f"VISC {Re}",
        f"MACH {Mach}",
        f"ITER {iter_max}",
        "PACC",
        "polar_tmp.txt",
        "",
        f"ALFA {alpha}",
        "PACC",
        "",
        "QUIT"
    ]

    # Lanzar XFOIL por stdin
    p = subprocess.Popen(
        [xfoil_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=xfoil_dir
    )

    for c in cmds:
        p.stdin.write(c + "\n")
        p.stdin.flush()
        time.sleep(0.05)

    p.stdin.close()
    out, err = p.communicate(timeout=10)

    # Borrar copia del .dat
    if os.path.exists(airfoil_local):
        os.remove(airfoil_local)

    # Procesar polar
    if not os.path.exists(polar_file):
        print("Polar no generado.")
        print(out)
        print(err)
        return None

    return parse_polar(polar_file)

def parse_polar(pf):
    with open(pf, "r") as f:
        for line in f:
            parts = line.split()

            # Saltar líneas vacías o muy cortas
            if len(parts) < 6:
                continue

            # Saltar líneas no-numéricas
            try:
                float(parts[0])   # alpha
                float(parts[1])   # CL
                float(parts[2])   # CD
                float(parts[4])   # CM
            except:
                continue

            # Si pasa, es una línea de datos REAL
            CL = float(parts[1])
            CD = float(parts[2])
            CM = float(parts[4])
            return CL, CD, CM

    return None
