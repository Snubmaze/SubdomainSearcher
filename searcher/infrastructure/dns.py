import socket

from searcher.domain import DomainName, ResolutionResult


def resolve_domain(domain: DomainName) -> ResolutionResult:
    try:
        records = socket.getaddrinfo(
            host=domain.value,
            port=None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as e:
        no_address_codes = {socket.EAI_NONAME}
        if hasattr(socket, "EAI_NODATA"):
            no_address_codes.add(socket.EAI_NODATA)
        if e.errno in no_address_codes:
            return ResolutionResult(domain, [])
        raise

    ipv4_addresses: set[str] = set()
    ipv6_addresses: set[str] = set()

    for family, _kind, _protocol, _canonical_name, socket_address in records:
        if family == socket.AF_INET:
            ipv4_addresses.add(socket_address[0])
        elif family == socket.AF_INET6:
            ipv6_addresses.add(socket_address[0])

    addresses = []

    addresses.extend(sorted(ipv4_addresses))
    addresses.extend(sorted(ipv6_addresses))

    return ResolutionResult(domain, addresses)
