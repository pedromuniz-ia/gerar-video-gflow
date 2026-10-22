# Como adicionar um avatar

1. Crie a pasta `avatares/<chave>/` (ex.: `avatares/ana/`; minúsculas, sem espaço).
2. Coloque as fotos (JPG, rosto bem iluminado, sem texto nem marca d'água):
   - `rosto.jpg` — close do rosto, de frente.
   - `corpo.jpg` — corpo inteiro ou meio corpo, com a roupa fixa do avatar.
   - Opcional: mais ângulos/expressões; liste todas em `fotos`.
3. Em `reference/avatares.json`, duplique a entrada `exemplo`, troque a chave por `<chave>` e preencha os campos (veja `reference/avatares.md`).
4. Na primeira geração, o agente cria o Personagem no Flow (SKILL.md, passo 1b) e anota `projeto_id` e `personagem_id` em `contas.<seu-perfil>`.

Use só imagens que você tem direito de usar. Esta pasta `exemplo` não traz fotos: é só o modelo.
