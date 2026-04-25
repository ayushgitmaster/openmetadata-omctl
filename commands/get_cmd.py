"""
omctl get — list OpenMetadata entities.

  omctl get tables      [--service <name>] [--tag <fqn>] [--limit N] [-o table|json|yaml]
  omctl get dashboards  [--service <name>] [--limit N] [-o ...]
  omctl get pipelines   [--service <name>] [--limit N] [-o ...]
  omctl get topics      [--service <name>] [--limit N] [-o ...]
  omctl get services    [--type database|dashboard|pipeline|messaging|storage]
"""

import json
import sys
from enum import Enum
from typing import List, Optional

import typer
from rich import print as rprint

from omctl import config as cfg_module
from omctl import formatters as fmt

app = typer.Typer(help="List OpenMetadata entities.", no_args_is_help=True)


class OutputFmt(str, Enum):
    table = "table"
    json = "json"
    yaml = "yaml"


class ServiceType(str, Enum):
    database = "database"
    dashboard = "dashboard"
    pipeline = "pipeline"
    messaging = "messaging"
    storage = "storage"


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

_INDEX_MAP = {
    "tables": "table_search_index",
    "dashboards": "dashboard_search_index",
    "pipelines": "pipeline_search_index",
    "topics": "topic_search_index",
}


def _fetch_entities(
    entity_type: str,
    service: Optional[str],
    tag: Optional[str],
    limit: int,
    output: OutputFmt,
) -> None:
    client = cfg_module.get_client()
    index = _INDEX_MAP[entity_type]

    # Build query_filter for service / tag
    must_clauses: List[dict] = []
    if service:
        must_clauses.append({"term": {"service.name.keyword": service}})
    if tag:
        must_clauses.append({"term": {"tags.tagFQN.keyword": tag}})

    query_filter = {"query": {"bool": {"must": must_clauses}}} if must_clauses else None

    try:
        result = client.search(
            query="*",
            index=index,
            size=limit,
            query_filter=query_filter,
        )
    except Exception as e:
        fmt.err(str(e))
        sys.exit(1)

    hits = result.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    raw_hits = hits.get("hits", [])
    entities = [h.get("_source") or h for h in raw_hits]

    if output == OutputFmt.json:
        fmt.print_json(entities)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(entities)
    else:
        fmt.print_entity_table(entities, entity_type.capitalize(), total)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command("tables")
def get_tables(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Filter by service name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag FQN (e.g. PII.Sensitive)"),
    limit: int = typer.Option(25, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List tables."""
    _fetch_entities("tables", service, tag, limit, output)


@app.command("dashboards")
def get_dashboards(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Filter by service name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag FQN"),
    limit: int = typer.Option(25, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List dashboards."""
    _fetch_entities("dashboards", service, tag, limit, output)


@app.command("pipelines")
def get_pipelines(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Filter by service name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag FQN"),
    limit: int = typer.Option(25, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List pipelines."""
    _fetch_entities("pipelines", service, tag, limit, output)


@app.command("topics")
def get_topics(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Filter by service name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag FQN"),
    limit: int = typer.Option(25, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List messaging topics."""
    _fetch_entities("topics", service, tag, limit, output)


@app.command("services")
def get_services(
    stype: ServiceType = typer.Option(ServiceType.database, "--type", "-t", help="Service category"),
    limit: int = typer.Option(25, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """List data services (database, dashboard, pipeline, messaging, storage)."""
    _svc_path_map = {
        "database": "services/databaseServices",
        "dashboard": "services/dashboardServices",
        "pipeline": "services/pipelineServices",
        "messaging": "services/messagingServices",
        "storage": "services/storageServices",
    }
    path = _svc_path_map[stype.value]
    client = cfg_module.get_client()
    try:
        result = client.get(path, params={"limit": limit})
    except Exception as e:
        fmt.err(str(e))
        sys.exit(1)

    services = result.get("data", [])

    if output == OutputFmt.json:
        fmt.print_json(services)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(services)
    else:
        fmt.print_services_table(services, stype.value.capitalize())
