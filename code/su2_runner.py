import subprocess
import shutil
import os
import shlex
import su2_configurator
from pathlib import Path

# Permite sobreescribir el ejecutable de SU2 dentro de WSL (por ejemplo /usr/local/bin/SU2_CFD)
SU2_CMD = os.environ.get("SU2_CMD", "SU2_CFD")


def to_wsl(path):
    r"""
    Convierte rutas de Windows a rutas WSL:
    C:\Users\Axel\file -> /mnt/c/Users/Axel/file
    """
    path = path.replace("\\", "/")
    if ":" in path:
        return "/mnt/" + path[0].lower() + path[2:]
    return path


def _check_su2_available():
    """
    Resuelve el binario de SU2 dentro de WSL.
    Estrategia:
      1) Si SU2_CMD está seteado, probar ese valor.
      2) Probar SU2_CFD en PATH.
      3) Probar activar conda env su2env y buscar SU2_CFD.
    Devuelve la ruta encontrada (string) o None si no se halló.
    """

    # comandos de setup habituales
    base_setup = "source ~/.bashrc 2>/dev/null; source ~/.profile 2>/dev/null;"
    conda_setup = (
        "source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || true; "
        "source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true; "
    )

    candidates = []

    # 1) valor explícito (puede ser ruta absoluta o nombre)
    if SU2_CMD:
        candidates.append(SU2_CMD)

    # 2) nombre estándar
    candidates.append("SU2_CFD")

    # 3) conda env su2env
    candidates.append("conda:su2env:SU2_CFD")

    for cand in candidates:
        if cand.startswith("conda:"):
            _, env_name, bin_name = cand.split(":")
            cmd = (
                f"{base_setup} {conda_setup} conda activate {shlex.quote(env_name)} 2>/dev/null && "
                f"command -v {shlex.quote(bin_name)}"
            )
        else:
            cmd = f"{base_setup} command -v {shlex.quote(cand)}"

        result = subprocess.run(
            ["wsl", "bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        path = result.stdout.strip()
        if result.returncode == 0 and path:
            return path

    print(f"[ERROR] No se encontró SU2_CFD en WSL.")
    print("        Opciones:")
    print("        - Instala SU2 dentro de WSL y agrega SU2_CFD al PATH.")
    print("        - Exporta la variable de entorno SU2_CMD con la ruta absoluta en WSL.")
    print("        - O instala/activa el entorno conda 'su2env' que contenga SU2_CFD.")
    return None


def is_su2_available():
    """Public wrapper to quickly test whether SU2 is available through WSL (True/False)."""
    return _check_su2_available() is not None


def get_su2_resolved_path():
    """Return the resolved path in WSL to the SU2 binary if available, or None.
    Use for detailed diagnostics from callers.
    """
    return _check_su2_available()


def _get_config_restart_filename(cfg_file: str):
    """Read a SU2 config file and extract the RESTART_FILENAME value (if any).
    Returns a string (filename, could be 'restart.csv' or 'solution') or None.
    """
    restart = None
    read_binary = False
    try:
        with open(cfg_file, "r") as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped.upper().startswith("RESTART_FILENAME"):
                    # e.g. RESTART_FILENAME = restart.csv
                    parts = line.split("=", 1)
                    if len(parts) > 1:
                        restart = parts[1].strip().strip('"').strip("'")
                elif line_stripped.upper().startswith("READ_BINARY_RESTART"):
                    parts = line.split("=", 1)
                    if len(parts) > 1 and parts[1].strip().upper().startswith("YES"):
                        read_binary = True
    except Exception:
        # If config cannot be read, fallthrough and return None
        pass
    return restart, read_binary


def parse_forces_file(forces_path: str):
    """Parse `forces_breakdown.dat` and return CL, CD, CM as floats.
    Raises RuntimeError if any value is not found.
    This function is factored out so it can be unit tested.
    """
    import re
    from pathlib import Path

    if not Path(forces_path).exists():
        raise FileNotFoundError(f"Forces file {forces_path} not found")

    text = Path(forces_path).read_text()

    def _extract(label: str):
        pattern = re.compile(
            rf"^\s*Total\s+{re.escape(label)}(?!/)\b.*?:\s*([+-]?[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)",
            flags=re.IGNORECASE | re.MULTILINE
        )
        # Use the last occurrence in the file (SU2 puede escribir el mismo archivo varias veces)
        matches = list(pattern.finditer(text))
        if not matches:
            return None
        return float(matches[-1].group(1))

    CL = _extract("CL")
    CD = _extract("CD")
    CM = _extract("CMz") or _extract("CM")
    missing = [name for name, val in (("CL", CL), ("CD", CD), ("CMz", CM)) if val is None]
    if missing:
        # Provide a more informative error message + sample
        raise RuntimeError(
            f"No se pudieron extraer {', '.join(missing)} de {forces_path}\nPrimeras 80 lineas:\n" +
            "---\n" + "\n".join(text.splitlines()[:80]) + "\n---"
        )

    return CL, CD, CM


def run_su2(mesh_file, cfg_template, aoa=0.0, mach=0.15, Re=1e6, viscous=False, max_iter=None, output_dir=None, retries: int = 1, strict: bool = False, cfl: float = None, incompressible: bool = False):
    su2_cmd_resolved = _check_su2_available()
    if su2_cmd_resolved is None:
        return None

    cfg_tmp = "config_tmp.cfg"
    # debug file for troubleshooting in tests
    def _debug(msg):
        try:
            with open('su2_runner_debug.log', 'a', encoding='utf-8') as df:
                df.write(msg + '\n')
        except Exception:
            pass
    _debug(f"run_su2 start: mesh_file={mesh_file}, cfg_template={cfg_template}, output_dir={output_dir}")

    # ----- Rutas absolutas -----
    mesh_wsl = to_wsl(os.path.abspath(mesh_file))

    # If no output_dir specified, default into results/su2/(inviscid|viscous)
    if output_dir is None:
        default_sub = "viscous" if viscous else "inviscid"
        output_dir = os.path.join("results", "su2", default_sub)

    os.makedirs(output_dir, exist_ok=True)

    def _is_converged(text: str) -> bool:
        t = text.lower()
        if "maximum number of iterations reached" in t:
            return False
        if "non-physical" in t:
            return False
        if "converged" in t and ("yes" in t or "converged |   yes" in t):
            return True
        # If no explicit signal, treat as not converged so we don’t keep looping silently
        return False

    # Parse initial CFL (if present in template) so we can adjust it across retries
    import re
    initial_cfl = None
    try:
        with open(cfg_template, 'r') as _f:
            for l in _f:
                m = re.match(r"^\s*CFL(?:_NUMBER)?\s*=\s*([0-9\.eE+-]+)", l)
                if m:
                    try:
                        initial_cfl = float(m.group(1))
                        break
                    except Exception:
                        initial_cfl = None
                        break
    except Exception:
        initial_cfl = None

    if cfl is not None:
        current_cfl = float(cfl)
    else:
        current_cfl = initial_cfl if initial_cfl is not None else 0.2
    # default iteration budget
    current_iter = int(max_iter) if max_iter is not None else 100

    attempt = 0
    last_error = None
    while attempt <= retries:
        attempt += 1
        # Create template with per-case replacements using su2_configurator
        try:
            # Create breakdown filename for this run
            breakdown_wsl = to_wsl(os.path.abspath(os.path.join(output_dir, "forces_breakdown.dat")))
            # Build replacement map
            replacements = {
                'MESH_FILENAME': mesh_wsl,
                'BREAKDOWN_FILENAME': breakdown_wsl,
                'AOA': aoa,
                'MACH_NUMBER': mach,
                'REYNOLDS_NUMBER': Re,
            }
            if current_iter is not None:
                replacements['ITER'] = int(current_iter)
            if current_cfl is not None:
                replacements['CFL_NUMBER'] = float(current_cfl)

            # Print debug info
            print(f"[DEBUG] Template exists: {cfg_template} -> {os.path.exists(cfg_template)}")
            print(f"[DEBUG] Replacements: mesh_wsl={mesh_wsl}, aoa={aoa}, mach={mach}, Re={Re}, iter={current_iter}, cfl={current_cfl}, breakdown={breakdown_wsl}")
            _debug(f"calling create_config_for_case with mesh_wsl={mesh_wsl}, aoa={aoa}, mach={mach}, Re={Re}, iter={current_iter}, cfl={current_cfl}, breakdown_wsl={breakdown_wsl}")
            # Extra claves específicas (ej. incomprensible)
            extra = {}
            if viscous and incompressible:
                # Constantes del tutorial SU2 NACA0012 Re=6e6 (densidad, viscosidad, velocidad)
                import math
                rho = 2.13163
                mu = 1.853e-5
                u = 52.157 * math.cos(math.radians(aoa))
                v = 52.157 * math.sin(math.radians(aoa))
                extra.update({
                    'INC_DENSITY_INIT': rho,
                    'INC_DENSITY_REF': 1.0,
                    'INC_VELOCITY_REF': 1.0,
                    'INC_NONDIM': 'INITIAL_VALUES',
                    'INC_VELOCITY_INIT': f"( {u}, {v}, 0.0 )",
                    'VISCOSITY_MODEL': 'CONSTANT_VISCOSITY',
                    'MU_CONSTANT': mu,
                })
            su2_configurator.create_config_for_case(
                cfg_template, cfg_tmp,
                mesh_wsl=mesh_wsl, aoa=aoa, mach=mach, Re=Re,
                iter_val=current_iter, cfl=current_cfl,
                breakdown_wsl=breakdown_wsl,
                extra=extra
            )
            _debug(f"config_tmp created, exists? {os.path.exists(cfg_tmp)}")
        except Exception as e:
            import traceback
            err_msg = f"[ERROR] No se pudo generar el archivo de configuración {cfg_tmp} desde plantilla {cfg_template}: {e}"
            print(err_msg)
            _debug(err_msg)
            # write full traceback to debug file
            try:
                with open('su2_runner_debug.log', 'a', encoding='utf-8') as df:
                    traceback.print_exc(file=df)
            except Exception:
                pass
            traceback.print_exc()
            return None

        cfg_wsl = to_wsl(os.path.abspath(cfg_tmp))

        # No restart copying: avoids mesh/solution mismatch crashes when cases differ

        print(f"[INFO] Ejecutando SU2 dentro de WSL... (attempt {attempt}/{retries+1})")

        wsl_workdir = to_wsl(os.path.abspath(output_dir))
        run_cmd = (
            f"source ~/.bashrc 2>/dev/null; "
            f"source ~/.profile 2>/dev/null; "
            f"cd {shlex.quote(wsl_workdir)} && "
            f"{shlex.quote(su2_cmd_resolved)} {shlex.quote(cfg_wsl)}"
        )

        result = subprocess.run([
            "wsl",
            "bash",
            "-lc",
            run_cmd,
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Always write SU2 stdout/stderr to files in output_dir for debugging
        try:
            stdout_path = os.path.join(output_dir, 'su2_stdout.log')
            stderr_path = os.path.join(output_dir, 'su2_stderr.log')
            with open(stdout_path, 'a', encoding='utf-8', errors='ignore') as sf:
                sf.write(result.stdout + "\n")
            with open(stderr_path, 'a', encoding='utf-8', errors='ignore') as ef:
                ef.write(result.stderr + "\n")
        except Exception:
            # Don't fail on log write issues; keep running
            pass

        # Also print the logs to the terminal for immediate feedback
        print(result.stdout)
        print(result.stderr)

        soutext = result.stdout + "\n" + result.stderr
        _debug(f"SU2 run complete: stdout_len={len(result.stdout)} stderr_len={len(result.stderr)}")
        converged = _is_converged(soutext)
        if not converged:
            print("[WARN] SU2 no convergió (max iterations reached o no convergió). Revisa salida de SU2 para más detalles.")
            last_error = soutext
            try:
                print(f"[INFO] Logs: {os.path.join(output_dir, 'su2_stdout.log')} and {os.path.join(output_dir, 'su2_stderr.log')}")
            except Exception:
                pass
            if attempt <= retries:
                print(f"[INFO] Reintentando SU2 con misma config (attempt {attempt+1})")
                continue
            if strict:
                raise RuntimeError("SU2 no convergió después de reintentos")

        # -------- Localizar resultado de fuerzas (intentar incluso si no convergió) --------
        forces_local = os.path.join(output_dir, "forces_breakdown.dat")
        _debug(f"forces_local path (Windows): {forces_local}, exists={os.path.exists(forces_local)}")
        if not os.path.exists(forces_local):
            print(f"[ERROR] No se encontró {forces_local}")
            try:
                print(f"cfg_tmp exists: {os.path.exists(cfg_tmp)}")
                if os.path.exists(cfg_tmp):
                    print('--- CONFIG TMP CONTENT START ---')
                    print(open(cfg_tmp, 'r', encoding='utf-8', errors='ignore').read())
                    print('--- CONFIG TMP CONTENT END ---')
            except Exception:
                pass
            print("         SU2 probablemente no llegó a calcular fuerzas.")
            return None

        try:
            CL, CD, CM = parse_forces_file(forces_local)
        except Exception as e:
            print(f"[ERROR] Parser de fuerzas fallo: {e}")
            raise

        print(f"[OK] CL={CL:.4f}, CD={CD:.5f}, CM={CM:.5f}")

        # Attempt to gather final iteration/residual from history files for a small run summary
        final_iter = None
        final_rms = None
        history_candidates = [os.path.join(output_dir, 'history.csv'), os.path.join(output_dir, 'history')]
        import csv
        for h in history_candidates:
            if os.path.exists(h):
                try:
                    with open(h, 'r', encoding='utf-8', errors='ignore') as hh:
                        reader = csv.reader(hh)
                        rows = [r for r in reader if r]
                        if len(rows) > 1:
                            headers = rows[0]
                            last = rows[-1]
                            for key in ('iter', 'ITER', 'it'):
                                for i, col in enumerate(headers):
                                    if key.lower() in col.lower():
                                        try:
                                            final_iter = int(last[i])
                                            break
                                        except Exception:
                                            pass
                                if final_iter is not None:
                                    break
                            for key in ('rms', 'RESIDUAL', 'RMS', 'RMS_DENSITY'):
                                for i, col in enumerate(headers):
                                    if key.lower() in col.lower():
                                        try:
                                            final_rms = float(last[i])
                                            break
                                        except Exception:
                                            pass
                                if final_rms is not None:
                                    break
                except Exception:
                    pass
                break

        # Save a small JSON summary into the output_dir
        try:
            import json
            summary = {
                'CL': CL, 'CD': CD, 'CM': CM,
                'converged': converged,
                'final_iter': final_iter,
                'final_rms': final_rms,
                'attempts': attempt,
                'final_CFL': current_cfl,
                'final_ITER': current_iter
            }
            with open(os.path.join(output_dir, 'run_summary.json'), 'w', encoding='utf-8') as jf:
                json.dump(summary, jf)
        except Exception:
            pass

        return CL, CD, CM, final_iter, final_rms, converged

    # If we somehow reach here and didn't return with CL/CD/CM
    return None
