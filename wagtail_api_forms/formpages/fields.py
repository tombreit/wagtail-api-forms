from django import forms
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

from .validators import (
    validate_file_exists,
    validate_filetype,
    validate_filesize,
)


class FormBuilderBaseFileField(forms.FileField):

    FORMBUILDER_MAX_UPLOAD_SIZE = 5000 * 1024
    FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES = [".pdf", ".txt"]
    FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES = [".jpg", ".jpeg", ".png"]

    def __init__(self, *args, help_text='', **kwargs):
        self.max_upload_size = kwargs.pop(
            'max_upload_size', self.FORMBUILDER_MAX_UPLOAD_SIZE
        )
        self.allowed_file_types = kwargs.pop(
            'allowed_file_types', self.FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES
        )
        self.file_art = kwargs.pop(
            'file_art', None
        )

        super().__init__(*args, **kwargs)

        _upload_size_hint = f"Max file size: {filesizeformat(self.max_upload_size)}."
        _filetype_hint = f"Valid file types: {', '.join(self.allowed_file_types)}"
        self.help_text = f"{help_text} {_upload_size_hint} {_filetype_hint}"

    def clean(self, *args, **kwargs):
        uploaded_file = super().clean(*args, **kwargs)

        if not validate_file_exists(uploaded_file, self.required):
            return None

        if all([
            validate_filesize(uploaded_file, self.max_upload_size),
            validate_filetype(uploaded_file, self.allowed_file_types),
        ]):
            return uploaded_file
        else:
            return None
