"""OpenAI behaviour: images answer inline, video is a job with a content fetch."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine_openai import Engine, EngineError, InputFile  # noqa: E402
from engine_openai.transport import ProviderError  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"pixels"
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"pixels"
IMG = "gpt-image-2.5-sunburst"
VID = "sora-2"


class FakeClient:
    def __init__(self, script=None, payload=PNG):
        self.script = list(script or [])
        self.payload = payload
        self.calls = []
        self.downloads = []
        self.forms = []

    def request_json(self, method, path, payload=None, *, headers=None, params=None):
        self.calls.append({"method": method, "path": path, "payload": payload})
        if not self.script:
            raise AssertionError(f"unexpected request {method} {path}")
        response = self.script.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def request_form(self, method, path, fields, *, files=None):
        self.forms.append({"path": path, "fields": fields})
        return {"id": "job-1", "status": "queued"}

    def request_bytes(self, method, path):
        self.calls.append({"method": method, "path": path})
        return self.payload

    def download(self, url):
        self.downloads.append(url)
        return self.payload


def make_engine(tmp_path, monkeypatch, client, endpoint=IMG, **profile):
    monkeypatch.setattr(Engine, "_client", lambda self: client)
    base = {
        "platform": "openai",
        "endpoint": endpoint,
        "media_type": "image",
        "parameters": {},
        "poll_interval": 0,
        "timeout_seconds": 0,
        "retry_on_429": 0,
    }
    base.update(profile)
    return Engine(base, tmp_path, api_key="sk-test")


def an_input(tmp_path, prompt="a paper lantern"):
    path = tmp_path / "shot.md"
    path.write_text(prompt + "\n")
    return InputFile(path=path, prompt=prompt)


def test_an_image_comes_back_inline_and_is_saved(tmp_path, monkeypatch):
    client = FakeClient([{"data": [{"url": "https://cdn.invalid/out.png"}]}])
    engine = make_engine(tmp_path, monkeypatch, client)
    results = engine.run([an_input(tmp_path)])
    assert [r.status for r in results] == ["ok"]
    assert results[0].path.read_bytes() == PNG
    assert client.calls[0]["path"] == "images/generations"
    assert client.downloads == ["https://cdn.invalid/out.png"]
    assert results[0].metadata["api_payload"]["prompt"] == "a paper lantern"


def test_base64_images_are_decoded_without_a_download(tmp_path, monkeypatch):
    import base64

    encoded = base64.b64encode(PNG).decode()
    client = FakeClient([{"data": [{"b64_json": encoded}]}])
    results = make_engine(tmp_path, monkeypatch, client).run([an_input(tmp_path)])
    assert results[0].status == "ok"
    assert results[0].path.read_bytes() == PNG
    assert client.downloads == []


def test_an_empty_prompt_fails_before_spending(tmp_path, monkeypatch):
    client = FakeClient([])
    results = make_engine(tmp_path, monkeypatch, client).run([an_input(tmp_path, prompt="")])
    assert results[0].status == "error"
    assert client.calls == []


def test_an_empty_answer_is_an_error(tmp_path, monkeypatch):
    client = FakeClient([{"data": []}])
    results = make_engine(tmp_path, monkeypatch, client).run([an_input(tmp_path)])
    assert results[0].status == "error"
    assert "No output" in results[0].error_msg


def test_video_submits_a_form_polls_and_fetches_the_content(tmp_path, monkeypatch):
    client = FakeClient(
        [{"id": "job-1", "status": "queued"},
         {"id": "job-1", "status": "in_progress"},
         {"id": "job-1", "status": "completed"}],
        payload=MP4,
    )
    results = make_engine(tmp_path, monkeypatch, client, endpoint=VID, media_type="video").run(
        [an_input(tmp_path, prompt="a slow dolly shot")]
    )
    assert [r.status for r in results] == ["ok"]
    assert results[0].path.suffix == ".mp4"
    assert client.forms[0]["path"] == "videos"
    assert client.forms[0]["fields"]["model"] == VID
    assert any(call["path"] == "videos/job-1/content" for call in client.calls)


def test_a_fatal_error_stops_the_batch(tmp_path, monkeypatch):
    client = FakeClient([ProviderError(401, "unauthorized")])
    results = make_engine(tmp_path, monkeypatch, client).run([an_input(tmp_path), an_input(tmp_path)])
    assert len(results) == 1
    assert len(client.calls) == 1


def test_a_missing_key_is_a_preflight_error(tmp_path):
    engine = Engine({"endpoint": IMG}, tmp_path)
    try:
        engine.run([an_input(tmp_path)])
    except EngineError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected EngineError")
