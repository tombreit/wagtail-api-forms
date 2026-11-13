"""
Upload hints and errors in the language of the form page, and the default
values of checkboxes.
"""

import pytest

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import translation

from wagtail_api_forms.formpages.fields import FormBuilderBaseFileField
from wagtail_api_forms.formpages.forms import CustomFormBuilder
from wagtail_api_forms.formpages.models import UserFormField
from wagtail_api_forms.formpages.validators import validate_filesize, validate_filetype


MB = 1024 * 1024


def plain(text):
    """filesizeformat separates number and unit by a no-break space."""
    return text.replace("\xa0", " ")


def upload_field():
    return FormBuilderBaseFileField(
        allowed_file_types=[".pdf", ".txt"], max_upload_size=3 * MB, required=False
    )


# ----- Upload hints and errors -----------------------------------------------


def test_upload_hint_in_english():
    with translation.override("en"):
        help_text = upload_field().help_text

    assert plain(help_text) == " Max file size: 3.0 MB. Valid file types: .pdf, .txt"


def test_upload_hint_in_german():
    with translation.override("de"):
        help_text = upload_field().help_text

    assert plain(help_text) == " Maximale Dateigröße: 3,0 MB. Erlaubte Dateitypen: .pdf, .txt"


@pytest.mark.parametrize(
    "validate, message",
    [
        (
            lambda: validate_filetype(SimpleUploadedFile("cv.txt", b""), [".txt"]),
            "Die hochgeladene Datei ist leer (0 Bytes).",
        ),
        (
            lambda: validate_filetype(
                SimpleUploadedFile("cv.pdf", b"MZ\x90\x00binary"), [".pdf"]
            ),
            "Nicht unterstützter Dateityp. Erlaubte Dateitypen: `.pdf`",
        ),
        (
            lambda: validate_filetype(SimpleUploadedFile("notes.csv", b"a,b\n"), [".txt"]),
            "Nicht erlaubte Dateiendung. Erlaubte Dateiendungen: `.txt`, erhalten: `.csv`.",
        ),
        (
            lambda: validate_filesize(SimpleUploadedFile("cv.txt", b"0123456789"), 5),
            "Bitte laden Sie eine Datei kleiner als 5 Bytes hoch. Die Datei hat 10 Bytes.",
        ),
    ],
    ids=["empty", "type", "extension", "size"],
)
def test_upload_errors_in_german(validate, message):
    with translation.override("de"), pytest.raises(ValidationError) as excinfo:
        validate()

    assert plain(excinfo.value.messages[0]).startswith(message)


# ----- Checkbox default values -----------------------------------------------


@pytest.mark.parametrize(
    "default_value, checked",
    [
        ("", False),
        ("False", False),
        ("false", False),
        ("no", False),
        (" Nein ", False),
        ("0", False),
        ("off", False),
        ("yes", True),
        ("Ja", True),
        ("on", True),
        ("true", True),
        ("1", True),
    ],
)
def test_checkbox_default_value(default_value, checked):
    field = UserFormField(label="Consent", field_type="checkbox", default_value=default_value)

    form = CustomFormBuilder([field]).get_form_class()()

    assert form.fields["consent"].initial is checked
    assert (" checked" in str(form["consent"])) is checked
