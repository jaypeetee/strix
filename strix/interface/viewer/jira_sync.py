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
        """Create an issue in Jira using v2 API (more stable).

        Args:
            project_key: Project key (e.g., "SEC")
            title: Issue title/summary
            description: Issue description (plain text)
            issue_type: Issue type (Bug, Task, etc.)
            **kwargs: Additional fields (labels, priority, etc.)

        Returns:
            Response with created issue key and ID.
        """
        url = f"{self.instance_url}/rest/api/2/issue"

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": description,
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
    """Create a Jira issue from a Strix finding with all details.

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

    # Build comprehensive description with all finding details
    description_parts = [
        f"Severity: {severity}",
        f"CVSS Score: {finding.get('cvss', 'N/A')}",
    ]

    if finding.get('description'):
        description_parts.append(f"\nDescription:\n{finding['description']}")

    if finding.get('assumptions'):
        description_parts.append(f"\nAssumptions:\n{finding['assumptions']}")

    if finding.get('remediation_steps'):
        description_parts.append(f"\nRemediation:\n{finding['remediation_steps']}")

    if finding.get('evidence'):
        description_parts.append(f"\nEvidence:\n{finding['evidence']}")

    if finding.get('poc_description'):
        description_parts.append(f"\nProof of Concept:\n{finding['poc_description']}")

    if finding.get('code_locations') and isinstance(finding['code_locations'], list):
        code_locs = finding['code_locations']
        if code_locs:
            description_parts.append("\nCode Locations:")
            for loc in code_locs:
                file = loc.get('file', 'unknown')
                line = loc.get('start_line', '?')
                description_parts.append(f"  - {file}:{line}")

    description = "\n".join(description_parts)

    # Map severity to Jira priority
    priority_map = {
        "CRITICAL": "Highest",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
    }
    priority = priority_map.get(severity, "Medium")

    # Add CVE if available
    labels = ["security", f"strix-{severity.lower()}"]
    if finding.get('cve'):
        labels.append(finding['cve'])

    return client.create_issue(
        project_key=project_key,
        title=title,
        description=description,
        issue_type="Task",
        priority=priority,
        labels=labels,
    )
