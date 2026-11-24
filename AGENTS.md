# AGENTS.md — engine-openai

Notes for anyone changing engine-openai, the engine wrapper for OpenAI. Its
consumer is helmer-transceiver; the engine contract is
`docs/architecture/ENGINE_CONTRACT.md` there. The key is `OPENAI_API_KEY`.

## Two shapes

- **Images answer inline.** `POST /images/generations` returns `data[]` with
  base64 bytes or a URL. An input with reference URLs goes to
  `POST /images/edits` instead, as JSON with an `images` array of
  `{image_url}` objects. No job, no polling.
- **Video is a job.** `POST /videos` creates it, `GET /videos/{id}` is polled
  until a terminal state, then `GET /videos/{id}/content` is downloaded.

`run()` returns the same `OutputFile` list either way.

## Rules

1. **The catalogue is data.** Models live under `engine_openai/endpoints`;
   standby presets under `engine_openai/profiles/standby`. Adding a model is a
   data file, not a branch in `engine.py`.
2. **`engine.py` holds no wire knowledge.** URLs, envelopes and terminal
   states live in `engine_openai/transport.py` and `engine_openai/tasks.py`.
3. **Never invent a model, a parameter or a price.** Every entry comes from
   OpenAI's own document or page.
4. **Fail loud.** An empty answer, an undeclared parameter sent, or a job that
   never finishes is an error with a message, never an empty success.
5. **Four categories:** `IMG`, `VID`, `LLM`, `AUD`. A model is carried by what
   it produces.

## Tests

```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

This includes the shared conformance suite. Keep it green.
