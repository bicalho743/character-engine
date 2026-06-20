# 🎬 OpenShorts.app & Character Engine (Fábrica de Personagens)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

Uma plataforma integrada de vídeo com inteligência artificial para **geração de cortes virais**, **criação de vídeos UGC com atores de IA (SaaS/Produtos)** e uma **Fábrica de Personagens virtuais com identidade própria ("alma")**. Este repositório oferece ferramentas via interface gráfica (painel web FastAPI/Vite) e via CLI (linha de comando).

---

## 📌 Visão Geral das Funcionalidades

### 1. Clip Generator (Gerador de Cortes)
Transforma vídeos longos (podcasts, entrevistas, aulas) em vídeos verticais (9:16) ideais para TikTok, Instagram Reels e YouTube Shorts.
- **Detecção de Momentos Virais**: Analisa a transcrição com IA (Google Gemini 3.0/3.5) para isolar de 3 a 15 trechos de alto engajamento.
- **Corte Inteligente 9:16 (Active Speaker Tracking)**: Rastreia o locutor usando MediaPipe e YOLOv8 com estabilização inteligente (Heavy Tripod).
- **Legendas Automáticas**: Transcrição rápida com word-level timestamps e queima de legendas estilizadas no vídeo.
- **Dublagem com IA**: Tradução de voz automática mantendo o tom e a emoção original (via ElevenLabs).

### 2. AI Shorts / UGC Creator (Criador de Vídeos de Marketing)
Gera vídeos publicitários a partir de uma URL ou descrição curta de um produto ou serviço.
- **Pesquisa e Análise de Mercado**: Scrape automático do site e pesquisa no Google Search (via Gemini) buscando depoimentos reais, concorrentes e dores dos clientes.
- **Roteirização Viral**: Cria roteiros no formato gancho (hook) -> problema -> solução -> CTA.
- **Atores Virtuais**: Geração de retratos hiper-realistas com Flux 2 Pro ou Recraft V4 e animação facial sincronizada com a voz (Kling Avatar v2 ou Hailuo + VEED).

### 3. Fábrica de Personagens Fixos (Character Engine)
Motor CLI projetado para criar e alimentar canais de personagens virtuais fixos de forma totalmente automatizada.
- **Arquitetura 1 Motor, N Personagens**: Cada personagem possui sua própria pasta de configuração (`persona.md`, `character.yaml`, `topics.yaml`).
- **Fila de Tópicos Automática**: Consome temas em sequência e gerencia o status de postagem.
- **Pós-processador Avançado**: Adiciona legendas de alto impacto, gera capas personalizadas (thumbnails) e publica ou agenda nas redes sociais através da API do Upload-Post.

---

## 🗺️ Estrutura do Repositório e Lista Completa de Funções

Abaixo estão detalhados todos os arquivos e scripts que constituem o sistema, acompanhados de suas respectivas classes, métodos e fluxos de execução.

---

### 📂 CLI & Controle de Personagens

#### 📄 [generate_character.py](file:///c:/2 - PERSONAGENS/character-engine/generate_character.py)
Script de interface de linha de comando (CLI) para a geração de roteiros, vozes e vídeos de personagens baseados em suas personas e tópicos pendentes.
*   `list_characters()`: Varre a pasta `characters/` e lista os personagens que possuem um arquivo `character.yaml` válido.
*   `list_topics(character_id)`: Lê a lista de tópicos em `topics.yaml` para o personagem informado.
*   `print_script(script)`: Exibe o roteiro gerado no console com marcações de blocos, narração detalhada e ideias de b-roll.
*   `save_script(script, topic, output_dir)`: Salva os arquivos de roteiro nos formatos JSON, TXT e o texto da legenda/caption em arquivos individuais.
*   `generate_voiceover(text, voice_id, elevenlabs_key, output_path, voice_settings)`: Converte o texto do roteiro em áudio usando a API do ElevenLabs (modelo `eleven_multilingual_v2`), aplicando configurações de estabilidade e clareza.
*   `generate_kling_avatar(image_path, audio_path, fal_key, output_path)`: Envia o avatar base e o áudio da narração para a API do Kling (via fal.ai) para gerar o vídeo do personagem falando de forma realista.

