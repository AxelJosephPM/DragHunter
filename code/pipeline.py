import os
from pathlib import Path
from Airfoil_Generator import Airfoil
from mesh_generator import generate_su2_mesh
from su2_runner import run_su2
from datetime import datetime
import csv

# ------------------------------
# CONFIGURACION DEL PIPELINE
# ------------------------------

NACA = "0012"
AOA = 0.0
MACH = 0.15
RE = 1e6

BASE_DIR = Path(__file__).resolve().parent
# Plantillas de SU2 dentro del propio repo (code/config)
CONFIG_DIR = BASE_DIR / "config"
CFG_INVISCID = str(CONFIG_DIR / "su2_template_inv.cfg")
CFG_VISCOUS = str(CONFIG_DIR / "su2_template_rans.cfg")
# Plantilla incomprensible (solo se usa si se solicita)
CFG_INCOMP = str(CONFIG_DIR / "su2_template_inc.cfg")

DAT_OUT = f"NACA{NACA}.dat"
MESH_DIR = "meshes"
RESULTS_DIR = "results"
SU2_RESULTS_DIR = f"{RESULTS_DIR}/su2"
MESH_OUT = f"{MESH_DIR}/airfoil_mesh.su2"


def main():
    # ------------------------------
    # 1. GENERAR PERFIL
    # ------------------------------
    print("\n[1] Generando perfil airfoil...")

    t_rel = int(NACA[-2:]) / 100.0  # grosor relativo 00xx -> xx/100
    foil = Airfoil.naca00xx(t_rel=t_rel, c=1.0, normalize=True)
    foil.save_dat(DAT_OUT, non_dim=True)

    if not os.path.exists(DAT_OUT):
        print("[ERROR] No se genero el archivo .dat")
        return

    print(f"[OK] Perfil generado: {DAT_OUT}")

    # ------------------------------
    # 2. GENERAR MALLA
    # ------------------------------
    print("\n[2] Generando malla SU2...")

    # confirmar que existen plantillas antes de gastar tiempo
    for cfg in (CFG_INVISCID, CFG_VISCOUS):
        if not os.path.exists(cfg):
            print(f"[ERROR] No se encontró la plantilla: {cfg}")
            return

    # ensure output directories exist
    os.makedirs(MESH_DIR, exist_ok=True)
    os.makedirs(SU2_RESULTS_DIR, exist_ok=True)

    generate_su2_mesh(DAT_OUT, MESH_OUT)

    if not os.path.exists(MESH_OUT):
        print("[ERROR] No se genero la malla SU2")
        return

    print(f"[OK] Malla generada: {MESH_OUT}")

    # ------------------------------
    # 3. PRIMERA SIMULACION (INVISCID)
    # ------------------------------
    print("\n[3] Ejecutando SU2 (INVISCID)...")

    sup_max_iter = None
    if os.environ.get("SU2_MAX_ITER"):
        try:
            sup_max_iter = int(os.environ.get("SU2_MAX_ITER"))
        except Exception:
            sup_max_iter = None

    inv_out_dir = os.path.join(SU2_RESULTS_DIR, "inviscid")
    os.makedirs(inv_out_dir, exist_ok=True)

    result_inv = run_su2(
        mesh_file=MESH_OUT,
        cfg_template=CFG_INVISCID,
        aoa=AOA,
        mach=MACH,
        Re=RE,
        viscous=False,
        max_iter=sup_max_iter,
        output_dir=inv_out_dir,
    )

    if result_inv is None:
        print("[ERROR] Fallo la simulacion inviscida")
    else:
        cli, cdi, cmi = result_inv[0], result_inv[1], result_inv[2]
        print(f"[OK] Inviscid -> CL={cli:.4f}, CD={cdi:.5f}, CM={cmi:.5f}")

    # ------------------------------
    # 4. SEGUNDA SIMULACION (RANS / VISCOSA)
    # ------------------------------
    print("\n[4] Ejecutando SU2 (VISCOSO / RANS)...")

    visc_out_dir = os.path.join(SU2_RESULTS_DIR, "viscous")
    os.makedirs(visc_out_dir, exist_ok=True)

    result_visc = run_su2(
        mesh_file=MESH_OUT,
        cfg_template=CFG_VISCOUS,
        aoa=AOA,
        mach=MACH,
        Re=RE,
        viscous=True,
        max_iter=sup_max_iter,
        output_dir=visc_out_dir,
    )

    if result_visc is None:
        print("[ERROR] Fallo la simulacion viscosa")
    else:
        clv, cdv, cmv = result_visc[0], result_visc[1], result_visc[2]
        print(f"[OK] Viscous -> CL={clv:.4f}, CD={cdv:.5f}, CM={cmv:.5f}")

    print("\n>>> PIPELINE COMPLETADO <<<\n")


if __name__ == "__main__":
    main()


