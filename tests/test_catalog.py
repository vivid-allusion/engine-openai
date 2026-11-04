"""The catalogue is small enough to read: five image models, two video models."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine_openai.catalog import load_catalog  # noqa: E402


def test_both_families_are_present():
    catalog = load_catalog()
    assert [s.id for s in catalog.specs() if s.category == "IMG"]
    assert [s.id for s in catalog.specs() if s.category == "VID"]


def test_images_are_synchronous_and_video_is_not():
    catalog = load_catalog()
    for spec in catalog.specs():
        if spec.category == "IMG":
            assert spec.mode == "sync", f"{spec.id} should be a one-call image model"
            assert spec.api_path == "images/generations"
        else:
            assert spec.mode == "async"
            assert spec.content_path.startswith("videos/")


def test_status_is_evidence_based():
    catalog = load_catalog()
    states = {catalog.status(spec.model) for spec in catalog.specs()}
    assert states <= {"experimental", "beta", "proven"}
    assert catalog.status("gpt-image-2.5-sunburst") == "beta"
    assert states == {"experimental", "beta"}
