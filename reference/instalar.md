# Instalar (Windows, macOS, Linux)

Instale uma vez. Faça os passos na ordem. O guia oficial do gflow-cli vem com ele: `gflow docs user-guide`.

## 1. Python 3.12, ffmpeg e Google Chrome

| Sistema | Comando |
| --- | --- |
| Windows (PowerShell) | `winget install Python.Python.3.12 Gyan.FFmpeg Google.Chrome astral-sh.uv` |
| macOS | `brew install python@3.12 ffmpeg uv` e `brew install --cask google-chrome` |
| Linux (Debian/Ubuntu) | `sudo apt install python3.12 ffmpeg` e `curl -LsSf https://astral.sh/uv/install.sh \| sh` (Chrome: pacote `.deb` em google.com/chrome) |

Feche e abra o terminal. Confira: `python --version` (no macOS/Linux, `python3`), `ffmpeg -version` e `uv --version`.

## 2. gflow-cli 0.87.0

```text
uv tool install gflow-cli==0.87.0
uvx --from gflow-cli==0.87.0 playwright install chromium
gflow --version
```

Sem `uv`: `python -m pip install gflow-cli==0.87.0` e depois `python -m playwright install chromium`.

No Windows, se aparecer texto quebrado, rode antes: `$env:PYTHONUTF8=1`.

## 3. Entrar no Flow (uma vez por conta)

```text
gflow auth login --browser chrome --profile minha-conta
gflow auth status --profile minha-conta
```

O Chrome abre. Entre na conta Google do Flow e resolva o captcha, se aparecer. Espere o Flow carregar: o gflow fecha a janela sozinho. `auth status` deve dizer `Flow session verified as <sua conta>`.

A sessão fica em:

- Windows: `%LOCALAPPDATA%\gflow-cli\profile_minha-conta\`
- macOS: `~/Library/Application Support/gflow-cli/profile_minha-conta/`
- Linux: `~/.local/share/gflow-cli/profile_minha-conta/`

Use `--profile minha-conta` em todo comando (ou `gflow auth use minha-conta` para deixar como padrão). **Rode um gflow por vez por perfil.** Dois ao mesmo tempo saem com o código 11 (perfil ocupado).

## 4. Opcional

- Transcrição local, sem API: `python -m pip install openai-whisper` (o `frames.py --transcrever` usa).
- O próprio gflow tem um servidor MCP (`gflow mcp`). Um agente com suporte a MCP pode chamá-lo direto; os scripts desta skill não precisam dele.

## Teste rápido, sem gastar crédito

```text
python scripts/gflow_cena.py saldo --perfil minha-conta
python scripts/gflow_cena.py video --projeto <id> --personagem-id <id> --personagem-nome "Exemplo" --ref avatares/exemplo/rosto.jpg --prompt "teste" --saida teste --seco
```

O primeiro mostra os créditos. O segundo só imprime o comando (`--seco`).

## Problemas conhecidos
- **HTTP 410 ao logar ou checar a sessão** ("Could not verify the Flow session"): desde 22/10/2026 o endpoint de sessão do Flow responde 410. Use o gflow-cli 0.87.0 ou mais novo (`uv tool install gflow-cli==0.87.0 --force`). Se o login já tiver desfeito o marcador do navegador, faça login de novo ou grave `chrome` em `~/.local/share/gflow-cli/profile_<perfil>/.gflow_browser_strategy`.
- **Contas migradas para flow.google.com**: no 0.87.0, `gflow credits` ainda não lê o saldo e `gflow character list` dá o código 7. Confira o saldo e o personagem pela tela do Flow.
