from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from gui.parameters import SimulationParameters
from gui.styles.palette import Colors, build_stylesheet
from gui.widgets.log_console import LogConsole
from gui.widgets.parameter_panel import ParameterPanel
from gui.widgets.result_viewer import ResultViewer


class RunnerThread(QtCore.QThread):
    line = QtCore.Signal(str)
    finished = QtCore.Signal(int)
    errored = QtCore.Signal(str)

    def __init__(self, cmd, workdir: Path):
        super().__init__()
        self.cmd = cmd
        self.workdir = workdir
        self.process: subprocess.Popen | None = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if self.process.stdout:
                for line in self.process.stdout:
                    self.line.emit(line.rstrip("\n"))
            self.process.wait()
            self.finished.emit(self.process.returncode or 0)
        except Exception as e:  # pragma: no cover - defensivo
            self.errored.emit(str(e))
            self.finished.emit(-1)

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass


class DragHunterMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo_root = Path(__file__).resolve().parent.parent
        self.setWindowTitle("DragHunter Control - Akira Ops Console")
        self.setMinimumSize(1300, 780)
        self.setStyleSheet(build_stylesheet())

        self.worker: RunnerThread | None = None
        self.current_params: SimulationParameters | None = None

        self._build_ui()

    # -------------------- UI --------------------
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        main_layout.addWidget(self._build_header())
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setHandleWidth(2)
        main_layout.addWidget(splitter, stretch=1)

        # left: parameters (scrollable)
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        self.param_panel = ParameterPanel()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.param_panel)
        left_layout.addWidget(scroll)
        splitter.addWidget(left_widget)

        # right: console + results
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(self._build_controls_bar())

        self.tab = QtWidgets.QTabWidget()
        self.log_console = LogConsole()
        self.results = ResultViewer()
        self.tab.addTab(self.log_console, "CONSOLE")
        self.tab.addTab(self.results, "RESULTS")
        right_layout.addWidget(self.tab, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)

    def _build_header(self):
        header = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QtWidgets.QLabel("DRAGHUNTER OPS // AKIRA PANEL")
        title.setStyleSheet(f"color: {Colors.ACCENT_CYAN}; font-size: 14px; font-weight: 800;")
        layout.addWidget(title)

        self.status_led = QtWidgets.QLabel(" IDLE ")
        self.status_led.setAlignment(QtCore.Qt.AlignCenter)
        self.status_led.setFixedWidth(120)
        self._set_status("IDLE")
        layout.addWidget(self.status_led)
        layout.addStretch(1)
        return header

    def _build_controls_bar(self):
        bar = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.run_btn = QtWidgets.QPushButton("RUN / EXECUTE")
        self.run_btn.setObjectName("runButton")
        self.run_btn.clicked.connect(self.start_run)

        self.stop_btn = QtWidgets.QPushButton("STOP")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_run)
        self.stop_btn.setEnabled(False)

        self.command_preview = QtWidgets.QLineEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setPlaceholderText("python main.py ...")

        layout.addWidget(self.run_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(QtWidgets.QLabel("COMMAND"))
        layout.addWidget(self.command_preview, stretch=1)
        return bar

    # -------------------- run logic --------------------
    def _set_status(self, status: str):
        status = status.upper()
        if status == "RUNNING":
            color = Colors.ACCENT_RED
        elif status == "ERROR":
            color = Colors.ACCENT_RED
        elif status == "DONE":
            color = Colors.ACCENT_GREEN
        else:
            color = Colors.ACCENT_CYAN
            status = "IDLE"
        self.status_led.setText(f" {status} ")
        self.status_led.setStyleSheet(
            f"background-color:{Colors.PANEL}; border:1px solid {color}; color:{color}; font-weight:800;"
        )

    def start_run(self):
        if self.worker and self.worker.isRunning():
            QtWidgets.QMessageBox.warning(self, "RUNNING", "Ya hay un job en ejecución.")
            return
        try:
            params = self.param_panel.collect_parameters()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid input", str(e))
            return

        self.current_params = params
        cmd = params.to_cli_args()
        self.command_preview.setText(" ".join(cmd))
        self.log_console.clear_console()
        self._set_status("RUNNING")
        self.stop_btn.setEnabled(True)
        self.run_btn.setEnabled(False)

        self.worker = RunnerThread(cmd, self.repo_root)
        self.worker.line.connect(self.log_console.append_line)
        self.worker.finished.connect(self._on_finish)
        self.worker.errored.connect(self._on_error)
        self.worker.start()

    def stop_run(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_console.append_line("[CTRL] Solicitud de parada enviada.")
        self._set_status("IDLE")
        self.stop_btn.setEnabled(False)
        self.run_btn.setEnabled(True)

    def _on_error(self, msg: str):
        self.log_console.append_line(f"[ERROR] {msg}")
        self._set_status("ERROR")

    def _on_finish(self, code: int):
        if code == 0:
            self._set_status("DONE")
            self.log_console.append_line("[OK] Pipeline completado.")
            if self.current_params:
                self.results.load_from_csv(self.repo_root / self.current_params.export_path)
        else:
            self._set_status("ERROR")
            self.log_console.append_line(f"[FAIL] Código de retorno {code}")
        self.stop_btn.setEnabled(False)
        self.run_btn.setEnabled(True)


def launch():
    app = QtWidgets.QApplication(sys.argv)
    window = DragHunterMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch()
