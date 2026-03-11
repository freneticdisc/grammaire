---
name: atlassian-api
description: >
  Direct access to Atlassian Jira and Confluence APIs for coding agents. Use this skill whenever a task involves reading
  or writing Jira issues, projects, boards, sprints, comments, attachments, worklogs, or Confluence pages, spaces,
  macros, or attachments. Trigger on any request mentioning Jira, Confluence, Atlassian, tickets, epics, sprints,
  backlogs, wiki pages, or any related workflow. This skill covers all auth mechanisms (API token, OAuth 2.0, PAT,
  browser session) and provides precise REST call patterns for both Cloud and Data Center deployments.
license: GPLv3
compatibility: Designed for Claude, Cline, KiloCode (or similar products)
---

# Atlassian Direct API Skill

> **Philosophy**: No local proxy, no MCP server, no middleware. Issue HTTP requests directly
> from the agent runtime. Authenticate once, then drive Jira and Confluence entirely through
> their versioned REST APIs.

---

## 0. Team Configuration

Instance URLs live in `~/.atlassian-skill/config.json` — not in this skill document.

```json
{
  "teams": [
    {
      "name": "My Org",
      "jira_url": "https://<org>.atlassian.net",
      "confluence_url": "https://<org>.atlassian.net/wiki",
      "deployment": "cloud"
    },
    {
      "name": "Client B",
      "jira_url": "https://jira.clientb.com",
      "confluence_url": "https://confluence.clientb.com",
      "deployment": "datacenter"
    }
  ],
  "default_team": "My Org"
}
```

`deployment` is `"cloud"` or `"datacenter"` and determines session file naming:
- **Cloud**: one session file per team covers both Jira and Confluence (shared auth domain `*.atlassian.net`). Stored as `sessions/<slug>.json`.
- **Data Center**: Jira and Confluence may be on different hosts with separate auth. Stored as `sessions/<slug>-jira.json` and `sessions/<slug>-confluence.json`.

> **Agents**: if `config.json` is absent, create it from the template above and ask the
> user to fill in their org URL. Never overwrite an existing `config.json`. Read the
> `default_team` entry to resolve the base URL without asking the user.

---

## 1. Quick-Start Decision Tree

```
START HERE — default auth method is Browser Session (§6).
Before proceeding, confirm with the user:
  "I'll open an external browser for you to log in and capture the session.
   Do you have an API token or PAT you'd prefer to use instead?"

  ├── User confirms browser login (or gives no preference)
  │     └── Use Browser Session (§6)  ← DEFAULT
  │
  └── User provides a token
        ├── Atlassian Cloud + email + API token → Auth Method 1 — API Token (§3)
        ├── Data Center + PAT              → Auth Method 2 — PAT (§4)
        └── Cloud + OAuth app credentials  → Auth Method 3 — OAuth 2.0 (§5)
```

---

## 2. Instance & Base URL Patterns

| Deployment           | Jira Base URL                 | Confluence Base URL                |
|----------------------|-------------------------------|------------------------------------|
| Cloud                | `https://<org>.atlassian.net` | `https://<org>.atlassian.net/wiki` |
| Data Center / Server | `https://<host>:<port>`       | `https://<host>:<port>/confluence` |

**Detect automatically**: If the URL contains `.atlassian.net`, it is Cloud. Otherwise, treat as Data Center.

---

## 3. Authentication Method 1 — API Token (Cloud Only, Recommended)

### Obtain
1. User visits: `https://id.atlassian.com/manage-profile/security/api-tokens`
2. Click **Create API token** → label it → copy the token string.
3. Token does **not expire** unless revoked.

### Usage — HTTP Basic Auth
```
Authorization: Basic <base64(email:api_token)>
```

### Python example
```python
import httpx, base64, os
from httpx import get, post

EMAIL = os.environ["ATLASSIAN_EMAIL"]
TOKEN = os.environ["ATLASSIAN_API_TOKEN"]
BASE  = os.environ["ATLASSIAN_BASE_URL"]   # e.g. https://acme.atlassian.net

credentials = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {credentials}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

def jira_get(path: str, **params):
    r = get(f"{BASE}/rest/api/3{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def jira_post(path: str, body: dict):
    r = post(f"{BASE}/rest/api/3{path}", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()
```

---

## 4. Authentication Method 2 — Personal Access Token / PAT (Data Center & Server)

