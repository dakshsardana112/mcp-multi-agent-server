# Changelog

All notable changes to this project are documented here. Dates are UTC.

## [0.1.0] — 2026-04-21

### Added
- Initial project scaffold: `src/` layout, `pyproject.toml`, MIT license, `.gitignore`, `requirements.txt`.
- Core MCP server (`server.py`) built on `FastMCP` with `server_info`, `ping`, `server://agents` resource, and `getting_started` prompt.
- `AgentRegistry` for microservices-style agent wiring — factories resolved lazily and attached per-agent.
- `JsonStore` persistence layer with atomic writes, read-modify-write callback, and corruption recovery.
- Six domain agents:
  - **task** — CRUD, filters, `task_stats` with overdue detection.
  - **notes** — create/list/search/update/delete, tag normalisation, `notes_tags` aggregation.
  - **weather** — deterministic mock forecast (no API key needed), history tracking, outfit prompt template.
  - **finance** — expense logging, per-category monthly budgets, summary with % usage + remaining.
  - **file** — directory scan, summary by category, substring search (read-only; never moves files).
  - **kb** — Q&A store with word-overlap retrieval + prompt template.
- Test suite: 57 pytest cases covering server wiring, registry, storage, and every agent (happy + edge cases).
- Example MCP client (`examples/client_demo.py`) demonstrating stdio transport, tool discovery, resource listing, prompt listing.
- Docs: `README.md`, `docs/LEARNING_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/ADD_AGENT.md`.

### Fixed
- `weather_agent._mock_forecast`: `temp_f` was derived from the unrounded `base_c`, causing off-by-0.1 drift when a caller round-tripped °C → °F → °C. Now derived from the already-rounded `temp_c`.