#### 📄 [post_process.py](file:///c:/2 - PERSONAGENS/character-engine/post_process.py)
Realiza todo o pós-processamento necessário no vídeo falante gerado. Cuida de legendagem, criação de capas e publicação automatizada.
*   `remove_acentos(texto)`: Normaliza strings removendo acentos para uso na geração de mídias do FFmpeg.
*   `get_video_dimensions(video_path)`: Obtém largura e altura do vídeo com `ffprobe`.
*   `gerar_srt(audio_path, srt_path)`: Transcreve o áudio usando `faster-whisper` com word-level timestamps e agrupa as palavras em blocos curtos de legenda (limite de 6 palavras ou 32 caracteres por bloco).
*   `gerar_video_legendado(video_path, srt_path, hook_text, output_path)`: Aplica as legendas em formato SRT diretamente no vídeo (burn-in) com estilo personalizado e fontes do Windows usando FFmpeg.
*   `gerar_thumbnail(video_path, hook_text, output_path)`: Cria uma imagem estática a partir de um frame do vídeo com o texto do gancho (hook) formatado em caixa preta e fundo branco (estilo TikTok).
*   `inserir_thumbnail_no_video(video_path, thumbnail_path, output_path)`: Insere a capa (thumbnail) como o primeiro segundo de frame do vídeo. Útil para que o Instagram Reels a use automaticamente como capa do vídeo.
*   `publicar_video(video_path, thumbnail_url, titulo, caption, upload_post_key, perfis, ...)`: Envia o vídeo e metadados para as redes sociais (Instagram Reels, TikTok, YouTube Shorts, X) através da API do Upload-Post. Suporta agendamentos futuros.

#### 📄 [character_shorts.py](file:///c:/2 - PERSONAGENS/character-engine/character_shorts.py)
Módulo interno que implementa as regras da "alma" e formatação de prompt para os personagens.
*   `load_character(character_id)`: Carrega a configuração (`character.yaml`), as definições de personalidade (`persona.md`) e os tópicos (`topics.yaml`) do diretório do personagem.
*   `pick_next_topic(character, mark_done)`: Seleciona o próximo tema pendente da fila do personagem e atualiza o status para `done` se solicitado.
*   `generate_character_script(character, topic, openai_key, gemini_key)`: Constrói os prompts detalhados e utiliza OpenAI (GPT-4o-Mini) ou Google Gemini (Gemini 2.5 Flash) para gerar o roteiro estruturado no formato JSON com as tags de modulação de voz ElevenLabs (ex: `[serious]`, `[soft]`, `[calm]`).

#### 📄 [run_batch.py](file:///c:/2 - PERSONAGENS/character-engine/run_batch.py)
Script utilitário para agendar e gerar múltiplos vídeos de personagens em lote (batch).
*   `main()`: Lê uma lista de tarefas agendadas, gera os vídeos chamando sequencialmente `generate_character.py` com o argumento `--from-script` e executa o pós-processamento `post_process.py` agendando cada postagem.

---

### 📂 Pipeline de Processamento de Vídeo

#### 📄 [main.py](file:///c:/2 - PERSONAGENS/character-engine/main.py)
O coração do pipeline do abridor de vídeos (Clip Generator). Contém toda a lógica de enquadramento automático e identificação de clipes.
*   **Classe `SmoothedCameraman`**:
    *   `update_target(face_box)`: Atualiza o ponto focal horizontal da câmera com base na posição da face detectada.
    *   `get_crop_box(force_snap)`: Calcula a janela de recorte 9:16 aplicando amortecimento linear e zona de segurança (Heavy Tripod) para evitar oscilações.
*   **Classe `SpeakerTracker`**:
    *   `get_target(face_candidates, frame_number, width)`: Rastreia as faces identificadas ao longo dos frames e gerencia a quem a câmera deve focar, prevenindo cortes e transições bruscas de câmera caso outra pessoa passe na frente.
