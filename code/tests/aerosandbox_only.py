import os
from pathlib import Path
import csv
import glob

from Airfoil_Generator import Airfoil

try:
    import aerosandbox as asb
    import aerosandbox.numpy as np
    from aerosandbox.aerodynamics.aero_2D import xfoil as asb_xfoil
except ImportError:
    asb = None
    np = None
    asb_xfoil = None

# --- Configuración editable ---
ESPESORES = [0.06, 0.12, 0.15, 0.18, 0.21, 0.24, 0.30, 0.36]
CUERDAS = [1.0, 0.5, 0.25, 0.1, 2.0, 3.0, 4.0, 5.0, 0.75]
AOA_LIST = [0.0, 2.0, 4.0]
MACH_LIST = [0.1, 0.15, 0.5, 0.7]
RE_LIST = [1e5, 5e6]
NORMALIZE = False
DAT_DIR = "generated_profiles"
CSV_PATH = "aerosandbox_results/summary.csv"
USE_EXISTING_DAT = False  # Si True, lee todos los .dat en DAT_DIR y no genera NACA nuevos
RUN_NEURALFOIL = True     # Ejecutar modelo NeuralFoil
RUN_XFOIL = False         # Ejecutar modelo XFOIL integrado en AeroSandbox
import os

# Ruta a xfoil: usa env XFOIL_COMMAND o asume que está en PATH
XFOIL_COMMAND = os.environ.get(
    "XFOIL_COMMAND",
    "xfoil.exe"
)  # se puede ajustar exportando XFOIL_COMMAND en cada máquina
# --- Fin configuración editable ---


def generate_airfoils(t_list, c_list, normalize=True, output_folder="generated_profiles"):
    os.makedirs(output_folder, exist_ok=True)
    airfoil_dict = {}
    for t_rel in t_list:
        for c in c_list:
            foil = Airfoil.naca00xx(t_rel=t_rel, c=c, normalize=normalize)
            thickness_str = f"{int(t_rel * 100):02d}"
            key = f"NACA00{thickness_str}_c{c:.1f}m" + ("_nd" if normalize else "")
            filename = f"{key}.dat"
            filepath = os.path.join(output_folder, filename)
            foil.save_dat(filepath, non_dim=normalize)
            airfoil_dict[key] = {"foil": foil, "dat": filepath}
            print(f"[OK] Generado: {filepath}")
    return airfoil_dict


def collect_dat_files(folder):
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"No existe la carpeta {folder_path}")
    files = sorted(glob.glob(str(folder_path / "*.dat")))
    if not files:
        raise FileNotFoundError(f"No se encontraron .dat en {folder_path}")
    out = {}
    for f in files:
        key = Path(f).stem
        out[key] = {"foil": None, "dat": f}
    print(f"[INFO] Encontrados {len(out)} perfiles .dat en {folder_path}")
    return out


