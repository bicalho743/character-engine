# ROADMAP

Designs and ordering for the three future features the user asked about
during the restructure planning, plus the refactors deliberately deferred
out of the restructure phase so it could ship safely.

The headline rule: **everything below depends on the package structure that
already shipped in Phase 1, plus the single-FFmpeg-wrapper convention.**
Each feature is sized so that it can land in a small handful of atomic
commits with the `pytest -m "not e2e"` suite green between commits.

---

## Ordering (lowest blast radius first)

1. **Feature C — Motion Graphics Library.** Reuses the proven
   FFmpeg-overlay pattern from `openshorts/overlays/hooks.py`. No changes
   to the pipeline hot loop. **Ships first** because the compositor it
   introduces is the prerequisite for feature A's audio batching.
2. **Feature A — Background Soundtracks + SFX with Ducking.** Self-contained
   at the audio layer once C's compositor exists. Integrates at the
   single audio-mux step in `openshorts/video/pipeline.py` — small
   surface area, but it needs the FFmpeg wrapper migration (below) done.
3. **Feature B — Layout Templates.** Last because it touches the hottest
   loop in the codebase. Once C and A have landed, layouts is a clean
   polymorphism extraction with no need to also be inventing infra.

The three deferred refactors interleave naturally:

- Before **A**: finish migrating every `subprocess.run(['ffmpeg', ...])` call to
  `openshorts/video/ffmpeg.py` (Phase 1.10 leftover).
- Before or alongside **B**: split `app.py` into the eleven planned routers
  under `openshorts/routes/` and centralize job state in
  `openshorts/core/job_store.py` (Phase 1.9 leftover).
- Independently: split `openshorts/saas/pipeline.py` into the five planned
  modules (research / scripting / media / compositing / pipeline) (Phase 1.8
  leftover).

---

## Feature C — Motion Graphics Library

### Why first

The hook-overlay code in `openshorts/overlays/hooks.py:add_hook_to_video()`
already proves out the pattern: render PNG via PIL, burn onto video via
FFmpeg `overlay` filter. Generalizing that to "a library of effects, each
rendered to a PNG sequence or alpha .mov, then composited in one ffmpeg
invocation" is a small extension. No changes to the per-frame loop.

### Architecture

```
openshorts/motion_graphics/
├── base.py
│   class MotionGraphicEffect(ABC):
│       def render(self, duration_sec, fps, out_dir) -> Path  # returns PNG seq or .mov with alpha
│       def get_overlay_filter(self, start_sec, end_sec, w, h) -> str   # the FFmpeg filter chain
│
├── compositor.py
│   class MotionGraphicsCompositor:
│       def add(self, effect: MotionGraphicEffect, start_sec, end_sec): ...
│       def render(self, input_video, output_video):
│           # 1. ask each effect for its PNG/mov
│           # 2. build ONE filter_complex chain ([0:v][1:v]overlay=...[v1];[v1][2:v]overlay=...[v2];...)
│           # 3. invoke openshorts.video.ffmpeg.run(...) ONCE — single re-encode
│
└── library/
    ├── lower_thirds.py     class LowerThirdsEffect
    ├── callout.py          class CalloutEffect
    ├── progress_bar.py     class ProgressBarEffect
    └── animated_emoji.py   class AnimatedEmojiEffect
```

### Files to add

- `openshorts/motion_graphics/base.py`
- `openshorts/motion_graphics/compositor.py`
- `openshorts/motion_graphics/library/{lower_thirds,callout,progress_bar,animated_emoji}.py`
- `openshorts/routes/motion_graphics.py` — `GET /api/motion-graphics/library` (lists effects + thumbnails) and `POST /api/motion-graphics/render` (apply a timeline)
- `openshorts/models/motion_graphics.py` — Pydantic schemas (`EffectInstance`, `RenderTimeline`, etc.)
- Frontend: a `MotionGraphicsModal.jsx` matching the existing `HookModal` / `SubtitleModal` pattern (defer until UI work is in scope)

### Integration

The compositor sits *after* the vertical-reframing step and *before* the
audio mux in `openshorts/video/pipeline.py`. Easiest way to wire it in
is to make `process_video_to_vertical()` accept an optional
`motion_graphics_timeline` argument and, if present, route the
silent-video output through the compositor before the audio merge.

### Risks the pipeline analysis flagged

- **Re-encoding per overlay.** Mitigated by the compositor building a
  single `filter_complex` chain — the video is decoded and re-encoded
  exactly once regardless of how many effects are applied.
