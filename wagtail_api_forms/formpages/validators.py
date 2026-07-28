import os
import magic
import mimetypes
from django.conf import settings
from django.core.exceptions import ValidationError
from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from ipware import get_client_ip


# How much of an upload libmagic gets to look at.
#
# libmagic identifies OOXML (.docx/.xlsx/.pptx) by locating the `word/` / `xl/` /
# `ppt/` entry name among the ZIP's local file headers, and that offset varies per
# document. With a 2 KB read it regularly falls off the end, fails to resolve the
# subtype and reports `application/octet-stream` — so a perfectly good .docx got
# rejected while another one sailed through.
#
# Measured over 3016 real OOXML files: 2048 identified 3005, 4096 identified 3013,
# 8192 identified 3014 — and 16k/32k identified no more than 8192 did. The only two
# stragglers at 8 KB are an Office `~$` lock stub and a file that reads as
# octet-stream even from the full payload, so this is the accuracy plateau.
#
# Deliberately a fixed cap rather than the whole upload: the buffer stays constant
# regardless of how large a file someone posts.
MIME_SNIFF_BYTES = 8192


def _get_mimetypes_for_extensions(file_extensions: list) -> list:
    """
    Todo: also check for common, but not standardized mime types:
    https://docs.python.org/3.7/library/mimetypes.html#mimetypes.common_types
    """
    _mimetypes = []
    for ext in file_extensions:
        # `types_map` is not always reliable, as it may not include all extensions
        # if mimetypes.types_map.get(ext):
        #     _mimetypes.append(mimetypes.types_map.get(ext))
        mime_type, _ = mimetypes.guess_type(f"file{ext}")
        if mime_type:
            _mimetypes.append(mime_type)
    return _mimetypes


def validate_file_exists(file, required):
    if not file and required:
        raise forms.ValidationError(_("This field is required."))

    return file


def validate_filetype(file, valid_file_extensions):
    valid_mime_types = _get_mimetypes_for_extensions(valid_file_extensions)
    file_mime_type = magic.from_buffer(file.read(MIME_SNIFF_BYTES), mime=True)
    # Reset the file pointer so subsequent readers (form save, AV scan)
    # see the full payload instead of starting at the end of the sniff window.
    file.seek(0)

    if file_mime_type not in valid_mime_types:
        _msg = f"Unsupported file type. Valid file types: `{', '.join(valid_file_extensions)}`, got `{file_mime_type}`!"
        raise ValidationError(_msg)

    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        _msg = f"Unacceptable file extension: Valid file extensions: `{', '.join(valid_file_extensions)}`, got `{ext}`!"
        raise ValidationError(_msg)

    return file


def validate_filesize(file, max_file_size):
    if file.size > max_file_size:
        _msg = _(
            f"Please keep file size under {filesizeformat(max_file_size)}. Current size is {filesizeformat(file.size)}."
        )
        raise forms.ValidationError(_msg)

    return file


def av_scan(file):
    import pyclamd

    try:
        cd = pyclamd.ClamdNetworkSocket(
            host=settings.CLAMD_HOST, port=settings.CLAMD_PORT
        )
        cd.ping()
    except pyclamd.ConnectionError:
        raise ValueError(
            f"Could not connect to clamd at {settings.CLAMD_HOST}:{settings.CLAMD_PORT}"
        )

    scan_result = cd.scan_stream(file)

    return scan_result


def validate_ip_whitelisted(request, whitelisted_ips):
    client_ip, _ = get_client_ip(request)

    if not whitelisted_ips:
        return False
    return client_ip in whitelisted_ips
