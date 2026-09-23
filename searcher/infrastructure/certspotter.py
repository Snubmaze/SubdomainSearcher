import json
from urllib import parse, request

from searcher.domain import DomainName

_CERT_SPOTTER_URL = "https://api.certspotter.com/v1/issuances"


def fetch_certspotter_data(
    domain: DomainName,
    timeout: float,
) -> object:
    query = parse.urlencode(
        {
            "domain": domain.value,
            "include_subdomains": "true",
            "expand": "dns_names",
        }
    )
    url = f"{_CERT_SPOTTER_URL}?{query}"

    with request.urlopen(url, timeout=timeout) as response:
        response_bytes = response.read()

    response_text = response_bytes.decode("utf-8")
    return json.loads(response_text)


def extract_payload_subdomains(payload: object, parent: DomainName) -> list[DomainName]:
    if not isinstance(payload, list):
        raise ValueError("CT Search API response must be list")

    subdomains: set[str] = set()

    for record in payload:
        if not isinstance(record, dict):
            raise ValueError("CT Search API response records are not JSON-formatted")
        raw_names = record.get("dns_names")
        if not isinstance(raw_names, list):
            raise ValueError("DNS names values are not list")

        for raw_name in raw_names:
            if not isinstance(raw_name, str):
                raise ValueError("Every value of 'dns_names' must be string")

            raw_name = raw_name.removeprefix("*.")

            try:
                domain = DomainName(raw_name)
            except ValueError:
                continue

            if domain.is_subdomain_of(parent):
                subdomains.add(domain.value)

    return [DomainName(value) for value in sorted(subdomains)]
