# Job Radar

Job Radar is a local-first desktop application for organizing job opportunities from Telegram sources that a user explicitly approves. The application is being built in small, verifiable increments. The repository contains the JR-001 desktop foundation and an initial responsive UI prototype; persistence, Telegram consent/auth, sync, and job workflows remain in progress.

## Technology

- Tauri 2 and a Rust desktop host
- React, TypeScript, and Vite
- A Python 3.12+ worker package (no Telegram integration yet)
- SQLite is planned for later tasks; this foundation does not create a database

## Prerequisites

- Node.js 24 or newer and pnpm 10.31
- Python 3.12 or newer and uv
- Rust stable with the Windows C++ build tools and WebView2 runtime for native desktop development

See the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/) for operating-system dependencies.

## Setup

```powershell
pnpm install
uv sync --project worker --dev
```

## Common commands

```powershell
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm check:python
pnpm check:rust
```

The desktop app uses Tauri's native host, so `pnpm dev` requires the Rust toolchain and platform prerequisites. Frontend checks can run independently.

## Project layout

```text
apps/desktop/       Tauri host and React frontend
worker/             Python worker package and its tests
contracts/v1/       Versioned IPC JSON Schema
Agent_Docs/          Local project specifications (currently ignored by Git)
```

The implementation source of truth is the project specification package in `Agent_Docs`, including `Job_Radar_2.0_Visual_Design_System.md` for the approved UI direction. `Agent_Docs` is currently ignored by Git, so its local specifications are not included in ordinary commits. The UI prototype is not a data-backed product flow. No Telegram credentials, user data, or production fixtures belong in this repository.
