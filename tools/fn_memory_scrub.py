"""fn_memory_scrub.py - exact mirror of the FN-Memory 30515c0a pre-write secret scrubber.

Code copied verbatim from the pinned FN-Memory checkout (full-line comments omitted) at commit 30515c0a33e30224f92d979e1d36e244654afe3b:
  space_neurons/memory/mcp_server.py      lines 168-291  (_SECRET_PATTERNS ... looks_like_secret)
  space_neurons/custom_relation_format.py canonical()
FN-Memory refuses a memory_store whose `text` trips looks_like_secret(text), and a memory_relation_create / _update whose
canonical(raw_payload).decode() trips it, where raw_payload holds relation, direction, participants, observed_at and
evidence (custom_relations.py:176-180). Pacta checks every graph node text and every relation payload with this mirror
BEFORE any write. The same file ships byte-identical in pacta (tools/) and pacta-core (packages/analytics-sync/); the
tests compare it with the pinned FN-Memory source when that checkout is available.
"""
import collections
import json
import math
import re

FN_MEMORY_COMMIT = "30515c0a33e30224f92d979e1d36e244654afe3b"


_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),                       # OpenAI-style keys
    re.compile(r"AKIA[0-9A-Z]{12,}"),                            # AWS access key id
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),                   # GitHub tokens
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{8,}"),                  # Slack tokens
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{12,}"),               # bearer auth headers
    re.compile(r"-----BEGIN[A-Z0-9 ]*PRIVATE KEY-----"),         # PEM private key
    re.compile(r"-----BEGIN [A-Z0-9 ]+-----"),                   # PEM blocks generally
    re.compile(                                                  # KEY=/TOKEN=/SECRET= assignments
        r"(?i)\b(?:api[_-]?key|secret(?:[_-]?key)?|access[_-]?key|"
        r"auth[_-]?token|token|password|passwd|pwd)\b\s*[:=]\s*(\S{4,})"),
    re.compile(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\s*=\s*(\S{4,})"),
]

_POINTER_VALUE = re.compile(
    r"\A(?:"
    r"~?/\S*"                            # filesystem path
    r"|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"   # env reference
    r"|<[^>]{1,40}>"                     # placeholder
    r"|\*{3,}"                           # masked
    r"|\.{3,}"                           # elided
    r")[.,;)]?\Z")

_BASE64_RUN = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
_PURE_HEX = re.compile(r"\A[0-9a-fA-F]+\Z")

_IDENT_SEGMENT = re.compile(r"\A[A-Za-z][A-Za-z0-9_-]*\Z")
_B64_MIN_ENTROPY = 4.2


def _shannon_bits(run):
    """Shannon entropy of ``run`` in bits per character."""
    if not run:
        return 0.0
    total = len(run)
    return -sum(
        (count / total) * math.log2(count / total)
        for count in collections.Counter(run).values())


def _is_encoded_blob(run):
    """True when a long base64-charset run is plausibly ENCODED BYTES rather
    than prose that happens to contain slashes."""
    if "=" in run or "+" in run:
        return True                       # padding or '+': unambiguous base64
    segments = [s for s in run.split("/") if s]
    if len(segments) >= 2 and all(_IDENT_SEGMENT.match(s) for s in segments):
        return _shannon_bits(run) >= _B64_MIN_ENTROPY
    return True


def secret_span(text):
    """First credential-shaped span in ``text``, or None if it is clean.

    Returns ``(rule, excerpt)`` where ``excerpt`` is REDACTED — first and last
    four characters with the middle masked. Callers need enough to locate the
    trigger in their own text without the value being echoed into a log, an
    error payload or a transcript. Before this existed a rejected caller had
    to bisect its own paragraphs to find out what tripped the scrub.
    """
    if not isinstance(text, str):
        return None

    def excerpt(value):
        if len(value) <= 12:
            return value[:2] + "*" * max(len(value) - 2, 0)
        return "%s...%s (%d chars)" % (value[:4], value[-4:], len(value))

    for pat in _SECRET_PATTERNS:
        if pat.groups:
            for match in pat.finditer(text):
                if not _POINTER_VALUE.match(match.group(1)):
                    return ("credential_assignment", excerpt(match.group(0)))
            continue
        match = pat.search(text)
        if match:
            return ("credential_pattern", excerpt(match.group(0)))
    for m in _BASE64_RUN.finditer(text):
        run = m.group(0)
        if _PURE_HEX.match(run):
            continue
        if _is_encoded_blob(run):
            return ("encoded_blob", excerpt(run))
    return None


def looks_like_secret(text):
    """True if ``text`` matches any credential pattern (over-rejects safely,
    except bare hex digests -- see the base64/hex note above)."""
    return secret_span(text) is not None


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(',', ':')).encode('utf-8')


def relation_payload_text(relation, direction, participants, observed_at, evidence=None):
    """The exact string FN-Memory scans on a relation write (custom_relations.py:176-180)."""
    raw = {"relation": relation, "direction": direction, "participants": participants, "observed_at": observed_at}
    if evidence is not None:
        raw["evidence"] = evidence
    return canonical(raw).decode()
