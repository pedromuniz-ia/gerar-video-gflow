"""Tira quadros e o áudio de um vídeo com o ffmpeg, para o agente olhar e ouvir.

Uso:
  python frames.py <video.mp4> --saida <pasta> [--quadros 12] [--em 3.5 7.2] [--audio]

Grava ``q_<segundos>.jpg`` (com o instante no nome), ``audio.mp3`` com ``--audio`` e
``info.json`` (duração, tamanho, se tem áudio). Se o ``whisper`` estiver instalado
(``pip install openai-whisper``), ``--transcrever`` grava ``audio.srt`` e ``audio.txt`` sem
API externa. Sem ele, o agente ouve o ``audio.mp3`` pelo próprio harness.
Só Python 3.12 padrão e ffmpeg/ffprobe no PATH.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def sondar(video: Path) -> dict:
    feito = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    dados = json.loads(feito.stdout)
    fluxos = dados.get("streams", [])
    imagem = next((f for f in fluxos if f.get("codec_type") == "video"), {})
    return {
        "duracao_s": round(float(dados["format"]["duration"]), 2),
        "largura": imagem.get("width"),
        "altura": imagem.get("height"),
        "tem_audio": any(f.get("codec_type") == "audio" for f in fluxos),
    }


def instantes(duracao: float, quantos: int) -> list[float]:
    """Instantes no meio de partes iguais: nunca o primeiro quadro preto nem o último."""
    return [round(duracao * (i + 0.5) / quantos, 2) for i in range(quantos)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("video", type=Path)
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--quadros", type=int, default=12)
    p.add_argument("--em", type=float, nargs="*", help="instantes exatos, em segundos")
    p.add_argument("--audio", action="store_true")
    p.add_argument("--transcrever", action="store_true")
    a = p.parse_args(argv)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("instale o ffmpeg (reference/instalar.md)")
    a.saida.mkdir(parents=True, exist_ok=True)
    info = sondar(a.video)
    for t in a.em or instantes(info["duracao_s"], a.quadros):
        destino = a.saida / f"q_{t:07.2f}.jpg"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(a.video), "-frames:v", "1",
             "-vf", "scale=-2:720", "-q:v", "3", str(destino)],
            check=True,
        )  # fmt: skip
    if (a.audio or a.transcrever) and info["tem_audio"]:
        audio = a.saida / "audio.mp3"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(a.video), "-vn", "-ac", "1", "-b:a", "96k",
             str(audio)],
            check=True,
        )  # fmt: skip
        if a.transcrever:
            if shutil.which("whisper"):
                subprocess.run(
                    ["whisper", str(audio), "--model", "small", "--output_dir", str(a.saida),
                     "--output_format", "all", "--word_timestamps", "True"],
                    check=True,
                )  # fmt: skip
            else:
                print("whisper não instalado: ouça audio.mp3 pelo seu harness", file=sys.stderr)
    (a.saida / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps({**info, "pasta": str(a.saida.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
