"""Calls each tool through httpx.MockTransport, so no network is used."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

sys.path.insert(0, str(Path(__file__).parents[1]))

from provider.textkit import TextKitProvider
from tools.check_verification import CheckVerificationTool
from tools.list_messages import ListMessagesTool
from tools.send_message import SendMessageTool
from tools.send_verification import SendVerificationTool

KEY = "ssms_sk_test_abc"  # pragma: allowlist secret
real_request = httpx.request


class Api:
    def __init__(self, status=200, payload=None, error=None):
        self.status, self.payload, self.error, self.seen = status, payload or {}, error, None

    def __enter__(self):
        def handler(request):
            self.seen = request
            if self.error:
                raise self.error
            return httpx.Response(self.status, json=self.payload)

        def fake(method, url, **kwargs):
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                return client.request(method, url, **kwargs)

        self.patcher = patch("provider.client.httpx.request", fake)
        self.patcher.start()
        return self

    def __exit__(self, *args):
        self.patcher.stop()

    @property
    def body(self):
        return json.loads(self.seen.content)


def run(tool_class, params, key=KEY):
    tool = tool_class.__new__(tool_class)
    tool.runtime = SimpleNamespace(credentials={"api_key": key})
    tool.create_json_message = lambda data: ("json", data)
    tool.create_text_message = lambda text: ("text", text)
    return list(tool._invoke(params))


def test_send_uses_body_field_and_bearer_key():
    with Api(201, {"id": "msg_1", "status": "queued"}) as api:
        out = run(SendMessageTool, {"to": " +15551234567 ", "body": "Hello"})
    assert str(api.seen.url) == "https://api.jointextkit.com/v1/messages"
    assert api.seen.headers["Authorization"] == f"Bearer {KEY}"
    assert api.body == {"to": "+15551234567", "body": "Hello"}
    assert out == [
        ("json", {"id": "msg_1", "status": "queued"}),
        ("text", "Message msg_1 is queued."),
    ]


def test_send_includes_from():
    with Api(201, {"id": "msg_1"}) as api:
        run(SendMessageTool, {"to": "+15551234567", "body": "Hi", "from": "+15550001111"})
    assert api.body["from"] == "+15550001111"


def test_api_error_keeps_the_message():
    error = {"error": {"code": "recipient_opted_out", "message": "This number opted out."}}
    with Api(403, error), pytest.raises(Exception, match="403: This number opted out"):
        run(SendMessageTool, {"to": "+15551234567", "body": "Hi"})


def test_missing_key_never_calls_the_api():
    with Api() as api, pytest.raises(Exception, match="API key is required"):
        run(SendMessageTool, {"to": "+15551234567", "body": "Hi"}, key="")
    assert api.seen is None


def test_network_failure():
    with Api(error=httpx.ConnectError("boom")), pytest.raises(Exception, match="Could not reach"):
        run(SendMessageTool, {"to": "+15551234567", "body": "Hi"})


def test_list_sends_only_set_filters():
    with Api(200, {"data": [{"id": "msg_1"}]}) as api:
        out = run(
            ListMessagesTool, {"number": "+15551234567", "direction": "inbound", "status": ""}
        )
    assert dict(api.seen.url.params) == {
        "limit": "25",
        "number": "+15551234567",
        "direction": "inbound",
    }
    assert out[1] == ("text", "Found 1 messages.")


@pytest.mark.parametrize(("limit", "sent"), [(500, "100"), (-3, "1"), (None, "25")])
def test_list_clamps_limit(limit, sent):
    with Api(200, {"data": []}) as api:
        run(ListMessagesTool, {"limit": limit})
    assert api.seen.url.params["limit"] == sent


def test_send_verification():
    with Api(201, {"id": "ver_1", "status": "pending"}) as api:
        run(SendVerificationTool, {"phone": "+15551234567", "app_name": "Acme"})
    assert str(api.seen.url) == "https://api.jointextkit.com/v1/verify"
    assert api.body == {"channel": "sms", "phone": "+15551234567", "app_name": "Acme"}


@pytest.mark.parametrize(("verified", "text"), [(True, "Verified."), (False, "Not verified.")])
def test_check_verification(verified, text):
    with Api(200, {"verified": verified}) as api:
        out = run(CheckVerificationTool, {"phone": "+15551234567", "code": " 123456 "})
    assert str(api.seen.url) == "https://api.jointextkit.com/v1/verify/check"
    assert api.body == {"phone": "+15551234567", "code": "123456"}
    assert out[1] == ("text", text)


def test_credential_check_rejects_a_bad_key():
    provider = TextKitProvider.__new__(TextKitProvider)
    error = {"error": {"code": "invalid_api_key", "message": "Invalid API key."}}
    with Api(401, error) as api, pytest.raises(ToolProviderCredentialValidationError):
        provider._validate_credentials({"api_key": "bad"})
    assert dict(api.seen.url.params) == {"limit": "1"}
