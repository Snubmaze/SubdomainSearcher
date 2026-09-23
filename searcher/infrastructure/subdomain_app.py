import json
from dataclasses import dataclass
from urllib import parse, request

from searcher.domain import DomainName

_QUERY_URL = "https://api.subdomain.app/v1/query"


@dataclass
class DiscoveryResult:
    subdomains: list[DomainName]
    count: int
    total: int

    @property
    def is_truncated(self) -> bool:
        return self.total > self.count


def fetch_subdomain_app_data(domain: DomainName, timeout: float) -> object:
    query_params= parse.urlencode({"domain": domain.value})
    url = f"{_QUERY_URL}?{query_params}"

    with request.urlopen(url, timeout=timeout) as response:
        response_bytes = response.read()

    response_text = response_bytes.decode("utf-8")
    return json.loads(response_text)


def extract_payload_subdomains(payload: object, parent: DomainName) -> DiscoveryResult:
    if not isinstance(payload, dict):
        raise ValueError("Subdomain API response is not JSON")

    if payload.get("domain") != parent.value:
        raise ValueError("Domain flield in response is not similar to parent")

    raw_names = payload.get("subdomains")
    if not isinstance(raw_names, list):
        raise ValueError("Subdomains field is not list")

    count = payload.get("count")
    total = payload.get("total")

    found_names: set[str] = set()
    for raw_name in raw_names:
        if not isinstance(raw_name, str):
            raise ValueError(f"Domain value {raw_name} is not string")
        try:
            name = DomainName(raw_name)
        except ValueError:
            continue
        if name.is_subdomain_of(parent):
            found_names.add(name.value)

    return DiscoveryResult(
        subdomains=[DomainName(value) for value in sorted(found_names)], 
        count=count, 
        total=total,
    )


def discover_subdomains(domain: DomainName, timeout: float) -> DiscoveryResult:
    payload = fetch_subdomain_app_data(domain, timeout)
    return extract_payload_subdomains(payload=payload, parent=domain)