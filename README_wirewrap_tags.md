# Wire-Wrap Tag Designer

A PySide6 desktop app for creating matching, printable wire-wrap socket labels and 3D-printable tags.

The startup screen keeps the normal job deliberately short:

1. Enter the device/part ID.
2. Set the even DIP pin count.
3. Choose the pin-row width (300, 400, 600, or 900 mil).
4. Click **Generate label + printable page + STL**.

The app shows live previews of the label, the print sheet, and an isometric tag model. The generated OpenSCAD/STL geometry uses the same pin pitch, holes, width, length, and margins as the label.

## Run it

Python 3.10 or later is recommended.

Linux and macOS:

```bash
./scripts/setup.sh
./scripts/run.sh
```

Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

Or activate the generated environment and run the installed command:

```bash
source .venv/bin/activate
wirewrap-tag-designer
```

OpenSCAD is optional for using the app, but required to produce the final STL. Without it, the app still exports the label, print sheet, PDF, and editable `.scad` model.

## Generated files

For a part called `IC12`, **Generate** creates:

- `IC12_label.svg` — one label at exact physical size
- `IC12_letter_sheet.svg` — labels laid out on a Letter sheet (A4 is also available)
- `IC12_letter_sheet.pdf` — ready to print at 100% / Actual Size
- `IC12_tag.scad` — editable parametric model
- `IC12_tag.stl` — ready to slice, when OpenSCAD is installed
- `IC12_settings.json` — a record of every setting used

If the requested number of labels exceeds one sheet, numbered SVG sheets and a multi-page PDF are generated.

> Print the PDF with **Actual Size** or **100%** selected. Disable “Fit to page” scaling.

## Common and advanced controls

Part ID, pin count, device width, and output folder stay on the main screen. **Design & print settings** contains the controls that are useful less often:

- label width beyond each pin row
- label extension beyond the top and bottom pins
- pin pitch and hole diameter
- pin-number distance from the inside hole edge and number size
- part-ID orientation, size, horizontal/vertical position, and font
- label, outline, pin-number, and part-ID colors
- notch and corner dimensions
- 3D tag thickness and optional center window
- custom A4/Letter grids or Avery-compatible 5160/8160 through 5164/8164 sheets
- automatic, unrotated, or 90-degree tag placement and copy count

Settings persist between launches. **Restore Defaults** only resets the advanced dialog, leaving the current device ID, pin count, and width intact.

## Command line

The original command-line workflow remains available:

```bash
./scripts/labels.sh --pins 16 --width 300 --id IC12 -o IC12.svg
```

Create a print-page SVG:

```bash
./scripts/labels.sh --pins 16 --width 300 --id IC12 \
  --paper A4 --copies 24 -o IC12_A4.svg
```

Run the automated geometry and SVG checks with:

```bash
./scripts/test.sh -q
```
