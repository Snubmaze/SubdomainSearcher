import json
import unittest
from unittest.mock import Mock, patch

from searcher.domain import DomainName
from searcher.infrastructure.certspotter import (
    extract_payload_subdomains,
    fetch_certspotter_data,
)


class FakeHttpResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return

    def read(self) -> bytes:
        return self.body


class FetchCertSpotterDataTests(unittest.TestCase):
    @patch("searcher.infrastructure.certspotter.request.urlopen")
    def test_builds_expected_url(self, urlopen_mock: Mock) -> None:
        urlopen_mock.return_value = FakeHttpResponse(b"[]")

        fetch_certspotter_data(DomainName("test.com"), timeout=10.0)

        requested_url = urlopen_mock.call_args.args[0]
        self.assertEqual(
            requested_url,
            "https://api.certspotter.com/v1/issuances?"
            "domain=test.com&include_subdomains=true&expand=dns_names",
        )

    @patch("searcher.infrastructure.certspotter.request.urlopen")
    def test_decodes_utf8_and_parses_json(self, urlopen_mock: Mock) -> None:
        expected = [{"dns_names": ["тест.ru"]}]
        body = json.dumps(expected, ensure_ascii=False).encode("utf-8")
        urlopen_mock.return_value = FakeHttpResponse(body)

        result = fetch_certspotter_data(DomainName("test.com"), timeout=5.0)

        self.assertEqual(result, expected)

    def test_normalizes_and_sorts_names(self) -> None:
        payload = [
            {
                "dns_names": [
                    "API.Google.COM",
                    "*.wild.google.com",
                    "test.com",
                    "notgoogle.com",
                    "invalid_symb.google.com",
                ]
            },
            {
                "dns_names": [
                    "youtube.google.com",
                ]
            },
        ]

        result = extract_payload_subdomains(payload, DomainName("google.com"))

        self.assertEqual(
            result,
            [
                DomainName("api.google.com"),
                DomainName("wild.google.com"),
                DomainName("youtube.google.com"),
            ],
        )

        @patch("searcher.infrastructure.certspotter.request.urlopen")
        def test_propagates_invalid_json_error(self, urlopen_mock: Mock) -> None:
            urlopen_mock.return_value = FakeHttpResponse(b"not json")

            with self.assertRaises(json.JSONDecodeError):
                fetch_certspotter_data(DomainName("gogle.com"), timeout=5.0)


if __name__ == "__main__":
    unittest.main()
