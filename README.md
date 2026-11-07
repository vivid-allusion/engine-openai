# engine-openai

Engine wrapper for **OpenAI** — images and video behind one interface.

**16 catalogued models, taken from OpenAI's own OpenAPI document (captured
2026-11-04, extended 2026-11-07):** 14 image ids — including
`gpt-image-2.6-sunburst` and `gpt-image-2.6-flare` — and 2 video ids
(`sora-2`, `sora-2-pro`). Each model's state is evidence-based; see
`status.json`.

## Two shapes, one interface

- **Images answer inline.** `POST /images/generations` returns `data[]` with
  either base64 bytes or a URL. No job, no polling. An input that carries
  reference URLs goes to `POST /images/edits` instead, as JSON with an
  `images` array of `{image_url}` objects; the answer has the same shape.
- **Video is a job.** `POST /videos` (a form, not JSON) returns an id;
  `GET /videos/{id}` reports state; `GET /videos/{id}/content` is the file.

The engine hides the difference: `run()` returns the same `OutputFile` list
either way, and an empty answer is an error, never an empty success.

## Setup

```
export OPENAI_API_KEY=sk-...
```

## Tests

```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

This engine's own tests, plus the shared conformance suite.

## Not carried yet

`images/variations` and local file uploads (including video `input_reference`)
still need a file-upload path in the engine; until then they are honestly
absent rather than half-supported. Reference URLs in a markdown file are
carried: they are sent to `images/edits` as `{image_url}` objects.
