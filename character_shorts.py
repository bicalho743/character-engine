"""
character_shorts.py — Camada de PERSONAGENS sobre o motor OpenShorts.

Transforma o pipeline UGC/SaaS original em um gerador de vídeos de personagens
fixos com "alma" (persona.md), voz fixa (ElevenLabs) e avatar fixo (imagem base).

Fluxo:
  1. load_character()            → carrega character.yaml + persona.md
  2. generate_character_script() → Gemini escreve roteiro PT-BR fiel à persona
  3. generate_character_video()  → reusa saasshorts.generate_full_video
                                   (voz + lipsync Kling/Hailuo+VEED + b-roll + FFmpeg)
  4. publish_character_video()   → Upload-Post (Instagram, TikTok, YouTube)

Cada personagem vive em characters/<slug>/:
  persona.md       — alma: tom, pilares, bordões, o que nunca fazer
  character.yaml   — voz, avatar, modo de vídeo, publicação
  topics.yaml      — fila de temas (pending/done)
  avatar/base.png  — imagem base do personagem (Midjourney etc.)
"""

import os
import re
import json
import datetime
import httpx
import yaml

from saasshorts import generate_full_video, GEMINI_MODEL

CHARACTERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "characters")
UPLOAD_POST_URL = "https://api.upload-post.com/api/upload"


# ═══════════════════════════════════════════════════════════════════════
# Carregamento do personagem
# ═══════════════════════════════════════════════════════════════════════

def list_characters() -> list:
    """Lista os slugs de personagens disponíveis."""
    if not os.path.isdir(CHARACTERS_DIR):
        return []
    return sorted(
        d for d in os.listdir(CHARACTERS_DIR)
        if os.path.isfile(os.path.join(CHARACTERS_DIR, d, "character.yaml"))
    )