*   `detect_face_candidates(frame)`: Executa a detecção facial ultrarrápida usando o detector do MediaPipe.
*   `detect_person_yolo(frame)`: Método fallback que detecta pessoas usando YOLOv8 caso o detector facial não encontre rostos.
*   `create_general_frame(frame, output_width, output_height)`: Cria o layout de plano geral com fundo borrado (blur) e vídeo horizontal centralizado para segmentos com múltiplos interlocutores ou paisagens.
*   `analyze_scenes_strategy(video_path, scenes)`: Analisa frames de cada cena identificada para decidir se o enquadramento deve ser individual (`TRACK`) ou plano aberto (`GENERAL`).
*   `detect_scenes(video_path)`: Utiliza PySceneDetect para encontrar limites lógicos de cortes de cena no vídeo original.
*   `download_youtube_video(url, output_dir)`: Faz o download de vídeos do YouTube de forma robusta contornando rate limits através do `yt-dlp`.
*   `process_video_to_vertical(input_video, final_output_video)`: Orquestra o processamento frame a frame do vídeo horizontal para vertical mesclando as trilhas de vídeo ajustada e áudio copiado.
*   `transcribe_video(video_path)`: Transcreve o vídeo por completo usando `faster-whisper` e gera metadados contendo timestamps por palavra.
*   `get_viral_clips(transcript_result, video_duration)`: Envia a transcrição integral ao Gemini para que selecione os clipes com maior potencial de viralização.

#### 📄 [saasshorts.py](file:///c:/2 - PERSONAGENS/character-engine/saasshorts.py)
Script responsável por gerar vídeos UGC para SaaS de maneira automatizada a partir de links públicos.
*   `research_saas_online(url, gemini_key)`: Executa pesquisas na web com Google Search Grounding usando Gemini para encontrar avaliações, reclamações e pontos fortes da marca.
*   `scrape_website(url)`: Varre a página principal e as subpáginas mais relevantes do SaaS capturando textos estruturados.
*   `analyze_saas(scraped_data, gemini_key, web_research)`: Processa o conteúdo do site e a pesquisa externa gerando um dossiê com públicos-alvo, dores principais e ganchos de atração.
*   `generate_scripts(analysis, gemini_key, num_scripts, style, ...)`: Roteiriza os vídeos baseados no público desejado respeitando uma estrutura rígida de 5 segmentos.
*   `generate_actor_images(description, fal_key, output_dir, title_slug, ...)`: Gera alternativas de fotos para o ator da campanha utilizando Flux 2 Pro no fal.ai.
*   `generate_voiceover(text, elevenlabs_key, output_path, voice_id)`: Gera a narração da propaganda.

#### 📄 [editor.py](file:///c:/2 - PERSONAGENS/character-engine/editor.py)
Fornece integração com o Gemini para analisar vídeos e criar filtros dinâmicos de FFmpeg (correção de cor, corte de silêncio, zoom panorâmico, aplicação de vinheta).
*   `upload_video(file_path)`: Faz upload do arquivo temporário para a API de arquivos do Gemini.
*   `get_ffmpeg_filter(video_file, duration, ...)`: Solicita ao Gemini que assista ao vídeo e sugira uma string de filtros complexos do FFmpeg.
*   `apply_edits(input_path, output_path, filter_data)`: Executa a linha de comando do FFmpeg aplicando os filtros determinados pela IA.

---

### 📂 Integração com API (FastAPI)

#### 📄 [app.py](file:///c:/2 - PERSONAGENS/character-engine/app.py)
Servidor HTTP FastAPI que provê a API para o painel de controle web (Dashboard React).
*   **Fila Assíncrona de Tarefas**: Implementa um loop baseado em `asyncio.Queue` controlado pelo semáforo `concurrency_semaphore` (definido por `MAX_CONCURRENT_JOBS`).
*   `cleanup_jobs()`: Tarefa em segundo plano que purga arquivos temporários de uploads e saídas a cada 1 hora.
*   **Endpoints Principais**:
    *   `POST /api/process`: Inicia o processamento de um novo vídeo horizontal (via upload de arquivo ou URL do YouTube) gerando os cortes verticais.
    *   `GET /api/status/{job_id}`: Retorna os logs de progresso e resultados de um job.
    *   `POST /api/edit`: Aplica filtros de vídeo inteligentes via `editor.py`.
    *   `POST /api/subtitle`: Gera e queima legendas personalizadas.
    *   `POST /api/translate`: Executa a tradução e dublagem de voz do clipe selecionado.
    *   `POST /api/render`: Faz proxy com o microsserviço Node.js de renderização do Remotion.
    *   `POST /api/social/post`: Agenda ou realiza a postagem direta dos vídeos processados no Instagram/TikTok/YouTube.

