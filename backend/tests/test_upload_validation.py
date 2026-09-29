import os
import sys

import pytest
from fastapi import HTTPException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upload_validation import safe_filename, validate_upload, max_upload_size_bytes


def test_safe_filename_strips_directory_components():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("/absolute/path/report.pdf") == "report.pdf"
    assert safe_filename("normal.pdf") == "normal.pdf"


def test_safe_filename_rejects_empty_or_dot_names():
    for bad in ["", "   ", ".", ".."]:
        with pytest.raises(HTTPException) as exc:
            safe_filename(bad)
        assert exc.value.status_code == 400


def test_validate_upload_accepts_known_types():
    assert validate_upload("report.PDF", "application/pdf") == "report.PDF"
    assert validate_upload("scan.png", "image/png") == "scan.png"
    assert validate_upload("notes.txt", None) == "notes.txt"


def test_validate_upload_rejects_disallowed_extension():
    with pytest.raises(HTTPException) as exc:
        validate_upload("payload.exe", "application/octet-stream")
    assert exc.value.status_code == 400


def test_validate_upload_rejects_mismatched_content_type():
    with pytest.raises(HTTPException) as exc:
        validate_upload("report.pdf", "application/x-msdownload")
    assert exc.value.status_code == 400


def test_validate_upload_blocks_path_traversal_attempt():
    # A traversal attempt disguised with an allowed extension must still be
    # confined to a bare filename before it ever reaches the filesystem.
    assert validate_upload("../../../etc/cron.d/evil.txt", "text/plain") == "evil.txt"


def test_max_upload_size_bytes_reads_env(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "5")
    assert max_upload_size_bytes() == 5 * 1024 * 1024
    monkeypatch.delenv("MAX_UPLOAD_SIZE_MB", raising=False)
    assert max_upload_size_bytes() == 20 * 1024 * 1024
