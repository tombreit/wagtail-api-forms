from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.forms.models import FORM_FIELD_CHOICES


class FileArtChoices(models.TextChoices):
    IMAGE_FILE = 'IMG_FILE'
    DOCUMENT_FILE = 'DOC_FILE'


# A page break is not a question: it starts a new step of a multi-step form
PAGE_BREAK = "pagebreak"

# The custom field types next to Wagtail's FORM_FIELD_CHOICES
IMAGE = "image"
DOCUMENT = "document"
MULTIPLE_CHOICE_TYPEAHEAD = "multiplechoicetypeahead"

FIELD_TYPE_CHOICES = list(FORM_FIELD_CHOICES) + [
    (IMAGE, _("Image file")),
    (DOCUMENT, _("Document file")),
    (MULTIPLE_CHOICE_TYPEAHEAD, _("Multiple Choice (typeahead)")),
    # ('image64', 'Uploaded Image (base64)'),
    (PAGE_BREAK, _("Page break (starts a new step)")),
]

# Which field types an attribute of a form field applies to; the admin only
# shows an attribute for these types (see panels.FieldTypePanel).
# All field types but the page break ask a question:
INPUT_FIELD_TYPES = [
    field_type for field_type, label in FIELD_TYPE_CHOICES if field_type != PAGE_BREAK
]
CHOICE_FIELD_TYPES = [
    "checkboxes",
    "dropdown",
    "multiselect",
    "radio",
    MULTIPLE_CHOICE_TYPEAHEAD,
]
# Their answers are lists: several choices are possible
MULTIPLE_CHOICE_FIELD_TYPES = ["checkboxes", "multiselect", MULTIPLE_CHOICE_TYPEAHEAD]
FILE_FIELD_TYPES = [IMAGE, DOCUMENT]
# Browsers ignore placeholders of date inputs, selects, checkboxes and radios
PLACEHOLDER_FIELD_TYPES = [
    "singleline",
    "multiline",
    "email",
    "number",
    "url",
    MULTIPLE_CHOICE_TYPEAHEAD,
]

# Default values which leave a checkbox unchecked (compared lowercase, without
# surrounding spaces); any other default value checks it
UNCHECKED_DEFAULT_VALUES = {
    "",
    "false",
    "no",
    "n",
    "0",
    "off",
    "none",
    "nein",
    "falsch",
    "unchecked",
}
