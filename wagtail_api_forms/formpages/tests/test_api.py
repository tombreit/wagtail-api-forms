"""
Unit tests for FormSubmissionSerializer.

These tests avoid building a full Wagtail page tree by mocking the
related objects (form submission, page, Site). They exercise the
serializer methods directly so that they stay green across the
SerializerMethodField refactor (drop wrong `source=` kwarg) and the
typo rename (`_detele_key_from_dict` -> `_delete_key_from_dict`).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from wagtail_api_forms.formpages.api import FormSubmissionSerializer


@pytest.fixture
def submission():
    obj = MagicMock()
    obj.page.title = "Contact"
    obj.page.url = "/en/contact/"
    obj.page.slug = "contact"
    obj.form_data_api = json.dumps(
        [
            {
                "label": "Email",
                "name": "email",
                "type": "email",
                "value": "user@example.org",
                "internal_bookkeeping": "drop me",
            },
            {
                "label": "Message",
                "name": "message",
                "field_type": "multiline",
                "value": "hello",
            },
        ]
    )
    return obj


def test_get_form_page_title_returns_page_title(submission):
    serializer = FormSubmissionSerializer()
    assert serializer.get_form_page_title(submission) == "Contact"


def test_get_form_page_url_combines_site_root_and_page_url(submission):
    site = MagicMock()
    site.root_url = "https://forms.example.org"
    with patch(
        "wagtail_api_forms.formpages.api.Site.objects.first",
        return_value=site,
    ):
        serializer = FormSubmissionSerializer()
        assert (
            serializer.get_form_page_url(submission)
            == "https://forms.example.org/en/contact/"
        )


def test_get_form_data_api_filters_unwanted_keys_and_renames_type(submission):
    serializer = FormSubmissionSerializer()
    result = list(serializer.get_form_data_api(submission))

    assert result == [
        {
            "label": "Email",
            "name": "email",
            "field_type": "email",
            "value": "user@example.org",
        },
        {
            "label": "Message",
            "name": "message",
            "field_type": "multiline",
            "value": "hello",
        },
    ]


def test_filter_helper_drops_unknown_keys_and_renames_type():
    # Access via the public name first, falling back to the legacy typo
    # so this test stays green both before and after the rename.
    helper = getattr(
        FormSubmissionSerializer,
        "_delete_key_from_dict",
        getattr(FormSubmissionSerializer, "_detele_key_from_dict", None),
    )
    assert helper is not None, "no key-filter helper found on serializer"

    out = helper({"label": "x", "name": "y", "type": "t", "secret": "s"})
    assert out == {"label": "x", "name": "y", "field_type": "t"}


def test_filter_helper_passes_through_non_dicts():
    helper = getattr(
        FormSubmissionSerializer,
        "_delete_key_from_dict",
        getattr(FormSubmissionSerializer, "_detele_key_from_dict", None),
    )
    # Existing implementation tolerates non-dict items (TODO comment in api.py)
    assert helper("not a dict") == "not a dict"
