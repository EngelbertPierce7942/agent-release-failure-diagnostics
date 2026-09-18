import os

from agent_failure_service import run_release_step
from infrai_client import InfraiClient


class Response:
    status_code = 200
    headers = {}

    def __init__(self, data):
        self.data = data

    def json(self):
        return {"ok": True, "data": self.data, "error": None, "metadata": {}}


def test_failed_release_is_captured_after_flag_check():
    os.environ["INFRAI_API_KEY"] = "test-key"
    requests_seen = []

    def transport(method, url, **kwargs):
        requests_seen.append((method, url, kwargs))
        if "is_enabled" in url:
            return Response({"enabled": True})
        return Response({"event_id": "evt-1"})

    client = InfraiClient(transport)
    result = run_release_step(client, "publish-build", lambda: 1 / 0)
    assert result == {"status": "captured", "step": "publish-build"}
    assert [item[0] for item in requests_seen] == ["GET", "POST"]
    assert requests_seen[1][2]["json"]["fingerprint"] == ["release", "publish-build"]

