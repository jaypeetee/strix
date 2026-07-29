"""Bounty program discovery from HackerOne and Bugcrowd via bounty-targets-data.

Optional reconnaissance tools — not loaded by default.
To enable: ``from strix.tools.bounty import enable_bounty_tools; enable_bounty_tools()``
"""

from strix.tools.bounty.tool import bounty_query, bounty_list_domains


def enable_bounty_tools() -> None:
    """Register bounty tools for agents."""
    from strix.agents.factory import register_agent_tools
    register_agent_tools(bounty_query, bounty_list_domains)


__all__ = ["bounty_query", "bounty_list_domains", "enable_bounty_tools"]
