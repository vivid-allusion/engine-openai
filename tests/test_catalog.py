"""The catalogue is small enough to read: the image models, two video models."""

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


def test_the_two_point_six_image_models_are_carried():
    catalog = load_catalog()
    for model in ("gpt-image-2.6-sunburst", "gpt-image-2.6-flare"):
        spec = catalog.get(model)
        assert spec.known
        assert spec.category == "IMG"
        assert spec.mode == "sync"


def test_every_catalogued_model_has_a_standby_preset():
    catalog = load_catalog()
    standby = Path(__file__).resolve().parent.parent / "engine_openai" / "profiles" / "standby"
    for spec in catalog.specs():
        preset = standby / spec.category / f"{spec.id.replace('.', '-')}.yaml"
        assert preset.is_file(), f"{spec.id} has no standby preset"
