"""QObject exposed to QML: job queue + settings."""
from __future__ import annotations

# droopy:feature delete begin
import shutil
import subprocess
# droopy:feature delete end
from pathlib import Path
from typing import Any

from PySide6.QtCore import (Property, QAbstractListModel, QModelIndex, QObject,
                            Qt, QThread, QUrl, Signal, Slot)
from PySide6.QtGui import QDesktopServices

from . import core
from .settings import Store
from .worker import Worker


class JobModel(QAbstractListModel):
    _FIELDS = ["jobId", "name", "source", "sourceDir", "output", "progress", "status", "message"]
    ROLE = {Qt.UserRole + 1 + i: f.encode() for i, f in enumerate(_FIELDS)}

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = []

    def roleNames(self):  # noqa: N802
        return self.ROLE

    def rowCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.rows)):
            return None
        name = self.ROLE.get(role)
        return self.rows[index.row()].get(name.decode()) if name else None

    def append(self, row: dict[str, Any]) -> None:
        self.beginInsertRows(QModelIndex(), len(self.rows), len(self.rows))
        self.rows.append(row)
        self.endInsertRows()

    def find(self, job_id: int) -> int:
        for i, r in enumerate(self.rows):
            if r["jobId"] == job_id:
                return i
        return -1

    def update(self, job_id: int, **fields: Any) -> None:
        i = self.find(job_id)
        if i < 0:
            return
        self.rows[i].update(fields)
        idx = self.index(i)
        roles = [r for r, n in self.ROLE.items() if n.decode() in fields]
        self.dataChanged.emit(idx, idx, roles)

    def remove_where(self, pred) -> None:
        for i in range(len(self.rows) - 1, -1, -1):
            if pred(self.rows[i]):
                self.beginRemoveRows(QModelIndex(), i, i)
                del self.rows[i]
                self.endRemoveRows()


