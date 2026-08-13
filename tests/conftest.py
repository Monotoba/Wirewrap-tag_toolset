"""Shared test configuration."""

import os


# GUI smoke tests should never require or open a desktop session.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
