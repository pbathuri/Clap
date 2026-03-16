from __future__ import annotations

import subprocess
import sys


def main() -> None:
    rc = subprocess.call(
        [sys.executable, "-m", "workflow_dataset.cli", "build", "--config", "configs/settings.yaml"],
        cwd=".",
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
