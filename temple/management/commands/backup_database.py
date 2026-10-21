import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a consistent SQLite or PostgreSQL backup and prune old backups."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=os.environ.get("TEMPLE_BACKUP_DIR", ""))
        parser.add_argument("--keep-days", type=int, default=30)

    def handle(self, *args, **options):
        keep_days = options["keep_days"]
        if keep_days < 1:
            raise CommandError("--keep-days must be at least 1.")

        output_dir = Path(options["output_dir"]) if options["output_dir"] else settings.BASE_DIR / "backups"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d-%H%M%S")
        engine = settings.DATABASES["default"]["ENGINE"]

        if engine.endswith("sqlite3"):
            backup_path = output_dir / f"temple-backup-{timestamp}.sqlite3"
            self._backup_sqlite(backup_path)
            pattern = "temple-backup-*.sqlite3"
        elif engine.endswith("postgresql"):
            backup_path = output_dir / f"temple-backup-{timestamp}.dump"
            self._backup_postgres(backup_path)
            pattern = "temple-backup-*.dump"
        else:
            raise CommandError(f"Unsupported database engine: {engine}")

        self._prune(output_dir, pattern, keep_days)
        self.stdout.write(self.style.SUCCESS(f"Database backup created: {backup_path}"))

    def _backup_sqlite(self, backup_path):
        connection.ensure_connection()
        destination = sqlite3.connect(str(backup_path))
        try:
            connection.connection.backup(destination)
        finally:
            destination.close()
        try:
            backup_path.chmod(0o600)
        except OSError:
            pass

    def _backup_postgres(self, backup_path):
        database = settings.DATABASES["default"]
        pg_dump = shutil.which("pg_dump")
        if not pg_dump:
            raise CommandError("pg_dump is required for PostgreSQL backups; install the PostgreSQL client tools.")

        environment = os.environ.copy()
        environment.update({
            "PGHOST": str(database.get("HOST", "")),
            "PGPORT": str(database.get("PORT", "5432")),
            "PGDATABASE": str(database["NAME"]),
            "PGUSER": str(database.get("USER", "")),
            "PGPASSWORD": str(database.get("PASSWORD", "")),
        })
        try:
            subprocess.run(
                [pg_dump, "--format=custom", "--no-owner", "--file", str(backup_path)],
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            backup_path.unlink(missing_ok=True)
            detail = (exc.stderr or "").strip().splitlines()
            raise CommandError(detail[-1] if detail else "pg_dump failed; verify database connectivity and credentials.") from exc
        except OSError as exc:
            backup_path.unlink(missing_ok=True)
            raise CommandError("PostgreSQL backup could not be started.") from exc

    def _prune(self, output_dir, pattern, keep_days):
        cutoff = datetime.now().timestamp() - timedelta(days=keep_days).total_seconds()
        for path in output_dir.glob(pattern):
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