- **PNG-sequence disk usage.** Each effect writes its frames to a per-clip
  temp dir under `output/<job_id>/_mg/`; cleaned up after the final mux.

---

## Feature A — Background Soundtracks + SFX with Ducking

### Why second

Logically independent of layouts. Needs the FFmpeg wrapper done so
the mixer can compose `amix` + `volume` + `silencedetect` chains cleanly.

### Architecture

```
openshorts/audio/
├── mixer.py
│   def mix_audio_tracks(original_audio, music_track, sfx_cues, output, ducking_db=-18):
│       # 1. Detect speech intervals via Whisper word timings (already cached in metadata.json)
│       #    OR via FFmpeg silencedetect if no transcript available.
│       # 2. Build a `volume` filter on the music track with `enable=between(t,...)` per speech interval.
│       # 3. amix=inputs=2 (original + ducked music) + each SFX cue at its trigger time.
│       # 4. Funnel through openshorts.video.ffmpeg.run(...).
│
├── library.py
│   def list_tracks(genre=None, mood=None, length_sec=None) -> list[TrackMeta]
│       # Reads assets/music/manifest.json — committed file listing tracks under assets/music/
│
└── cues.py
    def generate_sfx_cues(transcript, gemini_key) -> list[SfxCue]
        # Gemini analyzes transcript to suggest SFX moments (zoom-ins, scene changes, hook delivery).
        # Prompt lives at openshorts/prompts/sfx_cues.md.
```

### Files to add

- `openshorts/audio/mixer.py`
- `openshorts/audio/library.py`
- `openshorts/audio/cues.py`
- `openshorts/prompts/sfx_cues.md`
- `openshorts/routes/audio.py` — `POST /api/audio/apply`
- `openshorts/models/audio.py`
- `assets/music/manifest.json` + a small set of CC-licensed tracks (or stub manifest + user uploads in v1)

### Integration

Inside `openshorts/video/pipeline.py:process_video_to_vertical()` at the
existing audio-mux step (today around the `merge_command` block). The
audio mixer takes the original audio from `temp_audio_output`, mixes in
the soundtrack + cues, and writes the mixed audio back over the
intermediate file before the final mux. The video side never sees this.

### Risks

- **Speech-detection accuracy.** When word timings are unreliable
  (background noise, music in the source), fall back to FFmpeg
  `silencedetect=n=-30dB:d=0.5` to bracket speech intervals.
- **Music licensing.** v1 ships with placeholder royalty-free files
  under `assets/music/`. v2 can swap in an Epidemic Sound / Artlist
  client behind `openshorts/integrations/`.

---

## Feature B — Layout Templates

### Why last

Touches the per-frame loop in `openshorts/video/pipeline.py`. The other
two features add new boxes alongside the loop; this one rewrites how the
loop branches. Biggest blast radius — best to land it after C and A are
shipped and the test suite has shaken out any edge cases.

### Architecture

```
openshorts/layouts/
├── base.py
│   class Layout(ABC):
│       def __init__(self, output_w, output_h, video_w, video_h, fps): ...
│       def render_frame(self, frame, detections, frame_number) -> np.ndarray
│       def on_scene_change(self, scene_index): ...    # for cameramen / trackers to snap
│
├── vertical_panorama.py     class VerticalPanoramaLayout    # today's TRACK / GENERAL behavior, polymorphic
├── educational.py           class EducationalLayout         # top half = source content, bottom = presenter headshot
└── side_by_side.py          class SideBySideLayout          # stub for the next variant
```

### Files to add

- `openshorts/layouts/base.py`, `vertical_panorama.py`, `educational.py`, `side_by_side.py`
- `openshorts/routes/layouts.py` — `layout` field accepted on `POST /api/process`; later `POST /api/layout/reapply` to swap layout on an existing job's clips without re-transcribing
- `openshorts/models/layouts.py`

### Pipeline change

The branching at the heart of `process_video_to_vertical()` (the
`if current_strategy == 'GENERAL': ... else: ...` block) becomes:

```python
layout: Layout = layout_registry.get(request.layout)  # default: VerticalPanoramaLayout
# ... in the frame loop:
output_frame = layout.render_frame(frame, detections, frame_number)
```

`VerticalPanoramaLayout` wraps today's `SmoothedCameraman` +
`SpeakerTracker` + `create_general_frame()` exactly as they are — the
restructure already kept those in their own modules precisely to
support this.

