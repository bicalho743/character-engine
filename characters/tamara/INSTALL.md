# Instalação no character-engine

Copie a pasta inteira para o repo `character-engine`, no mesmo nível de `padre_miguel`:

```
character-engine/
└── characters/
    ├── Gi - Organize e Poupe/
    ├── padre_miguel/
    ├── theo/
    └── tamara/        ← esta pasta
```

## Passos

1. Copie `tamara/` para `characters/tamara/`.
2. Suba as fotos reais da Tâmara em `characters/tamara/avatar/` com os nomes do `character.yaml` (ver `avatar/LEIA-AVATAR.md`).
3. Configure o Voice ID do ElevenLabs por variável de ambiente `ELEVENLABS_VOICE_ID` (o `character.yaml` referencia `${ELEVENLABS_VOICE_ID}` — não versionar o valor real em repo público).
4. Calibre as `voice.settings` ouvindo uma amostra; a meta é fala calma e pausada.
5. Os tópicos em `topics.yaml` começam com `status: pending` — o engine consome conforme produz os vídeos.

## Mapeamento (de onde veio cada arquivo)

- 01_proposito_nicho ← identity + client_psychology + públicos (ALMA §1, §7)
- 02_tom_de_voz ← voice + never_say + writing_style
- 03_biblia_visual ← identidade visual (ALMA §6) + paleta + tipografia
- 04_pilares_conteudo ← content_pillars
- 05_voz_sonora ← config ElevenLabs + modo de gravação
- 06_plano_lancamento ← dados que orientam (ALMA §8) + estratégia de público
- 07_documento_mestre ← ALMA condensada (manifesto, regra de ouro, teste de autenticidade, roteiro)
- character.yaml / persona.md / topics.yaml ← config técnica e banco de temas no schema do engine
