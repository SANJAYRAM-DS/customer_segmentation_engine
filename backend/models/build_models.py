# backend/models/build_models.py

from datetime import datetime, timezone
import traceback
import time


def timed_step(name: str, fn):
    print(f"\n[START] {name}")
    start = time.perf_counter()
    try:
        fn()
        elapsed = time.perf_counter() - start
        print(f"[DONE] {name} ({elapsed:.2f}s)")
    except Exception:
        print(f"[FAILED] {name}")
        traceback.print_exc()
        raise


def main():
    print("=" * 60)
    print("[MODEL PIPELINE] STARTED")
    print("Timestamp:", datetime.now(timezone.utc).isoformat())
    print("=" * 60)

    # -------------------------
    # CHURN
    # -------------------------
    from backend.models.churn.train import main as train_churn

    timed_step(
        "Churn model training",
        train_churn,
    )

    # -------------------------
    # CLV
    # -------------------------
    from backend.models.clv.train import main as train_clv

    timed_step(
        "CLV model training",
        train_clv,
    )

    # -------------------------
    # SEGMENTATION
    # -------------------------
    from backend.models.segmentation.train import main as train_segmentation

    timed_step(
        "Segmentation model training",
        train_segmentation,
    )

    print("\n" + "=" * 60)
    print("[MODEL PIPELINE] COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()