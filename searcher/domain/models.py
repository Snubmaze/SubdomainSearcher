import re
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address

IPAdress = IPv4Address | IPv6Address

MAX_DOMAIN_LENGTH = 253
LABEL_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


@dataclass
class DomainName:
    value: str

    def __post_init__(self) -> None:
        self.value = _normalize_domain_name(self.value)

    def is_subdomain_of(self, parent: DomainName) -> bool:
        return self.value.endswith(f".{parent.value}")

    def __str__(self) -> str:
        return self.value


def _normalize_domain_name(value: str) -> str:
    if not value:
        raise ValueError("Empty domain name")

    if not isinstance(value, str):
        raise ValueError("Domain name must be string")

    value = value.strip()

    name_without_root_dot = value.removesuffix(".")
    if not name_without_root_dot:
        raise ValueError("Domain name must contain at least 1 label")

    ascii_labels: list[str] = []

    for label in name_without_root_dot.split("."):
        if not label:
            raise ValueError("Domain name contain empty label")
        try:
            ascii_label = label.encode("idna").decode("ascii").lower()
        except UnicodeError as e:
            raise ValueError("Domain name contains invalid label") from e

        if LABEL_PATTERN.fullmatch(ascii_label) is None:
            raise ValueError(f"Invalid domain label: {label!r}")

        ascii_labels.append(ascii_label)

    normalized_domain = ".".join(ascii_labels)

    if len(normalized_domain) > MAX_DOMAIN_LENGTH:
        raise ValueError("Domain name must not be longer than 253 symbols")

    return normalized_domain
