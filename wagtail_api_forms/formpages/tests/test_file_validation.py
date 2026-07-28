"""
Tests for validators.validate_filetype.

Two distinct ways a valid upload used to be rejected, both reported to the
visitor as "Unsupported file type":

1. The sniff window. libmagic identifies an OOXML file (.docx/.xlsx/.pptx) by
   finding the `word/` / `xl/` / `ppt/` entry among the ZIP's local file headers.
   How far in that header sits depends on what precedes it, so a fixed-size
   window can fall short and leave libmagic reporting `application/zip` or
   `application/octet-stream`. Some .docx files uploaded fine and others didn't,
   with nothing in the settings to explain the difference.

2. One MIME type per extension. libmagic classifies *text* by content, so a .txt
   of comma-separated lines comes back as text/csv — while the allow-list was
   built from mimetypes.guess_type(), which only ever offers text/plain.

These tests build their own fixtures at known offsets and with known content, so
they document the boundaries rather than depending on whichever sample document
happened to be at hand.
"""

import io
import mimetypes
import zipfile

import pytest

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail_api_forms.formpages import validators
from wagtail_api_forms.formpages.validators import (
    MIME_SNIFF_BYTES,
    _canonical_mime_types,
    _mime_matches_extension,
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

# An extension no MIME database knows, used to exercise the unresolvable paths.
UNKNOWN_EXT = ".madeupextension"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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


# ----- Text files get classified by content, not just by extension -----------


def test_comma_separated_txt_is_accepted_via_the_type_hierarchy():
    """The regression: libmagic calls a comma-separated .txt `text/csv`, while
    guess_type() only ever offers `text/plain`, so ordinary CSV-ish notes bounced.

    Asserts the *mechanism*, not just the outcome: acceptance must come from
    shared-mime-info's `text/csv sub-class-of text/plain` edge. If that edge ever
    stops being found, this fails here rather than silently passing because some
    hand-written list happened to contain text/csv."""
    assert _mime_matches_extension("text/csv", "text/plain")
    assert not _mime_matches_extension("text/plain", "text/csv")  # one-directional

    upload = _upload(b"name,age,city\nana,31,berlin\nbo,27,lisbon\n", name="notes.txt")

    assert validate_filetype(upload, [".txt"]) is upload


@pytest.mark.parametrize(
    "label,content",
    [
        ("prose", b"Just some notes for the archive.\n"),
        ("semicolons", b"name;age;city\nana;31;berlin\n"),
        ("tabs", b"name\tage\n1\t2\n"),
        ("crlf", b"line one\r\nline two\r\n"),
        ("utf8 umlauts", "Grüße aus München\n".encode()),
        ("utf16", "Hallo\n".encode("utf-16")),
    ],
)
def test_ordinary_txt_shapes_are_accepted(label, content):
    """Encodings and separators that already worked must keep working."""
    upload = _upload(content, name="notes.txt")

    assert validate_filetype(upload, [".txt"]) is upload


@pytest.mark.parametrize(
    "label,content",
    [
        ("json", b'{"key": "value", "n": [1, 2, 3]}\n'),
        ("html", b"<!DOCTYPE html>\n<html><body><p>hi</p></body></html>\n"),
        ("email", b"From: a@example.org\nTo: b@example.org\nSubject: hi\n\nbody\n"),
    ],
)
def test_structured_text_in_a_txt_is_accepted(label, content):
    """Deliberate behaviour change, recorded rather than silent.

    These used to be rejected under a hand-written allow-list holding only
    text/plain, text/csv and application/csv. shared-mime-info classes html, xml
    and friends under text/plain, and the point of deferring to that database is
    deferring to its notion of what counts as text — so they are accepted now.

    Safe here: private_storage sets the download Content-Type from the *filename
    extension* (private_storage/models.py:41-46), so a .txt is always served as
    text/plain, and SECURE_CONTENT_TYPE_NOSNIFF is on. HTML inside a .txt is not
    an XSS vector."""
    upload = _upload(content, name="notes.txt")

    assert validate_filetype(upload, [".txt"]) is upload


# ----- Empty uploads name their own problem ----------------------------------


@pytest.mark.parametrize("name", ["notes.txt", "report.docx", "scan.pdf"])
def test_empty_upload_is_rejected_as_empty_not_as_wrong_type(name):
    """A zero-byte file sniffs as application/x-empty. Reporting that as an
    unsupported file *type* sent people off checking their file format when the
    real problem was that nothing got uploaded."""
    upload = _upload(b"", name=name)

    with pytest.raises(ValidationError) as excinfo:
        validate_filetype(upload, [".txt", ".docx", ".pdf"])

    assert "empty" in str(excinfo.value)
    assert "Unsupported file type" not in str(excinfo.value)


# ----- Genuine mismatches must still be caught -------------------------------


def test_jpeg_payload_named_pdf_is_rejected():
    """Real case from the corpus sweep: JPEGs saved with a .pdf extension."""
    jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    upload = _upload(jpeg + b"\x00" * 512, name="report.pdf")

    with pytest.raises(ValidationError, match="Unsupported file type"):
        validate_filetype(upload, [".pdf"])


@pytest.mark.parametrize(
    "sniffed,canonical",
    [
        ("image/jpeg", "application/pdf"),
        ("image/jpeg", "image/png"),
        ("application/zip", DOCX_MIME),
        ("application/octet-stream", DOCX_MIME),
        ("text/plain", "application/pdf"),
    ],
)
def test_hierarchy_does_not_loosen_binary_formats(sniffed, canonical):
    """The whole risk of deferring to a type hierarchy is that it might make the
    binary formats permissive. Measured over 117747 files it does not — their
    acceptance rates were byte-identical before and after. These pin the cases
    that matter: a bare ZIP is not a Word document, a JPEG is not a PDF."""
    assert not _mime_matches_extension(sniffed, canonical)


# ----- Resolving the allow-list ----------------------------------------------


def test_settings_defaults_all_resolve_to_a_canonical_type():
    """Every extension shipped as a default must resolve via guess_type().

    This is the test that fails loudly in an image built without `media-types`:
    Python's built-in table has no .docx entry, so /etc/mime.types must be
    present. That's the point — better a red test than silently rejecting every
    Word document in production."""
    defaults = set(settings.FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES) | set(
        settings.FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES
    )

    assert set(_canonical_mime_types(sorted(defaults))) == defaults


def test_any_extension_the_os_knows_is_usable():
    """Nothing is hard-coded: an admin adding a type we never anticipated works
    as long as the MIME database knows it."""
    assert _canonical_mime_types([".odt"]) == {
        ".odt": "application/vnd.oasis.opendocument.text"
    }


def test_unresolvable_extension_yields_nothing():
    """UNKNOWN_EXT is asserted to be genuinely unknown first — '.xyz' looked like
    a safe stand-in but /etc/mime.types maps it to chemical/x-xyz, which quietly
    turned this into a test of something else entirely."""
    assert mimetypes.guess_type(f"file{UNKNOWN_EXT}")[0] is None

    assert _canonical_mime_types([UNKNOWN_EXT]) == {}


# ----- A missing database must degrade, not explode --------------------------


def test_missing_mime_database_degrades_to_exact_match(monkeypatch):
    """If an image is ever built without shared-mime-info, uploads must keep
    working on exact type matches rather than failing wholesale. The system
    check in formpages/checks.py is what surfaces the missing package."""
    monkeypatch.setattr(validators, "MIME_SUBCLASSES_PATH", "/nonexistent/subclasses")
    monkeypatch.setattr(validators, "MIME_ALIASES_PATH", "/nonexistent/aliases")
    validators._mime_hierarchy.cache_clear()

    try:
        assert not validators.mime_database_available()
        # Exact match still works ...
        assert validators._mime_matches_extension("text/plain", "text/plain")
        # ... but the subclass relation is gone, so this is now rejected.
        assert not validators._mime_matches_extension("text/csv", "text/plain")

        upload = _upload(b"Just some notes.\n", name="notes.txt")
        assert validate_filetype(upload, [".txt"]) is upload
    finally:
        validators._mime_hierarchy.cache_clear()


def test_hierarchy_is_available_in_this_environment():
    """Guards the tests above from passing vacuously on a box that simply has no
    shared-mime-info installed."""
    assert validators.mime_database_available()


def test_partially_unresolvable_config_still_accepts_the_known_type():
    """One bad entry must not punish someone uploading a perfectly good PDF."""
    upload = _upload(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"0" * 512, name="scan.pdf")

    assert validate_filetype(upload, [".pdf", UNKNOWN_EXT]) is upload


def test_entirely_unresolvable_config_reports_misconfiguration():
    """When nothing could ever pass, blame the configuration, not the file."""
    upload = _upload(b"hello\n", name=f"notes{UNKNOWN_EXT}")

    with pytest.raises(ValidationError, match="misconfigured"):
        validate_filetype(upload, [UNKNOWN_EXT])
