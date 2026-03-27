"""Whitelist-Host-Extraktion und syntaktische Validierung (ohne fest verdrahtete Domains)."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_MAX_HOSTNAME_LEN = 253
_MAX_LABEL_LEN = 63

# RFC 1035-kompatible Labels (ASCII nach IDNA); Lowercase nach Normalisierung
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_whitelist_entry(raw_value: str) -> str:
    """Host aus Freitext/URL extrahieren, lowercasing; leer wenn nichts Brauchbares."""
    value = raw_value.strip().lower()
    if not value:
        return ""

    if "://" in value:
        parsed = urlsplit(value)
        value = parsed.hostname or ""
    else:
        value = value.split("/", 1)[0]
        if "@" in value:
            value = value.rsplit("@", 1)[-1]
        if value.count(":") == 1:
            host, port = value.rsplit(":", 1)
            if port.isdigit():
                value = host

    value = value.strip().rstrip(".")
    if value.startswith("*."):
        value = value[2:]

    return value


def validate_whitelist_host(host: str) -> str:
    """
    Prüft einen bereits normalisierten Host (IP oder DNS-Name).
    Gibt kanonische Form zurück (ASCII/Punycode für Domainnamen).
    """
    if not host or len(host) > _MAX_HOSTNAME_LEN:
        raise ValueError("Ungültiger Host- oder Adresseintrag")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return host

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("Ungültiger Host- oder Adresseintrag") from exc

    if ".." in ascii_host or ascii_host.startswith(".") or ascii_host.endswith("."):
        raise ValueError("Ungültiger Host- oder Adresseintrag")

    labels = ascii_host.split(".")
    if not labels or len(labels) > 127:
        raise ValueError("Ungültiger Host- oder Adresseintrag")

    for label in labels:
        if not label or len(label) > _MAX_LABEL_LEN:
            raise ValueError("Ungültiger Host- oder Adresseintrag")
        if not _LABEL_RE.match(label):
            raise ValueError("Ungültiger Host- oder Adresseintrag")

    return ascii_host.lower()


def parse_whitelist_url_entry(raw_value: str) -> str | None:
    """
    Eine Zeile normalisieren und validieren.
    None = leer / ignoriert; ValueError bei ungültigem Eintrag.
    """
    normalized = normalize_whitelist_entry(raw_value)
    if not normalized:
        return None
    try:
        return validate_whitelist_host(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Ungültiger Whitelist-Eintrag: {raw_value.strip()!s}"
        ) from exc
