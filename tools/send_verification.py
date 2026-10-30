from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.client import textkit_request


class SendVerificationTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        payload = {"channel": "sms", "phone": str(tool_parameters["phone"]).strip()}
        app_name = str(tool_parameters.get("app_name") or "").strip()
        if app_name:
            payload["app_name"] = app_name
        verification = textkit_request(
            self.runtime.credentials, "POST", "/verify", json_body=payload
        )
        yield self.create_json_message(verification)
        yield self.create_text_message(
            f"Verification {verification.get('id')} is {verification.get('status')}."
        )
