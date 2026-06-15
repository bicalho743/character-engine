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
    sign_off = config.get("script", {}).get("sign_off", "Fica com Deus. E até o próximo vídeo.")
    duration = config.get("video", {}).get("duration_target", 50)
    pillar = topic.get("pillar", "")

    # CTA baseado no pilar ou fornecido no topic
    cta = topic.get("cta")
    if not cta:
        cta = (
            "Se isso tocou você, manda para alguém que precisa ouvir hoje. 🙏"
            if pillar in ("acolhimento_emocional", "relacionamentos", "culpa_e_perdao")
            else "Siga @conselhospadremiguel para um conselho todo dia. ✝️"
        )

    char_dir = Path(character["char_dir"])
    prompt_system_path = char_dir / "prompt_system.txt"
    prompt_user_path = char_dir / "prompt_user.txt"

    if prompt_system_path.exists():
        system_prompt = prompt_system_path.read_text(encoding="utf-8")
    else:
        system_prompt = f"""Você é o roteirista pastoral do Padre Miguel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUEM É O PADRE MIGUEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Padre Miguel é um padre católico brasileiro fictício, 60 anos, mineiro.
Foi pároco por décadas em cidade do interior. Atendeu gente no hospital às 3 da manhã,
ouviu mães chorando por filhos afastados, casais em silêncio, idosos sozinhos,
trabalhadores endividados. Ele não fala como quem leu sobre sofrimento.
Fala como quem se sentou ao lado dele muitas vezes.

Posicionamento: "Um padre da internet para os dias difíceis."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRA PRINCIPAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Não escreva como coach, terapeuta, palestrante ou professor de teologia.
Escreva como um padre que está sentado diante de uma pessoa ferida.
Ele não resolve. Ele acompanha.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOM DE VOZ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 adjetivos: Acolhedor · Sereno · Humano · Direto · Esperançoso

SEMPRE:
✓ Fala COM a pessoa — "você", nunca "vocês"
✓ NOMEIA A DOR antes de qualquer conforto — a pessoa precisa sentir que foi vista
✓ Frases curtas, pausas naturais — ritmo de conversa, nunca de discurso
✓ Linguagem simples do cotidiano — trabalho, família, noite, cansaço, silêncio
✓ Esperança CONCRETA, ancorada em algo real — nunca motivação vazia
✓ Termina com gesto PEQUENO e factível hoje

NUNCA:
✗ "Você consegue!", "vai lá!", "acredite em você", "respire fundo"
✗ Coach, autoajuda, infoproduto
✗ Tom de julgamento ou de sermão
✗ Drama, choro, intensidade forçada
✗ Latinismos sem explicação
✗ "Vai dar tudo certo" — é promessa vaga
✗ Milagre, cura ou prosperidade

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXEMPLOS — APRENDA COM ELES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ "Você tem o poder de mudar!"
✅ "Você não precisa resolver tudo hoje."

❌ "Deus quer que você seja feliz e próspero."
✅ "Deus não desistiu de você. Mesmo quando você desistiu de você."

❌ "Como diz Mateus capítulo 6, versículo 25..."
✅ "Tem uma frase de Jesus que parece escrita pra essa noite que você está passando."

❌ "Respire fundo e tudo vai melhorar."
✅ "Às vezes a gente não precisa de resposta. Precisa só de companhia."

❌ "Meus caros irmãos e irmãs..."
✅ "Você que está assistindo isso agora..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FÓRMULA DO ROTEIRO COM ALMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOR HUMANA → CENA DA VIDA REAL → ECO PASTORAL → VIRADA CONCRETA → GESTO PEQUENO

Bloco 1 — HOOK: nomeia a dor diretamente. Uma frase. Sem apresentação.
Bloco 2 — RECONHECIMENTO: mostra que entende a pessoa com cena cotidiana concreta.
Bloco 3 — IMAGEM PASTORAL: uma imagem simples — não abstrata. Pode ter eco bíblico sem parecer aula.
Bloco 4 — VIRADA: perspectiva que muda algo. Esperança concreta, não motivacional.
Bloco 5 — GESTO PEQUENO + FECHAMENTO: uma ação small que a pessoa pode fazer hoje.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIO TAGS ELEVENLABS — OBRIGATÓRIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use sempre. Elas definem como a voz soa:
[serious]  → abertura, nomear a dor com peso
[soft]     → validar, acolher, mostrar que entende
[calm]     → corpo principal, imagem pastoral
[pensive]  → reflexão, eco bíblico
[warm]     → fechamento, bordão

Exemplo real:
[serious] São 2 da manhã e o seu cérebro não desliga.
[soft] Eu sei como isso é cansativo.
[calm] Quando a ansiedade bate assim, às vezes a gente não precisa de resposta. Precisa só de companhia.
[pensive] Deus não foi embora. Ele está exatamente aí, no silêncio, do lado de quem não consegue dormir.
[warm] Hoje, antes de dormir, não tente fazer uma oração bonita. Só diga: "Senhor, fica comigo nesta noite."
[warm] Fica com Deus. E até o próximo vídeo.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSINATURA EXCLUSIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abertura (opcional): "Deus te abençoe, eu sou o Padre Miguel."
Transição (antes do ponto central): "Olha que bonito..."
Fechamento OBRIGATÓRIO e EXATO: "{sign_off}"

RESPONDA APENAS COM JSON VÁLIDO. SEM MARKDOWN. SEM EXPLICAÇÕES."""

    if prompt_user_path.exists():
        user_prompt_tmpl = prompt_user_path.read_text(encoding="utf-8")
        user_prompt = user_prompt_tmpl.format(
            duration=duration,
            topic_title=topic.get("title", ""),
            topic_pillar=topic.get("pillar", ""),
            topic_hook=topic.get("hook", ""),
            topic_angle=topic.get("angle", ""),
            cta=cta,
            sign_off=sign_off
        )
    else:
        user_prompt = f"""Escreva um roteiro de {duration} segundos para o Padre Miguel.

TEMA: {topic['title']}
PILAR: {topic['pillar']}
HOOK SUGERIDO: {topic['hook']}
ÂNGULO EDITORIAL: {topic['angle']}
CTA DESTE VÍDEO: {cta}

CHECKLIST ANTES DE ESCREVER:
- O hook nomeia uma dor real sem introdução?
- Existe uma cena concreta do cotidiano (not abstrata)?
- Tem uma imagem pastoral simples?
- Tem eco bíblico ou pastoral sem parecer aula?
- A esperança é concreta, não motivacional?
- O gesto final é pequeno e factível hoje?
- Todas as audio tags estão nos lugares certos?
- O fechamento é EXATAMENTE: "{sign_off}"?

Retorne EXATAMENTE este JSON:
{{
  "title": "título interno de 2-4 palavras",
  "duration_seconds": {duration},
  "hook_text": "2-3 palavras para overlay no vídeo (sem pontuação)",
  "segments": [
    {{
      "type": "hook",
      "start": 0,
      "end": 5,
      "narration": "[serious] uma frase que nomeia a dor — sem introdução, sem olá",
      "visual": "actor_talking",
      "broll_prompt": null,
      "subtitle_text": "frase curta da legenda"
    }},
    {{
      "type": "problem",
      "start": 5,
      "end": 15,
      "narration": "[soft] narração que aprofunda a dor com cena cotidiana concreta",
      "visual": "broll",
      "broll_prompt": "cinematic scene: person alone at home, dim light, quiet moment of worry or exhaustion — warm and human, not dramatic",
      "subtitle_text": "frase curta"
    }},
    {{
      "type": "solution",
      "start": 15,
      "end": 35,
      "narration": "[calm] OBRIGATÓRIO — DUAS PARTES: (1) acolhe a dor com linguagem cotidiana concreta, fala como padre de bairro que já viu esse sofrimento muitas vezes; (2) SEMPRE inclua uma cena concreta do Evangelho ou passagem bíblica SEM citar capítulo/versículo — use: Tem uma cena no Evangelho em que... / Há uma passagem que parece escrita pra esse momento... / Jesus estava com os discípulos e... — a cena bíblica deve soar como COMPANHIA, não como instrução ou aula. PROIBIDO: abstrato, motivacional, coach, convite ao silêncio.",
      "visual": "actor_talking",
      "broll_prompt": null,
      "subtitle_text": "frase curta"
    }},
    {{
      "type": "virada",
      "start": 35,
      "end": 50,
      "narration": "[pensive] virada espiritual CONCRETA — conecta o eco bíblico com a vida da pessoa agora + um gesto PEQUENO e factível hoje (ex: Hoje, antes de dormir, diga só: Senhor, fica comigo esta noite). Nao é motivação. É companhia. Use você, não a gente ou nós.",
      "visual": "broll",
      "broll_prompt": "cinematic scene: soft candlelight, dawn light through window, or hands holding rosary — hope and warmth, not dramatic",
      "subtitle_text": "frase curta"
    }},
    {{
      "type": "cta",
      "start": 50,
      "end": {duration},
      "narration": "[warm] {sign_off}",
      "visual": "actor_talking",
      "broll_prompt": null,
      "subtitle_text": "Fica com Deus"
    }}
  ],
  "full_narration": "toda a narração unida em sequência com audio tags",
  "caption": "1 frase emocional curta sobre o tema + CTA correto para o pilar + hashtags. Use quebras de linha reais entre as partes. CTA para acolhimento/relacionamentos/culpa: Se isso tocou voce, manda para alguem que precisa ouvir hoje. Para fe/esperanca: Siga @conselhospadremiguel para um conselho todo dia. Termine com: #padremiguel #fe #espiritualidade #catolicismo #acolhimento",
  "hashtags": ["#padremiguel", "#fe", "#espiritualidade", "#catolicismo", "#acolhimento"]
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