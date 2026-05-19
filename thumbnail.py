"""Compat shim: re-exports openshorts.thumbnails.* at the original import path.

This module was split into three files as part of the restructure:
- openshorts/thumbnails/titles.py        (analyze_video_for_titles, refine_titles)
- openshorts/thumbnails/images.py        (generate_thumbnail)
- openshorts/thumbnails/descriptions.py  (generate_youtube_description)

New code should import from those modules directly. This shim keeps existing
`from thumbnail import ...` calls working.
"""
from openshorts.thumbnails.titles import (  # noqa: F401
    analyze_video_for_titles,
    refine_titles,
)
from openshorts.thumbnails.images import generate_thumbnail  # noqa: F401
from openshorts.thumbnails.descriptions import generate_youtube_description  # noqa: F401
