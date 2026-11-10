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

Open **Settings > AI Guardrails** and select **Create Starter Policy**. This creates **Claude Code Baseline** in monitor mode, with eight rules:

| Rule | Looks at | Action |
|---|---|---|
| Personal data in prompts | Prompts: Social Security numbers and payment card numbers | Block |
| Secrets in prompts | Prompts: provider keys, tokens, private keys and passwords | Block |
| Secrets in files and output | File contents and tool output: the same secret detectors | Redact |
| Force push | Shell commands: `git push --force`, `-f`, `--force-with-lease` and `+refspec` | Block |
| Agent permission checks switched off | Commands: flags that turn off an agent's own approvals or sandbox, such as `--dangerously-skip-permissions`, `--yolo` and `--allow-all-tools` | Log only |
| An agent starting another agent | Commands: `claude`, `codex`, `copilot`, `cursor-agent`, `gemini` and other agent command lines, and the `npx` packages that start them | Log only |
| Sensitive file access | Paths: the built-in sensitive files (see [Rules on the Call Itself](#rules-on-the-call-itself-tools-paths-and-commands)) | Log only |
| Download piped into a shell | Shell commands: `curl` or `wget` piped into a shell, and PowerShell running a download (`iwr ... \| iex`) | Log only |

In **Monitor** mode, every prompt and tool call goes through, and Prompt Activity shows what the rules would have done. When the activity looks right, edit the policy and set it to **Enforce**. The four log-only rules stay log-only in either mode: change a rule's action to block or ask once you know what it catches.

A policy can also **Block Settings Changes**: Claude Code then keeps a change to a user, project or local settings file (new permissions, hooks or MCP servers, for example) from taking effect in the running session. The file itself has already changed, so the next session loads it; to lock a setting for good, put it in the managed settings, which always apply. Every settings change is recorded in Prompt Activity either way. In monitor mode the change takes effect and is recorded as **Flagged**.

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

A rule applies to every agent unless you choose its **Agents**: a rule for OpenAI Codex only, for example, never matches a Claude Code call.

### Rules on the Call Itself: Tools, Paths and Commands

Three more kinds of rule read the tool call rather than a text. They check a call before it runs, have no target, and can block, ask or log.

| Kind | Matches | Example |
|---|---|---|
| **Tool or MCP server** | The tool's name, and for an MCP tool its server and tool name. Every list you fill in must match. | Tool names `mcp__github__*`, or MCP server `github` with MCP tool `delete_*` |
| **File path** | The files the call reads, writes, edits or searches (including Grep, Glob and notebook paths), and every argument of a shell command, redirections included (`> ~/.ssh/authorized_keys`). Turn on **Match Sensitive Files** to add the built-in set. | `.env*`, `~/.ssh/**`, `secrets/*.key` |
| **Command list** | Each command a shell command line runs. **Match These Commands** is a deny list; **Match Any Other Command** is an allow list, which matches every command not listed. | Deny `rm -rf *`, `git push`, `terraform destroy`; or allow `git status`, `ls`, `npm test` |

Patterns use `*` for any characters. In a path, `*` stays within one folder and `**` crosses folders, `~` is the developer's home directory on every operating system, and a relative pattern (or a bare file name in a command) is matched from the agent's working directory. Paths are compared regardless of case, with `\` read as `/`, `$HOME`, `${HOME}`, `$env:USERPROFILE` and `%USERPROFILE%` read as `~`, and `.`, `..` and repeated slashes resolved, so a file written another way is still the same file. A command pattern without `*` matches as leading words: `git push` matches `git push origin main`, but `git` does not match `gitk`. Command names ignore case and `.exe`, and PowerShell and cmd commands ignore case throughout. Tool names ignore case too, since agents spell the same tool differently (`Bash`, `bash`).

A command line is split into every command it runs before a command list checks it, so an allowed command cannot carry a denied one past the rule. The split follows `;`, `&&`, `||`, pipes, background `&`, new lines and line continuations; subshells and groups (`( )`, `{ }`) and the commands inside `if`, `while`, `for` and `case`; `$( )`, backticks and `<( )`; the script of `sh -c`, `bash -c`, a here-string (`bash <<< '...'`), `eval`, `env -S`, `cmd /c`, `pwsh -Command` and `pwsh -EncodedCommand`; the command `find -exec` runs; and wrappers such as `sudo`, `env`, `nohup`, `timeout`, `xargs` and `busybox` with their own short and long options, plus leading `NAME=value` assignments. A PowerShell tool's command line is read as PowerShell, where backslashes are path separators and a backtick escapes. A command that builds its name at run time (a variable holding `rm`, or a script file the agent writes first and then runs) can't be seen this way, and neither can a script piped into a shell (the shell itself is a command, so an allow list still catches it). Pair a command list with a file path rule, or an allow list, where that matters.

The built-in **sensitive files** are:

- Keys: `~/.ssh/**`, `id_rsa*`, `id_ed25519*`, `id_ecdsa*`, `*.pem`, `*.key`, `*.p12`, `*.pfx` and `~/.gnupg/**`.
- Cloud, cluster and tool credentials: `~/.aws/credentials`, `~/.aws/config`, `~/.config/gcloud/**`, `~/.azure/**`, `~/.kube/config`, `~/.docker/config.json`, `~/.vault-token`, `~/.terraform.d/credentials.tfrc.json`, `~/.git-credentials` and `~/.config/gh/hosts.yml`.
- Package registry tokens: `.npmrc`, `.pypirc`, `~/.cargo/credentials*`, `~/.gem/credentials` and `~/.netrc`.
- Environment files: `.env*`.
- Browser profiles (cookies and saved passwords) of Chrome, Chromium, Edge, Firefox and Safari, on macOS, Linux and Windows.

Use **Try It** with a tool name, a file path or a command line. For a command list it shows every command the line runs and which of them the rule caught.

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

The file defines six HTTP hooks that post to `/api/v2/ai_guardrails/claude_code/hook/` on your DefectDojo instance. Developer machines need to reach that URL. Each hook sends the developer's account name (from `USER` or `USERNAME`) and machine name (from `HOSTNAME` or `COMPUTERNAME`), which Prompt Activity shows.

| Hook | What DefectDojo does |
|---|---|
| `UserPromptSubmit` | Checks the prompt. |
| `PreToolUse` | Checks the tool call: its input, and the tool, path and command rules. |
| `PermissionRequest` | Checks a call Claude Code is about to ask the developer about, with the same rules. A request for a call `PreToolUse` already recorded adds no second row to Prompt Activity. |
| `PostToolUse` | Checks what the tool returned. |
| `ConfigChange` | Records a settings change, and blocks it when the policy blocks settings changes. |
| `InstructionsLoaded` | Records each instruction file (`CLAUDE.md` and its imports) a session loads, and runs the file path rules over its path. It can't stop the load, so a match is recorded as **Flagged**. |

A seventh hook, `SessionStart`, records each session with the model in use. Claude Code runs `SessionStart` hooks only as commands, so it runs the same forwarder the other agents use (see [Other Agents](#other-agents-openai-codex-cursor-and-github-copilot-cli)): deploy the forwarder and the token file from the Claude Code tab with `managed-settings.json`. On Windows the hook needs Git Bash, which Claude Code itself requires. Without the forwarder, every other hook still works, and sessions are simply not recorded.

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
| Tool, path and command rules | Shell commands, MCP tools, and the files an `apply_patch` edit touches | Shell commands, MCP tools and file reads (an ask on a file read denies it) | Every tool call, with the file path it names |

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

Tool output is recorded only when a rule matched it, so a tool call usually appears once. For Claude Code, every session start, settings change and instructions load is recorded too, so you can see which model each session used, which settings changed mid-session, and which instruction files were loaded. An event's detail shows the model and the agent version when the agent reported them.

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

A rule's `kind` is `detectors`, `pattern`, `tool`, `path` or `command`, and its `agents` limits it to some agents (empty is every agent). A tool rule sets `tool_names`, `mcp_servers` and `mcp_tools`; a path rule sets `paths` and `sensitive_paths`; a command rule sets `commands` and `command_mode` (`deny` or `allow`). A policy's `block_settings_changes` turns on **Block Settings Changes**. To try a rule without saving it:

```http
POST /api/v2/ai_guardrails/rules/test/
{"kind": "command", "commands": ["rm -rf *"], "command_mode": "deny", "text": "grep -r token src; rm -rf ~"}
```

The answer says whether the rule `matched`, lists the commands it caught in `matches`, and lists every command the line runs in `commands`. A tool rule takes `tool_name` and a path rule takes `path` in place of `text`.
