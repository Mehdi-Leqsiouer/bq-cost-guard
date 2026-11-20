import subprocess
from pathlib import Path


def changed_files(base: str, cwd: Path) -> set[Path]:
    """Absolute paths of files added/changed/modified/renamed between `base` and HEAD."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--relative", "--diff-filter=ACMR", f"{base}...HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {(cwd / line).resolve() for line in out.splitlines() if line}
