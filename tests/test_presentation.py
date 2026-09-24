"""Проверки форматов на готовых результатах без HTTP и DNS."""

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
            count=2,
            total=2,
        )

        self.assertEqual(
            format_text(result),
            "count: 2\n"
            "total: 2\n"
            "is_truncated: false\n"
            "z.google.com: 2001:db8::2, 203.0.113.20, 203.0.113.10\n"
            "a.google.com: N/A",
        )

    def test_empty_search_still_shows_metadata(self) -> None:
        self.assertEqual(
            format_text(SearchResult([], 0, 0)),
            "count: 0\ntotal: 0\nis_truncated: false",
        )


class FormatJsonTests(unittest.TestCase):
    def test_keeps_resolution_and_address_order_with_empty_array(self) -> None:
        result = SearchResult(
            [
                ResolutionResult(
                    DomainName("z.google.com"),
                    ["2001:db8::2", "203.0.113.20", "203.0.113.10"],
                ),
                ResolutionResult(DomainName("a.google.com"), []),
            ],
            count=2,
            total=2,
        )

        self.assertEqual(
            json.loads(format_json(result)),
            {
                "count": 2,
                "total": 2,
                "is_truncated": False,
                "resolutions": [
                    {
                        "domain": "z.google.com",
                        "addresses": [
                            "2001:db8::2",
                            "203.0.113.20",
                            "203.0.113.10",
                        ],
                    },
                    {"domain": "a.google.com", "addresses": []},
                ],
            },
        )

    def test_empty_search_has_empty_resolutions(self) -> None:
        self.assertEqual(
            json.loads(format_json(SearchResult([], 0, 0))),
            {"count": 0, "total": 0, "is_truncated": False, "resolutions": []},
        )


if __name__ == "__main__":
    unittest.main()
