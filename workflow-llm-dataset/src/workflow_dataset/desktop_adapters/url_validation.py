"""
M23C-F3: Validate URL format for browser_open adapter. Local-first; simulate only.
Allows http, https, file://, and localhost. No remote browsing; no automation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class UrlValidationResult:
    valid: bool
    reason: str
    category: str  # "http" | "https" | "file" | "localhost" | "invalid"


ALLOWED_SCHEMES = frozenset({"http", "https", "file"})
# localhost-style with optional port
LOCALHOST_PATTERN = re.compile(r"^(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/.*)?$", re.IGNORECASE)


def validate_local_or_allowed_url(url: str) -> UrlValidationResult:
    """
    Validate URL for open_url preview. Allows http, https, file://, and localhost.
    Returns valid, reason, and category. No network access; format only.
    """
    if not url or not isinstance(url, str):
        return UrlValidationResult(valid=False, reason="empty_or_invalid", category="invalid")
    s = url.strip()
    if not s:
        return UrlValidationResult(valid=False, reason="empty_url", category="invalid")
    # Disallow dangerous schemes
    lower = s.lower()
    if lower.startswith("javascript:") or lower.startswith("data:") or lower.startswith("vbscript:"):
        return UrlValidationResult(valid=False, reason="scheme_not_allowed", category="invalid")
    if lower.startswith("file://"):
        parse = urlparse(s)
        if parse.scheme == "file":
            return UrlValidationResult(valid=True, reason="ok", category="file")
        return UrlValidationResult(valid=False, reason="invalid_file_url", category="invalid")
    if LOCALHOST_PATTERN.match(s) or s.startswith("http://localhost") or s.startswith("https://localhost"):
        return UrlValidationResult(valid=True, reason="ok", category="localhost")
    parse = urlparse(s if "://" in s else "http://" + s)
    scheme = (parse.scheme or "http").lower()
    if scheme not in ALLOWED_SCHEMES:
        return UrlValidationResult(valid=False, reason="scheme_not_allowed", category="invalid")
    if scheme == "file":
        return UrlValidationResult(valid=True, reason="ok", category="file")
    netloc = (parse.netloc or "").lower()
    if netloc in ("localhost", "127.0.0.1") or netloc.startswith("localhost:") or netloc.startswith("127.0.0.1:"):
        return UrlValidationResult(valid=True, reason="ok", category="localhost")
    return UrlValidationResult(valid=True, reason="ok", category=scheme)
