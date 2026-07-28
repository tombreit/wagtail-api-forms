"""
Tests for validators.validate_filetype, in particular the MIME sniff window.

libmagic identifies an OOXML file (.docx/.xlsx/.pptx) by finding the `word/` /
`xl/` / `ppt/` entry among the ZIP's local file headers. How far into the file
that header sits depends on what precedes it, so a fixed-size sniff window can
fall short and leave libmagic reporting `application/zip` or
`application/octet-stream` — which then fails the allow-list check and rejects a
perfectly valid upload. That was a real bug: some .docx files uploaded fine and
others didn't, with nothing in the settings to explain the difference.

These tests pin the behaviour by building .docx files whose `word/document.xml`
header is placed at a known offset, so the fixture itself documents the window
rather than depending on whichever sample document happened to be at hand.
"""

import io
import zipfile

import pytest

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail_api_forms.formpages.validators import (
    MIME_SNIFF_BYTES,
    validate_filetype,
)


# ----- Fixture construction --------------------------------------------------

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument'
    '/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)
DOCUMENT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>"
)

WORD_HEADER = b"PK\x03\x04"


def _docx_bytes(pad=0):
    """A minimal but structurally real .docx.

    `pad` bytes of XML comment are appended to [Content_Types].xml, which pushes
    the word/document.xml local file header that much deeper into the archive.
    Stored uncompressed so the padding translates 1:1 into offset.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as archive:
        padding = "<!--{}-->".format("x" * pad) if pad else ""
        archive.writestr("[Content_Types].xml", CONTENT_TYPES + padding)
        archive.writestr("_rels/.rels", RELS)
        archive.writestr("word/document.xml", DOCUMENT)
    return buf.getvalue()


def _word_entry_offset(data):
    """Offset of the word/document.xml local file header — the thing libmagic
    has to reach to call this a Word document rather than a plain ZIP."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return archive.getinfo("word/document.xml").header_offset


def _upload(data, name="report.docx"):
    return SimpleUploadedFile(name, data, content_type="application/octet-stream")


# ----- The fixture must actually exercise the window -------------------------


def test_padded_fixture_lands_beyond_the_old_2kb_window():
    """Guards the regression test below: if this fixture ever drifts back inside
    2 KB, test_docx_with_late_word_entry_is_accepted would pass for the wrong
    reason and stop protecting anything."""
    offset = _word_entry_offset(_docx_bytes(pad=3000))

    assert 2048 < offset < MIME_SNIFF_BYTES


# ----- Regression: the sniff window ------------------------------------------


def test_docx_with_late_word_entry_is_accepted():
    """The actual bug: word/document.xml past 2 KB made libmagic give up on the
    subtype, and the upload was rejected as an unsupported file type. Fails on
    the old 2048-byte read."""
    upload = _upload(_docx_bytes(pad=3000))

    assert validate_filetype(upload, [".docx"]) is upload


def test_docx_with_early_word_entry_still_accepted():
    """The documents that always worked must keep working."""
    upload = _upload(_docx_bytes(pad=0))

    assert validate_filetype(upload, [".docx"]) is upload


# ----- The content sniff must still do its job -------------------------------


def test_non_docx_payload_named_docx_is_rejected():
    """Widening the window must not soften the check into trusting the
    extension: a renamed binary is still refused."""
    upload = _upload(b"\x7fELF\x02\x01\x01\x00" + bytes(range(256)) * 40)

    with pytest.raises(ValidationError, match="Unsupported file type"):
        validate_filetype(upload, [".docx"])


def test_docx_rejected_when_not_in_allowed_extensions():
    """A genuine .docx is still refused if the page doesn't allow that type."""
    upload = _upload(_docx_bytes(pad=3000))

    with pytest.raises(ValidationError):
        validate_filetype(upload, [".pdf", ".txt"])


# ----- The file must stay readable for everyone downstream -------------------


def test_file_pointer_is_reset_after_validation():
    """Attachment.save() and the ClamAV scan read the same handle afterwards, so
    validate_filetype must not leave it parked at the end of the sniff window."""
    upload = _upload(_docx_bytes(pad=3000))

    validate_filetype(upload, [".docx"])

    assert upload.tell() == 0
    assert upload.read().startswith(WORD_HEADER)
