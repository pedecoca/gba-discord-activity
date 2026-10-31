#!/usr/bin/env python3
"""Aplica as URLs do GitHub Release ao catálogo e lista o que não copiar.

Os arquivos de PS1 grandes ficam em ``psx_release.json``. O Pages precisa
publicar o CUE do Release, mas não pode copiar BINs de centenas de MB para
dentro do site. Este script:

* troca a URL dos CUEs do catálogo pela URL do proxy ``api.pokedc.online``;
* cria entradas de catálogo para jogos que não estão no checkout do CI;
* grava a lista de arquivos locais que devem ser ignorados na cópia.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("dist/roms.json"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("psx_release.json"),
    )
    parser.add_argument(
        "--skip-output",
        type=Path,
        default=Path("dist/release-skip.json"),
    )
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    games = catalog.get("games")
    if not isinstance(games, list):
        raise SystemExit("roms.json inválido: falta a lista games.")

    proxy_base = str(manifest.get("proxy_base", "")).strip().rstrip("/")
    if not proxy_base:
        raise SystemExit("psx_release.json inválido: falta proxy_base.")

    files = {
        str(item["path"]): str(item["asset"])
        for item in manifest.get("files", [])
        if isinstance(item, dict) and item.get("path") and item.get("asset")
    }

    prefix = "./roms/"
    por_caminho: dict[str, dict] = {}
    por_nome: dict[str, dict] = {}
    for game in games:
        url = game.get("url", "")
        if isinstance(url, str) and url.startswith(prefix):
            relativo = unquote(url[len(prefix):])
            por_caminho[relativo] = game
        nome = str(game.get("name", ""))
        if nome:
            por_nome[nome] = game

    for item in manifest.get("games", []):
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", ""))
        asset = str(item.get("asset", "")) or files.get(path, "")
        if not path or not asset:
            continue

        url = f"{proxy_base}/{quote(asset, safe='')}"
        nome = str(item.get("name") or PurePosixPath(path).stem)
        # Primeiro procura pelo caminho local; se o catálogo já foi
        # processado antes, procura pelo nome para não duplicar o jogo.
        game = por_caminho.get(path) or por_nome.get(nome)
        if game is None:
            game = {
                "name": nome,
                "url": url,
                "core": str(item.get("core") or "pcsx_rearmed"),
            }
            games.append(game)
            por_caminho[path] = game
            por_nome[nome] = game
        else:
            game["url"] = url
            if item.get("name"):
                game["name"] = str(item["name"])
            if item.get("core"):
                game["core"] = str(item["core"])

    games.sort(key=lambda game: str(game.get("name", "")).casefold())
    args.catalog.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    skip = sorted(files)
    args.skip_output.parent.mkdir(parents=True, exist_ok=True)
    args.skip_output.write_text(
        json.dumps(skip, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Release aplicado: {len(manifest.get('games', []))} jogo(s) PS1; "
        f"{len(skip)} arquivo(s) ignorado(s) na cópia."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
