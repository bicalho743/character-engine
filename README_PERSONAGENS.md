# 🎭 Fábrica de Personagens — Padre Miguel, Theo e os próximos

Esta é uma adaptação do [OpenShorts](https://github.com/mutonby/openshorts) que
transforma o motor de vídeo (roteiro → voz → lip-sync → b-roll → FFmpeg →
publicação) em uma **fábrica de personagens fixos com "alma"**.

**Arquitetura: 1 motor, N personagens.** Cada personagem é uma pasta de
configuração — nada de um repositório por personagem.

```
characters/
  padre_miguel/
    persona.md        ← a ALMA: tom, pilares, bordões, o que nunca fazer
    character.yaml    ← voz (ElevenLabs), avatar, modo de vídeo, redes
    topics.yaml       ← fila de temas (pending → done)
    avatar/base.png   ← imagem base do personagem (Midjourney)
  theo/               ← skeleton pronto para migrar o Theo Explica
```

## Pipeline por vídeo

1. **Roteiro** — Gemini escreve em PT-BR seguindo o `persona.md` à risca
   (estrutura fixa: gancho → b-roll → explicação → b-roll → fechamento)
2. **Voz** — ElevenLabs TTS com a voz fixa do personagem
3. **Vídeo falante** — `lowcost`: Hailuo img2video + VEED Lipsync (~$0,65) ou
   `premium`: Kling Avatar v2 (~$2,00), sempre a partir da MESMA imagem base
4. **B-roll** — Flux 2 Pro + efeito Ken Burns, no estilo visual do personagem
5. **Composição** — FFmpeg com legendas estilo TikTok queimadas
6. **Publicação** — Upload-Post para Instagram Reels, TikTok e YouTube Shorts
   (imediata ou agendada)

## Setup rápido

```bash
# 1. Dependências (ou use o Docker do projeto original)
pip install -r requirements.txt

# 2. Chaves no .env
cp .env.example .env
#    GEMINI_API_KEY=...        (aistudio.google.com — grátis)
#    FAL_KEY=...               (fal.ai — pré-pago)
#    ELEVENLABS_API_KEY=...
#    UPLOAD_POST_API_KEY=...   (app.upload-post.com — para publicar)

# 3. Configure o personagem
#    - characters/padre_miguel/character.yaml → voice_id do ElevenLabs
#    - characters/padre_miguel/avatar/base.png → imagem do Midjourney
#    - No Upload-Post, crie o profile "padre_miguel" e conecte as 3 redes
```

## Uso

```bash
# Listar personagens
python generate_character.py --list

# Testar só o roteiro (grátis, sem gastar fal.ai/ElevenLabs)
python generate_character.py -c padre_miguel --next --script-only

# Gerar vídeo do próximo tema da fila
python generate_character.py -c padre_miguel --next

# Gerar com tema específico
python generate_character.py -c padre_miguel -t "O que é a Quaresma?"

# Gerar e publicar nas 3 redes
python generate_character.py -c padre_miguel --next --publish

# Gerar e agendar para domingo às 19h
python generate_character.py -c padre_miguel --next --publish --schedule "2026-06-14 19:00"

# Forçar modo premium (Kling Avatar v2)
python generate_character.py -c padre_miguel --next --mode premium
```

Saídas em `output/characters/<slug>/<timestamp>/` — vídeo final, roteiro
(`script.json`), áudio, talking head e b-rolls (com cache: se algo falhar no
meio, rode de novo e ele retoma de onde parou).

## Automação (n8n / cron / Railway)

O CLI foi pensado para automação: um node Execute Command no n8n com
`python generate_character.py -c padre_miguel --next --publish` consome a fila
de `topics.yaml` automaticamente. Reabasteça a fila adicionando temas no YAML
(ou peça ao Claude para gerar 30 temas de uma vez seguindo os pilares).

## Criar um novo personagem

1. `cp -r characters/padre_miguel characters/novo_personagem`
2. Reescreva `persona.md` (a alma) e ajuste `character.yaml`
3. Gere a imagem base e salve em `avatar/base.png`
4. Crie o profile no Upload-Post e conecte as redes
5. `python generate_character.py -c novo_personagem --next --script-only`

## Ordem de validação recomendada (gaste pouco até confiar)

1. `--script-only` até o roteiro sair com a cara do personagem (grátis)
2. 1 vídeo `lowcost` sem `--publish` — avalie voz, lip-sync e b-roll (~$0,65)
3. 1 vídeo `premium` para comparar o Kling (~$2,00)
4. Só então ligue `--publish` e depois a automação no n8n

---

O restante deste repositório (Clip Generator, AI Shorts UGC, YouTube Studio,
dashboard web) continua funcionando como no projeto original — ver `README.md`.
