import os
import shutil
import numpy as np
import subprocess


def _resolve_gmsh():
    """
    Devuelve el comando gmsh a usar:
    1) Variable de entorno GMSH_CMD
    2) gmsh/gmsh.bat en PATH
    3) Rutas típicas de Windows (Program Files o Scripts de Python)
    """
    env_cmd = os.environ.get("GMSH_CMD")
    if env_cmd:
        return env_cmd
    for candidate in ("gmsh", "gmsh.exe", "gmsh.bat"):
        path = shutil.which(candidate)
        if path:
            return path
    win_candidates = [
        r"C:\Program Files\gmsh\gmsh.exe",
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python312", "Scripts",
                     "gmsh.bat"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python312", "Scripts",
                     "gmsh"),
    ]
    for p in win_candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No se encontró gmsh. Define la variable GMSH_CMD o añade gmsh al PATH.")


GMSH_CMD = _resolve_gmsh()


# ============================================================
# 1. LOAD DAT FILE
# ============================================================

def load_airfoil_points(dat_file):
    """
    Carga puntos desde .dat ignorando cabecera si la hay.
    """
    try:
        return np.loadtxt(dat_file)
    except Exception:
        return np.loadtxt(dat_file, skiprows=1)


# ============================================================
# 2. FIX TRAILING EDGE (TE)
# ============================================================

def fix_trailing_edge(pts):
    """
    Deja exactamente dos puntos en el borde de salida:
    Colapsa el borde de salida a un único punto medio para evitar
    auto-intersecciones o segmentos degenerados en Gmsh.
    """
    xmax = np.max(pts[:, 0])
    te_mask = np.abs(pts[:, 0] - xmax) < 1e-8
    te_pts = pts[te_mask]
    middle = pts[~te_mask]

    # Punto medio del TE (cierra en un solo nodo)
    te_avg = te_pts.mean(axis=0)

    return np.vstack([te_avg, middle, te_avg])


# ============================================================
# 3. ORDER AIRFOIL FOR GMSH
# ============================================================

def clean_and_order_airfoil(pts):
    """
    Convierte el conjunto de puntos en un loop valido:
    TE -> upper -> LE -> lower -> TE
    """

    # eliminar duplicados manteniendo el orden de aparicion
    _, idx = np.unique(np.round(pts, 6), axis=0, return_index=True)
    pts = pts[np.sort(idx)]

    # Si el perfil es simétrico (tenemos puntos con y>0 y y<0), ordenar por x
    upper = pts[pts[:, 1] >= 0]
    lower = pts[pts[:, 1] < 0]
    if len(upper) > 0 and len(lower) > 0:
        upper = upper[np.argsort(-upper[:, 0])]  # TE->LE
        lower = lower[np.argsort(lower[:, 0])]   # LE->TE
        ordered = np.vstack([upper, lower])
    else:
        # localizar TE (x max) y LE (x min)
        i_te = np.argmax(pts[:, 0])
        pts = np.roll(pts, -i_te, axis=0)
        i_le = np.argmin(pts[:, 0])
        upper = pts[: i_le + 1]
        lower = pts[i_le:]
        if upper.shape[0] > 1 and upper[0, 0] < upper[-1, 0]:
            upper = upper[::-1]
        if lower.shape[0] > 1 and lower[0, 0] > lower[-1, 0]:
            lower = lower[::-1]
        ordered = np.vstack([upper, lower])

    # cerrar loop exacto
    if np.linalg.norm(ordered[0] - ordered[-1]) > 1e-12:
        ordered = np.vstack([ordered, ordered[0]])

    # eliminar duplicados consecutivos (evita segmentos de longitud cero)
    diffs = np.linalg.norm(np.diff(ordered, axis=0), axis=1)
    keep = np.hstack([[True], diffs > 1e-12])
    ordered = ordered[keep]

    return ordered


# ============================================================
# 4. GENERATE .GEO FILE
# ============================================================

