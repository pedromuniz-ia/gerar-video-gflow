---
name: gerar-video-gflow
description: Recria um vídeo de referência (reel/short) com o avatar do usuário, em qualquer nicho e idioma, usando o gflow-cli 0.87.0 num Chrome logado no Google Flow, no Windows, no macOS ou no Linux. Use quando pedirem "gera o vídeo deste reel com o avatar X". Você assiste o reel, escreve o roteiro, gera cada take, julga olhando os frames e monta com legenda. Nenhuma API externa decide nada.
---


## Regra 0: sincronizar com o repositório oficial (obrigatório)
Repositório oficial: https://github.com/pedromuniz-ia/gerar-video-gflow
- Logo depois de instalar, e antes de cada uso, atualize a skill a partir do repositório oficial: se a pasta foi clonada, rode `git pull --ff-only` dentro dela; se veio de um zip, rode `git clone https://github.com/pedromuniz-ia/gerar-video-gflow.git` e use essa cópia.
- Não mexa nos arquivos da skill localmente. Seus dados ficam em `config.json`, `reference/avatares.json` e `avatares/<chave>/` e não se perdem na atualização.
- Achou um bug? Abra uma issue no repositório oficial em vez de corrigir só na sua cópia.

# Gerar vídeo de avatar com o gflow-cli

Você faz o trabalho de ponta a ponta. Você **assiste** (frames e áudio), **escreve** o roteiro, **gera** cada take no Flow, **julga** olhando o resultado e **monta** o vídeo. Os 3 scripts só executam: `scripts/frames.py`, `scripts/gflow_cena.py` e `scripts/montar.py`. Eles usam só Python 3.12, o ffmpeg e o gflow-cli.

Primeiro uso na máquina: siga `reference/instalar.md`. Documentação oficial do gflow: `gflow docs usage` e `gflow docs character`.

## Regras

1. **Um gflow por vez por perfil.** Nunca rode dois comandos `gflow` no mesmo `--profile` ao mesmo tempo.
2. **Teto de créditos.** Cada take de vídeo custa 12 créditos. As imagens não custam. Antes de começar, diga ao usuário a estimativa (`tomadas × 12`). Pare antes de passar do teto que ele deu (padrão: estimativa + 25%).
3. **Vídeo com `pode_ter_cobrado: true` não se repete.** Abra a galeria do projeto no Flow. Se o vídeo existir, baixe com `gflow data download <media_id> --profile <perfil>`.
**4. Prompt para o Flow em inglês.** Fala no idioma do avatar (`idioma_saida`). Mensagem para o usuário no idioma dele.
5. **Nunca escreva o nome do avatar solto no prompt.** O Personagem vai no comando e é citado só como `@<nome_publico>` onde se aplica; a imagem de referência é citada como `@<nome do arquivo sem extensão>` (veja `reference/prompts.md`).
6. **Personagem travado, cenário do original.** Mesma pessoa e roupa em todas as cenas. O lugar, a luz e os objetos seguem o reel. As fotos do Personagem devem ter fundo neutro, e o prompt do vídeo repete o cenário da cena, porque o r2v não trava o primeiro quadro (veja `reference/prompts.md`).

## Entrada

- O reel: link ou arquivo `.mp4`.
- O avatar: uma chave de `reference/avatares.json`. Se não houver nenhum além de `exemplo`, ajude o usuário a criar um (`avatares/exemplo/README.md`).
- O perfil do gflow do usuário (`gflow auth list` mostra os perfis). Perfil, projeto e Personagem também podem vir de `config.json` ou das variáveis `GFLOW_*` (README); nesse caso os scripts dispensam as flags.
- A pasta do vídeo: crie `videos/<nome-curto>/`. Tudo fica nela.

## Passo 1 — Conta e Personagem

1. Rode `python scripts/gflow_cena.py saldo --perfil <perfil>`. Confira se o saldo cobre a estimativa.
2. Abra `reference/avatares.json` e leia o avatar inteiro: `biblia_visual`, `voz_descricao`, `sujeito_prompt`, `personalidade_flow`, `cta_seguir`, `legenda`, `fotos`.
3. Se `contas` tem o perfil do usuário com ids preenchidos, use o `projeto_id` e o `personagem_id` dela. **Verifique:** `gflow character list --project <projeto_id> --profile <perfil>` mostra o Personagem.

### Passo 1b — Conta sem Personagem

Crie o projeto: `gflow project create --name "<avatar>" --profile <perfil> --json` e guarde o id. Depois escolha um caminho:

- **Com navegador (melhor identidade):** no Chrome do perfil, abra o projeto no Flow, vá em Characters e crie um novo. Envie `avatares/<chave>/rosto.jpg` e `corpo.jpg`. Nome: `nome_publico`. Voz: `voz_flow`. Personalidade: `personalidade_flow`. Depois pegue o id com `gflow character list --project <id> --json`.
- **Sem navegador:** `gflow character create --project <id> --name "<nome_publico>" --face-prompt "<biblia_visual em inglês>" --voice <voz_flow> --personality "<personalidade_flow>" --model nanopro --profile <perfil> --json`. O rosto sai gerado, não igual à foto. Mostre-o ao usuário antes de seguir.
- **Sem Personagem:** omita `--personagem-id` e passe as fotos do avatar com `--ref` na imagem de cada cena (veja o passo 4).

