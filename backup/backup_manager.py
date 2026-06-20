"""
backup_manager.py — local + GCS backup after each research cycle.

Usage:
    python backup/backup_manager.py --local          # local backup only
    python backup/backup_manager.py --gcs            # local + GCS upload
    python backup/backup_manager.py                  # default: local + GCS
"""
import argparse
import os
import shutil
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKUP_DIR = ROOT / "backups"

FILES_TO_BACKUP = [
    "data/alpha_store.db",
    "data/theory_log.json",
    "data/research_status.json",
    "mcp_skill.md",
    "docs/legacy_sources.md",
]


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")


def _local_backup(ts: str) -> Path:
    dest = BACKUP_DIR / ts
    dest.mkdir(parents=True, exist_ok=True)
    backed = []
    for rel in FILES_TO_BACKUP:
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, dest / src.name)
            backed.append(src.name)
    print(f"[backup] Local → {dest}  ({len(backed)} files: {backed})")
    return dest


def _prune_local(keep_days: int = 7) -> None:
    from datetime import timedelta
    cutoff = datetime.now(UTC) - timedelta(days=keep_days)
    for folder in BACKUP_DIR.iterdir():
        if not folder.is_dir():
            continue
        try:
            dt = datetime.strptime(folder.name[:16], "%Y-%m-%d_%H-%M").replace(tzinfo=UTC)
            if dt < cutoff:
                shutil.rmtree(folder)
                print(f"[backup] Pruned old backup: {folder.name}")
        except ValueError:
            pass


def _gcs_upload(local_dir: Path, bucket: str) -> None:
    try:
        from google.cloud import storage as gcs
        client = gcs.Client()
        b = client.bucket(bucket.replace("gs://", ""))
        count = 0
        for f in local_dir.iterdir():
            blob_name = f"backups/{local_dir.name}/{f.name}"
            blob = b.blob(blob_name)
            blob.upload_from_filename(str(f))
            count += 1
        print(f"[backup] GCS → {bucket}/backups/{local_dir.name}  ({count} files)")
    except ImportError:
        print("[backup] google-cloud-storage not installed — skipping GCS upload.")
    except Exception as e:
        print(f"[backup] GCS upload failed: {e}")


def run(do_gcs: bool = True) -> None:
    ts       = _timestamp()
    local    = _local_backup(ts)
    _prune_local(keep_days=7)
    if do_gcs:
        bucket = os.getenv("GCS_BACKUP_BUCKET", "")
        if bucket:
            _gcs_upload(local, bucket)
        else:
            print("[backup] GCS_BACKUP_BUCKET not set — skipping GCS upload.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="Local backup only (no GCS)")
    ap.add_argument("--gcs",   action="store_true", help="Local + GCS upload")
    args = ap.parse_args()
    run(do_gcs=not args.local)
