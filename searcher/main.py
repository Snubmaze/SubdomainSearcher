import argparse
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError

from searcher.application import search_subdomains
from searcher.domain import DomainName, ResolutionResult
from searcher.infrastructure.dns import resolve_domain
from searcher.infrastructure.subdomain_app import discover_subdomains
from searcher.presentation import format_json, format_text

_HTTP_TIMEOUT = 10.0
_OUTPUT_DIRECTORY = Path("output")


class DnsLookupError(Exception):
    pass


def _resolve_for_cli(domain: DomainName) -> ResolutionResult:
    try:
        return resolve_domain(domain)
    except OSError as error:
        raise DnsLookupError(f"{domain}: {error}") from error


def _save_output(path: Path, content: str) -> None:
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    parser.add_argument(
        "--save",
        action="store_true",
    )
    args = parser.parse_args(argv)

    try:
        domain = DomainName(args.domain)
    except (ValueError, TypeError) as error:
        print(f"Неверный домен: {error}", file=sys.stderr)
        return 2

    try:
        result = search_subdomains(
            domain, _HTTP_TIMEOUT, discover_subdomains, _resolve_for_cli
        )
    except DnsLookupError as error:
        print(f"Ошибка DNS: {error}", file=sys.stderr)
        return 4
    except HTTPError as error:
        print(f"Ошибка HTTP: {error.code}", file=sys.stderr)
        return 3
    except (ValueError, UnicodeError) as error:
        print(f"Ошибка ответа Subdomain API: {error}", file=sys.stderr)
        return 3

    content = format_json(result) if args.format == "json" else format_text(result)
    if not args.save:
        print(content)
        return 0

    filename = "subdomains.json" if args.format == "json" else "subdomains.txt"
    output_path = _OUTPUT_DIRECTORY / filename
    try:
        _save_output(output_path, content)
    except OSError as error:
        print(f"Ошибка записи файла {output_path}: {error}", file=sys.stderr)
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
