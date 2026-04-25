"""
omctl lineage — explore data lineage.

  omctl lineage show <fqn>  [--type table] [--upstream N] [--downstream N] [--format tree|mermaid|json]
  omctl lineage impact <fqn> [--type table] [--depth N]
"""

import sys
from enum import Enum
from typing import Optional

import typer

from omctl import config as cfg_module
from omctl import formatters as fmt
from omctl.client import APIError

app = typer.Typer(help="Explore data lineage.", no_args_is_help=True)


class EntityType(str, Enum):
    table = "table"
    dashboard = "dashboard"
    pipeline = "pipeline"
    topic = "topic"
    mlmodel = "mlmodel"


class LineageFormat(str, Enum):
    tree = "tree"
    mermaid = "mermaid"
    json = "json"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command("show")
def lineage_show(
    fqn: str = typer.Argument(..., help="Fully-qualified name of the entity"),
    entity_type: EntityType = typer.Option(EntityType.table, "--type", "-t", help="Entity type"),
    upstream: int = typer.Option(1, "--upstream", "-u", help="Upstream depth (0 to disable)"),
    downstream: int = typer.Option(1, "--downstream", "-d", help="Downstream depth (0 to disable)"),
    lineage_format: LineageFormat = typer.Option(LineageFormat.tree, "--format", "-f", help="Output format"),
):
    """
    Show lineage graph for an entity.

    Examples:\n
      omctl lineage show warehouse.default.orders\n
      omctl lineage show warehouse.default.orders --upstream 3 --downstream 2\n
      omctl lineage show warehouse.default.orders --format mermaid\n
    """
    client = cfg_module.get_client()
    try:
        lineage = client.get_lineage(
            entity_type=entity_type.value,
            fqn=fqn,
            upstream_depth=upstream,
            downstream_depth=downstream,
        )
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Entity not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    if lineage_format == LineageFormat.json:
        fmt.print_json(lineage)
    elif lineage_format == LineageFormat.mermaid:
        fmt.print_lineage_mermaid(lineage)
    else:
        fmt.print_lineage(lineage, upstream_depth=upstream, downstream_depth=downstream)


@app.command("impact")
def lineage_impact(
    fqn: str = typer.Argument(..., help="Fully-qualified name of the entity to analyse"),
    entity_type: EntityType = typer.Option(EntityType.table, "--type", "-t", help="Entity type"),
    depth: int = typer.Option(3, "--depth", "-d", help="How many hops downstream to follow"),
    lineage_format: LineageFormat = typer.Option(LineageFormat.tree, "--format", "-f", help="Output format"),
):
    """
    Show the downstream impact of a change to this entity.

    Useful before schema migrations — quickly see all dashboards,
    pipelines, and downstream tables that would be affected.

    Examples:\n
      omctl lineage impact warehouse.default.orders\n
      omctl lineage impact warehouse.default.orders --depth 5\n
      omctl lineage impact warehouse.default.orders --format mermaid\n
    """
    client = cfg_module.get_client()
    try:
        lineage = client.get_lineage(
            entity_type=entity_type.value,
            fqn=fqn,
            upstream_depth=0,
            downstream_depth=depth,
        )
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Entity not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    nodes = lineage.get("nodes") or []
    edges = lineage.get("edges") or []

    # Summary header
    from rich import print as rprint
    rprint(
        f"\n[bold]Impact analysis:[/bold] [cyan]{fqn}[/cyan] "
        f"([dim]{entity_type.value}, downstream depth={depth}[/dim])"
    )

    # Count by type
    type_counts: dict = {}
    entity_id = (lineage.get("entity") or {}).get("id")
    for node in nodes:
        ntype = node.get("type") or node.get("entityType") or "unknown"
        type_counts[ntype] = type_counts.get(ntype, 0) + 1
    if type_counts:
        summary = "  Affected: " + ", ".join(f"[bold]{v}[/bold] {k}(s)" for k, v in type_counts.items())
        rprint(summary)
    else:
        rprint("  [dim]No downstream dependencies found.[/dim]")
    rprint()

    if lineage_format == LineageFormat.json:
        fmt.print_json(lineage)
    elif lineage_format == LineageFormat.mermaid:
        fmt.print_lineage_mermaid(lineage)
    else:
        fmt.print_lineage(lineage, upstream_depth=0, downstream_depth=depth)
