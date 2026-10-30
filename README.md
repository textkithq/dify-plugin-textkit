# TextKit for Dify

Send texts, list messages and verify phone numbers from Dify workflows, chatflows and agents with [TextKit](https://jointextkit.com), an SMS API.

## Tools

| Tool | What it does | API call |
| --- | --- | --- |
| `send_message` | Sends an SMS. | `POST /v1/messages` |
| `list_messages` | Lists sent and received texts, newest first. | `GET /v1/messages` |
| `send_verification` | Texts a one-time code to a phone number. | `POST /v1/verify` |
| `check_verification` | Checks the code a user entered. | `POST /v1/verify/check` |

## Setup

1. Create an API key in the [TextKit console](https://jointextkit.com/console). A test key (`ssms_sk_test_...`) simulates sends. A live key texts real numbers.
2. Install **TextKit** from the Dify Marketplace.
3. Open **Tools > TextKit**, choose **Authorize**, and paste the API key. Dify checks it with `GET /v1/messages?limit=1`.

## Usage

Add a TextKit tool to a workflow, or give it to an agent.

To verify a phone number, use `send_verification`, ask the user for the code, then use `check_verification`. Check the `verified` field in its output. A wrong code returns `verified: false` rather than an error.

If a request fails, the tool stops with TextKit's error message, for example when the API key is invalid or the recipient opted out.

## Connection requirements

The plugin needs outbound HTTPS access to `api.jointextkit.com`. It connects to no other host.

## Privacy

See [PRIVACY.md](PRIVACY.md).

## Source and support

- Source repository: https://github.com/textkithq/dify-plugin-textkit
- API docs: https://jointextkit.com/docs/quickstart
- Contact: support@jointextkit.com
