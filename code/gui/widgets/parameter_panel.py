from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6 import QtCore, QtWidgets

from gui.parameters import SimulationParameters


class ParameterPanel(QtWidgets.QWidget):
    """Panel de control de parámetros. Retorna SimulationParameters tipados."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.defaults = self._build_defaults()
        self._build_ui()

    # -------------------------- helpers --------------------------
    def _build_defaults(self):
        return {
            "aoa_list": "0.0",
            "mach_list": "0.32",
            "re_list": "37178444,33681989",
            "max_iter": 1000,
            "cfl": "",
            "mesh_file": "",
            "retries": 0,
            "compressible": False,
            "skip_su2": True,
            "skip_aerosb": True,
            "generate_only": False,
            "export_csv": "results/combined_results.csv",
            "profile_types": ["rotodomo"],
            "profiles_output": "generated_profiles",
            "t_list": "0.06",
            "c_list": "1.0",
            "normalize_profiles": False,
            "save_profile_plots": True,
            "antenna_length": 4.5,
            "antenna_height": 0.3,
            "naca_ant_c_start": 4.6,
            "naca_ant_c_end": 10.0,
            "naca_ant_c_step": 0.5,
            "naca_ant_t_min": 0.02,
            "naca_ant_t_max": 0.5,
            "naca_ant_pos_count": 10,
            "rotodomo_c_start": 4.6,
            "rotodomo_c_end": 10.0,
            "rotodomo_c_step": 0.1,
            "rotodomo_t_min": 0.05,
            "rotodomo_t_max": 0.45,
            "bezier_c_start": 6.0,
            "bezier_c_end": 7.3,
            "bezier_c_step": 0.1,
            "bezier_t_min": 0.05,
            "bezier_t_max": 0.55,
            "bezier_sharpness": "0.1,0.2,0.3,0.4,0.5,0.6,0.7",
            "run_comparison": True,
            "comparison_metric": "cd_mean",
            "comparison_solver": "",
            "comparison_aoa_min": "",
            "comparison_aoa_max": "",
            "comparison_output": "results/airfoil_rankings.csv",
            "plot_comparison": True,
            "plot_dir": "",
            "plot_top_n": 20,
        }

    def _line(self, text: str, placeholder: str = "", tooltip: str = ""):
        edit = QtWidgets.QLineEdit(text)
        edit.setPlaceholderText(placeholder)
        if tooltip:
            edit.setToolTip(tooltip)
        return edit

    def _spin(self, value: int, minimum: int = 0, maximum: int = 10_000):
        box = QtWidgets.QSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        return box

    def _dspin(self, value: float, minimum: float = -1e6, maximum: float = 1e6, step: float = 0.1, decimals: int = 3):
        box = QtWidgets.QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(step)
        box.setValue(value)
        return box

    def _chk(self, text: str, checked: bool = False):
        box = QtWidgets.QCheckBox(text)
        box.setChecked(checked)
        return box

    # -------------------------- UI --------------------------
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        layout.addWidget(self._build_conditions_box())
        layout.addWidget(self._build_profiles_box())
        layout.addWidget(self._build_geometry_box())
        layout.addWidget(self._build_comparison_box())
        layout.addStretch(1)

    def _build_conditions_box(self):
        box = QtWidgets.QGroupBox("FLIGHT / SOLVER")
        form = QtWidgets.QFormLayout()
        self.aoa_edit = self._line(self.defaults["aoa_list"], "0,2,4", "Lista de ángulos de ataque (grados)")
        self.mach_edit = self._line(self.defaults["mach_list"], "0.1,0.3", "Lista de Mach (coma)")
        self.re_edit = self._line(self.defaults["re_list"], "3e6,5e6", "Lista de Reynolds (coma)")
        self.max_iter_spin = self._spin(self.defaults["max_iter"], 10, 100000)
        self.cfl_edit = self._line(self.defaults["cfl"], "ej. 2.0", "CFL override (vacío = plantilla)")
        self.retries_spin = self._spin(self.defaults["retries"], 0, 10)
        self.mesh_file_edit = self._line(self.defaults["mesh_file"], "", "Ruta a malla SU2 existente (opcional)")

        self.compress_chk = self._chk("COMPRESSIBLE", self.defaults["compressible"])
        self.skip_su2_chk = self._chk("SKIP SU2", self.defaults["skip_su2"])
        self.skip_aerosb_chk = self._chk("SKIP AEROSB", self.defaults["skip_aerosb"])
        self.generate_only_chk = self._chk("GENERATE ONLY", self.defaults["generate_only"])

        form.addRow("AOA LIST", self.aoa_edit)
        form.addRow("MACH LIST", self.mach_edit)
        form.addRow("RE LIST", self.re_edit)
        form.addRow("MAX ITER", self.max_iter_spin)
        form.addRow("CFL", self.cfl_edit)
        form.addRow("RETRIES", self.retries_spin)
        form.addRow("MESH FILE", self.mesh_file_edit)

        flags_widget = QtWidgets.QWidget()
        flags_layout = QtWidgets.QHBoxLayout(flags_widget)
        for w in (self.compress_chk, self.skip_su2_chk, self.skip_aerosb_chk, self.generate_only_chk):
            flags_layout.addWidget(w)
        flags_layout.addStretch(1)
        form.addRow("FLAGS", flags_widget)

        box.setLayout(form)
        return box

    def _build_profiles_box(self):
        box = QtWidgets.QGroupBox("PROFILES")
        form = QtWidgets.QFormLayout()
        self.profile_types = {
            "naca": self._chk("NACA", False),
            "naca_antenna": self._chk("NACA+ANT", False),
            "rotodomo": self._chk("ROTODO", "rotodomo" in self.defaults["profile_types"]),
            "bezier": self._chk("BEZIER", False),
        }
        types_widget = QtWidgets.QWidget()
        types_layout = QtWidgets.QHBoxLayout(types_widget)
        for chk in self.profile_types.values():
            types_layout.addWidget(chk)
        types_layout.addStretch(1)

        self.t_list_edit = self._line(self.defaults["t_list"], "0.06,0.08")
        self.c_list_edit = self._line(self.defaults["c_list"], "1.0")
        self.profiles_out_edit = self._line(self.defaults["profiles_output"], "", "Carpeta para .dat generados")
        self.normalize_chk = self._chk("NORMALIZE", self.defaults["normalize_profiles"])
        self.plots_chk = self._chk("SAVE PROFILE PNG", self.defaults["save_profile_plots"])
        self.export_csv_edit = self._line(self.defaults["export_csv"], "", "CSV combinado de salida")

        form.addRow("PROFILE TYPES", types_widget)
        form.addRow("T LIST", self.t_list_edit)
        form.addRow("C LIST", self.c_list_edit)
        form.addRow("OUTPUT DIR", self.profiles_out_edit)

        flags_widget = QtWidgets.QWidget()
        flags_layout = QtWidgets.QHBoxLayout(flags_widget)
        flags_layout.addWidget(self.normalize_chk)
        flags_layout.addWidget(self.plots_chk)
        flags_layout.addStretch(1)
        form.addRow("PROFILE FLAGS", flags_widget)
        form.addRow("EXPORT CSV", self.export_csv_edit)

        box.setLayout(form)
        return box

    def _build_geometry_box(self):
        box = QtWidgets.QGroupBox("GEOMETRY / RANGES")
        grid = QtWidgets.QGridLayout()
        row = 0

        self.ant_length = self._dspin(self.defaults["antenna_length"], 0.0, 50.0, 0.1, 3)
        self.ant_height = self._dspin(self.defaults["antenna_height"], 0.0, 10.0, 0.05, 3)
        self.ant_positions = self._spin(self.defaults["naca_ant_pos_count"], 1, 50)

        grid.addWidget(QtWidgets.QLabel("ANTENNA L"), row, 0)
        grid.addWidget(self.ant_length, row, 1)
        grid.addWidget(QtWidgets.QLabel("ANTENNA H"), row, 2)
        grid.addWidget(self.ant_height, row, 3)
        grid.addWidget(QtWidgets.QLabel("POS COUNT"), row, 4)
        grid.addWidget(self.ant_positions, row, 5)
        row += 1

        # NACA+ANT ranges
        self.naca_c_start = self._dspin(self.defaults["naca_ant_c_start"], 0, 50, 0.1, 2)
        self.naca_c_end = self._dspin(self.defaults["naca_ant_c_end"], 0, 50, 0.1, 2)
        self.naca_c_step = self._dspin(self.defaults["naca_ant_c_step"], 0.01, 10, 0.05, 3)
        self.naca_t_min = self._dspin(self.defaults["naca_ant_t_min"], 0, 1, 0.01, 3)
        self.naca_t_max = self._dspin(self.defaults["naca_ant_t_max"], 0, 1, 0.01, 3)

        grid.addWidget(QtWidgets.QLabel("NACA C START"), row, 0)
        grid.addWidget(self.naca_c_start, row, 1)
        grid.addWidget(QtWidgets.QLabel("C END"), row, 2)
        grid.addWidget(self.naca_c_end, row, 3)
        grid.addWidget(QtWidgets.QLabel("C STEP"), row, 4)
        grid.addWidget(self.naca_c_step, row, 5)
        row += 1
        grid.addWidget(QtWidgets.QLabel("NACA T MIN"), row, 0)
        grid.addWidget(self.naca_t_min, row, 1)
        grid.addWidget(QtWidgets.QLabel("T MAX"), row, 2)
        grid.addWidget(self.naca_t_max, row, 3)
        row += 1

        # ROTODOMO ranges
        self.roto_c_start = self._dspin(self.defaults["rotodomo_c_start"], 0, 50, 0.1, 2)
        self.roto_c_end = self._dspin(self.defaults["rotodomo_c_end"], 0, 50, 0.1, 2)
        self.roto_c_step = self._dspin(self.defaults["rotodomo_c_step"], 0.01, 10, 0.05, 3)
        self.roto_t_min = self._dspin(self.defaults["rotodomo_t_min"], 0, 1, 0.01, 3)
        self.roto_t_max = self._dspin(self.defaults["rotodomo_t_max"], 0, 1, 0.01, 3)

        grid.addWidget(QtWidgets.QLabel("ROTO C START"), row, 0)
        grid.addWidget(self.roto_c_start, row, 1)
        grid.addWidget(QtWidgets.QLabel("C END"), row, 2)
        grid.addWidget(self.roto_c_end, row, 3)
        grid.addWidget(QtWidgets.QLabel("C STEP"), row, 4)
        grid.addWidget(self.roto_c_step, row, 5)
        row += 1
        grid.addWidget(QtWidgets.QLabel("ROTO T MIN"), row, 0)
        grid.addWidget(self.roto_t_min, row, 1)
        grid.addWidget(QtWidgets.QLabel("T MAX"), row, 2)
        grid.addWidget(self.roto_t_max, row, 3)
        row += 1

        # BEZIER ranges
        self.bez_c_start = self._dspin(self.defaults["bezier_c_start"], 0, 50, 0.1, 2)
        self.bez_c_end = self._dspin(self.defaults["bezier_c_end"], 0, 50, 0.1, 2)
        self.bez_c_step = self._dspin(self.defaults["bezier_c_step"], 0.01, 10, 0.05, 3)
        self.bez_t_min = self._dspin(self.defaults["bezier_t_min"], 0, 1, 0.01, 3)
        self.bez_t_max = self._dspin(self.defaults["bezier_t_max"], 0, 1, 0.01, 3)
        self.bez_sharp = self._line(self.defaults["bezier_sharpness"], "0.1,0.2,...", "Sharpness list 0-1")

        grid.addWidget(QtWidgets.QLabel("BEZ C START"), row, 0)
        grid.addWidget(self.bez_c_start, row, 1)
        grid.addWidget(QtWidgets.QLabel("C END"), row, 2)
        grid.addWidget(self.bez_c_end, row, 3)
        grid.addWidget(QtWidgets.QLabel("C STEP"), row, 4)
        grid.addWidget(self.bez_c_step, row, 5)
        row += 1
        grid.addWidget(QtWidgets.QLabel("BEZ T MIN"), row, 0)
        grid.addWidget(self.bez_t_min, row, 1)
        grid.addWidget(QtWidgets.QLabel("T MAX"), row, 2)
        grid.addWidget(self.bez_t_max, row, 3)
        grid.addWidget(QtWidgets.QLabel("SHARPNESS"), row, 4)
        grid.addWidget(self.bez_sharp, row, 5)

        box.setLayout(grid)
        return box

    def _build_comparison_box(self):
        box = QtWidgets.QGroupBox("COMPARISON / EXPORT")
        form = QtWidgets.QFormLayout()
        self.run_comp_chk = self._chk("RUN COMPARISON", self.defaults["run_comparison"])
        self.metric_combo = QtWidgets.QComboBox()
        self.metric_combo.addItems(["cd_mean", "cd_min", "cl_mean", "clcd_mean", "clcd_max"])
        self.metric_combo.setCurrentText(self.defaults["comparison_metric"])
        self.solver_edit = self._line(self.defaults["comparison_solver"], "su2-incomp", "Filtrar solver (opcional)")
        self.aoa_min_edit = self._line(self.defaults["comparison_aoa_min"], "", "AoA min (opcional)")
        self.aoa_max_edit = self._line(self.defaults["comparison_aoa_max"], "", "AoA max (opcional)")
        self.comp_output_edit = self._line(self.defaults["comparison_output"])
        self.plot_comp_chk = self._chk("PLOT", self.defaults["plot_comparison"])
        self.plot_dir_edit = self._line(self.defaults["plot_dir"], "results/plots")
        self.topn_spin = self._spin(self.defaults["plot_top_n"], 1, 100)

        flags_widget = QtWidgets.QWidget()
        flags_layout = QtWidgets.QHBoxLayout(flags_widget)
        flags_layout.addWidget(self.run_comp_chk)
        flags_layout.addWidget(self.plot_comp_chk)
        flags_layout.addStretch(1)

        form.addRow("COMPARISON FLAGS", flags_widget)
        form.addRow("METRIC", self.metric_combo)
        form.addRow("SOLVER", self.solver_edit)
        form.addRow("AOA MIN/MAX", self._pair(self.aoa_min_edit, self.aoa_max_edit))
        form.addRow("RANKING CSV", self.comp_output_edit)
        form.addRow("PLOT DIR", self.plot_dir_edit)
        form.addRow("PLOT TOP N", self.topn_spin)

        box.setLayout(form)
        return box

    def _pair(self, left: QtWidgets.QWidget, right: QtWidgets.QWidget):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(left)
        layout.addWidget(right)
        return widget

    # -------------------------- parsing --------------------------
    def _parse_list(self, widget: QtWidgets.QLineEdit, name: str, cast=float) -> List[float]:
        raw = widget.text().strip()
        if not raw:
            raise ValueError(f"{name} no puede estar vacío.")
        vals: List[float] = []
        for part in raw.split(","):
            if not part.strip():
                continue
            try:
                vals.append(cast(part.strip()))
            except Exception:
                raise ValueError(f"{name}: valor inválido '{part.strip()}'")
        if not vals:
            raise ValueError(f"{name}: ingrese al menos un valor.")
        return vals

    def _parse_optional_float(self, widget: QtWidgets.QLineEdit) -> float | None:
        raw = widget.text().strip()
        if not raw:
            return None
        try:
            return float(raw)
        except Exception:
            raise ValueError(f"Valor inválido: {raw}")

    def _parse_range(self, start_widget, end_widget, step_widget, name: str):
        start = float(start_widget.value())
        end = float(end_widget.value())
        step = float(step_widget.value())
        if step <= 0:
            raise ValueError(f"{name}: el paso debe ser > 0.")
        if end < start:
            raise ValueError(f"{name}: el final debe ser >= inicio.")
        return (start, end, step)

    def _selected_profile_types(self) -> List[str]:
        selected = [name for name, chk in self.profile_types.items() if chk.isChecked()]
        if not selected:
            selected = ["naca"]
        return selected

    def collect_parameters(self) -> SimulationParameters:
        aoa_list = self._parse_list(self.aoa_edit, "AOA")
        mach_list = self._parse_list(self.mach_edit, "Mach")
        re_list = self._parse_list(self.re_edit, "Reynolds")
        t_list = self._parse_list(self.t_list_edit, "T list")
        c_list = self._parse_list(self.c_list_edit, "C list")
        bezier_sharp = self._parse_list(self.bez_sharp, "Bezier sharpness")

        params = SimulationParameters(
            aoa_list=aoa_list,
            mach_list=mach_list,
            re_list=re_list,
            max_iter=self.max_iter_spin.value(),
            cfl=self._parse_optional_float(self.cfl_edit),
            mesh_file=self.mesh_file_edit.text().strip() or None,
            retries=self.retries_spin.value(),
            compressible=self.compress_chk.isChecked(),
            skip_su2=self.skip_su2_chk.isChecked(),
            skip_aerosb=self.skip_aerosb_chk.isChecked(),
            generate_only=self.generate_only_chk.isChecked(),
            export_csv=self.export_csv_edit.text().strip() or "results/combined_results.csv",
            profile_types=self._selected_profile_types(),
            profiles_output=self.profiles_out_edit.text().strip() or "generated_profiles",
            t_list=t_list,
            c_list=c_list,
            normalize_profiles=self.normalize_chk.isChecked(),
            save_profile_plots=self.plots_chk.isChecked(),
            antenna_length=self.ant_length.value(),
            antenna_height=self.ant_height.value(),
            naca_ant_c_range=self._parse_range(self.naca_c_start, self.naca_c_end, self.naca_c_step, "NACA C range"),
            naca_ant_t_range=(self.naca_t_min.value(), self.naca_t_max.value()),
            naca_ant_pos_count=self.ant_positions.value(),
            rotodomo_c_range=self._parse_range(self.roto_c_start, self.roto_c_end, self.roto_c_step, "Rotodomo C range"),
            rotodomo_t_range=(self.roto_t_min.value(), self.roto_t_max.value()),
            bezier_c_range=self._parse_range(self.bez_c_start, self.bez_c_end, self.bez_c_step, "Bezier C range"),
            bezier_t_range=(self.bez_t_min.value(), self.bez_t_max.value()),
            bezier_sharpness=bezier_sharp,
            run_comparison=self.run_comp_chk.isChecked(),
            comparison_metric=self.metric_combo.currentText(),
            comparison_solver=self.solver_edit.text().strip() or None,
            comparison_aoa_min=self._parse_optional_float(self.aoa_min_edit),
            comparison_aoa_max=self._parse_optional_float(self.aoa_max_edit),
            comparison_output=self.comp_output_edit.text().strip() or "results/airfoil_rankings.csv",
            plot_comparison=self.plot_comp_chk.isChecked(),
            plot_dir=self.plot_dir_edit.text().strip() or None,
            plot_top_n=self.topn_spin.value(),
        )
        return params


def ensure_dir(path_str: str):
    """Creación perezosa para carpetas ingresadas manualmente."""
    if not path_str:
        return
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
