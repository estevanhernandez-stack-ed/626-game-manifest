# Contributing — adding & fixing games

This repo is the **signed game-definition feed** for the 626 Mod Launcher. It publishes *facts* about games — Steam/GOG/Epic IDs, names, engine keys, mod-folder paths, Nexus slugs — so the launcher knows how to manage mods for a game without an app update.

You grow it by adding a small JSON file. No code.

## How it works

The published `games-manifest.json` is generated, not hand-edited. CI mines a backbone (Ludusavi + Mod Organizer 2) and then applies the **hand-curated overrides in [`overrides/`](overrides/)** — your overrides win over the mined data. On merge to `main`, CI regenerates and re-signs the manifest automatically. **Never edit `games-manifest.json` directly** — it's overwritten.

## Add or fix a game

1. Create `overrides/<slug>.json` (one file per game; `<slug>` is a kebab-case id, e.g. `baldurs-gate-3.json`).
2. Fill the fields below. `steamAppId` is the key; everything else is optional.
3. Open a PR. CI regenerates + signs on merge.

### Fields (camelCase)

| Field | Required | What it is |
|---|---|---|
| `steamAppId` | **yes** | Steam App ID (string). The key. An override whose id isn't in the backbone *adds* a new game; one that matches *corrects* it. |
| `id` | no | kebab-case slug for the entry (derived from name if omitted). |
| `name` | no | Display name. |
| `engine` | no | One of the 9 keys below. Sets the quick-pick + the mod mechanism. Omit if you don't know — a verified `nexusDomain` alone is enough to publish (see below). |
| `modPath` | no | The mod folder **relative** to the game root (e.g. `Data`, `Mods`, `Content/Paks/~mods`). Must be relative + safe — no leading `/`, no drive letter, no `..`. |
| `nexusDomain` | no | The game's Nexus Mods domain slug (the `…/games/<slug>` part of its Nexus URL). |
| `banRisk` | no | `low` \| `medium` \| `high` — see the guide below. |
| `fileExtensions` | no | Mod file extensions (e.g. `["esp","esl","esm","bsa"]`). |
| `featured` | no | Quick-pick rank (lower = higher). Only for marquee games. |
| `saveDirHint` | no | Descriptive save-location hint. |

### What makes a game "supported" — two paths

A game only ships if it earns a tag:

- **Nexus path (lightweight):** a verified `nexusDomain`. The game appears; the launcher **folder-detects the engine at runtime** when you add it. Good for the long tail.
- **Engine path (quick-pick):** a verified `engine` + safe `modPath` (+ `featured` for the quick-pick list). The launcher knows the engine up front.

If you set neither `engine` nor `nexusDomain`, the entry is dropped — don't submit those.

### The 9 engine keys

`ue-pak` · `bethesda` · `minecraft` · `bepinex` · `smapi` · `source` · `melonloader` · `fromsoft` · `custom`

Pick from the game's **documented mod loader** — don't guess from a folder name (a `Data` folder is Bethesda *or* FromSoft). A loader the launcher doesn't have yet is **not** a data PR — open an issue instead.

### banRisk guide

- `high` — active anti-cheat that bans for file mods, or a primarily-online/competitive title (the launcher gates enabling behind an explicit acknowledgment).
- `medium` — online with a softer stance / unofficial-server modding.
- `low` or omit — single-player, no anti-cheat.

## The one rule: facts, cross-verified

This feed publishes only **uncopyrightable facts**, and every datum must be **cross-verified against a second primary source**:

- `steamAppId` → the Steam store page / SteamDB.
- `engine` → the game's documented mod loader (its Nexus page, official modding docs).
- `nexusDomain` → the live Nexus Mods page (and that it has real mod activity).
- `modPath` → the loader's documented mod folder.

Never copy prose, instructions, or another tool's selection/arrangement. Don't bulk-scrape access-restricted sources (e.g. PCGamingWiki blocks automated fetch). Facts only, in our own schema.

## License

Tooling + schema: MIT. Manifest data: CC0 / public domain (see `DATA-LICENSE.md`). By contributing an override you agree your factual data is released CC0.
