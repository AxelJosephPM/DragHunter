import argparse
import itertools
import json
import os
from pathlib import Path
import csv

from Airfoil_Generator import Airfoil
import pipeline
import su2_runner
import airfoil_comparison
import profile_generators

try:
    import aerosandbox as asb
    import aerosandbox.numpy as np
except ImportError:
    asb = None
    np = None


def _to_scalar(val):
    """Best-effort conversion of aerosandbox outputs (could be numpy arrays) to float."""
    try:
        if np is not None:
            # Flatten in case we get a 1-element array
            return float(np.asarray(val).reshape(-1)[0])
        return float(val)
    except Exception:
        try:
            return float(val.item())
        except Exception as e:
            raise TypeError(f"No se pudo convertir {val!r} a float") from e


def _parse_num_list(raw: str, default):
    """Parse comma-separated numeric strings, fall back to default on error/empty."""
    if not raw:
        return default
    try:
        vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
        return vals if vals else default
    except Exception:
        return default


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


def analyze_su2(airfoil_dict, aoa=0.0, mach=0.15, Re=1e6, max_iter=None, aoa_list=None, mach_list=None,
                Re_list=None, retries=0, strict=False, add_ts=False, cfl=None, incompressible=True, mesh_file=None):
    results = []
    aoa_list = aoa_list or [aoa]
    mach_list = mach_list or [mach]
    Re_list = Re_list or [Re]
    for key, info in airfoil_dict.items():
        dat_path = info["dat"]
        for a, m, r in itertools.product(aoa_list, mach_list, Re_list):
            case_name = pipeline.generate_case_name(key, a, m, r, add_ts=add_ts)
            print(f"\n[SU2] {case_name} -> {dat_path}")
            res = pipeline.run_case(dat_path, case_name, aoa=a, mach=m, Re=r, max_iter=max_iter,
                                    retries=retries, strict=strict, cfl=cfl, incompressible=incompressible,
                                    mesh_override=mesh_file)
            results.append(res)
    return results


def analyze_aerosandbox(dat_path, alpha_list, Re, mach):
    if asb is None:
        raise RuntimeError("Aerosandbox no está instalado. Instala con 'pip install aerosandbox'.")
    # Carga .dat (salta cabecera si la hay)
    try:
        coords = np.loadtxt(dat_path)
    except Exception:
        coords = np.loadtxt(dat_path, skiprows=1)
    airfoil = asb.Airfoil(name=Path(dat_path).stem, coordinates=coords)
    fn = getattr(airfoil, "get_aero_from_neuralfoil", None)
    if fn is None:
        raise AttributeError("Esta versión de aerosandbox no tiene get_aero_from_neuralfoil.")
    rows = []
    airfoil_name = Path(dat_path).stem
    for alpha in alpha_list:
        aero = fn(alpha=alpha, Re=Re, mach=mach, n_crit=9.0, include_360_deg_effects=True)
        rows.append({
            "solver": "aerosandbox-neuralfoil",
            "airfoil": airfoil_name,
            "mach": mach,
            "Re": Re,
            "alpha": alpha,
            "CL": _to_scalar(aero["CL"]),
            "CD": _to_scalar(aero["CD"]),
            "CM": _to_scalar(aero.get("CM", aero.get("CMm", 0.0)))
        })
        print(f"[AeroSB] {Path(dat_path).name} AoA={alpha}° -> CL={rows[-1]['CL']:.5f} "
              f"CD={rows[-1]['CD']:.6f} CM={rows[-1]['CM']:.5f}")
    return rows


def extract_su2_row(case_name, incompressible=True):
    base = Path('results') / 'su2' / case_name
    visc_dir = base / 'viscous'
    summary_json = visc_dir / 'run_summary.json'
    if not summary_json.exists():
        return None
    try:
        data = json.loads(summary_json.read_text())
        return {
            "solver": "su2-incomp" if incompressible else "su2-comp",
            "airfoil": case_name,
            "mach": data.get("MACH"),
            "Re": data.get("REYNOLDS"),
            "alpha": data.get("AOA"),
            "CL": data.get("CL"),
            "CD": data.get("CD"),
            "CM": data.get("CM")
        }
    except Exception:
        return None


def export_csv(rows, out_path="results/combined_results.csv"):
    if not rows:
        print("[CSV] No hay datos para exportar.")
        return
    os.makedirs(Path(out_path).parent, exist_ok=True)
    fieldnames = ["solver", "airfoil", "alpha", "Re", "mach", "CL", "CD", "CM"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"[CSV] Exportado a {out_path}")


