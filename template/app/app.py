"""Qt Quick bootstrap."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .backend import Backend

ROOT = Path(__file__).resolve().parent.parent


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    QCoreApplication.setApplicationName("__APP_NAME__")
    QCoreApplication.setOrganizationName("__APP_NAME__")
    QQuickStyle.setStyle("Basic")  # fully custom-styled controls
    app = QGuiApplication(argv)
    app.setDesktopFileName("__APP_ID__")
    icon = ROOT / "packaging" / "__APP_ID__.svg"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    backend = Backend()
    app.aboutToQuit.connect(backend.shutdown)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qml" / "Main.qml")))
    if not engine.rootObjects():
        return 1

    # Files passed on the command line (droplet / "Open with") are queued right away.
    cli = [a for a in argv[1:] if not a.startswith("-")]
    if cli:
        backend.addPaths(cli)
    rc = app.exec()
    # Tear the engine down while `backend` is still alive, otherwise bindings
    # re-evaluate against a null context object and spam TypeErrors on exit.
    del engine
    return rc
