from collections.abc import Callable
from dataclasses import dataclass

from searcher.domain import DomainName, ResolutionResult


@dataclass
class DiscoveryResult:
    subdomains: list[DomainName]
    count: int
    total: int

    @property
    def is_truncated(self) -> bool:
        return self.total > self.count


@dataclass
class SearchResult:
    resolutions: list[ResolutionResult]
    count: int
    total: int

    @property
    def is_truncated(self) -> bool:
        return self.total > self.count


def search_subdomains(
    domain: DomainName,
    timeout: float,
    discover: Callable[[DomainName, float], DiscoveryResult],
    resolve: Callable[[DomainName], ResolutionResult],
) -> SearchResult:
    discovery = discover(domain, timeout)
    resolutions = [resolve(name) for name in discovery.subdomains]
    return SearchResult(resolutions, discovery.count, discovery.total)
