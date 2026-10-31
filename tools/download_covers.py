#!/usr/bin/env python3
"""Baixa e otimiza as capas para serem servidas pelo próprio site.

O Discord Activity pode bloquear imagens de domínios externos. Por isso,
este script baixa as capas do Libretro, redimensiona para um tamanho de
cartão e grava tudo em ``asset/covers/``, atualizando o ``covers.json`` para
usar caminhos locais.

Uso:
    ../bot/.venv/bin/python tools/download_covers.py
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def baixar_e_otimizar(url: str, destino: Path) -> bool:
    if destino.is_file() and destino.stat().st_size > 0:
        return True

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as resposta:
        dados = resposta.read()
    if not dados:
        return False

    with Image.open(io.BytesIO(dados)) as imagem:
        imagem = ImageOps.exif_transpose(imagem).convert("RGB")
        imagem.thumbnail((240, 320), Image.Resampling.LANCZOS)
        destino.parent.mkdir(parents=True, exist_ok=True)
        imagem.save(destino, "WEBP", quality=80, method=6)
    return destino.is_file() and destino.stat().st_size > 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--covers", default="covers.json")
    parser.add_argument("--asset-dir", default="asset/covers")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    covers_path = Path(args.covers)
    asset_dir = Path(args.asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)

    catalogo = json.loads(covers_path.read_text(encoding="utf-8"))
    tarefas: list[tuple[str, str, str, Path]] = []
    resultados: dict[tuple[str, str], str] = {}
    for core, itens in catalogo.items():
        for nome, url in itens.items():
            if url.startswith(("http://", "https://")):
                chave = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
                destino = asset_dir / f"{chave}.webp"
                tarefas.append((core, nome, url, destino))
            elif url.startswith("./") and Path(url[2:]).is_file():
                resultados[(core, nome)] = url

    falhas: list[tuple[str, str]] = []

    def executar(tarefa: tuple[str, str, str, Path]) -> tuple[str, str, str, Path | None]:
        core, nome, url, destino = tarefa
        try:
            baixar_e_otimizar(url, destino)
            return core, nome, url, destino
        except Exception as erro:  # noqa: BLE001 - registra e segue com as demais
            falhas.append((nome, str(erro)))
            return core, nome, url, None

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futuros = [executor.submit(executar, tarefa) for tarefa in tarefas]
        for indice, futuro in enumerate(as_completed(futuros), start=1):
            core, nome, _url, destino = futuro.result()
            if destino is not None and destino.is_file():
                resultados[(core, nome)] = f"./{asset_dir.as_posix()}/{destino.name}"
            if indice % 25 == 0 or indice == len(tarefas):
                print(f"{indice}/{len(tarefas)} capas processadas")

    atualizado: dict[str, dict[str, str]] = {}
    for core, itens in catalogo.items():
        for nome in itens:
            caminho = resultados.get((core, nome))
            if caminho:
                atualizado.setdefault(core, {})[nome] = caminho

    temporario = covers_path.with_suffix(".json.tmp")
    temporario.write_text(
        json.dumps(atualizado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.move(temporario, covers_path)

    total_bytes = sum(
        Path(caminho[2:]).stat().st_size
        for itens in atualizado.values()
        for caminho in itens.values()
        if Path(caminho[2:]).is_file()
    )
    print(
        f"Capas locais: {sum(len(v) for v in atualizado.values())}/"
        f"{sum(len(v) for v in catalogo.values())} "
        f"({total_bytes / 1024 / 1024:.1f} MB)"
    )
    if falhas:
        print(f"Falhas: {len(falhas)}")
        for nome, erro in falhas[:10]:
            print(f"  - {nome}: {erro}")


if __name__ == "__main__":
    main()
