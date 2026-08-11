"""Deterministic routing spec. Used as the routing-test oracle; live routing is
still the orchestrator's own LLM decision."""

from __future__ import annotations

_SIGNALS: dict[str, tuple[str, ...]] = {
    "access": (
        "vpn", "login", "log in", "password", "credential", "account",
        "locked", "shared drive", "drive", "access", "permission", "sso",
    ),
    "hardware": (
        "laptop", "device", "machine", "screen", "keyboard", "battery",
        "asset", "hardware", "won't turn on", "wont turn on", "broken", "rma",
    ),
    "licensing": (
        "license", "licence", "software", "seat", "subscription", "approval",
        "approve", "install ", "jetbrains", "tableau", "figma",
    ),
}

DOMAINS = tuple(_SIGNALS.keys())


def classify(request: str) -> list[str]:
    """Domains a request touches, in stable priority order."""
    text = f" {request.lower()} "
    return [d for d in DOMAINS if any(sig in text for sig in _SIGNALS[d])]


def is_multi_domain(request: str) -> bool:
    return len(classify(request)) > 1


def routing_hint(request: str) -> str:
    domains = classify(request)
    if not domains:
        return "No clear domain detected; ask one concise clarifying question before routing."
    if len(domains) == 1:
        return f"Likely a single-domain request -> {domains[0]} agent."
    return f"Multi-domain request -> fan out to: {', '.join(domains)}. Call each, then merge."
