#!/usr/bin/env python3
"""PySide6 desktop application for designing printable wire-wrap tags."""

from __future__ import annotations

from dataclasses import fields
import math
from pathlib import Path
import re
import sys

from PySide6.QtCore import QByteArray, QSettings, QSize, QSizeF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QDesktopServices,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPolygonF,
)
from PySide6.QtCore import QPointF, QRectF, QUrl
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .core import (
    CUSTOM_SHEET,
    LABEL_ROTATIONS,
    PAPER_SIZES_MM,
    SHEET_TEMPLATES,
    STANDARD_WIDTHS_MIL,
    TagSettings,
    effective_paper_size,
    find_openscad,
    label_page_svg,
    label_page_svgs,
    label_svg,
    page_dimensions,
    page_layout,
    render_stl,
    write_label_page_svg,
    write_label_svg,
    write_scad,
)


THEME_NAMES = ("system", "light", "dark")


def resolve_theme(preference: str, palette: QPalette | None = None) -> str:
    """Resolve the persisted theme preference to a concrete light/dark theme."""
    if preference in {"light", "dark"}:
        return preference
    palette = palette or QApplication.palette()
    return "dark" if palette.color(QPalette.ColorRole.Window).lightness() < 128 else "light"


def app_style(theme: str) -> str:
    """Return a complete, explicit-color stylesheet for the selected theme."""
    dark = theme == "dark"
    colors = {
        "window": "#171b20" if dark else "#f4f6f8",
        "panel": "#222830" if dark else "#ffffff",
        "field": "#191e24" if dark else "#ffffff",
        "text": "#edf1f5" if dark else "#1d2730",
        "muted": "#aeb9c4" if dark else "#526474",
        "border": "#4a5662" if dark else "#bdc7d1",
        "soft_border": "#3d4752" if dark else "#d7dde3",
        "button": "#2b333c" if dark else "#f8fafb",
        "button_hover": "#374554" if dark else "#eaf2fa",
        "selected": "#245f93" if dark else "#dcecfb",
        "info": "#28333d" if dark else "#eef3f7",
        "good": "#72d69b" if dark else "#217645",
        "warn": "#f0bd68" if dark else "#9b6416",
    }
    return f"""
QWidget {{ color: {colors['text']}; }}
QMainWindow, QDialog {{ background: {colors['window']}; }}
QFrame#header {{ background: #18232f; border-radius: 10px; }}
QLabel#title {{ color: #ffffff; font-size: 22px; font-weight: 700; }}
QLabel#subtitle {{ color: #b8c5d1; }}
QLabel#secondaryText {{ color: {colors['muted']}; }}
QLabel#dimensions {{ color: {colors['muted']}; padding: 8px;
                    background: {colors['info']}; border-radius: 5px; }}
QGroupBox {{ color: {colors['text']}; font-weight: 600;
             border: 1px solid {colors['soft_border']}; border-radius: 8px;
             margin-top: 10px; padding-top: 10px; background: {colors['panel']}; }}
QGroupBox::title {{ color: {colors['text']}; subcontrol-origin: margin;
                    left: 12px; padding: 0 4px; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    color: {colors['text']}; min-height: 28px; border: 1px solid {colors['border']};
    border-radius: 5px; padding: 0 7px; background: {colors['field']};
    selection-background-color: #2878c8; selection-color: #ffffff;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid #3b91df;
}}
QComboBox QAbstractItemView {{ color: {colors['text']}; background: {colors['field']};
                              selection-background-color: {colors['selected']}; }}
QPushButton {{ color: {colors['text']}; min-height: 30px; padding: 2px 13px;
               border-radius: 5px; border: 1px solid {colors['border']};
               background: {colors['button']}; }}
QPushButton:hover {{ background: {colors['button_hover']}; }}
QPushButton#primary {{ color: #ffffff; background: #1673c9; border-color: #378edb;
                       font-weight: 650; min-height: 36px; }}
QPushButton#primary:hover {{ background: #0f67b8; }}
QTabWidget::pane {{ border: 1px solid {colors['soft_border']};
                    background: {colors['panel']}; border-radius: 6px; }}
QTabBar::tab {{ color: {colors['text']}; background: {colors['button']};
                border: 1px solid {colors['soft_border']}; padding: 7px 12px; }}
QTabBar::tab:selected {{ background: {colors['panel']}; }}
QMenuBar, QMenu {{ color: {colors['text']}; background: {colors['panel']}; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: {colors['selected']}; }}
QMenu::separator {{ height: 1px; background: {colors['soft_border']}; margin: 4px 8px; }}
QToolTip {{ color: {colors['text']}; background: {colors['panel']};
            border: 1px solid {colors['border']}; }}
QWidget#svgPreview {{ background: {colors['panel']}; }}
QLabel#statusGood {{ color: {colors['good']}; }}
QLabel#statusWarn {{ color: {colors['warn']}; }}
"""


