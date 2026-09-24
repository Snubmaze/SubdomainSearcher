import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from searcher.application import DiscoveryResult
from searcher.domain import DomainName, ResolutionResult
from searcher.main import main


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.output_directory = Path(directory.name) / "output"
        output_patch = patch(
            "searcher.main._OUTPUT_DIRECTORY", self.output_directory
        )
        output_patch.start()
        self.addCleanup(output_patch.stop)

    def run_cli(self, arguments: list[str]) -> int:
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return main(arguments)

    @patch("searcher.main.resolve_domain")
    @patch("searcher.main.discover_subdomains")
    def test_default_text_keeps_metadata(self, discover, resolve) -> None:
        discover.return_value = DiscoveryResult(
            [DomainName("b.google.com"), DomainName("a.google.com")], 2, 7
        )
        resolve.side_effect = [
            ResolutionResult(DomainName("b.google.com"), ["192.0.2.2", "2001:db8::2"]),
            ResolutionResult(DomainName("a.google.com"), []),
        ]

        self.assertEqual(self.run_cli(["GOOGLE.COM."]), 0)

        self.assertEqual(
            self.stdout.getvalue(),
            "count: 2\ntotal: 7\nis_truncated: true\n"
            "b.google.com: 192.0.2.2, 2001:db8::2\na.google.com: N/A\n",
        )
        self.assertEqual(self.stderr.getvalue(), "")
        discover.assert_called_once_with(DomainName("google.com"), 10.0)
        self.assertEqual(resolve.call_count, 2)
        self.assertFalse(self.output_directory.exists())

    @patch("searcher.main.resolve_domain")
    @patch("searcher.main.discover_subdomains")
    def test_json_file_keeps_data(self, discover, resolve) -> None:
        discover.return_value = DiscoveryResult(
            [DomainName("b.google.com"), DomainName("a.google.com")], 2, 3
        )
        resolve.side_effect = [
            ResolutionResult(DomainName("b.google.com"), ["192.0.2.2"]),
            ResolutionResult(DomainName("a.google.com"), []),
        ]
        path = self.output_directory / "subdomains.json"
        self.assertEqual(self.run_cli(["google.com", "--format", "json", "--save"]), 0)
        saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(self.stdout.getvalue(), "")
        self.assertEqual(self.stderr.getvalue(), "")
        self.assertEqual(
            saved,
            {
                "count": 2,
                "total": 3,
                "is_truncated": True,
                "resolutions": [
                    {"domain": "b.google.com", "addresses": ["192.0.2.2"]},
                    {"domain": "a.google.com", "addresses": []},
                ],
            },
        )

    @patch("searcher.main.resolve_domain")
    @patch("searcher.main.discover_subdomains")
    def test_text_can_be_saved(self, discover, resolve) -> None:
        discover.return_value = DiscoveryResult([DomainName("a.google.com")], 1, 1)
        resolve.return_value = ResolutionResult(DomainName("a.google.com"), [])
        path = self.output_directory / "subdomains.txt"
        self.assertEqual(self.run_cli(["google.com", "--save"]), 0)
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "count: 1\ntotal: 1\nis_truncated: false\na.google.com: N/A\n",
        )
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertFalse((self.output_directory / "subdomains.json").exists())

    @patch("searcher.main.discover_subdomains")
    def test_invalid_domain_stops_before_network(self, discover) -> None:
        self.assertEqual(self.run_cli(["bad..google.com"]), 2)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertIn("Неверный домен", self.stderr.getvalue())
        discover.assert_not_called()


if __name__ == "main":
    unittest.main()
