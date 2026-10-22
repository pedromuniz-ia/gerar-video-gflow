# Gerar vídeo de avatar com IA (Google Flow)

Skill genérica: recria um vídeo de referência (reel, short, TikTok) com o **seu** avatar, em qualquer nicho e qualquer idioma.

1. Instale Python, ffmpeg, Chrome e o gflow-cli: [reference/instalar.md](reference/instalar.md).
2. Entre no Google Flow uma vez: `gflow auth login --browser chrome --profile minha-conta`.
3. Cadastre seu avatar: siga [avatares/exemplo/README.md](avatares/exemplo/README.md).
4. (Opcional) Copie `config.exemplo.json` para `config.json` e preencha perfil/projeto/Personagem — ou use as variáveis `GFLOW_PERFIL`, `GFLOW_PROJETO`, `GFLOW_PERSONAGEM_ID`, `GFLOW_PERSONAGEM_NOME`. O `config.json` não deve ser compartilhado.
5. Copie esta pasta para as skills do seu agente (`~/.claude/skills/`, `~/.codex/skills/`; no Windows `%USERPROFILE%\.claude\skills\`). Outra IA: cole o `SKILL.md` na conversa.
6. Peça: **"gera o vídeo deste reel <link> com o avatar <chave>"**. O agente mostra roteiro e custo; diga OK.
7. O vídeo fica em `videos/<nome>/final.mp4`, com `final.srt` e o relatório de créditos.

Nenhuma senha, chave ou cookie fica nesta pasta: a sessão do Flow fica no perfil do gflow, na sua máquina.
