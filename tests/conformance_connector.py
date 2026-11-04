"""The four answers the conformance suite needs from OpenAI.

Two shapes behind one connector: images answer inline, video is a job whose
bytes live behind the content path.
"""

from __future__ import annotations

from engine_conformance import Behaviours, Call, Connector, Provider


class OpenAIConnector(Connector):
    package = "engine_openai"

    entries = {
        "text_to_image": "IMG-Models/gpt-image-2-5-sunburst.toml",
        "image_to_video": "VID-Models/sora-2.toml",
    }

    provider_modules = ()
    supports_polling = False

    def install(self, monkeypatch, behaviours: Behaviours) -> Provider:
        provider = Provider()
        state = {"submit": list(behaviours.submit_errors), "polls": 0}

        class FakeClient:
            def request_json(self, method, path, payload=None, *, headers=None, params=None):
                provider.calls.append(Call(kind="poll" if method == "GET" else "submit",
                                           payload=payload, path=path))
                if method == "POST":
                    if behaviours.submit_error is not None:
                        raise behaviours.submit_error
                    if state["submit"]:
                        raise state["submit"].pop(0)
                    return {"data": [{"url": url} for url in behaviours.result_urls]}

                if behaviours.poll_error is not None:
                    raise behaviours.poll_error
                vocabulary = {"running": "in_progress", "succeeded": "completed"}
                statuses = behaviours.poll_statuses
                index = min(state["polls"], len(statuses) - 1)
                state["polls"] += 1
                status = vocabulary.get(statuses[index], statuses[index])
                return {"id": "job-1", "status": status}

            def request_form(self, method, path, fields, *, files=None):
                provider.calls.append(Call(kind="submit", payload=dict(fields), path=path))
                if behaviours.submit_error is not None:
                    raise behaviours.submit_error
                if state["submit"]:
                    raise state["submit"].pop(0)
                return {"id": "job-1", "status": "queued"}

            def request_bytes(self, method, path):
                provider.calls.append(Call(kind="download", path=path))
                if behaviours.download_error is not None:
                    raise behaviours.download_error
                return behaviours.result_bytes

            def download(self, url):
                provider.downloads.append(url)
                provider.calls.append(Call(kind="download", url=url))
                if behaviours.download_error is not None:
                    raise behaviours.download_error
                return behaviours.result_bytes

        fake = FakeClient()
        monkeypatch.setattr(self.engine_class(), "_client", lambda _self: fake)
        return provider