### Obtain
`Profile (avatar) → Personal Access Tokens → Create token`
Or admin path: `<base>/secure/ViewProfile.jspa` → *Personal Access Tokens*

### Usage — Bearer Token
```
Authorization: Bearer <PAT_STRING>
```

```python
PAT = os.os.environ["ATLASSIAN_PAT"]
HEADERS = {
    "Authorization": f"Bearer {PAT}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}
# Use Jira REST API v2 for Data Center (not v3)
API_VERSION = "/rest/api/2"
```

> ⚠️ Data Center uses **API v2** (`/rest/api/2`). Cloud supports both v2 and v3; prefer v3 for Cloud.

---

## 5. Authentication Method 3 — OAuth 2.0 (3-Legged, Cloud)

Use when acting on behalf of a user, or when building a persistent integration.

### App registration
1. `https://developer.atlassian.com/console/myapps/` → Create app → OAuth 2.0 (3LO)
2. Set callback URL, enable scopes (e.g. `read:jira-work`, `write:jira-work`, `read:confluence-content.all`)
3. Save `CLIENT_ID` and `CLIENT_SECRET`

### Authorization flow
```
GET https://auth.atlassian.com/authorize
  ?audience=api.atlassian.com
  &client_id=<CLIENT_ID>
  &scope=<SPACE_SEPARATED_SCOPES>
  &redirect_uri=<CALLBACK>
  &state=<RANDOM_STATE>
  &response_type=code
  &prompt=consent
```

### Token exchange
```python
from httpx import get, post

def exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str):
    r = post("https://auth.atlassian.com/oauth/token", json={
        "grant_type":    "authorization_code",
        "client_id":     client_id,
        "client_secret": client_secret,
        "code":          code,
        "redirect_uri":  redirect_uri,
    })
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "refresh_token": "...", "expires_in": 3600}

def refresh_token(refresh_tok: str, client_id: str, client_secret: str):
    r = post("https://auth.atlassian.com/oauth/token", json={
        "grant_type":    "refresh_token",
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_tok,
    })
    r.raise_for_status()
    return r.json()
```

### Usage
```python
ACCESS_TOKEN = "<token_from_exchange>"
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

# Discover accessible resources (Cloud only)
def get_cloud_id():
    r = get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers=HEADERS
    )
    r.raise_for_status()
    resources = r.json()
    return resources[0]["id"]  # cloudId — required for API calls

# OAuth base URL differs from API-token base URL
CLOUD_ID = get_cloud_id()
JIRA_BASE = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}"
CONF_BASE = f"https://api.atlassian.com/ex/confluence/{CLOUD_ID}"
```

---

## 6. Authentication Method 4 — Browser Session ✦ DEFAULT

Default auth method — works across Cloud, DC, SSO, and MFA with no token management.

> ⚠️ **Agent-internal browser warning** — agents like Cline and Cursor have an embedded
> browser. **Do not use it here.** It has no persistent session storage and its cookies
> are inaccessible to scripts. The script below always opens an external system browser.

### Step 1 — Install uv and set up file locations

**Install `uv` once per machine:**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Every generated script must start with a shebang + PEP 723 deps block, and use only static paths:
```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["playwright", "httpx", "python-dotenv"]
# ///
from pathlib import Path

SKILL_HOME   = Path.home() / ".atlassian-skill"   # mode 0o700 — treat like ~/.ssh/
SESSIONS_DIR = SKILL_HOME / "sessions"            # one file per team (or per team+product for DC)
SCRIPT_DIR   = SKILL_HOME / "tmp"
```

Run with `chmod +x script.py && ./script.py` or `uv run script.py`.
> ⚠️ Never `python script.py` — it silently ignores the deps block → `ModuleNotFoundError`.

**Session file naming** — derived from the team slug and deployment type:

```python
import json, re

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def session_path(team: str, product: str = "jira") -> Path:
    """
    Return the session file path for a team.

    Cloud:       one file covers both Jira + Confluence (shared auth domain).
                 ~/.atlassian-skill/sessions/<slug>.json
    Data Center: Jira and Confluence may be on different hosts → separate files.
                 ~/.atlassian-skill/sessions/<slug>-jira.json
                 ~/.atlassian-skill/sessions/<slug>-confluence.json
    """
    cfg   = json.loads((SKILL_HOME / "config.json").read_text())
    entry = next(t for t in cfg["teams"] if t["name"] == team)
    slug  = _slug(team)
    SESSIONS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if entry["deployment"] == "cloud":
        return SESSIONS_DIR / f"{slug}.json"
    return SESSIONS_DIR / f"{slug}-{product}.json"

def lock_path(team: str) -> Path:
    """Per-team lock — allows parallel captures for different teams."""
    return SESSIONS_DIR / f"{_slug(team)}.lock"
```

