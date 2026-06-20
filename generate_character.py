#!/usr/bin/env python3
"""
generate_character.py — CLI para geração de vídeos por personagem

Modo híbrido:
  --script-only  → gera roteiro, salva JSON + TXT para revisão humana
  --from-script  → usa roteiro já aprovado para gerar vídeo
  (sem flags)    → gera roteiro + vídeo automaticamente

Exemplos:
  python generate_character.py -c padre_miguel --next --script-only
  python generate_character.py -c padre_miguel --from-script output/padre_miguel/roteiro.json
  python generate_character.py -c padre_miguel --next
  python generate_character.py --list-characters
  python generate_character.py -c padre_miguel --list-topics
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

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


def print_script(script: dict):
    print(f"\n{'='*60}")
    print(f"ROTEIRO: {script.get('title', '?')}")
    print(f"Duração: {script.get('duration_seconds', '?')}s")
    print(f"Hook overlay: {script.get('hook_text', '?')}")
    print(f"{'='*60}")
    for seg in script.get("segments", []):
        print(f"\n[{seg['type'].upper()} {seg['start']}–{seg['end']}s]")
        print(f"  {seg['narration']}")
        if seg.get("broll_prompt"):
            print(f"  B-ROLL: {seg['broll_prompt']}")
    print(f"\n{'─'*60}")
    print(f"NARRAÇÃO COMPLETA:")
    print(script.get("full_narration", ""))
    print(f"\n{'─'*60}")
    print(f"CAPTION:")
    print(script.get("caption", ""))
    print(f"{'='*60}\n")


def save_script(script: dict, topic: dict, output_dir: Path) -> tuple:
    output_dir.mkdir(parents=True, exist_ok=True)
    title_slug = topic.get("id", "roteiro")

    json_path = output_dir / f"{title_slug}_roteiro.json"
    txt_path = output_dir / f"{title_slug}_roteiro.txt"
    caption_path = output_dir / f"{title_slug}_caption.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "script": script}, f, ensure_ascii=False, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"ROTEIRO: {script.get('title', '?')}\n")
        f.write(f"Tema: {topic.get('title', '?')}\n")
        f.write(f"Pilar: {topic.get('pillar', '?')}\n")
        f.write(f"{'='*60}\n\n")
        for seg in script.get("segments", []):
            f.write(f"[{seg['type'].upper()} {seg['start']}–{seg['end']}s]\n")
            f.write(f"{seg['narration']}\n")
            if seg.get("broll_prompt"):
                f.write(f"B-ROLL: {seg['broll_prompt']}\n")
            f.write("\n")
        f.write(f"{'─'*60}\n")
        f.write(f"NARRAÇÃO COMPLETA:\n{script.get('full_narration', '')}\n\n")
        f.write(f"CAPTION:\n{script.get('caption', '')}\n")

    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(script.get("caption", ""))

    return json_path, txt_path, caption_path


def generate_voiceover(text: str, voice_id: str, elevenlabs_key: str, output_path: str, voice_settings: dict = None):
    import httpx
    import re
    if os.path.exists(output_path):
        print(f"    [SKIP] Audio already exists: {output_path}")
        return
    print("[2/4] Gerando narração no ElevenLabs...")
    # Remove audio tags que eleven_multilingual_v2 não reconhece
    text = re.sub(r'\[(serious|soft|calm|pensive|warm)\]', '', text).strip()
    text = re.sub(r'\s+', ' ', text)

    # Configurações padrão
    settings = {
        "stability": 0.55,
        "similarity_boost": 0.80,
        "style": 0.30,
        "use_speaker_boost": True,
    }
    if voice_settings:
        for k, v in voice_settings.items():
            if v is not None:
                settings[k] = v

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": elevenlabs_key,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": settings,
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code != 200:
            raise Exception(f"ElevenLabs error ({resp.status_code}): {resp.text[:200]}")
        with open(output_path, "wb") as f:
            f.write(resp.content)
    print(f"    ✅ Áudio: {output_path}")


def generate_kling_avatar(image_path: str, audio_path: str, fal_key: str, output_path: str):
    import httpx
    import fal_client
    import asyncio

    print("[3/4] Gerando vídeo com Kling Avatar v2...")
    os.environ["FAL_KEY"] = fal_key

    async def run():
        print("    Upload da imagem...")
        image_url = await fal_client.upload_file_async(image_path)
        print(f"    Imagem: {image_url}")
        print("    Upload do áudio...")
        audio_url = await fal_client.upload_file_async(audio_path)
        print(f"    Audio: {audio_url}")
        print("    Submetendo para Kling (aguardando ~10-20 min)...")

        handler = await fal_client.submit_async(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": image_url,
                "audio_url": audio_url,
                "prompt": "person looking directly at camera, natural eye contact, minimal head movement, speaking naturally and calmly, stable face position",
            },
        )
        print(f"    Job: {handler.request_id}")

        async for event in handler.iter_events(with_logs=False):
            if isinstance(event, fal_client.InProgress):
                print(f"    Em progresso...")
            elif hasattr(event, "status"):
                print(f"    Status: {event.status}")

        result = await handler.get()
        return result

    result = asyncio.run(run())

    video_url = None
    if isinstance(result, dict):
        if "video" in result:
            video_url = result["video"].get("url")
        elif "output" in result:
            video_url = result["output"].get("video_url") or result["output"].get("url")

    if not video_url:
        raise Exception(f"URL do video nao encontrada: {result}")

    print("    Baixando video...")
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(video_url)
        with open(output_path, "wb") as f:
            f.write(resp.content)
    print(f"    OK Video: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Character Engine — gerador de vídeos por personagem")
    parser.add_argument("-c", "--character", help="ID do personagem (ex: padre_miguel)")
    parser.add_argument("--next", action="store_true", help="Usa o próximo tema da fila")
    parser.add_argument("--topic", help="ID específico de um tema")
    parser.add_argument("--script-only", action="store_true", help="Gera apenas o roteiro (modo híbrido)")
    parser.add_argument("--from-script", help="Caminho para JSON de roteiro já aprovado")
    parser.add_argument("--output-dir", default="output", help="Pasta de saída")
    parser.add_argument("--list-characters", action="store_true")
    parser.add_argument("--list-topics", action="store_true")
    parser.add_argument("--json-output", action="store_true", help="Saída em JSON para n8n")
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
    char_config = character["config"]

    if args.from_script:
        script_path = Path(args.from_script)
        if not script_path.exists():
            print(f"❌ Arquivo não encontrado: {args.from_script}")
            sys.exit(1)
        with open(script_path, encoding="utf-8") as f:
            data = json.load(f)
        topic = data["topic"]
        script = data["script"]
        print(f"✅ Roteiro carregado: {script.get('title', '?')}")
    else:
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
            print("❌ Use --next, --topic <id> ou --from-script <arquivo>")
            sys.exit(1)

        openai_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")
        if not openai_key:
            openai_key = None
        if not gemini_key:
            gemini_key = None
            
        if not openai_key and not gemini_key:
            print("❌ Nenhuma chave de API (OPENAI_API_KEY ou GEMINI_API_KEY) configurada.")
            sys.exit(1)

        print(f"\nPersonagem: {char_config['name']}")
        print(f"Tema: {topic['title']}\n")
        script = generate_character_script(character, topic, openai_key=openai_key, gemini_key=gemini_key)

    if args.script_only:
        output_dir = Path(args.output_dir) / args.character
        json_path, txt_path, caption_path = save_script(script, topic, output_dir)

        if args.json_output:
            print(json.dumps({"topic": topic, "script": script}, ensure_ascii=False, indent=2))
        else:
            print_script(script)
            print(f"📄 Arquivos salvos para revisão:")
            print(f"   Roteiro JSON: {json_path}")
            print(f"   Roteiro TXT:  {txt_path}")
            print(f"   Caption:      {caption_path}")
            print(f"\n✏️  Revise o roteiro e use o 11_checklist_alma.md para aprovar.")
            print(f"▶️  Para gerar o vídeo após aprovação:")
            print(f"   python generate_character.py -c {args.character} --from-script {json_path}")
        return

    raw_fal_key = os.environ.get("FAL_KEY", "")
    fal_key = raw_fal_key.strip().strip('"').strip("'")
    
    raw_eleven = os.environ.get("ELEVENLABS_API_KEY", "")
    elevenlabs_key = raw_eleven.strip().strip('"').strip("'")

    print(f"[DEBUG] FAL_KEY original len: {len(raw_fal_key)}, cleaned len: {len(fal_key)}")
    if len(fal_key) > 8:
        print(f"[DEBUG] FAL_KEY masked: {fal_key[:4]}...{fal_key[-4:]}")

    if not fal_key or not elevenlabs_key:
        print("❌ FAL_KEY e ELEVENLABS_API_KEY necessários para gerar vídeo.")
        sys.exit(1)

    output_dir = Path(args.output_dir) / args.character
    output_dir.mkdir(parents=True, exist_ok=True)
    title_slug = topic.get("id", "video")

    audio_path = str(output_dir / f"{title_slug}_voice.mp3")
    video_path = str(output_dir / f"{title_slug}_final.mp4")

    # Selecionar ângulo baseado no pilar
    pillar = topic.get("pillar", "default")
    pillar_angles = char_config.get("avatar", {}).get("pillar_angles", {})
    avatar_rel = pillar_angles.get(pillar) or char_config["avatar"]["path"]
    avatar_path = str(Path(__file__).parent / avatar_rel)

    if not Path(avatar_path).exists():
        print(f"❌ Avatar não encontrado: {avatar_path}")
        sys.exit(1)

    print(f"    Ângulo: {Path(avatar_path).name} (pilar: {pillar})")

    full_narration = script.get("full_narration", "")
    voice_config = char_config.get("voice", {})
    voice_id = voice_config.get("voice_id")
    voice_settings = voice_config.get("settings", {})

    print(f"\n[1/4] Tema: {topic['title']}")
    generate_voiceover(full_narration, voice_id, elevenlabs_key, audio_path, voice_settings)
    
    kling_success = False
    try:
        generate_kling_avatar(avatar_path, audio_path, fal_key, video_path)
        kling_success = True
    except Exception as e:
        print(f"\n⚠️  Erro ao gerar vídeo com Kling (fal.ai): {e}")
        print("    O áudio da narração foi salvo com sucesso, mas o vídeo não pôde ser gerado.")

    caption_path = str(output_dir / f"{title_slug}_caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(script.get("caption", ""))

    hook_text = script.get("hook_text", topic.get("hook", ""))

    print(f"\n{'='*60}")
    if kling_success:
        print(f"✅ Vídeo gerado: {video_path}")
        print(f"\n▶️  Próximo passo — aplicar legendas e publicar:")
        print(f'   python post_process.py -c {args.character} "{video_path}" "{audio_path}" "{hook_text}" "{output_dir}/final" "{caption_path}"')
    else:
        print("❌ Geração de vídeo com Kling falhou. Narração de áudio e caption prontas.")
        print(f"   Áudio: {audio_path}")
        print(f"   Legenda/Caption: {caption_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()