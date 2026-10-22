"""Gera a imagem ou o vídeo de uma cena no Google Flow pelo gflow-cli 0.87.0.

Só Python 3.12 padrão e o gflow-cli (``pip install gflow-cli==0.87.0``). Funciona no Windows,
no macOS e no Linux. A saída é sempre um JSON numa linha, para o agente ler:

  {"ok": true, "media_id": "...", "arquivo": "...", "codigo": 0, ...}
  {"ok": false, "codigo": 5, "erro": "...", "significado": "...", "acao": "...", "pode_ter_cobrado": false}

Uso:
  python gflow_cena.py imagem --projeto P --personagem-id E --personagem-nome "Nome" \
      --prompt "..." --saida cenas/01 [--ref quadro.png ...] [--perfil minha-conta] [--seco]
  python gflow_cena.py video --projeto P --personagem-id E --personagem-nome "Nome" \
      --ref cenas/01/imagem.png --prompt "..." --saida cenas/01/tomada-a [--perfil ...] [--seco]
  python gflow_cena.py saldo [--perfil ...]

Configuração (nada fica fixo no código): cada opção pode vir da linha de comando, de uma
variável de ambiente ou de ``config.json`` na raiz da skill (copie ``config.exemplo.json``).
Ordem: linha de comando > ambiente > config.json.
  GFLOW_PERFIL, GFLOW_PROJETO, GFLOW_PERSONAGEM_ID, GFLOW_PERSONAGEM_NOME

- ``--seco``: só mostra o comando; não abre o navegador e não gasta crédito.
- Falha passageira (códigos 4 e 10): espera 60, 120 e 180 s e tenta de novo, até 3 vezes.
- Os outros códigos param na hora. Os de ``pode_ter_cobrado: true`` NUNCA se repetem sem
  conferir a galeria do projeto no Flow: o vídeo pode já existir e ter sido cobrado.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSAO = "0.87.0"
CREDITOS_VIDEO = 12
TENTATIVAS = 3
ESPERA_S = 60
TEMPO_MAXIMO_S = 1200
PASSAGEIRO = {4, 10}
#: O vídeo pode existir no Flow e já ter sido cobrado (tabela em reference/codigos-gflow.md).
TALVEZ_COBRADO = {1, 6, 7, 9, 15, 26, 31}
SIGNIFICADO = {
    1: ("erro sem classe ou reCAPTCHA", "confira a galeria do projeto antes de repetir"),
    2: ("uso errado do comando ou perfil inexistente", "corrija o comando; rode `gflow auth list`"),
    3: ("sessão expirada", "rode `gflow auth login --browser chrome --profile <perfil>`"),
    4: ("limite de frequência", "espere alguns minutos e tente de novo"),
    5: ("o Flow recusou o prompt (política de conteúdo)", "suavize o prompt e tente de novo"),
    6: (
        "rede caiu 3 vezes",
        "se veio media_id, baixe grátis com `gflow data download <media_id>`; não gere de novo",
    ),
    7: ("resposta inesperada do Flow", "confira a galeria; atualize o gflow-cli"),
    8: ("perfil sem login", "rode `gflow auth login --browser chrome --profile <perfil>`"),
    9: ("passou do tempo", "confira a galeria do projeto antes de repetir"),
    10: ("camada de segurança do Flow recusou", "mude um pouco o prompt e tente de novo"),
    11: ("pedido que o Flow não aceita (modelo, duração, projeto)", "confira --projeto e o modelo"),
    15: ("a janela do navegador fechou no meio", "não feche a janela; confira a galeria"),
    23: ("o Flow mudou a tela", "abra o Flow no Chrome e confira; atualize o gflow-cli"),
    25: ("a conta está no modo Agente do Flow", "volte o Flow para a interface clássica"),
    26: ("não deu para saber qual mídia é desta geração", "confira a galeria do projeto"),
    27: ("o Flow recusou a imagem enviada", "reconverta a imagem para JPG e tente de novo"),
    29: ("não achou o Personagem no projeto", "confira --projeto e --personagem-id"),
    31: ("o Flow não abriu a página do projeto", "confira a galeria e tente depois"),
    32: ("referência não encontrada no projeto", "use o caminho de um arquivo local em --ref"),
    36: ("pedido que o Flow novo não aceita", "use os comandos desta skill sem mudar flags"),
    37: ("créditos insuficientes", "ponha crédito ou use outra conta"),
    38: ("o Google pediu para escolher a conta", "abra o Chrome do perfil e escolha a conta"),
    39: ("esta conta Google não tem acesso ao Flow", "use outra conta"),
}


RAIZ = Path(__file__).resolve().parents[1]
CONFIG = {"perfil": "GFLOW_PERFIL", "projeto": "GFLOW_PROJETO",
          "personagem_id": "GFLOW_PERSONAGEM_ID", "personagem_nome": "GFLOW_PERSONAGEM_NOME"}  # fmt: skip


def carregar_config(arquivo: Path | None = None) -> dict:
    """Valores padrão: config.json (se existir), sobrescritos pelas variáveis de ambiente."""
    arquivo = arquivo or Path(os.environ.get("GFLOW_CONFIG", RAIZ / "config.json"))
    dados = {}
    if arquivo.is_file():
        bruto = json.loads(arquivo.read_text(encoding="utf-8"))
        dados = {k: bruto[k] for k in CONFIG if bruto.get(k)}
    for chave, var in CONFIG.items():
        if os.environ.get(var):
            dados[chave] = os.environ[var]
    return dados


def gflow() -> list[str]:
    """O executável do gflow: o do PATH ou o módulo do Python atual."""
    achado = shutil.which("gflow")
    if achado:
        return [achado]
    return [sys.executable, "-c", "import sys; from gflow_cli.cli import main; sys.exit(main())"]


def ultimo_json(texto: str) -> dict:
    """O último objeto JSON de topo com "status" (o contrato do --json do gflow)."""
    decodificador, ultimo, posicao = json.JSONDecoder(), {}, 0
    for linha in texto.splitlines(keepends=True):
        if linha.startswith("{"):
            try:
                objeto, _ = decodificador.raw_decode(texto, posicao)
            except json.JSONDecodeError:
                objeto = None
            if isinstance(objeto, dict) and objeto.get("status") in ("ok", "fail"):
                ultimo = objeto
        posicao += len(linha)
    return ultimo


def nome_ref(caminho: str) -> str:
    """Nome com que o gflow cita uma referência enviada (@nome): o nome do arquivo sem extensão."""
    return Path(caminho).stem


def limpar_fala(fala: str) -> str:
    """Aspas duplas viram simples e sai todo ``@`` (o gflow lê ``@nome`` como menção)."""
    return fala.replace('"', "'").replace("@", "")


def prompt_imagem(imagem_ref: str, cenario: str, pessoa: str, personagem_nome: str,
                  acao: str = "", roupa: str = "") -> str:  # fmt: skip
    """Prompt da imagem da cena com as referências citadas inline (@quadro e @Personagem)."""
    partes = [
        f"Keep the @{imagem_ref} reference image's exact setting, background, lighting, camera "
        f"framing, composition and props: {cenario}.",
        f"Replace ONLY the person with {pessoa} from the character @{personagem_nome}.",
        acao, roupa,
        "Photorealistic smartphone creator footage, vertical 9:16, 35-50 mm, shallow depth of "
        "field, natural matte skin with visible pores, matching the original's lighting and "
        "colors. No cartoon, no 3D render, no plastic or waxy skin, no extra fingers or hands, "
        "no captions, no on-screen text, no logos, no watermark.",
    ]
    return " ".join(p.strip() for p in partes if p and p.strip())


def prompt_video(imagem_ref: str, cenario: str, pessoa: str, personagem_nome: str,
                 movimento: str, fala: str, voz: str, pronome: str = "He") -> str:  # fmt: skip
    """Prompt r2v com @Personagem e @imagem da cena inline, e o cenário concreto repetido."""
    final = f'{pronome} says to the camera: "{limpar_fala(fala)}" Voice: {voz}.' if fala else "No speech."
    partes = [
        f"{pessoa} from the character @{personagem_nome}.",
        f"Same setting as the reference scene image @{imagem_ref}: {cenario}; keep this "
        f"background, never the background of the character @{personagem_nome} reference photos.",
        movimento, "One continuous shot, no cuts.", final,
    ]
    return " ".join(p.strip() for p in partes if p and p.strip())


def comando(a: argparse.Namespace) -> list[str]:
    # Sem Personagem na conta: as fotos do avatar vão como --ref (modo referência).
    personagem = (
        ["--reference-entity", a.personagem_id, "--reference-entity-name", a.personagem_nome]
        if a.personagem_id
        else []
    )
    perfil = ["--profile", a.perfil] if a.perfil else []
    saida = str(Path(a.saida).resolve())
    refs = [arg for r in a.ref for arg in ("--ref", str(Path(r).resolve()))]
    if a.acao == "imagem":
        modo = ["image", "i2i", *refs] if refs else ["image", "t2i"]
        return [*gflow(), *modo, "--model", "nano-pro", "--aspect", "9:16", "--out", saida,
                "--project", a.projeto, *personagem, *perfil, "--json", "--", a.prompt]  # fmt: skip
    return [*gflow(), "video", "r2v", *refs, "--model", "omni-flash", "--aspect", "9:16",
            "--duration", "8", "--out-dir", saida, "--project", a.projeto, *personagem, *perfil,
            "--json", "--", a.prompt]  # fmt: skip


def resultado(codigo: int, saida: str, erro: str, video: bool) -> dict:
    dados = ultimo_json(saida)
    if codigo == 0:
        if video:
            arquivo = dados.get("local_path")
            ok = dados.get("succeeded") is True and bool(arquivo) and Path(arquivo).is_file()
            base = {
                "media_id": dados.get("media_id"),
                "arquivo": arquivo,
                "creditos": CREDITOS_VIDEO,
            }
        else:
            imagens = dados.get("images") or [{}]
            arquivo = imagens[0].get("local_path")
            ok = bool(arquivo) and Path(arquivo).is_file()
            base = {"media_id": imagens[0].get("media_id"), "arquivo": arquivo, "creditos": 0}
        if ok:
            return {"ok": True, "codigo": 0, **base}
        codigo = 1  # terminou sem o arquivo: o vídeo pode existir no Flow
    problema = dados.get("problem") or dados.get("error") or {}
    detalhe = problema.get("detail") if isinstance(problema, dict) else None
    linhas = [linha for linha in erro.splitlines() if linha.strip()]
    significado, acao = SIGNIFICADO.get(codigo, ("erro do gflow", "leia `gflow docs usage`"))
    return {
        "ok": False,
        "codigo": codigo,
        "erro": detalhe or (linhas[-1][:300] if linhas else ""),
        "significado": significado,
        "acao": acao,
        "pode_ter_cobrado": video and codigo in TALVEZ_COBRADO,
        "media_id": dados.get("media_id"),
    }


def rodar(args: list[str], video: bool, seco: bool) -> dict:
    print("comando: " + subprocess.list2cmdline(args), file=sys.stderr)
    if seco:
        return {"ok": True, "seco": True, "creditos": CREDITOS_VIDEO if video else 0}
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            feito = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=TEMPO_MAXIMO_S, check=False,
            )  # fmt: skip
            final = resultado(feito.returncode, feito.stdout, feito.stderr, video)
        except subprocess.TimeoutExpired:
            final = resultado(9, "", f"passou de {TEMPO_MAXIMO_S} s", video)
        if final["ok"] or final["codigo"] not in PASSAGEIRO or tentativa == TENTATIVAS:
            return final
        print(f"falha passageira ({final['codigo']}); nova tentativa em {ESPERA_S * tentativa} s",
              file=sys.stderr)  # fmt: skip
        time.sleep(ESPERA_S * tentativa)
    return final


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="acao", required=True)
    for nome in ("imagem", "video"):
        s = sub.add_parser(nome)
        s.add_argument("--projeto")
        s.add_argument(
            "--personagem-id", help="omita na conta sem Personagem (use --ref com as fotos)"
        )
        s.add_argument("--personagem-nome", default="")
        s.add_argument("--prompt", required=True)
        s.add_argument("--saida", required=True)
        s.add_argument("--ref", action="append", default=[], required=nome == "video")
        s.add_argument("--perfil")
        s.add_argument("--seco", action="store_true")
    saldo = sub.add_parser("saldo")
    saldo.add_argument("--perfil")
    a = p.parse_args(argv)
    for chave, valor in carregar_config().items():
        if getattr(a, chave, "x") in (None, ""):
            setattr(a, chave, valor)
    if a.acao != "saldo" and not a.projeto:
        p.error("falta o projeto: --projeto, GFLOW_PROJETO ou config.json")
    if a.acao != "saldo" and a.personagem_id and not a.personagem_nome:
        p.error("--personagem-id exige --personagem-nome")
    if a.acao == "saldo":
        perfil = ["--profile", a.perfil] if a.perfil else []
        return subprocess.run([*gflow(), "credits", "user", *perfil], check=False).returncode
    Path(a.saida).mkdir(parents=True, exist_ok=True)
    final = rodar(comando(a), a.acao == "video", a.seco)
    print(json.dumps(final, ensure_ascii=False))
    return 0 if final["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