### Step 2 — Launch browser and auto-detect login completion

Polls for Atlassian's XSRF meta tags — injected only after a successful authenticated page
load. No user interaction needed beyond logging in.

> **Browser preference** — uses already-installed browsers; no download required.
> Chromium-based: `channel=`; Firefox: separate `p.firefox` engine.
>
> | Priority | Browser | Mechanism |
> |---|---|---|
> | 1 | Chrome | `channel="chrome"` |
> | 2 | Firefox | `p.firefox.launch()` |
> | 3 | Edge | `channel="msedge"` |
> | 4 | Chrome Beta | `channel="chrome-beta"` |
> | 5 | Playwright Chromium | `channel=None` ⚠️ requires prior `playwright install chromium` |
>
> `playwright install chromium` never runs as a setup step — it appears only in the
> error message when all five options fail.

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["playwright", "httpx", "python-dotenv"]
# ///

import asyncio, logging, os, json
from pathlib import Path
from traceback import format_exc
from playwright.async_api import async_playwright, Browser
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# Static paths — no shell evaluation, no tempfile, no surprises
SKILL_HOME    = Path.home() / ".atlassian-skill"
SESSIONS_DIR  = SKILL_HOME / "sessions"
SCRIPT_DIR    = SKILL_HOME / "tmp"
POLL_INTERVAL = 2    # seconds between DOM checks
LOGIN_TIMEOUT = 300  # seconds before giving up and closing the browser (5 min)

# Preferred browsers in order — first available wins.
# Chromium-based browsers use channel=; Firefox uses p.firefox engine.
BROWSER_PREFERENCE = [
    ("chromium", "chrome"),       # Google Chrome stable
    ("firefox",  None),           # Mozilla Firefox (separate Playwright engine)
    ("chromium", "msedge"),       # Microsoft Edge stable
    ("chromium", "chrome-beta"),  # Google Chrome Beta
    ("chromium", None),           # Playwright-managed Chromium (last resort)
]

async def _find_browser(p) -> Browser:
    """Try browsers in preference order; raise if none found."""
    for engine, channel in BROWSER_PREFERENCE:
        try:
            if engine == "firefox":
                browser = await p.firefox.launch(headless=False)
            else:
                browser = await p.chromium.launch(headless=False, channel=channel)
            label = "firefox" if engine == "firefox" else (channel or "chromium")
            logging.info("Using browser: %s", label)
            return browser
        except Exception:
            label = "firefox" if engine == "firefox" else (channel or "chromium")
            logging.debug("Browser '%s' not available, trying next…", label)
    raise RuntimeError(
        "No supported browser found. Install Chrome, Firefox, or Edge, "
        "or run: uvx playwright install chromium"
    )

def _acquire_lock(lock_file: Path) -> None:
    """Write a PID lock file. Raise if another live capture for this team is running."""
    if lock_file.exists():
        try:
            pid = int(lock_file.read_text().strip())
            os.kill(pid, 0)
            raise RuntimeError(
                f"A browser login session is already in progress (PID {pid}). "
                f"If that process is no longer running, delete {lock_file} and retry."
            )
        except ProcessLookupError:
            logging.warning("Removing stale lock file from PID %s", lock_file.read_text().strip())
            lock_file.unlink()
    lock_file.write_text(str(os.getpid()))

def _release_lock(lock_file: Path) -> None:
    lock_file.unlink(missing_ok=True)

