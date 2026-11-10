---
title: "Laptop Agent Scans and Agent Posture"
description: "Inventory the AI agents, MCP servers, plugins, extensions and skills on developer machines, and check how each agent is configured"
weight: 10
audience: pro
---

The **agent scanner** (`shogun-agentscan`) reads how the AI coding and desktop agents on a machine are set up: Claude Code, Claude Desktop, OpenAI Codex, Cursor, VS Code with GitHub Copilot, Copilot CLI, Gemini CLI, Windsurf and Kiro. It posts one document per run to DefectDojo, and DefectDojo turns it into three things on the Asset the scanner's token belongs to:

- The machine becomes a **host Location** on the Asset.
- The agents, MCP servers, plugins, extensions and skills it found join the Asset's [AI Inventory](../pro__ai_inventory/), so [AI Governance Policies](/triage_findings/findings_workflows/pro__ai_governance_policies/) decide on them exactly as they do for components found in a repository.
- The **agent posture benchmark** checks each agent's configuration, and every check the machine fails is a Finding in an **Agent Posture** engagement on the Asset, attached to the host.

> Laptop agent scans are part of the **AI Inventory and Governance** feature (beta). Turn it on from the [Feature Flags page](/admin/feature_flags/pro__feature_flags/). While the flag is off, uploads are refused. Only superusers can manage scanner tokens and see scanned hosts.

## Set Up a Scanner Token

A scanner token connects a group of machines to one Asset, for example an Asset named **Engineering Laptops**. Create one with the API as a superuser:

```
POST /api/v2/agent_scan/tokens/
{"name": "Engineering laptops", "product": 42}
```

The response contains the token (it starts with `ddas_`), the upload URL and the command to run. **The token is shown only once.** DefectDojo stores only its SHA-256 digest. The token can post scans for its Asset and do nothing else, so it is safe to place on every machine that runs the scanner.

- `POST /api/v2/agent_scan/tokens/{id}/rotate/` replaces the token. The old one stops working at once.
- `POST /api/v2/agent_scan/tokens/{id}/revoke/` stops the token working. Scans posted with it are refused.

A token stays bound to the Asset it was created for.

## Run the Scanner

Save the token in a file that only the account running the scanner can read, then run:

```
shogun-agentscan --url https://defectdojo.example.com/api/v2/agent_scan/scans/ --token-file /etc/defectdojo/agentscan-token
```

Run it as an administrator with `--all-users` to scan every home directory on the machine. Schedule it with your MDM tool, cron or Task Scheduler to keep the inventory and posture current. The scanner only reads configuration and changes nothing.

Each run has its own scan id. Sending the same scan twice changes nothing, and a scan older than the host's latest one is recorded but not applied, so a retried upload never rolls a host back.

## What the Scanner Sends

The scanner reports what is configured, never the secrets the configuration holds. It does not read MCP server environment or header values, OAuth client secrets, extension settings or credential helper commands. Values that look like credentials in command lines, URLs and settings are replaced with `[REDACTED]` on the machine before anything is sent. When an MCP server holds a secret literally, the scanner reports where (for example the `env` variable name), never the value.

DefectDojo keeps names, file paths and setting keys from the scan. It never stores a command line or an argument, and it drops any value that looks like a credential.

## What Lands in the AI Inventory

| Found on the machine | Inventory kind | Recorded as |
|---|---|---|
| An agent that is installed, configured or running | Coding Assistants | `pkg:generic/ai-assistant/<agent>`, for example `claude-code` or `github-copilot` |
| An MCP server started with `npx`, `bunx`, `pnpm dlx`, `uvx` or `pipx run` | MCP Servers | The npm or PyPI package, with its version only when the command pins one |
| A remote MCP server | MCP Servers | `pkg:generic/mcp-server/<host>` |
| Any other MCP server | MCP Servers | `pkg:generic/mcp-server/<name it is configured under>` |
| A skill (a directory with a `SKILL.md`) | Agent Skills | `pkg:generic/ai-skill/<name>` |
| A Claude Code plugin | Agent Extensions | `pkg:generic/ai-plugin/<id>` |
| A Claude Desktop or Gemini CLI extension | Agent Extensions | `pkg:generic/ai-extension/<id>` |

These are the same Package URLs the repository scanner uses, so a policy such as "unauthorized: `pkg:npm/@modelcontextprotocol/server-filesystem*`" applies to repositories and laptops alike. A component stays in the Asset's inventory while any of its hosts reports it, and the inventory shows which hosts those are. Disabled MCP servers, extensions and plugins are left out.

## Agent Posture Checks

