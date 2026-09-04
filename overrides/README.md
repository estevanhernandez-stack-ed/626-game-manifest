# Curated overrides

Hand-curated corrections that **win over** mined data. One `<game>.json` per game. The **Steam app id
is the key when the game has one**; a game sold outside Steam — the EA app, Epic, GOG — is keyed by its
`id` slug instead. Exactly one of the two is required. The build workflow applies these as the final merge step (after the Ludusavi backbone + MO2 enrichment), so a curated `engine` / `modPath` beats whatever the miner guessed — and an override for a game the mined sources don't have simply **adds** it.

The build **fails** if two files share an `id` or a Steam app id: one would silently win, and picking a
winner is not something a build should do quietly.

## Format (camelCase; exactly one of `steamAppId` / `id` is required)

```json
{
  "steamAppId": "72850",
  "id": "skyrim",
  "name": "The Elder Scrolls V: Skyrim",
  "engine": "bethesda",
  "modPath": "Data",
  "nexusDomain": "skyrim",
  "featured": 20,
  "fileExtensions": ["esp", "esl", "esm", "bsa"],
  "banRisk": "high"
}
```

`engine` must be a known engine key: `bethesda`, `ue-pak`, `bepinex`, `smapi`, `minecraft`, `source`, `melonloader`, `fromsoft`, `custom`. Unspecified fields are left as the miner set them. A wrong `steamAppId` just doesn't match — it's reported in the build summary, never corrupts.

`banRisk` (`"low"` / `"medium"` / `"high"`) marks a game's anti-cheat/ban exposure for online modding. On `high` the launcher warns and gates enabling behind a one-time acknowledgment — it never auto-enables and never hard-blocks (disable stays one click away). Flag it only where modding online genuinely risks a ban (online / kernel anti-cheat). Don't flag offline-friendly single-player games, and don't flag a game whose ban risk the launcher already mediates (e.g. Elden Ring, where the reversible EAC toggle is the safe-modding path).

`saveLayout` (`"worlds"` / `"typedFiles"`) says how the game arranges its saves. `"worlds"` means a folder per world, save or slot — Palworld, Cyberpunk 2077 — which lets the launcher back up and restore **one** of them instead of the whole folder. `"typedFiles"` means several formats of one save side by side, like Elden Ring's `.sl2` / `.co2` / `.err`.

**Check it against a real install before adding it, and check the right folder.** `saveLayout` describes whatever `saveDirHint` resolves to, so a hint pointing one level too high makes the layout actively wrong rather than merely absent. Stellaris is the cautionary case: it genuinely is folder-per-campaign, but its hint resolves to the game's config directory, so declaring `"worlds"` would list `.launcher-cache` and `logs` to the user as if they were saves.

Leaving it out costs nothing. The launcher falls back to whole-folder backup and restore — what every game does today.

## Adding a game

Drop a `<game>.json` here and open a PR. On merge, the build workflow regenerates and **re-signs** `games-manifest.json`. A game on an engine the launcher already knows ships as this data PR — no app release.

## Finding `savePlayerPaths` — the world/character seam

This is the one field you cannot look up. It is a fact about how a studio arranged its save folder,
and the only way to get it right is to open a real install and look. Two rules first:

**Ask the shape question before the seam question.** Does the player *make* a world? Palworld, Windrose,
Terraria and Valheim: yes. Cyberpunk and Elden Ring: no — the world is the studio's and the save is
your character inside it, so there is no seam and the field stays absent. Adding one to a
character-progression game is not a small mistake; it implies a "share the world" the game cannot
support.

**Paths are relative to a save UNIT, not the save folder.** A unit is one world folder when
`saveLayout` is `"worlds"`, and the whole save folder otherwise. The two curated examples are one of
each, which is why they look so different.

### What to look for

Play the game once, then open the save folder and sort by what changes:

| clue | example |
|---|---|
| a folder named for the player concept | `Players/`, `Accounts/`, `characters_local/` |
| a file whose size tracks YOUR progress, not the world's | Palworld's `LocalData.sav` — 128 KB against `Level.sav`'s 2 MB |
| **the multiplayer tell** | a world you JOINED keeps only your half. Palworld's joined world is `LocalData.sav` and nothing else — the game is showing you the seam |
| a folder named for the place | `Worlds/`, `worlds_local/`, `save games/` |

That third row is the strongest signal there is. If the game supports joining someone else's world,
whatever it keeps locally for that world **is** the player half, by definition.

### The two curated examples

**Palworld** — `saveLayout: "worlds"`, so a unit is one world folder:

