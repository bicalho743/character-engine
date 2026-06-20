# SKILL 05 — Voz Sonora
## Personagem: Frei Miguel Lucero

---

## Perfil da voz

| Atributo | Descrição |
|---|---|
| Plataforma | ElevenLabs — modelo `eleven_multilingual_v2` |
| Gênero | Masculino |
| Timbre | Médio-grave, claro, ressonante — mais firme e penetrante que o Padre |
| Ritmo | Pausado, com silêncios deliberados — o silêncio cria a tensão antes da revelação |
| Tom | Reflexivo com peso, intencional — de quem descobriu algo e precisa te contar |
| Sotaque | Português brasileiro neutro com leve calor; menos "interiorano" que o Padre, mais "sábio" |

> **Critério de diferenciação:** a voz do Frei deve soar **mais firme, mais "desperta" e ligeiramente mais jovem** que a do Padre Miguel (que é barítono caloroso e mais idoso). Se as duas vozes pudessem ser confundidas, escolha outra para o Frei.

---

## Configurações ElevenLabs

```yaml
voice_id: PREENCHER_APÓS_ESCOLHA
model: eleven_multilingual_v2
stability: 0.50          # um pouco mais de variação expressiva que o Padre (0.55)
similarity_boost: 0.80
style: 0.40              # mais "presença"/intenção que o Padre (0.30)
use_speaker_boost: true
```

---

## Audio tags recomendadas (ElevenLabs v3)

| Tag | Quando usar |
|---|---|
| `[serious]` | Hook de tensão — abrir com peso |
| `[curious]` | Ganchos de curiosidade ("existe uma oração que quase ninguém ensina") |
| `[calm]` | Corpo principal, condução de oração |
| `[pensive]` | Momentos de reflexão e pausa |
| `[warm]` | Virada esperançosa e fechamento com o bordão |

---

## Exemplo de roteiro com audio tags

```
[curious] Se você continua acordando entre 2 e 4 da manhã,
  não ignore isso tão rápido.
[serious] Talvez não seja só insônia.
[pensive] Às vezes é o seu coração tentando dizer aquilo que você
  passou o dia inteiro tentando calar.
[calm] Não entre em pânico. Não veja como castigo.
  Veja como um convite.
[calm] Feche os olhos. Respire. E pergunte:
  Senhor, o que o meu coração está tentando me mostrar?
[warm] Que Deus ilumine o seu caminho. Paz e bem.
```

---

## Critério de escolha da voz

A voz do Frei Miguel Lucero deve passar imediatamente a sensação de:
- Um homem que **viu muito e entende o que você sente** antes de você terminar de falar
- Que tem uma **calma intencional**, não passiva — calma de quem sabe algo
- Que fala devagar porque cada palavra **carrega peso**, não porque está lendo

Teste sempre com um trecho de **tensão real** (um hook de curiosidade ou dor), não com uma frase neutra.
A voz deve soar **distinta da voz do Padre Miguel** (mais idoso, mais acolhedor) e da voz do Theo (mais jovem, mais leve).
