import traceback
from typing import Callable, Any

from infrai_client import InfraiClient


def setup_release_diagnostics(client: InfraiClient) -> None:
    """Validate that the documented diagnostics flag is available."""
    if not client.is_enabled("agent-release-diagnostics"):
        raise RuntimeError(
            "agent-release-diagnostics is not enabled; enable it in the Infrai project first"
        )


def run_release_step(client: InfraiClient, step: str, action: Callable[[], Any]) -> dict:
    """Run a release step only when diagnostics are enabled; capture failures."""
    if not client.is_enabled("agent-release-diagnostics"):
        return {"status": "skipped", "step": step}
    try:
        result = action()
        return {"status": "completed", "step": step, "result": result}
    except Exception as exc:
        client.capture(
            title=f"release step {step} failed",
            message=str(exc),
            level="error",
            fingerprint=["release", step],
            exception=traceback.format_exc(),
            context={"step": step, "operation": "release"},
        )
        return {"status": "captured", "step": step}


if __name__ == "__main__":
    client = InfraiClient()
    setup_release_diagnostics(client)
    print(run_release_step(client, "publish-build", lambda: {"artifact": "agent-demo"}))
