"""
omctl config — manage connection contexts.

  omctl config set-context <name> --host <url> --token <token>
  omctl config login               (interactive — prompts for credentials)
  omctl config use-context <name>
  omctl config get-contexts
  omctl config current-context
  omctl config delete-context <name>
"""

import typer
from rich import print as rprint
from rich.table import Table
from rich.console import Console

from omctl import config as cfg_module

app = typer.Typer(help="Manage OpenMetadata connection contexts.", no_args_is_help=True)
console = Console()


@app.command("set-context")
def set_context(
    name: str = typer.Argument(..., help="Context name (e.g. local, prod)"),
    host: str = typer.Option(..., "--host", "-H", help="OpenMetadata server URL"),
    token: str = typer.Option(..., "--token", "-t", help="Bearer token (JWT)"),
):
    """Create or update a named connection context."""
    config = cfg_module.load_config()
    config.setdefault("contexts", {})[name] = {"host": host, "token": token}

    # Auto-activate if it's the first context
    if not config.get("current-context"):
        config["current-context"] = name
        rprint(f"[dim]Context[/dim] [bold cyan]{name}[/bold cyan] [dim]set as current.[/dim]")

    cfg_module.save_config(config)
    rprint(f"[bold green]✓[/bold green] Context [bold cyan]{name}[/bold cyan] saved. ([dim]{host}[/dim])")


@app.command("login")
def login(
    name: str = typer.Option("default", "--name", "-n", help="Context name to save credentials under"),
    host: str = typer.Option(None, "--host", "-H", help="OpenMetadata server URL"),
    email: str = typer.Option(None, "--email", "-e", help="Login email"),
    password: str = typer.Option(None, "--password", "-p", help="Password", hide_input=True),
):
    """
    Authenticate with username/password and save the token automatically.

    If flags are omitted you will be prompted interactively.
    """
    from omctl.client import OpenMetadataClient, APIError

    if not host:
        host = typer.prompt("OpenMetadata host (e.g. http://localhost:8585)")
    if not email:
        email = typer.prompt("Email")
    if not password:
        password = typer.prompt("Password", hide_input=True)

    rprint(f"[dim]Authenticating with[/dim] {host} …")
    try:
        # Use a dummy token just to call login
        client = OpenMetadataClient(host=host, token="")
        token = client.login(email=email, password=password)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] {e.message}")
        raise typer.Exit(1)

    config = cfg_module.load_config()
    config.setdefault("contexts", {})[name] = {"host": host, "token": token}
    if not config.get("current-context"):
        config["current-context"] = name
    cfg_module.save_config(config)

    rprint(f"[bold green]✓[/bold green] Logged in. Context [bold cyan]{name}[/bold cyan] saved.")


@app.command("use-context")
def use_context(name: str = typer.Argument(..., help="Context name to switch to")):
    """Set the active context."""
    config = cfg_module.load_config()
    if name not in config.get("contexts", {}):
        rprint(f"[bold red]✗[/bold red] Context [bold]{name}[/bold] not found.")
        raise typer.Exit(1)
    config["current-context"] = name
    cfg_module.save_config(config)
    rprint(f"[bold green]✓[/bold green] Switched to context [bold cyan]{name}[/bold cyan].")


@app.command("current-context")
def current_context():
    """Print the active context name."""
    ctx = cfg_module.get_current_context_name()
    if not ctx:
        rprint("[dim]No current context set.[/dim]")
    else:
        rprint(f"[bold cyan]{ctx}[/bold cyan]")


@app.command("get-contexts")
def get_contexts():
    """List all configured contexts."""
    config = cfg_module.load_config()
    contexts = config.get("contexts", {})
    current = config.get("current-context")

    if not contexts:
        rprint("[dim]No contexts configured. Run [bold cyan]omctl config set-context[/bold cyan] to add one.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("", width=2)  # active marker
    table.add_column("Name", style="cyan")
    table.add_column("Host")

    for name, ctx in contexts.items():
        marker = "[bold green]*[/bold green]" if name == current else " "
        table.add_row(marker, name, ctx.get("host", "—"))

    console.print(table)
    rprint("\n[dim]* = current context[/dim]")


@app.command("delete-context")
def delete_context(name: str = typer.Argument(..., help="Context name to delete")):
    """Remove a context from the config."""
    config = cfg_module.load_config()
    if name not in config.get("contexts", {}):
        rprint(f"[bold red]✗[/bold red] Context [bold]{name}[/bold] not found.")
        raise typer.Exit(1)

    del config["contexts"][name]
    if config.get("current-context") == name:
        config["current-context"] = next(iter(config["contexts"]), None)
        if config["current-context"]:
            rprint(f"[dim]Current context switched to[/dim] [bold cyan]{config['current-context']}[/bold cyan].")

    cfg_module.save_config(config)
    rprint(f"[bold green]✓[/bold green] Context [bold]{name}[/bold] deleted.")