class Backend(QObject):
    settingsChanged = Signal()
    stateChanged = Signal()
    # droopy:feature delete begin
    pendingDeleteChanged = Signal()
    # droopy:feature delete end
    # droopy:feature history begin
    historyChanged = Signal()
    # droopy:feature history end
    toast = Signal(str)
    _startJob = Signal(int, str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.store = Store()
        self.model = JobModel()
        self._next_id = 1
        self._running: int | None = None
        # droopy:feature delete begin
        self._pending: list[dict[str, str]] = []
        self._session_choice: str | None = None  # "yes" | "no" for the current batch
        # droopy:feature delete end

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self._startJob.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.thread.start()

    # ------------------------------------------------------------------ lifecycle
    def shutdown(self) -> None:
        self.worker.cancel_event.set()
        self.thread.quit()
        self.thread.wait(5000)

    # ------------------------------------------------------------------ properties
    @Property("QVariantMap", notify=settingsChanged)
    def settings(self):
        return dict(self.store.data)

    @Property(QObject, constant=True)
    def jobs(self):
        return self.model

    @Property(float, notify=stateChanged)
    def overallProgress(self):  # noqa: N802
        rows = self.model.rows
        if not rows:
            return 0.0
        return sum(1.0 if r["status"] in ("done", "error", "skipped") else r["progress"]
                   for r in rows) / len(rows)

    @Property(bool, notify=stateChanged)
    def busy(self):
        return any(r["status"] in ("queued", "working") for r in self.model.rows)

    @Property(int, notify=stateChanged)
    def jobCount(self):  # noqa: N802
        return len(self.model.rows)

    @Property(int, notify=stateChanged)
    def doneCount(self):  # noqa: N802
        return sum(1 for r in self.model.rows if r["status"] in ("done", "error", "skipped"))

    @Property(str, notify=stateChanged)
    def mascotState(self):  # noqa: N802
        rows = self.model.rows
        if any(r["status"] in ("queued", "working") for r in rows):
            return "working"
        if any(r["status"] == "error" for r in rows):
            return "error"
        if any(r["status"] == "done" for r in rows):
            return "done"
        return "idle"

    # droopy:feature delete begin
    @Property(bool, notify=pendingDeleteChanged)
    def hasPendingDelete(self):  # noqa: N802
        return bool(self._pending)

    @Property("QVariantMap", notify=pendingDeleteChanged)
    def pendingDelete(self):  # noqa: N802
        if not self._pending:
            return {"name": "", "source": "", "output": "", "count": 0}
        p = self._pending[0]
        return {**p, "count": len(self._pending)}
    # droopy:feature delete end

    # droopy:feature history begin
    @Property("QVariantList", notify=historyChanged)
    def history(self):
        out = []
        for h in reversed(self.store.history[-100:]):
            s = Path(h["source"])
            out.append({"name": s.name, "sourceDir": str(s.parent), "output": h["output"],
                        "status": h["status"], "time": h["time"]})
        return out
    # droopy:feature history end

    # ------------------------------------------------------------------ settings
    @Slot(str, "QVariant")
    def setSetting(self, key: str, value: Any) -> None:  # noqa: N802
        if self.store.set(key, value):
            self.settingsChanged.emit()

    # ------------------------------------------------------------------ queue
    @Slot("QVariantList")
    def addUrls(self, urls: list) -> None:  # noqa: N802
        paths: list[str] = []
        for u in urls:
            s = u.toLocalFile() if isinstance(u, QUrl) else QUrl(str(u)).toLocalFile() or str(u)
            if s:
                paths.append(s)
        self.addPaths(paths)

    def addPaths(self, paths: list[str]) -> None:  # noqa: N802
        if not paths:
            return
        # droopy:feature delete begin
        if not self.busy:
            self._session_choice = None
        # droopy:feature delete end
        items = core.expand_inputs(paths)
        if not items:
            self.toast.emit("__NOTHING_MSG__")
            return
        first_parent = str(Path(paths[0]).parent)
        self.store.set("lastDir", first_parent)
        self.settingsChanged.emit()
        for p in items:
            self.model.append({
                "jobId": self._next_id, "name": p.name, "source": str(p),
                "sourceDir": str(p.parent), "output": "", "progress": 0.0,
                "status": "queued", "message": "Waiting…",
            })
            self._next_id += 1
        self.stateChanged.emit()
        self._pump()

    @Slot(int)
    def removeJob(self, job_id: int) -> None:  # noqa: N802
        i = self.model.find(job_id)
        if i >= 0 and self.model.rows[i]["status"] != "working":
            self.model.remove_where(lambda r: r["jobId"] == job_id)
            self.stateChanged.emit()

    @Slot()
    def clearFinished(self) -> None:  # noqa: N802
        self.model.remove_where(lambda r: r["status"] in ("done", "error", "skipped"))
        self.stateChanged.emit()

    # droopy:feature retry begin
    @Slot()
    def retryFailed(self) -> None:  # noqa: N802
        for r in self.model.rows:
            if r["status"] == "error":
                self.model.update(r["jobId"], status="queued", progress=0.0, output="", message="Waiting…")
        self.stateChanged.emit()
        self._pump()
    # droopy:feature retry end

    def _out_dir_for(self, src: str) -> str:
        s = self.store.data
        if s["outputMode"] == "custom" and s["customDir"]:
            return s["customDir"]
        return str(Path(src).parent)  # next to where it came from

    def _pump(self) -> None:
        if self._running is not None:
            return
        for r in self.model.rows:
            if r["status"] == "queued":
                self._running = r["jobId"]
                s = self.store.data
                self.model.update(r["jobId"], status="working", message="Starting…")
                self.stateChanged.emit()
                opts = {k: s[k] for k in core.OPTION_DEFAULTS}
                opts.update({"outDir": self._out_dir_for(r["source"]), "overwrite": s["overwrite"]})
                self._startJob.emit(r["jobId"], r["source"], opts)
                return
        self.stateChanged.emit()

    @Slot(int, float, str)
    def _on_progress(self, job_id: int, frac: float, msg: str) -> None:
        self.model.update(job_id, progress=frac, message=msg)
        self.stateChanged.emit()

    @Slot(int, str, str, str, bool)
    def _on_finished(self, job_id: int, status: str, output: str, message: str, in_place: bool) -> None:
        i = self.model.find(job_id)
        self._running = None
        if i >= 0:
            row = self.model.rows[i]
            self.model.update(job_id, status=status, output=output, message=message,
                              progress=1.0 if status != "error" else row["progress"])
            # droopy:feature history begin
            self.store.add_history(row["source"], output, status)
            self.historyChanged.emit()
            # droopy:feature history end
            # droopy:feature delete begin
            if status == "done" and not in_place:
                self._after_success(row["name"], row["source"], output, job_id)
            # droopy:feature delete end
        self.stateChanged.emit()
        self._pump()

    # droopy:feature delete begin
    # ------------------------------------------------------------------ deletion
    def _after_success(self, name: str, source: str, output: str, job_id: int) -> None:
        mode = self.store.data["deleteMode"]
        if mode == "never" or self._session_choice == "no":
            return
        if mode == "always" or self._session_choice == "yes":
            self._delete(source, output, job_id)
            return
        self._pending.append({"name": name, "source": source, "output": output, "jobId": str(job_id)})
        self.pendingDeleteChanged.emit()

    @Slot(str)
    def answerDelete(self, choice: str) -> None:  # noqa: N802
        """choice: yes | no | yesAll | noAll"""
        if not self._pending:
            return
        item = self._pending.pop(0)
        if choice in ("yes", "yesAll"):
            self._delete(item["source"], item["output"], int(item["jobId"]))
        if choice == "yesAll":
            self._session_choice = "yes"
            for p in self._pending:
                self._delete(p["source"], p["output"], int(p["jobId"]))
            self._pending.clear()
        elif choice == "noAll":
            self._session_choice = "no"
            self._pending.clear()
        self.pendingDeleteChanged.emit()

    def _delete(self, source: str, output: str, job_id: int) -> None:
        src, out = Path(source), Path(output)
        # Safety net: never delete unless the new file really exists and is non-empty.
        try:
            if not out.exists() or (out.is_file() and out.stat().st_size == 0) or out.resolve() == src.resolve():
                self.toast.emit("Kept the original - output looks wrong")
                return
        except OSError:
            return
        try:
            if self.store.data["useTrash"]:
                subprocess.run(["gio", "trash", str(src)], check=True,
                               capture_output=True, timeout=60)
                note = "Original moved to trash"
            else:
                shutil.rmtree(src) if src.is_dir() else src.unlink()
                note = "Original deleted"
            self.model.update(job_id, message=note)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or b"").decode(errors="replace").strip() or str(exc)
            self.toast.emit(f"Could not trash original: {detail}")
        except (OSError, subprocess.SubprocessError) as exc:
            self.toast.emit(f"Could not remove original: {exc}")
    # droopy:feature delete end

    # ------------------------------------------------------------------ misc
    @Slot(str)
    def reveal(self, path: str) -> None:
        if not path:
            return
        p = Path(path)
        target = p.parent if p.is_file() or not p.exists() else p
        if not target.exists():
            target = target.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    # droopy:feature history begin
    @Slot()
    def clearHistory(self) -> None:  # noqa: N802
        self.store.clear_history()
        self.historyChanged.emit()
    # droopy:feature history end

    @Slot(str, result=str)
    def toLocalPath(self, url: str) -> str:  # noqa: N802
        return QUrl(url).toLocalFile()
