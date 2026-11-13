"""
After submitting, visitors are redirected to <form page>/thank-you/, which
optionally shows the poll results of the form's choice questions.
"""

from datetime import timedelta

import pytest

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client

from wagtail.models import PageViewRestriction

from wagtail_api_forms.formpages.models import (
    THANK_YOU_MAX_AGE,
    CustomFormSubmission,
    UserFormField,
)
from wagtail_api_forms.formpages.results import get_results
from wagtail_api_forms.formpages.tests.utils import page_title


FIELDS = [
    {"label": "Name", "field_type": "singleline", "required": False},
    {"label": "Colour", "field_type": "radio", "choices": "Red\nGreen\nBlue"},
    {
        "label": "Topics",
        "field_type": "checkboxes",
        "choices": "Law, Policy",
        "required": False,
    },
    {
        "label": "Tags",
        "field_type": "multiplechoicetypeahead",
        "choices": "One\nTwo",
        "required": False,
    },
    {"label": "Consent", "field_type": "checkbox", "required": False},
]


@pytest.fixture
def poll_page(form_page):
    form_page.thank_you_text = "<p>Thanks for voting.</p>"
    form_page.show_results = True
    form_page.save()
    for sort_order, attrs in enumerate(FIELDS):
        UserFormField.objects.create(page=form_page, sort_order=sort_order, **attrs)
    return form_page


@pytest.fixture
def thank_you_url(poll_page, form_url):
    return f"{form_url}thank-you/"


def submit(page, **form_data):
    return CustomFormSubmission.objects.create(page=page, form_data=form_data)


def as_dict(results):
    return {
        result.question: [
            (choice.label, choice.count, choice.percent, choice.chosen)
            for choice in result.choices
        ]
        for result in results
    }


# ----- Thank-you page --------------------------------------------------------


@pytest.mark.django_db
def test_submitting_redirects_to_thank_you_page(client, form_url, thank_you_url):
    response = client.post(form_url, {"colour": "Red"})

    assert response.status_code == 302
    assert response["Location"] == thank_you_url

    response = client.get(thank_you_url)
    assert response.status_code == 200
    assert response.templates[0].name == "formpages/form_page_landing.html"
    assert "Thanks for voting." in response.content.decode()
    assert response.context["form_submission"] == CustomFormSubmission.objects.get()


@pytest.mark.django_db
def test_thank_you_page_title_and_link(client, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})

    html = client.get(thank_you_url).content.decode()

    assert page_title(html).startswith("Thank you – Contact")
    assert "Fill in the form again" in html


@pytest.mark.django_db
def test_default_thank_you_text(client, poll_page, form_url, thank_you_url):
    poll_page.thank_you_text = ""
    poll_page.save()
    client.post(form_url, {"colour": "Red"})

    html = client.get(thank_you_url).content.decode()

    assert "Thank you. Your answers have been sent." in html


@pytest.mark.django_db
def test_reloading_thank_you_page_submits_nothing(client, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})

    client.get(thank_you_url)
    client.get(thank_you_url)

    assert CustomFormSubmission.objects.count() == 1


@pytest.mark.django_db
def test_thank_you_page_only_for_visitor_who_submitted(client, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})

    response = Client().get(thank_you_url)

    assert response.status_code == 302
    assert response["Location"] == form_url


@pytest.mark.django_db
def test_thank_you_page_only_for_a_while(client, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})
    submission = CustomFormSubmission.objects.get()
    CustomFormSubmission.objects.filter(pk=submission.pk).update(
        submit_time=submission.submit_time - THANK_YOU_MAX_AGE - timedelta(minutes=1)
    )

    response = client.get(thank_you_url)

    assert response.status_code == 302
    assert response["Location"] == form_url
    assert submission.page.specific.get_session_key() not in client.session


@pytest.mark.django_db
def test_thank_you_page_is_not_cached(client, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})

    response = client.get(thank_you_url)

    assert response.status_code == 200
    cache_control = response["Cache-Control"]
    assert "no-store" in cache_control
    assert "private" in cache_control


@pytest.mark.django_db
def test_submitting_changes_the_session_key(client, form_url, thank_you_url):
    """A session key planted by another site can't open the thank-you page."""
    planted = client.session
    planted["planted"] = True
    planted.save()

    client.post(form_url, {"colour": "Red"})

    assert client.cookies[settings.SESSION_COOKIE_NAME].value != planted.session_key
    assert not Session.objects.filter(session_key=planted.session_key).exists()
    assert client.get(thank_you_url).status_code == 200


@pytest.mark.django_db
def test_submitting_keeps_the_session_key_of_logged_in_users(
    client, superuser, form_url, thank_you_url
):
    client.force_login(superuser)
    session_key = client.session.session_key

    client.post(form_url, {"colour": "Red"})

    assert client.session.session_key == session_key
    assert client.get(thank_you_url).status_code == 200