def run_aerosandbox(dat_path, alpha_list, Re, mach):
    if asb is None:
        raise RuntimeError("Aerosandbox no está instalado. Instala con 'pip install aerosandbox'.")
    try:
        coords = np.loadtxt(dat_path)
    except Exception:
        coords = np.loadtxt(dat_path, skiprows=1)
    airfoil = asb.Airfoil(name=Path(dat_path).stem, coordinates=coords)
    rows = []
    for alpha in alpha_list:
        if RUN_NEURALFOIL:
            nf_fn = getattr(airfoil, "get_aero_from_neuralfoil", None)
            if nf_fn is None:
                raise AttributeError("Esta versión de aerosandbox no tiene get_aero_from_neuralfoil.")
            aero_nf = nf_fn(alpha=alpha, Re=Re, mach=mach, n_crit=9.0, include_360_deg_effects=True)
            cl = np.array(aero_nf["CL"]).item() if np is not None else float(aero_nf["CL"])
            cd = np.array(aero_nf["CD"]).item() if np is not None else float(aero_nf["CD"])
            cm_val = aero_nf.get("CM", aero_nf.get("CMm", 0.0))
            cm = np.array(cm_val).item() if np is not None else float(cm_val)
            row_nf = {
                "solver": "neuralfoil",
                "airfoil": Path(dat_path).stem,
                "alpha": alpha,
                "Re": Re,
                "mach": mach,
                "CL": float(cl),
                "CD": float(cd),
                "CM": float(cm)
            }
            rows.append(row_nf)
            print(f"[NeuralFoil] {row_nf['airfoil']} AoA={alpha}° -> CL={row_nf['CL']:.5f} CD={row_nf['CD']:.6f} CM={row_nf['CM']:.5f}")

        if RUN_XFOIL:
            try:
                xf_fn = getattr(airfoil, "get_aero_from_xfoil", None)
                if xf_fn is not None:
                    aero_xf = xf_fn(alpha=alpha, Re=Re, mach=mach, n_crit=9.0, max_iter=200, xfoil_command=XFOIL_COMMAND)
                elif asb_xfoil is not None and hasattr(asb_xfoil, "XFoil"):
                    xf = asb_xfoil.XFoil(
                        airfoil=airfoil,
                        Re=Re,
                        mach=mach,
                        n_crit=9.0,
                        max_iter=200,
                        xfoil_command=XFOIL_COMMAND,
                        verbose=False,
                    )
                    xf_out = xf.alpha(alpha)
                    if xf_out and "CL" in xf_out and len(xf_out["CL"]) > 0:
                        # Buscar el índice cuyo alpha esté más cerca del solicitado
                        import numpy as _np
                        a_arr = _np.array(xf_out["alpha"])
                        idx = int(_np.argmin(_np.abs(a_arr - alpha)))
                        aero_xf = {
                            "CL": xf_out["CL"][idx],
                            "CD": xf_out["CD"][idx],
                            "CM": xf_out.get("CM", xf_out.get("CMm", 0.0))[idx],
                        }
                    else:
                        raise RuntimeError("XFoil no devolvió datos")
                else:
                    print("[WARN] XFOIL no disponible (sin get_aero_from_xfoil ni clase XFoil).")
                    continue
                clx = np.array(aero_xf["CL"]).item() if np is not None else float(aero_xf["CL"])
                cdx = np.array(aero_xf["CD"]).item() if np is not None else float(aero_xf["CD"])
                cmx_val = aero_xf.get("CM", aero_xf.get("CMm", 0.0))
                cmx = np.array(cmx_val).item() if np is not None else float(cmx_val)
                row_xf = {
                    "solver": "aerosandbox-xfoil",
                    "airfoil": Path(dat_path).stem,
                    "alpha": alpha,
                    "Re": Re,
                    "mach": mach,
                    "CL": float(clx),
                    "CD": float(cdx),
                    "CM": float(cmx)
                }
                rows.append(row_xf)
                print(f"[XFOIL] {row_xf['airfoil']} AoA={alpha}° -> CL={row_xf['CL']:.5f} CD={row_xf['CD']:.6f} CM={row_xf['CM']:.5f}")
            except Exception as e:
                print(f"[WARN] XFOIL falló para {Path(dat_path).name} AoA={alpha}: {e}")
    return rows


def export_csv(rows, out_path):
    if not rows:
        print("[CSV] No hay datos para exportar.")
        return
    os.makedirs(Path(out_path).parent, exist_ok=True)
    fieldnames = ["solver", "airfoil", "alpha", "Re", "mach", "CL", "CD", "CM"]
    target = Path(out_path)
    with open(target, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"[CSV] Exportado a {target}")


if __name__ == "__main__":
    os.environ["PATH"] = str(Path(XFOIL_COMMAND).parent) + os.pathsep + os.environ.get("PATH", "")
    os.makedirs(Path(CSV_PATH).parent, exist_ok=True)
    os.makedirs(DAT_DIR, exist_ok=True)

    if USE_EXISTING_DAT:
        profiles = collect_dat_files(DAT_DIR)
    else:
        profiles = generate_airfoils(ESPESORES, CUERDAS, normalize=NORMALIZE, output_folder=DAT_DIR)

    all_rows = []
    for _, info in profiles.items():
        for Re in RE_LIST:
            for mach in MACH_LIST:
                all_rows.extend(run_aerosandbox(info["dat"], AOA_LIST, Re, mach))

    export_csv(all_rows, CSV_PATH)