def safe_stem(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return value or "wirewrap_tag"


class ColorButton(QPushButton):
    color_changed = Signal(str)

    def __init__(self, color: str):
        super().__init__()
        self._color = color
        self.clicked.connect(self.choose)
        self.set_color(color)

    def color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = QColor(color).name()
        self.setText(self._color.upper())
        foreground = "#ffffff" if QColor(self._color).lightness() < 130 else "#111111"
        self.setStyleSheet(
            f"QPushButton {{ background: {self._color}; color: {foreground}; "
            "border: 1px solid #8b96a1; min-width: 92px; }"
        )

    def choose(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._color), self, "Choose color")
        if chosen.isValid():
            self.set_color(chosen.name())
            self.color_changed.emit(self._color)


def mm_spin(value: float, minimum: float = -20.0, maximum: float = 50.0) -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(minimum, maximum)
    widget.setDecimals(3)
    widget.setSingleStep(0.1)
    widget.setSuffix(" mm")
    widget.setValue(value)
    return widget


class SettingsDialog(QDialog):
    def __init__(self, settings: TagSettings, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Design settings")
        self.resize(560, 540)
        self._source = settings
        self.controls: dict[str, QWidget] = {}

        tabs = QTabWidget()
        tabs.addTab(self._geometry_tab(), "Label && tag")
        tabs.addTab(self._text_tab(), "Text && color")
        tabs.addTab(self._page_tab(), "Print page")
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.RestoreDefaults
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)
        self.load(settings)

    def _geometry_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        entries = [
            ("side_margin_mm", "Width beyond each pin row", mm_spin(2.0, 0.2, 20.0)),
            ("end_margin_mm", "Extension past top/bottom pins", mm_spin(2.2, 0.2, 20.0)),
            ("pitch_mm", "Pin pitch", mm_spin(2.54, 0.5, 10.0)),
            ("hole_diameter_mm", "Pin-hole diameter", mm_spin(1.15, 0.2, 5.0)),
            ("corner_radius_mm", "Corner radius", mm_spin(0.8, 0.0, 10.0)),
            ("notch_width_mm", "Orientation-notch width", mm_spin(4.0, 0.0, 20.0)),
            ("notch_depth_mm", "Label notch depth", mm_spin(1.4, 0.0, 10.0)),
            ("thickness_mm", "3D tag thickness", mm_spin(0.8, 0.2, 5.0)),
        ]
        for key, label, control in entries:
            self.controls[key] = control
            form.addRow(label, control)
        window = QCheckBox("Cut out the center of the 3D tag")
        self.controls["center_window"] = window
        form.addRow("Center window", window)
        window_margin = mm_spin(1.5, 0.1, 20.0)
        self.controls["center_window_margin_mm"] = window_margin
        form.addRow("Window edge margin", window_margin)
        return page

    def _text_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        pin_size = mm_spin(1.45, 0.5, 8.0)
        id_size = mm_spin(1.85, 0.5, 12.0)
        gap = mm_spin(0.55, -2.0, 10.0)
        x_offset = mm_spin(-0.925, -20.0, 20.0)
        y_offset = mm_spin(0.0, -50.0, 50.0)
        orientation = QComboBox()
        orientation.addItems(["Top to bottom", "Bottom to top", "Horizontal", "Upside down"])
        font = QLineEdit()
        for key, label, control in [
            ("pin_font_size_mm", "Pin-number size", pin_size),
            ("number_gap_mm", "Numbers from inside hole edge", gap),
            ("id_font_size_mm", "Part-ID size", id_size),
            ("id_x_offset_mm", "Part-ID left/right position", x_offset),
            ("id_y_offset_mm", "Part-ID top/bottom position", y_offset),
            ("id_orientation", "Part-ID orientation", orientation),
            ("font_family", "Font family", font),
        ]:
            self.controls[key] = control
            form.addRow(label, control)
        for key, label, color in [
            ("label_color", "Label background", "#ffffff"),
            ("outline_color", "Outline and holes", "#000000"),
            ("pin_number_color", "Pin numbers", "#000000"),
            ("id_color", "Part ID", "#000000"),
        ]:
            button = ColorButton(color)
            self.controls[key] = button
            form.addRow(label, button)
        return page

    def _page_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        template = QComboBox()
        template.addItems([CUSTOM_SHEET, *SHEET_TEMPLATES])
        paper = QComboBox()
        paper.addItems(PAPER_SIZES_MM)
        orientation = QComboBox()
        orientation.addItems(["Portrait", "Landscape"])
        rotation = QComboBox()
        rotation.addItems(LABEL_ROTATIONS)
        margin = mm_spin(8.0, 0.0, 40.0)
        spacing = mm_spin(3.0, 0.0, 30.0)
        copies = QSpinBox()
        copies.setRange(1, 500)
        for key, label, control in [
            ("sheet_template", "Label-sheet stock", template),
            ("paper_size", "Paper size", paper),
            ("page_orientation", "Page orientation", orientation),
            ("page_margin_mm", "Page margin", margin),
            ("label_spacing_mm", "Space between labels", spacing),
            ("label_rotation", "Tag rotation in each label", rotation),
            ("copies", "Copies", copies),
        ]:
            self.controls[key] = control
            form.addRow(label, control)
        note = QLabel(
            "Avery presets use fixed Letter-sheet positions. Auto rotation turns the tag 90° "
            "when that is required to fit. Print the PDF at 100% / Actual Size."
        )
        note.setWordWrap(True)
        form.addRow(note)
        template.currentTextChanged.connect(self._update_page_controls)
        return page

    def _update_page_controls(self, value: str) -> None:
        custom = value == CUSTOM_SHEET
        for key in ("paper_size", "page_orientation", "page_margin_mm", "label_spacing_mm"):
            self.controls[key].setEnabled(custom)
        self.controls["label_rotation"].setEnabled(not custom)

    def load(self, values: TagSettings) -> None:
        for field in fields(values):
            control = self.controls.get(field.name)
            if control is None:
                continue
            value = getattr(values, field.name)
            if isinstance(control, QDoubleSpinBox) or isinstance(control, QSpinBox):
                control.setValue(value)
            elif isinstance(control, QCheckBox):
                control.setChecked(value)
            elif isinstance(control, QComboBox):
                control.setCurrentText(str(value))
            elif isinstance(control, QLineEdit):
                control.setText(str(value))
            elif isinstance(control, ColorButton):
                control.set_color(str(value))
        self._update_page_controls(values.sheet_template)

    def restore_defaults(self) -> None:
        defaults = TagSettings(
            pins=self._source.pins,
            width_mil=self._source.width_mil,
            part_id=self._source.part_id,
        )
        self.load(defaults)

    def result_settings(self) -> TagSettings:
        values = {field.name: getattr(self._source, field.name) for field in fields(self._source)}
        for key, control in self.controls.items():
            if isinstance(control, (QDoubleSpinBox, QSpinBox)):
                values[key] = control.value()
            elif isinstance(control, QCheckBox):
                values[key] = control.isChecked()
            elif isinstance(control, QComboBox):
                values[key] = control.currentText()
            elif isinstance(control, QLineEdit):
                values[key] = control.text()
            elif isinstance(control, ColorButton):
                values[key] = control.color()
        return TagSettings(**values)


