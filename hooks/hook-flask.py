"""Runtime hook to set Flask environment variables."""

import os


def pre_init():
    """Set Flask environment variables before app initialization."""
    os.environ["FLASK_ENV"] = "production"
    os.environ["FLASK_DEBUG"] = "0"
