import json
from pathlib import Path


def is_dbt_project(path: Path) -> bool:
    return (path / "dbt_project.yml").exists()


def compiled_models(project: Path) -> dict[Path, Path]:
    """Map each model's source file (absolute) to its compiled SQL file.

    Uses target/manifest.json when present, else falls back to target/compiled/**/*.sql
    (keyed by the compiled path itself, so --git-diff cannot match them).
    """
    project = project.resolve()
    manifest = project / "target" / "manifest.json"
    if manifest.exists():
        nodes = json.loads(manifest.read_text()).get("nodes", {})
        found = {
            (project / n["original_file_path"]): project / n["compiled_path"]
            for n in nodes.values()
            if n.get("resource_type") == "model" and n.get("original_file_path") and n.get("compiled_path")
        }
        return {src: c for src, c in found.items() if c.exists()}
    return {p: p for p in (project / "target" / "compiled").rglob("*.sql")}
