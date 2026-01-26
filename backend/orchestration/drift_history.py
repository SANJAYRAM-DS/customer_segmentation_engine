from pathlib import Path
import json
from datetime import datetime, timezone


def save_drift_report(model: str, report: dict, project_root: Path):
    drift_dir = project_root / "backend" / "monitoring" / "drift" / model
    drift_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    report["timestamp"] = ts

    # save point-in-time report
    report_path = drift_dir / f"drift_{ts.replace(':', '-')}.json"
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)

    # append to history
    history_path = drift_dir / "history.json"
    if history_path.exists():
        history = json.loads(history_path.read_text())
    else:
        history = []

    history.append(report)

    with history_path.open("w") as f:
        json.dump(history, f, indent=2)

    return report_path
