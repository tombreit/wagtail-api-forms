from django.core.management import call_command
from huey import crontab
from huey.contrib.djhuey import periodic_task
from sqlite_snapshot.contrib.django import snapshot_database


@periodic_task(crontab(minute="0"))
def snapshot_database_task():
    """
    Write settings.SQLITE_SNAPSHOT_PATH, a consistent copy of the WAL database
    for the backup to pick up instead of the live db.sqlite3.
    """
    snapshot_database()


@periodic_task(crontab(minute="30", hour="3"))
def clear_expired_sessions_task():
    """
    Django doesn't delete expired sessions on its own. Each form submission
    creates one (see FormPage.render_landing_page), holding the submission's
    id for the thank-you page.
    """
    call_command("clearsessions")
