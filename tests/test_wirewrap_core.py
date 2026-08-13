from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from wirewrap_tag_designer.core import (
    SHEET_TEMPLATES,
    TagSettings,
    dip_pin_positions,
    find_openscad,
    label_page_svg,
    label_page_svgs,
    label_rotation,
    label_svg,
    page_dimensions,
    page_layout,
    scad_source,
    write_label_svg,
)


def test_default_geometry_matches_300_mil_16_pin_dip():
    settings = TagSettings()
    assert settings.row_spacing_mm == pytest.approx(7.62)
    assert settings.label_width_mm == pytest.approx(11.62)
    assert settings.label_height_mm == pytest.approx(22.18)


def test_pin_numbering_runs_down_left_and_up_right():
    positions = list(dip_pin_positions(TagSettings()))
    assert positions[0] == (1, 0.0, 0.0, "left")
    assert positions[7][0:2] == (8, 0.0)
    assert positions[8][0] == 9
    assert positions[8][2] > positions[-1][2]
    assert positions[-1][0] == 16


def test_label_svg_is_well_formed_and_uses_selected_colors():
    settings = TagSettings(part_id="A&B<1>", label_color="#ffeeaa", pin_number_color="#123456")
    source = label_svg(settings)
    ET.fromstring(source)
    assert 'width="11.620mm"' in source
    assert "#ffeeaa" in source
    assert "#123456" in source
    assert "A&amp;B&lt;1&gt;" in source


def test_letter_and_a4_physical_page_sizes():
    letter = TagSettings(paper_size="Letter", copies=2)
    a4 = TagSettings(paper_size="A4", copies=2)
    assert page_dimensions(letter) == (215.9, 279.4)
    assert page_dimensions(a4) == (210.0, 297.0)
    assert 'width="215.900mm"' in label_page_svg(letter)
    assert 'height="297.000mm"' in label_page_svg(a4)


def test_large_copy_count_creates_multiple_sheets():
    settings = TagSettings(copies=131)
    assert page_layout(settings)[2] == 130
    assert len(label_page_svgs(settings)) == 2


def test_avery_5160_uses_fixed_30_label_layout():
    template_name = "Avery 5160 / 8160 (30 per sheet)"
    settings = TagSettings(sheet_template=template_name, copies=30)
    template = SHEET_TEMPLATES[template_name]

    assert page_dimensions(settings) == (215.9, 279.4)
    assert page_layout(settings) == (3, 10, 30)
    source = label_page_svg(settings, show_guides=True)
    assert source.count('stroke="#7aa7c7"') == 30
    assert f'x="{template.left_mm:.3f}"' in source
    assert source.count("IC1") == 30


def test_auto_rotation_turns_long_tag_to_fit_avery_5160():
    settings = TagSettings(
        pins=40,
        sheet_template="Avery 5160 / 8160 (30 per sheet)",
        label_rotation="Auto",
    )
    template = SHEET_TEMPLATES[settings.sheet_template]

    assert settings.label_height_mm > template.label_height_mm
    assert label_rotation(settings, template.label_width_mm, template.label_height_mm) == 90
    assert "rotate(90)" in label_page_svg(settings)


def test_forced_rotation_reports_when_tag_does_not_fit():
    settings = TagSettings(
        pins=40,
        sheet_template="Avery 5160 / 8160 (30 per sheet)",
        label_rotation="0°",
    )

    with pytest.raises(ValueError, match="does not fit"):
        label_page_svg(settings)


def test_avery_copy_count_creates_additional_sheet():
    settings = TagSettings(
        sheet_template="Avery 5163 / 8163 (10 per sheet)",
        copies=11,
    )

    assert len(label_page_svgs(settings)) == 2
    assert label_page_svgs(settings)[1].count("IC1") == 1


def test_scad_uses_same_geometry_and_thickness():
    source = scad_source(TagSettings(pins=40, width_mil=600, thickness_mm=1.2))
    assert "pins = 40;" in source
    assert "row_spacing = 15.2400;" in source
    assert "thickness = 1.2000;" in source
    assert "linear_extrude(height=thickness)" in source


def test_write_label_svg(tmp_path: Path):
    output = write_label_svg(TagSettings(part_id="CPU1"), tmp_path / "label.svg")
    assert output.exists()
    assert "CPU1" in output.read_text(encoding="utf-8")


def test_openscad_environment_override(tmp_path: Path, monkeypatch):
    executable = tmp_path / "custom-openscad"
    executable.touch()
    monkeypatch.setattr("wirewrap_tag_designer.core.shutil.which", lambda _name: None)

    assert find_openscad(environment={"OPENSCAD_PATH": str(executable)}) == str(executable)


def test_openscad_macos_user_application(tmp_path: Path, monkeypatch):
    executable = tmp_path / "Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    executable.parent.mkdir(parents=True)
    executable.touch()
    monkeypatch.setattr("wirewrap_tag_designer.core.shutil.which", lambda _name: None)

    assert find_openscad(system_name="Darwin", environment={}, home=tmp_path) == str(executable)


def test_openscad_windows_program_files(tmp_path: Path, monkeypatch):
    executable = tmp_path / "OpenSCAD" / "openscad.exe"
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.setattr("wirewrap_tag_designer.core.shutil.which", lambda _name: None)

    environment = {"ProgramFiles": str(tmp_path)}
    assert find_openscad(system_name="Windows", environment=environment) == str(executable)


@pytest.mark.parametrize("pins", [3, 5, 17])
def test_invalid_pin_counts_are_rejected(pins):
    with pytest.raises(ValueError, match="even"):
        label_svg(TagSettings(pins=pins))
