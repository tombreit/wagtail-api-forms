from datetime import timedelta

import pytest

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.utils import timezone

from wagtail_api_forms.home.tasks import clear_expired_sessions_task


def create_session(expire_date):
    session = SessionStore()
    session["formpage-1-submission"] = "id"
    session.save()
    Session.objects.filter(session_key=session.session_key).update(
        expire_date=expire_date
    )
    return session.session_key


@pytest.mark.django_db
def test_clear_expired_sessions_task():
    now = timezone.now()
    expired = create_session(now - timedelta(minutes=1))
    valid = create_session(now + timedelta(days=1))

    clear_expired_sessions_task.call_local()

    assert list(Session.objects.values_list("session_key", flat=True)) == [valid]
    assert expired != valid
