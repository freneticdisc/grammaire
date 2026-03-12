#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#  "rich"
# ]
# requires-python = ">=3.12"
# ///
from pathlib import Path

from rich.console import Console

APP_DIR = Path.home() / ".atlassian"
BROWSERS_CACHE = APP_DIR / "browsers"
CONFIG_FILE = APP_DIR / "config.json"

if __name__ == "__main__":
    Console().print_json(
        data={
            "application_dir": str(APP_DIR),
            "browsers_cache": str(BROWSERS_CACHE),
            "config_file": str(CONFIG_FILE),
            "success": True
        },
        indent=2
    )