def write_geo(pts, geo_file, mesh_file):
    """
    Crea el archivo .geo que Gmsh usara para generar el mallado.
    """

    pts = np.asarray(pts)

    # si el ultimo punto coincide con el primero, evitar duplicarlo como nodo nuevo
    if np.linalg.norm(pts[0] - pts[-1]) < 1e-12:
        pts = pts[:-1]

    with open(geo_file, "w") as f:
        f.write("// ============ AIRFOIL GEOMETRY ============\n")

        # puntos del perfil
        for i, (x, y) in enumerate(pts):
            f.write(f"Point({i+1}) = {{{x}, {y}, 0, 0.01}};\n")

        # spline del perfil (cerrando explicitamente sobre el primer nodo)
        indices_list = [str(i + 1) for i in range(len(pts))]
        indices_list.append("1")
        indices = ",".join(indices_list)
        f.write(f"Spline(1) = {{{indices}}};\n")

        # dominio exterior (farfield a 20c)
        f.write("Point(1001) = {-20, -20, 0, 3.0};\n")
        f.write("Point(1002) = { 20, -20, 0, 3.0};\n")
        f.write("Point(1003) = { 20,  20, 0, 3.0};\n")
        f.write("Point(1004) = {-20,  20, 0, 3.0};\n")

        # control global de tamano de elemento (refinado cerca del perfil)
        f.write("Mesh.CharacteristicLengthMin = 5e-5;\n")
        f.write("Mesh.CharacteristicLengthMax = 3.0;\n")

        f.write("Line(1001) = {1001, 1002};\n")
        f.write("Line(1002) = {1002, 1003};\n")
        f.write("Line(1003) = {1003, 1004};\n")
        f.write("Line(1004) = {1004, 1001};\n")

        # loops
        f.write("Curve Loop(1) = {1};\n")
        f.write("Curve Loop(2) = {1001, 1002, 1003, 1004};\n")

        # superficie externa agujereando el airfoil
        f.write("Plane Surface(10) = {2,1};\n")
        f.write("Recombine Surface {10};\n")

        # grupos fisicos para que SU2 identifique las fronteras
        f.write('Physical Surface("fluid") = {10};\n')
        f.write('Physical Curve("farfield") = {1001, 1002, 1003, 1004};\n')
        f.write('Physical Curve("airfoil") = {1};\n')

        # campo de capa limite alrededor del airfoil (malla cuadriculada)
        f.write("Field[1] = BoundaryLayer;\n")
        f.write("Field[1].EdgesList = {1};\n")
        f.write("Field[1].hwall_n = 5e-5;\n")
        f.write("Field[1].thickness = 0.2;\n")
        f.write("Field[1].ratio = 1.15;\n")
        f.write("Field[1].Quads = 1;\n")
        f.write("Field[1].IntersectMetrics = 1;\n")
        f.write("Field[2] = Distance;\n")
        f.write("Field[2].EdgesList = {1};\n")
        f.write("Field[3] = Threshold;\n")
        f.write("Field[3].IField = 2;\n")
        f.write("Field[3].LcMin = 0.005;\n")
        f.write("Field[3].LcMax = 2.0;\n")
        f.write("Field[3].DistMin = 0.2;\n")
        f.write("Field[3].DistMax = 5.0;\n")
        f.write("Background Field = 3;\n")


# ============================================================
# 5. GENERATE SU2 MESH
# ============================================================

def generate_su2_mesh(dat_file, mesh_file="NACA0012.su2"):
    """
    Paso completo: cargar, reparar, ordenar y mallar.
    """

    # 1. cargar .dat
    pts = load_airfoil_points(dat_file)

    # 2. limpiar borde de salida
    pts = fix_trailing_edge(pts)

    # 3. ordenar para Gmsh
    pts = clean_and_order_airfoil(pts)

    # 4. escribir geo
    geo_file = "temp.geo"
    write_geo(pts, geo_file, mesh_file)

    # 5. ejecutar Gmsh
    print("[INFO] Ejecutando Gmsh...")
    subprocess.run([GMSH_CMD, geo_file, "-2", "-o", mesh_file, "-format", "su2"], check=False)

    print(f"[OK] Malla SU2 generada: {mesh_file}")


# ============================================================
# 6. SOLO PARA DEBUG DIRECTO
# ============================================================

if __name__ == "__main__":
    generate_su2_mesh("NACA0012.dat")
