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
| `stores` | object | `{ steamAppId?, gogId?, epicAppName?, xboxStoreId? }` (only Steam is probed today) |
| `nexusDomain` | string \| null | Nexus game slug (e.g. `skyrimspecialedition`) |
| `curseforgeGameId` | int \| null | |
| `modPath` | string \| null | mod folder, relative — **must not** be absolute or contain `..` |
| `fileExtensions` | string[] \| null | override to the engine's default extensions |
| `groupingRule` | string \| null | override to the engine's default grouping |
| `featured` | int \| null | quick-pick rank; null ⇒ not featured |
| `saveDirHint` | string \| null | descriptive save-location hint |
| `saveLayout` | string \| null | `"worlds"` (a folder per world/save/slot — Palworld, Cyberpunk 2077) or `"typedFiles"` (several formats of one save side by side — Elden Ring's `.sl2`/`.co2`/`.err`). **Null means nobody has checked**, not "flat". Descriptive only: it says what the folder looks like, never how to write to it. Additive, optional; binaries that predate it ignore it. **See the note below — this describes the folder `saveDirHint` resolves to.** |
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
- A bad signature / unknown schema / too-high `minBinaryVersion` ⇒ the launcher
  falls back to its embedded manifest. The feed can only ever add/refresh; it
  can never break a working install.
- `banRisk` is descriptive — it states a game *is* ban-risky (online / kernel
  anti-cheat); it never says how to enable/disable a mod (that stays launcher
  code). Unlike every other field, it merges by **never-downgrade max**: a feed
  refresh can raise a game's risk but can never silently lower a curated `high`,
  so an auto-mined refresh can't quietly un-gate a game.