async def capture_session(team: str,
                          product: str = "jira",
                          sleep_duration: float = POLL_INTERVAL,
                          timeout: float = LOGIN_TIMEOUT) -> None:
    cfg      = json.loads((SKILL_HOME / "config.json").read_text())
    entry    = next(t for t in cfg["teams"] if t["name"] == team)
    url      = entry["jira_url"] if product == "jira" else entry["confluence_url"]
    state_file = session_path(team, product)
    lock_file  = lock_path(team)

    SKILL_HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    _acquire_lock(lock_file)

    browser = None
    try:
        async with async_playwright() as p:
            browser = await _find_browser(p)
            context = await browser.new_context()
            page    = await context.new_page()

            await page.goto(url)
            logging.info(
                "Browser opened for %s / %s — please log in (timeout: %ds).",
                team, product, timeout
            )

            elapsed = 0.0
            while elapsed < timeout:
                try:
                    token_present = (
                        await page.query_selector('meta[id="atlassian-token"]')
                        or await page.query_selector('meta[name="ajs-atl-token"]')
                    )
                    if token_present:
                        await context.storage_state(path=str(state_file))
                        logging.info("Session saved → %s", state_file)
                        return
                    logging.warning("Waiting for authenticated page load… (%.0fs / %ds)", elapsed, timeout)
                except Exception:
                    logging.error(format_exc())

                await asyncio.sleep(sleep_duration)
                elapsed += sleep_duration

            raise TimeoutError(
                f"Login not completed within {timeout}s. "
                "Browser closed. Re-run capture_session.py to try again."
            )
    finally:
        if browser:
            try:
                await browser.close()
                logging.info("Browser closed.")
            except Exception:
                logging.debug("Browser already closed: %s", format_exc())
        _release_lock(lock_file)

if __name__ == "__main__":
    import sys
    load_dotenv(SKILL_HOME / ".env")
    cfg = json.loads((SKILL_HOME / "config.json").read_text())
    team    = sys.argv[1] if len(sys.argv) > 1 else cfg["default_team"]
    product = sys.argv[2] if len(sys.argv) > 2 else "jira"
    asyncio.run(capture_session(team=team, product=product))
```

### Step 3 — Convert cookies to request headers

```python
import json, os
from pathlib import Path

SKILL_HOME   = Path.home() / ".atlassian-skill"
SESSIONS_DIR = SKILL_HOME / "sessions"

def load_session(team: str, product: str = "jira") -> dict:
    """Load saved browser session as request headers for the given team and product."""
    state_file = session_path(team, product)   # uses session_path() from Step 1
    data       = json.loads(state_file.read_text())

    cfg   = json.loads((SKILL_HOME / "config.json").read_text())
    entry = next(t for t in cfg["teams"] if t["name"] == team)
    base  = entry["jira_url"] if product == "jira" else entry["confluence_url"]

    cookie_str = "; ".join(
        f"{c['name']}={c['value']}"
        for c in data["cookies"]
        if base in c.get("domain", "") or c.get("domain", "").lstrip(".") in base
    )
    xsrf_token = next(
        (c["value"] for c in data["cookies"]
         if c["name"] in ("atlassian.xsrf.token", "XSRF-TOKEN", "atl.xsrf.token")),
        None,
    )
    headers = {
        "Cookie":       cookie_str,
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }
    if xsrf_token:
        headers["X-Atlassian-Token"] = "no-check"
        headers["X-XSRF-TOKEN"]      = xsrf_token
    return headers

# Usage:
# HEADERS = load_session("My Org")                   # Jira, default team
# HEADERS = load_session("My Org", "confluence")     # Confluence, same team
# HEADERS = load_session("Client B", "jira")         # different team
```

### Step 4 — Validate session
```python
import json
from httpx import get
from pathlib import Path

SKILL_HOME = Path.home() / ".atlassian-skill"
cfg  = json.loads((SKILL_HOME / "config.json").read_text())
team = cfg["default_team"]
BASE = next(t for t in cfg["teams"] if t["name"] == team)["jira_url"]

HEADERS = load_session(team)   # from Step 3
r = get(f"{BASE}/rest/api/2/myself", headers=HEADERS)
if r.status_code == 200:
    me = r.json()
    logging.info("Authenticated as %s (%s)", me["displayName"], me["emailAddress"])
elif r.status_code == 401:
    logging.error("Session expired — re-run: capture_session.py '%s'", team)