class TagModelPreview(QWidget):
    """Lightweight isometric preview; the exported STL remains authoritative."""
    def __init__(self):
        super().__init__()
        self.settings = TagSettings()
        self.theme = "light"
        self.setMinimumSize(300, 300)

    def set_settings(self, settings: TagSettings) -> None:
        self.settings = settings
        self.update()

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(460, 420)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark = self.theme == "dark"
        painter.fillRect(self.rect(), QColor("#222830" if dark else "#fbfcfd"))
        s = self.settings
        logical_length = s.label_height_mm
        logical_width = s.label_width_mm
        scale = min((self.width() - 80) / max(logical_length, 1),
                    (self.height() - 110) / max(logical_width * 1.2, 1))
        length = logical_length * scale
        width = logical_width * scale
        depth = max(5.0, min(18.0, s.thickness_mm * scale * 0.7))
        cx, cy = self.width() / 2, self.height() / 2

        def iso(x: float, y: float, z: float = 0.0) -> QPointF:
            return QPointF(cx + x - y * 0.34, cy + y * 0.42 - z)

        x1, x2 = -length / 2, length / 2
        y1, y2 = -width / 2, width / 2
        top = QPolygonF([iso(x1, y1, depth), iso(x2, y1, depth),
                         iso(x2, y2, depth), iso(x1, y2, depth)])
        front = QPolygonF([iso(x1, y2, 0), iso(x2, y2, 0),
                           iso(x2, y2, depth), iso(x1, y2, depth)])
        side = QPolygonF([iso(x2, y1, 0), iso(x2, y2, 0),
                          iso(x2, y2, depth), iso(x2, y1, depth)])
        painter.setPen(QPen(QColor("#526474"), 1.2))
        painter.setBrush(QColor("#9aabb9"))
        painter.drawPolygon(front)
        painter.setBrush(QColor("#8194a5"))
        painter.drawPolygon(side)
        painter.setBrush(QColor("#dfe7ed"))
        painter.drawPolygon(top)

        hole_radius = max(2.0, s.hole_diameter_mm * scale / 2)
        row_y = s.row_spacing_mm * scale / 2
        first_x = x1 + s.end_margin_mm * scale
        painter.setBrush(QColor("#33404b"))
        painter.setPen(QPen(QColor("#edf2f5"), 0.7))
        for index in range(s.pins // 2):
            x = first_x + index * s.pitch_mm * scale
            for y in (-row_y, row_y):
                point = iso(x, y, depth + 0.2)
                painter.drawEllipse(point, hole_radius, hole_radius * 0.58)

        painter.setPen(QColor("#d4dde5" if dark else "#425466"))
        info = (f"{s.label_height_mm:.2f} × {s.label_width_mm:.2f} × "
                f"{s.thickness_mm:.2f} mm")
        painter.drawText(QRectF(12, self.height() - 38, self.width() - 24, 25),
                         Qt.AlignmentFlag.AlignCenter, info)


class SvgPreview(QSvgWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.setObjectName("svgPreview")

    def set_svg(self, source: str) -> None:
        self.load(QByteArray(source.encode("utf-8")))
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)


def write_pdf(svg_pages: str | list[str], path: Path, settings: TagSettings) -> None:
    from PySide6.QtCore import QMarginsF
    from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter

    page_w, page_h = page_dimensions(settings)
    writer = QPdfWriter(str(path))
    writer.setResolution(300)
    writer.setPageSize(QPageSize(QSizeF(page_w, page_h),
                                 QPageSize.Unit.Millimeter, effective_paper_size(settings)))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    painter = QPainter(writer)
    pages = [svg_pages] if isinstance(svg_pages, str) else svg_pages
    for index, svg in enumerate(pages):
        if index:
            writer.newPage()
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        renderer.render(painter, QRectF(0, 0, writer.width(), writer.height()))
    painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wire-Wrap Tag Designer")
        self.resize(1120, 720)
        self.app_settings = QSettings("WireWrapTools", "TagDesigner")
        self.theme_preference = str(self.app_settings.value("theme", "system")).lower()
        if self.theme_preference not in THEME_NAMES:
            self.theme_preference = "system"
        self.theme = resolve_theme(self.theme_preference)
        QApplication.instance().setStyleSheet(app_style(self.theme))
        self.settings = self.load_settings()
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(100)
        self.preview_timer.timeout.connect(self.refresh_preview)
        self._build_ui()
        self.refresh_preview()

    def _build_ui(self) -> None:
        self._build_menu()
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(18, 18, 18, 14)

        header = QFrame(objectName="header")
        header_layout = QVBoxLayout(header)
        title = QLabel("Wire-Wrap Tag Designer", objectName="title")
        subtitle = QLabel("Design once · print labels at exact size · export a matching STL", objectName="subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        outer.addWidget(header)

        content = QHBoxLayout()
        content.setSpacing(14)
        outer.addLayout(content, 1)

        controls = QGroupBox("Quick setup")
        controls.setFixedWidth(330)
        control_layout = QVBoxLayout(controls)
        form = QFormLayout()
        self.part_id = QLineEdit(self.settings.part_id)
        self.part_id.setPlaceholderText("e.g. IC12 or CPU1")
        self.pins = QSpinBox()
        self.pins.setRange(4, 256)
        self.pins.setSingleStep(2)
        self.pins.setValue(self.settings.pins)
        self.width = QComboBox()
        for item in STANDARD_WIDTHS_MIL:
            self.width.addItem(f"{item} mil  ({item * 0.0254:.2f} mm)", item)
        self.width.setCurrentIndex(STANDARD_WIDTHS_MIL.index(self.settings.width_mil))
        form.addRow("Device / part ID", self.part_id)
        form.addRow("Number of pins", self.pins)
        form.addRow("Pin-row width", self.width)
        control_layout.addLayout(form)

        dimensions = QLabel(objectName="dimensions")
        dimensions.setWordWrap(True)
        self.dimensions = dimensions
        control_layout.addWidget(dimensions)

        settings_button = QPushButton("Design && print settings…")
        settings_button.clicked.connect(self.open_settings)
        control_layout.addWidget(settings_button)

        output_group = QGroupBox("Save to")
        output_layout = QVBoxLayout(output_group)
        output_row = QHBoxLayout()
        default_output = self.app_settings.value("output_dir", str(Path.cwd()))
        self.output_dir = QLineEdit(str(default_output))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.choose_output_dir)
        output_row.addWidget(self.output_dir, 1)
        output_row.addWidget(browse)
        output_layout.addLayout(output_row)
        control_layout.addWidget(output_group)

        generate = QPushButton("Generate label + printable page + STL", objectName="primary")
        generate.clicked.connect(self.generate_all)
        control_layout.addWidget(generate)
        export_row = QHBoxLayout()
        label_button = QPushButton("Label only…")
        label_button.clicked.connect(self.export_label)
        stl_button = QPushButton("STL only…")
        stl_button.clicked.connect(self.export_stl)
        export_row.addWidget(label_button)
        export_row.addWidget(stl_button)
        control_layout.addLayout(export_row)
        control_layout.addStretch()

        openscad = find_openscad()
        self.tool_status = QLabel(
            "OpenSCAD found — STL export ready" if openscad else
            "OpenSCAD not found — SVG/PDF works; STL needs OpenSCAD",
            objectName="statusGood" if openscad else "statusWarn",
        )
        self.tool_status.setWordWrap(True)
        control_layout.addWidget(self.tool_status)
        content.addWidget(controls)

        previews = QTabWidget()
        self.label_preview = SvgPreview()
        self.model_preview = TagModelPreview()
        self.model_preview.set_theme(self.theme)
        self.page_preview = SvgPreview()
        previews.addTab(self.label_preview, "Label preview")
        previews.addTab(self.model_preview, "3D tag preview")
        previews.addTab(self.page_preview, "Print sheet")
        content.addWidget(previews, 1)

        self.status = QLabel("Ready", objectName="secondaryText")
        outer.addWidget(self.status)

        self.part_id.textChanged.connect(self.schedule_preview)
        self.pins.valueChanged.connect(self.normalize_pins)
        self.pins.valueChanged.connect(self.schedule_preview)
        self.width.currentIndexChanged.connect(self.schedule_preview)

    def _build_menu(self) -> None:
        settings_menu = self.menuBar().addMenu("&Settings")
        advanced = QAction("Design && print settings…", self)
        advanced.setObjectName("advancedSettingsAction")
        advanced.setShortcut("Ctrl+,")
        advanced.triggered.connect(self.open_settings)
        settings_menu.addAction(advanced)
        settings_menu.addSeparator()

        theme_menu = settings_menu.addMenu("Appearance")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for key, label in (
            ("system", "Use system theme"),
            ("light", "Light mode"),
            ("dark", "Dark mode"),
        ):
            action = QAction(label, self, checkable=True)
            action.setChecked(key == self.theme_preference)
            action.triggered.connect(lambda checked=False, value=key: self.set_theme(value))
            theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[key] = action

    def set_theme(self, preference: str) -> None:
        if preference not in THEME_NAMES:
            return
        self.theme_preference = preference
        self.theme = resolve_theme(preference)
        if hasattr(self, "theme_actions"):
            self.theme_actions[preference].setChecked(True)
        self.app_settings.setValue("theme", preference)
        QApplication.instance().setStyleSheet(app_style(self.theme))
        if hasattr(self, "model_preview"):
            self.model_preview.set_theme(self.theme)

    def normalize_pins(self, value: int) -> None:
        if value % 2:
            self.pins.setValue(value + 1)

    def current_settings(self) -> TagSettings:
        self.settings.part_id = self.part_id.text().strip() or "UNTITLED"
        self.settings.pins = self.pins.value()
        self.settings.width_mil = int(self.width.currentData())
        return self.settings

    def schedule_preview(self, *args) -> None:
        self.preview_timer.start()

    def refresh_preview(self) -> None:
        try:
            current = self.current_settings()
            self.label_preview.set_svg(label_svg(current))
            self.page_preview.set_svg(label_page_svg(current, show_guides=True))
            self.model_preview.set_settings(current)
            columns, rows, capacity = page_layout(current)
            sheet_name = current.sheet_template if current.sheet_template != CUSTOM_SHEET else current.paper_size
            self.dimensions.setText(
                f"Finished tag: {current.label_width_mm:.2f} × {current.label_height_mm:.2f} mm\n"
                f"{sheet_name}: {columns} × {rows} grid, up to {capacity} labels"
            )
            self.status.setText("Preview updated")
        except ValueError as exc:
            self.status.setText(str(exc))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.current_settings(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.result_settings()
            self.refresh_preview()
            self.save_settings()

    def choose_output_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir.text())
        if selected:
            self.output_dir.setText(selected)
            self.app_settings.setValue("output_dir", selected)

    def _default_path(self, suffix: str) -> Path:
        return Path(self.output_dir.text()).expanduser() / f"{safe_stem(self.current_settings().part_id)}{suffix}"

    def export_label(self) -> None:
        suggested = self._default_path("_label.svg")
        selected, _ = QFileDialog.getSaveFileName(self, "Save label SVG", str(suggested), "SVG files (*.svg)")
        if selected:
            try:
                write_label_svg(self.current_settings(), selected)
                self.status.setText(f"Saved {selected}")
            except Exception as exc:
                self.show_error(exc)

    def export_stl(self) -> None:
        suggested = self._default_path("_tag.stl")
        selected, _ = QFileDialog.getSaveFileName(self, "Save tag STL", str(suggested), "STL files (*.stl)")
        if selected:
            try:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                render_stl(self.current_settings(), selected)
                self.status.setText(f"Saved {selected}")
            except Exception as exc:
                self.show_error(exc)
            finally:
                QApplication.restoreOverrideCursor()

    def generate_all(self) -> None:
        try:
            current = self.current_settings()
            current.validate()
            output = Path(self.output_dir.text()).expanduser()
            output.mkdir(parents=True, exist_ok=True)
            stem = safe_stem(current.part_id)
            paper_name = effective_paper_size(current).lower()
            label_path = write_label_svg(current, output / f"{stem}_label.svg")
            svg_pages = label_page_svgs(current)
            page_paths = []
            for index, svg_page in enumerate(svg_pages, start=1):
                page_suffix = f"_page{index}" if len(svg_pages) > 1 else ""
                page_path = output / f"{stem}_{paper_name}_sheet{page_suffix}.svg"
                page_path.write_text(svg_page, encoding="utf-8")
                page_paths.append(page_path)
            pdf_path = output / f"{stem}_{paper_name}_sheet.pdf"
            write_pdf(svg_pages, pdf_path, current)
            scad_path = write_scad(current, output / f"{stem}_tag.scad")
            settings_path = output / f"{stem}_settings.json"
            settings_path.write_text(current.to_json(), encoding="utf-8")
            generated = [label_path.name, *(path.name for path in page_paths),
                         pdf_path.name, scad_path.name, settings_path.name]
            if find_openscad():
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                stl_path = render_stl(current, output / f"{stem}_tag.stl")
                generated.append(stl_path.name)
            self.save_settings()
            self.status.setText(f"Generated {len(generated)} files in {output}")
            box = QMessageBox(self)
            box.setWindowTitle("Files generated")
            box.setIcon(QMessageBox.Icon.Information)
            box.setText(f"Your label and tag files are ready in:\n{output}")
            box.setInformativeText("Print the PDF at 100% / Actual Size.\n\n" + "\n".join(generated))
            open_button = box.addButton("Open folder", QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Close)
            box.exec()
            if box.clickedButton() is open_button:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(output)))
        except Exception as exc:
            self.show_error(exc)
        finally:
            QApplication.restoreOverrideCursor()

    def show_error(self, error: Exception) -> None:
        self.status.setText(str(error))
        QMessageBox.critical(self, "Could not generate files", str(error))

    def load_settings(self) -> TagSettings:
        raw = self.app_settings.value("tag_settings", "")
        if raw:
            try:
                return TagSettings.from_json(str(raw))
            except (ValueError, TypeError):
                pass
        return TagSettings()

    def save_settings(self) -> None:
        self.app_settings.setValue("tag_settings", self.current_settings().to_json())
        self.app_settings.setValue("output_dir", self.output_dir.text())

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.save_settings()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Wire-Wrap Tag Designer")
    app.setOrganizationName("WireWrapTools")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
