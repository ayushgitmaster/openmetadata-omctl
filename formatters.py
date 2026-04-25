"""
Rich-based output formatters for omctl.
All commands route through these helpers so output is consistent.
"""

import json
from typing import Any, Dict, List, Optional

import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()

# ---------------------------------------------------------------------------
# Output format router
# ---------------------------------------------------------------------------

OUTPUT_FORMATS = ["table", "json", "yaml"]


def print_json(data: Any) -> None:
    console.print(Syntax(json.dumps(data, indent=2, default=str), "json", theme="monokai"))


def print_yaml(data: Any) -> None:
    console.print(Syntax(yaml.dump(data, default_flow_style=False, allow_unicode=True), "yaml", theme="monokai"))


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def ok(msg: str) -> None:
    rprint(f"[bold green]✓[/bold green] {msg}")


def err(msg: str) -> None:
    rprint(f"[bold red]✗[/bold red] {msg}")


def warn(msg: str) -> None:
    rprint(f"[bold yellow]⚠[/bold yellow]  {msg}")


def info(msg: str) -> None:
    rprint(f"[dim]{msg}[/dim]")


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def tags_str(entity: Dict) -> str:
    tags = entity.get("tags") or []
    return ", ".join(t.get("tagFQN", "") for t in tags) or "—"


def owners_str(entity: Dict) -> str:
    owners = entity.get("owners") or []
    return ", ".join(o.get("name") or o.get("displayName", "") for o in owners) or "—"


def svc_name(entity: Dict) -> str:
    svc = entity.get("service") or {}
    return svc.get("name") or svc.get("displayName") or "—"


# ---------------------------------------------------------------------------
# Entity list table
# ---------------------------------------------------------------------------

def print_entity_table(entities: List[Dict], entity_type: str, count: int) -> None:
    """Generic table for get commands (tables / dashboards / pipelines / topics)."""
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title=f"[bold]{entity_type}[/bold] — {count} result(s)",
        title_style="bold white",
    )
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Service", style="green")
    table.add_column("Owner(s)")
    table.add_column("Tags")
    table.add_column("Description", max_width=45)

    for e in entities:
        table.add_row(
            e.get("fullyQualifiedName") or e.get("name", ""),
            svc_name(e),
            owners_str(e),
            tags_str(e),
            (e.get("description") or "")[:120],
        )
    console.print(table)


def print_services_table(services: List[Dict], svc_type: str) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title=f"[bold]{svc_type} Services[/bold] — {len(services)} result(s)",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Description", max_width=50)

    for s in services:
        table.add_row(
            s.get("name", ""),
            s.get("serviceType") or s.get("databaseServiceType") or "—",
            (s.get("description") or "")[:100],
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Describe panels
# ---------------------------------------------------------------------------

def print_table_detail(t: Dict) -> None:
    fqn = t.get("fullyQualifiedName") or t.get("name", "")
    lines = [
        f"[bold]Service:[/bold]     {svc_name(t)}",
        f"[bold]Database:[/bold]    {(t.get('database') or {}).get('name', '—')}",
        f"[bold]Schema:[/bold]      {(t.get('databaseSchema') or {}).get('name', '—')}",
        f"[bold]Type:[/bold]        {t.get('tableType', '—')}",
        f"[bold]Owner(s):[/bold]    {owners_str(t)}",
        f"[bold]Tags:[/bold]        {tags_str(t)}",
        f"[bold]Description:[/bold] {t.get('description') or '—'}",
    ]
    console.print(Panel("\n".join(lines), title=f"[bold cyan]Table: {fqn}[/bold cyan]", expand=False))

    columns = t.get("columns") or []
    if columns:
        col_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            title=f"Columns ({len(columns)})",
        )
        col_table.add_column("Name", style="cyan")
        col_table.add_column("Data Type", style="green")
        col_table.add_column("Tags")
        col_table.add_column("Description", max_width=50)
        for col in columns:
            col_table.add_row(
                col.get("name", ""),
                col.get("dataTypeDisplay") or col.get("dataType", ""),
                ", ".join(tg.get("tagFQN", "") for tg in (col.get("tags") or [])) or "—",
                (col.get("description") or "")[:100],
            )
        console.print(col_table)


