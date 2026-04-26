---
name: atlassian-browser-authentication
description: Open a local browser for Atlassian login and save reusable Playwright auth state.
---

# Atlassian Browser Authentication

Use this when Atlassian API/browser work needs an authenticated session.

## Rules

- Always run with escalation.
- Use standalone commands only (no pipes/chaining/redirection/subshells).
- This flow is interactive: after the browser opens, wait for the user to complete login/MFA and do not continue until
  the command exits.
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
