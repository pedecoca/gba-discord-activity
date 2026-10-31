#!/usr/bin/env python3
"""Baixa capas ausentes do Libretro e atualiza o covers.json local.

Diferente de ``build_covers.py`` (que cria URLs remotas), este script
salva as imagens em ``asset/covers`` para que o Discord Activity não precise
carregar imagens de domínios externos. Capas já existentes são preservadas.

Uso no CI, depois de gerar ``dist/roms.json`` e copiar ``dist/asset``::

    python3 tools/sync_missing_covers.py \
        --catalog dist/roms.json \
        --covers dist/covers.json \
        --asset-dir dist/asset/covers \
        --core melonds
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_covers import CORE_TO_LIBRETRO, THUMBNAILS, fetch_boxarts, find_cover
from download_covers import baixar_e_otimizar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="roms.json")
    parser.add_argument("--covers", default="covers.json")
    parser.add_argument("--asset-dir", default="asset/covers")
    parser.add_argument(
        "--core",
        action="append",
        dest="cores",
        help="Processa apenas este core (pode repetir). Padrão: todos.",
    )
    args = parser.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    covers_path = Path(args.covers)
    if covers_path.is_file():
        covers = json.loads(covers_path.read_text(encoding="utf-8"))
    else:
        covers = {}
    if not isinstance(covers, dict):
        raise SystemExit(f"{covers_path} não contém um objeto JSON.")

    asset_dir = Path(args.asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)
    filtro = set(args.cores or [])
    indexes: dict[str, list[str]] = {}
    adicionadas = 0

    for game in catalog.get("games", []):
        core = game.get("core")
        nome = game.get("name")
        if not core or not nome:
            continue
        if filtro and core not in filtro:
            continue
        if covers.get(core, {}).get(nome):
            continue
        if core not in CORE_TO_LIBRETRO:
            continue

        if core not in indexes:
            indexes[core] = fetch_boxarts(core)
        filename = find_cover(nome, indexes[core])
        if filename is None:
            print(f"Sem capa: {core} / {nome}")
            continue

        sistema = CORE_TO_LIBRETRO[core]
        url = (
            f"{THUMBNAILS}/{urllib.parse.quote(sistema)}/Named_Boxarts/"
            f"{urllib.parse.quote(filename)}"
        )
        chave = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        destino = asset_dir / f"{chave}.webp"
        try:
            baixar_e_otimizar(url, destino)
        except Exception as erro:  # noqa: BLE001 - uma capa não deve travar o deploy
            print(f"Falha ao baixar capa de {nome}: {erro}")
            continue
        if not destino.is_file():
            print(f"Capa vazia: {core} / {nome}")
            continue
        try:
            caminho_relativo = destino.relative_to(covers_path.parent)
        except ValueError:
            caminho_relativo = destino
        covers.setdefault(core, {})[nome] = f"./{caminho_relativo.as_posix()}"
        adicionadas += 1

    temporario = covers_path.with_suffix(".json.tmp")
    temporario.write_text(
        json.dumps(covers, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.move(temporario, covers_path)
    print(f"Capas novas: {adicionadas}")


if __name__ == "__main__":
    main()
