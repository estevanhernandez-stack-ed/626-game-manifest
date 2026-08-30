#!/usr/bin/env python3
"""Generate the public supported-games surfaces from the built games-manifest.json.

Emits three files (committed by CI on the same rail as the signed manifest, so they can
never drift from it):
  SUPPORTED-GAMES.md   - the human page GitHub renders
  supported-games.json - the stable consumer contract (hub website, Discord bot)
  badge.json           - shields.io endpoint schema (live "N supported games" badge)

Stdlib only. Deterministic: games sorted by name, stable field order, timestamp supplied
by the caller (--generated-utc or SOURCE_DATE env) - the generator never reads the clock.

Saves derivation publishes two INDEPENDENT fields rather than one ordered tier. An early
proposal had a single ladder (backup < per-save < shareable) on the claim that each rung
contains the one above; the data says otherwise - windrose has savePlayerPaths and no
saveLayout, so it is shareable without being per-save. Granularity and shareability are
separate facts and are published separately. Both are OMITTED when the manifest has not
established them, because null there means "nobody has checked", never "flat" or "no
character data".

A "named" tier was proposed too and is deliberately absent: reading a save's own name is
compiled behaviour in the launcher, not a manifest fact, so no data field could honestly
carry it and a data PR could claim it for a game the binary cannot name.

Tier derivation mirrors the launcher facades: an entry with an engine is "engine-curated"
(quick-pick setup); else one with a nexusDomain is "nexus-only" (engine folder-detected at
runtime). The published manifest only contains entries that earned a tier; anything else
is skipped defensively.

Run `generate-public.py --self-test` to execute the embedded fixture assertions (CI runs
this as a gate before generating).
"""

import argparse
import json
import os
import sys

REPO = "estevanhernandez-stack-ed/626-game-manifest"
REQUEST_URL = f"https://github.com/{REPO}/issues/new?template=game-request.yml"
BADGE_COLOR = "17d4fa"  # 626 cyan, shields endpoint convention (no leading #)

ENGINE_CURATED = "engine-curated"
NEXUS_ONLY = "nexus-only"


def project(manifest):
    """Manifest dict -> sorted list of public game dicts (optional fields omitted)."""
    games = []
    for g in manifest.get("games", []):
        engine = g.get("engine")
        nexus = g.get("nexusDomain")
        if engine:
            tier = ENGINE_CURATED
        elif nexus:
            tier = NEXUS_ONLY
        else:
            continue  # defensively skip untagged entries; the published feed has none

        row = {
            "id": g.get("id", ""),
            "name": g.get("name", ""),
            "tier": tier,
        }
        steam_id = (g.get("stores") or {}).get("steamAppId")
        if steam_id:
            row["steamAppId"] = steam_id
            row["steamUrl"] = f"https://store.steampowered.com/app/{steam_id}/"
        if engine:
            row["engine"] = engine
            mod_path = g.get("modPath")
            if mod_path:
                row["modPath"] = mod_path
        # Two independent save facts, each omitted unless the manifest establishes it.
        # "per-save" says one save unit can be handled on its own; "shareable" says the
        # line between the place and the player is known, so a world can travel without
        # its character. Neither implies the other.
        if g.get("saveLayout"):
            row["saveGranularity"] = "per-save"
        if g.get("savePlayerPaths"):
            row["saveShareable"] = True
        if g.get("featured") is not None:
            row["featured"] = g["featured"]
        if nexus:
            row["nexusUrl"] = f"https://www.nexusmods.com/{nexus}"
        games.append(row)

    games.sort(key=lambda r: (r["name"].casefold(), r["id"]))
    return games


def build_json(games, generated_utc):
    curated = sum(1 for g in games if g["tier"] == ENGINE_CURATED)
    return {
        "schemaVersion": 1,
        "generatedUtc": generated_utc,
        "counts": {
            "total": len(games),
            "engineCurated": curated,
            "nexusOnly": len(games) - curated,
            "savesPerSave": sum(1 for g in games if g.get("saveGranularity") == "per-save"),
            "savesShareable": sum(1 for g in games if g.get("saveShareable")),
        },
        "games": games,
    }


def build_badge(games):
    return {
        "schemaVersion": 1,
        "label": "supported games",
        "message": str(len(games)),
        "color": BADGE_COLOR,
    }


def md_escape(s):
    return s.replace("|", "\\|")


def link(label, url):
    return f"[{label}]({url})" if url else "—"


def saves_cell(g):
    """What is KNOWN about this game's saves. Every game can be backed up whole, so that is
    the floor and the honest word for "nobody has curated any more than that"."""
    bits = []
    if g.get("saveGranularity") == "per-save":
        bits.append("per-save")
    if g.get("saveShareable"):
        bits.append("shareable")
    return " · ".join(bits) if bits else "backup"


