# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A HACS-distributed Home Assistant **custom integration** (`custom_components/minimax_tts`)
that adds **MiniMax** as a cloud **text-to-speech** engine to the Assist voice
pipeline. It is **TTS-only by design**: MiniMax has no speech-to-text/ASR
endpoint, and its chat models (incl. MiniMax-M2.7) are text-only and cannot
ingest audio — there is nothing to call for STT. Voice *input* is meant to be
handled by HA's local Whisper add-on; this integration produces the spoken
*replies*.

## Commands

```bash
pip install -r requirements_test.txt   # pytest + aiohttp
python -m pytest tests/ -q             # run unit tests
```

- The tests run on plain CPython (3.11+) **without** installing Home Assistant —
  see the testing note below.
- Structural validation (manifest, hassfest, HACS rules) runs in CI via
  `.github/workflows/validate.yml` (HACS action + hassfest) on every push.
- Manual end-to-end test: copy `custom_components/minimax_tts` into a real HA
  `config/custom_components/`, restart, add the **MiniMax TTS** integration with
  a real token (the voice dropdown populating proves auth + `get_voice`), then
  Developer Tools → Actions → `tts.speak` against the entity (audio playing
  proves `t2a_v2` + hex decode).

## Architecture

Single config entry → one `TextToSpeechEntity`. Audio flow:
`async_get_tts_audio` → `MiniMaxClient.synthesize` → `POST /v1/t2a_v2` →
hex-decode `data.audio` → `(format, bytes)` back to HA.

- **`const.py`** — the single source of truth for `DOMAIN`, API hosts, the model
  list, all config/option keys (`CONF_*`), defaults, `SUPPORTED_LANGUAGES` and
  `FALLBACK_VOICES`. Every other module imports keys from here; **keep names in
  sync across files** when you change anything.
- **`api.py`** — `MiniMaxClient`, the *only* module that talks HTTP to MiniMax,
  and intentionally free of Home Assistant imports so it stays unit-testable.
  `get_voices()` (`POST /v1/get_voice`) doubles as the credential check used by
  the config flow. `synthesize()` (`POST /v1/t2a_v2`) returns `(format, bytes)`.
  Every response goes through `_check_base_resp`: MiniMax returns business errors
  inside the JSON body with HTTP 200, so codes are checked even on success. Codes
  1004/2049 → `MiniMaxAuthError`; rate/quota codes → `MiniMaxRateLimitError`.
- **`config_flow.py`** — two steps: `user` (token + region + optional GroupId,
  validated by calling `get_voices`) → `voice` (default voice + model).
  Credentials live in `entry.data`; tunables (voice, model, speed, format,
  sample rate, language boost) live in `entry.options`. `MiniMaxOptionsFlow`
  subclasses `OptionsFlowWithReload`, so saving options auto-reloads the entity.
- **`__init__.py`** — maps the stored region key to a base URL, builds the
  `MiniMaxClient`, stashes it in `entry.runtime_data`, and forwards
  `Platform.TTS`.
- **`tts.py`** — `MiniMaxTTSEntity`. `async_get_supported_voices` exposes the
  account's voices to the UI; `async_get_tts_audio` resolves voice/model/speed
  from the per-call `options` first, then `entry.options` defaults.

## Gotchas

- **Audio is hex-encoded** (`output_format: "hex"`), not base64/binary — decode
  with `bytes.fromhex`.
- **Key and region are region-bound** (`api.minimax.io` vs `api.minimaxi.com`)
  and must match, or MiniMax rejects the key.
- **GroupId** is appended as `?GroupId=` only when set; the `t2a_v2` spec omits
  it but some accounts/endpoints require it.
- **Testing without HA:** `tests/conftest.py` registers a stand-in `minimax_tts`
  package and loads `const.py`/`api.py` via importlib so the real
  `__init__.py` (which imports `homeassistant`) is never executed. If you add a
  testable pure-logic module, load it there too. Don't import `tts.py`,
  `config_flow.py` or `__init__.py` from tests — they need Home Assistant.

## Publishing

`manifest.json` and `README.md` point at `github.com/tetsuo-repo/minimax-tts`.
Listing in the HACS default store additionally requires a logo PR to
`home-assistant/brands`; custom-repository installation works without it.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **minimax-tts** (230 symbols, 323 relationships, 8 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/minimax-tts/context` | Codebase overview, check index freshness |
| `gitnexus://repo/minimax-tts/clusters` | All functional areas |
| `gitnexus://repo/minimax-tts/processes` | All execution flows |
| `gitnexus://repo/minimax-tts/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
