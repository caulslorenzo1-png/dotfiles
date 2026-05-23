# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Windows home directory (`C:\Users\lcaul`) containing multiple independent projects. There is no single root build system — each subdirectory is its own project.

Key projects:
- **`openclaw/`** — Large TypeScript monorepo (AI platform). Has its own `CLAUDE.md` (symlink to `AGENTS.md`). Read that file before working in that directory.
- **`okdf-mission-control/`** — React 19 + Vite 8 dashboard app (the main active custom project).
- **`okdf-system/`** — Early-stage client (Vue 3 + Vite) + server (Express + OpenAI SDK).

---

## okdf-mission-control

### Commands

```sh
cd okdf-mission-control
npm install        # install deps
npm run dev        # start dev server (Vite HMR)
npm run build      # production build
npm run lint       # ESLint
npm run preview    # preview production build
```

No test runner is configured.

### Architecture

The entire app lives in `src/MissionControl.jsx` (~1143 lines). `src/main.jsx` mounts it as the root component — `src/App.jsx` is unused Vite scaffold.

**How it works:** The app calls the Anthropic API directly from the browser (`https://api.anthropic.com/v1/messages`) — there is no backend. `callClaude` sends **no `x-api-key` header**; auth is handled by the browser's claude.ai session cookies, so the app only works when opened in a browser signed into claude.ai. It passes `mcp_servers` in the request body to have Claude orchestrate external services:

- `MCP_MAKE` → Make.com MCP (`https://mcp.make.com`)
- `MCP_STRIPE` → Stripe MCP (`https://mcp.stripe.com`)
- `MCP_NETLIFY` → Netlify MCP (`https://netlify-mcp.netlify.app/mcp`)
- `MCP_NOTION` → Notion MCP (`https://mcp.notion.com`)

All Claude calls go through `callClaude(prompt, mcpServers?)`, which returns raw API response objects. `getText(d)` extracts text blocks; `tryJSON(s)` parses JSON out of Claude's responses (stripping code fences).

**Layout:** 3-column grid. Above the grid: `Briefing` bar.
- Column 1: `MakePanel` + `OpenClawPanel`
- Column 2: `OrionMemoryPanel` + `TasksPanel` + `ActionLogPanel`
- Column 3: `StripePanel` + `NetlifyPanel` + `ContentQueuePanel`

**Panels:**
- `MakePanel` — controls the two "Orion Prime" Make.com scenarios (activate/pause/run now) and lists connectors; uses `MCP_MAKE`
- `OpenClawPanel` — connects to the local openclaw agent gateway at `http://localhost:18789` (constants `GW` + `GW_TOKEN` at top of panel section); shows online status and agent stats; lets you trigger hardcoded `CRON_JOBS` or send direct instructions to Orion via a chat input
- `OrionMemoryPanel` — reads the `orion_state` key from Make data store ID 99050; this is the Orion Prime agent's persistent memory/status (green/yellow/red health, ops summary, agent tasks, last decision); uses `MCP_MAKE`
- `TasksPanel` — reads priority tasks from a Notion Tasks DB (hardcoded URL); uses `MCP_NOTION`
- `ActionLogPanel` — reads the last 10 entries from the "Orion Action Log" Notion DB (found by title search); shows type, result, notes, and cycle timestamp; uses `MCP_NOTION`
- `StripePanel` — shows account balance and last 5 payment intents; uses `MCP_STRIPE`
- `NetlifyPanel` — shows current deploy status for site `NETLIFY_ID`; uses `MCP_NETLIFY`
- `ContentQueuePanel` — reads Draft/Scheduled items from a Notion Content Queue DB; can trigger posting to X/WhatsApp/Slack; uses `MCP_NOTION`
- `Briefing` — aggregates resolved data from all panels then generates a 3-sentence "Director's Briefing" via a direct `callClaude` call (no MCP servers); **auto-generates** once all four data sources are ready (`makeReady` + `stripeData` + `netlifyData` + `orionData`); button shown afterward for manual refresh

**"Orion Prime"** is the name of the autonomous agent system — two Make.com scenarios running every 4 hours (CEO Runner + Watchdog) with state persisted in a Make data store. This dashboard is the human operator's view of it.

**Color system:** All colors are in the `C` constant object at the top of `MissionControl.jsx`. The theme is dark (`#06070B` background) with gold accent (`#D4931F`).

**Panel pattern:** Each service section is a `<Panel>` component with a `status` prop (`"ok"` / `"err"` / `"loading"` / `"idle"`) that drives the indicator dot color.

**Hardcoded IDs** in `MissionControl.jsx` (top of file): Make.com team ID (`TEAM_ID`), Netlify site ID (`NETLIFY_ID`), and the two tracked Make.com scenario IDs in `SCENARIOS`.

**Claude model:** All `callClaude` calls use `claude-sonnet-4-6`. `max_tokens` is 1000 for most calls, 4000 in Orion's CEO Runner scenario.

**Startup timing:** The root `App` component delays MakePanel initialization by 3 seconds (`makeReady` state + `setTimeout`) to avoid hammering the Make MCP on first load.

### orion-prime/

Supporting files for the Orion Prime autonomous agent system (not runtime code — these are reference/config):

- `ceo-runner-prompt.md` — Full system prompt pasted into the CEO Runner Make.com scenario
- `watchdog-prompt.md` — System prompt for the Watchdog scenario
- `state-schema.json` — Initial value for the `orion_state` key in Make data store ID 99050
- `setup-guide.md` — Step-by-step checklist for first-time setup of all integrations (Make scenarios, Notion DBs, Stripe permissions, Slack)

---

## okdf-system

Early-stage, not functional yet.

- `client/` — Vue 3 + Vite; `npm run dev` inside that directory
- `server/` — Express + OpenAI SDK; `node index.js` (no start script defined)

---

## openclaw

See `openclaw/AGENTS.md` (also symlinked as `openclaw/CLAUDE.md`) for full guidance. Key commands from that file:

```sh
cd openclaw
pnpm install
pnpm dev            # run CLI in dev mode
pnpm build          # build
pnpm test <filter>  # run tests (never raw vitest)
pnpm check          # full check suite
pnpm format:*       # format with oxfmt (not Prettier)
pnpm openclaw agents --json   # list configured agents as JSON (config-only, no plugin loading)
claude agents --json          # list live Claude Code sessions as JSON
```

**Task registry (`src/tasks/`):** The `claude_session` type has `agent_id` (which configured openclaw agent owns the session) and `parent_agent_id` (the spawning agent for subagent/nested sessions).
