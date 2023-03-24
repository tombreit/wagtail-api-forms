import os
import magic
import mimetypes
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from ipware import get_client_ip


def _get_mimetypes_for_extensions(file_extensions: list) -> list:
    """
    Todo: also check for common, but not standardized mime types:
    https://docs.python.org/3.7/library/mimetypes.html#mimetypes.common_types
    """
    _mimetypes = []
    for ext in file_extensions:
        if mimetypes.types_map.get(ext):
            _mimetypes.append(mimetypes.types_map.get(ext))
    return _mimetypes


def validate_file_exists(file, required):
    if not file and required:
        raise forms.ValidationError(_('This field is required.'))
    
    return file


def validate_filetype(file, valid_file_extensions):
    valid_mime_types = _get_mimetypes_for_extensions(valid_file_extensions)
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)

    if file_mime_type not in valid_mime_types:
        _msg = f'Unsupported file type. Valid file types: `{", ".join(valid_file_extensions)}`, got `{file_mime_type}`!'
        raise ValidationError(_msg)

    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        _msg = f'Unacceptable file extension: Valid file extensions: `{", ".join(valid_file_extensions)}`, got `{ext}`!'
        raise ValidationError(_msg)

    return file


def validate_filesize(file, max_file_size):
    if file.size > max_file_size:
        _msg = _(f'Please keep file size under {filesizeformat(max_file_size)}. Current size is {filesizeformat(file.size)}.')
        raise forms.ValidationError(_msg)

    return file


def av_scan(file):
    import pyclamd

    try:
        cd = pyclamd.ClamdNetworkSocket()
        cd.ping()
    except pyclamd.ConnectionError:
        raise ValueError("Could not connect to clamd server by network socket!")

    scan_result = cd.scan_stream(file)

    return scan_result


def validate_ip_whitelisted(request, whitelisted_ips):
    client_ip, _ = get_client_ip(request)

    if not whitelisted_ips:
        return False
    elif client_ip in whitelisted_ips:
        return True
