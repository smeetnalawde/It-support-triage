"""Routing tests against the deterministic classifier — no LLM, no creds."""

from common.classifier import classify, is_multi_domain, routing_hint


def test_routes_access_request():
    assert classify("I can't connect to the VPN") == ["access"]


def test_routes_hardware_request():
    assert classify("my laptop won't turn on, asset LAP-1029") == ["hardware"]


def test_routes_licensing_request():
    assert classify("please approve a Tableau license for me") == ["licensing"]


def test_multi_domain_fan_out_is_detected():
    req = "my laptop won't connect to VPN, and I also need a new software license approved"
    domains = classify(req)
    assert is_multi_domain(req) is True
    assert "access" in domains and "licensing" in domains


def test_three_distinct_request_types_route_distinctly():
    assert classify("reset my vpn password") == ["access"]
    assert classify("is my device under warranty?") == ["hardware"]
    assert classify("I need a figma seat") == ["licensing"]


def test_unknown_request_asks_for_clarification():
    assert classify("hello, are you there?") == []
    assert "clarifying" in routing_hint("hello, are you there?")


def test_routing_hint_mentions_fan_out_for_multi_domain():
    hint = routing_hint("VPN is broken and I need a license")
    assert "fan out" in hint.lower()
