# Manifest schema

`games-manifest.json` — camelCase JSON, the exact shape the launcher's
`ModManager.Core.Manifest.GameManifest` deserializes.

```jsonc
{
  "schemaVersion": 1,                 // a launcher older than it understands ignores the file
  "generatedUtc": "2026-06-14T00:00:00Z",
  "minBinaryVersion": "0.6.0",        // launchers older than this ignore the remote copy
  "games": [ /* GameManifestEntry[] */ ]
}
```

## GameManifestEntry

| Field | Type | Notes |
|---|---|---|
| `id` | string | stable slug, unique (primary key) |
| `name` | string | display name |
| `engine` | string \| null | must be a known engine key (below); null ⇒ launcher folder-detects at runtime |
| `stores` | object | `{ steamAppId?, gogId?, epicAppName?, xboxStoreId?, eaContentId? }` (Steam and the EA app are probed; an EA app install is offered only when `eaContentId` matches) |
| `nexusDomain` | string \| null | Nexus game slug (e.g. `skyrimspecialedition`) |
| `curseforgeGameId` | int \| null | |
| `modPath` | string \| null | mod folder, relative — **must not** be absolute or contain `..` |
| `modPathModOnly` | bool \| null | `true` says `modPath` holds nothing but mods: no file in it is the game's own (Cyberpunk 2077's `archive/pc/mod` yes; a Bethesda `Data` or a Total War `data` never). Safe Clear's "Return to vanilla" reads it to know it may move everything left in that folder into the restore point. Without it, a `modPath` is swept only when it matches its engine's own mod-only shape (a UE `Content/Paks/~mods`, `BepInEx/plugins`, a SMAPI `Mods`, …); any other mod folder is left alone. Set it only after checking a real install: a wrong `true` moves base-game files out of the game until Restore. **The build refuses an override that sets it** without a `modPath`, on the game root, on a known base-content folder (`Data`, `Modules`, `GameData`, `Content`, `bin`, `Binaries`, …) or on a `Content/Paks` folder, and a refusal stops the whole feed from regenerating, so run the miner's `--with-overrides` locally before merging (see `overrides/README.md`). It binds to the path it describes: a feed that restates the same `modPath` keeps it, a corrected path drops an inherited `true`, and a feed `false` overrides an embedded `true`. Additive, optional; binaries that predate it ignore it. |
| `extraModTrees` | string[] \| null | other mod folders, relative to the game root, that a game's mods also write to (Cyberpunk 2077: `r6/scripts`, `r6/tweaks`, …). Each must name a folder below the game root: the launcher drops one that is empty, absolute (a leading `/` or `\` on any OS), drive-qualified, contains `..`, has a segment of only dots or spaces, or is `.`, and keeps the rest of the entry. It is a relative-path check only; the trees are never written to, so they do not go through `modPath`'s forbidden-paths gate. At runtime a tree that is, holds or sits inside one of the game's own mod folders is skipped. Descriptive only: the launcher names which trees hold a top-level entry with a mod's name (letters and digits, any case), never moves them. Additive, optional; binaries that predate it ignore it. |
| `fileExtensions` | string[] \| null | override to the engine's default extensions |
| `groupingRule` | string \| null | override to the engine's default grouping |
| `featured` | int \| null | quick-pick rank; null ⇒ not featured |
| `saveDirHint` | string \| null | descriptive save-location hint |
| `saveLayout` | string \| null | `"worlds"` (a folder per world/save/slot — Palworld, Cyberpunk 2077) or `"typedFiles"` (several formats of one save side by side — Elden Ring's `.sl2`/`.co2`/`.err`). **Null means nobody has checked**, not "flat". Descriptive only: it says what the folder looks like, never how to write to it. Additive, optional; binaries that predate it ignore it. **See the note below — this describes the folder `saveDirHint` resolves to.** |
| `savePlayerPaths` | string[] \| null | Globs, **relative to a save unit**, naming the files that are the PLAYER rather than the place — the line a shared world is cut along. A unit is one world folder when `saveLayout` is `"worlds"`, and the whole save folder otherwise. **Null means nobody has curated it**, never "this game has no character data". Descriptive: it says where the line is, never how to cut it. |
| `banRisk` | string \| null | `"low"` / `"medium"` / `"high"` — anti-cheat/ban exposure for online modding. Descriptive only; on `high` the launcher warns + gates enabling behind a one-time acknowledgment (never auto-enables, never hard-blocks). |
| `safeRoute` | string \| null | `"offline"` / `"private-server"` / `"official-mods"` / `"none"` / `"unclear"` — whether a DOCUMENTED safe modding route exists despite the ban risk. Additive, optional; binaries that predate it ignore it. |
| `safeRouteHint` | string \| null | One user-facing sentence naming the safe route (or its absence). Rendered by the launcher's ban-risk warning. |
| `provenance` | object | `{ sources: string[], status: "auto" | "curated" }` |

### `saveLayout` describes the folder `saveDirHint` resolves to

Get the hint wrong and the layout is worse than absent. Three real examples from one machine:

| Game | `saveDirHint` resolves to | Verdict |
|---|---|---|
| Palworld | `…/Pal/Saved/SaveGames/<storeUserId>` → the world folders | `"worlds"` ✅ |
| Cyberpunk 2077 | `…/Saved Games/CD Projekt Red/Cyberpunk 2077` → 93 save folders | `"worlds"` ✅ |
| Stellaris | `<winDocuments>/Paradox Interactive/Stellaris` → `.launcher-cache`, `data`, `logs` | **do not declare** ❌ |

Stellaris *is* folder-per-campaign, but one level down in `save games/`. Declaring `"worlds"` against
the hint it currently has would list launcher caches to the user as if they were saves.

**So: check the hint against a real install before declaring a layout.** A game whose hint points at a
parent folder needs the hint fixed first. Leaving `saveLayout` null costs nothing — the launcher falls
back to whole-folder backup and restore, which is what every game does today.

## Known engine keys

`bethesda`, `ue-pak`, `bepinex`, `smapi`, `minecraft`, `source`, `melonloader`,
`fromsoft`, `custom`. An entry with an unknown engine key is **skipped** by an
older launcher (forward-compat) — adding a new engine is launcher code, not data.

## Trust + safety (enforced by the launcher, re-stated here)

- The manifest is consumed only if its detached `.sig` verifies against the
  public key pinned in the launcher binary (ECDSA P-256 / SHA-256, `IeeeP1363`).
- `modPath` is re-validated through the launcher's forbidden-paths gate
  (relative-only, no `..`, no escape) — the manifest never widens it.
- `modPathModOnly` is honoured only on the game's primary, non-user-set location at
  exactly `modPath`, and never on a folder the launcher's gate refuses (see the field
  above) or one holding an `.exe`, so a mistyped flag can't open a base folder to sweeping.
- `extraModTrees` entries are checked as relative folders below the game root
  and are only ever READ (listed), never written to; an unsafe one is dropped.
- A bad signature / unknown schema / too-high `minBinaryVersion` ⇒ the launcher
  falls back to its embedded manifest. The feed can only ever add/refresh; it
  can never break a working install.
- `banRisk` is descriptive — it states a game *is* ban-risky (online / kernel
  anti-cheat); it never says how to enable/disable a mod (that stays launcher
  code). Unlike every other field, it merges by **never-downgrade max**: a feed
  refresh can raise a game's risk but can never silently lower a curated `high`,
  so an auto-mined refresh can't quietly un-gate a game.
