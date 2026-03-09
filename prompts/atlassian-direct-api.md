# Prompt: Generate or Update the Atlassian Direct API Skill Document

---

## Your Role

Write a `SKILL.md` that teaches any coding agent to interact with Atlassian Jira and Confluence directly via REST APIs — no MCP server, no proxy, no middleware.

---

## Phase 1 — Check for an Existing Skill

Look for `SKILL.md`, `atlassian-api/SKILL.md`, `skills/atlassian-direct-api/SKILL.md`, or any file the user points to. Not found → Phase 2. Found → Phase 3.

---

## Phase 2 — Write a Fresh Skill

Produce a single `SKILL.md` file. Structure it exactly as follows, in this order:

### 2.1 YAML Frontmatter
```yaml
---
name: atlassian-direct-api
description: >
  <one concise paragraph — what the skill enables, when to trigger it,
   which products it covers, which auth methods it supports>
---
```

### 2.2 Required Sections

Follow the Canonical Skill Reference section map (§ 0–12) exactly — structure, names, and order.
The only section with non-obvious implementation requirements is §6 (Browser Session):

**§6 — Auth Method 4: Browser Session ✦ DEFAULT**
- Mark heading `✦ DEFAULT`. Include `⚠️ Agent-internal browser warning`: never use embedded agent browsers (Cline, Cursor, etc.) — always open an external browser via Playwright `headless=False`.
- **Toolchain**: `uv`/`uvx` only, no `pip`. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`. Every generated script starts with `#!/usr/bin/env -S uv run` shebang + PEP 723 `# /// script` deps block. Run via `chmod +x script.py && ./script.py` or `uv run script.py`. ⚠️ Never `python script.py` — it silently ignores the deps block.
- **File locations** (all static under `~/.atlassian-skill/`, never `tempfile` or project dir): `SESSION_FILE`, `LOCK_FILE = SKILL_HOME / "capture.lock"`, `SCRIPT_DIR = SKILL_HOME / "tmp"`.
- **Browser capture**: async Playwright only. `_find_browser(p)` tries `BROWSER_PREFERENCE` tuples in order (see Canonical Patterns). PID lock via `_acquire_lock()` / `_release_lock()` — detects competing processes, clears stale locks. `LOGIN_TIMEOUT = 300`; poll loop is `while elapsed < timeout`, not `while True`. Wrap in `try/finally` — `browser.close()` + `_release_lock()` must run on success, timeout, exception, and cancellation.
- **Login detection**: poll DOM for `meta[id="atlassian-token"]` OR `meta[name="ajs-atl-token"]`. Do NOT use `wait_for_selector()`. On detection: `context.storage_state(path=str(SESSION_FILE))`.
- **Session → headers**: build `Cookie:` string; find XSRF token by name (`atlassian.xsrf.token`, `XSRF-TOKEN`, `atl.xsrf.token`); add `X-Atlassian-Token: no-check` + `X-XSRF-TOKEN` if present.
- **Refresh**: same lock + timeout + `try/finally` pattern; load `storage_state` so SSO renews silently.

### 2.3 Code Style Rules (apply to every snippet)

- Python: use `httpx` (not `requests`). Import only what's needed: `from httpx import get, post, put, delete, request` and `from httpx import TimeoutException`. Use `async`/`await` for Playwright code.
- Secrets always come from `os.environ`, never hardcoded.
- Every script that can be run standalone must have a PEP 723 `# /// script` block.
- Use `logging` (not `print`) for any operational messages.
- Comments explain *why*, not *what*.

---

## Canonical Skill Reference

> Authoritative baseline. Phase 2: reproduce exactly. Phase 3: diff against this to find drift — propose changes only for genuine gaps, never to force alignment.

### Section Map (canonical order)