def print_dashboard_detail(d: Dict) -> None:
    fqn = d.get("fullyQualifiedName") or d.get("name", "")
    lines = [
        f"[bold]Service:[/bold]     {svc_name(d)}",
        f"[bold]Owner(s):[/bold]    {owners_str(d)}",
        f"[bold]Tags:[/bold]        {tags_str(d)}",
        f"[bold]URL:[/bold]         {d.get('sourceUrl') or d.get('dashboardUrl') or '—'}",
        f"[bold]Description:[/bold] {d.get('description') or '—'}",
    ]
    console.print(Panel("\n".join(lines), title=f"[bold cyan]Dashboard: {fqn}[/bold cyan]", expand=False))

    charts = d.get("charts") or []
    if charts:
        ct = Table(show_header=True, header_style="bold cyan", border_style="dim", title=f"Charts ({len(charts)})")
        ct.add_column("Name", style="cyan")
        ct.add_column("Type", style="green")
        ct.add_column("Description", max_width=55)
        for ch in charts:
            ct.add_row(
                ch.get("name", ""),
                ch.get("chartType", "—"),
                (ch.get("description") or "")[:100],
            )
        console.print(ct)


def print_pipeline_detail(p: Dict) -> None:
    fqn = p.get("fullyQualifiedName") or p.get("name", "")
    lines = [
        f"[bold]Service:[/bold]     {svc_name(p)}",
        f"[bold]Owner(s):[/bold]    {owners_str(p)}",
        f"[bold]Tags:[/bold]        {tags_str(p)}",
        f"[bold]URL:[/bold]         {p.get('sourceUrl') or p.get('pipelineUrl') or '—'}",
        f"[bold]Description:[/bold] {p.get('description') or '—'}",
    ]
    console.print(Panel("\n".join(lines), title=f"[bold cyan]Pipeline: {fqn}[/bold cyan]", expand=False))

    tasks = p.get("tasks") or []
    if tasks:
        tt = Table(show_header=True, header_style="bold cyan", border_style="dim", title=f"Tasks ({len(tasks)})")
        tt.add_column("Name", style="cyan")
        tt.add_column("Type", style="green")
        tt.add_column("Description", max_width=55)
        for tk in tasks:
            tt.add_row(
                tk.get("name", ""),
                tk.get("taskType", "—"),
                (tk.get("description") or "")[:100],
            )
        console.print(tt)


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------

def _node_label(node: Dict) -> str:
    fqn = node.get("fullyQualifiedName") or node.get("name") or node.get("id", "unknown")
    ntype = node.get("type") or node.get("entityType") or ""
    type_icon = {
        "table": "🗃️ ",
        "dashboard": "📊 ",
        "pipeline": "🔄 ",
        "topic": "📨 ",
        "mlmodel": "🤖 ",
    }.get(ntype.lower(), "📦 ")
    return f"{type_icon}[cyan]{fqn}[/cyan] [dim]({ntype})[/dim]"


def _build_adj(edges: List[Dict], direction: str) -> Dict[str, List[str]]:
    """Build an adjacency list. direction='downstream' or 'upstream'."""
    adj: Dict[str, List[str]] = {}
    for edge in edges:
        src = edge.get("fromEntity", {}).get("id")
        dst = edge.get("toEntity", {}).get("id")
        if not src or not dst:
            continue
        if direction == "downstream":
            adj.setdefault(src, []).append(dst)
        else:
            adj.setdefault(dst, []).append(src)
    return adj


def _render_tree(
    node_id: str,
    node_map: Dict[str, Dict],
    adj: Dict[str, List[str]],
    tree: Tree,
    visited: Optional[set] = None,
) -> None:
    if visited is None:
        visited = set()
    visited.add(node_id)
    for child_id in adj.get(node_id, []):
        if child_id in visited:
            continue
        child_node = node_map.get(child_id, {"id": child_id})
        branch = tree.add(_node_label(child_node))
        _render_tree(child_id, node_map, adj, branch, visited)


