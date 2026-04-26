# `grammaire`

`grammaire` is the Old French word for grammar, a curated collection of arcane knowledge that practitioners (agents)
consult to perform powerful actions.

To use the skills provided in this repo, clone this repository first.

```shell
git clone https://github.com/freneticdisc/grammaire.git
```

## 🕵️ Open Agent

```shell
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills" ~/.agents/skills/grammaire
```

## 🧠 Claude Code

```shell
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills" ~/.claude/skills/grammaire
```

## 🤖 Cline

```shell
mkdir -p ~/.cline/skills
ln -s "$(pwd)/skills" ~/.cline/skills/
```

## 🤖 Codex

```shell
mkdir -p ~/.codex/skills
ln -s "$(pwd)/skills" ~/.codex/skills/grammaire
```

## 🔐 Permissions and approvals

The Agent Skills spec defines how skills are structured and triggered, but approval/sandbox behavior is controlled by
each client runtime.

Use allow rules for these terminal command prefixes (platform-agnostic):

- `git remote -v`
- `git rev-parse`
- `jq -r ...`
- `oci --auth security_token --profile ... raw-request`
- `oci session authenticate`
- `oci session refresh`
- `ssh operator-access-token.svc.ad1.r2 generate --mode jwt`
- `uv run .../atlassian-browser-authentication/scripts/browser.py`
- `uvx oh-my-releases`
- `uvx pariksha`

Regex is not portable across these clients. Use explicit prefix/glob patterns instead:

- Codex: token-prefix rules (`prefix_rule(...)`)
- Claude Code: `Bash(...)` glob patterns (not full regex)
- Oh-My-OpenCode: command glob patterns under `permission`

> ⚠️ **Security note**: avoid allow rules for `sudo`, shell-wide allow-all patterns (for example `zsh`, `bash`,
> `Bash(*)`, or `"*": "allow"`), or destructive command families (`rm`, `chmod`, `chown`, `mkfs`, `dd`, `diskutil`).
> Over-broad rules can let an agent modify or delete files, install software, exfiltrate secrets, or execute
> privileged system changes without review.

### 🤖 Codex

Add rules in `~/.codex/rules/default.rules`:

```text
prefix_rule(pattern=["git", "remote", "-v"], decision="allow")
prefix_rule(pattern=["git", "rev-parse"], decision="allow")
prefix_rule(pattern=["jq"], decision="allow")
prefix_rule(pattern=["oci", "--auth", "security_token"], decision="allow")
prefix_rule(pattern=["oci", "--version"], decision="allow")
prefix_rule(pattern=["oci", "session", "refresh"], decision="allow")
prefix_rule(pattern=["oci", "session", "authenticate"], decision="allow")
prefix_rule(pattern=["ossh"], decision="allow")
prefix_rule(pattern=["ssh", "operator-access-token.svc.ad1.r2"], decision="allow")
prefix_rule(pattern=["uv", "run"], decision="allow")
prefix_rule(pattern=["uvx"], decision="allow")
```

### 🧠 Claude Code

Add `permissions.allow` in one of `~/.claude/settings.json`, `.claude/settings.json`, or `.claude/settings.local.json`.
The `Bash(...)` matcher name represents terminal commands across macOS/Linux/Windows.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git remote -v)",
      "Bash(git rev-parse --abbrev-ref HEAD)",
      "Bash(jq *)",
      "Bash(oci --auth security_token --profile * raw-request *)",
      "Bash(oci --version)",
      "Bash(oci session authenticate *)",
      "Bash(oci session refresh *)",
      "Bash(ossh *)",
      "Bash(ssh operator-access-token.svc.ad1.r2 generate --mode jwt)",
      "Bash(uv run *)",
      "Bash(uvx *)"
    ]
  }
}
```

### 🤖 OpenCode

Add rules in `~/.config/opencode/opencode.json` or repo `opencode.json`. If your runtime uses a different terminal tool
key, mirror the same command patterns there.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": {
      "*": "ask",
      "git remote -v": "allow",
      "git rev-parse *": "allow",
      "jq *": "allow",
      "oci session refresh *": "allow",
      "oci session authenticate *": "allow",
      "oci --auth security_token --profile * raw-request *": "allow",
      "oci --version": "allow",
      "ossh *": "allow",
      "ssh operator-access-token.svc.ad1.r2 generate --mode jwt": "allow",
      "uv run *": "allow",
      "uvx *": "allow"
    }
  }
}
```
