"""
restore.py — restore data from a backup snapshot.

Usage:
    python backup/restore.py --latest --source local
    python backup/restore.py --latest --source gcs
    python backup/restore.py --timestamp 2026-06-19_14-30 --source local
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKUP_DIR = ROOT / "backups"


def _latest_local() -> Path | None:
    candidates = [d for d in BACKUP_DIR.iterdir() if d.is_dir()]
    return max(candidates, key=lambda d: d.name) if candidates else None


def _latest_gcs(bucket: str) -> str | None:
    try:
        from google.cloud import storage as gcs
        client = gcs.Client()
        b = client.bucket(bucket.replace("gs://", ""))
        blobs = list(b.list_blobs(prefix="backups/"))
        timestamps = sorted({b.name.split("/")[1] for b in blobs if len(b.name.split("/")) > 2})
        return timestamps[-1] if timestamps else None
    except Exception as e:
        print(f"[restore] GCS error: {e}")
        return None


def _restore_local(ts_dir: Path) -> None:
    for f in ts_dir.iterdir():
        dest = ROOT / "data" / f.name
        if f.name == "legacy_sources.md":
            dest = ROOT / "docs" / f.name
        print(f"  {f} -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)


def _restore_gcs(ts: str, bucket: str) -> None:
    try:
        from google.cloud import storage as gcs
        client = gcs.Client()
        b = client.bucket(bucket.replace("gs://", ""))
        blobs = list(b.list_blobs(prefix=f"backups/{ts}/"))
        for blob in blobs:
            fname = blob.name.split("/")[-1]
            if fname == "legacy_sources.md":
                dest = ROOT / "docs" / fname
            else:
                dest = ROOT / "data" / fname
            print(f"  gs://{bucket}/{blob.name} -> {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(dest))
    except ImportError:
        print("[restore] google-cloud-storage not installed.")
    except Exception as e:
        print(f"[restore] GCS restore error: {e}")


def run(source: str, timestamp: str | None) -> None:
    print(f"[restore] source={source} ts={timestamp or 'latest'}")

    if source == "local":
        if timestamp:
            ts_dir = BACKUP_DIR / timestamp
        else:
            ts_dir = _latest_local()
        if not ts_dir or not ts_dir.exists():
            print("[restore] No local backup found.")
            sys.exit(1)
        print(f"[restore] Restoring from: {ts_dir}")
        _restore_local(ts_dir)

    elif source == "gcs":
        bucket = os.getenv("GCS_BACKUP_BUCKET", "")
        if not bucket:
            print("[restore] GCS_BACKUP_BUCKET env var not set.")
            sys.exit(1)
        ts = timestamp or _latest_gcs(bucket)
        if not ts:
            print("[restore] No GCS backup found.")
            sys.exit(1)
        print(f"[restore] Restoring from GCS: {ts}")
        _restore_gcs(ts, bucket)

    print("[restore] Restore complete.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source",    choices=["local", "gcs"], default="local")
    ap.add_argument("--timestamp", default=None, help="e.g. 2026-06-19_14-30")
    ap.add_argument("--latest",    action="store_true", help="Use the most recent backup")
    args = ap.parse_args()
    run(source=args.source, timestamp=args.timestamp)
