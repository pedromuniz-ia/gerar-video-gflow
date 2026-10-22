"""Junta as tomadas num vídeo 9:16 e põe a legenda (.srt), só com o ffmpeg.

Uso:
  python montar.py --plano plano.json --saida final.mp4 [--estilo amarelo_pop|classico|nenhum]
                   [--posicao 0.70]

``plano.json`` é uma lista, na ordem do vídeo:
  [{"arquivo": "cenas/01/tomada-a/x.mp4", "fala": "texto dito", "fim": 7.4}, ...]
- ``fim`` (opcional): corta a tomada nesse segundo (tire o silêncio do fim de cada take).
- ``inicio`` (opcional): pula o começo da tomada.

Grava ``final.srt`` ao lado (blocos curtos, com o tempo de cada fala repartido pelas
palavras) e, com estilo, queima a legenda no vídeo. ``--estilo nenhum`` entrega sem legenda
queimada (o .srt continua ao lado). Fontes em ``fontes/`` (licença OFL).
Só Python 3.12 padrão e ffmpeg/ffprobe no PATH.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FONTES = Path(__file__).resolve().parents[1] / "fontes"
#: O libass mede a legenda de um .srt numa tela de 288 linhas, qualquer que seja o vídeo.
ALTURA_ASS = 288
#: Estilos de legenda (fontes livres em fontes/, licença OFL).
ESTILOS = {
    "amarelo_pop": {"fonte": "Anton", "tamanho": 0.056, "palavras": 3, "caixa_alta": True,
                    "cor": "&H00FFFFFF", "contorno": 5, "sombra": 2},
    "classico": {"fonte": "Montserrat ExtraBold", "tamanho": 0.05, "palavras": 6,
                      "caixa_alta": False, "cor": "&H00FFFFFF", "contorno": 0, "sombra": 3},
}  # fmt: skip


def duracao(video: Path) -> float:
    feito = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    return float(feito.stdout.strip())


def tempo_srt(s: float) -> str:
    ms = round(s * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def blocos_srt(trechos: list[tuple[float, float, str]], por_bloco: int, caixa_alta: bool) -> str:
    """Cada trecho (início, fim, fala) vira blocos de ``por_bloco`` palavras, com o tempo
    repartido pelo número de letras (palavra longa fica mais tempo na tela)."""
    saida, n = [], 1
    for inicio, fim, fala in trechos:
        palavras = fala.upper().split() if caixa_alta else fala.split()
        if not palavras:
            continue
        letras = sum(len(p) for p in palavras)
        t = inicio
        for i in range(0, len(palavras), por_bloco):
            grupo = palavras[i : i + por_bloco]
            fim_bloco = t + (fim - inicio) * sum(len(p) for p in grupo) / letras
            saida.append(f"{n}\n{tempo_srt(t)} --> {tempo_srt(fim_bloco)}\n{' '.join(grupo)}\n")
            n, t = n + 1, fim_bloco
    return "\n".join(saida)


def normalizar(item: dict, destino: Path) -> float:
    """Corta e converte a tomada para 1080x1920, 30 fps, AAC 48 kHz; devolve a duração."""
    origem = Path(item["arquivo"])
    inicio = float(item.get("inicio") or 0)
    fim = float(item.get("fim") or duracao(origem))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{inicio}", "-to", f"{fim}", "-i", str(origem),
         "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
         "-af", "aresample=48000", "-ac", "2", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(destino)],
        check=True,
    )  # fmt: skip
    return duracao(destino)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--plano", type=Path, required=True)
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--estilo", default="amarelo_pop", choices=[*ESTILOS, "nenhum"])
    p.add_argument("--posicao", type=float, default=0.70, help="altura da legenda (0 topo, 1 base)")
    a = p.parse_args(argv)
    if not shutil.which("ffmpeg"):
        sys.exit("instale o ffmpeg (reference/instalar.md)")
    plano = json.loads(a.plano.read_text(encoding="utf-8"))
    estilo = ESTILOS.get(a.estilo, ESTILOS["amarelo_pop"])
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        trechos, t = [], 0.0
        lista = pasta / "lista.txt"
        with lista.open("w", encoding="utf-8") as arquivo:
            for i, item in enumerate(plano):
                parte = pasta / f"p{i:03d}.mp4"
                d = normalizar(item, parte)
                trechos.append((t, t + d, item.get("fala", "")))
                t += d
                arquivo.write(f"file '{parte.name}'\n")
        junto = pasta / "junto.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista.name,
             "-c", "copy", junto.name],
            check=True, cwd=pasta,
        )  # fmt: skip
        srt = a.saida.with_suffix(".srt")
        srt.write_text(
            blocos_srt(trechos, estilo["palavras"], estilo["caixa_alta"]), encoding="utf-8"
        )
        if a.estilo == "nenhum":
            shutil.copyfile(junto, a.saida)
        else:
            shutil.copyfile(srt, pasta / "legenda.srt")
            for fonte in FONTES.glob("*.ttf"):
                shutil.copyfile(fonte, pasta / fonte.name)
            forca = (
                f"FontName={estilo['fonte']},Fontsize={round(ALTURA_ASS * estilo['tamanho'])},"
                f"PrimaryColour={estilo['cor']},OutlineColour=&H00000000,BorderStyle=1,"
                f"Outline={estilo['contorno'] / 2},Shadow={estilo['sombra'] / 2},Alignment=2,"
                f"MarginV={round(ALTURA_ASS * (1 - a.posicao))}"
            )
            # Caminhos relativos e cwd na pasta: o filtro subtitles não lida com "C:\" no Windows.
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", junto.name, "-vf",
                 f"subtitles=legenda.srt:fontsdir=.:force_style='{forca}'", "-c:v", "libx264",
                 "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "copy",
                 "final.mp4"],
                check=True, cwd=pasta,
            )  # fmt: skip
            shutil.copyfile(pasta / "final.mp4", a.saida)
    print(json.dumps({"arquivo": str(a.saida.resolve()), "srt": str(srt.resolve()),
                      "duracao_s": round(duracao(a.saida), 2), "tomadas": len(plano)},
                     ensure_ascii=False))  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
