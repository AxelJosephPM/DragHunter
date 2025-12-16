from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Dict

from PySide6 import QtWidgets

try:  # matplotlib es opcional
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - dependencia opcional
    FigureCanvas = None
    plt = None


class ResultViewer(QtWidgets.QWidget):
    """Tabla + plot rápido a partir del CSV combinado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: List[Dict[str, str]] = []
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.status_label = QtWidgets.QLabel("RESULT VIEWER")
        layout.addWidget(self.status_label)

        self.table = QtWidgets.QTableWidget(0, 0)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, stretch=2)

        if FigureCanvas and plt:
            self.fig, self.ax = plt.subplots(figsize=(5, 3))
            self.canvas = FigureCanvas(self.fig)
            layout.addWidget(self.canvas, stretch=1)
        else:
            self.fig = None
            self.ax = None
            self.canvas = None
            layout.addWidget(QtWidgets.QLabel("Matplotlib no disponible: solo tabla."))

    def load_from_csv(self, path: Path):
        if not path or not path.exists():
            self.status_label.setText(f"CSV no encontrado: {path}")
            self.table.clear()
            return
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            self.rows = [row for row in reader]
        if not self.rows:
            self.status_label.setText(f"CSV vacío: {path}")
            self.table.clear()
            return

        headers = reader.fieldnames or list(self.rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        max_rows = min(len(self.rows), 400)
        self.table.setRowCount(max_rows)
        for i, row in enumerate(self.rows[:max_rows]):
            for j, h in enumerate(headers):
                item = QtWidgets.QTableWidgetItem(str(row.get(h, "")))
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"{path} ({len(self.rows)} filas)")
        self._update_plot()

    def _update_plot(self):
        if not self.canvas or not self.rows:
            return
        self.ax.clear()
        solvers = {}
        for r in self.rows:
            solver = r.get("solver", "unknown")
            try:
                cd = float(r.get("CD", 0))
                cl = float(r.get("CL", 0))
            except Exception:
                continue
            solvers.setdefault(solver, {"cd": [], "cl": []})
            solvers[solver]["cd"].append(cd)
            solvers[solver]["cl"].append(cl)
        for solver, data in solvers.items():
            self.ax.scatter(data["cd"], data["cl"], label=solver, s=18)
        self.ax.set_xlabel("CD")
        self.ax.set_ylabel("CL")
        self.ax.grid(True, linestyle="--", alpha=0.3)
        self.ax.legend(fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()
