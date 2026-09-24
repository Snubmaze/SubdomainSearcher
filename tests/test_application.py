import json
import socket
import unittest
from unittest.mock import Mock, patch

from searcher.application import search_subdomains
from searcher.domain import DomainName, ResolutionResult
from searcher.infrastructure.dns import resolve_domain
from searcher.infrastructure.subdomain_app import discover_subdomains


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def ipv4_record(address: str) -> tuple:
    return (socket.AF_INET, socket.SOCK_STREAM, 0, "", (address, 0))


class SearchSubdomainsTests(unittest.TestCase):
    @patch("searcher.infrastructure.dns.socket.getaddrinfo")
    @patch("searcher.infrastructure.subdomain_app.request.urlopen")
    def test_resolves_in_discovery_order_and_keeps_empty_addresses(
        self, urlopen_mock: Mock, getaddrinfo_mock: Mock
    ) -> None:
        urlopen_mock.return_value = FakeHttpResponse(
            {
                "domain": "google.com",
                "count": 3,
                "total": 3,
                "subdomains": [
                    "b.google.com",
                    "bad_symb.google.com",
                    "a.google.com",
                ],
            }
        )
        getaddrinfo_mock.side_effect = [
            [ipv4_record("203.0.113.10")],
            [],
        ]

        result = search_subdomains(
            DomainName("google.com"), 2.5, discover_subdomains, resolve_domain
        )

        self.assertEqual(
            result.resolutions,
            [
                ResolutionResult(DomainName("a.google.com"), ["203.0.113.10"]),
                ResolutionResult(DomainName("b.google.com"), []),
            ],
        )
        self.assertEqual((result.count, result.total), (3, 3))
        self.assertFalse(result.is_truncated)
        urlopen_mock.assert_called_once_with(
            "https://api.subdomain.app/v1/query?domain=google.com", timeout=2.5
        )
        self.assertEqual(getaddrinfo_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
