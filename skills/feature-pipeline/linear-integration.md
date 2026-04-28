# Linear Integration Guide

> **Status**: Optional reference. Not a pipeline component.

This document explains how to integrate `/feature-pipeline` with Linear issue tracking for feature lifecycle management.

## Overview

Linear can serve as the external trigger and audit trail for feature pipeline execution:
- Linear issue creation → trigger `feat-plan` routine
- Status updates in plan.md → reflected in Linear issue status
- Ship completion → Linear issue marked as "Done"

## Integration Points

### 1. Issue → Plan Mapping

When a new feature is approved in Linear (e.g., moved to "Ready" status), automatically invoke:

```bash
/feature-pipeline "Feature from Linear AILS-XX: <issue-title>"
```

The plan.md should include Linear metadata in frontmatter:

```yaml
---
feature: <slug>
status: draft
retry_count: 0
created_at: <ISO-8601 datetime>
linear_issue: AILS-XX
linear_url: https://linear.app/onepersoncompany/issue/AILS-XX/...
---
```

### 2. Status Synchronization

Map pipeline statuses to Linear states:

| plan.md status | Linear Status |
|----------------|---------------|
| `draft` | In Progress |
| `pending_approval` | In Review |
| `approved` | Ready for Dev |
| `designing` | In Progress |
| `implementing` | In Progress |
| `verifying` | In Review |
| `verified` | Ready to Ship |
| `done` | Done |
| `failed` / `aborted` | Canceled |

### 3. Automatic Updates (Optional Webhook)

If using Linear API webhooks, create a sync routine:

```python
# Pseudocode for sync routine
def sync_to_linear(plan_path):
    plan = read_frontmatter(plan_path)
    linear_issue = plan.get('linear_issue')
    
    if not linear_issue:
        return
    
    status_map = {...}  # from table above
    linear_status = status_map[plan['status']]
    
    linear_api.update_issue(
        issue_id=linear_issue,
        state=linear_status,
        description=f"Pipeline status: {plan['status']}\n"
                   f"Retry count: {plan['retry_count']}\n"
                   f"Last updated: {now()}"
    )
```

### 4. Ship Gate → Linear Comment

When Ship gate is triggered, post a comment to Linear issue:

```
✅ Verify completed. Ready to ship.
PR: <pr_url>
Pipeline: docs/plans/<slug>.md

cc @<owner> - Please approve ship.
```

After successful ship, update Linear with merge details:

```
🚀 Shipped to production
PR merged: <merged_commit>
Deploy status: Success
Canary health: Green
```

## Non-Goals

This integration does **NOT**:
- Replace plan.md as the single source of truth
- Automatically trigger ship (human approval still required)
- Sync task-level progress (only milestone states)
- Replace the existing `/feature-pipeline` orchestration

## Setup Instructions (if implementing)

1. **Linear API Token**: Store in `.env` as `LINEAR_API_KEY`
2. **Webhook Endpoint**: Set up a webhook listener for Linear issue status changes
3. **Sync Routine**: Create a cron job that:
   - Scans `docs/plans/*.md` every 10 minutes
   - Compares last_synced timestamp
   - Pushes status updates to Linear API
4. **Branch Naming**: Ensure feature branches include Linear issue ID (e.g., `feat/AILS-29-feature-pipeline`)

## Example Workflow

1. User creates Linear issue "AILS-29: Implement feature X"
2. User moves issue to "Ready" in Linear
3. Dev invokes: `/feature-pipeline "AILS-29: feature X description"`
4. Plan created with `linear_issue: AILS-29` in frontmatter
5. As pipeline progresses, sync routine updates Linear status
6. At Ship gate, user clicks "Ship" in chat AND marks Linear issue as "Ship approved"
7. After successful merge, Linear issue auto-transitions to "Done"

## Alternative: Manual Sync

If not implementing webhooks, use manual commands:

```bash
# Update Linear from plan
/sync-to-linear docs/plans/2026-04-27-feature-x.md

# Pull Linear status
/pull-from-linear AILS-29
```

## See Also

- [SKILL.md](SKILL.md) — Main pipeline orchestration
- [scheme-c-schedule.md](scheme-c-schedule.md) — Schedule routine architecture
- Linear API docs: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
