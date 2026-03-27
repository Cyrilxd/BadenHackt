"""Tests für Whitelist-URL-/Host-Validierung."""

import pytest
from app.schemas import WhitelistCreate, WhitelistUpdate
from app.validators import (
    normalize_whitelist_entry,
    parse_whitelist_url_entry,
    validate_whitelist_host,
)
from pydantic import ValidationError


@pytest.mark.parametrize(
    "raw,expected_host",
    [
        ("https://WWW.Example.COM/path", "www.example.com"),
        ("example.com:443", "example.com"),
        ("user@Example.COM", "example.com"),
        ("192.168.1.1:8080", "192.168.1.1"),
        ("http://[::1]/x", "::1"),
    ],
)
def test_normalize_extracts_host(raw: str, expected_host: str) -> None:
    assert normalize_whitelist_entry(raw) == expected_host


def test_validate_accepts_ipv4() -> None:
    assert validate_whitelist_host("8.8.8.8") == "8.8.8.8"


def test_validate_accepts_ipv6() -> None:
    assert validate_whitelist_host("::1") == "::1"


def test_validate_accepts_hostname() -> None:
    assert validate_whitelist_host("google.com") == "google.com"


def test_validate_rejects_single_label_hostname() -> None:
    with pytest.raises(ValueError, match="Ungültig"):
        validate_whitelist_host("asdf")


def test_validate_idna_punycode() -> None:
    assert parse_whitelist_url_entry("münchen.de") == "xn--mnchen-3ya.de"


def test_parse_whitelist_url_entry_none_for_empty() -> None:
    assert parse_whitelist_url_entry("   ") is None
    assert parse_whitelist_url_entry("") is None


@pytest.mark.parametrize(
    "invalid",
    [
        "kein-host-mit-leerzeichen .com",
        "foo..bar.com",
        "https://bad..host/",
        "-bad.com",
        "bad-.com",
        "a" * 254,
        "asdf",
        "https://asdf/path",
        "not!valid.com",
    ],
)
def test_parse_rejects_invalid(invalid: str) -> None:
    with pytest.raises(ValueError, match="Ungültig"):
        parse_whitelist_url_entry(invalid)


def test_whitelist_create_requires_one_valid_url() -> None:
    with pytest.raises(ValidationError):
        WhitelistCreate(name="t", urls=["   ", "http://"], room_id=1)


def test_whitelist_create_accepts_valid_urls() -> None:
    m = WhitelistCreate(
        name="t",
        urls=["https://a.example/x", "b.example"],
        room_id=1,
    )
    assert m.urls == ["a.example", "b.example"]


def test_whitelist_update_same_validation() -> None:
    m = WhitelistUpdate(
        name="t",
        urls=["1.1.1.1"],
        room_id=1,
    )
    assert m.urls == ["1.1.1.1"]
