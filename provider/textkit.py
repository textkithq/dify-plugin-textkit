from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from provider.client import TextKitError, textkit_request


class TextKitProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            textkit_request(credentials, "GET", "/messages", params={"limit": 1})
        except TextKitError as e:
            raise ToolProviderCredentialValidationError(str(e)) from None
