import socket
import unittest
from unittest.mock import Mock, patch

from searcher.domain import DomainName, ResolutionResult
from searcher.infrastructure.dns import resolve_domain


def address_record(family: int, address: str) -> tuple:
    socket_address = (address, 0) if family == socket.AF_INET else (address, 0, 0, 0)
    return (family, socket.SOCK_STREAM, 0, "", socket_address)


class ResolveDomainTests(unittest.TestCase):
    @patch("searcher.infrastructure.dns.socket.getaddrinfo")
    def test_returns_all_ips(self, getaddrinfo_mock: Mock) -> None:
        getaddrinfo_mock.return_value = [
            address_record(socket.AF_INET6, "2001:db8::2"),
            address_record(socket.AF_INET, "203.0.113.20"),
            address_record(socket.AF_INET6, "2001:db8::1"),
            address_record(socket.AF_INET, "203.0.113.10"),
            address_record(socket.AF_INET, "203.0.113.20"),
        ]
        domain = DomainName("API.google.COM.")

        result = resolve_domain(domain)

        self.assertEqual(
            result,
            ResolutionResult(
                domain,
                ["203.0.113.10", "203.0.113.20", "2001:db8::1", "2001:db8::2"],
            ),
        )
        getaddrinfo_mock.assert_called_once_with(
            host="api.google.com",
            port=None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )

    @patch("searcher.infrastructure.dns.socket.getaddrinfo", return_value=[])
    def test_returns_empty_addresses_for_no_records(
        self, _getaddrinfo_mock: Mock
    ) -> None:
        self.assertEqual(resolve_domain(DomainName("a.google.com")).addresses, [])

    @patch("searcher.infrastructure.dns.socket.getaddrinfo")
    def test_returns_empty_addresses_for_unknown_name(
        self, getaddrinfo_mock: Mock
    ) -> None:
        getaddrinfo_mock.side_effect = socket.gaierror(socket.EAI_NONAME, "no name")

        self.assertEqual(resolve_domain(DomainName("a.google.com")).addresses, [])


if __name__ == "__main__":
    unittest.main()
