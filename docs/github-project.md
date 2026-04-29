# GitHub issue/project setup

This repository uses GitHub Issues as the source of truth for task tracking.

## Recommended Project

Create a GitHub Project named **deepagents-video-maker** and add this repository as the linked source.

Recommended fields:

| Field | Type | Values |
| --- | --- | --- |
| Status | Single select | Backlog, Ready, In progress, In review, Done |
| Priority | Single select | High, Normal, Low |
| Area | Single select | Producer, Tools, Skills, Web UI, Testing, Docs, CI |
| Milestone | Iteration or text | M1, M2, M3 |

Recommended views:

1. **Board by Status** — group by `Status`.
2. **Roadmap by Milestone** — group by `Milestone`.
3. **By Area** — group by `Area`.

## Initial milestones

- **M1: Stabilize research → script** — make the current runnable pipeline reliable.
- **M2: Web UI and HITL workflow** — make the LangGraph-backed UI usable for real sessions.
- **M3: Assets/rendering integration boundary** — define and prepare integration with the future standalone rendering toolchain.

## Labels

The canonical label set is stored in `.github/labels.yml`.

After GitHub CLI auth is fixed, sync labels with:

```bash
gh label create "type: bug" --color d73a4a --description "Something is broken or regressed." --force
gh label create "type: feature" --color a2eeef --description "New behavior or capability." --force
gh label create "type: task" --color cfd3d7 --description "Implementation, cleanup, or tracking work." --force
gh label create "type: docs" --color 0075ca --description "Documentation-only work." --force
gh label create "status: triage" --color fbca04 --description "Needs prioritization and scope confirmation." --force
gh label create "status: ready" --color 0e8a16 --description "Ready for implementation." --force
gh label create "status: blocked" --color b60205 --description "Blocked by dependency, decision, or credentials." --force
gh label create "priority: high" --color b60205 --description "Important or urgent." --force
gh label create "priority: normal" --color fbca04 --description "Default priority." --force
gh label create "priority: low" --color c5def5 --description "Low urgency." --force
gh label create "area: producer" --color 5319e7 --description "DeepAgents Producer/controller orchestration." --force
gh label create "area: tools" --color 1d76db --description "Typed tools, LangChain tools, artifacts, ratify gates." --force
gh label create "area: skills" --color 0052cc --description "skills/video-maker and .deepagents skill wrappers." --force
gh label create "area: web-ui" --color f9d0c4 --description "Next.js chat UI and LangGraph SDK integration." --force
gh label create "area: testing" --color bfdadc --description "Tests, smoke checks, and CI validation." --force
gh label create "area: docs" --color 0075ca --description "README, AGENTS, design docs, and project docs." --force
gh label create "area: ci" --color 0e8a16 --description "GitHub Actions and automation." --force
```

## Issue assignment rules

- Default assignee: `AILatentspace1`.
- Every issue should have:
  - one `type:*` label,
  - one or more `area:*` labels,
  - one `priority:*` label,
  - a milestone when it belongs to M1/M2/M3.
- Keep acceptance criteria explicit and command-based.

## Project automation

Recommended GitHub Project workflows:

- New issues from this repo → `Status = Backlog`.
- Issues with label `status: ready` → `Status = Ready`.
- Pull request linked → `Status = In review`.
- Issue closed → `Status = Done`.
