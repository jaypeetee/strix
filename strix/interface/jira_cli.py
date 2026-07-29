#!/usr/bin/env python3
"""CLI tool to sync Strix findings to Jira."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from strix.core.paths import latest_run_dir, run_dir_for, runs_base_dir
from strix.interface.viewer.jira_sync import sync_finding_to_jira
from strix.interface.viewer.transcript import read_vulnerabilities


logger = logging.getLogger(__name__)
console = Console()


def list_runs() -> list[str]:
    """List available runs."""
    runs_dir = runs_base_dir()
    if not runs_dir.is_dir():
        return []
    return sorted([d.name for d in runs_dir.iterdir() if d.is_dir()])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Strix findings to Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all findings from latest run to Jira
  strix-jira-sync --jira-url https://company.atlassian.net \\
                  --email user@company.com \\
                  --token YOUR_API_TOKEN \\
                  --project SEC

  # Sync specific run
  strix-jira-sync --run my-scan-2025-01-15 \\
                  --jira-url https://company.atlassian.net \\
                  --email user@company.com \\
                  --token YOUR_API_TOKEN \\
                  --project SEC

  # List available runs
  strix-jira-sync --list-runs

  # Filter by severity
  strix-jira-sync --severity critical,high \\
                  --jira-url https://company.atlassian.net \\
                  --email user@company.com \\
                  --token YOUR_API_TOKEN \\
                  --project SEC
        """,
    )

    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="List available runs and exit",
    )

    parser.add_argument(
        "--run",
        type=str,
        help="Run name to sync (default: latest)",
    )

    parser.add_argument(
        "--jira-url",
        type=str,
        help="Jira instance URL (e.g., https://company.atlassian.net)",
    )

    parser.add_argument(
        "--email",
        type=str,
        help="Jira account email",
    )

    parser.add_argument(
        "--token",
        type=str,
        help="Jira API token (get from id.atlassian.com)",
    )

    parser.add_argument(
        "--project",
        type=str,
        help="Jira project key (e.g., SEC)",
    )

    parser.add_argument(
        "--severity",
        type=str,
        help="Comma-separated severity levels to sync (e.g., critical,high)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # List runs
    if args.list_runs:
        runs = list_runs()
        if not runs:
            console.print("[yellow]No runs found[/]")
            return

        table = Table(title="Available Runs")
        table.add_column("Run Name", style="cyan")
        for run in reversed(runs):
            table.add_row(run)
        console.print(table)
        return

    # Validate required args
    if not all([args.jira_url, args.email, args.token, args.project]):
        console.print(
            "[red]Error: --jira-url, --email, --token, and --project are required[/]"
        )
        parser.print_help()
        sys.exit(1)

    # Find run directory
    if args.run:
        run_dir = run_dir_for(args.run)
        if not run_dir.is_dir():
            console.print(f"[red]Run not found: {args.run}[/]")
            sys.exit(1)
    else:
        # Use latest run
        run_dir = latest_run_dir()
        if not run_dir:
            console.print("[red]No runs found[/]")
            sys.exit(1)

    console.print(f"[cyan]Syncing run:[/] {run_dir.name}")

    # Read findings
    try:
        findings = read_vulnerabilities(run_dir)
    except Exception as e:
        console.print(f"[red]Error reading findings: {e}[/]")
        sys.exit(1)

    if not findings:
        console.print("[yellow]No findings to sync[/]")
        return

    # Filter by severity
    if args.severity:
        severity_filter = set(args.severity.lower().split(","))
        findings = [f for f in findings if f.get("severity", "").lower() in severity_filter]

    if not findings:
        console.print("[yellow]No findings match the severity filter[/]")
        return

    console.print(f"[cyan]Found {len(findings)} findings to sync[/]\n")

    # Sync findings
    created = 0
    failed = 0

    for finding in findings:
        try:
            result = sync_finding_to_jira(
                instance_url=args.jira_url,
                api_token=args.token,
                email=args.email,
                project_key=args.project,
                finding=finding,
            )
            issue_key = result.get("key", "?")
            console.print(
                f"  [green]✓[/] {finding.get('title', 'Unknown')[:60]} → {issue_key}"
            )
            created += 1
        except Exception as e:
            console.print(
                f"  [red]✗[/] {finding.get('title', 'Unknown')[:60]} - {str(e)}"
            )
            if args.verbose:
                logger.exception("Sync failed for finding")
            failed += 1

    console.print()
    console.print(f"[green]Created: {created}[/] | [red]Failed: {failed}[/]")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
