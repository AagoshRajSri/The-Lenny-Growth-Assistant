"""
test_sanitization.py
Verifies XSS payload removal matches Phase 7 requirements.
No database or network required.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.agent.sanitize import sanitize_artifact_content

MALICIOUS_HTML = (
    '<div id="test">Safe text'
    '<script>alert(\'xss\')</script>'
    '<img src="x" onerror="alert(1)" />'
    '<a href="javascript:alert(2)">click</a>'
    '</div>'
)


def test_script_tag_stripped():
    result = sanitize_artifact_content(MALICIOUS_HTML, "html")
    assert "<script>" not in result


def test_onerror_stripped():
    result = sanitize_artifact_content(MALICIOUS_HTML, "html")
    assert "onerror" not in result


def test_javascript_url_stripped():
    result = sanitize_artifact_content(MALICIOUS_HTML, "html")
    assert "javascript:" not in result


def test_safe_text_preserved():
    result = sanitize_artifact_content(MALICIOUS_HTML, "html")
    assert "Safe text" in result


def test_markdown_passthrough():
    raw = "# Hello\n\n```python\nprint('safe')\n```"
    result = sanitize_artifact_content(raw, "markdown")
    assert result == raw


def test_iframe_stripped():
    payload = '<iframe src="https://evil.com"></iframe>'
    result = sanitize_artifact_content(payload, "html")
    assert "<iframe" not in result


def test_empty_string():
    assert sanitize_artifact_content("", "html") == ""
