import json
from urllib import parse, request

from searcher.application import DiscoveryResult
from searcher.domain import DomainName

_QUERY_URL = "https://api.subdomain.app/v1/query"


def fetch_subdomain_app_data(domain: DomainName, timeout: float) -> object:
    query_params = parse.urlencode({"domain": domain.value})
    url = f"{_QUERY_URL}?{query_params}"

    with request.urlopen(url, timeout=timeout) as response:
        response_bytes = response.read()

    response_text = response_bytes.decode("utf-8")
    return json.loads(response_text)


def extract_payload_subdomains(
    payload: object, requested: DomainName
) -> DiscoveryResult:
    if not isinstance(payload, dict):
        raise ValueError("Subdomain API response is not JSON")

    raw_domain = payload.get("domain")
    if not isinstance(raw_domain, str):
        raise ValueError("Domain field must be a domain name")
    try:
        response_domain = DomainName(raw_domain)
    except ValueError as error:
        raise ValueError("Domain field is invalid") from error
    if requested != response_domain and not requested.is_subdomain_of(response_domain):
        raise ValueError("Domain field is not a parent of the requested domain")

    raw_names = payload.get("subdomains")
    if not isinstance(raw_names, list):
        raise ValueError("Subdomains field is not a list")

    count = payload.get("count")
    total = payload.get("total")
    if type(count) is not int or type(total) is not int:
        raise ValueError("Count and total must be integers")
    if count != len(raw_names):
        raise ValueError("Count does not match subdomains length")
    if total < count:
        raise ValueError("Total cannot be less than count")

    found_names: set[str] = set()
    for raw_name in raw_names:
        if not isinstance(raw_name, str):
            raise ValueError(f"Domain value {raw_name} is not string")
        try:
            name = DomainName(raw_name)
        except ValueError:
            continue
        if name.is_subdomain_of(requested):
            found_names.add(name.value)

    return DiscoveryResult(
        subdomains=[DomainName(value) for value in sorted(found_names)],
        is_truncated=total > count,
    )


def discover_subdomains(domain: DomainName, timeout: float) -> DiscoveryResult:
    payload = fetch_subdomain_app_data(domain, timeout)
    return extract_payload_subdomains(payload=payload, requested=domain)
