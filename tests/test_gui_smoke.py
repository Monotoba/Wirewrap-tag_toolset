from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QLabel

from wirewrap_tag_designer.gui import MainWindow, SettingsDialog, app_style


def test_main_window_builds_valid_svg_previews():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.refresh_preview()

    assert window.label_preview.renderer().isValid()
    assert window.page_preview.renderer().isValid()
    assert window.current_settings().pins >= 4

    window.deleteLater()
    app.processEvents()


def test_settings_are_discoverable_and_form_labels_are_visible():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    action = window.findChild(QAction, "advancedSettingsAction")

    assert action is not None
    assert action.shortcut().toString()

    dialog = SettingsDialog(window.current_settings(), window)
    labels = [label.text() for label in dialog.findChildren(QLabel)]
    assert "Width beyond each pin row" in labels
    assert "Font family" in labels
    assert "Label-sheet stock" in labels
    assert "Tag rotation in each label" in labels
    assert "Paper size" in labels

    dialog.deleteLater()
    window.deleteLater()
    app.processEvents()


def test_light_and_dark_styles_define_text_and_background_colors():
    light = app_style("light")
    dark = app_style("dark")

    assert "QWidget { color: #1d2730; }" in light
    assert "QMainWindow, QDialog { background: #f4f6f8; }" in light
    assert "QWidget { color: #edf1f5; }" in dark
    assert "QMainWindow, QDialog { background: #171b20; }" in dark
