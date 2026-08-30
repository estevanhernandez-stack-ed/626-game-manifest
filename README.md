# 626 Mod Launcher — game manifest feed

[![supported games](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Festevanhernandez-stack-ed%2F626-game-manifest%2Fmain%2Fbadge.json)](SUPPORTED-GAMES.md)

The signed game-definition feed the [626 Mod Launcher](https://github.com/estevanhernandez-stack-ed/626-mod-launcher) fetches at runtime, so new game support reaches users without an app release.

**See the full [supported games list](SUPPORTED-GAMES.md)** — regenerated automatically as curation lands. Machine-readable: [`supported-games.json`](supported-games.json) (stable schema, CORS-open raw URL — built for the 626 Labs hub, Discord bots, and anything else that wants it).

This repo holds **game identity data only** — names, store IDs, engine keys, mod-folder paths, Nexus slugs. No mods, no binaries, no copyrighted text. The launcher already knows *how* each engine loads mods (that's code, shipped in the app); this feed only tells it *which games exist and where their mods go*.

## What's here

| Path | What |
|---|---|
| `games-manifest.json` | The generated, published manifest the launcher fetches. |
| `games-manifest.json.sig` | Detached ECDSA P-256 signature over the exact manifest bytes. |
| `overrides/` | Hand-curated corrections (`<game>.json`) — these win over mined data. |
| `SCHEMA.md` | The manifest shape. |
| `supported-games.json` | The public consumer contract, generated from the manifest. |
| `SUPPORTED-GAMES.md` | The human-readable game list, generated from the manifest. |
| `.github/workflows/` | CI that mines → curates → signs → publishes. |
| `NOTICE` | Attribution for the upstream factual-data sources. |

## The public contract (`supported-games.json`)

Generated from the signed manifest on the same CI rail, so it can never drift from it. The hub website
and the Discord bot read it, so it changes **additively only**: a field here keeps its name and meaning.

| Field | Always? | What |
|---|---|---|
| `id` / `name` | yes | The game's key and display name. |
| `tier` | yes | `engine-curated` (the launcher knows the engine and mod folder) or `nexus-only` (identified on Nexus; engine detected from the folder at runtime). |
| `steamAppId` / `steamUrl` | when known | Store identity. |
| `engine` / `modPath` | engine-curated | How mods reach the game. |
| `nexusUrl` | when known | Nexus Mods page. |
| `featured` | rarely | Ordering hint for the featured list. |
| `saveGranularity` | when curated | `"per-save"` — the save layout is known, so one save can be handled on its own. |
| `saveShareable` | when curated | `true` — the player seam is curated, so a world can be shared without the character who lived in it. |

**The two save fields are independent, not a ladder.** An early proposal published one ordered value
(`backup` < `per-save` < `shareable`) on the claim that each contains the one above. The data does not
work that way: Windrose has a curated seam and no known layout, so it is shareable *without* being
per-save. A single value would have had to claim a layout nobody has checked.

**Absent means nobody has curated it, never that the game lacks it.** Every game can be backed up and
restored whole; these fields say only what is known beyond that floor. Consumers should treat a missing
field as *unknown*, and must not render it as a limitation of the game.

There is deliberately no field for the launcher reading a save's own name. That is compiled behaviour
in the binary, not a fact about the game, so no data field could honestly carry it — and a data PR
could set it for a game the launcher cannot actually name.

## How it's built

1. **Backbone** — game names + Steam IDs + save hints, mined from the [Ludusavi manifest](https://github.com/mtkennerly/ludusavi-manifest).
2. **Enrichment** — mod paths, mined from [MO2 `basic_games`](https://github.com/ModOrganizer2/modorganizer-basic_games), merged by Steam ID.
3. **Curation** — `overrides/` win over everything: the reliable `engine` + `modPath` for the games people actually mod.
4. **Sign** — ECDSA P-256 (`IeeeP1363`) over the canonical bytes, with the private key held only in CI (`MANIFEST_SIGNING_KEY`). The public key is pinned in the launcher binary.
5. **Publish** — `games-manifest.json` + `.sig` committed here; the launcher fetches them raw, verifies, and merges over its embedded snapshot.

Mined data is **facts only** (app IDs, names, paths) — never upstream code, prose, or table structure — cross-verified against primary sources. Facts are uncopyrightable ([*Feist v. Rural*](https://supreme.justia.com/cases/federal/us/499/340/)); see `NOTICE`.

## Adding / fixing a game (curation)

Drop a `<game>.json` in `overrides/` (Steam ID is the key; see `overrides/README.md` for the format), open a PR, and CI regenerates + re-signs. A wrong Steam ID simply doesn't match — it's reported, never corrupts.

A new game on an engine the launcher **already knows** is a data PR here — no app release. A *new engine* is launcher code (a release), by design.

## License

- **Tooling / schema / CI:** MIT — see `LICENSE`.
- **Manifest data (the facts):** CC0 / public domain — see `DATA-LICENSE.md`.
- **Upstream sources:** credited in `NOTICE`.
