"""Compat shim: re-exports openshorts.integrations.elevenlabs at the original path.

This module moved to openshorts/integrations/elevenlabs.py as part of the
restructure. New code should import from `openshorts.integrations.elevenlabs`
directly; this shim keeps existing `from translate import ...` calls working.
"""
from openshorts.integrations.elevenlabs import *  # noqa: F401,F403
from openshorts.integrations.elevenlabs import (  # noqa: F401
    SUPPORTED_LANGUAGES,
    ELEVENLABS_API_BASE,
    create_dubbing_project,
    get_dubbing_status,
    download_dubbed_video,
    translate_video,
    get_supported_languages,
)
