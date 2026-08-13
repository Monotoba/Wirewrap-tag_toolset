# Contributing

Contributions are welcome, especially fixes that improve dimensional accuracy, print reliability, accessibility, or the everyday design workflow.

## Development setup

Linux and macOS:

```bash
./scripts/setup.sh
./scripts/test.sh -q
```

Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\test.ps1 -q
```

Run the GUI during development with:

```bash
./scripts/run.sh
```

On Windows, run `.\scripts\run.ps1`.

## Before submitting a change

- Keep geometry and file-generation logic in `src/wirewrap_tag_designer/core.py` when it does not require Qt.
- Preserve the simple main-screen workflow; advanced controls belong in the settings dialog.
- Add or update tests for geometry, page layout, SVG, or OpenSCAD changes.
- Run `./scripts/check.sh` and `git diff --check`.
- On Windows, run `.\scripts\check.ps1` and `git diff --check`.
- Describe any physical print or fit testing performed.

Small, focused changes are easiest to review. Bug reports should include the pin count, device width, relevant settings, operating system, and generated file type.
