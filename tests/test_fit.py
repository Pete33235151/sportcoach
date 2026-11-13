from io import BytesIO
from zipfile import ZipFile
import pytest
from app.services.fit import extract_fit


def test_fit_rejects_malformed():
    with pytest.raises(ValueError):
        extract_fit(b"not a fit")


def test_fit_zip_extracts_in_memory():
    fit = b"\x0c\x10\x00\x00\x00\x00\x00\x00.FIT" + b"dummydata"
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as archive:
        archive.writestr("subdir/workout.fit", fit)
    assert extract_fit(buffer.getvalue()) == fit


def test_fit_zip_rejects_multi():
    fit = b"\x0c\x10\x00\x00\x00\x00\x00\x00.FIT" + b"dummy"
    buffer = BytesIO()
    with ZipFile(buffer,'w') as archive:
        archive.writestr("a.fit",fit)
        archive.writestr("b.fit",fit)
    with pytest.raises(ValueError):
        extract_fit(buffer.getvalue())
