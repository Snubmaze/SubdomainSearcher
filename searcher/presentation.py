import json

from searcher.application import SearchResult


def format_text(result: SearchResult) -> str:
    output = [
        f"requested_domain: {result.requested_domain}",
        f"discovered_subdomains: {len(result.resolutions)}",
        f"is_truncated: {str(result.is_truncated).lower()}",
    ]

    if result.resolutions:
        output.append("")

    for res in result.resolutions:
        addresses = ", ".join(res.addresses) if res.addresses else "N/A"
        output.append(f"{res.domain}: {addresses}")

    if not result.resolutions:
        output.append(
            "Нет обнаруженных строгих поддоменов для "
            f"{result.requested_domain} в ответе API."
        )

    return "\n".join(output)


def format_json(result: SearchResult) -> str:
    output = {
        "requested_domain": result.requested_domain.value,
        "discovered_subdomains": len(result.resolutions),
        "is_truncated": result.is_truncated,
        "resolutions": [
            {"domain": res.domain.value, "addresses": res.addresses}
            for res in result.resolutions
        ],
    }
    return json.dumps(output, indent=2)