Most checks ask whether an administrator has enforced a setting through **managed configuration**: a system-wide file, an MDM profile or a Windows registry policy that developers can't override. A developer's own setting does not count as a control.

| Check | Agent | Fails when | Severity |
|---|---|---|---|
| Bypass permissions mode is not disabled | Claude Code | Managed settings don't set `permissions.disableBypassPermissionsMode` to `disable` | High |
| Starts in bypass permissions mode | Claude Code | A settings file makes `bypassPermissions` the default mode | High |
| No managed hooks | Claude Code | No hook is deployed through managed settings | Medium |
| Runs hooks that are not managed | Claude Code | `allowManagedHooksOnly` is not set in managed settings | Medium |
| Sandbox is not enforced | Claude Code | Managed settings don't turn on `sandbox.enabled` | Medium |
| Allows MCP servers that are not managed | Claude Code | `allowManagedMcpServersOnly` is not set in managed settings | Medium |
| Runs repository hooks or MCP servers without managed settings | Claude Code | A project's `.claude/settings.json` hooks or `.mcp.json` servers are in use and managed settings don't restrict them | Medium |
| Allows unsigned extensions | Claude Desktop | Policy neither requires signed extensions nor turns extensions off | High |
| Has an unsigned extension installed | Claude Desktop | An installed extension is unsigned or self-signed | High |
| Allows local MCP servers | Claude Desktop | Policy doesn't set `isLocalDevMcpEnabled` to false | Medium |
| Allows the danger-full-access sandbox mode | Codex | `requirements.toml` doesn't exclude `danger-full-access` | High |
| Allows the never approval policy | Codex | `requirements.toml` doesn't exclude `never` | High |
| Has no requirements.toml | Codex | No managed `requirements.toml` is deployed | Medium |
| Has no enterprise hooks | Cursor | No machine-wide `hooks.json` is deployed | Medium |
| Runs Copilot agent tools without approval | VS Code | `chat.tools.autoApprove` is on and the `ChatToolsAutoApprove` policy doesn't turn it off | High |
| Has no MCP server allowlist | VS Code | No policy limits which MCP servers Copilot may use | Medium |
| Has no managed hooks | Copilot CLI | No hook is deployed through Copilot CLI policy | Medium |
| YOLO mode is not disabled | Gemini CLI | System settings don't set `security.disableYoloMode` | High |
| Has no system settings | Gemini CLI | No system settings file is deployed | Low |
| MCP server launched from an unpinned package | Any | A package runner starts a server with no exact version or image digest (`npx -y pkg`, `@latest`, an image tag) | Medium |
| Remote MCP server over plain HTTP | Any | A server is reached over `http://` or `ws://` to another machine | Medium |
| MCP server configuration holds a secret | Any | A server entry holds a secret literally instead of referencing an environment variable | High |
| MCP server tools run without approval | Any | A server is trusted for every tool (`trust: true`, or `autoApprove: ["*"]`) | Medium |
| Agent running with approvals and sandbox turned off | Any | A running agent was started with `--dangerously-skip-permissions`, `--yolo` or `--dangerously-bypass-approvals-and-sandbox` | High |
| Agent version with a known vulnerability | Any | An installed agent is older than the version that fixes a published CVE | Up to Critical |

Each Finding names the host, the agents and what the check found, and its mitigation gives the fix for each agent: the managed setting to add and where the file lives on macOS, Linux and Windows. `GET /api/v2/agent_scan/checks/` lists every check with its fixes.

### How Posture Findings Change Over Time

- A check the host fails opens its Finding, or reopens it if a later scan had closed it.
- A check the host passes on a later scan closes its Finding. So does removing the agent.
- Some locations aren't documented by the vendor, or the scanner couldn't read them. When the answer depends on one of these, the check's result is **unknown**, and the Finding is left as it is.
- A Finding you mark as false positive, out of scope or risk accepted is never reopened or changed by a later scan.

## Hosts

`GET /api/v2/agent_scan/hosts/` lists every machine that has posted a scan, with its last scan time and the result of each check. Filter with `product`, `hostname`, `token` or `failed_check` (a check id, for example `?failed_check=mcp-literal-secret`). Deleting a host removes its components from the Asset's inventory (unless another host still has them) and closes its open posture Findings. A later scan from that machine adds it back.

## Related

- [AI Inventory](../pro__ai_inventory/)
- [AI Governance Policies](/triage_findings/findings_workflows/pro__ai_governance_policies/)
- [AI Guardrails for Claude Code](/triage_findings/findings_workflows/pro__ai_guardrails/)
