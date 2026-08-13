"""Geometry and file generation for the wire-wrap tag designer.

The module deliberately has no Qt dependency, which keeps the command-line
generator and its geometry testable without starting a GUI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Iterable, Mapping


MIL_TO_MM = 0.0254
STANDARD_WIDTHS_MIL = (300, 400, 600, 900)
PAPER_SIZES_MM = {
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
}
CUSTOM_SHEET = "Custom grid"
LABEL_ROTATIONS = ("Auto", "0°", "90°")


@dataclass(frozen=True, slots=True)
class SheetTemplate:
    """Fixed geometry for a sheet of pre-cut adhesive labels."""

    name: str
    paper_size: str
    columns: int
    rows: int
    label_width_mm: float
    label_height_mm: float
    left_mm: float
    top_mm: float
    horizontal_pitch_mm: float
    vertical_pitch_mm: float

    @property
    def capacity(self) -> int:
        return self.columns * self.rows


INCH_TO_MM = 25.4
SHEET_TEMPLATES = {
    # Product families that share these layouts include the corresponding
    # 816x inkjet stock. Measurements are expressed in millimetres here but
    # originate from the inch-based Letter templates.
    "Avery 5160 / 8160 (30 per sheet)": SheetTemplate(
        "Avery 5160 / 8160 (30 per sheet)", "Letter", 3, 10,
        2.625 * INCH_TO_MM, 1.0 * INCH_TO_MM,
        0.1875 * INCH_TO_MM, 0.5 * INCH_TO_MM,
        2.75 * INCH_TO_MM, 1.0 * INCH_TO_MM,
    ),
    "Avery 5161 / 8161 (20 per sheet)": SheetTemplate(
        "Avery 5161 / 8161 (20 per sheet)", "Letter", 2, 10,
        4.0 * INCH_TO_MM, 1.0 * INCH_TO_MM,
        0.1875 * INCH_TO_MM, 0.5 * INCH_TO_MM,
        4.125 * INCH_TO_MM, 1.0 * INCH_TO_MM,
    ),
    "Avery 5162 / 8162 (14 per sheet)": SheetTemplate(
        "Avery 5162 / 8162 (14 per sheet)", "Letter", 2, 7,
        4.0 * INCH_TO_MM, (4.0 / 3.0) * INCH_TO_MM,
        0.1875 * INCH_TO_MM, (1.0 / 3.0) * INCH_TO_MM,
        4.125 * INCH_TO_MM, 1.5 * INCH_TO_MM,
    ),
    "Avery 5163 / 8163 (10 per sheet)": SheetTemplate(
        "Avery 5163 / 8163 (10 per sheet)", "Letter", 2, 5,
        4.0 * INCH_TO_MM, 2.0 * INCH_TO_MM,
        0.1875 * INCH_TO_MM, 0.5 * INCH_TO_MM,
        4.125 * INCH_TO_MM, 2.0 * INCH_TO_MM,
    ),
    "Avery 5164 / 8164 (6 per sheet)": SheetTemplate(
        "Avery 5164 / 8164 (6 per sheet)", "Letter", 2, 3,
        4.0 * INCH_TO_MM, (10.0 / 3.0) * INCH_TO_MM,
        0.1875 * INCH_TO_MM, 0.5 * INCH_TO_MM,
        4.125 * INCH_TO_MM, (10.0 / 3.0) * INCH_TO_MM,
    ),
}


@dataclass(slots=True)
class TagSettings:
    pins: int = 16
    width_mil: int = 300
    part_id: str = "IC1"

    pitch_mm: float = 2.54
    hole_diameter_mm: float = 1.15
    side_margin_mm: float = 2.0
    end_margin_mm: float = 2.2
    corner_radius_mm: float = 0.8
    notch_depth_mm: float = 1.4
    notch_width_mm: float = 4.0

    pin_font_size_mm: float = 1.45
    id_font_size_mm: float = 1.85
    number_gap_mm: float = 0.55
    id_x_offset_mm: float = -0.925
    id_y_offset_mm: float = 0.0
    id_orientation: str = "Top to bottom"
    font_family: str = "DejaVu Sans"

    label_color: str = "#ffffff"
    outline_color: str = "#000000"
    pin_number_color: str = "#000000"
    id_color: str = "#000000"

    thickness_mm: float = 0.8
    center_window: bool = False
    center_window_margin_mm: float = 1.5

    paper_size: str = "Letter"
    page_orientation: str = "Portrait"
    page_margin_mm: float = 8.0
    label_spacing_mm: float = 3.0
    copies: int = 1
    sheet_template: str = CUSTOM_SHEET
    label_rotation: str = "Auto"

    def validate(self) -> None:
        if self.pins < 4 or self.pins % 2:
            raise ValueError("DIP pin count must be an even number of 4 or more.")
        if self.width_mil not in STANDARD_WIDTHS_MIL:
            raise ValueError(f"Device width must be one of {STANDARD_WIDTHS_MIL} mil.")
        positive = {
            "pin pitch": self.pitch_mm,
            "hole diameter": self.hole_diameter_mm,
            "side margin": self.side_margin_mm,
            "end margin": self.end_margin_mm,
            "tag thickness": self.thickness_mm,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name.title()} must be greater than zero.")
        if self.paper_size not in PAPER_SIZES_MM:
            raise ValueError(f"Unknown paper size: {self.paper_size}")
        if self.page_orientation not in ("Portrait", "Landscape"):
            raise ValueError(f"Unknown page orientation: {self.page_orientation}")
        if self.page_margin_mm < 0 or self.label_spacing_mm < 0:
            raise ValueError("Page margin and label spacing cannot be negative.")
        if self.copies < 1:
            raise ValueError("Copies must be at least 1.")
        if self.sheet_template != CUSTOM_SHEET and self.sheet_template not in SHEET_TEMPLATES:
            raise ValueError(f"Unknown label-sheet template: {self.sheet_template}")
        if self.label_rotation not in LABEL_ROTATIONS:
            raise ValueError(f"Unknown label rotation: {self.label_rotation}")

    @property
    def row_spacing_mm(self) -> float:
        return self.width_mil * MIL_TO_MM

    @property
    def label_width_mm(self) -> float:
        return self.row_spacing_mm + 2 * self.side_margin_mm

    @property
    def label_height_mm(self) -> float:
        return (self.pins // 2 - 1) * self.pitch_mm + 2 * self.end_margin_mm

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, value: str) -> "TagSettings":
        known = cls.__dataclass_fields__
        return cls(**{key: item for key, item in json.loads(value).items() if key in known})


def dip_pin_positions(settings: TagSettings) -> Iterable[tuple[int, float, float, str]]:
    settings.validate()
    count_per_side = settings.pins // 2
    for index in range(count_per_side):
        yield index + 1, 0.0, index * settings.pitch_mm, "left"
    for index in range(count_per_side):
        yield (
            count_per_side + index + 1,
            settings.row_spacing_mm,
            (count_per_side - 1 - index) * settings.pitch_mm,
            "right",
        )


def _rotation(orientation: str) -> int:
    return {
        "Top to bottom": 90,
        "Bottom to top": -90,
        "Horizontal": 0,
        "Upside down": 180,
    }.get(orientation, 90)


def label_svg(settings: TagSettings) -> str:
    """Return one physical-size label as SVG text."""
    settings.validate()
    width = settings.label_width_mm
    height = settings.label_height_mm
    x0 = settings.side_margin_mm
    y0 = settings.end_margin_mm
    font = escape(settings.font_family, quote=True)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width:.3f}mm" height="{height:.3f}mm" '
        f'viewBox="0 0 {width:.3f} {height:.3f}">',
        f'<rect x="0.15" y="0.15" width="{width - 0.30:.3f}" '
        f'height="{height - 0.30:.3f}" rx="{settings.corner_radius_mm:.3f}" '
        f'fill="{escape(settings.label_color)}" stroke="{escape(settings.outline_color)}" '
        'stroke-width="0.20"/>',
    ]

    center_x = width / 2
    lines.append(
        f'<path d="M {center_x - settings.notch_width_mm / 2:.3f},0.15 '
        f'Q {center_x:.3f},{settings.notch_depth_mm:.3f} '
        f'{center_x + settings.notch_width_mm / 2:.3f},0.15" fill="none" '
        f'stroke="{escape(settings.outline_color)}" stroke-width="0.20"/>'
    )

    for pin, pin_x, pin_y, side in dip_pin_positions(settings):
        x, y = x0 + pin_x, y0 + pin_y
        radius = settings.hole_diameter_mm / 2
        lines.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius:.3f}" '
            f'fill="{escape(settings.label_color)}" stroke="{escape(settings.outline_color)}" '
            'stroke-width="0.16"/>'
        )
        if side == "left":
            text_x, anchor = x + radius + settings.number_gap_mm, "start"
        else:
            text_x, anchor = x - radius - settings.number_gap_mm, "end"
        lines.append(
            f'<text x="{text_x:.3f}" y="{y:.3f}" font-family="{font},Arial,sans-serif" '
            f'font-size="{settings.pin_font_size_mm:.3f}" fill="{escape(settings.pin_number_color)}" '
            f'text-anchor="{anchor}" dominant-baseline="middle">{pin}</text>'
        )

    id_x = width / 2 + settings.id_x_offset_mm
    id_y = height / 2 + settings.id_y_offset_mm
    lines.append(
        f'<g transform="translate({id_x:.3f} {id_y:.3f}) rotate({_rotation(settings.id_orientation)})">'
        f'<text x="0" y="0" font-family="{font},Arial,sans-serif" '
        f'font-size="{settings.id_font_size_mm:.3f}" font-weight="bold" '
        f'fill="{escape(settings.id_color)}" text-anchor="middle" '
        f'dominant-baseline="central">{escape(settings.part_id)}</text></g>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


def write_label_svg(settings: TagSettings, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(label_svg(settings), encoding="utf-8")
    return output


def page_dimensions(settings: TagSettings) -> tuple[float, float]:
    settings.validate()
    paper_size = effective_paper_size(settings)
    width, height = PAPER_SIZES_MM[paper_size]
    if settings.sheet_template != CUSTOM_SHEET:
        return width, height
    if settings.page_orientation == "Landscape":
        return height, width
    return width, height


def effective_paper_size(settings: TagSettings) -> str:
    """Return the paper stock actually used by the selected layout."""
    template = SHEET_TEMPLATES.get(settings.sheet_template)
    return template.paper_size if template else settings.paper_size


def page_layout(settings: TagSettings) -> tuple[int, int, int]:
    """Return columns, rows and labels-per-page for the current paper."""
    settings.validate()
    template = SHEET_TEMPLATES.get(settings.sheet_template)
    if template:
        return template.columns, template.rows, template.capacity
    page_width, page_height = page_dimensions(settings)
    usable_width = page_width - 2 * settings.page_margin_mm
    usable_height = page_height - 2 * settings.page_margin_mm
    columns = max(0, int((usable_width + settings.label_spacing_mm) /
                         (settings.label_width_mm + settings.label_spacing_mm)))
    rows = max(0, int((usable_height + settings.label_spacing_mm) /
                      (settings.label_height_mm + settings.label_spacing_mm)))
    return columns, rows, columns * rows


def label_rotation(settings: TagSettings, cell_width: float, cell_height: float) -> int:
    """Return a fitting 0/90-degree rotation for a label-sheet cell."""
    unrotated_fits = (
        settings.label_width_mm <= cell_width + 1e-9
        and settings.label_height_mm <= cell_height + 1e-9
    )
    rotated_fits = (
        settings.label_height_mm <= cell_width + 1e-9
        and settings.label_width_mm <= cell_height + 1e-9
    )
    requested = settings.label_rotation
    if requested == "0°" and unrotated_fits:
        return 0
    if requested == "90°" and rotated_fits:
        return 90
    if requested == "Auto":
        if unrotated_fits:
            return 0
        if rotated_fits:
            return 90
    orientation = "without rotation" if requested == "0°" else "rotated 90°"
    raise ValueError(
        f"The {settings.label_width_mm:.2f} × {settings.label_height_mm:.2f} mm tag "
        f"does not fit the selected sheet label {orientation}."
    )


def _template_placement(
    settings: TagSettings,
    template: SheetTemplate,
    index: int,
) -> tuple[float, float, int]:
    column = index % template.columns
    row = index // template.columns
    cell_x = template.left_mm + column * template.horizontal_pitch_mm
    cell_y = template.top_mm + row * template.vertical_pitch_mm
    rotation = label_rotation(settings, template.label_width_mm, template.label_height_mm)
    placed_width = settings.label_height_mm if rotation else settings.label_width_mm
    placed_height = settings.label_width_mm if rotation else settings.label_height_mm
    x = cell_x + (template.label_width_mm - placed_width) / 2
    y = cell_y + (template.label_height_mm - placed_height) / 2
    return x, y, rotation


def label_page_svg(
    settings: TagSettings,
    copies: int | None = None,
    page_index: int = 0,
    show_guides: bool = False,
) -> str:
    """Create one A4/Letter print sheet, preserving exact millimetre size."""
    settings.validate()
    total = settings.copies if copies is None else max(1, copies)
    page_width, page_height = page_dimensions(settings)
    columns, _, capacity = page_layout(settings)
    template = SHEET_TEMPLATES.get(settings.sheet_template)
    if capacity == 0:
        raise ValueError("The label does not fit on the selected paper with these margins.")
    start = page_index * capacity
    count = max(0, min(total - start, capacity))
    single = label_svg(settings)
    inner = single[single.find(">") + 1:single.rfind("</svg>")]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{page_width:.3f}mm" height="{page_height:.3f}mm" '
        f'viewBox="0 0 {page_width:.3f} {page_height:.3f}">',
        f'<rect width="{page_width:.3f}" height="{page_height:.3f}" fill="white"/>',
    ]
    if show_guides and template:
        for guide_index in range(template.capacity):
            column = guide_index % template.columns
            row = guide_index // template.columns
            x = template.left_mm + column * template.horizontal_pitch_mm
            y = template.top_mm + row * template.vertical_pitch_mm
            lines.append(
                f'<rect x="{x:.3f}" y="{y:.3f}" width="{template.label_width_mm:.3f}" '
                f'height="{template.label_height_mm:.3f}" rx="0.8" fill="none" '
                'stroke="#7aa7c7" stroke-width="0.25" stroke-dasharray="1.2,0.8"/>'
            )
    for index in range(count):
        if template:
            x, y, rotation = _template_placement(settings, template, index)
        else:
            column = index % columns
            row = index // columns
            x = settings.page_margin_mm + column * (settings.label_width_mm + settings.label_spacing_mm)
            y = settings.page_margin_mm + row * (settings.label_height_mm + settings.label_spacing_mm)
            rotation = 0
        if rotation:
            center_x = x + settings.label_height_mm / 2
            center_y = y + settings.label_width_mm / 2
            transform = (
                f"translate({center_x:.3f} {center_y:.3f}) rotate(90) "
                f"translate({-settings.label_width_mm / 2:.3f} {-settings.label_height_mm / 2:.3f})"
            )
        else:
            transform = f"translate({x:.3f} {y:.3f})"
        lines.append(f'<g transform="{transform}">{inner}</g>')
    lines.append("</svg>")
    return "\n".join(lines)


def label_page_svgs(settings: TagSettings, copies: int | None = None) -> list[str]:
    total = settings.copies if copies is None else max(1, copies)
    _, _, capacity = page_layout(settings)
    if capacity == 0:
        raise ValueError("The label does not fit on the selected paper with these margins.")
    page_count = max(1, (total + capacity - 1) // capacity)
    return [label_page_svg(settings, total, index) for index in range(page_count)]


def write_label_page_svg(settings: TagSettings, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(label_page_svg(settings), encoding="utf-8")
    return output


def scad_source(settings: TagSettings) -> str:
    """Create a self-contained OpenSCAD model matching the label geometry."""
    settings.validate()
    window = "true" if settings.center_window else "false"
    return f"""// Generated by Wire-Wrap Tag Designer. Units: mm.
