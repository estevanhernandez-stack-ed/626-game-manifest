# Curated overrides

Hand-curated corrections that **win over** mined data. One `<game>.json` per game; the **Steam app id is the key**. The build workflow applies these as the final merge step (after the Ludusavi backbone + MO2 enrichment), so a curated `engine` / `modPath` beats whatever the miner guessed — and an override for a game the mined sources don't have simply **adds** it.

## Format (camelCase; only `steamAppId` is required)

```json
{
  "steamAppId": "72850",
  "id": "skyrim",
  "name": "The Elder Scrolls V: Skyrim",
  "engine": "bethesda",
  "modPath": "Data",
  "nexusDomain": "skyrim",
  "featured": 20,
  "fileExtensions": ["esp", "esl", "esm", "bsa"]
}
```

`engine` must be a known engine key: `bethesda`, `ue-pak`, `bepinex`, `smapi`, `minecraft`, `source`, `melonloader`, `fromsoft`, `custom`. Unspecified fields are left as the miner set them. A wrong `steamAppId` just doesn't match — it's reported in the build summary, never corrupts.

## Adding a game

Drop a `<game>.json` here and open a PR. On merge, the build workflow regenerates and **re-signs** `games-manifest.json`. A game on an engine the launcher already knows ships as this data PR — no app release.
