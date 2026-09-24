import json

from searcher.application import SearchResult


def format_text(result: SearchResult) -> str:
    output = [
        f"count: {result.count}",
        f"total: {result.total}",
        f"is_truncated: {str(result.is_truncated).lower()}",
    ]

    for res in result.resolutions:
        addresses = ", ".join(res.addresses) if res.addresses else "N/A"
        output.append(f"{res.domain}: {addresses}")

    return "\n".join(output)


def format_json(result: SearchResult) -> object:
    output = {
        "count": result.count,
        "total": result.total,
        "is_truncated": result.is_truncated,
        "resolutions": [
            {"domain": res.domain.value, "addresses": res.addresses}
            for res in result.resolutions
        ],
    }
    return json.dumps(output, indent=2)
