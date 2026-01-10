"""Scripts for running development tools."""

import subprocess
import sys


def fmt():
    """Run ruff formatter."""
    result = subprocess.run(["ruff", "format", "."], cwd=".")
    sys.exit(result.returncode)


def lint():
    """Run ruff linter."""
    result = subprocess.run(["ruff", "check", "."], cwd=".")
    sys.exit(result.returncode)
