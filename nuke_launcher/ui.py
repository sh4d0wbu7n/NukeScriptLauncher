from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .cache import ProjectCache
from .config import AppConfig, ConfigStore
from .launcher import launch_nuke, reveal_in_file_manager
from .models import ScanResult, ScriptGroup, ScriptVersion
from .scanner import ProjectScanner


APP_STYLE = """
QWidget {
    background: #171a1d;
    color: #e6e9eb;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background: #15181a; }
QFrame#Sidebar { background: #141719; border-right: 1px solid #303438; }
QLabel#AppTitle { font-size: 16pt; font-weight: 600; color: #f1f3f4; }
QLabel#SectionLabel { color: #aeb5ba; font-size: 9pt; font-weight: 600; }
QLabel#Summary { color: #c8cdd0; font-size: 11pt; }
QLabel#Muted { color: #8d969c; }
QLabel#Success { color: #78c96b; }
QLineEdit, QComboBox {
    background: #202428;
    border: 1px solid #3a4045;
    border-radius: 5px;
    padding: 8px 10px;
    min-height: 20px;
    selection-background-color: #416f38;
}
QLineEdit:focus, QComboBox:focus { border-color: #6dbb5d; }
QComboBox::drop-down { border: none; width: 26px; }
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    padding: 2px 0;
}
QListWidget::item { padding: 10px 10px; border-left: 3px solid transparent; }
QListWidget::item:hover { background: #22272a; }
QListWidget::item:selected {
    background: #26342b;
    border-left: 3px solid #70c360;
    color: #ffffff;
}
QTreeWidget {
    background: #1a1e21;
    alternate-background-color: #1d2124;
    border: 1px solid #30353a;
    border-radius: 5px;
    outline: none;
}
QTreeWidget::item { height: 48px; border-bottom: 1px solid #2b3034; }
QTreeWidget::item:selected { background: #26342b; color: #ffffff; }
QTreeWidget::item:hover { background: #22282b; }
QHeaderView::section {
    background: #181c1f;
    color: #aeb5ba;
    border: none;
    border-right: 1px solid #30353a;
    border-bottom: 1px solid #30353a;
    padding: 9px;
    font-size: 9pt;
    font-weight: 600;
}
QPushButton {
    background: #272c30;
    border: 1px solid #41474d;
    border-radius: 5px;
    padding: 7px 12px;
}
QPushButton:hover { background: #31373c; border-color: #596168; }
QPushButton:pressed { background: #202428; }
QPushButton#PrimaryButton {
    background: #356e31;
    border-color: #4f9147;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover { background: #41803b; }
QPushButton#ToggleButton:checked {
    background: #2b4c2b;
    border-color: #5c9e53;
    color: #dff2db;
}
QStatusBar { background: #111315; border-top: 1px solid #2d3236; color: #9ba3a8; }
QSplitter::handle { background: #303438; width: 1px; }
QDialog { background: #191c1f; }
"""


