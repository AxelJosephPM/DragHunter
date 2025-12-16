import re
import os
from pathlib import Path


def _replace_key_value(lines, key, value):
    """Replace or add 'KEY = value' entry in a set of lines.
    Returns modified list of lines.
    """
    key_pattern = re.compile(rf"^\s*{re.escape(key)}\s*(?:=|\s)\s*.*$", flags=re.IGNORECASE)
    replaced = False
    new_lines = []
    for l in lines:
        if key_pattern.match(l):
            # Keep same spacing left, but write KEY = value
            new_lines.append(f"{key} = {value}\n")
            replaced = True
        else:
            new_lines.append(l)
    if not replaced:
        # append a new line at end
        new_lines.append(f"{key} = {value}\n")
    return new_lines


def apply_replacements_to_template(template_file: str, output_file: str, replacements: dict):
    """Write a SU2 config (output_file) from a template by replacing keys defined in replacements dict.

    - template_file: path to the SU2 template
    - output_file: path to write the new SU2 config
    - replacements: dict { 'AOA' : '2.0', 'MESH_FILENAME' : '/mnt/c/.../mesh.su2', ... }
    """
    try:
        with open(template_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] Cannot read template file {template_file}: {e}")
        raise

    for k, v in replacements.items():
        # ensure v is string
        try:
            vstr = str(v)
        except Exception:
            vstr = repr(v)
        lines = _replace_key_value(lines, k, vstr)

    try:
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[ERROR] Cannot write output file {output_file}: {e}")
        raise

    print(f"[OK] Config SU2 generado: {output_file}")


def create_config_for_case(template_file: str, output_file: str, mesh_wsl: str = None, aoa: float = None, mach: float = None, Re: float = None, iter_val: int = None, cfl: float = None, breakdown_wsl: str = None, restart_wsl: str = None, read_binary_restart: bool = False, extra: dict = None):
    """High-level helper: create a SU2 config for a specific case by setting common keys.

    `extra` can contain additional keys to be set in the template.
    """
    replacements = {}
    if mesh_wsl:
        replacements['MESH_FILENAME'] = mesh_wsl
    if breakdown_wsl:
        replacements['BREAKDOWN_FILENAME'] = breakdown_wsl
    if aoa is not None:
        replacements['AOA'] = aoa
    if mach is not None:
        replacements['MACH_NUMBER'] = mach
    if Re is not None:
        replacements['REYNOLDS_NUMBER'] = Re
    if iter_val is not None:
        replacements['ITER'] = int(iter_val)
    if cfl is not None:
        # SU2 usa CFL_NUMBER; no escribimos clave CFL (no es válida en v8).
        replacements['CFL_NUMBER'] = float(cfl)
    if restart_wsl:
        replacements['RESTART_FILENAME'] = restart_wsl
    if read_binary_restart:
        replacements['READ_BINARY_RESTART'] = 'YES'
    if extra:
        for k, v in extra.items():
            replacements[k] = v

    apply_replacements_to_template(template_file, output_file, replacements)

