<!-- Adding or fixing a game? One overrides/<slug>.json per game. See CONTRIBUTING.md. -->

## What this adds/fixes

<!-- Game name(s) + what changed. -->

## Checklist

- [ ] One `overrides/<slug>.json` per game, keyed by `steamAppId`
- [ ] `steamAppId` verified on the Steam store / SteamDB
- [ ] Earns a publish tag: a verified `nexusDomain` **or** `engine` + safe `modPath` (not neither)
- [ ] `engine` (if set) is one of the 9 keys **and** matches the game's documented mod loader (not guessed from a folder name)
- [ ] `modPath` (if set) is **relative + safe** — no leading `/`, no drive letter, no `..`
- [ ] `banRisk` set for anti-cheat / online titles (`low`|`medium`|`high`)
- [ ] Every datum **cross-verified against a second primary source** — facts only, no copied prose

<!-- CI regenerates + signs games-manifest.json on merge — don't edit it directly. -->
