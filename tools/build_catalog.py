#!/usr/bin/env python3
"""Gera o catálogo ``roms.json`` da Discord Activity a partir da pasta ``rom/``.

O repositório pedecoca/EmulatorJS guarda as ROMs de forma "plana"
(``rom/Jogo.gba``) e também aceita subpastas por core (``rom/mgba/Jogo.gba``).
Este script resolve o core de cada arquivo usando, nesta ordem:

1. subpasta igual ao id do core (``rom/mgba/...``) ou a um alias conhecido
   (``rom/gba/...``, ``rom/n64/...``);
2. extensão do arquivo, quando apenas um sistema do ``systems.json`` a usa;
3. extensão ambígua + ``PREFERRED_CORE_BY_EXTENSION`` (ex.: ``.z64`` -> N64);
4. conteúdo do arquivo (magic bytes) quando não há extensão.

Uso no CI (baixa as ROMs para ``dist/roms``)::

    python3 tools/build_catalog.py --download-to dist/roms --output dist/roms.json

Uso local (não baixa nada, só gera o catálogo)::

    python3 tools/build_catalog.py --local-rom-dir ../EmulatorJS/rom \
        --output roms.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

USER_AGENT = "gba-discord-activity-catalog"

# Extensões que mais de um sistema do systems.json reivindica.
PREFERRED_CORE_BY_EXTENSION = {
    ".z64": "mupen64plus_next",
    ".n64": "mupen64plus_next",
    ".v64": "mupen64plus_next",
    ".nds": "melonds",
    ".gba": "mgba",
    ".agb": "mgba",
    ".gb": "gambatte",
    ".gbc": "gambatte",
    ".dmg": "gambatte",
    ".sgb": "gambatte",
    ".nes": "fceumm",
    ".fds": "fceumm",
    ".sfc": "snes9x",
    ".smc": "snes9x",
    ".md": "genesis_plus_gx",
    ".gen": "genesis_plus_gx",
    ".smd": "genesis_plus_gx",
    ".sms": "smsplus",
    ".gg": "smsplus",
    ".pce": "mednafen_pce",
    ".ws": "mednafen_wswan",
    ".wsc": "mednafen_wswan",
    ".ngp": "mednafen_ngp",
    ".ngc": "mednafen_ngp",
    ".vb": "beetle_vb",
    ".lnx": "handy",
    ".a26": "stella2014",
    ".a52": "a5200",
    ".a78": "prosystem",
    ".col": "gearcoleco",
    ".j64": "virtualjaguar",
    ".jag": "virtualjaguar",
    ".adf": "puae",
    ".d64": "vice_x64",
    ".g64": "vice_x64",
    ".t64": "vice_x64",
    ".prg": "vice_x64",
    ".crt": "vice_x64",
    ".dsk": "cap32",
    ".cpr": "cap32",
    ".dosz": "dosbox_pure",
    ".pbp": "pcsx_rearmed",
}

# Pastas aceitas em rom/<pasta>/...
CORE_ALIASES = {
    "gba": "mgba",
    "gb": "gambatte",
    "gbc": "gambatte",
    "nes": "fceumm",
    "famicom": "fceumm",
    "snes": "snes9x",
    "supernintendo": "snes9x",
    "n64": "mupen64plus_next",
    "ps1": "pcsx_rearmed",
    "psx": "pcsx_rearmed",
    "playstation": "pcsx_rearmed",
    "genesis": "genesis_plus_gx",
    "megadrive": "genesis_plus_gx",
    "mega-drive": "genesis_plus_gx",
    "sms": "smsplus",
    "mastersystem": "smsplus",
    "master-system": "smsplus",
    "gg": "smsplus",
    "gamegear": "smsplus",
    "saturn": "yabause",
    "dreamcast": "yabause",  # não suportado pelo EmulatorJS; cai no aviso
    "arcade": "fbneo",
    "mame": "mame2003_plus",
    "pce": "mednafen_pce",
    "pcengine": "mednafen_pce",
    "wonderswan": "mednafen_wswan",
    "ngp": "mednafen_ngp",
    "neogeopocket": "mednafen_ngp",
    "vb": "beetle_vb",
    "virtualboy": "beetle_vb",
    "lynx": "handy",
    "atari2600": "stella2014",
    "atari7800": "prosystem",
    "atari5200": "a5200",
    "coleco": "gearcoleco",
    "colecovision": "gearcoleco",
    "c64": "vice_x64",
    "amiga": "puae",
    "dos": "dosbox_pure",
    "jaguar": "virtualjaguar",
    "3do": "opera",
    "cdi": "same_cdi",
    "zx": "fuse",
    "spectrum": "fuse",
    "cpc": "cap32",
    "nds": "melonds",
    "ds": "melonds",
}

# Sistema detectado pelos magic bytes quando o arquivo não tem extensão.
SNIFFED_SYSTEM_CORE = {
    "n64": "mupen64plus_next",
    "gba": "mgba",
    "snes": "snes9x",
    "zip": None,  # ambíguo demais (arcade/DOS/Amiga)
}

N64_MAGIC = {
    b"\x80\x37\x12\x40": "n64",  # .z64 (big endian)
    b"\x37\x80\x40\x12": "n64",  # .v64 (byteswapped)
    b"\x40\x12\x37\x80": "n64",  # .n64 (little endian)
}

VALID_EXTENSION = re.compile(r"\.[a-z0-9]+")


class CatalogError(RuntimeError):
    pass


def load_systems(path: Path) -> list[dict]:
    systems = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(systems, list) or not systems:
        raise CatalogError(f"{path} não contém uma lista de sistemas.")
    seen: set[str] = set()
    for system in systems:
        core = system.get("id")
        if not isinstance(core, str) or not re.fullmatch(r"[a-z0-9_]+", core):
            raise CatalogError(f"Id de core inválido em {path}: {core!r}")
        if core in seen:
            raise CatalogError(f"Core duplicado em {path}: {core}")
        seen.add(core)
    return systems


def build_extension_owners(systems: Iterable[dict]) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for system in systems:
        for extension in system.get("extensions", []):
            if not isinstance(extension, str) or not VALID_EXTENSION.fullmatch(extension):
                raise CatalogError(f"Extensão inválida em {system['id']}: {extension!r}")
            owners.setdefault(extension, []).append(system["id"])
    return owners


def sniff_system(head: bytes) -> str | None:
    """Detecta o sistema pelos primeiros bytes do arquivo (sem extensão)."""
    if len(head) >= 4 and head[:4] in N64_MAGIC:
        return N64_MAGIC[head[:4]]
    if len(head) >= 0xB4 and head[0xB2] == 0x96 and head[0xB3] == 0x00:
        return "gba"
    if len(head) >= 4 and head[:4] == b"PK\x03\x04":
        return "zip"
    if len(head) >= 0x7FE and head[0x7FC:0x7FE] == b"\xAA\xBB":
        return "snes"
    return None


def resolve_core(
    rom_path: str,
    systems_by_id: dict[str, dict],
    extension_owners: dict[str, list[str]],
    head_reader: Callable[[str], bytes] | None,
) -> tuple[str | None, str]:
    """Retorna ``(core, motivo)``; ``core`` é ``None`` quando não dá para decidir."""
    parts = rom_path.split("/")
    if len(parts) < 2 or parts[0] != "rom":
        return None, "fora da pasta rom/"
    if any(part in ("", ".", "..") or "\\" in part for part in parts):
        return None, "caminho inválido"

    if len(parts) > 2:
        folder = parts[1].lower()
        core = folder if folder in systems_by_id else CORE_ALIASES.get(folder)
        if core in systems_by_id:
            return core, f"pasta {parts[1]}/"

    extension = PurePosixPath(parts[-1]).suffix.lower()
    if extension:
        owners = extension_owners.get(extension, [])
        if len(owners) == 1:
            return owners[0], f"extensão {extension}"
        preferred = PREFERRED_CORE_BY_EXTENSION.get(extension)
        if preferred and preferred in owners:
            return preferred, f"extensão {extension} (preferido)"
        if owners:
            return None, f"extensão {extension} ambígua ({', '.join(owners)})"
        return None, f"extensão {extension} sem sistema"

    if head_reader is None:
        return None, "sem extensão"
    try:
        head = head_reader(rom_path)
    except Exception as error:  # rede/arquivo: apenas ignora
        return None, f"sem extensão e falha ao ler cabeçalho ({error})"
    sniffed = sniff_system(head)
    if sniffed is None:
        return None, "sem extensão e cabeçalho desconhecido"
    core = SNIFFED_SYSTEM_CORE.get(sniffed)
    if core is None:
        return None, f"cabeçalho {sniffed} ambíguo"
    return core, f"cabeçalho {sniffed}"


def quote_path(path: str) -> str:
    return "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))


def fetch_github_tree(repo: str, branch: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("truncated"):
        raise CatalogError("GitHub retornou uma listagem incompleta da pasta rom/.")
    tree = data.get("tree")
    if not isinstance(tree, list):
        raise CatalogError("GitHub não retornou a árvore de arquivos.")
    return tree


def fetch_github_head(repo: str, branch: str) -> Callable[[str], bytes]:
    def reader(rom_path: str) -> bytes:
        url = (
            f"https://raw.githubusercontent.com/{repo}/{branch}/{quote_path(rom_path)}"
        )
        request = urllib.request.Request(
            url, headers={"Range": "bytes=0-1023", "User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(1024)

    return reader


def download_github_blob(repo: str, branch: str, rom_path: str, destination: Path) -> None:
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{quote_path(rom_path)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=180) as response:
        destination.write_bytes(response.read())


def build_catalog(
    rom_paths: Iterable[str],
    systems: list[dict],
    head_reader: Callable[[str], bytes] | None,
    downloader: Callable[[str], None] | None = None,
    url_base: str = "./roms/",
) -> tuple[list[dict], list[tuple[str, str]]]:
    if not url_base.endswith("/"):
        url_base += "/"
    systems_by_id = {system["id"]: system for system in systems}
    extension_owners = build_extension_owners(systems)
    games: list[dict] = []
    skipped: list[tuple[str, str]] = []

    for rom_path in sorted(rom_paths, key=str.casefold):
        core, reason = resolve_core(rom_path, systems_by_id, extension_owners, head_reader)
        if core is None:
            skipped.append((rom_path, reason))
            continue

        relative = rom_path.split("/")[1:]
        if downloader is not None:
            downloader(rom_path)

        games.append(
            {
                "name": PurePosixPath(relative[-1]).stem,
                "url": url_base + quote_path("/".join(relative)),
                "core": core,
            }
        )

    games.sort(key=lambda game: game["name"].casefold())
    return games, skipped


def collect_local_rom_paths(rom_dir: Path) -> list[str]:
    paths: list[str] = []
    for path in rom_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(rom_dir).as_posix()
            paths.append(f"rom/{relative}")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--systems", type=Path, default=Path("systems.json"))
    parser.add_argument("--output", type=Path, default=Path("roms.json"))
    parser.add_argument("--download-to", type=Path, default=None)
    parser.add_argument("--repo", default="pedecoca/EmulatorJS")
    parser.add_argument("--branch", default="main")
    parser.add_argument(
        "--url-base",
        default="./roms/",
        help="Prefixo das URLs do catálogo (use uma URL absoluta do GitHub para não baixar ROMs).",
    )
    parser.add_argument(
        "--local-rom-dir",
        type=Path,
        default=None,
        help="Usa uma pasta rom/ local em vez da API do GitHub.",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    systems = load_systems(args.systems)

    if args.local_rom_dir is not None:
        rom_dir = args.local_rom_dir.resolve()
        if not rom_dir.is_dir():
            raise CatalogError(f"Pasta de ROMs não encontrada: {rom_dir}")
        rom_paths = collect_local_rom_paths(rom_dir)

        def head_reader(rom_path: str) -> bytes:
            relative = rom_path.split("/", 1)[1]
            with (rom_dir / relative).open("rb") as handle:
                return handle.read(1024)

        downloader = None
    else:
        tree = fetch_github_tree(args.repo, args.branch)
        rom_paths = [
            item["path"]
            for item in tree
            if item.get("type") == "blob" and item.get("path", "").startswith("rom/")
        ]
        head_reader = fetch_github_head(args.repo, args.branch)

        def downloader(rom_path: str, *, _dest: Path | None = args.download_to) -> None:
            if _dest is None:
                return
            relative = rom_path.split("/", 1)[1]
            download_github_blob(args.repo, args.branch, rom_path, _dest / relative)

    games, skipped = build_catalog(
        rom_paths, systems, head_reader, downloader, url_base=args.url_base
    )

    if not games:
        raise CatalogError("Nenhuma ROM válida encontrada; o catálogo ficaria vazio.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"games": games}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if not args.quiet:
        by_core: dict[str, int] = {}
        for game in games:
            by_core[game["core"]] = by_core.get(game["core"], 0) + 1
        print(f"{len(games)} jogo(s) no catálogo -> {args.output}")
        for core, count in sorted(by_core.items(), key=lambda item: item[1], reverse=True):
            print(f"  {core:24} {count}")
        if skipped:
            reasons: dict[str, int] = {}
            for _, reason in skipped:
                reasons[reason] = reasons.get(reason, 0) + 1
            print(f"{len(skipped)} arquivo(s) ignorado(s):")
            for reason, count in sorted(reasons.items(), key=lambda item: item[1], reverse=True):
                print(f"  {count:3}  {reason}")
            for path, reason in skipped[:10]:
                print(f"  - {path} ({reason})")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CatalogError as error:
        print(f"erro: {error}", file=sys.stderr)
        sys.exit(1)
