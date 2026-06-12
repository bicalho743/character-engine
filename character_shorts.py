"""
character_shorts.py — Motor de personagens (script-only mode)
"""

import os
import json
import yaml
import httpx
from pathlib import Path
from typing import Optional

CHARACTERS_DIR = Path(__file__).parent / "characters"
OPENAI_API_BASE = "https://api.openai.com/v1"


def load_character(character_id: str) -> dict:
    char_dir = CHARACTERS_DIR / character_id
    if not char_dir.exists():
        raise FileNotFoundError(f"Personagem '{character_id}' não encontrado.")

    config_path = char_dir / "character.yaml"
    persona_path = char_dir / "persona.md"
    topics_path = char_dir / "topics.yaml"

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    persona = ""
    if persona_path.exists():
        persona = persona_path.read_text(encoding="utf-8")

    topics = []
    if topics_path.exists():
        with open(topics_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            topics = data.get("topics", [])

    # Verificar avatar
    avatar_rel = config.get("avatar", {}).get("path", "")
    avatar_abs = str(Path(__file__).parent / avatar_rel) if avatar_rel else ""

    problems = []
    if not avatar_abs or not Path(avatar_abs).exists():
        problems.append(f"Imagem do avatar não encontrada em {avatar_rel}")

    if problems:
        print("⚠️  Problemas de configuração:")
        for p in problems:
            print(f"   - {p}")

    return {
        "id": character_id,
        "config": config,
        "persona": persona,
        "topics": topics,
        "char_dir": str(char_dir),
        "avatar_path": avatar_abs,
    }


def pick_next_topic(character: dict, mark_done: bool = False) -> Optional[dict]:
    topics = character["topics"]
    pending = [t for t in topics if t.get("status", "pending") == "pending"]
    if not pending:
        return None
    topic = pending[0]
    if mark_done:
        topics_path = Path(character["char_dir"]) / "topics.yaml"
        with open(topics_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        for t in raw["topics"]:
            if t["id"] == topic["id"]:
                t["status"] = "done"
                break
        with open(topics_path, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False)
    return topic


def generate_character_script(character: dict, topic: dict, openai_key: str) -> dict:
    config = character["config"]
    persona = character["persona"]
    sign_off = config.get("script", {}).get("sign_off", "Fica com Deus. E até o próximo vídeo.")
    duration = config.get("video", {}).get("duration_target", 50)

    system_prompt = f"""Você é o roteirista do {config['name']}.

PERSONA DO PERSONAGEM:
{persona}

REGRAS:
- Idioma: português brasileiro coloquial e caloroso
- Duração alvo: {duration} segundos
- Sempre terminar com: "{sign_off}"
- Responda APENAS com JSON válido, sem markdown"""

    user_prompt = f"""Crie um roteiro para:
Título: {topic['title']}
Hook: {topic['hook']}
Ângulo: {topic['angle']}
Pilar: {topic['pillar']}

Retorne este JSON:
{{
  "title": "título curto",
  "duration_seconds": {duration},
  "hook_text": "2-4 palavras para overlay",
  "segments": [
    {{"type": "hook", "start": 0, "end": 5, "narration": "...", "visual": "actor_talking", "broll_prompt": null, "subtitle_text": "..."}},
    {{"type": "problem", "start": 5, "end": 15, "narration": "...", "visual": "broll", "broll_prompt": "english description", "subtitle_text": "..."}},
    {{"type": "solution", "start": 15, "end": 35, "narration": "...", "visual": "actor_talking", "broll_prompt": null, "subtitle_text": "..."}},
    {{"type": "virada", "start": 35, "end": 50, "narration": "...", "visual": "broll", "broll_prompt": "english description", "subtitle_text": "..."}},
    {{"type": "cta", "start": 50, "end": {duration}, "narration": "{sign_off}", "visual": "actor_talking", "broll_prompt": null, "subtitle_text": "Fica com Deus"}}
  ],
  "full_narration": "toda a narração unida",
  "caption": "legenda para Instagram/TikTok com hashtags",
  "hashtags": ["#padremiguel", "#fe"]
}}"""

    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.get("script", {}).get("model", "gpt-4o-mini"),
        "max_tokens": 1500,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    print(f"[character_shorts] Gerando roteiro: {topic['title']}...")

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=body)
        if resp.status_code != 200:
            raise Exception(f"OpenAI error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    raw = data["choices"][0]["message"]["content"]
    script = json.loads(raw)
    print(f"[character_shorts] ✅ Roteiro gerado: {script.get('title', '?')}")
    return script