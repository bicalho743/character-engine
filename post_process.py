"""
post_process.py — Legendas + Hook + Thumbnail + Publicacao
Uso: python post_process.py -c <character_id> <video> <audio> <hook_text> <output_dir> [caption_file]
     python post_process.py <video> <audio> <hook_text> <output_dir> [caption_file]  (fallback: padre_miguel)
"""
import sys
import os
import subprocess
import textwrap
import unicodedata
from dotenv import load_dotenv

load_dotenv()

# ── Perfis de publicação por personagem ──────────────────────────────────────
CHARACTER_PROFILES = {
    "padre_miguel": {
        "perfis": ["Conselhosdopadremiguel"],
        "first_comment": "#padre #catholiclife #catolico #fecatolica #reflexao #palavradedeus #religiao #espiritualidade",
        "fallback_caption_cta": "Se isso tocou voce, manda para alguem que precisa ouvir hoje. 🙏",
        "fallback_hashtags": "#padremiguel #fe #espiritualidade #catolicismo #ansiedade",
        "youtube_tags": "padre miguel,fe,espiritualidade,catolicismo,acolhimento,oracao,ansiedade,esperanca,padre,reflexao",
    },
    "tamara": {
        "perfis": ["tamaraorganiza"],
        "first_comment": "#personalorganizer #organizacaoresidencial #mudancadealtopadrao #organizacaoinvisivel #closet #casaprontaparaservivida",
        "fallback_caption_cta": "Quer transformar o seu espaço? Chama no direct.",
        "fallback_hashtags": "#tamaraorganiza #personalorganizer #organizacaoresidencial #mudancadealtopadrao #organizacaoinvisivel",
        "youtube_tags": "tamara cavalcante,personal organizer,organizacao,mudanca,alto padrao,closet,casa organizada,rotina leve",
    },
}
DEFAULT_CHARACTER = "padre_miguel"



def remove_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def fix_path(p):
    return p.replace("\\", "/")


