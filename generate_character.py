#!/usr/bin/env python3
"""
generate_character.py — CLI da fábrica de personagens.

Uso típico:

  # Gerar vídeo do Padre Miguel sobre um tema específico:
  python generate_character.py --character padre_miguel \
      --topic "Por que rezamos pelos mortos?"

  # Pegar o próximo tema pendente da fila (topics.yaml) e gerar:
  python generate_character.py --character padre_miguel --next

  # Gerar E publicar (Instagram + TikTok + YouTube via Upload-Post):
  python generate_character.py --character padre_miguel --next --publish

  # Agendar publicação:
  python generate_character.py --character padre_miguel --next --publish \
      --schedule "2026-06-15 19:00"

  # Só gerar o roteiro (rápido e grátis, para revisar antes de gastar API):
  python generate_character.py --character padre_miguel --next --script-only

Chaves de API: defina no .env ou como variáveis de ambiente:
  GEMINI_API_KEY, FAL_KEY, ELEVENLABS_API_KEY, UPLOAD_POST_API_KEY

Para automação (n8n/cron no Railway), basta chamar este script com --next --publish.
"""

import os
import sys
import json
import argparse
import datetime

from dotenv import load_dotenv

load_dotenv()

from character_shorts import (
    list_characters,
    load_character,
    validate_character,
    next_pending_topic,
    mark_topic_done,
    generate_character_script,
    generate_character_video,
    publish_character_video,
)

OUTPUT_BASE = os.environ.get("CHARACTER_OUTPUT_DIR", "output/characters")


def main():
    parser = argparse.ArgumentParser(description="Gera vídeos de personagens de IA")
    parser.add_argument("--character", "-c", required=False, help="Slug do personagem (ex: padre_miguel)")
    parser.add_argument("--topic", "-t", help="Tema do vídeo")
    parser.add_argument("--next", action="store_true", help="Usar o próximo tema pendente do topics.yaml")
    parser.add_argument("--script-only", action="store_true", help="Gera apenas o roteiro (não gasta fal.ai/ElevenLabs)")
    parser.add_argument("--publish", action="store_true", help="Publica nas redes após gerar (Upload-Post)")
    parser.add_argument("--schedule", help='Agendar publicação: "YYYY-MM-DD HH:MM" (horário de Brasília)')
    parser.add_argument("--mode", choices=["lowcost", "premium"], help="Sobrescreve o modo de vídeo do character.yaml")
    parser.add_argument("--list", action="store_true", help="Lista personagens disponíveis")
    args = parser.parse_args()

    if args.list or not args.character:
        print("Personagens disponíveis:")
        for slug in list_characters():
            print(f"  - {slug}")
        if not args.character:
            sys.exit(0)

    character = load_character(args.character)

    # Validação
    problems = validate_character(character)
    if problems:
        print("⚠️  Problemas de configuração:")
        for p in problems:
            print(f"   - {p}")
        if not args.script_only:
            print("Corrija antes de gerar o vídeo (com --script-only dá para testar o roteiro mesmo assim).")
            sys.exit(1)

    if args.mode:
        character["config"].setdefault("video", {})["mode"] = args.mode

    # Tema
    topic_item = None
    if args.next:
        topic_item = next_pending_topic(character)
        if not topic_item:
            print("Nenhum tema pendente em topics.yaml. Adicione temas ou use --topic.")
            sys.exit(1)
        topic = topic_item["topic"]
        print(f"📋 Próximo tema da fila: {topic}")
    elif args.topic:
        topic = args.topic
    else:
        print("Informe --topic \"...\" ou use --next para pegar da fila.")
        sys.exit(1)

    # Chaves
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        print("Defina GEMINI_API_KEY no .env")
        sys.exit(1)

    # 1) Roteiro
    script = generate_character_script(character, topic, gemini_key)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_BASE, character["slug"], timestamp)
    os.makedirs(output_dir, exist_ok=True)

    script_path = os.path.join(output_dir, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"\n──── ROTEIRO ────")
    print(f"Título: {script.get('title')}")
    for seg in script.get("segments", []):
        print(f"  [{seg['type']:<12}] {seg.get('narration', '')}")
    print(f"Caption: {script.get('caption', '')}")
    print(f"Salvo em: {script_path}\n")

    if args.script_only:
        print("✅ --script-only: parando aqui (nenhum custo de vídeo/voz).")
        sys.exit(0)

    # 2) Vídeo
    fal_key = os.environ.get("FAL_KEY", "")
    eleven_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not fal_key or not eleven_key:
        print("Defina FAL_KEY e ELEVENLABS_API_KEY no .env")
        sys.exit(1)

    result = generate_character_video(
        character, script, fal_key, eleven_key, output_dir
    )
    print(f"\n🎬 Vídeo final: {result['video_path']}")
    print(f"💰 Custo estimado: ${result['cost_estimate']['total']}")

    # 3) Fila
    if topic_item:
        mark_topic_done(character, topic, result.get("video_filename", ""))
        print("📋 Tema marcado como 'done' no topics.yaml")

    # 4) Publicação
    if args.publish:
        up_key = os.environ.get("UPLOAD_POST_API_KEY", "")
        if not up_key:
            print("Defina UPLOAD_POST_API_KEY no .env para publicar.")
            sys.exit(1)
        scheduled = None
        if args.schedule:
            scheduled = args.schedule.replace(" ", "T") + ":00"
        publish_character_video(
            character,
            result["video_path"],
            title=script.get("title", "Vídeo"),
            caption=script.get("caption", ""),
            upload_post_key=up_key,
            scheduled_date=scheduled,
        )

    print("\n✅ Concluído.")


if __name__ == "__main__":
    main()
