---
title: "Agent Shield"
description: "One place for the pages that protect AI coding and desktop agents, with an overview of hooked agents, open agent findings and blocked guardrail calls"
audience: pro
weight: 4
---

**Agent Shield** gathers the DefectDojo Pro pages that protect AI coding and desktop agents into one section of the sidebar, and adds an overview page that sums them up.

> Agent Shield is in beta and off by default. Turn it on with the **Agent Shield** flag on the [Feature Flags page](/admin/feature_flags/pro__feature_flags/). It requires Locations.

## The Agent Shield Section

With the flag on, the sidebar gets an **Agent Shield** section with these entries:

| Entry | What it opens | Who sees it |
|---|---|---|
| **Overview** | The Agent Shield overview, described below. | Everyone. |
| **AI Inventory** | The [AI Inventory](/asset_modelling/locations/pro__ai_inventory/): the AI found in scanned repositories. | Needs **AI Inventory and Governance**. |
| **Agent Targets** | The AI Agents view of the Sensei hub, where agents are red-teamed. | Needs the Sensei View permission. Without a Sensei license the page shows the upgrade notice. |
| **Prompt Activity** | Every prompt and tool call the [AI Guardrails](/triage_findings/findings_workflows/pro__ai_guardrails/) checked. | Superusers, with **AI Inventory and Governance**. |
| **AI Guardrails** | The guardrail policies and collectors. | Superusers, with **AI Inventory and Governance**. |
| **AI Governance Policies** | The [AI Governance Policies](/triage_findings/findings_workflows/pro__ai_governance_policies/) that authorize AI components. | Needs **AI Inventory and Governance**. |

AI Inventory and Prompt Activity move out of **Attack Surface**, and AI Guardrails and AI Governance Policies move out of **Settings**, while the flag is on. The pages and their addresses do not change, so bookmarks keep working, and **All Settings** still lists the two settings pages. Turn the flag off and the sidebar is back to how it was.

## The Overview

The overview counts what protects the agents developers use:

- **Guardrail Collectors**: the collectors that are not revoked.
- **Agents Covered**: the agents those collectors deploy hooks for.
- **Scanned Hosts**: the laptops the agent scanner has reported, leaving out hosts of archived assets.
- **Calls Blocked in the Last 7 Days**: the prompts and tool calls a guardrail policy in Enforce mode blocked. Calls a policy in Monitor mode only flagged are not counted.

**Open Findings by Pillar** counts the active findings about agents:

| Pillar | Findings counted |
|---|---|
| **Posture** | Findings from the agent posture checks that run on each laptop scan. |
| **Test** | Findings from Sensei red teaming of agent targets. |
| **Govern** | Findings for AI components the AI Governance Policies do not authorize. |

Each count follows the permissions of the page it sums up. The finding counts include only findings the user may view. The guardrail counts and Scanned Hosts are shown to superusers only, and only while **AI Inventory and Governance** is on; anyone else sees **Not Available** with the reason. A count of zero means nothing was found, while **Not Available** means the count cannot be shown.

When every count is visible to the user and nothing is hooked, scanned or found yet, the overview says so, and offers a shortcut to set up AI Guardrails.

The lightbulb in the lower right corner of the overview offers a short tour of the page.