def get_video_dimensions(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        fix_path(video_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        w, h = map(int, res.stdout.strip().split("x"))
        return w, h
    except Exception as e:
        print(f"Aviso: nao foi possivel obter dimensoes do video: {e}. Usando padrao 720x1280.")
        return 720, 1280


def gerar_srt(audio_path, srt_path):
    from faster_whisper import WhisperModel
    print("[1/5] Transcrevendo audio com word-level timestamps...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(fix_path(audio_path), language="pt", word_timestamps=True)

    # Coletar todas as palavras com seus respectivos tempos
    all_words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                all_words.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end
                })
        else:
            text_words = seg.text.strip().split()
            if text_words:
                dt = (seg.end - seg.start) / len(text_words)
                for j, w in enumerate(text_words):
                    all_words.append({
                        "word": w,
                        "start": seg.start + j * dt,
                        "end": seg.start + (j + 1) * dt
                    })

    # Agrupar palavras em blocos curtos (max 6 palavras ou max 32 caracteres)
    groups = []
    current_group = []
    current_length = 0

    for w in all_words:
        word_text = w["word"].strip()
        if not word_text:
            continue
        
        # Fecha o grupo anterior se exceder o limite de palavras ou caracteres
        if current_group and (len(current_group) >= 6 or current_length + len(word_text) + 1 > 32):
            groups.append(current_group)
            current_group = []
            current_length = 0
            
        current_group.append(w)
        current_length += len(word_text) + (1 if current_length > 0 else 0)

    if current_group:
        groups.append(current_group)

    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # Gravar o arquivo SRT formatado com os novos blocos
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, grp in enumerate(groups, 1):
            text_str = " ".join(w["word"].strip() for w in grp)
            start_t = grp[0]["start"]
            end_t = grp[-1]["end"]
            f.write(f"{i}\n{fmt(start_t)} --> {fmt(end_t)}\n{text_str}\n\n")

    print(f"    OK SRT: {srt_path} ({len(groups)} blocos curtos)")


def gerar_video_legendado(video_path, srt_path, hook_text, output_path):
    print("[2/5] Adicionando legendas...")

    import shutil
    srt_temp = "legendas_temp.srt"
    shutil.copy(srt_path, srt_temp)

    subtitle_style = (
        "FontName=Arial,"
        "FontSize=12,"
        "PrimaryColour=&H001A1A1A,"
        "OutlineColour=&H33FFFFFF,"
        "BorderStyle=3,"
        "Outline=3,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=60"
    )

    vf = f"subtitles={srt_temp}:fontsdir=C\\\\:/Windows/Fonts:force_style='{subtitle_style}'"
    cmd = ["ffmpeg", "-y", "-i", fix_path(video_path), "-vf", vf, "-c:a", "copy", fix_path(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg erro: {result.stderr[-400:]}")
    print(f"    OK Video: {output_path}")


def gerar_thumbnail(video_path, hook_text, output_path):
    print("[3/5] Gerando thumbnail...")
    hook_clean = hook_text  # já veio sem acentos do main()

    total_chars = len(hook_clean)
    if total_chars <= 20:
        fonte = 95
        width = 15
    elif total_chars <= 35:
        fonte = 80
        width = 18
    elif total_chars <= 50:
        fonte = 70
        width = 20
    else:
        fonte = 60
        width = 22

    linhas = textwrap.wrap(hook_clean, width=width)
    _, altura = get_video_dimensions(video_path)
    espaco = int(fonte * 1.4)
    y_inicio = int(altura * 0.68)

    filtros = []
    for i, linha in enumerate(linhas):
        linha_esc = linha.replace("'", "\\'").replace(":", "\\:")
        y = y_inicio + (i * espaco)
        filtros.append(
            f"drawtext=text='{linha_esc}'"
            f":fontcolor=yellow"
            f":fontsize={fonte}"
            f":box=1"
            f":boxcolor=black@0.75"
            f":boxborderw=20"
            f":x=(w-text_w)/2"
            f":y={y}"
            f":fontfile=C\\\\:/Windows/Fonts/arial.ttf"
            f":borderw=4"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", fix_path(video_path),
        "-vframes", "1",
        "-update", "1",
        "-vf", ",".join(filtros),
        "-q:v", "2",
        fix_path(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg erro: {result.stderr[-400:]}")
    print(f"    OK Thumbnail: {output_path}")


def inserir_thumbnail_no_video(video_path, thumbnail_path, output_path):
    """Insere thumbnail como primeiro frame do video — Instagram usa como capa."""
    print("[4/5] Inserindo thumbnail como capa do video...")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "1", "-i", fix_path(thumbnail_path),
        "-i", fix_path(video_path),
        "-filter_complex",
        "[0:v]scale=1072:1904,setsar=1,fps=30[thumb];"
        "[1:v]scale=1072:1904,setsar=1[vid];"
        "[thumb][vid]concat=n=2:v=1:a=0[outv];"
        "[1:a]adelay=1000|1000[outa]",
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        fix_path(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg erro: {result.stderr[-400:]}")
    print(f"    OK Video com capa: {output_path}")


def upload_thumbnail_fal(thumbnail_path, fal_key):
    import fal_client
    import asyncio
    os.environ["FAL_KEY"] = fal_key

    async def run():
        url = await fal_client.upload_file_async(thumbnail_path)
        return url

    return asyncio.run(run())


def publicar_video(video_path, thumbnail_url, titulo, caption, upload_post_key, perfis, first_comment="", youtube_tags="", scheduled_date=None):
    print("[5/5] Publicando nas redes...")
    import httpx

    with open(fix_path(video_path), "rb") as vf:
        video_bytes = vf.read()

    for perfil in perfis:
        print(f"    Enviando para {perfil}...")
        files = {
            "video": (os.path.basename(video_path), video_bytes, "video/mp4"),
        }
        data = {
            "user": perfil,
            "title": caption,
            "description": caption,
            "platform[]": ["instagram", "tiktok", "youtube", "x"],
            "first_comment": first_comment,
            # Instagram Specifics
            "media_type": "REELS",
            "share_to_feed": "true",
            # TikTok Specifics
            "tiktok_ai_generated_content": "true",
            "post_mode": "DIRECT_POST",
            # YouTube Specifics
            "youtube_title": titulo,
            "youtube_description": caption,
            "youtube_tags": youtube_tags,
            "youtube_category_id": "29",
            "youtube_privacy_status": "public",
            "privacyStatus": "public",
        }
        if thumbnail_url:
            data["instagram_cover_url"] = thumbnail_url
        if scheduled_date:
            data["scheduled_date"] = scheduled_date
            data["timezone"] = "America/Sao_Paulo"

        headers = {"Authorization": f"Apikey {upload_post_key}"}

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                "https://api.upload-post.com/api/upload",
                headers=headers,
                data=data,
                files=files,
            )

        if resp.status_code in (200, 201, 202):
            print(f"    OK Publicado em {perfil}")
            print(f"    Resposta: {resp.text[:200]}")
        else:
            print(f"    ERRO em {perfil}: {resp.status_code} — {resp.text[:200]}")


def main():
    # Parse -c <character> flag
    args = sys.argv[1:]
    character_id = DEFAULT_CHARACTER

    if "-c" in args:
        idx = args.index("-c")
        if idx + 1 < len(args):
            character_id = args[idx + 1]
            args = args[:idx] + args[idx + 2:]  # remove -c and value
        else:
            print("Erro: -c requer o ID do personagem (ex: -c tamara)")
            sys.exit(1)

    if len(args) < 4:
        print("Uso: python post_process.py [-c <character>] <video.mp4> <audio.mp3> <hook_text> <output_dir> [caption_file] [scheduled_date]")
        print(f"Personagens disponíveis: {', '.join(CHARACTER_PROFILES.keys())}")
        sys.exit(1)

    video_path = args[0]
    audio_path = args[1]
    hook_text = args[2]
    output_dir = args[3]
    caption_file = args[4] if len(args) > 4 else None
    scheduled = args[5] if len(args) > 5 else None

    # Resolve character profile
    profile = CHARACTER_PROFILES.get(character_id)
    if not profile:
        print(f"⚠️  Personagem '{character_id}' não tem perfil de publicação configurado.")
        print(f"   Disponíveis: {', '.join(CHARACTER_PROFILES.keys())}")
        print(f"   Continuando sem publicação...")
        profile = None

    print(f"\n🎬 Pós-processamento: {character_id}")

    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(video_path))[0]
    srt_path = os.path.join(output_dir, f"{base}.srt")
    video_legendado = os.path.join(output_dir, f"{base}_legendado.mp4")
    thumbnail = os.path.join(output_dir, f"{base}_thumb.jpg")
    video_final = os.path.join(output_dir, f"{base}_final_pub.mp4")

    if caption_file and os.path.exists(caption_file):
        with open(caption_file, encoding="utf-8") as f:
            caption = f.read().strip()
        print(f"Caption carregada: {caption[:80]}...")
    else:
        if profile:
            caption = (
                hook_text +
                f"\n\n{profile['fallback_caption_cta']}"
                f"\n\n{profile['fallback_hashtags']}"
            )
        else:
            caption = hook_text

    gerar_srt(audio_path, srt_path)
    gerar_video_legendado(video_path, srt_path, hook_text, video_legendado)
    hook_para_thumb = remove_acentos(hook_text)
    gerar_thumbnail(video_path, hook_para_thumb, thumbnail)
    inserir_thumbnail_no_video(video_legendado, thumbnail, video_final)

    upload_key = os.environ.get("UPLOAD_POST_KEY", "")
    fal_key = os.environ.get("FAL_KEY", "")

    if upload_key and profile:
        thumbnail_url = None
        if fal_key:
            print("    Fazendo upload do thumbnail para fal.ai...")
            try:
                thumbnail_url = upload_thumbnail_fal(thumbnail, fal_key)
                print(f"    Thumbnail URL: {thumbnail_url}")
            except Exception as e:
                print(f"    Aviso: falha no upload do thumbnail: {e}")

        perfis = profile["perfis"]
        titulo = remove_acentos(hook_text)
        publicar_video(
            video_final, thumbnail_url, titulo, caption, upload_key, perfis,
            first_comment=profile.get("first_comment", ""),
            youtube_tags=profile.get("youtube_tags", ""),
            scheduled_date=scheduled
        )
    else:
        if not upload_key:
            print("UPLOAD_POST_KEY nao configurado — pulando publicacao.")
        elif not profile:
            print(f"Sem perfil de publicação para '{character_id}' — pulando publicacao.")

    print(f"\nPronto!")
    print(f"   Video final: {video_final}")
    print(f"   Thumbnail:   {thumbnail}")


if __name__ == "__main__":
    main()