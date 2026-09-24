import json
import unittest

from searcher.application import SearchResult
from searcher.domain import DomainName, ResolutionResult
from searcher.presentation import format_json, format_text


class FormatTextTests(unittest.TestCase):
    def test_keeps_resolution_and_address_order_and_shows_na(self) -> None:
        result = SearchResult(
            [
                ResolutionResult(
                    DomainName("z.google.com"),
                    ["2001:db8::2", "203.0.113.20", "203.0.113.10"],
                ),
                ResolutionResult(DomainName("a.google.com"), []),
            ],
            DomainName("google.com"),
            False,
        )

        self.assertEqual(
            format_text(result),
            "requested_domain: google.com\n"
            "discovered_subdomains: 2\n"
            "is_truncated: false\n\n"
            "z.google.com: 2001:db8::2, 203.0.113.20, 203.0.113.10\n"
            "a.google.com: N/A",
        )

    def test_empty_search_still_shows_metadata(self) -> None:
        self.assertEqual(
            format_text(SearchResult([], DomainName("my.google.com"), True)),
            "requested_domain: my.google.com\ndiscovered_subdomains: 0\n"
            "is_truncated: true\n"
            "Нет обнаруженных строгих поддоменов для my.google.com "
            "в ответе API.",
        )


class FormatJsonTests(unittest.TestCase):
    def test_empty_search_has_empty_resolutions(self) -> None:
        self.assertEqual(
            json.loads(format_json(SearchResult([], DomainName("google.com"), True))),
            {
                "requested_domain": "google.com",
                "discovered_subdomains": 0,
                "is_truncated": True,
                "resolutions": [],
            },
        )


if __name__ == "__main__":
    unittest.main()
