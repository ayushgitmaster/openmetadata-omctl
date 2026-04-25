"""
Config management for omctl.
Stores contexts in ~/.omctl/config.yaml

Example config:
  current-context: local
  contexts:
    local:
      host: http://localhost:8585
      token: eyJhbGci...
    prod:
      host: https://openmetadata.mycompany.com
      token: eyJhbGci...
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

CONFIG_DIR = Path.home() / ".omctl"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Module-level override set by the --context global flag
_context_override: Optional[str] = None


def set_context_override(ctx: Optional[str]) -> None:
    global _context_override
    _context_override = ctx


def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {"contexts": {}, "current-context": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {"contexts": {}, "current-context": None}


def save_config(config: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def get_current_context_name() -> Optional[str]:
    return _context_override or load_config().get("current-context")


def get_client():
    """Return an OpenMetadataClient for the active context, or exit with an error."""
    from omctl.client import OpenMetadataClient
    from rich import print as rprint

    cfg = load_config()
    ctx_name = _context_override or cfg.get("current-context")

    if not ctx_name:
        rprint(
            "[bold red]✗[/bold red] No context configured.\n"
            "  Run: [bold cyan]omctl config set-context <name> --host <url> --token <token>[/bold cyan]\n"
            "  Or:  [bold cyan]omctl config login[/bold cyan]"
        )
        sys.exit(1)

    ctx = cfg.get("contexts", {}).get(ctx_name)
    if not ctx:
        rprint(
            f"[bold red]✗[/bold red] Context [bold]{ctx_name}[/bold] not found.\n"
            "  Run [bold cyan]omctl config get-contexts[/bold cyan] to list available contexts."
        )
        sys.exit(1)

    return OpenMetadataClient(host=ctx["host"], token=ctx.get("token", ""))
