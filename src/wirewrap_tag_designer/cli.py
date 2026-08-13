#!/usr/bin/env python3
"""Command-line label generator for the wire-wrap tag designer."""

from __future__ import annotations

import argparse

from .core import (
    CUSTOM_SHEET,
    LABEL_ROTATIONS,
    SHEET_TEMPLATES,
    STANDARD_WIDTHS_MIL,
    TagSettings,
    write_label_page_svg,
    write_label_svg,
)


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
    """Backward-compatible Python API retained from toolset v6."""
    settings = TagSettings(
        pins=pin_count,
        width_mil=width_mil,
        part_id=part_id,
        hole_diameter_mm=hole_dia_mm,
        pitch_mm=pitch_mm,
        end_margin_mm=end_margin_mm,
        side_margin_mm=side_margin_mm,
        notch_depth_mm=notch_depth_mm,
        notch_width_mm=notch_width_mm,
        pin_font_size_mm=font_size_pin_mm,
        id_font_size_mm=font_size_id_mm,
        number_gap_mm=number_gap_mm,
        id_x_offset_mm=id_x_offset_mm,
    )
    return write_label_svg(settings, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a physical-size wire-wrap tag label SVG."
    )
    parser.add_argument("--pins", type=int, required=True)
    parser.add_argument("--width", type=int, required=True, choices=STANDARD_WIDTHS_MIL)
    parser.add_argument("--id", required=True, dest="part_id")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--id-size", type=float, default=1.85)
    parser.add_argument("--pin-size", type=float, default=1.45)
    parser.add_argument("--id-x-offset", type=float, default=-0.925)
    parser.add_argument("--number-gap", type=float, default=0.55)
    parser.add_argument("--side-margin", type=float, default=2.0)
    parser.add_argument("--end-margin", type=float, default=2.2)
    parser.add_argument("--paper", choices=["A4", "Letter"],
                        help="Lay labels out on a printable page instead of writing one label.")
    parser.add_argument("--copies", type=int, default=1)
    parser.add_argument(
        "--sheet-template",
        choices=[CUSTOM_SHEET, *SHEET_TEMPLATES],
        default=CUSTOM_SHEET,
        help="Use a fixed pre-cut label-sheet layout.",
    )
    parser.add_argument(
        "--rotation",
        choices=LABEL_ROTATIONS,
        default="Auto",
        help="Rotate each tag within its pre-cut sheet label.",
    )
    args = parser.parse_args()

    settings = TagSettings(
        pins=args.pins,
        width_mil=args.width,
        part_id=args.part_id,
        id_font_size_mm=args.id_size,
        pin_font_size_mm=args.pin_size,
        id_x_offset_mm=args.id_x_offset,
        number_gap_mm=args.number_gap,
        side_margin_mm=args.side_margin,
        end_margin_mm=args.end_margin,
        paper_size=args.paper or "Letter",
        copies=args.copies,
        sheet_template=args.sheet_template,
        label_rotation=args.rotation,
    )
    if args.paper or args.sheet_template != CUSTOM_SHEET:
        write_label_page_svg(settings, args.output)
    else:
        write_label_svg(settings, args.output)


if __name__ == "__main__":
    main()
