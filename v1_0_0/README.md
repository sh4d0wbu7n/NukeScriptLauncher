# Nuke Script Launcher

Ein kompakter Windows-Launcher für Nuke-Scripts in einer festen Produktionsstruktur. Er zeigt standardmäßig nur die höchste numerische Version eines Scripts und kann ältere Versionen bei Bedarf einblenden.

## Erwartete Ordnerstruktur

Der konfigurierte Base-Pfad zeigt direkt auf `01_projects`:

```text
01_projects
└── <Projekt>
    └── work
        └── <Szene>
            └── <Shot>
                └── comp
                    ├── <name>_v001.nk
                    └── <name>_v002.nk
```

Beispiel:

```text
\\192.168.70.10\BackupKI\production\01_projects\helendorn\work\SC0026\S0120\comp\helendorn_SC0026_S0120_v002.nk
```

## Funktionen

- Projekte aus der ersten Ebene des Base-Ordners
- Hintergrundscan nur für das ausgewählte Projekt
- Aktuelle Version über die höchste `_v###`-Nummer
- Dynamische Suche nach Szene, Shot, Scriptname und Version
- Ein- und Ausblenden älterer Versionen
- Start in Nuke oder NukeX
- Öffnen des Speicherorts im Windows Explorer
- Konfigurationsdialog und direkt editierbare `config.json`
- Lokaler Projektcache für eine schnelle erste Anzeige
- Fehleranzeige bei nicht erreichbaren Netzpfaden

## Konfiguration

Die Datei `config.json` liegt neben `app.py` beziehungsweise neben der gebauten EXE:

```json
{
  "base_path": "\\\\192.168.70.10\\BackupKI\\production\\01_projects",
  "nuke_executable": "C:\\Program Files\\Nuke14.0v5\\Nuke14.0.exe",
  "default_launch_mode": "NukeX",
  "launch_modes": {
    "Nuke": [],
    "NukeX": ["--nukex"]
  }
}
```

Die gleichen Werte können über **Einstellungen** in der Anwendung geändert werden. Beim Wechsel auf eine andere Nuke-Version muss nur `nuke_executable` angepasst werden.

## Portable Windows-Version bauen

Voraussetzung für den einmaligen Build ist Python 3.11 oder 3.12 für Windows. Danach:

1. `build_windows.bat` doppelklicken.
2. Das Skript erstellt eine isolierte `.venv`, installiert PySide6 und PyInstaller und führt die Tests aus.
3. Die fertige Anwendung liegt unter:

```text
dist\NukeScriptLauncher\NukeScriptLauncher.exe
```

Der komplette Ordner `dist\NukeScriptLauncher` kann ohne Installation kopiert oder auf einem Fileserver bereitgestellt werden. Die EXE sollte nicht einzeln aus diesem Ordner herauskopiert werden, weil die Qt-Abhängigkeiten im Unterordner `_internal` liegen.

## Aus dem Quellcode starten

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Danach kann auch `start_source.bat` verwendet werden.

## Versionsregeln

Die aktuelle Version wird ausschließlich aus dem Suffix `_v` plus Zahl ermittelt. `_v10` und `_v010` werden beide als Version 10 verstanden. Das Änderungsdatum entscheidet nicht über die aktuelle Version.

Scripts ohne lesbare Versionsnummer werden mit **OHNE VERSION** markiert. Sie werden nicht automatisch mit nummerierten Versionen zusammengeführt.
