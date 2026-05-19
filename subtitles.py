"""Compat shim: re-exports openshorts.overlays.subtitles_* at the original path.

This module was split into two files as part of the restructure:
- openshorts/overlays/subtitles_generate.py (transcribe + SRT writing)
- openshorts/overlays/subtitles_render.py  (FFmpeg subtitles burn-in)

New code should import from those modules directly. This shim keeps existing
`from subtitles import ...` calls working.
"""
from openshorts.overlays.subtitles_generate import (  # noqa: F401
    transcribe_audio,
    generate_srt_from_video,
    generate_srt,
    format_srt_block,
)
from openshorts.overlays.subtitles_render import (  # noqa: F401
    hex_to_ass_color,
    burn_subtitles,
)
