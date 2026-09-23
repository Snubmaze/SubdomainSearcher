"""Проверки Subdomain API без живой сети."""

import json
import unittest
from unittest.mock import Mock, patch

from searcher.domain import DomainName
from searcher.infrastructure.subdomain_app import (
    discover_subdomains,
    extract_payload_subdomains,
    fetch_subdomain_app_data,
)


class FakeHttpResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class FetchSubdomainAppDataTests(unittest.TestCase):
    @patch("searcher.infrastructure.subdomain_app.request.urlopen")
    def test_discovers_names_from_one_response(self, urlopen_mock: Mock) -> None:
        payload = {
            "domain": "google.com",
            "count": 3,
            "total": 3,
            "subdomains": ["B.GOOGLE.COM", "a.google.com", "b.google.com"],
        }
        urlopen_mock.return_value = FakeHttpResponse(json.dumps(payload).encode())

        result = discover_subdomains(DomainName("google.com"), timeout=3)

        self.assertEqual(
            result.subdomains,
            [DomainName("a.google.com"), DomainName("b.google.com")],
        )
        self.assertFalse(result.is_truncated)
        urlopen_mock.assert_called_once()

    @patch("searcher.infrastructure.subdomain_app.request.urlopen")
    def test_decodes_utf8_json(self, urlopen_mock: Mock) -> None:
        payload = {
            "domain": "google.com",
            "count": 1,
            "total": 1,
            "subdomains": ["тест.google.com"],
        }
        urlopen_mock.return_value = FakeHttpResponse(
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )

        self.assertEqual(
            fetch_subdomain_app_data(DomainName("google.com"), 3), payload
        )

    @patch("searcher.infrastructure.subdomain_app.request.urlopen")
    def test_propagates_invalid_json(self, urlopen_mock: Mock) -> None:
        urlopen_mock.return_value = FakeHttpResponse(b"not json")

        with self.assertRaises(json.JSONDecodeError):
            discover_subdomains(DomainName("google.com"), 3)

    def test_normalizes_and_sorts(self) -> None:
        payload = {
            "domain": "google.com",
            "count": 8,
            "total": 8,
            "subdomains": [
                "Z.google.COM",
                "a.google.com.",
                "z.google.com",
                "api.google.com",
                "google.com",
                "notgoogle.com",
                "bad_symbol.google.com",
            ],
        }

        result = extract_payload_subdomains(payload, DomainName("google.com"))

        self.assertEqual(
            result.subdomains,
            [
                DomainName("a.google.com"),
                DomainName("api.google.com"),
                DomainName("z.google.com"),
            ],
        )
        self.assertEqual((result.count, result.total), (8, 8))

    def test_empty_result(self) -> None:
        payload = {"domain": "google.com", "count": 0, "total": 0, "subdomains": []}

        result = extract_payload_subdomains(payload, DomainName("google.com"))

        self.assertEqual(result.subdomains, [])
        self.assertFalse(result.is_truncated)

    def test_returns_names_and_reports_truncation(self) -> None:
        payload = {
            "domain": "google.com",
            "count": 1,
            "total": 2,
            "subdomains": ["a.google.com"],
        }

        result = extract_payload_subdomains(payload, DomainName("google.com"))

        self.assertEqual(result.subdomains, [DomainName("a.google.com")])
        self.assertTrue(result.is_truncated)


if __name__ == "__main__":
    unittest.main()
