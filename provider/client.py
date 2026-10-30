"""One authenticated call to the TextKit REST API."""

from typing import Any

import httpx

API_BASE_URL = "https://api.jointextkit.com/v1"
TIMEOUT_SECONDS = 30


class TextKitError(Exception):
    """A TextKit request that could not be completed."""


def _error_message(response: httpx.Response) -> str:
    """Keep the API's own message: errors carry {"error": {"code": ..., "message": ...}}."""
    detail = None
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        detail = payload["error"].get("message") or payload["error"].get("code")
    return f"TextKit API error {response.status_code}: {detail or 'request failed'}"


def textkit_request(
    credentials: dict[str, Any],
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = credentials.get("api_key")
    if not api_key:
        raise TextKitError("TextKit API key is required.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "dify-plugin-textkit",
    }
    try:
        response = httpx.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            json=json_body,
            params=params,
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as e:
        raise TextKitError(f"Could not reach TextKit: {e}") from e

    if response.is_error:
        raise TextKitError(_error_message(response))
    try:
        payload = response.json()
    except ValueError as e:
        raise TextKitError("TextKit returned an unexpected response (expected JSON).") from e
    if not isinstance(payload, dict):
        raise TextKitError("TextKit returned an unexpected response (expected a JSON object).")
    return payload
