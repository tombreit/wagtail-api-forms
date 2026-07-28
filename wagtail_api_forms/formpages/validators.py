import logging
import os
import magic
import mimetypes
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError
from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from ipware import get_client_ip


logger = logging.getLogger(__name__)


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


# The freedesktop shared-mime-info database, as emitted by update-mime-database.
#
# We need to answer "may libmagic legitimately report X for a file with this
# extension?", and mimetypes.guess_type() cannot: it is one-to-one, mapping an
# extension to a single canonical type. libmagic answers a different question —
# what the *content* looks like — and for text formats that yields several
# answers, e.g. a .txt of comma-separated lines sniffs as text/csv, never
# text/plain. Those files used to be rejected.
#
# shared-mime-info already encodes exactly this relation as a type hierarchy
# ("text/csv sub-class-of text/plain"), so we defer to it rather than keeping a
# hand-written table. Both files are plain two-column text; no parser needed.
MIME_SUBCLASSES_PATH = "/usr/share/mime/subclasses"  # "<child> <parent>"
MIME_ALIASES_PATH = "/usr/share/mime/aliases"  # "<alias> <canonical>"


def _read_mime_pairs(path: str) -> dict:
    """Parse a two-column shared-mime-info file into {left: {right, ...}}."""
    pairs = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) == 2:
                    pairs.setdefault(parts[0], set()).add(parts[1])
    except OSError as exc:
        # Degrade to exact-type comparison rather than blocking every upload.
        logger.warning("Cannot read MIME database %s: %s", path, exc)
    return pairs


@lru_cache(maxsize=1)
def _mime_hierarchy() -> tuple:
    """(subclasses, aliases), read once per process."""
    subclasses = _read_mime_pairs(MIME_SUBCLASSES_PATH)
    aliases = {
        alias: sorted(targets)[0]
        for alias, targets in _read_mime_pairs(MIME_ALIASES_PATH).items()
    }
    return subclasses, aliases


def mime_database_available() -> bool:
    """Whether the type hierarchy loaded. Used in tests only for now."""
    subclasses, _aliases = _mime_hierarchy()
    return bool(subclasses)


def _mime_matches_extension(sniffed: str, canonical: str) -> bool:
    """Is `sniffed` an acceptable stand-in for `canonical`?

    True when the two are the same type, or when `sniffed` descends from
    `canonical` in the shared-mime-info hierarchy — text/csv IS-A text/plain, so
    a comma-separated .txt is fine. The relation is deliberately one-directional:
    application/zip does NOT descend from wordprocessingml.document, so a bare
    ZIP renamed .docx stays rejected, as does a JPEG named .pdf.
    """
    subclasses, aliases = _mime_hierarchy()
    sniffed = aliases.get(sniffed, sniffed)
    canonical = aliases.get(canonical, canonical)

    if sniffed == canonical:
        return True

    # Walk sub-class-of transitively; the graph is small (~500 edges) and may
    # contain cycles in principle, so track what we have already visited.
    seen = set()
    pending = [sniffed]
    while pending:
        for parent in subclasses.get(pending.pop(), ()):
            parent = aliases.get(parent, parent)
            if parent == canonical:
                return True
            if parent not in seen:
                seen.add(parent)
                pending.append(parent)

    return False


def _canonical_mime_types(file_extensions: list) -> dict:
    """{extension: canonical MIME type} for the configured extensions.

    An extension nothing recognises is logged rather than silently dropped —
    that used to leave a type in the form's help text that could never actually
    be uploaded, with the resulting error blaming the visitor's file.
    """
    canonical = {}
    unresolved = []

    for ext in file_extensions:
        guessed, _encoding = mimetypes.guess_type(f"file{ext}")
        if guessed:
            canonical[ext] = guessed
        else:
            unresolved.append(ext)

    if unresolved:
        logger.warning(
            "No known MIME type for configured file extension(s): %s. "
            "Uploads of those types cannot succeed.",
            ", ".join(unresolved),
        )

    return canonical


def validate_file_exists(file, required):
    if not file and required:
        raise forms.ValidationError(_("This field is required."))

    return file


def validate_filetype(file, valid_file_extensions):
    # A zero-byte upload sniffs as application/x-empty (or inode/x-empty, depending
    # on the libmagic version) and used to be reported as an unsupported *file
    # type*, which sends people off checking their file format for no reason.
    # Testing the size instead of the MIME string sidesteps that version split.
    if not file.size:
        raise ValidationError(
            "The uploaded file is empty (0 bytes). Please check the file and try again."
        )

    canonical_types = _canonical_mime_types(valid_file_extensions)
    if not canonical_types:
        # Nothing could ever pass — that's a configuration problem, not the
        # visitor's file. Say so instead of blaming whatever they uploaded.
        raise ValidationError(
            "This form is misconfigured: none of the configured file types "
            f"(`{', '.join(valid_file_extensions)}`) are recognised. "
            "Please contact the site administrator."
        )

    file_mime_type = magic.from_buffer(file.read(MIME_SNIFF_BYTES), mime=True)
    # Reset the file pointer so subsequent readers (form save, AV scan)
    # see the full payload instead of starting at the end of the sniff window.
    file.seek(0)

    if not any(
        _mime_matches_extension(file_mime_type, canonical)
        for canonical in canonical_types.values()
    ):
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