| §  | Title                                     | Key content                                                                                                                                                                                                        |
|----|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0  | Team Configuration                        | Points to `~/.atlassian-skill/config.json`; JSON template; agent creates if absent, never overwrites                                                                                                               |
| 1  | Quick-Start Decision Tree                 | ASCII tree: offer browser login first; fall back to token only if user provides one                                                                                                                                |
| 2  | Instance & Base URL Patterns              | Table: Cloud vs DC/Server × Jira vs Confluence; auto-detect rule                                                                                                                                                   |
| 3  | Auth Method 1 — API Token                 | Cloud only; `Basic base64(email:token)`; Python `httpx` example                                                                                                                                                    |
| 4  | Auth Method 2 — PAT                       | DC/Server; `Bearer <PAT>`; v2 API required for DC                                                                                                                                                                  |
| 5  | Auth Method 3 — OAuth 2.0                 | 3LO Cloud; app registration; auth URL; token exchange; refresh; cloud ID discovery                                                                                                                                 |
| 6  | Auth Method 4 — Browser Session ✦ DEFAULT | External browser only; `uv`/PEP 723; static `SKILL_HOME` paths; `_find_browser()` + `BROWSER_PREFERENCE`; PID lock; `LOGIN_TIMEOUT`; `try/finally` cleanup; meta-tag polling; header construction; session refresh |
| 7  | Jira REST API — Core Operations           | Issues CRUD, transitions, comments, worklogs, attachments; boards/sprints; pagination helper                                                                                                                       |
| 8  | Confluence REST API — Core Operations     | v2 vs v1 detection; pages CRUD (version bump); CQL search; spaces; attachments; comments                                                                                                                           |
| 9  | Error Handling & Retry Strategy           | `AtlassianAPIError`; retry loop; 429/5xx backoff; 401/403/404                                                                                                                                                      |
| 10 | Common Workflow Recipes                   | ≥3 end-to-end examples                                                                                                                                                                                             |
| 11 | Environment Variable Conventions          | Canonical names table; dotenv PEP 723 load                                                                                                                                                                         |
| 12 | Key API Reference Quick-Links             | Jira v3, Agile, Confluence v2/v1, OAuth scopes                                                                                                                                                                     |
| 13 | Security Notes                            | No committed secrets; `~/.atlassian-skill/` is `0700`; HTTPS; scope minimisation; rate limits                                                                                                                      |

### Canonical Code Patterns

These patterns are load-bearing. Any deviation is a `[BREAKING]` change (see Phase 3).

**Python HTTP helper (API token auth)**
```python
# /// script
# dependencies = ["httpx", "python-dotenv"]
# ///
from base64 import b64encode
from os import environ
from httpx import get, post
from dotenv import load_dotenv
load_dotenv()

credentials = b64encode(
    f"{environ['ATLASSIAN_EMAIL']}:{environ['ATLASSIAN_API_TOKEN']}".encode()
).decode()
HEADERS = {
    "Authorization": f"Basic {credentials}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}
BASE = environ["ATLASSIAN_BASE_URL"]

def jira_get(path: str, **params):
    r = get(f"{BASE}/rest/api/3{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()
```

**Browser session — load-bearing constants and patterns**
```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["playwright", "httpx", "python-dotenv"]
# ///
from pathlib import Path

SKILL_HOME   = Path.home() / ".atlassian-skill"   # mode 0o700
SESSIONS_DIR = SKILL_HOME / "sessions"            # one file per team (Cloud) or per team+product (DC)
SCRIPT_DIR   = SKILL_HOME / "tmp"
POLL_INTERVAL = 2
LOGIN_TIMEOUT = 300

# session_path(team, product) → SESSIONS_DIR/<slug>.json (Cloud) or <slug>-{jira|confluence}.json (DC)
# lock_path(team) → SESSIONS_DIR/<slug>.lock  (per-team — parallel captures for different teams OK)

# _acquire_lock(lock_file): check file; os.kill(pid,0) to test liveness; clear stale; write os.getpid()
# _release_lock(lock_file): lock_file.unlink(missing_ok=True)

# capture_session(team, product="jira"): reads config.json for URL → acquires lock → opens browser
#   → polls meta tags → storage_state(session_path(team, product)) → finally: close + release
# refresh_session(team, product="jira"): same but loads storage_state first (SSO silent renew)
# load_session(team, product="jira"): reads session file → filters cookies by base URL → returns headers dict

# Meta tags (login signal): meta[id="atlassian-token"] OR meta[name="ajs-atl-token"]

BROWSER_PREFERENCE = [
    ("chromium", "chrome"),
    ("firefox",  None),          # p.firefox.launch() — not a channel
    ("chromium", "msedge"),
    ("chromium", "chrome-beta"),
    ("chromium", None),          # last resort; error msg is only place for `playwright install chromium`
]
```

CLI usage:
```bash
# Default team, Jira
uv run capture_session.py

# Named team and product
uv run capture_session.py "Client B" confluence
```

**Retry / error wrapper**
```python
import time
from httpx import request, TimeoutException

class AtlassianAPIError(Exception):
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")

def api_call(method: str, url: str, headers: dict, retries: int = 3, **kwargs):
    for attempt in range(retries):
        try:
            r = request(method, url, headers=headers, timeout=30, **kwargs)
        except TimeoutException:
            if attempt < retries - 1:
                time.sleep(2 ** attempt); continue
            raise
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 5))); continue
        if r.status_code in (500, 502, 503, 504):
            if attempt < retries - 1:
                time.sleep(2 ** attempt); continue
        if r.status_code == 401: raise AtlassianAPIError(401, "Session expired or invalid credentials.")
        if r.status_code == 403: raise AtlassianAPIError(403, f"Permission denied: {r.text}")
        if r.status_code == 404: raise AtlassianAPIError(404, f"Not found: {url}")
        if not r.is_success:             raise AtlassianAPIError(r.status_code, r.text)
        return r.json() if r.content else {}
    raise AtlassianAPIError(0, "Exceeded retry limit")
```

