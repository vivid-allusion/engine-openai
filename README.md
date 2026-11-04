# engine-openai

Engine wrapper for **OpenAI** — images and video behind one interface.

**7 endpoints, taken from OpenAI's own OpenAPI document (captured 2026-11-04):**
5 image models (`gpt-image-2.5-sunburst`, `gpt-image-2.5-flare`, `gpt-image-2`,
`gpt-image-1.5`, `gpt-image-1-mini`) and 2 video models (`sora-2`, `sora-2-pro`).
Every endpoint is `experimental` until a real call proves it.

## Two shapes, one interface

- **Images answer inline.** `POST /images/generations` returns `data[]` with
  either base64 bytes or a URL. No job, no polling.
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

`images/edits` and `images/variations` take an uploaded file rather than a URL,
and video `input_reference` does too. They need a file-upload path in the
engine; until then they are honestly absent rather than half-supported.
