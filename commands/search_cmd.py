"""
omctl search — full-text search across all metadata entities.

  omctl search <query> [--type all|table|dashboard|pipeline|topic] [--limit N] [-o table|json|yaml]
"""

import sys
from enum import Enum
from typing import Optional

import typer

from omctl import config as cfg_module
from omctl import formatters as fmt
from omctl.client import APIError

app = typer.Typer(help="Full-text search across all metadata entities.", no_args_is_help=True)


class EntityFilter(str, Enum):
    all = "all"
    table = "table"
    dashboard = "dashboard"
    pipeline = "pipeline"
    topic = "topic"
    glossary_term = "glossary_term"
    tag = "tag"


class OutputFmt(str, Enum):
    table = "table"
    json = "json"
    yaml = "yaml"


_INDEX_MAP = {
    "all": "all",
    "table": "table_search_index",
    "dashboard": "dashboard_search_index",
    "pipeline": "pipeline_search_index",
    "topic": "topic_search_index",
    "glossary_term": "glossary_term_search_index",
    "tag": "tag_search_index",
}


@app.command("query")
def search_query(
    query: str = typer.Argument(..., help='Search query (e.g. "orders" or "customer PII")'),
    entity_type: EntityFilter = typer.Option(EntityFilter.all, "--type", "-t", help="Entity type to search"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results to return"),
    output: OutputFmt = typer.Option(OutputFmt.table, "--output", "-o", help="Output format"),
):
    """
    Full-text search across OpenMetadata entities.

    Examples:\n
      omctl search query orders\n
      omctl search query "customer data" --type table\n
      omctl search query pii --type table --limit 50\n
    """
    client = cfg_module.get_client()
    index = _INDEX_MAP[entity_type.value]

    try:
        result = client.search(query=query, index=index, size=limit)
    except APIError as e:
        fmt.err(e.message)
        sys.exit(1)

    hits_obj = result.get("hits", {})
    total = hits_obj.get("total", {}).get("value", 0)
    raw_hits = hits_obj.get("hits", [])

    if output == OutputFmt.json:
        fmt.print_json(raw_hits)
    elif output == OutputFmt.yaml:
        fmt.print_yaml(raw_hits)
    else:
        if not raw_hits:
            fmt.info(f'No results for "{query}".')
        else:
            fmt.print_search_results(raw_hits, query, total)