class ProjectListWorker(QObject):
    ready = Signal(list)
    error = Signal(str)
    finished = Signal()

    def __init__(self, base_path: str) -> None:
        super().__init__()
        self.base_path = base_path

    def run(self) -> None:
        try:
            self.ready.emit(ProjectScanner(self.base_path).list_projects())
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class ScanWorker(QObject):
    ready = Signal(object)
    error = Signal(str, str)
    finished = Signal()

    def __init__(self, base_path: str, project: str) -> None:
        super().__init__()
        self.base_path = base_path
        self.project = project

    def run(self) -> None:
        try:
            self.ready.emit(ProjectScanner(self.base_path).scan_project(self.project))
        except Exception as exc:
            self.error.emit(self.project, str(exc))
        finally:
            self.finished.emit()


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(680)
        self._launch_modes = dict(config.launch_modes)

        self.base_edit = QLineEdit(config.base_path)
        self.nuke_edit = QLineEdit(config.nuke_executable)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(config.launch_modes.keys())
        self.mode_combo.setCurrentText(config.default_launch_mode)

        base_row = self._path_row(self.base_edit, self._browse_base)
        nuke_row = self._path_row(self.nuke_edit, self._browse_nuke)

        note = QLabel(
            "Der Base-Ordner ist direkt der Ordner 01_projects. Darunter wird immer "
            "<Projekt>\\work\\<Szene>\\<Shot>\\comp erwartet."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        form.addRow("Base (01_projects)", base_row)
        form.addRow("Nuke-EXE", nuke_row)
        form.addRow("Standard-Startmodus", self.mode_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(buttons)

    @staticmethod
    def _path_row(edit: QLineEdit, callback: object) -> QWidget:
        button = QPushButton("Durchsuchen …")
        button.clicked.connect(callback)  # type: ignore[arg-type]
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return row

    def _browse_base(self) -> None:
        start = self.base_edit.text().strip()
        selected = QFileDialog.getExistingDirectory(self, "01_projects auswählen", start)
        if selected:
            self.base_edit.setText(selected)

    def _browse_nuke(self) -> None:
        start = self.nuke_edit.text().strip()
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Nuke-EXE auswählen",
            start,
            "Programme (*.exe);;Alle Dateien (*)",
        )
        if selected:
            self.nuke_edit.setText(selected)

    def _validate_and_accept(self) -> None:
        if not self.base_edit.text().strip() or not self.nuke_edit.text().strip():
            QMessageBox.warning(self, "Unvollständige Einstellungen", "Base und Nuke-EXE müssen angegeben werden.")
            return
        self.accept()

    def config(self) -> AppConfig:
        return AppConfig(
            base_path=self.base_edit.text().strip(),
            nuke_executable=self.nuke_edit.text().strip(),
            default_launch_mode=self.mode_combo.currentText(),
            launch_modes=self._launch_modes,
        )


class MainWindow(QMainWindow):
    PATH_ROLE = int(Qt.ItemDataRole.UserRole)
    SEARCH_ROLE = PATH_ROLE + 1

    def __init__(self, config_store: ConfigStore | None = None) -> None:
        super().__init__()
        self.config_store = config_store or ConfigStore()
        self.cache = ProjectCache()
        self._threads: set[QThread] = set()
        self._workers: set[QObject] = set()
        self._current_project = ""
        self._current_result: ScanResult | None = None
        self._config_error = ""

        try:
            self.config = self.config_store.load()
        except ValueError as exc:
            self.config = AppConfig()
            self._config_error = str(exc)

        self.setWindowTitle("Nuke Script Launcher")
        self.setMinimumSize(1080, 650)
        self.resize(1440, 820)
        self._build_ui()
        self._apply_config_to_ui()
        QTimer.singleShot(0, self.reload_projects)
        if self._config_error:
            QTimer.singleShot(100, lambda: self._show_config_error(self._config_error))

    def _build_ui(self) -> None:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(APP_STYLE)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 18, 14)
        title = QLabel("Nuke Script Launcher")
        title.setObjectName("AppTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(125)
        self.mode_combo.currentTextChanged.connect(self._mode_changed)
        header_layout.addWidget(QLabel("Startmodus"))
        header_layout.addWidget(self.mode_combo)
        self.settings_button = QPushButton("Einstellungen")
        self.settings_button.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_button)
        root.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #303438;")
        root.addWidget(divider)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main_panel())
        splitter.setSizes([285, 1155])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self.status_message = QLabel("")
        self.status_nuke = QLabel("")
        self.statusBar().addWidget(self.status_message, 1)
        self.statusBar().addPermanentWidget(self.status_nuke)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(230)
        sidebar.setMaximumWidth(390)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        section = QLabel("PROJEKTE")
        section.setObjectName("SectionLabel")
        self.project_filter = QLineEdit()
        self.project_filter.setPlaceholderText("Projekte filtern …")
        self.project_filter.setClearButtonEnabled(True)
        self.project_filter.textChanged.connect(self.filter_projects)

        self.project_list = QListWidget()
        self.project_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.project_list.currentItemChanged.connect(self._project_changed)

        layout.addWidget(section)
        layout.addWidget(self.project_filter)
        layout.addWidget(self.project_list, 1)
        return sidebar

    def _build_main_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 20, 28, 18)
        layout.setSpacing(14)

        self.breadcrumb = QLabel("Kein Projekt ausgewählt")
        self.breadcrumb.setObjectName("Summary")
        layout.addWidget(self.breadcrumb)

        search_row = QHBoxLayout()
        self.script_search = QLineEdit()
        self.script_search.setPlaceholderText("Shot oder Script suchen …")
        self.script_search.setClearButtonEnabled(True)
        self.script_search.textChanged.connect(self.filter_scripts)
        self.refresh_button = QPushButton("Aktualisieren")
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.clicked.connect(self.refresh_current_project)
        search_row.addWidget(self.script_search, 1)
        search_row.addWidget(self.refresh_button)
        layout.addLayout(search_row)

        self.summary = QLabel("Noch keine Scripts geladen")
        self.summary.setObjectName("Summary")
        layout.addWidget(self.summary)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["SZENE / SHOT", "SCRIPT", "VERSION", "GEÄNDERT", "STATUS", "AKTION"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setIndentation(20)
        self.tree.itemDoubleClicked.connect(self._open_item)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tree, 1)

        footer = QHBoxLayout()
        self.older_button = QPushButton("Ältere Versionen anzeigen")
        self.older_button.setObjectName("ToggleButton")
        self.older_button.setCheckable(True)
        self.older_button.toggled.connect(self._toggle_older_versions)
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("Muted")
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.addWidget(self.older_button)
        footer.addStretch(1)
        footer.addWidget(self.warning_label)
        layout.addLayout(footer)
        return panel

    def _apply_config_to_ui(self) -> None:
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItems(self.config.launch_modes.keys())
        self.mode_combo.setCurrentText(self.config.default_launch_mode)
        self.mode_combo.blockSignals(False)
        self._update_status()

    def _update_status(self, message: str | None = None, success: bool = False) -> None:
        if message is None:
            base_ok = Path(self.config.base_path).is_dir()
            message = "Projektpfad erreichbar" if base_ok else "Projektpfad nicht erreichbar"
            success = base_ok
        self.status_message.setText(message)
        self.status_message.setObjectName("Success" if success else "Muted")
        self.status_message.style().unpolish(self.status_message)
        self.status_message.style().polish(self.status_message)
        exe_name = Path(self.config.nuke_executable).stem or "Nuke nicht konfiguriert"
        self.status_nuke.setText(f"{exe_name}  •  {self.mode_combo.currentText()}")

    def _show_config_error(self, message: str) -> None:
        QMessageBox.warning(self, "Konfiguration fehlerhaft", f"{message}\n\nBitte prüfe die Einstellungen.")

    def _start_worker(self, worker: QObject, run_slot: object) -> QThread:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(run_slot)  # type: ignore[arg-type]
        worker.finished.connect(thread.quit)  # type: ignore[attr-defined]
        worker.finished.connect(worker.deleteLater)  # type: ignore[attr-defined]
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._threads.discard(thread))
        thread.finished.connect(lambda: self._workers.discard(worker))
        self._threads.add(thread)
        self._workers.add(worker)
        thread.start()
        return thread

    def reload_projects(self) -> None:
        self.refresh_button.setEnabled(False)
        self._update_status("Projekte werden geladen …")
        worker = ProjectListWorker(self.config.base_path)
        worker.ready.connect(self._projects_loaded)
        worker.error.connect(self._projects_failed)
        self._start_worker(worker, worker.run)

    def _projects_loaded(self, projects: list[str]) -> None:
        previous = self._current_project
        self.project_list.blockSignals(True)
        self.project_list.clear()
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        for project in projects:
            item = QListWidgetItem(folder_icon, project)
            item.setData(Qt.ItemDataRole.UserRole, project)
            self.project_list.addItem(item)
        self.project_list.blockSignals(False)
        self.refresh_button.setEnabled(True)
        self.filter_projects(self.project_filter.text())

        target_row = 0
        if previous:
            matches = self.project_list.findItems(previous, Qt.MatchFlag.MatchExactly)
            if matches:
                target_row = self.project_list.row(matches[0])
        if self.project_list.count():
            self.project_list.setCurrentRow(target_row)
        else:
            self._current_project = ""
            self.tree.clear()
            self.summary.setText("Keine Projekte gefunden")
        self._update_status(success=True)

    def _projects_failed(self, message: str) -> None:
        self.refresh_button.setEnabled(True)
        self.project_list.clear()
        self.tree.clear()
        self.summary.setText("Projektpfad nicht erreichbar")
        self._update_status(message)

    def filter_projects(self, query: str) -> None:
        needle = query.strip().casefold()
        for row in range(self.project_list.count()):
            item = self.project_list.item(row)
            item.setHidden(bool(needle and needle not in item.text().casefold()))

    def _project_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        del previous
        if current is None:
            return
        project = str(current.data(Qt.ItemDataRole.UserRole))
        self._current_project = project
        self.breadcrumb.setText(f"{project}  /  work")
        cached = self.cache.load(self.config.base_path, project)
        if cached:
            self._display_result(cached, cached=True)
        else:
            self.tree.clear()
            self.summary.setText("Scripts werden geladen …")
        self._scan_project(project)

    def refresh_current_project(self) -> None:
        if self._current_project:
            self._scan_project(self._current_project)
        else:
            self.reload_projects()

    def _scan_project(self, project: str) -> None:
        self.refresh_button.setEnabled(False)
        self._update_status(f"{project} wird gescannt …")
        worker = ScanWorker(self.config.base_path, project)
        worker.ready.connect(self._scan_finished)
        worker.error.connect(self._scan_failed)
        worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self._start_worker(worker, worker.run)

    def _scan_finished(self, result: ScanResult) -> None:
        self.cache.save(self.config.base_path, result)
        if result.project == self._current_project:
            self._display_result(result, cached=False)
            self._update_status("Projektpfad erreichbar", success=True)

    def _scan_failed(self, project: str, message: str) -> None:
        if project == self._current_project:
            self.summary.setText("Scan fehlgeschlagen")
            self._update_status(message)

    def _display_result(self, result: ScanResult, cached: bool) -> None:
        self._current_result = result
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        for group in result.groups:
            self._add_group(group)
        self.tree.setUpdatesEnabled(True)
        self.filter_scripts(self.script_search.text())
        suffix = " · Cache wird aktualisiert" if cached else ""
        self.summary.setText(f"{len(result.groups)} aktuelle Scripts{suffix}")
        if result.warnings:
            self.warning_label.setText(f"{len(result.warnings)} Hinweis(e)")
            self.warning_label.setToolTip("\n".join(result.warnings[:25]))
        else:
            self.warning_label.clear()
            self.warning_label.setToolTip("")

    def _add_group(self, group: ScriptGroup) -> None:
        latest = group.latest
        item = self._make_script_item(latest, status="AKTUELL" if latest.is_versioned else "OHNE VERSION")
        self.tree.addTopLevelItem(item)
        self._attach_action_widget(item, latest)
        for older in group.older:
            child = self._make_script_item(older, status="ÄLTER", older=True)
            item.addChild(child)
            self._attach_action_widget(child, older)
            child.setHidden(not self.older_button.isChecked())
        if group.older:
            item.setExpanded(self.older_button.isChecked())

    def _make_script_item(self, script: ScriptVersion, status: str, older: bool = False) -> QTreeWidgetItem:
        first_column = "Ältere Version" if older else f"{script.scene} / {script.shot}"
        item = QTreeWidgetItem(
            [
                first_column,
                script.base_name,
                script.version_label,
                self._format_date(script.modified_at),
                status,
                "",
            ]
        )
        item.setData(0, self.PATH_ROLE, str(script.path))
        search_blob = " ".join(
            [script.project, script.scene, script.shot, script.base_name, script.path.name, script.version_label]
        ).casefold()
        item.setData(0, self.SEARCH_ROLE, search_blob)
        if status == "AKTUELL":
            item.setForeground(2, QColor("#7dcc70"))
            item.setForeground(4, QColor("#7dcc70"))
            font = QFont(item.font(4))
            font.setBold(True)
            item.setFont(4, font)
        elif status == "OHNE VERSION":
            item.setForeground(4, QColor("#e7b45b"))
        else:
            for column in range(5):
                item.setForeground(column, QColor("#9aa2a7"))
        item.setToolTip(1, str(script.path))
        return item

    def _attach_action_widget(self, item: QTreeWidgetItem, script: ScriptVersion) -> None:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        open_button = QPushButton("In Nuke öffnen")
        open_button.setObjectName("PrimaryButton")
        open_button.setMinimumWidth(125)
        open_button.clicked.connect(lambda checked=False, path=script.path: self.open_script(path))
        folder_button = QPushButton()
        folder_button.setToolTip("Im Explorer anzeigen")
        folder_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        folder_button.setFixedSize(QSize(36, 32))
        folder_button.clicked.connect(lambda checked=False, path=script.path: self.reveal_script(path))
        layout.addWidget(open_button)
        layout.addWidget(folder_button)
        self.tree.setItemWidget(item, 5, container)

    @staticmethod
    def _format_date(timestamp: float | None) -> str:
        if timestamp is None:
            return "—"
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")

    def filter_scripts(self, query: str) -> None:
        needle = query.strip().casefold()
        show_older = self.older_button.isChecked()
        visible_count = 0
        for row in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(row)
            parent_match = not needle or needle in str(parent.data(0, self.SEARCH_ROLE))
            child_match = False
            for child_row in range(parent.childCount()):
                child = parent.child(child_row)
                matches = not needle or needle in str(child.data(0, self.SEARCH_ROLE))
                child_match = child_match or matches
                child.setHidden(not show_older or not matches)
            visible = parent_match or (show_older and child_match)
            parent.setHidden(not visible)
            parent.setExpanded(show_older and visible and parent.childCount() > 0)
            if visible:
                visible_count += 1
        if self._current_result is not None:
            self.summary.setText(f"{visible_count} von {len(self._current_result.groups)} Scripts")

    def _toggle_older_versions(self, enabled: bool) -> None:
        self.older_button.setText("Ältere Versionen ausblenden" if enabled else "Ältere Versionen anzeigen")
        self.filter_scripts(self.script_search.text())

    def _open_item(self, item: QTreeWidgetItem, column: int) -> None:
        del column
        path = item.data(0, self.PATH_ROLE)
        if path:
            self.open_script(Path(str(path)))

    def open_script(self, path: Path) -> None:
        mode = self.mode_combo.currentText()
        try:
            launch_nuke(self.config, mode, path)
        except Exception as exc:
            QMessageBox.critical(self, "Nuke konnte nicht gestartet werden", str(exc))
            return
        self._update_status(f"{path.name} wird in {mode} geöffnet …", success=True)

    def reveal_script(self, path: Path) -> None:
        try:
            reveal_in_file_manager(path)
        except Exception as exc:
            QMessageBox.warning(self, "Explorer konnte nicht geöffnet werden", str(exc))

    def _mode_changed(self, mode: str) -> None:
        if not mode:
            return
        self.config.default_launch_mode = mode
        try:
            self.config_store.save(self.config)
        except OSError as exc:
            self._update_status(f"Startmodus konnte nicht gespeichert werden: {exc}")
        self._update_status()

    def open_settings(self) -> None:
        old_base = self.config.base_path
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_config = dialog.config()
        try:
            self.config_store.save(new_config)
        except OSError as exc:
            QMessageBox.critical(self, "Einstellungen konnten nicht gespeichert werden", str(exc))
            return
        self.config = new_config
        self._apply_config_to_ui()
        if old_base != new_config.base_path:
            self._current_project = ""
            self._current_result = None
            self.tree.clear()
            self.reload_projects()
        else:
            self._update_status()

    def closeEvent(self, event: QCloseEvent) -> None:
        for thread in list(self._threads):
            thread.quit()
        for thread in list(self._threads):
            thread.wait(2000)
        super().closeEvent(event)


def run_app() -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Nuke Script Launcher")
    app.setOrganizationName("VFX Tools")
    window = MainWindow()
    window.show()
    return app.exec()
