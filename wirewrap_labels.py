#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

MIL_TO_MM = 0.0254
STANDARD_WIDTHS_MIL = [300, 400, 600, 900]

def dip_pin_positions(pin_count, row_width_mm, pitch_mm=2.54):
    if pin_count < 4 or pin_count % 2:
        raise ValueError("DIP pin count must be even and >= 4.")
    n = pin_count // 2
    pts = []
    for i in range(n):
        pts.append((i + 1, 0.0, i * pitch_mm, "left"))
    for i in range(n):
        pts.append((n + i + 1, row_width_mm, (n - 1 - i) * pitch_mm, "right"))
    return pts

def esc(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

def generate_label_svg(
    pin_count,
    width_mil,
    part_id,
    out_path,
    hole_dia_mm=1.15,
    pitch_mm=2.54,
    end_margin_mm=2.2,
    side_margin_mm=2.0,
    notch_depth_mm=1.4,
    notch_width_mm=4.0,
    font_size_pin_mm=1.45,
    font_size_id_mm=1.85,
    number_gap_mm=0.55,
    id_x_offset_mm=-0.925,
):
    if width_mil not in STANDARD_WIDTHS_MIL:
        raise ValueError(f"Choose width from {STANDARD_WIDTHS_MIL}")

    row_width_mm = width_mil * MIL_TO_MM
    n = pin_count // 2
    tag_w = row_width_mm + 2 * side_margin_mm
    tag_h = (n - 1) * pitch_mm + 2 * end_margin_mm
    x0, y0 = side_margin_mm, end_margin_mm

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{tag_w:.3f}mm" height="{tag_h:.3f}mm" '
        f'viewBox="0 0 {tag_w:.3f} {tag_h:.3f}">'
    ]
    lines.append(
        f'<rect x="0.15" y="0.15" width="{tag_w - 0.30:.3f}" '
        f'height="{tag_h - 0.30:.3f}" rx="0.6" '
        f'fill="white" stroke="black" stroke-width="0.20"/>'
    )

    # Orientation notch at pin-1 end.
    cx = tag_w / 2
    lines.append(
        f'<path d="M {cx - notch_width_mm/2:.3f},0.15 '
        f'Q {cx:.3f},{notch_depth_mm:.3f} '
        f'{cx + notch_width_mm/2:.3f},0.15" '
        f'fill="none" stroke="black" stroke-width="0.20"/>'
    )

    # Pin holes and numbers on the inside of the two pin rows.
    for pin_no, px, py, side in dip_pin_positions(pin_count, row_width_mm, pitch_mm):
        x, y = x0 + px, y0 + py
        r = hole_dia_mm / 2

        lines.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r:.3f}" '
            f'fill="white" stroke="black" stroke-width="0.16"/>'
        )

        if side == "left":
            tx, anchor = x + r + number_gap_mm, "start"
        else:
            tx, anchor = x - r - number_gap_mm, "end"

        lines.append(
            f'<text x="{tx:.3f}" y="{y:.3f}" '
            f'font-family="DejaVu Sans,Arial,sans-serif" '
            f'font-size="{font_size_pin_mm:.3f}px" '
            f'text-anchor="{anchor}" dominant-baseline="middle">'
            f'{pin_no}</text>'
        )

    # Part ID: start from the geometric center, then nudge it horizontally.
    # Default offset is -0.925 mm (about half the default ID text height),
    # moving the rotated ID left so it clears the high-number/right-side labels.
    id_x = (tag_w / 2.0) + id_x_offset_mm
    id_y = tag_h / 2.0
    lines.append(
        f'<g transform="translate({id_x:.3f} {id_y:.3f}) rotate(90)">'
        f'<text x="0" y="0" '
        f'font-family="DejaVu Sans,Arial,sans-serif" '
        f'font-size="{font_size_id_mm:.3f}px" font-weight="bold" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'alignment-baseline="central">'
        f'{esc(part_id)}</text></g>'
    )

    lines.append("</svg>")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")

def main():
    p = argparse.ArgumentParser(
        description="Generate wire-wrap tag labels with inward pin numbers "
                    "and a top-to-bottom rotated center part ID."
    )
    p.add_argument("--pins", type=int, required=True)
    p.add_argument("--width", type=int, required=True, choices=STANDARD_WIDTHS_MIL)
    p.add_argument("--id", required=True, dest="part_id")
    p.add_argument("-o", "--output", required=True)
    p.add_argument(
        "--id-size",
        type=float,
        default=1.85,
        help="Part-ID font size in SVG user units (default: 1.85)"
    )
    p.add_argument(
        "--id-x-offset",
        type=float,
        default=-0.925,
        help="Horizontal ID offset in mm; negative moves left (default: -0.925)"
    )
    args = p.parse_args()

    generate_label_svg(
        args.pins,
        args.width,
        args.part_id,
        args.output,
        font_size_id_mm=args.id_size,
        id_x_offset_mm=args.id_x_offset,
    )

if __name__ == "__main__":
    main()
