from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


def _join(values: List[float]) -> str:
    return ",".join(str(v) for v in values)


@dataclass
class SimulationParameters:
    aoa_list: List[float]
    mach_list: List[float]
    re_list: List[float]
    max_iter: int
    cfl: Optional[float]
    mesh_file: Optional[str]
    retries: int
    compressible: bool
    skip_su2: bool
    skip_aerosb: bool
    generate_only: bool
    export_csv: str
    profile_types: List[str]
    profiles_output: str
    t_list: List[float]
    c_list: List[float]
    normalize_profiles: bool
    save_profile_plots: bool
    antenna_length: float
    antenna_height: float
    naca_ant_c_range: Tuple[float, float, float]
    naca_ant_t_range: Tuple[float, float]
    naca_ant_pos_count: int
    rotodomo_c_range: Tuple[float, float, float]
    rotodomo_t_range: Tuple[float, float]
    bezier_c_range: Tuple[float, float, float]
    bezier_t_range: Tuple[float, float]
    bezier_sharpness: List[float]
    run_comparison: bool
    comparison_metric: str
    comparison_solver: Optional[str]
    comparison_aoa_min: Optional[float]
    comparison_aoa_max: Optional[float]
    comparison_output: str
    plot_comparison: bool
    plot_dir: Optional[str]
    plot_top_n: int

    def to_cli_args(self) -> List[str]:
        """Traduce los parámetros tipados a la línea de comandos de main.py."""
        cmd: List[str] = [
            sys.executable,
            "main.py",
            "--aoa-list",
            _join(self.aoa_list),
            "--mach-list",
            _join(self.mach_list),
            "--Re-list",
            _join(self.re_list),
            "--max-iter",
            str(self.max_iter),
            "--export-csv",
            self.export_csv,
            "--profile-types",
            ",".join(self.profile_types),
            "--profiles-output",
            self.profiles_output,
            "--t-list",
            _join(self.t_list),
            "--c-list",
            _join(self.c_list),
            "--antenna-length",
            str(self.antenna_length),
            "--antenna-height",
            str(self.antenna_height),
            "--naca-ant-c-start",
            str(self.naca_ant_c_range[0]),
            "--naca-ant-c-end",
            str(self.naca_ant_c_range[1]),
            "--naca-ant-c-step",
            str(self.naca_ant_c_range[2]),
            "--naca-ant-t-min",
            str(self.naca_ant_t_range[0]),
            "--naca-ant-t-max",
            str(self.naca_ant_t_range[1]),
            "--naca-ant-pos-count",
            str(self.naca_ant_pos_count),
            "--rotodomo-c-start",
            str(self.rotodomo_c_range[0]),
            "--rotodomo-c-end",
            str(self.rotodomo_c_range[1]),
            "--rotodomo-c-step",
            str(self.rotodomo_c_range[2]),
            "--rotodomo-t-min",
            str(self.rotodomo_t_range[0]),
            "--rotodomo-t-max",
            str(self.rotodomo_t_range[1]),
            "--bezier-c-start",
            str(self.bezier_c_range[0]),
            "--bezier-c-end",
            str(self.bezier_c_range[1]),
            "--bezier-c-step",
            str(self.bezier_c_range[2]),
            "--bezier-t-min",
            str(self.bezier_t_range[0]),
            "--bezier-t-max",
            str(self.bezier_t_range[1]),
            "--bezier-sharpness",
            _join(self.bezier_sharpness),
        ]
        if self.cfl is not None:
            cmd += ["--cfl", str(self.cfl)]
        if self.mesh_file:
            cmd += ["--mesh-file", self.mesh_file]
        if self.compressible:
            cmd.append("--compressible")
        if self.skip_su2:
            cmd.append("--skip-su2")
        if self.skip_aerosb:
            cmd.append("--skip-aerosb")
        if self.retries:
            cmd += ["--retries", str(self.retries)]
        if self.normalize_profiles:
            cmd.append("--normalize-profiles")
        if self.save_profile_plots:
            cmd.append("--save-profile-plots")
        if self.generate_only:
            cmd.append("--generate-only")
        if self.run_comparison:
            cmd += [
                "--run-comparison",
                "--comparison-metric",
                self.comparison_metric,
                "--comparison-output",
                self.comparison_output,
                "--plot-top-n",
                str(self.plot_top_n),
            ]
            if self.comparison_solver:
                cmd += ["--comparison-solver", self.comparison_solver]
            if self.comparison_aoa_min is not None:
                cmd += ["--comparison-aoa-min", str(self.comparison_aoa_min)]
            if self.comparison_aoa_max is not None:
                cmd += ["--comparison-aoa-max", str(self.comparison_aoa_max)]
            if self.plot_comparison:
                cmd.append("--plot-comparison")
            if self.plot_dir:
                cmd += ["--plot-dir", self.plot_dir]
        return cmd

    @property
    def export_path(self) -> Path:
        return Path(self.export_csv)

    @property
    def comparison_path(self) -> Path:
        return Path(self.comparison_output)
