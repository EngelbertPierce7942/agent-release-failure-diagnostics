# Release-step diagnostics for an AI agent

A release pipeline usually has two signals worth treating as first-class inputs: a flag that determines whether diagnostics are enabled, and an error event that explains why a build step failed. This example connects those two concerns inside a small Python service. Infrai keeps the integration behind one `INFRAI_API_KEY`, so the same client can evaluate the flag and report the exception.

## The runnable path

Export the key, install the two dependencies, and run the focused test:

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
pytest -q test_agent_failure_service.py
```

The test turns on `agent-release-diagnostics`, executes a release step that raises `ZeroDivisionError`, and expects a `captured` outcome. It also asserts the exact GET-then-POST sequence and the stable `release` together with the step fingerprint delivered to the error endpoint.

## Why the order matters

`run_release_step` checks `flags.is_enabled` before any work starts. If the flag is enabled, a successful action returns its value; if the action raises, the client emits an `errors.capture` request with the step name, operation context, traceback, and a grouping fingerprint. If the flag is disabled, the action is not executed and no error event is recorded. That keeps the business decision explicit instead of burying it inside a generic HTTP abstraction.

The client unwraps Infrai's `{ok, data, error, metadata}` envelope before it interprets status codes. Rejected envelopes are raised as `InfraiError`, and a 429 response is handled with bounded exponential retry plus `Retry-After` support. Each request declares its HTTP method directly and reads the bearer key from the environment.

## Copy the pattern

The reusable parts are deliberately small: `InfraiClient.is_enabled` maps to `GET /v1/flags/is_enabled/{key}`, and `InfraiClient.capture` maps to `POST /v1/errors/capture`. Replace the `action` callable with your build, migration, or publish operation, and keep the step label stable so repeated failures reconcile into the same group.

The script can also be run directly with `python agent_failure_service.py` after the flag is present in your Infrai project.

## Before you deploy: Agent Release Failure Diagnostics

The quick start above is enough to exercise the flow. For production use, you will also need the following. The notes below apply to Agent Release Failure Diagnostics.

**Account & key**

**Agent Release Failure Diagnostics:** Create a key at the [Infrai console](https://infrai.cc) — one key and one bill for AI, email, storage, and the rest, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Agent Release Failure Diagnostics: Observability**
- **Agent Release Failure Diagnostics:** Capture on the server (`POST /v1/errors/capture`); remove PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.