`EducationalLayout` owns *two* cameramen — one for the source content
(top half, treated as a screencast crop) and one for the presenter face
(bottom half, tight headshot crop using `detect_face_candidates`).
At each frame, both crops are computed and stacked vertically. If no
face is detected for the presenter slot, falls back to vertical panorama
for that segment.

### Risks

- **Per-frame cost.** Two cameramen + two crops doubles the
  detection / transform cost. Mitigation: detect once per frame; both
  cameramen consume the same `detections` list.
- **Layout-change-mid-clip.** Out of scope for v1 — layout is fixed for
  the whole clip. v2 could allow per-scene layout swaps.

---

## Deferred refactors (Phase 1 leftovers)

| Refactor | Why deferred | Plan |
| --- | --- | --- |
| Full router split of `app.py` | 2256 lines / 32 routes; doing it as one pass would have been risky given the test suite mocks heavy ML deps at the module-import boundary. | Split per the plan: 11 routers under `openshorts/routes/` + `create_app()` factory in `openshorts/app.py`. One router per commit. The OpenAPI snapshot in `tests/snapshots/baseline.openapi.json` is the gate — it must stay byte-identical except when a route is deliberately changed. |
| Migrate every `subprocess.run(['ffmpeg', ...])` to `openshorts/video/ffmpeg.py` | Many call sites (app.py, video/pipeline.py, overlays/*, editing/ai_filters.py, saas/pipeline.py). Migrating all of them in one pass would have ballooned the restructure commit set. | One caller per commit. Tests between. The hook overlay in `overlays/hooks.py:add_hook_to_video()` is a good first migration — small, well-tested. |
| Internal split of `openshorts/saas/pipeline.py` | 1474-line file. No direct test coverage (only via the OpenAPI contract). Splitting it carries risk without the safety net of tests. | Per the original plan: `saas/research.py` (scraping + analyze), `saas/scripting.py`, `saas/media.py` (fal.ai + ElevenLabs TTS), `saas/compositing.py`, `saas/pipeline.py` (orchestrator). Add focused unit tests for the research + scripting + compositing layers as you split them. |
| `openshorts/core/job_store.py` + `api_keys.py` resolver | Today the job-state dicts (`jobs`, `thumbnail_sessions`, `publish_jobs`, `saas_jobs`) live as globals in `app.py`. The router split is a natural place to extract them. | Land alongside the router split, not before — extracting them prematurely just shifts where the globals live without delivering value. |
| Frontend restructure | Explicitly out of scope per the planning Q&A — frontend changes are deferred to a separate round. | When the user is ready: split `dashboard/src/App.jsx` along the same modal-per-feature axes as the backend routes, and introduce a centralized api client. |

---

## What landed in this restructure

For posterity. Phase 0 + Phase 1 + Phases 2-5 produced these commits on
`chore/restructure-and-docs` (newest first):

- `docs(claude.md): add per-folder sub-CLAUDE.md stubs` — five `CLAUDE.md` files at directory boundaries.
- `docs(claude.md): rewrite with structured guidance + auto-managed sections` — the new CLAUDE.md.
- `chore(tooling): add CLAUDE.md auto-updater + pre-commit hook`.
- `docs(env): expand .env.example to match what the code actually reads`.
- `chore(restructure): Dockerfile CMD points at openshorts.app:app`.
- `chore(restructure): add openshorts/video/ffmpeg.py wrapper scaffold`.
- `chore(restructure): add openshorts/app.py re-export for Docker entrypoint`.
- `chore(restructure): move saasshorts -> openshorts/saas/pipeline.py`.
- `chore(restructure): split main.py -> video/* + ml/* + ingest/youtube.py`.
- `chore(restructure): split thumbnail -> thumbnails/{titles,images,descriptions}.py`.
- `chore(restructure): split editor -> editing/ai_filters + editing/prompts + utils/filters`.
- `chore(restructure): split subtitles -> overlays/subtitles_{generate,render}.py`.
- `chore(restructure): move hooks -> openshorts/overlays/hooks.py`.
- `chore(restructure): move translate -> openshorts/integrations/elevenlabs.py`.
- `chore(restructure): move s3_uploader -> openshorts/integrations/s3.py`.
- `chore(restructure): scaffold empty openshorts/ package + extend pyproject`.
- `test: add Phase 0 safety net before restructure`.

The revert point: `git tag pre-restructure-20260519-1526`. `git reset --hard
pre-restructure-20260519-1526` returns the tree to its pre-restructure state.
