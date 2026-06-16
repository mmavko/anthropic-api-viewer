# Anthropic API Viewer

A single-file HTML tool for inspecting raw Anthropic `/v1/messages` API interactions captured via a proxy (e.g. Proxyman).

## Workflow

1. In Proxyman, select a request to `api.anthropic.com` and export it as HAR (**File → Export → HAR**)
2. Open `viewer.html` in any browser (no server needed — works from the filesystem)
3. Paste the HAR content into the **Source** tab
4. Validation runs automatically; any JSON or schema errors are shown inline
5. Switch to the **Rendered** tab to see the interaction in a human-readable layout

## Views

**Source** — raw textarea for pasting HAR content. Validates on every edit; shows errors if the JSON is malformed or required HAR fields are missing.

**Rendered** — structured view of the captured exchange:
- Request: method, URL, headers, and parsed request body (model, messages, parameters)
- Response: status, headers, and parsed response body (content blocks, usage stats, stop reason)

## Input format

HAR 1.2 as exported by Proxyman. The viewer expects at least one entry targeting `api.anthropic.com/v1/messages`. Response bodies encoded as base64 are decoded automatically.