def build_markdown(games, generated_utc):
    curated = [g for g in games if g["tier"] == ENGINE_CURATED]
    nexus_only = [g for g in games if g["tier"] == NEXUS_ONLY]
    featured = sorted(
        (g for g in games if "featured" in g), key=lambda g: g["featured"]
    )

    out = []
    out.append("# Supported games")
    out.append("")
    per_save = [g for g in games if g.get("saveGranularity") == "per-save"]
    shareable = [g for g in games if g.get("saveShareable")]

    out.append(
        f"**{len(games)} games** — {len(curated)} engine-curated · "
        f"{len(nexus_only)} Nexus-only. Generated {generated_utc}."
    )
    out.append("")
    out.append(
        "**Engine-curated** games get quick-pick setup — the launcher knows the engine "
        "and mod folder. **Nexus-only** games are identified on Nexus Mods; the launcher "
        "detects the engine from the game folder at runtime."
    )
    out.append("")
    out.append(
        f"**Saves** — every game here can be backed up and restored whole. "
        f"{len(per_save)} also have a known save layout, so a single save can be handled on "
        f"its own; {len(shareable)} have a curated player seam, so a world can be shared "
        f"without the character who lived in it. The two are independent: a game can have "
        f"the seam without the layout. Blank means nobody has curated it yet, not that the "
        f"game lacks it."
    )
    out.append("")
    out.append(f"Missing a game? [Request it]({REQUEST_URL}) — facts welcome.")
    out.append("")

    if featured:
        out.append("## Featured")
        out.append("")
        for g in featured:
            out.append(
                f"{g['featured']}. **{md_escape(g['name'])}** — {g.get('engine', '')}"
            )
        out.append("")

    out.append(f"## Engine-curated ({len(curated)})")
    out.append("")
    out.append("| Game | Engine | Mod path | Saves | Steam | Nexus |")
    out.append("|---|---|---|---|---|---|")
    for g in curated:
        out.append(
            "| {name} | `{engine}` | `{mod}` | {saves} | {steam} | {nexus} |".format(
                name=md_escape(g["name"]),
                engine=g.get("engine", ""),
                mod=g.get("modPath", "—"),
                saves=saves_cell(g),
                steam=link("Steam", g.get("steamUrl")),
                nexus=link("Nexus", g.get("nexusUrl")),
            )
        )
    out.append("")

    out.append(f"## Nexus-only ({len(nexus_only)})")
    out.append("")
    out.append("| Game | Saves | Steam | Nexus |")
    out.append("|---|---|---|---|")
    for g in nexus_only:
        out.append(
            "| {name} | {saves} | {steam} | {nexus} |".format(
                name=md_escape(g["name"]),
                saves=saves_cell(g),
                steam=link("Steam", g.get("steamUrl")),
                nexus=link("Nexus", g.get("nexusUrl")),
            )
        )
    out.append("")
    out.append("---")
    out.append("")
    out.append(
        "*Generated by CI from `games-manifest.json` — do not edit by hand. "
        "Machine-readable: [`supported-games.json`](supported-games.json).*"
    )
    out.append("")
    return "\n".join(out)


