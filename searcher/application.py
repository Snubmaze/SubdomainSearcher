from collections.abc import Callable
from dataclasses import dataclass

from searcher.domain import DomainName, ResolutionResult


@dataclass
class DiscoveryResult:
    subdomains: list[DomainName]
    is_truncated: bool


@dataclass
class SearchResult:
    resolutions: list[ResolutionResult]
    requested_domain: DomainName
    is_truncated: bool


def search_subdomains(
    domain: DomainName,
    timeout: float,
    discover: Callable[[DomainName, float], DiscoveryResult],
    resolve: Callable[[DomainName], ResolutionResult],
) -> SearchResult:
    discovery = discover(domain, timeout)
    resolutions = [resolve(name) for name in discovery.subdomains]
    return SearchResult(resolutions, domain, discovery.is_truncated)
