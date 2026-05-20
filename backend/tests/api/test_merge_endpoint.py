"""Contract tests for POST /api/merge.

Validates the request schema (bounds checks, dedup, transition allowlist) and
the integration with the in-memory job store. The actual ffmpeg invocation is
mocked at ``app.video.merge.concat_clips`` so the test runs without ffmpeg.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    (tmp_path / "uploads").mkdir(exist_ok=True)
    (tmp_path / "output").mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app, jobs

    # Seed a fake completed job with 3 clips.
    job_id = "test-merge-job"
    job_dir = tmp_path / "output" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    clip_files = []
    for i in range(3):
        p = job_dir / f"_clip_{i}.mp4"
        p.write_bytes(b"fake clip data")
        clip_files.append(p)
    jobs[job_id] = {
        "id": job_id,
        "status": "completed",
        "result": {
            "clips": [
                {"video_url": f"/videos/{job_id}/_clip_{i}.mp4"} for i in range(3)
            ],
        },
    }

    with TestClient(fastapi_app) as client:
        yield client, job_id, job_dir

    jobs.pop(job_id, None)


def test_merge_rejects_unknown_job(app_client):
    client, _job_id, _ = app_client
    r = client.post("/api/merge", json={
        "job_id": "ghost-job",
        "clip_indices": [0, 1],
    })
    assert r.status_code == 404


def test_merge_rejects_out_of_bounds_clip_index(app_client):
    client, job_id, _ = app_client
    r = client.post("/api/merge", json={
        "job_id": job_id,
        "clip_indices": [0, 99],
    })
    assert r.status_code in (400, 422)


def test_merge_rejects_single_clip(app_client):
    client, job_id, _ = app_client
    r = client.post("/api/merge", json={
        "job_id": job_id,
        "clip_indices": [0],
    })
    assert r.status_code in (400, 422)


def test_merge_rejects_unknown_transition(app_client):
    client, job_id, _ = app_client
    r = client.post("/api/merge", json={
        "job_id": job_id,
        "clip_indices": [0, 1],
        "transition": "starfade",
    })
    assert r.status_code in (400, 422)


def test_merge_dedupes_repeated_clip_indices(app_client):
    client, job_id, job_dir = app_client

    captured = {}

    def fake_concat(inputs, output):
        captured["inputs"] = list(inputs)
        captured["output"] = output
        Path(output).write_bytes(b"merged")
        return output

    with patch("app.main.concat_clips", side_effect=fake_concat):
        r = client.post("/api/merge", json={
            "job_id": job_id,
            "clip_indices": [0, 0, 1, 1, 2],
        })
    assert r.status_code == 200
    # Dedup preserves first occurrence order: [0, 1, 2].
    assert len(captured["inputs"]) == 3
    assert os.path.basename(captured["inputs"][0]) == "_clip_0.mp4"
    assert os.path.basename(captured["inputs"][1]) == "_clip_1.mp4"
    assert os.path.basename(captured["inputs"][2]) == "_clip_2.mp4"


def test_merge_happy_path_returns_new_video_url(app_client):
    client, job_id, job_dir = app_client

    def fake_concat(inputs, output):
        Path(output).write_bytes(b"merged")
        return output

    with patch("app.main.concat_clips", side_effect=fake_concat):
        r = client.post("/api/merge", json={
            "job_id": job_id,
            "clip_indices": [2, 0],
        })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["new_video_url"].startswith(f"/videos/{job_id}/merged_")
    assert body["new_video_url"].endswith(".mp4")
    # Filename encodes the user-picked order, not sorted: "merged_2_0.mp4".
    assert "merged_2_0.mp4" in body["new_video_url"]
