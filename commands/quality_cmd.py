"""
omctl quality — data quality test suites and test cases.

  omctl quality suites  [--limit N] [-o table|json|yaml]
  omctl quality cases   <suite-fqn>  [-o table|json|yaml]
  omctl quality summary <suite-fqn>
"""

import sys
from enum import Enum
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from omctl import config as cfg_module
from omctl import formatters as fmt
from omctl.client import APIError

app = typer.Typer(help="View data quality test suites and results.", no_args_is_help=True)
console = Console()


class OutputFmt(str, Enum):
    table = "table"
    json = "json"
    yaml = "yaml"


@app.command("suites")
def list_suites(
    limit: int = typer.Option(25, "--limit", "-l", help="Max results"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List all data quality test suites."""
    client = cfg_module.get_client()
    try:
        result = client.get(
            "dataQuality/testSuites",
            params={"limit": limit, "fields": "tests,testCaseResultSummary"},
        )
    except APIError as e:
        fmt.err(e.message)
        sys.exit(1)

    suites = result.get("data", [])

    if output == OutputFmt.json:
        fmt.print_json(suites)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(suites)
    else:
        fmt.print_test_suites(suites)


@app.command("cases")
def list_cases(
    suite_fqn: str = typer.Argument(..., help="Test suite fully-qualified name"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List test cases belonging to a test suite."""
    client = cfg_module.get_client()
    try:
        result = client.get(
            "dataQuality/testCases",
            params={
                "testSuiteId": _resolve_suite_id(client, suite_fqn),
                "limit": limit,
                "fields": "testDefinition,testCaseResult",
            },
        )
    except APIError as e:
        fmt.err(e.message)
        sys.exit(1)

    cases = result.get("data", [])

    if output == OutputFmt.json:
        fmt.print_json(cases)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(cases)
    else:
        fmt.print_test_cases(cases)


@app.command("summary")
def suite_summary(
    suite_fqn: str = typer.Argument(..., help="Test suite fully-qualified name"),
):
    """Print a pass/fail summary for a test suite."""
    client = cfg_module.get_client()
    try:
        suite = client.get(
            f"dataQuality/testSuites/name/{suite_fqn}",
            params={"fields": "tests,testCaseResultSummary"},
        )
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Suite not found: [bold]{suite_fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    summary = suite.get("testCaseResultSummary") or {}
    total = summary.get("total", 0)
    success = summary.get("success", 0)
    failed = summary.get("failed", 0)
    aborted = summary.get("aborted", 0)
    queued = total - success - failed - aborted

    pass_rate = f"{(success / total * 100):.1f}%" if total else "N/A"
    color = "green" if failed == 0 and total > 0 else ("red" if failed > 0 else "dim")

    lines = [
        f"[bold]Suite:[/bold]    {suite.get('fullyQualifiedName') or suite.get('name')}",
        f"[bold]Tests:[/bold]    {total}",
        f"[bold green]Passed:[/bold green]   {success}",
        f"[bold red]Failed:[/bold red]   {failed}",
        f"[bold yellow]Aborted:[/bold yellow]  {aborted}",
        f"[bold]Pass rate:[/bold] [{color}]{pass_rate}[/{color}]",
    ]
    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold]Quality Summary[/bold]",
            border_style=color,
            expand=False,
        )
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_suite_id(client, suite_fqn: str) -> str:
    """Resolve a test suite FQN to its UUID."""
    try:
        suite = client.get(f"dataQuality/testSuites/name/{suite_fqn}", params={"fields": "id"})
        return suite["id"]
    except APIError as e:
        fmt.err(f"Suite not found: [bold]{suite_fqn}[/bold] — {e.message}")
        sys.exit(1)
