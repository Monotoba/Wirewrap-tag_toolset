from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_posix_setup_updates_build_backend_before_editable_install():
    script = (PROJECT_ROOT / "scripts" / "setup.sh").read_text(encoding="utf-8")

    upgrade = 'pip install --upgrade "setuptools>=77" wheel'
    editable = "pip install --no-build-isolation --editable"

    assert upgrade in script
    assert script.index(upgrade) < script.index(editable)


def test_windows_setup_updates_build_backend_before_editable_install():
    script = (PROJECT_ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")

    upgrade = 'pip install --upgrade "setuptools>=77" wheel'
    editable = "pip install --no-build-isolation --editable"

    assert upgrade in script
    assert script.index(upgrade) < script.index(editable)
