from __future__ import annotations

from PySide6 import QtGui, QtWidgets


class LogConsole(QtWidgets.QPlainTextEdit):
    """Consola de logs con estilo técnico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.document().setMaximumBlockCount(2000)
        self.setPlaceholderText("LOG OUTPUT")

    def append_line(self, text: str):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text.rstrip("\n") + "\n")
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_console(self):
        self.clear()