def run_case(dat_file: str, case_name: str, aoa: float = AOA, mach: float = MACH, Re: float = RE, max_iter: int = None, retries: int = 1, strict: bool = False, cfl: float = None, incompressible: bool = False, mesh_override: str = None):
    """Run a full pipeline for a given DAT airfoil file and case name.
    This will produce a mesh under meshes/{case_name}/ and su2 results under results/su2/{case_name}/inviscid and /viscous
    Returns a dict with results for inviscid and viscous runs.
    """
    # mesh output inside a case subdirectory (overwrite if already exists)
    mesh_case_dir = Path(MESH_DIR) / case_name
    if mesh_case_dir.exists():
        # Remove previous mesh files so gmsh generates fresh output
        import shutil
        try:
            shutil.rmtree(mesh_case_dir)
        except Exception:
            pass
    os.makedirs(mesh_case_dir, exist_ok=True)
    mesh_out = str(mesh_case_dir / f"{case_name}_airfoil_mesh.su2")

    # results directories
    # results directories (overwrite contents if they exist)
    results_case_dir = Path(SU2_RESULTS_DIR) / case_name
    if results_case_dir.exists():
        import shutil
        try:
            shutil.rmtree(results_case_dir)
        except Exception:
            pass
    inv_out_dir = str(results_case_dir / "inviscid")
    visc_out_dir = str(results_case_dir / "viscous")
    os.makedirs(inv_out_dir, exist_ok=True)
    os.makedirs(visc_out_dir, exist_ok=True)

    # generate or reuse mesh for this case
    if mesh_override:
        # copiar la malla provista al directorio del caso
        import shutil
        if not os.path.exists(mesh_override):
            raise FileNotFoundError(f"Malla provista no existe: {mesh_override}")
        try:
            shutil.copy(mesh_override, mesh_out)
            print(f"[INFO] Usando malla provista: {mesh_override} -> {mesh_out}")
        except Exception as e:
            raise RuntimeError(f"No se pudo copiar la malla provista {mesh_override}: {e}")
    else:
        generate_su2_mesh(dat_file, mesh_out)

    if incompressible:
        # Solo una corrida incomprensible (usa plantilla INC)
        inv = None
        visc = run_su2(
            mesh_file=mesh_out,
            cfg_template=CFG_INCOMP,
            aoa=aoa,
            mach=mach,   # se ignora en INC, pero mantenemos firma
            Re=Re,       # se ignora en INC, pero mantenemos firma
            viscous=True,
            max_iter=max_iter,
            retries=retries,
            strict=strict,
            cfl=cfl,
            output_dir=visc_out_dir,
            incompressible=True,
        )
    else:
        # run inviscid (compresible)
        inv = run_su2(
            mesh_file=mesh_out,
            cfg_template=CFG_INVISCID,
            aoa=aoa,
            mach=mach,
            Re=Re,
            viscous=False,
            max_iter=max_iter,
            retries=retries,
            strict=strict,
            cfl=cfl,
            output_dir=inv_out_dir,
        )

        # run viscous (RANS compresible)
        visc = run_su2(
            mesh_file=mesh_out,
            cfg_template=CFG_VISCOUS,
            aoa=aoa,
            mach=mach,
            Re=Re,
            viscous=True,
            max_iter=max_iter,
            retries=retries,
            strict=strict,
            cfl=cfl,
            output_dir=visc_out_dir,
        )

    # record to summary CSV (overwrite previous entry for the same case)
    summary_file = Path(RESULTS_DIR) / "summary.csv"
    headers = [
        "timestamp", "case", "dat_file", "aoa", "mach", "Re",
        "CL_inv", "CD_inv", "CM_inv", "INV_converged", "INV_final_iter", "INV_final_rms",
        "CL_visc", "CD_visc", "CM_visc", "VIS_converged", "VIS_final_iter", "VIS_final_rms",
    ]
    row = [datetime.now().isoformat(), case_name, dat_file, aoa, mach, Re]
    if inv is None:
        row.extend([None, None, None, None, None, None])
    else:
        row.extend([inv[0], inv[1], inv[2]])
        # additional values if present
        if len(inv) >= 6:
            row.extend([inv[5], inv[3], inv[4]])
        else:
            row.extend([None, None, None])
    if visc is None:
        row.extend([None, None, None, None, None, None])
    else:
        row.extend([visc[0], visc[1], visc[2]])
        # additional values if present
        if len(visc) >= 6:
            row.extend([visc[5], visc[3], visc[4]])
        else:
            row.extend([None, None, None])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    write_header = not Path(summary_file).exists()
    # If the file exists, load it and remove previous entries for this case
    if Path(summary_file).exists():
        try:
            with open(summary_file, 'r', newline='') as csvr:
                reader = list(csv.reader(csvr))
            # split header and rows
            header = reader[0] if reader else headers
            rows = reader[1:] if len(reader) > 1 else []
            # remove any rows for this case (strip white-space for robustness)
            prev_rows = [r for r in rows if len(r) < 2 or r[1].strip() != case_name.strip()]
        except Exception:
            prev_rows = []
            header = headers
        with open(summary_file, 'w', newline='') as csvw:
            writer = csv.writer(csvw)
            # Always ensure header present when recreating the file
            writer.writerow(header)
            # write previous rows except ones for this case
            for r in prev_rows:
                writer.writerow(r)
            writer.writerow(row)
    else:
        with open(summary_file, 'a', newline='') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(headers)
            writer.writerow(row)

    return {"case": case_name, "inviscid": inv, "viscous": visc}


def generate_case_name(base_key: str, aoa: float, mach: float, Re: float, add_ts: bool = False):
    """Generate a filesystem-friendly case name with parameters and optional timestamp.
    Example: NACA0012_c1.0m_AoA2.0_M0.20_Re5000000_20251205_123456
    """
    key_safe = base_key.replace(' ', '_')
    name = f"{key_safe}_AoA{aoa:.1f}_M{mach:.2f}_Re{int(Re)}"
    if add_ts:
        name += "_" + datetime.now().strftime('%Y%m%d_%H%M%S')
    return name