def print_lineage(lineage: Dict, upstream_depth: int, downstream_depth: int) -> None:
    entity = lineage.get("entity", {})
    nodes: List[Dict] = lineage.get("nodes") or []
    edges: List[Dict] = lineage.get("edges") or []

    root_id = entity.get("id")
    node_map: Dict[str, Dict] = {root_id: entity}
    for n in nodes:
        node_map[n["id"]] = n

    root_label = _node_label(entity)

    # Upstream
    if upstream_depth > 0:
        up_adj = _build_adj(edges, "upstream")
        up_tree = Tree(f"[bold white]▲ Upstream[/bold white]\n{root_label}")
        _render_tree(root_id, node_map, up_adj, up_tree)
        console.print(up_tree)
        console.print()

    # Downstream
    if downstream_depth > 0:
        dn_adj = _build_adj(edges, "downstream")
        dn_tree = Tree(f"[bold white]▼ Downstream[/bold white]\n{root_label}")
        _render_tree(root_id, node_map, dn_adj, dn_tree)
        console.print(dn_tree)


def print_lineage_mermaid(lineage: Dict) -> None:
    entity = lineage.get("entity", {})
    nodes: List[Dict] = lineage.get("nodes") or []
    edges: List[Dict] = lineage.get("edges") or []

    node_map: Dict[str, Dict] = {entity["id"]: entity}
    for n in nodes:
        node_map[n["id"]] = n

    lines = ["```mermaid", "graph LR"]

    def safe_id(nid: str) -> str:
        return "n" + nid.replace("-", "")[:12]

    all_ids = set(node_map.keys())
    for nid in all_ids:
        node = node_map[nid]
        label = (node.get("fullyQualifiedName") or node.get("name") or nid).replace('"', "'")
        lines.append(f'    {safe_id(nid)}["{label}"]')

    for edge in edges:
        src = edge.get("fromEntity", {}).get("id")
        dst = edge.get("toEntity", {}).get("id")
        if src and dst:
            lines.append(f"    {safe_id(src)} --> {safe_id(dst)}")

    lines.append("```")
    rprint("\n".join(lines))


# ---------------------------------------------------------------------------
# Quality / Test suites
# ---------------------------------------------------------------------------

def print_test_suites(suites: List[Dict]) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title=f"[bold]Test Suites[/bold] — {len(suites)} result(s)",
    )
    table.add_column("Name", style="cyan")
    table.add_column("FQN")
    table.add_column("Tests", style="green")
    table.add_column("Description", max_width=45)
    for s in suites:
        table.add_row(
            s.get("name", ""),
            s.get("fullyQualifiedName", ""),
            str(s.get("testCaseResultSummary", {}).get("total", "—")),
            (s.get("description") or "")[:80],
        )
    console.print(table)


def print_test_cases(cases: List[Dict]) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title=f"[bold]Test Cases[/bold] — {len(cases)} result(s)",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Entity", style="green")
    table.add_column("Last Status")
    table.add_column("Test Type")

    status_color = {"Success": "green", "Failed": "red", "Aborted": "yellow"}

    for c in cases:
        last = (c.get("testCaseResult") or {}).get("testCaseStatus") or "—"
        color = status_color.get(last, "white")
        table.add_row(
            c.get("name", ""),
            c.get("entityLink", "").split("::")[-1].rstrip(">"),
            f"[{color}]{last}[/{color}]",
            c.get("testDefinition", {}).get("name", "—"),
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Search results
# ---------------------------------------------------------------------------

def print_search_results(hits: List[Dict], query: str, total: int) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title=f'[bold]Search:[/bold] "{query}" — {total} result(s)',
    )
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Type", style="green")
    table.add_column("Service")
    table.add_column("Tags")
    table.add_column("Description", max_width=45)
    for h in hits:
        src = h.get("_source") or h
        table.add_row(
            src.get("fullyQualifiedName") or src.get("name", ""),
            src.get("entityType") or h.get("_index", "").replace("_search_index", ""),
            (src.get("service") or {}).get("name", "—"),
            ", ".join(t.get("tagFQN", "") for t in (src.get("tags") or [])) or "—",
            (src.get("description") or "")[:100],
        )
    console.print(table)
