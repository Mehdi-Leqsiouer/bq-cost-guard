from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

DEFAULT_CONFIG_FILE = Path(".bqcostguard.yaml")


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_per_tib: float = 6.25
    warn_cost_usd: float = 1.0
    fail_cost_usd: float = 10.0
    ignore_rules: list[str] = []


def load_config(path: Path | None = None) -> Config:
    """Load config from `path` (or the default file); defaults if the default is missing."""
    path = path or DEFAULT_CONFIG_FILE
    if not path.exists():
        return Config()
    return Config(**(yaml.safe_load(path.read_text()) or {}))
