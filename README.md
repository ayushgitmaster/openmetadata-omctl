# omctl

> There's no `kubectl` for your data catalog — until now.  
> `omctl` brings OpenMetadata to the terminal: query tables, trace lineage, enforce tags, and monitor data quality without ever opening a browser.

```
 Usage: omctl [OPTIONS] COMMAND [ARGS]...

╭─ Commands ───────────────────────────────────────────────────────╮
│ config     Manage connection contexts                            │
│ get        List entities (tables, dashboards, pipelines…)        │
│ describe   Show full details for a single entity                 │
│ lineage    Explore data lineage and impact                       │
│ quality    View data quality suites and results                  │
│ tag        Manage tags on entities                               │
│ search     Full-text search across all entities                  │
╰──────────────────────────────────────────────────────────────────╯
```

---

## What is this?

OpenMetadata is a powerful metadata platform — but every interaction requires a browser. `omctl` fixes that.

It's a **developer-first CLI** that wraps OpenMetadata's REST API with a clean, scriptable interface — so you can discover data, trace lineage, apply governance tags, and check data quality directly from your terminal or CI pipeline.

---

## Installation

**Requirements:** Python 3.9+

```bash
git clone https://github.com/your-username/openmetadata-omctl
cd openmetadata-omctl
pip install -e .
```

Verify it works:

```bash
omctl --version
# omctl v0.1.0
```

---

## Quick Start

### Step 1 — Connect to OpenMetadata

**Interactive login** (recommended for local dev):
```bash
omctl config login
# > Host: http://localhost:8585
# > Email: admin@open-metadata.org
# > Password: ****
# ✓ Logged in. Context "default" saved.
```

**Token-based** (recommended for CI/scripts):
```bash
omctl config set-context prod \
  --host https://openmetadata.mycompany.com \
  --token eyJhbGci...
```

### Step 2 — Run your first command

```bash
omctl get tables --limit 10
```

That's it. You're querying your data catalog from the terminal.

---

## Commands

### `config` — Manage environments

```bash
omctl config login                          # authenticate interactively
omctl config set-context prod --host <url> --token <jwt>
omctl config get-contexts                   # list all environments
omctl config use-context prod               # switch active environment
omctl config current-context               # show which context is active
omctl config delete-context staging        # remove an environment
```

> Switch context for a single command without changing your default:
> ```bash
> omctl --context prod get tables
> ```

---

### `get` — List entities

```bash
omctl get tables
omctl get tables --service snowflake_prod         # filter by service
omctl get tables --tag PII.Sensitive              # filter by tag
omctl get tables --limit 50 --output json         # pipe-friendly output
omctl get dashboards
omctl get pipelines
omctl get topics
omctl get services --type database                # database | dashboard | pipeline | messaging | storage
```

**Output formats:** `table` (default) · `json` · `yaml`

---

### `describe` — Inspect a single entity

```bash
omctl describe table  snowflake_prod.default.public.orders
omctl describe dashboard metabase.Revenue_Dashboard
omctl describe pipeline airflow.nightly_transform
omctl describe topic kafka.user-events
```

Shows: columns, data types, owner, tags, description, source URL — everything in one panel.

---

### `lineage` — Trace data flow

```bash
# Show lineage tree (upstream + downstream)
omctl lineage show snowflake_prod.default.public.orders

# Control depth
omctl lineage show snowflake_prod.default.public.orders --upstream 3 --downstream 2

# Export as Mermaid diagram (paste into any markdown)
omctl lineage show snowflake_prod.default.public.orders --format mermaid

# Impact analysis — what breaks if this table changes?
omctl lineage impact snowflake_prod.default.public.orders --depth 5
```

Example tree output:
```
▲ Upstream
└── 🗃️  snowflake_prod.default.public.orders (table)
    └── 🔄 airflow.ingest_orders (pipeline)

▼ Downstream
└── 🗃️  snowflake_prod.default.public.orders (table)
    ├── 📊 metabase.Revenue_Dashboard (dashboard)
    └── 🗃️  snowflake_prod.default.public.order_metrics (table)
```

---

### `tag` — Govern your metadata

```bash
omctl tag list   snowflake_prod.default.public.orders          # see applied tags
omctl tag add    snowflake_prod.default.public.orders PII.Sensitive
omctl tag remove snowflake_prod.default.public.orders PII.Sensitive
omctl tag classifications                                       # list all tag categories
```

Supports `--type` flag for non-table entities:
```bash
omctl tag add myDashboard PersonalData.Email --type dashboard
```

---

### `quality` — Monitor data health

```bash
omctl quality suites                         # list all test suites
omctl quality cases my.nightly.suite         # list test cases in a suite
omctl quality summary my.nightly.suite       # pass/fail summary panel
```

Example summary output:
```
╭─── Quality Summary ──────────────╮
│ Suite:     my.nightly.suite      │
│ Tests:     42                    │
│ Passed:    40                    │
│ Failed:    2                     │
│ Pass rate: 95.2%                 │
╰──────────────────────────────────╯
```

---

### `search` — Find anything

```bash
omctl search query "customer orders"
omctl search query "revenue" --type dashboard
omctl search query "pii email" --type table --limit 50
omctl search query "events" --type topic --output json
```

---

## Scripting & CI Usage

Every command supports `--output json` for piping:

```bash
# Get all PII tables and extract FQNs
omctl get tables --tag PII.Sensitive --output json | jq '.[].fullyQualifiedName'

# Export lineage as Mermaid into a file
omctl lineage show warehouse.orders --format mermaid >> lineage.md

# Check data quality in a CI step
omctl quality summary nightly-checks --output json | jq '.testCaseResultSummary.failed'

# Use a specific context in CI without changing config
omctl --context prod quality summary nightly-checks
# or via environment variable:
# OMCTL_CONTEXT=prod omctl quality summary nightly-checks
```

---

## Configuration File

Contexts are stored at `~/.omctl/config.yaml`:

```yaml
current-context: local
contexts:
  local:
    host: http://localhost:8585
    token: eyJhbGci...
  prod:
    host: https://openmetadata.mycompany.com
    token: eyJhbGci...
```

---

## Project Structure

```
omctl/
├── main.py              ← root CLI entry point
├── config.py            ← context management (~/.omctl/config.yaml)
├── client.py            ← OpenMetadata REST API wrapper (httpx)
├── formatters.py        ← Rich-based output (tables, trees, panels)
└── commands/
    ├── config_cmd.py    ← omctl config *
    ├── get_cmd.py       ← omctl get *
    ├── describe_cmd.py  ← omctl describe *
    ├── lineage_cmd.py   ← omctl lineage *
    ├── quality_cmd.py   ← omctl quality *
    ├── tag_cmd.py       ← omctl tag *
    └── search_cmd.py    ← omctl search *
```

---

## Built With

- [Typer](https://typer.tiangolo.com/) — CLI framework
- [Rich](https://rich.readthedocs.io/) — terminal formatting
- [httpx](https://www.python-httpx.org/) — HTTP client
- [OpenMetadata REST API](https://docs.open-metadata.org/v1.12.x/main-concepts/apis) — metadata backend

---

## Built for the WeMakeDevs × OpenMetadata Hackathon 2026
