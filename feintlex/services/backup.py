from __future__ import annotations

"""Progress backup: months of mastery in one un-backed-up SQLite file
is a bad bet. Creates a timestamped zip holding a HOT copy of the
database (via the sqlite3 backup API, safe while the server runs and
on drives with aggressive file locking) plus every export.
"""

import logging
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from feintlex.config import PROJECT_ROOT, Settings, get_settings


LOGGER = logging.getLogger("feintlex.backup")


def create_backup(
    *,
    settings: Settings | None = None,
    dest_dir: Path | str | None = None,
) -> dict[str, object]:
    settings = settings or get_settings()
    destination = Path(dest_dir) if dest_dir else PROJECT_ROOT / "backups"
    destination.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = destination / f"feintlex-backup-{stamp}.zip"

    db_path = settings.resolved_db_path
    files_added = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            if db_path.exists():
                # Hot copy via the sqlite backup API — consistent even if
                # the server holds the file open.
                snapshot = Path(tmp_dir) / db_path.name
                source = sqlite3.connect(str(db_path))
                target = sqlite3.connect(str(snapshot))
                with target:
                    source.backup(target)
                source.close()
                target.close()
                archive.write(snapshot, arcname=f"data/{db_path.name}")
                files_added += 1

            export_dir = settings.resolved_export_dir
            if export_dir.exists():
                for exported in sorted(export_dir.iterdir()):
                    if exported.is_file() and exported.suffix in {".md", ".tsv", ".csv", ".txt"}:
                        archive.write(exported, arcname=f"exports/{exported.name}")
                        files_added += 1

    if files_added == 0:
        archive_path.unlink(missing_ok=True)
        raise ValueError("Nothing to back up yet: no database or exports found.")

    size_kb = archive_path.stat().st_size // 1024
    LOGGER.info("backup_created", extra={"path": str(archive_path), "files": files_added, "size_kb": size_kb})
    return {"path": str(archive_path), "files": files_added, "size_kb": size_kb}
