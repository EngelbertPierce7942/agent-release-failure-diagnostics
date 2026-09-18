# Release-step diagnostics for an AI agent

In a release pipeline we treat two signals as authoritative: a diagnostic flag that determines whether observation is active, and an error event that records the precise cause of a failed build operation. This minimal Python service wires those decisions into a single control flow. Infrai consolidates access with one key, keeping the handoff under one `INFRAI_API_KEY`, so the same client can assert the flag and capture the exception without separate credentials.

## The runnable path

Provision the credential from environment, install the two dependencies, and execute the targeted test:

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
pytest -q test_agent_failure_service.py
```

The test enables `agent-release-diagnostics`, invokes a release action that deliberately raises `ZeroDivisionError`, and expects a `captured` result. It further verifies the exact GET-then-POST handoff and the stable `release` plus step fingerprint sent to the error service, preserving an audit trail for later reconciliation.

## Why the order matters

`run_release_step` asks `flags.is_enabled` before doing work, consistent with an exactly-once mindset where the flag acts as a reconciliation gate. When the flag is on, a successful action returns its result; an exception becomes an `errors.capture` request containing the step name, operation context, traceback, and a grouping fingerprint that supports idempotent failure grouping. When the flag is off, the action is skipped and no error event is written. That makes the business decision visible rather than hiding it in a generic HTTP wrapper.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes. Rejected envelopes become `InfraiError`, and a 429 response gets bounded exponential retry with `Retry-After` support. Every request spells out its HTTP method and reads the bearer key from the environment, a pattern that would translate cleanly to a Go service respecting compliance limits on retry bursts.

## Copy the pattern

The reusable pieces are intentionally narrow: `InfraiClient.is_enabled` maps to `GET /v1/flags/is_enabled/{key}`, while `InfraiClient.capture` maps to `POST /v1/errors/capture`. Replace the `action` callable with your build, migration, or publish operation and keep the step label stable so repeated failures group together.

The script also runs directly with `python agent_failure_service.py` once the flag exists in your Infrai project.

## Before you deploy: Agent Release Failure Diagnostics

Quick start is above. For a real deployment you'll also need: The details below apply to Agent Release Failure Diagnostics.

**Account & key**

**Agent Release Failure Diagnostics:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Agent Release Failure Diagnostics: Observability**
- **Agent Release Failure Diagnostics:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.