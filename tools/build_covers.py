#!/usr/bin/env python3
"""Associa os jogos do catálogo às capas públicas do Libretro.

O catálogo é gerado pelo build_catalog.py e pode mudar quando novas ROMs
entram no repositório. Este script mantém o covers.json atualizado sem
baixar imagens: o site carrega as capas diretamente do servidor Libretro.

Uso:
    python3 tools/build_covers.py --catalog roms.json --output covers.json
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

THUMBNAILS = "https://thumbnails.libretro.com"
CORE_TO_LIBRETRO = {
    "mgba": "Nintendo - Game Boy Advance",
    "mupen64plus_next": "Nintendo - Nintendo 64",
    "snes9x": "Nintendo - Super Nintendo Entertainment System",
    "genesis_plus_gx": "Sega - Mega Drive - Genesis",
    "smsplus": "Sega - Master System - Mark III",
    "gambatte": "Nintendo - Game Boy",
    "fceumm": "Nintendo - Nintendo Entertainment System",
    "nestopia": "Nintendo - Nintendo Entertainment System",
    "mednafen_pce": "NEC - PC Engine - TurboGrafx 16",
    "mednafen_wswan": "Bandai - WonderSwan",
}

# Títulos que o catálogo abrevia ou que são hacks de um jogo comercial.
ALIASES = {
    "007 GoldenEye": "GoldenEye 007",
    "Paper Mario 64": "Paper Mario",
    "The Legend of Zelda - Majora's Mask": "Legend of Zelda, The - Majora's Mask",
    "The Legend of Zelda - Ocarina of Time": "Legend of Zelda, The - Ocarina of Time",
    "Ninja Five-0": "Ninja Five-O",
    "Sim City 2000": "SimCity 2000",
    "Space Station Silicon Valley": "SpaceStation Silicon Valley",
    "The Powerpuff Girls - Mojo Jojo A-Go-Go": "Powerpuff Girls, The - Mojo Jojo A-Go-Go",
    "Disney’s Pinocchio": "Pinocchio",
    "Moemon - Fire Red": "Pokemon - FireRed Version",
    "Moemon Emerald": "Pokemon - Emerald Version",
    "Moemon Ruby": "Pokemon - Ruby Version",
    "Pokemon - AshGray 4.5.3": "Pokemon - FireRed Version",
    "Pokemon - Fire Red Version (Rev 1)": "Pokemon - FireRed Version",
    "Pokemon - Water Blue": "Pokemon - LeafGreen Version",
    "Pokemon Omega Ruby v1.8": "Pokemon - Ruby Version",
    "Pokemon Resolute Version": "Pokemon - Ruby Version",
    "Pokemon Ribeirao Pires": "Pokemon - Emerald Version",
    "Pokemon Stone Dragon": "Pokemon - Emerald Version",
    "Pokemon Dark Fire": "Pokemon - FireRed Version",
    "Pokemon Dark Pearl": "Pokemon - Pearl Version",
    "Pokemon Volcano": "Pokemon - FireRed Version",
    "Pokemon Shadow Force": "Pokemon - FireRed Version",
    "Pokemon New Hoenn": "Pokemon - Ruby Version",
    "Pokemon Light Platinum (BR)": "Pokemon - Ruby Version",
    "Pokemon Lunares BR": "Pokemon - Emerald Version",
    "Pokemon Quetzal Pt-Br Alpha 9v1": "Pokemon - Emerald Version",
    "Moemon Quetzal Pt-Br Alpha 9v1": "Pokemon - Emerald Version",
    "Pokémon Legendary": "Pokemon - FireRed Version",
}

REGION_PRIORITY = ("(usa", "(europe", "(japan", "(world", "(usa, europe")


def normalize(value: str) -> str:
    value = urllib.parse.unquote(value)
    value = re.sub(
        r"\.(png|gba|agb|z64|n64|v64|sfc|smc|md|gen|smd|bin|sms|gg|sg)$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", value)
    value = value.replace("&", " ")
    value = re.sub(r"\b(the|and)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return " ".join(value.split())


def normalize_compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize(value))


def region_rank(filename: str) -> tuple[int, int]:
    lowered = filename.lower()
    for index, region in enumerate(REGION_PRIORITY):
        if region in lowered:
            return index, len(filename)
    return len(REGION_PRIORITY), len(filename)


def fetch_boxarts(core: str) -> list[str]:
    system = CORE_TO_LIBRETRO.get(core)
    if not system:
        return []
    url = f"{THUMBNAILS}/{urllib.parse.quote(system)}/Named_Boxarts/"
    with urllib.request.urlopen(url, timeout=120) as response:
        page = response.read().decode("utf-8", "replace")
    return [
        urllib.parse.unquote(html.unescape(item))
        for item in re.findall(r'href="([^"]+\.png)"', page)
    ]


def find_cover(name: str, filenames: list[str]) -> str | None:
    target = ALIASES.get(name, name)
    normalized = normalize(target)
    compact = normalize_compact(target)

    matches = [item for item in filenames if normalize(item) == normalized]
    if not matches:
        matches = [item for item in filenames if normalize_compact(item) == compact]
    if not matches:
        # Alguns jogos têm pequenas diferenças de pontuação; só aceita
        # aproximações muito próximas para não trocar a capa por outro jogo.
        candidates = difflib.get_close_matches(
            normalized,
            [normalize(item) for item in filenames],
            n=3,
            cutoff=0.94,
        )
        if candidates:
            matches = [
                item
                for item in filenames
                if normalize(item) in candidates
            ]
    if not matches:
        return None

    matches.sort(key=region_rank)
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="roms.json")
    parser.add_argument("--output", default="covers.json")
    args = parser.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    games = catalog["games"]
    by_core: dict[str, list[str]] = {}
    for game in games:
        by_core.setdefault(game["core"], [])
        if game["name"] not in by_core[game["core"]]:
            by_core[game["core"]].append(game["name"])

    indexes = {core: fetch_boxarts(core) for core in by_core}
    covers: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    for game in games:
        filename = find_cover(game["name"], indexes.get(game["core"], []))
        if filename is None:
            missing.append(game["name"])
            continue
        system = CORE_TO_LIBRETRO[game["core"]]
        covers.setdefault(game["core"], {})[game["name"]] = (
            f"{THUMBNAILS}/{urllib.parse.quote(system)}/Named_Boxarts/"
            f"{urllib.parse.quote(filename)}"
        )

    Path(args.output).write_text(
        json.dumps(covers, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    found = sum(len(items) for items in covers.values())
    print(f"Capas encontradas: {found}/{len(games)}")
    if missing:
        print(f"Sem capa ({len(missing)}): {', '.join(missing[:20])}")


if __name__ == "__main__":
    main()
