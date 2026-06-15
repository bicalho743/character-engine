import os
import sys
import json
import subprocess
from pathlib import Path

# Definindo o mapeamento de dias, arquivos e datas de agendamento
BATCH_JOBS = [
    {
        "day": 4,
        "script_name": "dia04_casamento_esfria.json",
        "hook_text": "Voce olha para o lado e parece que viraram colegas",
        "scheduled": "2026-06-18 08:00"
    },
    {
        "day": 5,
        "script_name": "dia05_recomecar_erro.json",
        "hook_text": "Voce fez algo que nao esperava ser capaz de fazer",
        "scheduled": "2026-06-19 08:00"
    },
    {
        "day": 6,
        "script_name": "dia06_amanha_voce_vai_acordar.json",
        "hook_text": "Amanha voce vai acordar",
        "scheduled": "2026-06-20 08:00"
    },
    {
        "day": 7,
        "script_name": "dia07_solidao_multidao.json",
        "hook_text": "Solidao no meio de muita gente",
        "scheduled": "2026-06-21 08:00"
    },
    {
        "day": 8,
        "script_name": "dia08_fe_duvidando.json",
        "hook_text": "Ter fe quando esta duvidando",
        "scheduled": "2026-06-22 08:00"
    },
    {
        "day": 9,
        "script_name": "dia09_mae_imperfeita.json",
        "hook_text": "A culpa de ser mae imperfeita",
        "scheduled": "2026-06-23 08:00"
    },
    {
        "day": 10,
        "script_name": "dia10_o_que_tem_hoje.json",
        "hook_text": "O que voce tem hoje que e real",
        "scheduled": "2026-06-24 08:00"
    }
]

def run_command(cmd, env=None):
    print(f"\n[EXEC] {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=False)
    if result.returncode != 0:
        raise Exception(f"Comando falhou com codigo {result.returncode}")

def main():
    base_dir = Path(r"C:\2 - PERSONAGENS\character-engine")
    output_dir = base_dir / "output" / "padre_miguel"
    
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    
    for job in BATCH_JOBS:
        day = job["day"]
        script_file = output_dir / job["script_name"]
        
        print(f"\n==================================================")
        print(f"INICIANDO DIA {day:02d}: {job['script_name']}")
        print(f"==================================================")
        
        if not script_file.exists():
            print(f"Erro: Roteiro {script_file} nao encontrado! Pulando...")
            continue
            
        # Determinar nomes dos arquivos de saída gerados pelo generate_character.py
        base_name = script_file.stem  # ex: dia04_casamento_esfria
        video_path = output_dir / f"{base_name}_final.mp4"
        audio_path = output_dir / f"{base_name}_voice.mp3"
        caption_path = output_dir / f"{base_name}_caption.txt"
        day_output_dir = output_dir / f"dia{day:02d}_final"
        
        # Etapa 1: Gerar o vídeo com Kling e voz no ElevenLabs
        print(f"\n--- [1/2] Gerando video do Dia {day:02d} ---")
        gen_cmd = [
            "python", "generate_character.py",
            "-c", "padre_miguel",
            "--from-script", str(script_file)
        ]
        try:
            run_command(gen_cmd, env=env)
        except Exception as e:
            print(f"Erro na geracao do video do Dia {day}: {e}")
            continue
            
        # Etapa 2: Pós-processamento (legendas, thumbnail e publicação/agendamento)
        print(f"\n--- [2/2] Pos-processamento do Dia {day:02d} ---")
        post_cmd = [
            "python", "post_process.py",
            str(video_path),
            str(audio_path),
            job["hook_text"],
            str(day_output_dir),
            str(caption_path),
            job["scheduled"]
        ]
        try:
            run_command(post_cmd, env=env)
        except Exception as e:
            print(f"Erro no pos-processamento do Dia {day}: {e}")
            continue

        print(f"\n✅ Concluido Dia {day:02d} com sucesso!")

if __name__ == "__main__":
    main()