def write_outputs(manifest, out_dir, generated_utc):
    games = project(manifest)
    payload = build_json(games, generated_utc)
    badge = build_badge(games)
    md = build_markdown(games, generated_utc)

    def write(name, content):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        return path

    write("supported-games.json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    write("badge.json", json.dumps(badge, indent=2, ensure_ascii=False) + "\n")
    write("SUPPORTED-GAMES.md", md)
    return payload


FIXTURE = {
    "schemaVersion": 1,
    "games": [
        {
            "id": "elden-ring",
            "name": "ELDEN RING",
            "engine": "fromsoft",
            "modPath": "mod",
            "nexusDomain": "eldenring",
            "featured": 3,
            "stores": {"steamAppId": "1245620"},
        },
        {
            "id": "baldurs-gate-3",
            "name": "Baldur's Gate 3",
            "nexusDomain": "baldursgate3",
            "stores": {"steamAppId": "1086940"},
        },
        {
            # Both save facts, and the only rung an ordered tier would have got right.
            "id": "palworld",
            "name": "Palworld",
            "engine": "ue-pak",
            "modPath": "Pal/Content/Paks",
            "nexusDomain": "palworld",
            "saveLayout": "worlds",
            "savePlayerPaths": ["**/Players/**"],
            "stores": {"steamAppId": "1623730"},
        },
        {
            # THE case that killed the single ordered tier: a seam with no layout, so
            # shareable WITHOUT per-save. A ladder would have to claim per-save here, which
            # nobody has checked.
            "id": "windrose",
            "name": "Windrose",
            "engine": "ue-pak",
            "modPath": "mods",
            "savePlayerPaths": ["**/Accounts/**"],
            "stores": {},
        },
        {
            # A save fact on a NEXUS-ONLY game. Stellaris is exactly this on the real feed,
            # so the nexus-only table has to carry the column or the fact leaves the page.
            "id": "stellaris",
            "name": "Stellaris",
            "nexusDomain": "stellaris",
            "saveLayout": "worlds",
            "stores": {"steamAppId": "281990"},
        },
        {
            "id": "no-steam-game",
            "name": "A Shopless Game",
            "engine": "custom",
            "modPath": "mods",
            "stores": {},
        },
    ],
}


def self_test():
    games = project(FIXTURE)
    payload = build_json(games, "2026-01-01T00:00:00Z")
    badge = build_badge(games)
    md = build_markdown(games, "2026-01-01T00:00:00Z")

    assert payload["counts"] == {
        "total": 6, "engineCurated": 4, "nexusOnly": 2,
        "savesPerSave": 2, "savesShareable": 2,
    }, payload["counts"]
    assert badge["message"] == "6" and badge["color"] == BADGE_COLOR

    by_id = {g["id"]: g for g in games}
    er = by_id["elden-ring"]
    assert er["tier"] == ENGINE_CURATED and er["featured"] == 3
    assert er["steamUrl"] == "https://store.steampowered.com/app/1245620/"
    assert er["nexusUrl"] == "https://www.nexusmods.com/eldenring"

    bg3 = by_id["baldurs-gate-3"]
    assert bg3["tier"] == NEXUS_ONLY
    assert "engine" not in bg3 and "featured" not in bg3, "optional fields must be OMITTED"

    shopless = by_id["no-steam-game"]
    assert "steamAppId" not in shopless and "steamUrl" not in shopless and "nexusUrl" not in shopless

    # --- saves: two independent fields, never an ordered tier ---------------------------
    pal = by_id["palworld"]
    assert pal["saveGranularity"] == "per-save" and pal["saveShareable"] is True

    # The case the ladder got wrong: shareable is NOT allowed to imply per-save.
    wind = by_id["windrose"]
    assert wind["saveShareable"] is True
    assert "saveGranularity" not in wind, "shareable must not imply a layout nobody checked"

    # ...and neither does per-save imply a seam.
    stel = by_id["stellaris"]
    assert stel["saveGranularity"] == "per-save"
    assert "saveShareable" not in stel, "a layout must not imply a curated player seam"

    # Unestablished means ABSENT, not false: null in the manifest means nobody has checked.
    assert "saveGranularity" not in er and "saveShareable" not in er

    assert saves_cell(pal) == "per-save · shareable"
    assert saves_cell(wind) == "shareable"
    assert saves_cell(stel) == "per-save"
    assert saves_cell(er) == "backup"

    # ordering: sorted by name casefold, so ELDEN RING sits between Baldur's and Palworld
    assert [g["id"] for g in games] == [
        "no-steam-game", "baldurs-gate-3", "elden-ring", "palworld", "stellaris", "windrose",
    ]

    assert "## Featured" in md and "3. **ELDEN RING** — fromsoft" in md
    assert "| ELDEN RING | `fromsoft` | `mod` | backup |" in md
    assert "| Palworld | `ue-pak` | `Pal/Content/Paks` | per-save · shareable |" in md
    assert "| Windrose | `ue-pak` | `mods` | shareable |" in md
    assert "no-steam-game" not in md  # ids aren't rendered; names are
    assert "| A Shopless Game | `custom` | `mods` | backup | — | — |" in md

    # A save fact on a nexus-only game reaches the page. Dropping the column from that
    # table would have taken Stellaris's curated layout off the surface entirely.
    assert "| Stellaris | per-save | [Steam]" in md
    assert "| Baldur's Gate 3 | backup | [Steam]" in md
    print("self-test: OK (all assertions passed)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", nargs="?", default="games-manifest.json")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--generated-utc", default=os.environ.get("SOURCE_DATE"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    if not args.generated_utc:
        sys.exit("--generated-utc (or SOURCE_DATE env) is required for generation")

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    payload = write_outputs(manifest, args.out_dir, args.generated_utc)
    c = payload["counts"]
    print(
        f"generated: {c['total']} games ({c['engineCurated']} engine-curated, "
        f"{c['nexusOnly']} nexus-only) -> SUPPORTED-GAMES.md, supported-games.json, badge.json"
    )


if __name__ == "__main__":
    main()
