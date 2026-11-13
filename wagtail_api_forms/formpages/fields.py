from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _

from .validators import (
    validate_file_exists,
    validate_filetype,
    validate_filesize,
)


class FormBuilderBaseFileField(forms.FileField):
    def __init__(self, *args, help_text="", **kwargs):
        self.max_upload_size = kwargs.pop(
            "max_upload_size", settings.FORMBUILDER_MAX_UPLOAD_SIZE
        )
        self.allowed_file_types = kwargs.pop("allowed_file_types", [])
        self.file_art = kwargs.pop("file_art", None)

        super().__init__(*args, **kwargs)

        # In the language of the form page: form fields are built per request
        _upload_size_hint = _("Max file size: %(size)s.") % {
            "size": filesizeformat(self.max_upload_size)
        }
        _filetype_hint = _("Valid file types: %(types)s") % {
            "types": ", ".join(self.allowed_file_types)
        }
        self.help_text = f"{help_text} {_upload_size_hint} {_filetype_hint}"

    def clean(self, *args, **kwargs):
        uploaded_file = super().clean(*args, **kwargs)

        if not validate_file_exists(uploaded_file, self.required):
            return None

        if all(
            [
                validate_filesize(uploaded_file, self.max_upload_size),
                validate_filetype(uploaded_file, self.allowed_file_types),
            ]
        ):
            return uploaded_file
        else:
            return None
