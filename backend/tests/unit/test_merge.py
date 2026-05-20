"""Tests for the Phase 4 merge helper.

Covers the public surface of ``app.video.merge.concat_clips``: input
validation, filter-graph composition, output path derivation, and the
FFmpeg invocation contract (only via the wrapper).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.video.merge import (
    NORMALIZE_FILTER,
    build_concat_args,
    concat_clips,
)


def test_normalize_filter_targets_1080x1920_30fps():
    # Output normalized to 9:16 1080x1920 @ 30fps so concat can succeed
    # regardless of source resolution / fps.
    assert "scale=1080:1920" in NORMALIZE_FILTER
    assert "fps=30" in NORMALIZE_FILTER
    assert "setsar=1" in NORMALIZE_FILTER
    assert "format=yuv420p" in NORMALIZE_FILTER


def test_build_concat_args_two_inputs(tmp_path):
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    out = tmp_path / "merged.mp4"

    args = build_concat_args([str(a), str(b)], str(out))

    # Both inputs declared with -i.
    assert args.count("-i") == 2
    # Filter graph references the normalize chain once per input, then concat.
    fc_index = args.index("-filter_complex")
    fc = args[fc_index + 1]
    assert "[0:v]" in fc and "[1:v]" in fc
    assert "[0:a]" in fc and "[1:a]" in fc
    assert "concat=n=2:v=1:a=1" in fc
    # Audio re-encoded to AAC 48 kHz stereo for clean concat.
    assert "-c:a" in args and args[args.index("-c:a") + 1] == "aac"
    assert "-ar" in args and args[args.index("-ar") + 1] == "48000"
    assert "-ac" in args and args[args.index("-ac") + 1] == "2"
    # Video re-encoded with libx264.
    assert "-c:v" in args and args[args.index("-c:v") + 1] == "libx264"
    # Output path is the last positional argument.
    assert args[-1] == str(out)


def test_build_concat_args_three_inputs_concat_n_matches(tmp_path):
    paths = []
    for name in ("a.mp4", "b.mp4", "c.mp4"):
        p = tmp_path / name
        p.write_bytes(b"x")
        paths.append(str(p))
    out = tmp_path / "merged.mp4"

    args = build_concat_args(paths, str(out))
    fc = args[args.index("-filter_complex") + 1]
    assert "concat=n=3:v=1:a=1" in fc
    for i in range(3):
        assert f"[{i}:v]" in fc
        assert f"[{i}:a]" in fc


def test_concat_clips_rejects_empty_list(tmp_path):
    with pytest.raises(ValueError) as exc:
        concat_clips([], str(tmp_path / "out.mp4"))
    assert "at least" in str(exc.value).lower()


def test_concat_clips_rejects_single_input(tmp_path):
    a = tmp_path / "a.mp4"
    a.write_bytes(b"x")
    with pytest.raises(ValueError) as exc:
        concat_clips([str(a)], str(tmp_path / "out.mp4"))
    assert "at least 2" in str(exc.value).lower()


def test_concat_clips_rejects_missing_input(tmp_path):
    a = tmp_path / "a.mp4"
    a.write_bytes(b"x")
    missing = tmp_path / "ghost.mp4"
    with pytest.raises(FileNotFoundError):
        concat_clips([str(a), str(missing)], str(tmp_path / "out.mp4"))


def test_concat_clips_invokes_ffmpeg_with_expected_filter(tmp_path):
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    out = tmp_path / "merged.mp4"

    def fake_run(args, **_kwargs):
        # Mimic a successful ffmpeg run by creating the output file.
        out.write_bytes(b"merged")
        return None

    with patch("app.video.merge.ffmpeg_wrapper.run", side_effect=fake_run) as run_mock:
        result = concat_clips([str(a), str(b)], str(out))

    assert result == str(out)
    args = run_mock.call_args.args[0]
    fc = args[args.index("-filter_complex") + 1]
    assert "concat=n=2:v=1:a=1" in fc


def test_concat_clips_raises_when_ffmpeg_produces_empty_output(tmp_path):
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    out = tmp_path / "merged.mp4"

    with patch("app.video.merge.ffmpeg_wrapper.run") as run_mock:
        run_mock.return_value = None
        with pytest.raises(RuntimeError) as exc:
            concat_clips([str(a), str(b)], str(out))
        assert "empty output" in str(exc.value)