---

### 📂 Utilitários de Apoio

*   **[s3_uploader.py](file:///c:/2 - PERSONAGENS/character-engine/s3_uploader.py)**: Responsável pelas operações de backup e hospedagem em buckets da AWS S3 (armazenamento privado de cortes e público de galeria de vídeos e avatares).
*   **[subtitles.py](file:///c:/2 - PERSONAGENS/character-engine/subtitles.py)**: Utilitários auxiliares para converter transcrições em arquivos `.srt` e queimar legendas.
*   **[thumbnail.py](file:///c:/2 - PERSONAGENS/character-engine/thumbnail.py)**: Gerador automatizado de capas de vídeo do YouTube e títulos chamativos baseado no conteúdo transcrito.
*   **[translate.py](file:///c:/2 - PERSONAGENS/character-engine/translate.py)**: Gerencia o fluxo de tradução e dublagem de voz utilizando ElevenLabs.
*   **[hooks.py](file:///c:/2 - PERSONAGENS/character-engine/hooks.py)**: Utilitário baseado em Pillow (PIL) para renderização e posicionamento de overlays de ganchos textuais (hooks) em vídeo.

---

## 🛠️ Scripts de Validação

O projeto conta com scripts dedicados à verificação local rápida de estética e geração de sobreposições de imagens:
- **`verify_aesthetic.py`**: Gera e valida a qualidade estética do texto de hook com efeito de sombra.
- **`verify_hooks.py`**: Valida se o pipeline do Pillow consegue criar e salvar com sucesso os arquivos de imagens dos ganchos textuais.
- **`verify_custom_hook.py`**: Testa o redimensionamento dinâmico e o posicionamento do hook no vídeo final.

---

## 🚀 Como Iniciar

### Requisitos Mínimos
- Python 3.10 ou superior instalado localmente.
- Docker e Docker Compose (caso opte pela execução em contêineres).
- FFmpeg configurado no PATH do sistema.

### Configuração (.env)
Copie o arquivo `.env.example` para `.env` e preencha as chaves de API necessárias:
```bash
GEMINI_API_KEY=...        # Obtenha em aistudio.google.com (Uso geral do sistema)
FAL_KEY=...               # Obtenha em fal.ai (Geração de imagens de Atores/Kling)
ELEVENLABS_API_KEY=...    # Obtenha em elevenlabs.io (Geração de Voz/Dublagem)
UPLOAD_POST_KEY=...       # Obtenha em upload-post.com (Agendamento de Redes Sociais)
AWS_ACCESS_KEY_ID=...     # Opcional (Para Backup em Nuvem S3)
AWS_SECRET_ACCESS_KEY=... # Opcional
```

### Inicializando a Dashboard Web (Via Docker)
Para rodar a plataforma completa (Backend + Dashboard Frontend + Renderizador Remotion):
```bash
docker compose up --build
```
Acesse o painel web através do endereço **`http://localhost:5175`**.

### Inicializando a Fábrica de Personagens (CLI)
Para operar a geração e publicação de personagens fixos usando os scripts locais:

```bash
# Instale as dependências
pip install -r requirements.txt

# 1. Listar personagens ativos
python generate_character.py --list-characters

# 2. Testar a roteirização de um tema específico (sem custos extras de vídeo)
python generate_character.py -c frei_miguel_lucero --next --script-only

# 3. Gerar o vídeo completo a partir de um roteiro revisado e aprovado
python generate_character.py -c frei_miguel_lucero --from-script output/frei_miguel_lucero/tema_roteiro.json

# 4. Processar e publicar o vídeo gerado imediatamente nas redes configuradas
python post_process.py -c frei_miguel_lucero --publish output/frei_miguel_lucero/video_final.mp4 output/frei_miguel_lucero/video_voice.mp3 "Texto de Gancho" output/final_post/
```
