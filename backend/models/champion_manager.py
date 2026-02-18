from pathlib import Path
import json
from datetime import datetime, timezone


def load_champion(model_dir: Path):
    path = model_dir / "champion.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def promote_champion(
    model_dir: Path,
    model_name: str,
    version: int,
    metrics: dict,
    reason: str,
):
    champion = {
        "model_name": model_name,
        "version": version,
        "metrics": metrics,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }

    (model_dir / "champion.json").write_text(
        json.dumps(champion, indent=2)
    )