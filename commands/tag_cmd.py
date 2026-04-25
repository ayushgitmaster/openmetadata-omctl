"""
omctl tag — manage tags on metadata entities.

  omctl tag list   <fqn> [--type table]
  omctl tag add    <fqn> <tag-fqn> [--type table]
  omctl tag remove <fqn> <tag-fqn> [--type table]
  omctl tag classifications
"""

import sys
from enum import Enum
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from omctl import config as cfg_module
from omctl import formatters as fmt
from omctl.client import APIError

app = typer.Typer(help="Manage tags on metadata entities.", no_args_is_help=True)
console = Console()


class EntityType(str, Enum):
    table = "tables"
    dashboard = "dashboards"
    pipeline = "pipelines"
    topic = "topics"
    glossary_term = "glossaryTerms"


_ENTITY_LABEL = {
    "tables": "table",
    "dashboards": "dashboard",
    "pipelines": "pipeline",
    "topics": "topic",
    "glossaryTerms": "glossary term",
}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command("list")
def tag_list(
    fqn: str = typer.Argument(..., help="Fully-qualified name of the entity"),
    entity_type: EntityType = typer.Option(EntityType.table, "--type", "-t", help="Entity type"),
):
    """List all tags currently applied to an entity."""
    client = cfg_module.get_client()
    try:
        entity = client.get_entity(entity_type.value, fqn, fields="tags")
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Entity not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    tags = entity.get("tags") or []
    if not tags:
        rprint(f"[dim]No tags on[/dim] [bold]{fqn}[/bold]")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                  title=f"Tags on [bold]{fqn}[/bold]")
    table.add_column("Tag FQN", style="cyan")
    table.add_column("Label Type", style="green")
    table.add_column("State")
    table.add_column("Source")

    for tag in tags:
        table.add_row(
            tag.get("tagFQN", ""),
            tag.get("labelType", "—"),
            tag.get("state", "—"),
            tag.get("source", "—"),
        )
    console.print(table)


@app.command("add")
def tag_add(
    fqn: str = typer.Argument(..., help="Fully-qualified name of the entity"),
    tag_fqn: str = typer.Argument(..., help="Tag to apply (e.g. PII.Sensitive)"),
    entity_type: EntityType = typer.Option(EntityType.table, "--type", "-t", help="Entity type"),
):
    """Add a tag to an entity."""
    client = cfg_module.get_client()

    # Resolve entity ID
    try:
        entity = client.get_entity(entity_type.value, fqn, fields="id,tags")
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Entity not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    entity_id = entity.get("id")
    if not entity_id:
        fmt.err("Could not resolve entity ID.")
        sys.exit(1)

    # Check if tag already exists
    existing = [t.get("tagFQN") for t in (entity.get("tags") or [])]
    if tag_fqn in existing:
        rprint(f"[yellow]⚠[/yellow]  Tag [bold cyan]{tag_fqn}[/bold cyan] already applied to [bold]{fqn}[/bold].")
        return

    try:
        client.tag_entity(entity_type.value, entity_id, tag_fqn)
    except APIError as e:
        fmt.err(f"Failed to add tag: {e.message}")
        sys.exit(1)

    fmt.ok(f"Tag [bold cyan]{tag_fqn}[/bold cyan] added to [bold]{fqn}[/bold].")


@app.command("remove")
def tag_remove(
    fqn: str = typer.Argument(..., help="Fully-qualified name of the entity"),
    tag_fqn: str = typer.Argument(..., help="Tag to remove (e.g. PII.Sensitive)"),
    entity_type: EntityType = typer.Option(EntityType.table, "--type", "-t", help="Entity type"),
):
    """Remove a tag from an entity."""
    client = cfg_module.get_client()

    # Resolve entity ID and current tags
    try:
        entity = client.get_entity(entity_type.value, fqn, fields="id,tags")
    except APIError as e:
        if e.status_code == 404:
            fmt.err(f"Entity not found: [bold]{fqn}[/bold]")
        else:
            fmt.err(e.message)
        sys.exit(1)

    entity_id = entity.get("id")
    existing = [t.get("tagFQN") for t in (entity.get("tags") or [])]

    if tag_fqn not in existing:
        rprint(f"[yellow]⚠[/yellow]  Tag [bold cyan]{tag_fqn}[/bold cyan] is not applied to [bold]{fqn}[/bold].")
        return

    try:
        client.untag_entity(entity_type.value, fqn, tag_fqn, entity_id)
    except APIError as e:
        fmt.err(f"Failed to remove tag: {e.message}")
        sys.exit(1)

    fmt.ok(f"Tag [bold cyan]{tag_fqn}[/bold cyan] removed from [bold]{fqn}[/bold].")


@app.command("classifications")
def list_classifications(
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
):
    """List all tag classifications and their tags."""
    client = cfg_module.get_client()
    try:
        result = client.get("classifications", params={"limit": limit})
    except APIError as e:
        fmt.err(e.message)
        sys.exit(1)

    classifications = result.get("data", [])
    table = Table(
        show_header=True, header_style="bold cyan", border_style="dim",
        title=f"Tag Classifications — {len(classifications)} found",
    )
    table.add_column("Classification", style="cyan")
    table.add_column("Description", max_width=60)
    table.add_column("Tag Count", style="green")

    for cls in classifications:
        table.add_row(
            cls.get("name", ""),
            (cls.get("description") or "")[:100],
            str(cls.get("termCount", "—")),
        )
    console.print(table)
