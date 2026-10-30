from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.client import textkit_request


class CheckVerificationTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        payload = {
            "phone": str(tool_parameters["phone"]).strip(),
            "code": str(tool_parameters["code"]).strip(),
        }
        result = textkit_request(
            self.runtime.credentials, "POST", "/verify/check", json_body=payload
        )
        yield self.create_json_message(result)
        yield self.create_text_message("Verified." if result.get("verified") else "Not verified.")
