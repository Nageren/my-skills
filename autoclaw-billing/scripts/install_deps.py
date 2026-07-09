#!/usr/bin/env python3
"""Install Python dependencies into the current local Python environment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"


def main() -> int:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "-r",
        str(REQUIREMENTS),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
