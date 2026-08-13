"""Allow ``python -m wirewrap_tag_designer`` to launch the GUI."""

from .gui import main


if __name__ == "__main__":
    raise SystemExit(main())
