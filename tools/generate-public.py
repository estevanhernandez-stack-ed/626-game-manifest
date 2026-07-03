#!/usr/bin/env python3
"""Generate the public supported-games surfaces from the built games-manifest.json.

Emits three files (committed by CI on the same rail as the signed manifest, so they can
never drift from it):
  SUPPORTED-GAMES.md   - the human page GitHub renders
  supported-games.json - the stable consumer contract (hub website, Discord bot)
  badge.json           - shields.io endpoint schema (live "N supported games" badge)

Stdlib only. Deterministic: games sorted by name, stable field order, timestamp supplied
by the caller (--generated-utc or SOURCE_DATE env) - the generator never reads the clock.

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


def build_markdown(games, generated_utc):
    curated = [g for g in games if g["tier"] == ENGINE_CURATED]
    nexus_only = [g for g in games if g["tier"] == NEXUS_ONLY]
    featured = sorted(
        (g for g in games if "featured" in g), key=lambda g: g["featured"]
    )

    out = []
    out.append("# Supported games")
    out.append("")
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
    out.append("| Game | Engine | Mod path | Steam | Nexus |")
    out.append("|---|---|---|---|---|")
    for g in curated:
        out.append(
            "| {name} | `{engine}` | `{mod}` | {steam} | {nexus} |".format(
                name=md_escape(g["name"]),
                engine=g.get("engine", ""),
                mod=g.get("modPath", "—"),
                steam=link("Steam", g.get("steamUrl")),
                nexus=link("Nexus", g.get("nexusUrl")),
            )
        )
    out.append("")

    out.append(f"## Nexus-only ({len(nexus_only)})")
    out.append("")
    out.append("| Game | Steam | Nexus |")
    out.append("|---|---|---|")
    for g in nexus_only:
        out.append(
            "| {name} | {steam} | {nexus} |".format(
                name=md_escape(g["name"]),
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

    assert payload["counts"] == {"total": 3, "engineCurated": 2, "nexusOnly": 1}, payload["counts"]
    assert badge["message"] == "3" and badge["color"] == BADGE_COLOR

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

    # ordering: sorted by name casefold -> A Shopless.., Baldur's.., ELDEN RING
    assert [g["id"] for g in games] == ["no-steam-game", "baldurs-gate-3", "elden-ring"]

    assert "## Featured" in md and "3. **ELDEN RING** — fromsoft" in md
    assert "| ELDEN RING | `fromsoft` | `mod` |" in md
    assert "| Baldur's Gate 3 | [Steam]" in md
    assert "no-steam-game" not in md  # ids aren't rendered; names are
    assert "| A Shopless Game | `custom` | `mods` | — | — |" in md
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