def validate_exports(results_list: list, incompressible=True):
    import json
    ok_all = True
    print("\n[VERIFY] Validating exported SU2 results (viscous only)...")
    for r in results_list:
        if not isinstance(r, dict) or 'case' not in r:
            print(f"[WARN] Unexpected result entry: {r}")
            ok_all = False
            continue
        case = r['case']
        visc = r.get('viscous')
        base = Path('results') / 'su2' / case
        visc_dir = base / 'viscous'
        forces_file = visc_dir / 'forces_breakdown.dat'
        summary_json = visc_dir / 'run_summary.json'
        if not forces_file.exists():
            print(f"[MISSING] {case}: {forces_file}")
            ok_all = False
        else:
            try:
                CL, CD, CM = su2_runner.parse_forces_file(str(forces_file))
                if visc and isinstance(visc, (list, tuple)) and len(visc) >= 3:
                    pass
                print(f"[OK] {case} -> CL={CL:.5f} CD={CD:.6f} CM={CM:.5f}")
            except Exception as e:
                print(f"[ERROR] {case}: parser could not read {forces_file}: {e}")
                ok_all = False
        if not summary_json.exists():
            print(f"[MISSING] {case}: {summary_json}")
            ok_all = False
        else:
            try:
                data = json.loads(summary_json.read_text())
                for k in ('CL', 'CD', 'CM'):
                    if k not in data or data[k] is None:
                        print(f"[WARN] {case}: run_summary.json missing or null {k}")
                        ok_all = False
            except Exception as e:
                print(f"[ERROR] {case}: Cannot parse run_summary.json: {e}")
                ok_all = False
    if ok_all:
        print("[VERIFY] All viscous cases have forces and summaries.")
    else:
        print("[VERIFY] Some viscous cases failed validation.")
    return ok_all


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Generate and analyze airfoils with SU2 and Aerosandbox")
    parser.add_argument("--generate-only", action="store_true", help="Only generate .dat profiles and skip analysis")
    parser.add_argument("--aoa", type=float, default=0.0, help="AoA for SU2 runs")
    parser.add_argument("--mach", type=float, default=0.15, help="Mach for SU2 and Aerosandbox (neuralfoil)")
    parser.add_argument("--mach-list", type=str, default=None, help="Comma-separated Machs for sweeps (e.g. '0.1,0.2')")
    parser.add_argument("--Re", type=float, default=1e6, help="Reynolds for SU2 and Aerosandbox")
    parser.add_argument("--Re-list", type=str, default=None, help="Comma-separated Re for sweeps (e.g. '5e5,1e6')")
    parser.add_argument("--aoa-list", type=str, default=None, help="Comma-separated AoAs for sweeps (e.g. '0,2,4')")
    parser.add_argument("--t-list", type=str, default=None,
                        help="Espesores relativos para NACA 00xx (e.g. '0.06,0.08' para 6% y 8%)")
    parser.add_argument("--c-list", type=str, default=None,
                        help="Cuerdas en metros para generar los perfiles (e.g. '0.8,1.0')")
    parser.add_argument("--normalize-profiles", action="store_true",
                        help="Normaliza las coordenadas de los perfiles generados (x/c, y/c)")
    parser.add_argument("--profile-types", type=str, default="naca",
                        help="Tipos de perfiles: naca,naca_antenna,rotodomo,bezier o all (separados por coma)")
    parser.add_argument("--profiles-output", type=str, default="generated_profiles",
                        help="Carpeta donde guardar los .dat e imágenes de perfiles")
    parser.add_argument("--save-profile-plots", action="store_true",
                        help="Guardar PNG de los perfiles si matplotlib está disponible")
    parser.add_argument("--antenna-length", type=float, default=4.5, help="Longitud de la antena (m)")
    parser.add_argument("--antenna-height", type=float, default=0.3, help="Altura de la antena (m)")
    parser.add_argument("--naca-ant-c-start", type=float, default=4.6, help="Cuerda inicial para barrido NACA+antena")
    parser.add_argument("--naca-ant-c-end", type=float, default=10.0, help="Cuerda final para barrido NACA+antena")
    parser.add_argument("--naca-ant-c-step", type=float, default=0.1, help="Paso de cuerda en NACA+antena")
    parser.add_argument("--naca-ant-t-min", type=float, default=0.02, help="Espesor mínimo (relativo) en NACA+antena")
    parser.add_argument("--naca-ant-t-max", type=float, default=0.5, help="Espesor máximo (relativo) en NACA+antena")
    parser.add_argument("--naca-ant-pos-count", type=int, default=10, help="Número de posiciones a probar en la antena")
    parser.add_argument("--rotodomo-c-start", type=float, default=4.6, help="Cuerda inicial para rotodomo")
    parser.add_argument("--rotodomo-c-end", type=float, default=11.0, help="Cuerda final para rotodomo")
    parser.add_argument("--rotodomo-c-step", type=float, default=0.1, help="Paso de cuerda para rotodomo")
    parser.add_argument("--rotodomo-t-min", type=float, default=0.05, help="Espesor mínimo (relativo) para rotodomo")
    parser.add_argument("--rotodomo-t-max", type=float, default=0.45, help="Espesor máximo (relativo) para rotodomo")
    parser.add_argument("--bezier-c-start", type=float, default=6.0, help="Cuerda inicial para perfil Bézier simétrico")
    parser.add_argument("--bezier-c-end", type=float, default=10.0, help="Cuerda final para perfil Bézier simétrico")
    parser.add_argument("--bezier-c-step", type=float, default=0.5, help="Paso de cuerda para perfil Bézier")
    parser.add_argument("--bezier-t-min", type=float, default=0.05, help="Espesor mínimo (relativo) para perfil Bézier")
    parser.add_argument("--bezier-t-max", type=float, default=0.55, help="Espesor máximo (relativo) para perfil Bézier")
    parser.add_argument("--bezier-sharpness", type=str, default="0.1,0.2,0.3,0.4,0.5,0.6,0.7",
                        help="Lista de sharpness para el Bézier (0-1, separados por coma)")
    parser.add_argument("--max-iter", type=int, default=100, help="ITER for SU2 (default 100)")
    parser.add_argument("--retries", type=int, default=0, help="Retries for SU2")
    parser.add_argument("--cfl", type=float, default=None, help="CFL for SU2")
    parser.add_argument("--compressible", action="store_true", help="Run SU2 compresible (inv+visc). Default incompressible viscous only.")
    parser.add_argument("--mesh-file", type=str, default=None, help="Use an existing SU2 mesh instead of generating with Gmsh")
    parser.add_argument("--skip-su2", action="store_true", help="Skip SU2 analysis")
    parser.add_argument("--skip-aerosb", action="store_true", help="Skip Aerosandbox analysis")
    parser.add_argument("--export-csv", type=str, default="results/combined_results.csv",
                        help="Ruta del CSV combinado (AeroSandbox/NeuralFoil y SU2)")
    parser.add_argument("--comparison-csv", type=str, default="results/simulations_clcdcm.csv",
                        help="Ruta adicional para exportar CL/CD/CM de NeuralFoil y SU2")
    parser.add_argument("--run-comparison", action="store_true",
                        help="Ejecuta ranking de perfiles tras generar el CSV")
    parser.add_argument("--comparison-metric", type=str, default="cd_mean",
                        help="Métrica de ranking: cd_mean, cd_min, cl_mean, clcd_mean, clcd_max")
    parser.add_argument("--comparison-solver", type=str, default=None,
                        help="Filtrar por solver en el ranking (e.g. su2-incomp)")
    parser.add_argument("--comparison-aoa-min", type=float, default=None, help="Ángulo mínimo para ranking")
    parser.add_argument("--comparison-aoa-max", type=float, default=None, help="Ángulo máximo para ranking")
    parser.add_argument("--comparison-output", type=str, default="results/airfoil_rankings.csv",
                        help="CSV de ranking de perfiles")
    parser.add_argument("--plot-comparison", action="store_true", help="Generar PNG de ranking y polar")
    parser.add_argument("--plot-dir", type=str, default=None, help="Carpeta donde guardar las gráficas")
    parser.add_argument("--plot-top-n", type=int, default=10, help="Top-N para la barra de ranking")
    return parser


