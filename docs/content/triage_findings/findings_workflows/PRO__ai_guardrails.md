---
title: "AI Guardrails for AI Coding Agents"
description: "Check every prompt and tool call from Claude Code, OpenAI Codex, Cursor and GitHub Copilot CLI against a central policy: block personal data, redact secrets, stop risky commands, and review the activity"
audience: pro
weight: 5
---

**AI Guardrails** checks what AI coding agents send and run against a policy you control. It works with **Claude Code**, **OpenAI Codex**, **Cursor** and **GitHub Copilot CLI**. Each agent calls DefectDojo through its hooks at the same points: when a developer submits a prompt, before a tool runs, and after a tool returns. DefectDojo answers each call with what the agent should do, in the agent's own format, and records it in **Prompt Activity**.

One policy covers every agent. The examples below use Claude Code; [Other Agents](#other-agents-openai-codex-cursor-and-github-copilot-cli) lists what each of the others can and cannot do.

A policy can:

- **Block a prompt** that contains personal data, such as a U.S. Social Security number or a payment card number. Claude Code never sends the prompt to the model, and the developer sees why.
- **Redact secrets** from file contents and command output before Claude sees them. The model still gets the file, but each key is replaced with a marker such as `[REDACTED:github_token]`.
- **Stop a command** before it runs, such as a `git push --force` that would overwrite a shared branch, or ask the developer to confirm it.
- **Log** a match without stepping in, so you can see how often something happens.

The hooks are deployed through each agent's managed configuration, which developers can't override from their own settings.

> AI Guardrails is part of the **AI Inventory and Governance** feature (beta). Turn it on from the [Feature Flags page](/admin/feature_flags/pro__feature_flags/). Only superusers can see or change guardrails and Prompt Activity.

## How It Fits Together

| | What it is |
|---|---|
| **Policy** | A named set of rules, in **Enforce** or **Monitor** mode. |
| **Rule** | What to look for, where to look, and what to do on a match. |
| **Collector** | A deployment: the hooks of one or more agents plus a token that connect a group of machines to one policy. |
| **Prompt Activity** | One row for each prompt and tool call a collector checked, with its agent, status, user and the rules it matched. |

## Start With the Baseline Policy

Open **Settings > AI Guardrails** and select **Create Starter Policy**. This creates **Claude Code Baseline** in monitor mode, with four rules:

| Rule | Looks at | Action |
|---|---|---|
| Personal data in prompts | Prompts: Social Security numbers and payment card numbers | Block |
| Secrets in prompts | Prompts: provider keys, tokens, private keys and passwords | Block |
| Secrets in files and output | File contents and tool output: the same secret detectors | Redact |
| Force push | Shell commands: `git push --force`, `-f`, `--force-with-lease` and `+refspec` | Block |

In **Monitor** mode, every prompt and tool call goes through, and Prompt Activity shows what the rules would have done. When the activity looks right, edit the policy and set it to **Enforce**.

## Rules

Each rule has three parts.

**What to look for.** Either **built-in detectors** or a **custom pattern**.

- Personal data: U.S. Social Security number, payment card number (Luhn-checked), email address.
- Secrets: private keys; AWS access and secret keys; GitHub, GitLab and Slack tokens; Anthropic, OpenAI and Google API keys; Stripe keys; JSON Web Tokens; passwords in connection strings; and secrets assigned to a variable (`API_KEY=...` in a `.env` file, YAML or JSON). Placeholders such as `${DB_PASSWORD}` and `changeme` are ignored.
- A custom pattern is a regular expression, for example `\bterraform\s+destroy\b`. Each search is time-limited, so a slow pattern can't hold up a developer.

**Where to look.**

| Target | What is checked |
|---|---|
| Prompts | The text a developer submits |
| Shell commands | The command of a `Bash` or `PowerShell` tool call |
| Other tool input | The input of every other tool call: file writes and edits, web fetches, MCP tools |
| File contents and tool output | What a tool returns before Claude sees it: files Claude reads, command output, search results, MCP results |

**What to do on a match.** The actions available depend on the target:

| Target | Block | Redact | Ask the developer | Log only |
|---|---|---|---|---|
| Prompts | ✓ | | | ✓ |
| Shell commands, other tool input | ✓ | | ✓ | ✓ |
| File contents and tool output | ✓ | ✓ | | ✓ |

Claude Code can stop a prompt but can't rewrite it, so prompts can only be blocked or logged. Blocking output withholds each value that matched and tells Claude why. When several rules match one call, the strongest action wins: block, then ask, then redact, then log.

A rule can carry its own **message**, shown to the developer (for a blocked prompt or an ask) or to Claude (for a blocked tool call). Use **Try It** in the rule form to test a rule against sample text before you save it.

## Deploy a Collector

1. In **Settings > AI Guardrails > Collectors**, select **New Collector**, name it (for example, *Engineering laptops*), choose its policy, and choose its **Agents**. One collector, and one token, can serve every agent on the same machines.
2. DefectDojo shows the collector's token **once**, together with the managed configuration for each agent, built from it, on one tab per agent. Copy the files now. If you lose the token, rotate it to get new files.
3. Choose the deployment options:
   - **Block Prompts and Tool Calls While DefectDojo Is Unreachable** sets `"onFailure": "block"` on every Claude Code hook (Claude Code 2.1.295 or later), and makes the other agents' forwarder block when DefectDojo doesn't answer. Without it, a call goes through when DefectDojo doesn't answer.
   - **Turn Off Hooks Developers and Projects Add** sets `allowManagedHooksOnly` for Claude Code and `allow_managed_hooks_only` for OpenAI Codex, so only the managed hooks run. Cursor and GitHub Copilot CLI have no such setting.
4. For Claude Code, deploy `managed-settings.json` to every developer machine with your device management tooling:

| OS | Path |
|---|---|
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Linux and WSL | `/etc/claude-code/managed-settings.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-settings.json` |

You can also deliver the same settings through an MDM profile, the Windows registry, or Claude Code's server-managed settings. See [Claude Code settings](https://code.claude.com/docs/en/settings) for the options and their precedence.

The file defines three HTTP hooks (`UserPromptSubmit`, `PreToolUse` and `PostToolUse`) that post to `/api/v2/ai_guardrails/claude_code/hook/` on your DefectDojo instance. Developer machines need to reach that URL. Each hook sends the developer's account name (from `USER` or `USERNAME`) and machine name (from `HOSTNAME` or `COMPUTERNAME`), which Prompt Activity shows.

The token can only submit hook calls for its collector: it can't read or change anything else in DefectDojo. Developers can read it in the settings file, so treat it as an identifier, not a secret. **Revoke** a collector to stop its token working, or **Rotate** it to issue a new token and file. Rotating stops the old token at once, so deploy the new file at the same time.

## Other Agents: OpenAI Codex, Cursor and GitHub Copilot CLI

These agents run their hooks as local commands. Their managed configuration runs a small **forwarder** that sends each hook call to DefectDojo and hands the answer back: a POSIX shell script using `curl` on macOS and Linux, and a PowerShell script on Windows. Each agent's tab in the collector setup lists every file and where it goes:

| File | macOS and Linux | Windows |
|---|---|---|
| OpenAI Codex requirements | `/etc/codex/requirements.toml` | `C:\ProgramData\OpenAI\Codex\requirements.toml` |
| Cursor enterprise hooks | `/Library/Application Support/Cursor/hooks.json` (macOS), `/etc/cursor/hooks.json` (Linux) | `C:\ProgramData\Cursor\hooks.json` |
| GitHub Copilot CLI policy | `/etc/github-copilot/policy.d/defectdojo-guardrails.json` | `C:\ProgramData\GitHub\Copilot\policy.d\defectdojo-guardrails.json` |
| Forwarder | `/opt/defectdojo/guardrails/hook.sh` | `C:\ProgramData\DefectDojo\Guardrails\hook.ps1` |
| Token file | `/opt/defectdojo/guardrails/token` | `C:\ProgramData\DefectDojo\Guardrails\token` |

The forwarder and the token file are shared by every agent on a machine. The token is never written into an agent's configuration: the forwarder reads it from the token file, or from the `DEFECTDOJO_GUARDRAILS_TOKEN` environment variable when it is set. The token file must be readable by every developer account and writable only by administrators. On macOS and Linux the Copilot policy file must be owned by root and not writable by group or others.

Each agent supports a different set of hooks, so a rule does what the agent allows:

| | OpenAI Codex | Cursor | GitHub Copilot CLI |
|---|---|---|---|
| Hooks used | `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse` | `beforeSubmitPrompt`, `beforeShellExecution`, `beforeMCPExecution`, `beforeReadFile`, `afterFileEdit`, `afterMCPExecution` | `userPromptSubmitted`, `preToolUse`, `postToolUse` |
| Block a prompt | Yes | Yes | No: Copilot ignores a prompt hook's answer, so the prompt is recorded as **Flagged** |
| Block a tool call | Yes | Shell commands and MCP tools | Yes |
| Ask the developer | No: an ask blocks the call, with a message saying a person must confirm it. When Codex itself is about to ask for approval, the developer is asked | Shell commands and MCP tools | Yes (denied in autopilot mode, where nobody can answer) |
| Redact tool output | Yes: the output is replaced with the masked copy | No: a read with a secret is denied | Yes |
| File edits and MCP results | Checked with tool input and output | Recorded when a rule matches; they already happened | Checked with tool input and output |

Prompt Activity shows what the agent actually did with a call. A Copilot prompt that a blocking rule matched is **Flagged**, not **Blocked**, and a Codex call a rule asked about is **Blocked**.

## Prompt Activity

Open **Prompt Activity** to see every prompt and tool call the collectors checked, newest first. Each row shows the time, the status, the developer, the agent, the rules it was flagged for, the hook (prompt, tool call or tool output), the tool, an excerpt and the machine. Filter by status, agent, user, host, tool or hook, and select a row to see every rule that matched, with each detector and its count.

| Status | Meaning |
|---|---|
| Allowed | No rule matched. |
| Blocked | A prompt was stopped, a tool call was denied, or output was withheld. |
| Redacted | Matches were masked in a tool's output before Claude saw it. |
| Asked | The developer was asked to confirm the tool call. |
| Flagged | A log-only rule matched, the policy is in monitor mode, or the agent could not carry out what the rule asked. Monitored rows carry a **Monitor** tag. |

Tool output is recorded only when a rule matched it, so a tool call usually appears once.

### What Is Stored

DefectDojo never stores file contents or tool output. An event keeps the start of the prompt or command (or the file path or URL of a tool call), the names of the rules and detectors that fired, and how often each fired.

The excerpt is masked before it is stored. Anything a built-in detector matched is replaced with a marker, and so is any secret the built-in detectors recognize, even where no rule looks for one. A custom pattern's match is masked in prompts and tool output, but stays readable in shell commands and other tool input, so a blocked `git push --force` shows what was stopped. To store no excerpt at all, turn off **Record Excerpts** on the policy. Events then keep only who, when, which tool and what was decided.

A blocked prompt never reaches the model, but the agent may still keep it in the developer's local prompt history and transcript.

## Using the API

Everything in this page is available to a superuser's API token under `/api/v2/ai_guardrails/`:

```http
GET  /api/v2/ai_guardrails/policies/
POST /api/v2/ai_guardrails/policies/starter/
GET  /api/v2/ai_guardrails/rules/?policy=3
POST /api/v2/ai_guardrails/rules/test/
POST /api/v2/ai_guardrails/collectors/
POST /api/v2/ai_guardrails/collectors/7/rotate/
GET  /api/v2/ai_guardrails/events/?status=blocked&agent=codex,cursor&actor=jdoe
```

Creating a collector, or rotating its token, returns `token`, `hook_url`, `managed_settings` (Claude Code's file) and `agent_configs`, which holds every file for each of the collector's agents. This is the only time the token is returned. A collector's agents are set with `agents`, for example `["claude_code", "codex"]`.
