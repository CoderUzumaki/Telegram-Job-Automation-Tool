# Telegram Job Radar — Product Documentation

> **Architecture status:** FROZEN v3.1 — approved for development  
> **Last updated:** 2026-06-29

This folder is the single source of product context for humans and AI agents. Read this index first, then drill into the linked documents.

## Quick start for agents

1. Read [product-summary.md](./product-summary.md) — what we're building and why
2. Read [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md) — frozen decisions (do not contradict without explicit user approval)
3. Check [implementation-status.md](./implementation-status.md) — what's done vs pending
4. Follow [implementation-order.md](./implementation-order.md) — step gates (parser golden tests block UI)
5. Use [agent-guidelines.md](./agent-guidelines.md) — ownership boundaries, file layout, conventions

## Document map

| Document | Purpose |
|----------|---------|
| [product-summary.md](./product-summary.md) | Elevator pitch, problem, success criteria, MVP scope |
| [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md) | Full frozen architecture spec |
| [tech-stack-and-justification.md](./tech-stack-and-justification.md) | Stack choices and rejected alternatives |
| [database-schema.md](./database-schema.md) | SQLite tables, indexes, extraction model |
| [state-machines.md](./state-machines.md) | Processing, review, and export state dimensions |
| [api-contract.md](./api-contract.md) | REST + HTMX routes |
| [design-system.md](./design-system.md) | UI patterns, components, visual direction for HTMX |
| [implementation-order.md](./implementation-order.md) | Build sequence with ship gates |
| [implementation-status.md](./implementation-status.md) | Living checklist — update as work completes |
| [prompts/ui-design-tool-prompt.md](./prompts/ui-design-tool-prompt.md) | Copy-paste prompt for Stitch / v0 / Lovable |

## Pre-development blockers

These must be resolved before certain steps:

| Blocker | Blocks |
|---------|--------|
| 5–10 sample Telegram job posts | Step 3 — golden parser tests |
| Job profile seed JSON | Step 4 — LLM scoring calibration |
| Telegram API credentials | Step 2 — ingest |
| Google Sheet column layout decision | Step 6 — export |

## Project root layout (target)

See [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md#final-project-structure) for the full tree. Code lives at repo root under `app/`, `config/`, `tests/`, `scripts/`.

## Rules for modifying this folder

- **Architecture changes** require updating `architecture-freeze-v3.1.md` and bumping the version header
- **Progress changes** go in `implementation-status.md` only
- Do not duplicate frozen specs across files — link instead
- Keep agent-guidelines.md actionable, not narrative
