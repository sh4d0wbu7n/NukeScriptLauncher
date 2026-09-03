# Nuke Script Launcher 2.0.0

A compact Windows launcher for Nuke scripts and QuickTime shot previews. It scans a fixed production folder structure, shows only the highest numeric version by default, and lets artists reveal older versions when needed.

## Expected folder structure

The configured base path must point directly to `01_projects`:

```text
01_projects
└── <Project>
    └── work
        └── <Scene>
            └── <Shot>
                ├── comp
                │   ├── <project>_<scene>_<shot>_v001.nk
                │   └── <project>_<scene>_<shot>_v002.nk
                └── _OUT
                    └── PREVIEW
                        ├── <project>_<scene>_<shot>_v001
                        │   └── <project>_<scene>_<shot>_v001_preview.mov
                        └── <project>_<scene>_<shot>_v002
                            └── <project>_<scene>_<shot>_v002_preview.mov
```

Example preview:

```text
Z:\production\01_projects\grenzgaenger\work\SC0001\S0391\_OUT\PREVIEW\grenzgaenger_SC0001_S0391_v001\grenzgaenger_SC0001_S0391_v001_preview.mov
```

## Features

- Projects are loaded from the first level below the base folder.
- Only the selected project is scanned, using a background worker.
- Nuke scripts and QuickTime previews are presented on separate tabs.
- The current version is determined by the highest numeric `_v###` suffix.
- Current script and preview versions are compared in the STATUS column.
- Older script and preview versions can be revealed independently.
- The selected project refreshes automatically every 60 seconds by default.
- Live search covers project, scene, shot, filename, and version.
- Scripts can be launched in either Nuke or NukeX.
- MOV previews open in the default Windows video application.
- Any listed file can be revealed in Windows Explorer.
- Settings and `config.json` can change the base path and Nuke executable.
- A local per-project cache provides a fast initial display.
- Network and filename problems are reported without freezing the interface.

## Configuration

`config.json` is located next to `app.py` or the built executable:

```json
{
  "base_path": "\\\\192.168.70.10\\BackupKI\\production\\01_projects",
  "nuke_executable": "C:\\Program Files\\Nuke14.0v5\\Nuke14.0.exe",
  "default_launch_mode": "NukeX",
  "auto_refresh_seconds": 60,
  "launch_modes": {
    "Nuke": [],
    "NukeX": ["--nukex"]
  }
}
```

The same values can be changed through **Settings**. To move to another Nuke release, change only `nuke_executable`. Set `auto_refresh_seconds` to `0` to disable automatic refresh.

## Version status

The STATUS column compares assets with the same project, scene, shot, and base filename:

- `IN SYNC`: current script and preview have the same version.
- `MISMATCH · Preview v003`: the current script has a different preview version.
- `MISMATCH · Script v002`: the current preview has a different script version.
- `NO PREVIEW` or `NO SCRIPT`: the counterpart does not exist.
- `NO VERSION`: the filename does not contain a recognized version number.

## Build the portable Windows version

Use a standard 64-bit Python installation. Python 3.13 is supported.

1. Double-click `build_windows.bat`.
2. The script creates an isolated `.venv`, installs PySide6 and PyInstaller, and runs all tests.
3. The finished application is created at:

```text
dist\NukeScriptLauncher\NukeScriptLauncher.exe
```

The complete `dist\NukeScriptLauncher` folder is portable. Do not copy the EXE by itself because the required Qt files are stored in `_internal`.

After a successful build, `.venv`, `build`, and the generated `.spec` file are no longer needed. Keep the source folder only if you want to build another version later.

## Run from source

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Afterwards, `start_source.bat` can be used.

## Version rules

Script versions must end in `_v` plus a number before `.nk`:

```text
grenzgaenger_SC0001_S0391_v012.nk
```

Preview versions must end in `_v` plus a number and `_preview.mov`:

```text
grenzgaenger_SC0001_S0391_v012_preview.mov
```

`_v10` and `_v010` are both interpreted as version 10. Modification dates never decide which file is current. Files without a recognized version are marked **NO VERSION** and are not silently merged with numbered versions.
