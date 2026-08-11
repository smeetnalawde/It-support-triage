"""Pure tool logic — no MCP dependency, so it's testable without a server.

Every function returns a dict: status "ok" or "error", plus a code the caller
can branch on instead of parsing text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Mock backend data. Swap for a real directory/asset DB/approval system later —
# nothing outside this file needs to change.
_USERS: dict[str, dict[str, Any]] = {
    "smeet": {"vpn_enabled": True, "drive_access": ["finance", "eng"], "locked": False},
    "radha": {"vpn_enabled": False, "drive_access": ["marketing"], "locked": True},
}

_ASSETS: dict[str, dict[str, Any]] = {
    "LAP-1029": {"type": "laptop", "state": "active", "warranty_days": 210},
    "LAP-4471": {"type": "laptop", "state": "rma_pending", "warranty_days": 0},
}

_LICENSE_CATALOG: dict[str, dict[str, Any]] = {
    "jetbrains": {"seat_cost_usd": 289, "auto_approve_under_usd": 300},
    "tableau": {"seat_cost_usd": 840, "auto_approve_under_usd": 300},
    "figma": {"seat_cost_usd": 144, "auto_approve_under_usd": 300},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ok(**payload: Any) -> dict[str, Any]:
    return {"status": "ok", "timestamp": _now(), **payload}


def _error(code: str, message: str, **payload: Any) -> dict[str, Any]:
    return {"status": "error", "code": code, "message": message, "timestamp": _now(), **payload}


# --- Access ---

def check_user_access(user_id: str, resource: str) -> dict[str, Any]:
    user = _USERS.get(user_id.lower())
    if user is None:
        return _error(
            "USER_NOT_FOUND", f"No directory entry for user '{user_id}'.", user_id=user_id
        )

    granted = resource.lower() in [r.lower() for r in user["drive_access"]]
    return _ok(
        code="ACCESS_RESOLVED",
        user_id=user_id,
        resource=resource,
        access_granted=granted,
        account_locked=user["locked"],
        remediation=None if granted else "request_share_grant",
    )


def reset_vpn_credentials(user_id: str) -> dict[str, Any]:
    user = _USERS.get(user_id.lower())
    if user is None:
        return _error(
            "USER_NOT_FOUND", f"No directory entry for user '{user_id}'.", user_id=user_id
        )
    if user["locked"]:
        return _error(
            "ACCOUNT_LOCKED",
            f"Account '{user_id}' is locked; VPN reset requires an unlock ticket first.",
            user_id=user_id,
            next_action="open_unlock_ticket",
        )

    user["vpn_enabled"] = True
    return _ok(
        code="VPN_RESET",
        user_id=user_id,
        temp_credential=f"tmp-{user_id.lower()}-{datetime.now(timezone.utc).strftime('%H%M%S')}",
        expires_in_minutes=15,
    )


# --- Hardware ---

def get_asset_status(asset_tag: str) -> dict[str, Any]:
    asset = _ASSETS.get(asset_tag.upper())
    if asset is None:
        return _error(
            "ASSET_NOT_FOUND", f"No asset registered under tag '{asset_tag}'.", asset_tag=asset_tag
        )

    return _ok(
        code="ASSET_RESOLVED",
        asset_tag=asset_tag.upper(),
        asset_type=asset["type"],
        lifecycle_state=asset["state"],
        under_warranty=asset["warranty_days"] > 0,
        warranty_days_remaining=asset["warranty_days"],
    )


# --- Licensing ---

def request_license_approval(user_id: str, software: str, seats: int = 1) -> dict[str, Any]:
    # NOTE: ok-but-denied (approved=False, manager_review) is a valid business
    # outcome, not a failure — the agent needs to tell the two apart.
    if seats < 1:
        return _error("INVALID_REQUEST", "seats must be >= 1.", seats=seats)

    entry = _LICENSE_CATALOG.get(software.lower())
    if entry is None:
        return _error(
            "SOFTWARE_NOT_IN_CATALOG",
            f"'{software}' is not in the license catalog.",
            software=software,
            catalog=sorted(_LICENSE_CATALOG.keys()),
        )

    total_cost = entry["seat_cost_usd"] * seats
    auto = total_cost < entry["auto_approve_under_usd"]
    return _ok(
        code="APPROVAL_PROCESSED",
        user_id=user_id,
        software=software.lower(),
        seats=seats,
        total_cost_usd=total_cost,
        approved=auto,
        approval_route="auto" if auto else "manager_review",
        ticket_id=f"LIC-{abs(hash((user_id, software, seats))) % 100000:05d}",
    )