```

### Session rotation / silent refresh

Same structure as `capture_session` (PID lock, timeout, `try/finally`). Only difference: load existing storage state so SSO sessions renew silently without re-login.

```python
async def refresh_session(team: str,
                          product: str = "jira",
                          timeout: float = LOGIN_TIMEOUT) -> None:
    cfg        = json.loads((SKILL_HOME / "config.json").read_text())
    entry      = next(t for t in cfg["teams"] if t["name"] == team)
    url        = entry["jira_url"] if product == "jira" else entry["confluence_url"]
    state_file = session_path(team, product)
    lock_file  = lock_path(team)

    _acquire_lock(lock_file)
    browser = None
    try:
        async with async_playwright() as p:
            browser = await _find_browser(p)
            # ← Only difference from capture_session: reuse saved cookies
            context = await browser.new_context(storage_state=str(state_file))
            page    = await context.new_page()
            await page.goto(f"{url}/rest/api/2/myself")
            elapsed = 0.0
            while elapsed < timeout:
                try:
                    if (await page.query_selector('meta[id="atlassian-token"]')
                            or await page.query_selector('meta[name="ajs-atl-token"]')):
                        await context.storage_state(path=str(state_file))
                        logging.info("Session refreshed → %s", state_file)
                        return
                except Exception:
                    logging.error(format_exc())
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
            raise TimeoutError(f"Session refresh not completed within {timeout}s.")
    finally:
        if browser:
            try: await browser.close()
            except Exception: pass
        _release_lock(lock_file)
```

---

## 7. Jira REST API — Core Operations

> All examples assume `jira_get` / `jira_post` helpers from §3 are in scope.
> Replace `/rest/api/3` with `/rest/api/2` for Data Center.

### Issues

```python
from httpx import put, post

# Get issue
jira_get("/issue/PROJ-123")

# Search (JQL)
jira_get("/search", jql="project=PROJ AND status='In Progress'", maxResults=50, fields="summary,status,assignee")

# Create issue
jira_post("/issue", {
    "fields": {
        "project":     {"key": "PROJ"},
        "summary":     "Implement feature X",
        "issuetype":   {"name": "Story"},
        "description": {
            "type":    "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Details here."}]}]
        },
        "priority":    {"name": "High"},
        "assignee":    {"accountId": "<account_id>"},
    }
})

# Update issue
put(f"{BASE}/rest/api/3/issue/PROJ-123", headers=HEADERS, json={
    "fields": {"summary": "New summary", "priority": {"name": "Medium"}}
})

# Transition (change status)
transitions = jira_get("/issue/PROJ-123/transitions")
target = next(t for t in transitions["transitions"] if t["name"] == "Done")
jira_post("/issue/PROJ-123/transitions", {"transition": {"id": target["id"]}})

# Add comment
jira_post("/issue/PROJ-123/comment", {
    "body": {
        "type": "doc", "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Resolved in PR #42."}]}]
    }
})

# Log work
jira_post("/issue/PROJ-123/worklog", {
    "timeSpent": "2h 30m",
    "comment": {"type": "doc", "version": 1, "content": []},
    "started": "2024-03-01T09:00:00.000+0000"
})

# Upload attachment
with open("screenshot.png", "rb") as f:
    post(
        f"{BASE}/rest/api/3/issue/PROJ-123/attachments",
        headers={**HEADERS, "X-Atlassian-Token": "no-check", "Content-Type": None},
        files={"file": ("screenshot.png", f, "image/png")}
    )
```

### Projects & Boards

```python
jira_get("/project/search", maxResults=50)           # list all projects
jira_get("/project/PROJ")                            # project detail
jira_get("/board", projectKeyOrId="PROJ")            # boards for project  (Agile API)
jira_get("/board/42/sprint", state="active")         # active sprint
jira_get("/board/42/backlog", maxResults=100)         # backlog items
```

### Users

```python
jira_get("/user/search", query="john@example.com")
jira_get("/myself")
```

### Bulk / Pagination pattern

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

---

## 8. Confluence REST API — Core Operations

> Confluence v2 API (`/wiki/api/v2`) is preferred on Cloud.
> Confluence v1 (`/wiki/rest/api`) is required for Data Center / Server.

### Detect API version
```python
# Cloud → use v2 where available; fall back to v1 for unsupported endpoints
# Data Center → always v1
CONF_V2 = f"{BASE}/wiki/api/v2"
CONF_V1 = f"{BASE}/wiki/rest/api"
```

### Pages

```python
from httpx import get, post, put, delete

# List pages in space (v2)
get(f"{CONF_V2}/pages", headers=HEADERS, params={"spaceKey": "ENG", "limit": 50}).json()

