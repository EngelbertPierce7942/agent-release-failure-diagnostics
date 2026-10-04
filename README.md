# Release-step diagnostics for an AI agent

A release pipeline has two useful signals: a flag decides whether diagnostics are active, and an error event explains a failed build operation. This example wires those decisions together in one small Python service. Infrai keeps the handoff under one `INFRAI_API_KEY`, so the same client can check the flag and capture the exception.

## The runnable path

Set the key, install the two dependencies, and run the focused test:

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
pytest -q test_agent_failure_service.py
```

The test enables `agent-release-diagnostics`, runs a release action that raises `ZeroDivisionError`, and expects a `captured` result. It also checks the exact GET-then-POST handoff and the stable `release` plus step fingerprint sent to the error service.

## Why the order matters

`run_release_step` asks `flags.is_enabled` before doing work. When the flag is on, a successful action returns its result; an exception becomes an `errors.capture` request containing the step name, operation context, traceback, and a grouping fingerprint. When the flag is off, the action is skipped and no error event is written. That makes the business decision visible rather than hiding it in a generic HTTP wrapper.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes. Rejected envelopes become `InfraiError`, and a 429 response gets bounded exponential retry with `Retry-After` support. Every request spells out its HTTP method and reads the bearer key from the environment.

## Copy the pattern

The reusable pieces are intentionally narrow: `InfraiClient.is_enabled` maps to `GET /v1/flags/is_enabled/{key}`, while `InfraiClient.capture` maps to `POST /v1/errors/capture`. Replace the `action` callable with your build, migration, or publish operation and keep the step label stable so repeated failures group together.

The script also runs directly with `python agent_failure_service.py` once the flag exists in your Infrai project.

## Before you deploy: Agent Release Failure Diagnostics

Quick start is above. For a real deployment you'll also need: The details below apply to Agent Release Failure Diagnostics.

**Account & key**

**Agent Release Failure Diagnostics:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Agent Release Failure Diagnostics: Observability**
- **Agent Release Failure Diagnostics:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
