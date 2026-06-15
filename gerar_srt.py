import whisper

model = whisper.load_model("small")
result = model.transcribe("output/padre_miguel/audio_do_video.wav", language="pt")

def fmt(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

with open("output/padre_miguel/ansiedade_noite_v2.srt", "w", encoding="utf-8") as f:
    for i, seg in enumerate(result["segments"], 1):
        f.write(f"{i}\n{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text'].strip()}\n\n")

print("SRT gerado!")