pins = {settings.pins};
row_spacing = {settings.row_spacing_mm:.4f};
thickness = {settings.thickness_mm:.4f};
pin_pitch = {settings.pitch_mm:.4f};
hole_diameter = {settings.hole_diameter_mm:.4f};
end_margin = {settings.end_margin_mm:.4f};
side_margin = {settings.side_margin_mm:.4f};
notch_radius = {settings.notch_width_mm / 2:.4f};
corner_radius = {settings.corner_radius_mm:.4f};
center_window = {window};
center_window_margin = {settings.center_window_margin_mm:.4f};
rows = pins / 2;
length = (rows - 1) * pin_pitch + 2 * end_margin;
width = row_spacing + 2 * side_margin;

module rounded_rect_2d(x, y, r) {{
    hull() for (sx=[-1,1], sy=[-1,1])
        translate([sx*(x/2-r), sy*(y/2-r)]) circle(r=r, $fn=32);
}}
module tag_2d() {{
    difference() {{
        rounded_rect_2d(length, width, corner_radius);
        for (i=[0:rows-1]) {{
            x = -length/2 + end_margin + i*pin_pitch;
            translate([x, -row_spacing/2]) circle(d=hole_diameter, $fn=28);
            translate([x,  row_spacing/2]) circle(d=hole_diameter, $fn=28);
        }}
        translate([-length/2, 0]) circle(r=notch_radius, $fn=48);
        if (center_window) {{
            window_len = max(1, length - 2*(end_margin + center_window_margin));
            window_wid = max(1, row_spacing - 2*center_window_margin);
            square([window_len, window_wid], center=true);
        }}
    }}
}}
linear_extrude(height=thickness) tag_2d();
"""


def write_scad(settings: TagSettings, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(scad_source(settings), encoding="utf-8")
    return output


def _openscad_candidate_paths(
    system_name: str,
    environment: Mapping[str, str],
    home: Path,
) -> Iterable[Path]:
    """Yield platform-specific OpenSCAD locations not normally on PATH."""
    override = environment.get("OPENSCAD_PATH")
    if override:
        yield Path(override).expanduser()

    if system_name == "Darwin":
        yield Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
        yield home / "Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    elif system_name == "Windows":
        for variable in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
            base = environment.get(variable)
            if base:
                yield Path(base) / "OpenSCAD" / "openscad.exe"
        local_app_data = environment.get("LOCALAPPDATA")
        if local_app_data:
            yield Path(local_app_data) / "Programs" / "OpenSCAD" / "openscad.exe"
        yield home / "scoop" / "apps" / "openscad" / "current" / "openscad.exe"


def find_openscad(
    system_name: str | None = None,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> str | None:
    """Find OpenSCAD on PATH or in common Linux, macOS, and Windows locations."""
    active_environment = os.environ if environment is None else environment
    active_system = system_name or platform.system()
    active_home = Path.home() if home is None else home

    override = active_environment.get("OPENSCAD_PATH")
    if override:
        override_path = Path(override).expanduser()
        if override_path.is_file():
            return str(override_path)

    for executable_name in ("openscad", "OpenSCAD", "openscad.exe"):
        executable = shutil.which(executable_name)
        if executable:
            return executable

    for candidate in _openscad_candidate_paths(active_system, active_environment, active_home):
        if candidate.is_file():
            return str(candidate)
    return None


def render_stl(settings: TagSettings, path: str | Path, openscad: str | None = None) -> Path:
    executable = openscad or find_openscad()
    if not executable:
        raise RuntimeError("OpenSCAD was not found. Install it to generate STL files.")
    output = Path(path)
    source = output.with_suffix(".scad")
    write_scad(settings, source)
    result = subprocess.run(
        [executable, "-o", str(output), str(source)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown OpenSCAD error"
        raise RuntimeError(f"Could not generate STL: {detail}")
    return output
