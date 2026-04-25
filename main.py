"""
omctl — kubectl-style CLI for OpenMetadata.

Usage:
  omctl config set-context local --host http://localhost:8585 --token <token>
  omctl config login

  omctl get tables --service snowflake --limit 10
  omctl get dashboards
  omctl get pipelines
  omctl get services

  omctl describe table warehouse.default.public.orders
  omctl describe dashboard metabase.default.Revenue

  omctl lineage show warehouse.default.orders --upstream 2 --downstream 3
  omctl lineage show warehouse.default.orders --format mermaid
  omctl lineage impact warehouse.default.orders

  omctl tag add warehouse.default.orders PII.Sensitive
  omctl tag remove warehouse.default.orders PII.Sensitive
  omctl tag list warehouse.default.orders
  omctl tag classifications

  omctl quality suites
  omctl quality cases my.test.suite
  omctl quality summary my.test.suite

  omctl search query "customer orders" --type table
"""

from typing import Optional

import typer
from rich import print as rprint

from omctl import __version__
from omctl import config as cfg_module
from omctl.commands import (
    config_cmd,
    describe_cmd,
    get_cmd,
    lineage_cmd,
    quality_cmd,
    search_cmd,
    tag_cmd,
)

# ---------------------------------------------------------------------------
# Root app
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="omctl",
    help=(
        "[bold cyan]omctl[/bold cyan] — kubectl-style CLI for [bold]OpenMetadata[/bold]\n\n"
        "Manage metadata, explore lineage, and enforce governance directly from your terminal."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

# ---------------------------------------------------------------------------
# Sub-command groups
# ---------------------------------------------------------------------------

app.add_typer(config_cmd.app, name="config", help="Manage connection contexts.")
app.add_typer(get_cmd.app, name="get", help="List entities (tables, dashboards, pipelines…).")
app.add_typer(describe_cmd.app, name="describe", help="Show full detail for a single entity.")
app.add_typer(lineage_cmd.app, name="lineage", help="Explore data lineage and impact.")
app.add_typer(quality_cmd.app, name="quality", help="View data quality suites and results.")
app.add_typer(tag_cmd.app, name="tag", help="Manage tags on entities.")
app.add_typer(search_cmd.app, name="search", help="Full-text search across all entities.")

# ---------------------------------------------------------------------------
# Global callback — --version / --context
# ---------------------------------------------------------------------------


def _version_callback(value: bool) -> None:
    if value:
        rprint(f"[bold cyan]omctl[/bold cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        envvar="OMCTL_CONTEXT",
        help="Override the active context for this command.",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """omctl — OpenMetadata CLI"""
    if context:
        cfg_module.set_context_override(context)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> None:
    app()


if __name__ == "__main__":
    run()
