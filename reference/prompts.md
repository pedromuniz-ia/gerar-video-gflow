# Regras do roteiro e modelos de prompt

Vale para qualquer nicho e idioma. Os prompts que vão ao Flow ficam **em inglês**. A fala fica no idioma do avatar (`idioma_saida`).

## 1. Roteiro em modo fiel (você escreve, olhando o reel)

Escreva `roteiro.json` na pasta do vídeo:

```json
{
  "idioma_original": "en",
  "cta_original": "texto do CTA do original",
  "cta_final": "CTA do avatar (cta_seguir) ou vazio",
  "cenas": [
    {"ordem": 1, "inicio": 0.0, "fim": 4.2, "tipo": "falada",
     "fala": "fala exata no idioma do avatar",
     "prompt_imagem": "...", "prompt_movimento": "...", "quadro_s": 2.1}
  ]
}
```

Regras:

1. **Fala:** copie palavra por palavra. Se o original está em outra língua, traduza literalmente para o idioma do avatar, com o mesmo gancho, ritmo, tamanho de frase e ordem. Nunca resuma, suavize, acrescente ou tire promessa.
2. **Cenas:** siga os cortes do original. Um plano do original = uma cena. Junte um corte de menos de 1 s ao vizinho. Mantenha a ordem, o tempo (`inicio`/`fim` em segundos do original), a ação e os objetos. Só o apresentador muda.
3. **Promessa:** mantenha todo benefício e promessa como foram ditos.
4. **CTA:** use `cta_seguir` do avatar. Se ele é vazio, tire o CTA final da fala e deixe `cta_final` vazio. Nunca prometa link, livro, produto, guia ou DM que o avatar não tem.
5. **Linha vermelha:** os temas de `linhas_vermelhas` do avatar e, sempre, promessa de cura, conselho médico/financeiro/jurídico arriscado ou resultado garantido. Não reescreva sozinho: mostre o trecho ao usuário e proponha uma versão segura do mesmo tamanho.
6. **Identidade:** nunca invente biografia, credencial, produto ou resultado pessoal. Marca do original vira termo genérico.
7. **Nome:** nunca escreva o nome do avatar nos prompts. O Personagem vai no comando (`--personagem-id`).
8. **Cena `off`:** narração sem rosto (close de mão, produto, objeto). `quadro_s`: o instante do original que melhor mostra o enquadramento; com ele, a imagem nasce desse quadro.

## 2. Tomadas

Cada vídeo do Flow sai com 8 s. Divida a fala de cada cena na pontuação em partes de **até 16 palavras**, o mínimo de partes possível, sem mudar palavras nem ordem. Nomes: `01` (cena de uma tomada) ou `04a`, `04b`.

## 3. Prompt da imagem da cena (1 por cena, 0 crédito)

```text
{sujeito_prompt}. {setting of the original shot, concrete: place, background, surfaces, props, light}. {action and framing}. {wardrobe from the visual bible}. Photorealistic smartphone creator footage, vertical 9:16, 35-50 mm, shallow depth of field, natural matte skin with visible pores, matching the original's lighting and colors. No cartoon, no 3D render, no plastic or waxy skin, no extra fingers or hands, no captions, no on-screen text, no logos, no watermark.
```

## 4. Prompt do vídeo da tomada (12 créditos)

```text
{sujeito_prompt}. {movement of the scene: gesture, camera, expression}. One continuous shot, no cuts. He says to the camera: "{fala da tomada}" Voice: {voz_descricao}.
```

- Mulher ou dupla: troque `He` por `She` ou `They`.
- Cena `off`: `{sujeito_prompt} narrates off-camera: "{fala}" Voice: {voz_descricao}.`
- Sem fala: termine com `No speech.`
- Na fala, troque aspas duplas por simples e tire todo `@` (o gflow lê `@nome` como menção).

## 5. Como julgar (você olha os frames)

Rode `frames.py` na imagem ou no vídeo gerado e confira:

**Imagem** (aprove só se tudo valer):

1. O rosto de cada apresentador aparece e é natural, sem distorção, sem traço derretido ou duplicado (cena em off pode não ter rosto).
2. Toda mão visível está certa: cinco dedos, nenhuma mão a mais, a menos ou grudada.
3. Nenhuma legenda, texto na tela, logo ou marca d'água (rótulo de produto real pode).
4. Parece foto real, não desenho, render 3D ou pele de plástico.
5. É a mesma pessoa das fotos em `avatares/<chave>/` (formato do rosto, olhos, nariz, boca, cabelo, pele, idade) e a roupa da bíblia visual.

**Vídeo** (ouça o áudio):

1. A mensagem é a mesma da fala da tomada. Gagueira, palavra repetida, palavra pequena a mais ou a menos passam.
2. Reprove se faltar ou mudar palavra-chave, número, item citado ou promessa, se o sentido mudou, ou se a fala acaba antes do fim do texto.
3. Voz no idioma e no timbre do avatar; boca sincronizada; plano contínuo, sem corte; a pessoa não muda no meio.

Reprovou: refaça só aquela tomada (custa outros 12 créditos; conte no teto). Na segunda reprovação pela mesma causa, mude o prompt (por exemplo, simplifique o movimento) antes de gastar de novo.