@pytest.mark.django_db
def test_password_protected_form(client, poll_page, form_url, thank_you_url):
    """The thank-you page and the step validation are protected as well."""
    UserFormField.objects.create(page=poll_page, sort_order=99, field_type="pagebreak")
    UserFormField.objects.create(page=poll_page, sort_order=100, label="Last")
    submission = submit(poll_page, colour="Red")
    session = client.session
    session[poll_page.get_session_key()] = str(submission.pk)
    session.save()
    PageViewRestriction.objects.create(
        page=poll_page, restriction_type=PageViewRestriction.PASSWORD, password="secret"
    )

    for response in (
        client.get(thank_you_url),
        client.post(f"{form_url}validate-step/", {"form_step": "1"}),
    ):
        assert response.status_code == 200
        assert response.templates[0].name == "wagtailcore/password_required.html"
        assert response["Content-Type"].startswith("text/html")
        assert "Thanks for voting." not in response.content.decode()


@pytest.mark.django_db
def test_thank_you_page_of_an_unpublished_form(client, poll_page, form_url, thank_you_url):
    client.post(form_url, {"colour": "Red"})
    poll_page.unpublish()

    assert client.get(thank_you_url).status_code == 404


@pytest.mark.django_db
def test_embedded_thank_you_page_stays_embedded(client, form_url, thank_you_url):
    response = client.post(f"{form_url}?embed=true", {"colour": "Red"})
    assert response["Location"] == f"{thank_you_url}?embed=true"

    content = client.get(response["Location"]).content.decode()
    # The embedding page scrolls to the thank-you text
    assert "data-waf-submitted" in content
    assert f'href="{form_url}?embed=true"' in content

    response = Client().get(f"{thank_you_url}?embed=true")
    assert response["Location"] == f"{form_url}?embed=true"


@pytest.mark.django_db
def test_invalid_submission_stays_on_form(client, poll_page, form_url):
    response = client.post(f"{form_url}?embed=true", {"colour": "Purple"})

    assert response.status_code == 200
    assert response.templates[0].name == "formpages/form_page.html"
    assert "data-waf-submitted" in response.content.decode()
    assert not CustomFormSubmission.objects.exists()


@pytest.mark.django_db
def test_landing_page_preview(client, poll_page, superuser):
    client.force_login(superuser)

    response = client.get(f"/admin/pages/{poll_page.pk}/edit/preview/?mode=landing")

    assert response.status_code == 200


@pytest.mark.django_db
def test_landing_page_preview_renders_without_submission(rf, poll_page):
    submit(poll_page, colour="Red")
    request = rf.get("/")
    request.is_preview = True

    response = poll_page.serve_preview(request, "landing")

    assert response.status_code == 200
    assert response.context_data["form_submission"] is None
    assert as_dict(response.context_data["results"])["Colour"][0] == ("Red", 1, 100, False)


# ----- Results ---------------------------------------------------------------


@pytest.mark.django_db
def test_results_are_shown_after_submitting(client, poll_page, form_url, thank_you_url):
    submit(poll_page, colour="Blue")
    client.post(form_url, {"name": "Jane", "colour": "Red", "topics": ["Law", "Policy"]})

    response = client.get(thank_you_url)

    results = as_dict(response.context["results"])
    assert results["Colour"] == [
        ("Red", 1, 50, True),
        ("Green", 0, 0, False),
        ("Blue", 1, 50, False),
    ]
    content = response.content.decode()
    assert "Results so far" in content
    assert "Your answers are marked" in content
    # Answers to other questions are never shown
    assert "Jane" not in content


@pytest.mark.django_db
def test_no_results_unless_enabled(client, poll_page, form_url, thank_you_url):
    poll_page.show_results = False
    poll_page.save()
    client.post(form_url, {"colour": "Red"})

    response = client.get(thank_you_url)

    assert "results" not in response.context
    assert "Results so far" not in response.content.decode()


@pytest.mark.django_db
def test_only_choice_questions_are_counted(poll_page):
    submit(poll_page, name="Jane", colour="Red", consent=True)

    results = get_results(poll_page)

    assert [result.question for result in results] == ["Colour", "Topics", "Tags"]


@pytest.mark.django_db
def test_several_choices_per_answer(poll_page):
    submit(poll_page, topics=["Law", "Policy"], tags=["Two"])
    submit(poll_page, topics=["Law"], tags=[])
    own = submit(poll_page, topics=["Policy"])

    results = {result.question: result for result in get_results(poll_page, own)}

    assert results["Topics"].multiple
    assert results["Topics"].answer_count == 3
    assert as_dict(results.values())["Topics"] == [
        ("Law", 2, 67, False),
        ("Policy", 2, 67, True),
    ]
    # Submissions without a choice are not counted as answers
    assert results["Tags"].answer_count == 1
    assert not results["Colour"].multiple


@pytest.mark.django_db
def test_answers_which_are_no_choice_are_ignored(poll_page):
    submit(poll_page, colour="Red")
    # E.g. a renamed choice, or a question added later
    submit(poll_page, colour="Crimson")
    submit(poll_page)

    results = {result.question: result for result in get_results(poll_page)}

    assert results["Colour"].answer_count == 1
    assert as_dict(results.values())["Colour"][0] == ("Red", 1, 100, False)


@pytest.mark.django_db
def test_no_answers_yet(poll_page):
    results = {result.question: result for result in get_results(poll_page)}

    assert results["Colour"].answer_count == 0
    assert [choice.percent for choice in results["Colour"].choices] == [0, 0, 0]
