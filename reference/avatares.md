# Avatares

Cada avatar é uma entrada em `avatares.json` (chave = nome da pasta em `avatares/<chave>/`). Como criar: `avatares/exemplo/README.md`.

| Campo | O que é |
|---|---|
| `nome_publico` | Nome do Personagem no Flow (nunca vai no prompt). |
| `idioma_saida` | Idioma da fala (ex.: `pt-BR`, `en-US`, `es-419`). |
| `publico` | Para quem o avatar fala. |
| `sujeito_prompt` | Como o prompt se refere a ele (ex.: `The woman in the reference photos`). |
| `voz_flow` | Voz do Flow (lista no criador de Characters do Flow). |
| `voz_descricao` | Timbre, sotaque e ritmo, em inglês. |
| `personalidade_flow` | Personalidade (campo do Character no Flow). |
| `cta_seguir` | CTA final; vazio = sem CTA. |
| `linhas_vermelhas` | Temas que exigem revisão humana (saúde, dinheiro, promessas...). |
| `biblia_visual` | Aparência, roupa fixa e estilo de cenário. |
| `legenda` | `estilo_id` (`amarelo_pop`, `classico` ou `nenhum`) e `posicao_y_rel` (0 topo, 1 base). |
| `contas` | Por perfil do gflow: `projeto_id` e `personagem_id` já criados. Comece vazio. |
| `fotos` | Caminhos das fotos em `avatares/<chave>/`. |