def load_character(slug: str) -> dict:
    """Carrega configuração + persona de um personagem."""
    char_dir = os.path.join(CHARACTERS_DIR, slug)
    yaml_path = os.path.join(char_dir, "character.yaml")
    persona_path = os.path.join(char_dir, "persona.md")

    if not os.path.isfile(yaml_path):
        raise FileNotFoundError(
            f"Personagem '{slug}' não encontrado. Disponíveis: {list_characters()}"
        )

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    persona = ""
    if os.path.isfile(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona = f.read()

    avatar_rel = config.get("avatar", {}).get("image", "")
    avatar_abs = os.path.join(os.path.dirname(CHARACTERS_DIR), avatar_rel) if avatar_rel else ""

    return {
        "slug": slug,
        "dir": char_dir,
        "config": config,
        "persona": persona,
        "avatar_path": avatar_abs,
    }


def validate_character(character: dict) -> list:
    """Retorna lista de problemas de configuração (vazia = ok)."""
    problems = []
    cfg = character["config"]
    voice_id = cfg.get("voice", {}).get("voice_id", "")
    if not voice_id or "SUBSTITUA" in voice_id:
        problems.append("voice.voice_id não configurado em character.yaml")
    if not character["avatar_path"] or not os.path.isfile(character["avatar_path"]):
        problems.append(
            f"Imagem do avatar não encontrada em {cfg.get('avatar', {}).get('image', '?')}"
        )
    if not character["persona"]:
        problems.append("persona.md vazio ou ausente")
    return problems


# ═══════════════════════════════════════════════════════════════════════
# Fila de temas (topics.yaml)
# ═══════════════════════════════════════════════════════════════════════

def _topics_path(character: dict) -> str:
    return os.path.join(character["dir"], "topics.yaml")


def next_pending_topic(character: dict) -> dict | None:
    """Retorna o primeiro tema com status 'pending' (ou None)."""
    path = _topics_path(character)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for item in data.get("topics", []):
        if item.get("status", "pending") == "pending":
            return item
    return None


def mark_topic_done(character: dict, topic_text: str, video_filename: str = ""):
    """Marca um tema como 'done' no topics.yaml."""
    path = _topics_path(character)
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for item in data.get("topics", []):
        if item.get("topic") == topic_text:
            item["status"] = "done"
            item["done_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            if video_filename:
                item["video"] = video_filename
            break
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


# ═══════════════════════════════════════════════════════════════════════
# Geração de roteiro com a persona
# ═══════════════════════════════════════════════════════════════════════

def generate_character_script(character: dict, topic: str, gemini_key: str) -> dict:
    """
    Gera UM roteiro fiel à persona do personagem, no mesmo formato de 5 segmentos
    do motor original (ator, broll, ator, broll, ator) para reutilizar o
    compositing sem nenhuma alteração.
    """
    from google import genai
    from google.genai import types

    cfg = character["config"]
    name = cfg.get("name", character["slug"])
    duration = int(cfg.get("video", {}).get("duration_target", 25))
    broll_style = cfg.get("video", {}).get("broll_style", "cinematic, warm light")
    hashtags = cfg.get("publish", {}).get("default_hashtags", [])

    print(f"[Personagens] 📝 Gerando roteiro de '{name}' sobre: {topic}")

    client = genai.Client(api_key=gemini_key)

    prompt = f"""Você é o roteirista oficial do personagem "{name}", um personagem
de vídeos curtos (Reels/TikTok/Shorts). Abaixo está o DOCUMENTO DE PERSONA do
personagem. Você deve segui-lo À RISCA: tom de voz, pilares, bordões, audiência
e principalmente a seção "O que NUNCA fazer".

══════════ DOCUMENTO DE PERSONA ══════════
{character['persona']}
═══════════════════════════════════════════

TEMA DO VÍDEO DE HOJE: {topic}

IDIOMA: TODO o texto (narração, legendas, título, caption, hashtags) deve estar
em PORTUGUÊS DO BRASIL, natural e falado — como o personagem realmente falaria.
Os campos broll_prompt devem estar em INGLÊS (são prompts de geração de imagem).

DURAÇÃO TOTAL: {duration} segundos. Nunca mais que {duration + 3}.

ESTRUTURA OBRIGATÓRIA DE EXATAMENTE 5 SEGMENTOS:
1. GANCHO: type="hook", visual="actor_talking", broll_prompt=null — o personagem
   abre com uma frase que prende em 2 segundos (pergunta, afirmação surpreendente
   ou dor real da audiência). NÃO comece com "Olá" nem apresentação.
2. B-ROLL 1: type="context", visual="broll", broll_prompt OBRIGATÓRIO em inglês —
   narração em off contextualiza o tema. Estilo visual do b-roll: {broll_style}
3. CORPO: type="explanation", visual="actor_talking", broll_prompt=null — o
   personagem entrega o ponto central, com a profundidade e o tom da persona.
4. B-ROLL 2: type="illustration", visual="broll", broll_prompt OBRIGATÓRIO em
   inglês — imagem que ilustra a aplicação prática. Mesmo estilo visual.
5. FECHAMENTO: type="cta", visual="actor_talking", broll_prompt=null — conclusão
   com o fechamento característico da persona + convite para seguir o perfil.

REGRAS CRÍTICAS:
- EXATAMENTE 5 segmentos na ordem: actor, broll, actor, broll, actor.
- Segmentos 2 e 4: visual="broll" e broll_prompt preenchido (string em inglês).
- Segmentos 1, 3, 5: visual="actor_talking" e broll_prompt=null.
- full_narration = TODA a narração unida (incluindo a dos segmentos de b-roll).
- Frases curtas, ritmo de fala natural, sem palavras difíceis não explicadas.
- Os broll_prompts NUNCA devem conter texto legível, rostos de pessoas reais,
  marcas ou símbolos polêmicos.
- hook_text: 2 a 5 palavras de overlay (em português).

Retorne APENAS um objeto JSON (não um array):
{{
    "title": "Título curto do vídeo (PT-BR)",
    "duration_seconds": {duration},
    "hook_text": "Overlay de 2-5 palavras",
    "segments": [
        {{"type": "hook", "start": 0, "end": 5, "narration": "...", "visual": "actor_talking", "broll_prompt": null, "emotion": "warm", "subtitle_text": "..."}},
        {{"type": "context", "start": 5, "end": 10, "narration": "...", "visual": "broll", "broll_prompt": "... (english)", "emotion": "calm", "subtitle_text": "..."}},
        {{"type": "explanation", "start": 10, "end": 18, "narration": "...", "visual": "actor_talking", "broll_prompt": null, "emotion": "warm", "subtitle_text": "..."}},
        {{"type": "illustration", "start": 18, "end": 22, "narration": "...", "visual": "broll", "broll_prompt": "... (english)", "emotion": "hopeful", "subtitle_text": "..."}},
        {{"type": "cta", "start": 22, "end": {duration}, "narration": "...", "visual": "actor_talking", "broll_prompt": null, "emotion": "warm", "subtitle_text": "..."}}
    ],
    "full_narration": "Toda a narração unida",
    "hashtags": {json.dumps(hashtags, ensure_ascii=False)},
    "caption": "Caption pronta para Instagram/TikTok com 1-2 frases + hashtags"
}}"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=8192,
        ),
    )

    raw = (response.text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Exception(f"Falha ao interpretar JSON do roteiro: {e}\nRaw: {raw[:500]}")

    # O motor original espera actor_description; aqui o ator é fixo (avatar),
    # mas preenchemos por segurança caso a imagem base falhe.
    script.setdefault("actor_description", "3D animated character portrait")
    script["character"] = character["slug"]
    print(f"[Personagens] ✅ Roteiro pronto: {script.get('title')}")
    return script


# ═══════════════════════════════════════════════════════════════════════
# Geração do vídeo (reusa o motor)
# ═══════════════════════════════════════════════════════════════════════

def generate_character_video(
    character: dict,
    script: dict,
    fal_key: str,
    elevenlabs_key: str,
    output_dir: str,
    log=print,
) -> dict:
    """Roda o pipeline completo do motor com avatar e voz FIXOS do personagem."""
    cfg = character["config"]
    config = {
        "fal_key": fal_key,
        "elevenlabs_key": elevenlabs_key,
        "voice_id": cfg["voice"]["voice_id"],
        "selected_actor_path": character["avatar_path"],
        "video_mode": cfg.get("video", {}).get("mode", "lowcost"),
    }
    result = generate_full_video(script, config, output_dir, log=log)
    # Salva o roteiro junto do vídeo para auditoria/reuso
    script_path = os.path.join(output_dir, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    result["script_path"] = script_path
    return result


# ═══════════════════════════════════════════════════════════════════════
# Publicação (Upload-Post)
# ═══════════════════════════════════════════════════════════════════════

def publish_character_video(
    character: dict,
    video_path: str,
    title: str,
    caption: str,
    upload_post_key: str,
    platforms: list | None = None,
    scheduled_date: str | None = None,
    timezone: str = "America/Sao_Paulo",
) -> dict:
    """Publica o vídeo nas redes do personagem via Upload-Post."""
    cfg = character["config"].get("publish", {})
    platforms = platforms or cfg.get("platforms", ["instagram", "tiktok", "youtube"])
    user = cfg.get("upload_post_user", character["slug"])

    headers = {"Authorization": f"Apikey {upload_post_key}"}
    data = {
        "user": user,
        "title": title,
        "platform[]": platforms,
        "async_upload": "true",
    }
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
        data["timezone"] = timezone
    if "tiktok" in platforms:
        data["tiktok_title"] = caption
    if "instagram" in platforms:
        data["instagram_title"] = caption
        data["media_type"] = "REELS"
    if "youtube" in platforms:
        data["youtube_title"] = title
        data["youtube_description"] = caption
        data["privacyStatus"] = "public"

    with open(video_path, "rb") as f:
        files = {"video": (os.path.basename(video_path), f.read(), "video/mp4")}

    print(f"[Personagens] 📡 Publicando em {platforms} (perfil Upload-Post: {user})...")
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(UPLOAD_POST_URL, headers=headers, data=data, files=files)
    if resp.status_code not in (200, 201, 202):
        raise Exception(f"Upload-Post error ({resp.status_code}): {resp.text}")
    print("[Personagens] ✅ Enviado para publicação.")
    return resp.json()
