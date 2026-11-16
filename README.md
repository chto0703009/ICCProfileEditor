# ICC Profile Editor

<img src="resources/editor-header.png" alt="ICC Profile Editor app icon" width="72">

A standalone macOS app for editing the internal profile name and copyright in ICC v2 and v4 profiles. Open a profile, edit the fields, and choose **Save Copy**. The app suggests a filename based on the profile name and preserves the source file, color tables, and other ICC tags.

## Install on macOS

Download the universal disk image from [Releases](https://github.com/chto0703009/ICCProfileEditor/releases/latest). It supports both Apple Silicon and Intel Macs and includes Python and Tcl/Tk. Open the disk image and drag **ICC Profile Editor** to **Applications**.

For details on how the app reads, edits, and saves profiles, see the [technical documentation in Swedish](DOKUMENTATION.md).

[Swedish PDF guide](docs/ICC-Profile-Editor-SV.pdf) · [English PDF guide](docs/ICC-Profile-Editor-EN.pdf)

**Open ICC…** starts on the Desktop. The app remembers the last profile and save folders between launches. The first copy defaults to the profile folder.

## Run from source

Use Python 3 with Tkinter.

```sh
python3 icc_profile_editor.py
```

## Build the macOS app

Use Python 3 with Tkinter. Create a separate virtual environment for the build. For a universal build, use a universal2 Python distribution and pass `--target-arch universal2` to PyInstaller.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m PyInstaller --windowed --name 'ICC Profile Editor' --icon resources/Editor.icns \
  --osx-bundle-identifier se.borgasundsfotografiska.iccprofileeditor \
  --add-data resources:resources icc_profile_editor.py
```

The app is built in `dist/`.

## ICC Profile Analyzer

To compare profiles, inspect curves, or export analysis reports, see [ICC Profile Analyzer](https://github.com/chto0703009/ICCProfileAnalyzer) and its [downloads and guides](https://github.com/chto0703009/ICCProfileAnalyzer/releases/latest). Editor uses the Python standard library and Tkinter at runtime.

## License

The source code is licensed under [GNU GPL v3 or later](LICENSE).
