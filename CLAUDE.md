# one-offs — Claude context

## What this repo is

A collection of standalone, one-off scripts. No shared framework, no build system, no tests. Each script is self-contained and lives here so it isn't lost. Scripts are added as needed and may be in any language.

## API keys and `.env`

A `.env` file at the repo root holds API keys (not checked in; see `.env.example`). Scripts that call an external API follow this pattern:

- Look for a script-specific key first (e.g. `VOICEGEN_OPENROUTER_KEY`).
- Fall back to the shared default (e.g. `OPENROUTER_KEY`) if the specific key is absent.

When adding a new script that uses OpenRouter, add its `<SCRIPTNAME>_OPENROUTER_KEY` entry to `.env.example`. For other APIs, follow the same pattern and add the shared default key to `.env.example` only once.

## Conventions

- Each script gets its own directory named for what it does (e.g. `rename-photos/`, `export-contacts/`).
- The directory contains the script itself and any supporting files (sample input, a small README, config templates).
- When a script gets complex enough to need a real project, it graduates out of this repo.

## README upkeep

When a new script is added, add a row to the **Scripts** table in `README.md` with: name (linked to its directory), language, and one-line description.
