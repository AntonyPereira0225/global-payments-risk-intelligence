"""Run the complete local synthetic-data pipeline in the correct order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "src" / "generate_dimensions.py",
    ROOT / "src" / "generate_transactions.py",
    ROOT / "src" / "validate_data.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\n=== Running {script.name} ===")
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
    print("\nSynthetic payments pipeline completed successfully.")


if __name__ == "__main__":
    main()