# Get page with body (v2)
get(f"{CONF_V2}/pages/{page_id}", headers=HEADERS,
    params={"body-format": "storage"}).json()

# Create page (v1 — works on both)
post(f"{CONF_V1}/content", headers=HEADERS, json={
    "type":  "page",
    "title": "API Design Guidelines",
    "space": {"key": "ENG"},
    "body": {
        "storage": {
            "value":          "<p>Content here</p>",
            "representation": "storage"
        }
    }
})

# Update page (must supply current version number)
current = get(f"{CONF_V1}/content/{page_id}", headers=HEADERS,
              params={"expand": "version"}).json()
version_num = current["version"]["number"]

put(f"{CONF_V1}/content/{page_id}", headers=HEADERS, json={
    "id":      page_id,
    "type":    "page",
    "title":   "Updated Title",
    "version": {"number": version_num + 1},
    "body": {
        "storage": {
            "value":          "<p>Updated content.</p>",
            "representation": "storage"
        }
    }
})

# Delete page
delete(f"{CONF_V1}/content/{page_id}", headers=HEADERS)

# Search pages (CQL)
get(f"{CONF_V1}/content/search", headers=HEADERS,
    params={"cql": 'space="ENG" AND title~"Design" AND type=page',
            "limit": 25}).json()
```

### Spaces

```python
get(f"{CONF_V1}/space", headers=HEADERS, params={"limit": 50}).json()
get(f"{CONF_V1}/space/ENG", headers=HEADERS).json()
```

### Attachments

```python
# Upload attachment to page
with open("diagram.png", "rb") as f:
    post(
        f"{CONF_V1}/content/{page_id}/child/attachment",
        headers={**HEADERS, "X-Atlassian-Token": "no-check", "Content-Type": None},
        files={"file": ("diagram.png", f, "image/png")}
    )

# List attachments
get(f"{CONF_V1}/content/{page_id}/child/attachment", headers=HEADERS).json()
```

### Comments

```python
post(f"{CONF_V1}/content/{page_id}/child/comment", headers=HEADERS, json={
    "type":  "comment",
    "body": {
        "storage": {
            "value": "<p>Nice work!</p>",
            "representation": "storage"
        }
    }
})
```

---

## 8. Error Handling & Retry Strategy

```python
import time
from httpx import request
from httpx import TimeoutException

class AtlassianAPIError(Exception):
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")

