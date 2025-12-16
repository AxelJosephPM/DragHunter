from __future__ import annotations

import sys

from PySide6 import QtWidgets

from gui.main_window import DragHunterMainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = DragHunterMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