Grave o projeto e o Personagem em `contas.<perfil>` do avatar (ou no `config.json`). Na próxima vez, ele não precisa criar de novo.

## Passo 2 — Assistir o reel

```text
yt-dlp -o videos/<nome>/original.mp4 "<link>"
python scripts/frames.py videos/<nome>/original.mp4 --saida videos/<nome>/original --quadros 16 --audio
```

Se você não tem o `yt-dlp`, peça o arquivo ao usuário (`python -m pip install yt-dlp` também instala).

Olhe cada `q_<segundos>.jpg` e ouça o `audio.mp3`. Se você não ouve áudio, rode com `--transcrever` (usa o `whisper` local, se estiver instalado) ou peça a transcrição ao usuário. Para ver um corte de perto, use `--em 3.2 3.6 4.0`.

**Verifique:** você sabe cada corte do reel (início e fim em segundos), o que aparece em cada um e cada palavra dita.

## Passo 3 — Escrever o roteiro

Escreva `videos/<nome>/roteiro.json` com as regras de `reference/prompts.md` §1. Divida as tomadas como diz o §2.

**Verifique e mostre ao usuário, antes de gastar crédito:**

- Uma cena por corte do original, com o tempo do original.
- A fala completa, traduzida literalmente para o idioma do avatar.
- O CTA do avatar e as linhas vermelhas encontradas.
- O número de tomadas e o custo (`tomadas × 12` créditos).

Espere o OK do usuário.

## Passo 4 — Gerar cada cena

Para cada cena, em ordem:

**4.1 Imagem** (0 crédito). Use o prompt de `reference/prompts.md` §3 (`Keep the @<quadro> reference image's exact setting... Replace ONLY the person with ... from the character @<nome_publico>`):

```text
python scripts/gflow_cena.py imagem --projeto <projeto_id> --personagem-id <personagem_id> --personagem-nome "<nome_publico>" --perfil <perfil> --saida videos/<nome>/cenas/01 --prompt "<prompt da imagem>"
```

- Se a cena tem `quadro_s`, tire o quadro (`frames.py ... --em <quadro_s>`) e acrescente `--ref <quadro.jpg>`: a imagem nasce do enquadramento original.
- Sem Personagem: tire `--personagem-id` e `--personagem-nome` e acrescente `--ref avatares/<chave>/rosto.jpg --ref avatares/<chave>/corpo.jpg`.

**4.2 Julgue a imagem.** Abra o `arquivo` que o script devolveu e confira os critérios de `reference/prompts.md` §5. Reprovou: ajuste o prompt e gere outra imagem (é grátis).

**4.3 Vídeo de cada tomada** (12 créditos). Use o prompt do §4, com `@<nome_publico>` e `@imagem` (a imagem aprovada) inline e o cenário concreto repetido:

```text
python scripts/gflow_cena.py video --projeto <projeto_id> --personagem-id <personagem_id> --personagem-nome "<nome_publico>" --perfil <perfil> --ref <imagem aprovada> --saida videos/<nome>/cenas/01/tomada-01a --prompt "<prompt do vídeo>"
```

**Leia a última linha da saída** (JSON):

- `"ok": true`: guarde `media_id` e `arquivo` num `videos/<nome>/estado.json` (cena, tomada, media_id, arquivo, créditos). Some os créditos.
- `"ok": false`: faça o que diz `acao`. Códigos 4 e 10 já foram repetidos pelo script. Com `"pode_ter_cobrado": true`, siga a regra 3. A tabela completa está em `reference/codigos-gflow.md`.

**4.4 Julgue o vídeo.** `python scripts/frames.py <arquivo> --saida <pasta>/juiz --quadros 6 --audio`. Olhe os quadros, ouça o áudio e confira o §5. Reprovou: gere a tomada de novo (conte no teto). Anote no estado onde a fala termina (em segundos): é o `fim` no passo 5.

Se o usuário parar no meio, o `estado.json` diz o que já está pronto. Não gere de novo o que já tem `media_id`.

## Passo 5 — Montar e entregar

Escreva `videos/<nome>/plano.json` na ordem das tomadas: `[{"arquivo": "...", "fala": "...", "fim": 7.4}, ...]`. Use `fim` para cortar o silêncio do fim de cada take.

```text
python scripts/montar.py --plano videos/<nome>/plano.json --saida videos/<nome>/final.mp4 --estilo <legenda.estilo_id do avatar> --posicao <legenda.posicao_y_rel>
```

`--estilo nenhum` entrega sem legenda no vídeo. O `final.srt` fica ao lado nos dois casos.

**Verifique:** abra o `final.mp4` e olhe 4 a 6 quadros (`frames.py`). Confira se o vídeo é 9:16, tem som, a legenda está legível e nenhuma fala foi cortada.

**Entregue ao usuário:**

- O caminho do `final.mp4` e do `final.srt`.
- O relatório: tomadas geradas, refeitas, créditos gastos, saldo final (`gflow_cena.py saldo`) e o `media_id` de cada tomada.
