from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from provider.client import textkit_request

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


class ListMessagesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        limit = int(tool_parameters.get("limit") or DEFAULT_LIMIT)
        params: dict[str, Any] = {"limit": max(1, min(limit, MAX_LIMIT))}
        for name in ("number", "direction", "status"):
            value = str(tool_parameters.get(name) or "").strip()
            if value:
                params[name] = value
        page = textkit_request(self.runtime.credentials, "GET", "/messages", params=params)
        yield self.create_json_message(page)
        yield self.create_text_message(f"Found {len(page.get('data') or [])} messages.")
