# Wire-Wrap Tag Designer

[![Cross-platform tests](https://github.com/Monotoba/Wirewrap-tag_toolset/actions/workflows/ci.yml/badge.svg)](https://github.com/Monotoba/Wirewrap-tag_toolset/actions/workflows/ci.yml)
[![Build and release](https://github.com/Monotoba/Wirewrap-tag_toolset/actions/workflows/release.yml/badge.svg)](https://github.com/Monotoba/Wirewrap-tag_toolset/actions/workflows/release.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small PySide6 desktop application for designing matching wire-wrap socket labels and 3D-printable tags.

If you enjoy wire-wrapping prototype or one-off circuits—and perhaps find spending countless hours with a wire-wrap tool strangely therapeutic—you have probably discovered an unfortunate fact: the wire, sockets, and hand tools are still fairly easy to find, but the little identification tags that fit over DIP sockets have all but disappeared.

That was a problem worth fixing.

To support my own obsession with hardware development, prototyping, and tinkering, I created **Wire-Wrap Tag Designer**: a simple set of tools for producing both the plastic socket tags and the printed identification labels that go on top of them. The finished tags can show the component ID and pin numbers right beside the corresponding socket pins, making it much easier to keep your place while wiring a crowded vectorboard or Veroboard.

The plastic tags are generated as STL models and can be printed on an ordinary 3D printer. Because the pin holes are small, a well-tuned printer helps—especially extrusion, pressure advance, and retraction settings. If your printer is feeling less cooperative, you may occasionally need to clean out a hole with a small drill bit. Even then, that is often preferable to repeatedly counting socket pins across a densely populated board.

While the plastic tags are printing, you can print the matching labels. Use ordinary paper and adhesive, self-adhesive label stock, or common peel-and-stick sheets such as Avery-compatible labels.

Set the part ID, DIP pin count, and pin-row width, inspect the live previews, then generate a dimensionally accurate label sheet and matching STL model with a single click.

![Example 16-pin wire-wrap label](wirewrap-label.svg)

## Highlights

- Simple three-field setup for the most common workflow
- Live label, print-sheet, and isometric tag previews
- Standard 300, 400, 600, and 900 mil DIP widths
- A4 and US Letter output at exact physical size
- Avery-compatible 5160/8160 through 5164/8164 Letter-sheet presets
- Automatic or forced 90-degree tag rotation within pre-cut labels
- Multi-page PDF and SVG label sheets
- Matching SVG, PDF, OpenSCAD, and STL geometry
- Adjustable label margins, pin holes, number spacing, text, and colors
- Adjustable tag thickness, corners, notch, and optional center window
- Persistent settings and a backward-compatible command-line tool
- Light, dark, and system-matched application themes

## Requirements

- Python 3.10 or newer
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [OpenSCAD](https://openscad.org/) for STL export

OpenSCAD is optional if you only need SVG, PDF, or editable `.scad` output.

## Platform support

| Platform | GUI and print output | STL export | Setup tools |
| --- | --- | --- | --- |
| Linux | Supported | OpenSCAD on PATH | Bash |
| macOS | Supported | PATH or standard `OpenSCAD.app` locations | Bash |
| Windows 10/11 | Supported | PATH, Program Files, LocalAppData, or Scoop | PowerShell and CMD |

Every push and pull request runs the Python, CLI, and headless GUI tests on current GitHub-hosted Linux, macOS, and Windows runners.

## Installation

Clone the repository, then use the setup command for your platform.

### Linux and macOS

```bash
git clone https://github.com/Monotoba/Wirewrap-tag_toolset.git
cd Wirewrap-tag_toolset
./scripts/setup.sh
```

For an application-only environment:

```bash
./scripts/setup.sh --runtime
```

### Windows

From PowerShell:

```powershell
git clone https://github.com/Monotoba/Wirewrap-tag_toolset.git
Set-Location Wirewrap-tag_toolset
.\scripts\setup.ps1
```

Or from Command Prompt:

```batch
git clone https://github.com/Monotoba/Wirewrap-tag_toolset.git
cd Wirewrap-tag_toolset
scripts\setup.cmd
```

Use `-Mode runtime` with `setup.ps1`, or `runtime` with `setup.cmd`, for an application-only environment. All setup variants create a local `.venv/`; development mode installs the project editably with its test tools.

## Running the application

From the repository:

```bash
./scripts/run.sh
```

On Windows, use either:

```powershell
.\scripts\run.ps1
```

```batch
scripts\run.cmd
```

An editable installation also provides:

```bash
wirewrap-tag-designer
```

The normal workflow is:

1. Enter a device or part ID such as `IC12`.
2. Select an even DIP pin count.
3. Select the pin-row width.
4. Choose an output folder.
5. Click **Generate label + printable page + STL**.

Use **Settings → Design & print settings** (or `Ctrl+,`) for less common adjustments such as label extension, number placement, font size, orientation, colors, page layout, pre-cut label stock, or tag thickness. Choose **Settings → Appearance** to use the system theme or explicitly select light or dark mode.

### Pre-cut Avery-compatible sheets

In **Design & print settings → Print page**, choose a stock preset for the common Letter-size layouts 5160/8160 (30 labels), 5161/8161 (20), 5162/8162 (14), 5163/8163 (10), or 5164/8164 (6). The same tag is repeated up to the requested copy count and additional PDF/SVG pages are created when necessary.

**Auto** rotation preserves the tag's exact dimensions and turns it 90° only when the unrotated tag does not fit the individual adhesive label. You can force either orientation. Dashed stock boundaries appear in the live preview only; they are omitted from exported SVG and PDF files.

## Generated files

For a part named `IC12`, the application can produce:

| File | Purpose |
| --- | --- |
| `IC12_label.svg` | One label at exact physical size |
| `IC12_letter_sheet.svg` | Printable label sheet |
| `IC12_letter_sheet.pdf` | Print-ready PDF, including additional pages when needed |
| `IC12_tag.scad` | Editable parametric tag model |
| `IC12_tag.stl` | Model ready for a slicer |
| `IC12_settings.json` | Complete record of the design settings |

> [!IMPORTANT]
> Print PDFs using **Actual Size** or **100%**. Disable “Fit to page” so the label remains dimensionally accurate.

## Command-line use

The label command-line interface remains available through `scripts/labels.sh`:

```bash
./scripts/labels.sh \
  --pins 16 \
  --width 300 \
  --id IC12 \
  -o IC12.svg
```

Create an A4 sheet containing 24 labels:

```bash
./scripts/labels.sh \
  --pins 16 \
  --width 300 \
  --id IC12 \
  --paper A4 \
  --copies 24 \
  -o IC12_A4.svg
```

Create an Avery 5160/8160-compatible sheet, rotating long tags when needed:

```bash
./scripts/labels.sh \
  --pins 40 \
  --width 300 \
  --id CPU1 \
  --sheet-template "Avery 5160 / 8160 (30 per sheet)" \
  --copies 30 \
  -o CPU1_5160.svg
```

After an editable installation, the same command is available as `wirewrap-labels`.

On Windows, replace `./scripts/labels.sh` with `.\scripts\labels.ps1` or `scripts\labels.cmd`.

## OpenSCAD discovery

The application searches PATH first, followed by common macOS and Windows installation locations. If OpenSCAD is installed somewhere unusual, set `OPENSCAD_PATH` to the full executable path before launching the application:

```bash
export OPENSCAD_PATH=/custom/path/to/openscad
```

```powershell
$env:OPENSCAD_PATH = "C:\Custom\OpenSCAD\openscad.exe"
```

## Development

The default setup includes the test dependency. Run the suite with:

```bash
./scripts/test.sh -q
```

Run all development checks with:

```bash
./scripts/check.sh
```

Windows equivalents are `.\scripts\test.ps1 -q` and `.\scripts\check.ps1`, with matching `.cmd` wrappers.

The repository follows a standard `src/` package layout:

```text
src/wirewrap_tag_designer/
├── core.py       # geometry and file generation; no Qt dependency
├── gui.py        # PySide6 desktop interface
├── cli.py        # label command-line interface
└── __main__.py   # python -m wirewrap_tag_designer

scripts/
├── *.sh          # Linux and macOS commands
├── *.ps1         # native Windows PowerShell commands
└── *.cmd         # Windows Command Prompt wrappers
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and [README_wirewrap_tags.md](README_wirewrap_tags.md) for the detailed control reference.

Security reports should use GitHub's private vulnerability reporting flow described in [SECURITY.md](SECURITY.md). Community participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and release history is recorded in [CHANGELOG.md](CHANGELOG.md).

## License

Released under the [MIT License](LICENSE).
