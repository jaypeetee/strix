"""``bounty_query`` — Query HackerOne and Bugcrowd engagements from bounty-targets-data."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import requests
from agents import RunContextWrapper, function_tool

logger = logging.getLogger(__name__)

BOUNTY_DATA_BASE = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data"


def _load_bounty_data(platform: str) -> list[dict] | None:
    """Fetch bounty program data from bounty-targets-data."""
    if platform not in ("hackerone", "bugcrowd"):
        return None

    url = f"{BOUNTY_DATA_BASE}/{platform}_data.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch {platform} data: {e}")
        return None


def _filter_programs(programs: list[dict], filters: dict) -> list[dict]:
    """Extract programs matching optional filters (status, min_bounty, etc)."""
    if not isinstance(programs, list):
        return []

    status = filters.get("status")
    if status:
        programs = [p for p in programs if p.get("submission_state") == status]

    min_bounty = filters.get("min_bounty")
    if min_bounty:
        programs = [
            p
            for p in programs
            if p.get("offers_bounties") is True
        ]

    return programs


@function_tool(timeout=30)
async def bounty_query(
    ctx: RunContextWrapper,
    platform: str = "hackerone",
    status: str | None = None,
    min_bounty: int | None = None,
    limit: int = 20,
) -> str:
    """Query active bounty engagements from HackerOne or Bugcrowd.

    Use this for reconnaissance to identify active bug bounty programs
    and their reward structures.

    Args:
        platform: "hackerone" or "bugcrowd"
        status: Filter by program status (e.g., "active", "paused")
        min_bounty: Minimum max bounty in USD
        limit: Maximum results to return (default 20)

    Returns:
        JSON string with list of programs and metadata.
    """
    if platform not in ("hackerone", "bugcrowd"):
        return json.dumps({"error": f"Unknown platform: {platform}. Use 'hackerone' or 'bugcrowd'"})

    programs = _load_bounty_data(platform)
    if not programs:
        return json.dumps({"error": f"Failed to fetch {platform} data"})

    filters = {}
    if status:
        filters["status"] = status
    if min_bounty:
        filters["min_bounty"] = min_bounty

    filtered = _filter_programs(programs, filters)[:limit]

    # Extract key fields for agents
    simplified = []
    for p in filtered:
        targets_count = len(p.get("targets", [])) if p.get("targets") else 0
        simplified.append({
            "name": p.get("name", ""),
            "url": p.get("url", ""),
            "handle": p.get("handle", ""),
            "submission_state": p.get("submission_state", ""),
            "offers_bounties": p.get("offers_bounties", False),
            "offers_swag": p.get("offers_swag", False),
            "targets": targets_count,
        })

    result = {
        "platform": platform,
        "timestamp": datetime.utcnow().isoformat(),
        "total_programs": len(programs),
        "returned": len(simplified),
        "programs": simplified,
    }
    return json.dumps(result)


@function_tool(timeout=30)
async def bounty_list_domains(
    ctx: RunContextWrapper,
    platform: str = "hackerone",
    program_name: str | None = None,
) -> str:
    """List in-scope domains/targets for a bounty program.

    Use this to enumerate target domains within an active bug bounty program.

    Args:
        platform: "hackerone" or "bugcrowd"
        program_name: Specific program name; if None, returns all unique domains

    Returns:
        JSON string with list of in-scope domains.
    """
    programs = _load_bounty_data(platform)
    if not programs:
        return json.dumps({"error": f"Failed to fetch {platform} data"})

    if program_name:
        programs = [p for p in programs if p.get("name", "").lower() == program_name.lower()]
        if not programs:
            return json.dumps({"error": f"Program '{program_name}' not found"})

    domains = set()
    for p in programs:
        targets = p.get("targets", []) or []
        for target in targets:
            if isinstance(target, dict):
                identifier = target.get("target_identifier", "")
            else:
                identifier = str(target)
            if identifier:
                domains.add(identifier)

    result = {
        "platform": platform,
        "program_name": program_name or "all",
        "domain_count": len(domains),
        "domains": sorted(list(domains))[:100],
    }
    return json.dumps(result)
