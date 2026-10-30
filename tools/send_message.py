from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.client import textkit_request


class SendMessageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        payload = {"to": str(tool_parameters["to"]).strip(), "body": tool_parameters["body"]}
        sender = str(tool_parameters.get("from") or "").strip()
        if sender:
            payload["from"] = sender
        message = textkit_request(self.runtime.credentials, "POST", "/messages", json_body=payload)
        yield self.create_json_message(message)
        yield self.create_text_message(f"Message {message.get('id')} is {message.get('status')}.")
