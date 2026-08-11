"""Unit tests for the MCP tool logic.

These exercise the pure functions in ``mcp_server.logic`` directly, so they
need no running server, no MCP SDK, and no LLM. They cover both success paths
and every simulated failure mode.
"""

from mcp_server import logic

# --- Access ---------------------------------------------------------------

def test_check_user_access_granted():
    r = logic.check_user_access("smeet", "finance")
    assert r["status"] == "ok"
    assert r["access_granted"] is True


def test_check_user_access_denied_has_remediation():
    r = logic.check_user_access("smeet", "hr")
    assert r["status"] == "ok"
    assert r["access_granted"] is False
    assert r["remediation"] == "request_share_grant"


def test_check_user_access_unknown_user_fails_cleanly():
    r = logic.check_user_access("nobody", "finance")
    assert r["status"] == "error"
    assert r["code"] == "USER_NOT_FOUND"


def test_reset_vpn_locked_account_is_error():
    # radha's account is locked -> reset must be refused with a next action.
    r = logic.reset_vpn_credentials("radha")
    assert r["status"] == "error"
    assert r["code"] == "ACCOUNT_LOCKED"
    assert r["next_action"] == "open_unlock_ticket"


def test_reset_vpn_ok_issues_temp_credential():
    r = logic.reset_vpn_credentials("smeet")
    assert r["status"] == "ok"
    assert r["temp_credential"].startswith("tmp-smeet-")


# --- Hardware -------------------------------------------------------------

def test_get_asset_status_ok():
    r = logic.get_asset_status("lap-1029")  # case-insensitive
    assert r["status"] == "ok"
    assert r["asset_tag"] == "LAP-1029"
    assert r["under_warranty"] is True


def test_get_asset_status_not_found_is_the_graceful_failure_case():
    r = logic.get_asset_status("LAP-9999")
    assert r["status"] == "error"
    assert r["code"] == "ASSET_NOT_FOUND"


# --- Licensing ------------------------------------------------------------

def test_license_auto_approves_cheap_seat():
    r = logic.request_license_approval("smeet", "figma", seats=1)
    assert r["status"] == "ok"
    assert r["approved"] is True
    assert r["approval_route"] == "auto"


def test_license_routes_expensive_to_manager():
    r = logic.request_license_approval("smeet", "tableau", seats=1)
    assert r["status"] == "ok"
    assert r["approved"] is False              # denied auto-approval, not a tool failure
    assert r["approval_route"] == "manager_review"


def test_license_unknown_software_fails():
    r = logic.request_license_approval("smeet", "not-a-real-app")
    assert r["status"] == "error"
    assert r["code"] == "SOFTWARE_NOT_IN_CATALOG"
    assert "catalog" in r