def api_call(method: str, url: str, headers: dict, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            r = request(method, url, headers=headers, timeout=30, **kwargs)
        except TimeoutException:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise

        if r.status_code == 429:                        # rate limited
            retry_after = int(r.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            continue

        if r.status_code in (500, 502, 503, 504):      # transient server error
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue

        if r.status_code == 401:
            raise AtlassianAPIError(401, "Credentials invalid or session expired.")

        if r.status_code == 403:
            raise AtlassianAPIError(403, f"Permission denied: {r.text}")

        if r.status_code == 404:
            raise AtlassianAPIError(404, f"Resource not found: {url}")

        if not r.is_success:
            raise AtlassianAPIError(r.status_code, r.text)

        # Return empty dict for 204 No Content
        return r.json() if r.content else {}

    raise AtlassianAPIError(0, "Exceeded retry limit")
```

---

## 9. Common Workflow Recipes

### Recipe A — Triage: Assign all unassigned Critical bugs in a project

```python
from httpx import put

issues = jira_search_all('project=PROJ AND priority=Critical AND assignee is EMPTY AND status!="Done"')
triager_id = jira_get("/user/search", query="triager@acme.com")[0]["accountId"]
for issue in issues:
    put(f"{BASE}/rest/api/3/issue/{issue['key']}", headers=HEADERS,
              json={"fields": {"assignee": {"accountId": triager_id}}})
    print(f"Assigned {issue['key']}")
```

### Recipe B — Sprint report: Collect velocity data

```python
board_id = 42
sprints = jira_get(f"/board/{board_id}/sprint", state="closed")["values"]
for sprint in sprints[-5:]:  # last 5 sprints
    issues = jira_get(f"/board/{board_id}/sprint/{sprint['id']}/issue",
                      maxResults=200, fields="story_points,status")
    completed = [i for i in issues["issues"] if i["fields"]["status"]["name"] == "Done"]
    print(f"{sprint['name']}: {len(completed)}/{len(issues['issues'])} done")
```

### Recipe C — Confluence docs sync: Mirror a folder of Markdown files to a space

```python
import re
from pathlib import Path
from httpx import get, put, post

def md_to_storage(md_text: str) -> str:
    """Minimal Markdown → Confluence Storage XML. Use a proper converter for production."""
    html = md_text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    html = re.sub(r"^# (.+)$",  r"<h1>\1</h1>",  html, flags=re.M)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>",  html, flags=re.M)
    html = re.sub(r"\n", "<br/>", html)
    return html

for md_file in Path("docs/").glob("*.md"):
    title   = md_file.stem.replace("-", " ").title()
    storage = md_to_storage(md_file.read_text())
    # Check if page exists
    results = get(f"{CONF_V1}/content", headers=HEADERS,
                  params={"spaceKey": "ENG", "title": title}).json()
    if results["results"]:
        page_id = results["results"][0]["id"]
        version = results["results"][0]["version"]["number"]
        put(f"{CONF_V1}/content/{page_id}", headers=HEADERS, json={
            "id": page_id, "type": "page", "title": title,
            "version": {"number": version + 1},
            "body": {"storage": {"value": storage, "representation": "storage"}}
        })
        print(f"Updated: {title}")
    else:
        post(f"{CONF_V1}/content", headers=HEADERS, json={
            "type": "page", "title": title, "space": {"key": "ENG"},
            "body": {"storage": {"value": storage, "representation": "storage"}}
        })
        print(f"Created: {title}")
```

---

## 10. Environment Variable Conventions

Store credentials outside code. Secrets file: `~/.atlassian-skill/.env` (not in the project dir). Load with `load_dotenv(Path.home() / ".atlassian-skill" / ".env")` — add `python-dotenv` to the script's PEP 723 deps block.

| Variable                  | Purpose                                                                        |
|---------------------------|--------------------------------------------------------------------------------|
| `ATLASSIAN_BASE_URL`      | Root URL of instance (no trailing slash)                                       |
| `ATLASSIAN_EMAIL`         | User email (Cloud + API token auth)                                            |
| `ATLASSIAN_API_TOKEN`     | API token (Cloud)                                                              |
| `ATLASSIAN_PAT`           | Personal Access Token (Data Center)                                            |
| `ATLASSIAN_CLIENT_ID`     | OAuth 2.0 app client ID                                                        |
| `ATLASSIAN_CLIENT_SECRET` | OAuth 2.0 app client secret                                                    |
| `ATLASSIAN_SESSION_FILE`  | Override session file path (bypasses `session_path()` naming — for manual use) |

---

## 11. Key API Reference Quick-Links

| Resource                 | Cloud Docs                                                                                   |
|--------------------------|----------------------------------------------------------------------------------------------|
| Jira REST v3             | `https://developer.atlassian.com/cloud/jira/platform/rest/v3/`                               |
| Jira Agile / Board       | `https://developer.atlassian.com/cloud/jira/software/rest/`                                  |
| Confluence v2            | `https://developer.atlassian.com/cloud/confluence/rest/v2/`                                  |
| Confluence v1            | `https://developer.atlassian.com/cloud/confluence/rest/v1/`                                  |
| OAuth 2.0 Scopes         | `https://developer.atlassian.com/cloud/jira/platform/scopes-for-oauth-2-3LO-and-forge-apps/` |
| Atlassian API Token Mgmt | `https://id.atlassian.com/manage-profile/security/api-tokens`                                |

---

## 12. Security Notes

- All sensitive files live in `~/.atlassian-skill/` (`mode=0o700`). Never write tokens, sessions, or scripts to the project directory or any version-controlled path. Treat it like `~/.ssh/`.
- Session files live in `~/.atlassian-skill/sessions/`, named `<team-slug>.json` (Cloud) or `<team-slug>-jira.json` / `<team-slug>-confluence.json` (Data Center). Each file contains full authentication material — treat them like passwords.
- `config.json` is user-managed — the agent creates it only when absent, never overwrites it.
- Lock files (`sessions/<slug>.lock`) persist only during an active capture. Delete any stale lock manually if a prior browser was abandoned.
- API tokens have full user scope — prefer OAuth 2.0 with minimum required scopes for automated integrations.
- HTTPS is mandatory. Always handle `429` with `Retry-After` backoff (see §9).