```
Level.sav  LevelMeta.sav  WorldOption.sav   the place
LocalData.sav  Players/                     you        ->  ["Players/**", "LocalData.sav"]
```

**Windrose** — not `worlds`, so a unit is the whole save folder:

```
0.10.0/Worlds/<guid>/       23.6 MB   the place
0.10.0/Players/<guid>/       1.4 MB   you
0.10.0/Accounts/<guid>/       54 KB   you
```

Those three repeat under `RocksDB/`, `RocksDB_v2/`, a nested migration tree and a backups tree — which
is exactly why the field takes **globs** rather than a list of names:

```json
["**/Accounts/**", "**/Players/**", "**/AccountDescription.json"]
```

`**` crosses directories, `*` does not, and everything else is literal.

### When to leave it out

Leaving it absent costs nothing — the launcher simply does not offer to share a world for that game,
and there is no message about it, because a control that only explains why it cannot work is worse
than no control. Getting it *wrong* costs someone their character in a public file. **If you are not
looking at a real install, do not curate this field.**

### Two worked refusals

Curating well means knowing when not to. Both of these looked like easy wins and were not.

**Stellaris — the hint was wrong, so the layout would have been.** It *is* folder-per-campaign, but
Ludusavi's path points at the game's config directory:

```
<winDocuments>/Paradox Interactive/Stellaris        .launcher-cache, data, logs, dlc_load.json …
<winDocuments>/Paradox Interactive/Stellaris/save games   <- the campaigns are here
```

Declaring `"worlds"` against the first would have listed launcher caches to the user as if they were
saves. Fixed by overriding `saveDirHint` down one level, and *then* the layout is true. **A layout
field is only ever as good as the hint it describes.**

**Sons Of The Forest — a partial seam is worse than none.** Its saves are `SaveData.zip`, and the
player lives *inside* the archive:

```
PlayerInventorySaveData.json   12,080 bytes
PlayerStateSaveData.json       21,004 bytes
PlayerArmourSystemSaveData.json, PlayerClothingSystemSaveData.json …
```

A glob over the save folder cannot reach inside a zip. Curating `["PlayerProfile.json"]` would have
looked correct, produced a "shareable" world, and shipped the character's inventory and state anyway.
**Left absent on purpose.**

It has no `saveLayout` either: save units sit two levels down and split across parallel `Multiplayer/`
and `MultiplayerClient/` trees, so no single folder's subdirectories are the units.

### Before curating a seam: check whether the game stamps an account id INSIDE its saves

**A shareable bundle can remove files. It cannot remove fields.** The seam is a list of paths, so the
launcher can drop a character's *files* — it cannot reach inside a save and take an id out of it.

Every Steam game keeps `steam_autocloud.vdf` beside its saves, holding the account id, and a shareable
bundle drops that file. If the game *also* writes the id into the save data, dropping the `.vdf`
produces a bundle that looks clean, is described as clean, and still identifies its owner. **False
assurance is worse than no assurance**, because the person acts on it.

So before adding `savePlayerPaths`, grep the save folder for your own Steam id in **three forms** —
the ID64 as ASCII, the ID64 as little-endian bytes, and the Steam3 account id:

```python
import os, struct
id64  = b"7656119XXXXXXXXXX"                      # your ID64, ASCII
raw   = struct.pack("<Q", 7656119XXXXXXXXXX)      # the same number, little-endian binary
acct  = b"XXXXXXX"                                 # Steam3 account id (the userdata folder name)

for r, _, fs in os.walk(save_dir):
    for f in fs:
        b = open(os.path.join(r, f), "rb").read()
        if id64 in b or raw in b or acct in b:
            print(os.path.relpath(os.path.join(r, f), save_dir))
```

**Only `steam_autocloud.vdf` should come back.** Anything else means the game embeds the id, and the
seam should not be curated until someone has decided what to do about it.

Two real results from that scan:

| Game | Where the id is | Consequence |
|---|---|---|
| Palworld, Windrose, Cyberpunk, Witchfire, … | `steam_autocloud.vdf` only | safe to curate |
| **Elden Ring** | little-endian **inside 18 of 19 save files** | a seam here would leak the owner. It is also a character game, so it gets none — but that is luck, not a rule |
| **Gas Station Simulator** | in the **filename** — `GSS_Stats_<id64>_…` | the path itself carries it |

Elden Ring is the cautionary case. Its id sits in a checksummed save, so it cannot be stripped without
corrupting the file — that is exactly why save re-signing tools exist for FromSoft games. Rewriting it
would mean recomputing per-slot hashes, which is writing into a save format, which this project does
not do casually.
