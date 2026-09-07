import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import periodic_task


logger = logging.getLogger(__name__)


def snapshot_database():
    """
    Write a consistent copy of the SQLite database for the backup to pick up.

    The database runs in WAL mode, so recently committed transactions live in a
    `-wal` sidecar until a checkpoint moves them into the main file. rsync is
    not atomic across that pair, so a checkpoint landing mid-copy can produce a
    backup that is silently missing commits. `VACUUM INTO` is consistent
    against a live database and needs no downtime.

    Deliberately uses a plain sqlite3 connection rather than the ORM: VACUUM
    cannot run inside a transaction, and this needs none of Django's state.
    """
    dest = Path(settings.FORMBUILDER_DB_SNAPSHOT_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # VACUUM INTO refuses to overwrite, so build beside the target and rename.
    # The rename is atomic, so a concurrent rsync sees either the previous
    # snapshot or the new one, never a half-written file.
    tmp = dest.with_name(f"{dest.name}.{os.getpid()}.tmp")

    try:
        source = str(settings.DATABASES["default"]["NAME"])
        # isolation_level=None keeps the connection in autocommit; otherwise
        # Python opens an implicit transaction and VACUUM is refused.
        with closing(sqlite3.connect(source, timeout=30, isolation_level=None)) as conn:
            conn.execute("VACUUM INTO ?", (str(tmp),))

        with closing(sqlite3.connect(tmp)) as check:
            (result,) = check.execute("PRAGMA integrity_check").fetchone()
        if result != "ok":
            raise RuntimeError(f"snapshot failed integrity_check: {result}")

        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)

    logger.info("DB snapshot: wrote %s (%s bytes)", dest, dest.stat().st_size)
    return dest


@periodic_task(crontab(minute="0"))
def snapshot_database_task():
    snapshot_database()
