import subprocess
import sys
from pathlib import Path

# --- Config editable ---
AOA_LIST = [0.0]
MACH_LIST = [0.32]
RE_LIST = [37178444, 33681989]
MAX_ITER = 1000
CFL = None  # e.g. 2.0
MESH_FILE = None  # e.g. "meshes/n0012_897-257.su2"
RETRIES = 0
COMPRESSIBLE = False
SKIP_SU2 = True
SKIP_AEROSB = True
EXPORT_CSV = "results/combined_results.csv"
PROFILE_TYPES = ["rotodomo"]  # opciones: naca,naca_antenna,rotodomo,bezier,all
PROFILES_OUTPUT = "generated_profiles"
SAVE_PROFILE_PLOTS = True
T_LIST = [0.06]  # espesor relativo (0.06 -> 6%) para NACA 00xx normal
C_LIST = [1.0]   # cuerda en metros para NACA 00xx normal
NORMALIZE_PROFILES = False
ANTENNA_LENGTH = 4.5
ANTENNA_HEIGHT = 0.3
NACA_ANT_C_RANGE = (4.6, 10.0, 0.5)
NACA_ANT_T_RANGE = (0.02, 0.5)
NACA_ANT_POSITIONS = 10
ROTODO_C_RANGE = (4.6, 10.0, 0.1)
ROTODO_T_RANGE = (0.05, 0.45)
BEZ_C_RANGE = (6.0, 7.3, 0.1)
BEZ_T_RANGE = (0.05, 0.55)
BEZ_SHARPNESS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
RUN_COMPARISON = True
COMPARISON_METRIC = "cd_mean"  # cd_mean, cd_min, cl_mean, clcd_mean, clcd_max
COMPARISON_SOLVER = None  # e.g. "su2-incomp" o "aerosandbox-neuralfoil"
COMPARISON_AOA_MIN = None
COMPARISON_AOA_MAX = None
COMPARISON_OUTPUT = "results/airfoil_rankings.csv"
PLOT_COMPARISON = True
PLOT_DIR = None  # usa default si None
PLOT_TOP_N = 20
# --- Fin config editable ---


def build_cmd():
    cmd = [
        sys.executable,
        "main.py",
        "--aoa-list",
        ",".join(str(a) for a in AOA_LIST),
        "--mach-list",
        ",".join(str(m) for m in MACH_LIST),
        "--Re-list",
        ",".join(str(r) for r in RE_LIST),
        "--max-iter",
        str(MAX_ITER),
        "--export-csv",
        EXPORT_CSV,
        "--profile-types",
        ",".join(PROFILE_TYPES),
        "--profiles-output",
        PROFILES_OUTPUT,
        "--t-list",
        ",".join(str(t) for t in T_LIST),
        "--c-list",
        ",".join(str(c) for c in C_LIST),
        "--antenna-length",
        str(ANTENNA_LENGTH),
        "--antenna-height",
        str(ANTENNA_HEIGHT),
        "--naca-ant-c-start",
        str(NACA_ANT_C_RANGE[0]),
        "--naca-ant-c-end",
        str(NACA_ANT_C_RANGE[1]),
        "--naca-ant-c-step",
        str(NACA_ANT_C_RANGE[2]),
        "--naca-ant-t-min",
        str(NACA_ANT_T_RANGE[0]),
        "--naca-ant-t-max",
        str(NACA_ANT_T_RANGE[1]),
        "--naca-ant-pos-count",
        str(NACA_ANT_POSITIONS),
        "--rotodomo-c-start",
        str(ROTODO_C_RANGE[0]),
        "--rotodomo-c-end",
        str(ROTODO_C_RANGE[1]),
        "--rotodomo-c-step",
        str(ROTODO_C_RANGE[2]),
        "--rotodomo-t-min",
        str(ROTODO_T_RANGE[0]),
        "--rotodomo-t-max",
        str(ROTODO_T_RANGE[1]),
        "--bezier-c-start",
        str(BEZ_C_RANGE[0]),
        "--bezier-c-end",
        str(BEZ_C_RANGE[1]),
        "--bezier-c-step",
        str(BEZ_C_RANGE[2]),
        "--bezier-t-min",
        str(BEZ_T_RANGE[0]),
        "--bezier-t-max",
        str(BEZ_T_RANGE[1]),
        "--bezier-sharpness",
        ",".join(str(s) for s in BEZ_SHARPNESS),
    ]
    if RUN_COMPARISON:
        cmd.append("--run-comparison")
        cmd += [
            "--comparison-metric",
            COMPARISON_METRIC,
            "--comparison-output",
            COMPARISON_OUTPUT,
            "--plot-top-n",
            str(PLOT_TOP_N),
        ]
        if COMPARISON_SOLVER:
            cmd += ["--comparison-solver", COMPARISON_SOLVER]
        if COMPARISON_AOA_MIN is not None:
            cmd += ["--comparison-aoa-min", str(COMPARISON_AOA_MIN)]
        if COMPARISON_AOA_MAX is not None:
            cmd += ["--comparison-aoa-max", str(COMPARISON_AOA_MAX)]
        if PLOT_COMPARISON:
            cmd.append("--plot-comparison")
        if PLOT_DIR:
            cmd += ["--plot-dir", PLOT_DIR]
    if CFL is not None:
        cmd += ["--cfl", str(CFL)]
    if MESH_FILE:
        cmd += ["--mesh-file", MESH_FILE]
    if COMPRESSIBLE:
        cmd.append("--compressible")
    if SKIP_SU2:
        cmd.append("--skip-su2")
    if SKIP_AEROSB:
        cmd.append("--skip-aerosb")
    if RETRIES:
        cmd += ["--retries", str(RETRIES)]
    if NORMALIZE_PROFILES:
        cmd.append("--normalize-profiles")
    if SAVE_PROFILE_PLOTS:
        cmd.append("--save-profile-plots")
    return cmd


def main():
    cmd = build_cmd()
    print("[RUN] " + " ".join(cmd))
    res = subprocess.run(cmd, cwd=Path(__file__).parent)
    if res.returncode != 0:
        raise SystemExit(res.returncode)


if __name__ == "__main__":
    main()