def run_pipeline(args):

    t_list = _parse_num_list(args.t_list, [0.06])
    c_list = _parse_num_list(args.c_list, [1.0])
    bezier_sharpness = _parse_num_list(args.bezier_sharpness, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    profile_types = [p.strip().lower() for p in (args.profile_types or "naca").split(",") if p.strip()]
    if "all" in profile_types:
        profile_types = ["naca", "naca_antenna", "rotodomo", "bezier"]

    profiles = {}
    if "naca" in profile_types:
        profiles.update(generate_airfoils(t_list, c_list, normalize=args.normalize_profiles,
                                          output_folder=args.profiles_output))
    if "naca_antenna" in profile_types:
        profiles.update(profile_generators.generate_naca_antenna_profiles(
            chord_start=args.naca_ant_c_start,
            chord_end=args.naca_ant_c_end,
            chord_step=args.naca_ant_c_step,
            thickness_min=args.naca_ant_t_min,
            thickness_max=args.naca_ant_t_max,
            positions_count=args.naca_ant_pos_count,
            antenna_length=args.antenna_length,
            antenna_height=args.antenna_height,
            output_dir=args.profiles_output,
            save_plots=args.save_profile_plots,
        ))
    if "rotodomo" in profile_types:
        profiles.update(profile_generators.generate_rotodomo_profiles(
            chord_start=args.rotodomo_c_start,
            chord_end=args.rotodomo_c_end,
            chord_step=args.rotodomo_c_step,
            thickness_min=args.rotodomo_t_min,
            thickness_max=args.rotodomo_t_max,
            antenna_length=args.antenna_length,
            antenna_height=args.antenna_height,
            output_dir=args.profiles_output,
            save_plots=args.save_profile_plots,
        ))
    if "bezier" in profile_types:
        profiles.update(profile_generators.generate_bezier_profiles(
            chord_start=args.bezier_c_start,
            chord_end=args.bezier_c_end,
            chord_step=args.bezier_c_step,
            thickness_min=args.bezier_t_min,
            thickness_max=args.bezier_t_max,
            sharpness_list=bezier_sharpness,
            antenna_length=args.antenna_length,
            antenna_height=args.antenna_height,
            output_dir=args.profiles_output,
            save_plots=args.save_profile_plots,
        ))

    if not profiles:
        print("[WARN] No se generaron perfiles.")
        return
    if args.generate_only:
        return

    aoa_list = _parse_num_list(args.aoa_list, None)
    mach_list = _parse_num_list(args.mach_list, [args.mach])
    re_list = _parse_num_list(args.Re_list, [args.Re])

    aero_rows = []
    if not args.skip_aerosb:
        for key, info in profiles.items():
            for Re in re_list:
                for mach in mach_list:
                    aero_rows.extend(analyze_aerosandbox(info["dat"], aoa_list or [args.aoa], Re, mach))

    su2_rows = []
    if not args.skip_su2:
        su2_ok = su2_runner.is_su2_available()
        if not su2_ok:
            print("[WARN] SU2 no disponible en WSL; se omite análisis SU2.")
        else:
            results = analyze_su2(profiles, aoa=args.aoa, mach=args.mach, Re=args.Re, max_iter=args.max_iter,
                                  aoa_list=aoa_list, mach_list=mach_list, Re_list=re_list, retries=args.retries,
                                  strict=False, add_ts=False, cfl=args.cfl, incompressible=not args.compressible,
                                  mesh_file=args.mesh_file)
            validate_exports(results, incompressible=not args.compressible)
            for res in results:
                case = res.get("case") if isinstance(res, dict) else None
                if case:
                    row = extract_su2_row(case, incompressible=not args.compressible)
                    if row:
                        su2_rows.append(row)

    export_rows = aero_rows + su2_rows
    export_csv(export_rows, out_path=args.export_csv)
    # Exportar también a un archivo adicional si se solicita (por defecto, results/simulations_clcdcm.csv)
    if args.comparison_csv and Path(args.comparison_csv) != Path(args.export_csv):
        export_csv(export_rows, out_path=args.comparison_csv)
    if args.run_comparison:
        airfoil_comparison.run_comparison(
            csv_in=Path(args.export_csv),
            csv_out=Path(args.comparison_output),
            metric=args.comparison_metric,
            solver=args.comparison_solver,
            aoa_min=args.comparison_aoa_min,
            aoa_max=args.comparison_aoa_max,
            plot=args.plot_comparison,
            plot_dir=Path(args.plot_dir) if args.plot_dir else None,
            top_n=args.plot_top_n,
        )
    return export_rows


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return run_pipeline(args)


if __name__ == "__main__":
    main()
