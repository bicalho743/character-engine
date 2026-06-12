#!/usr/bin/env python3
import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CHARACTERS_DIR = Path(__file__).parent / "characters"


def list_characters():
    chars = []
    for d in CHARACTERS_DIR.iterdir():
        if d.is_dir() and (d / "character.yaml").exists():
            with open(d / "character.yaml", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            chars.append({
                "id": d.name,
                "name": cfg.get("name", d.name),
                "active": cfg.get("active", False),
            })
    return chars


def list_topics(character_id: str):
    topics_path = CHARACTERS_DIR / character_id / "topics.yaml"
    if not topics_path.exists():
        return []
    with open(topics_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("topics", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--character")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--topic")
    parser.add_argument("--script-only", action="store_true")
    parser.add_argument("--list-characters", action="store_true")
    parser.add_argument("--list-topics", action="store_true")
    parser.add_argument("--json-output", action="store_true")
    args = parser.parse_args()

    if args.list_characters:
        for c in list_characters():
            print(f"  {c['id']} — {c['name']}")
        return

    if not args.character:
        parser.print_help()
        sys.exit(1)

    if args.list_topics:
        for t in list_topics(args.character):
            icon = "✅" if t.get("status") == "done" else "⏳"
            print(f"  {icon} [{t['id']}] {t['title']}")
        return

    from character_shorts import load_character, pick_next_topic, generate_character_script

    character = load_character(args.character)

    if args.next:
        topic = pick_next_topic(character, mark_done=False)
        if topic is None:
            print(f"❌ Sem temas pendentes para {args.character}.")
            sys.exit(1)
    elif args.topic:
        matching = [t for t in character["topics"] if t["id"] == args.topic]
        if not matching:
            print(f"❌ Tema '{args.topic}' não encontrado.")
            sys.exit(1)
        topic = matching[0]
    else:
        print("❌ Use --next ou --topic <id>")
        sys.exit(1)

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY não configurado no .env")
        sys.exit(1)

    if args.script_only:
        script = generate_character_script(character, topic, openai_key)

        if args.json_output:
            print(json.dumps({"topic": topic, "script": script},
                             ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"ROTEIRO: {script.get('title', '?')}")
            print(f"{'='*50}")
            for seg in script.get("segments", []):
                print(f"\n[{seg['type'].upper()} {seg['start']}–{seg['end']}s]")
                print(f"  Narração: {seg['narration']}")
                if seg.get("broll_prompt"):
                    print(f"  B-roll:   {seg['broll_prompt']}")
            print(f"\nNarração completa:\n{script.get('full_narration', '')}")
            print(f"\nCaption: {script.get('caption', '')}")
        return

    print("❌ Geração de vídeo ainda não implementada. Use --script-only.")


if __name__ == "__main__":
    main()