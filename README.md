# Anthropic API Viewer

A single-file HTML tool for inspecting raw Anthropic `/v1/messages` API interactions captured via a proxy (e.g. Proxyman).

**Live:** https://mmavko.github.io/anthropic-api-viewer/

## Workflow

1. In Proxyman, select a request to `api.anthropic.com` and export it as HAR (**File → Export → HAR**)
2. Open the viewer (locally or at the URL above)
3. Drag and drop the `.har` file onto the textarea, or paste its contents
4. Validation runs automatically; any JSON or schema errors are shown inline
5. Switch to the **Rendered** tab to see the interaction in a human-readable layout

## Views

**Source** — raw textarea for pasting or dropping HAR content. Validates on every edit; shows errors if the JSON is malformed or required HAR fields are missing.

**Rendered** — structured view of the captured exchange:
- Request: method, URL, headers, and parsed request body (model, messages, parameters)
- Response: status, headers, and parsed response body (content blocks, usage stats, stop reason)

Message and system block content is rendered as Markdown. Custom XML-like tags (e.g. `<tool_description>`) are highlighted for readability.

## Input format

HAR 1.2 as exported by Proxyman. The viewer expects at least one entry targeting `api.anthropic.com/v1/messages`. Response bodies encoded as base64 are decoded automatically. Streaming (`text/event-stream`) responses are assembled into a single message object.

## Project layout

```
docs/        # viewer source + GitHub Pages root (docs/index.html = the app)
ref/         # reference docs: SCHEMA.md, tools.md
tools/       # Python helper scripts for inspecting and validating HAR files
data/        # .har files (gitignored)
```

GitHub Pages is configured to serve from the `docs/` folder on the `main` branch. Editing `docs/index.html` is all that's needed to update the live app — no build step.

## Helper scripts

See `ref/tools.md` for usage.
