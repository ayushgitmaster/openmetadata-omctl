"""
omctl describe — show full detail for a single entity.

  omctl describe table     <fqn>
  omctl describe dashboard <fqn>
  omctl describe pipeline  <fqn>
  omctl describe topic     <fqn>
"""

import sys
from enum import Enum
from typing import Optional

import typer
from rich import print as rprint

from omctl import config as cfg_module
from omctl import formatters as fmt
from omctl.client import APIError

app = typer.Typer(help="Show full details for a single entity.", no_args_is_help=True)


class OutputFmt(str, Enum):
    table = "table"
    json = "json"
    yaml = "yaml"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command("table")
def describe_table(
    fqn: str = typer.Argument(..., help="Fully-qualified name (e.g. snowflake.default.public.orders)"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """Show full detail for a table including columns, tags, and owner."""
    client = cfg_module.get_client()
    fields = "columns,tags,owners,followers,usageSummary,joins,tableConstraints"
    try:
        entity = client.get_entity("tables", fqn, fields=fields)
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Table not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    if output == OutputFmt.json:
        fmt.print_json(entity)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(entity)
    else:
        fmt.print_table_detail(entity)


@app.command("dashboard")
def describe_dashboard(
    fqn: str = typer.Argument(..., help="Fully-qualified name"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """Show full detail for a dashboard including charts, tags, and owner."""
    client = cfg_module.get_client()
    fields = "charts,tags,owners,followers,usageSummary"
    try:
        entity = client.get_entity("dashboards", fqn, fields=fields)
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Dashboard not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    if output == OutputFmt.json:
        fmt.print_json(entity)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(entity)
    else:
        fmt.print_dashboard_detail(entity)


@app.command("pipeline")
def describe_pipeline(
    fqn: str = typer.Argument(..., help="Fully-qualified name"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """Show full detail for a pipeline including tasks, tags, and owner."""
    client = cfg_module.get_client()
    fields = "tasks,tags,owners,followers,pipelineStatus"
    try:
        entity = client.get_entity("pipelines", fqn, fields=fields)
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Pipeline not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    if output == OutputFmt.json:
        fmt.print_json(entity)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(entity)
    else:
        fmt.print_pipeline_detail(entity)


@app.command("topic")
def describe_topic(
    fqn: str = typer.Argument(..., help="Fully-qualified name"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """Show full detail for a messaging topic."""
    client = cfg_module.get_client()
    fields = "tags,owners,followers"
    try:
        entity = client.get_entity("topics", fqn, fields=fields)
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Topic not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    if output == OutputFmt.json:
        fmt.print_json(entity)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(entity)
    else:
        # Generic fallback: show as a panel
        from rich.panel import Panel
        from rich.console import Console
        console = Console()
        name = entity.get("fullyQualifiedName") or entity.get("name", "")
        lines = [
            f"[bold]Service:[/bold]     {fmt.svc_name(entity)}",
            f"[bold]Owner(s):[/bold]    {fmt.owners_str(entity)}",
            f"[bold]Tags:[/bold]        {fmt.tags_str(entity)}",
            f"[bold]Schema Type:[/bold] {entity.get('schemaType', '—')}",
            f"[bold]Partitions:[/bold]  {entity.get('partitions', '—')}",
            f"[bold]Description:[/bold] {entity.get('description') or '—'}",
        ]
        console.print(Panel("\n".join(lines), title=f"[bold cyan]Topic: {name}[/bold cyan]", expand=False))