**Pagination helper**
```python
def jira_search_all(jql: str, fields: str = "*all") -> list:
    results, start = [], 0
    while True:
        page = jira_get("/search", jql=jql, fields=fields, startAt=start, maxResults=100)
        results.extend(page["issues"])
        start += len(page["issues"])
        if start >= page["total"]:
            break
    return results
```

**Canonical environment variable names**

| Variable                  | Purpose                           |
|---------------------------|-----------------------------------|
| `ATLASSIAN_BASE_URL`      | Root URL, no trailing slash       |
| `ATLASSIAN_EMAIL`         | User email (API token auth)       |
| `ATLASSIAN_API_TOKEN`     | Cloud API token                   |
| `ATLASSIAN_PAT`           | Data Center Personal Access Token |
| `ATLASSIAN_CLIENT_ID`     | OAuth 2.0 client ID               |
| `ATLASSIAN_CLIENT_SECRET` | OAuth 2.0 client secret           |
| `ATLASSIAN_SESSION_FILE`  | Path to browser session JSON      |

---

## Phase 3 — Conservative Update (existing skill found)

> **Prime directive: do the least work necessary. Preserve every architectural decision, section order, code pattern, and naming convention already in the file.**

Read the entire file first. Tag every proposed change:

| Tag          | Meaning                                                          | Needs approval?                                |
|--------------|------------------------------------------------------------------|------------------------------------------------|
| `[PATCH]`    | Typo, broken link, wording fix                                   | No                                             |
| `[ADDITIVE]` | New content only, nothing removed                                | No                                             |
| `[UPDATE]`   | Replaces existing content                                        | Show BEFORE/AFTER, wait for confirmation       |
| `[BREAKING]` | Reorders/renames sections, removes content, changes architecture | Never silently — always explain tradeoff first |

**Breaking changes** (never silent): reordering/renaming sections; switching auth default; changing toolchain (`uv`, Playwright, `httpx`); removing any auth method; renaming env vars; any change to browser session flow or meta-tag polling.

**Always safe to add without asking**: new recipes, new endpoint examples, new env vars (add only, never rename), new quick-links, new security notes.

**After updating**: don't bump version numbers, reformat untouched code, reorder sections, or touch frontmatter unless explicitly asked.

---

## Output

Output the file only — no wrapper prose. For `[UPDATE]`/`[BREAKING]`, show labelled BEFORE/AFTER diff first, then wait for approval before writing.

---

## Anti-Patterns — Never Do These

- ❌ **Wrong runner**: replace `uvx`/PEP 723 with `pip`+venv, or run scripts with `python script.py` (silently ignores deps → `ModuleNotFoundError`). Always `uv run` or `./script.py` after `chmod +x`.
- ❌ **Wrong HTTP / async library**: replace `httpx` with `requests`, or `async_playwright` with the sync Playwright API. Do not `import httpx` wholesale — import only what's needed: `from httpx import get, post, put, delete, request` and `from httpx import TimeoutException`.
- ❌ **Wrong login signal**: replace meta-tag polling with `page.wait_for_selector()`, or ask the user to press Enter. `meta[id="atlassian-token"]` / `meta[name="ajs-atl-token"]` is the only signal.
- ❌ **Wrong browser launch**: use the agent's internal browser (Cline, Cursor, etc.) — it has no persistent storage. Always external via `headless=False`. Never hardcode `executable_path`; use `channel` + `BROWSER_PREFERENCE`.
- ❌ **`playwright install chromium` in setup**: it belongs only in the `_find_browser()` error message. Never in instructions, prerequisites, or comments.
- ❌ **Unbounded browser lifecycle**: use `while True` instead of `while elapsed < timeout`, or close the browser only on the happy path. Always `try/finally` — `browser.close()` + `_release_lock()` must run on success, timeout, exception, and cancellation.
- ❌ **Wrong file locations**: write session files, `.env`, config, or scripts to the project dir or cwd. Use `tempfile.gettempdir()` for `SCRIPT_DIR` (macOS path in shell `$()` → zsh parse error). All files go under `~/.atlassian-skill/`.
- ❌ **Overwrite config.json**: the agent creates it only when absent. It is user-managed.
- ❌ **Default to token auth** without confirming with the user first. Browser Session is the default; tokens are opt-in.
- ❌ **Add a local OAuth callback server** unless the user explicitly requests an interactive OAuth flow.
- ❌ **Generate the file then describe it** — output the file, done.
