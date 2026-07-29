"""Jira issue creation from Strix findings."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for Jira Cloud REST API."""

    def __init__(self, instance_url: str, api_token: str, email: str):
        """Initialize Jira client.

        Args:
            instance_url: Base URL of Jira instance (e.g., https://company.atlassian.net)
            api_token: Jira API token (generated in account settings)
            email: Email address associated with Jira account
        """
        self.instance_url = instance_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({"Content-Type": "application/json"})

    def create_issue(
        self,
        project_key: str,
        title: str,
        description: str,
        issue_type: str = "Bug",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create an issue in Jira.

        Args:
            project_key: Project key (e.g., "SEC")
            title: Issue title/summary
            description: Issue description (can include markdown)
            issue_type: Issue type (Bug, Task, etc.)
            **kwargs: Additional fields (labels, priority, etc.)

        Returns:
            Response with created issue key and ID.
        """
        url = f"{self.instance_url}/rest/api/3/issues"

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
            }
        }

        # Add optional fields
        if "priority" in kwargs:
            payload["fields"]["priority"] = {"name": kwargs["priority"]}
        if "labels" in kwargs:
            payload["fields"]["labels"] = kwargs["labels"]
        if "assignee" in kwargs:
            payload["fields"]["assignee"] = {"name": kwargs["assignee"]}

        try:
            resp = self.session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Jira issue: {e}")
            raise


def sync_finding_to_jira(
    instance_url: str,
    api_token: str,
    email: str,
    project_key: str,
    finding: dict[str, Any],
) -> dict[str, Any]:
    """Create a Jira issue from a Strix finding.

    Args:
        instance_url: Jira instance URL
        api_token: Jira API token
        email: Jira account email
        project_key: Target Jira project
        finding: Finding dict with title, severity, description, etc.

    Returns:
        Created issue details (key, id, etc.)
    """
    client = JiraClient(instance_url, api_token, email)

    title = finding.get("title", "Security Finding")
    severity = finding.get("severity", "medium").upper()
    description = (
        f"*Severity:* {severity}\n\n"
        f"{finding.get('description', 'No description provided')}"
    )

    # Map severity to Jira priority
    priority_map = {
        "CRITICAL": "Highest",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
    }
    priority = priority_map.get(severity, "Medium")

    return client.create_issue(
        project_key=project_key,
        title=title,
        description=description,
        issue_type="Bug",
        priority=priority,
        labels=["security", f"strix-{severity.lower()}"],
    )
