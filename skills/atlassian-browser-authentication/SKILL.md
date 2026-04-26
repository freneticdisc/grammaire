---
name: atlassian-browser-authentication
description: >
  Use when authenticating to Atlassian (Jira, Confluence) — opens a local browser for sign-in/MFA and saves a reusable
  Playwright auth state (session, cookies).
---

# Atlassian Browser Authentication

Use this when Atlassian API/browser work needs an authenticated session.

## Rules

- Use standalone commands only (no pipes/chaining/redirection/subshells).
- This flow is interactive: after the browser opens, wait for the user to complete login/MFA and do not continue until
  the command exits.
- The script returns only `{"state_file": "<path>"}` — page content is never passed back to the agent.
- Prefer reusable prefix approvals:
  - `["uv", "run", "$SKILL_DIR/scripts/browser.py"]`

## Inputs

- `URL` (required): Jira/Confluence URL.
- `FORCE` (optional, default `false`): re-authenticate even if cached state is fresh.

## Run

- Set `SKILL_DIR` to the absolute installed path of this skill.
- Run: `uv run "$SKILL_DIR/scripts/browser.py" "<URL>"`.
- If `FORCE=true`, run: `uv run "$SKILL_DIR/scripts/browser.py" "<URL>" true`.

Use absolute script paths so this works both from the repo and when the skill is installed under agent skills.

## Output

- JSON: `{"state_file":"<absolute-path>"}`.
