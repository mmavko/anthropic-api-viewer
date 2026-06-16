# Tools Reference

Helper scripts for inspecting and validating Proxyman-exported HAR files containing Anthropic `/v1/messages` traffic.

All scripts are in `tools/` and can be run from any working directory.

---

## get_request_body.py

Extracts the request body from a HAR file and prints it as formatted JSON.

```
python3 tools/get_request_body.py <file.har>
```

Filters entries to `/v1/messages` only. If the file contains multiple matching entries, each is printed with a header line.

---

## get_response_body.py

Extracts the response body from a HAR file and prints it as formatted JSON.

```
python3 tools/get_response_body.py <file.har>
```

Handles both response types:

- **Non-streaming** (`application/json`) — decodes base64 if needed, parses and prints.
- **Streaming** (`text/event-stream`) — assembles SSE events into the equivalent non-streaming message object: merges `message_start` metadata, accumulates `content_block_delta` text, and applies `message_delta` for stop reason and final token counts.

The assembled streaming object matches the non-streaming schema (see `docs/SCHEMA.md` for the two minor differences).

---

## validate.py

Validates HAR files against the schema documented in `docs/SCHEMA.md`.

```
# Validate all .har files in data/
python3 tools/validate.py

# Validate specific files
python3 tools/validate.py path/to/file.har ...
```

Checks:

- **Request body** — presence of required fields (`model`, `max_tokens`, `messages`), correct types, valid enum values for `role`, `thinking.type`, etc.
- **Response body** — presence of required fields (`id`, `type`, `role`, `model`, `content`, `stop_reason`, `usage`), valid content block structure, valid `stop_reason` value, integer token counts.

Exits 0 if all entries pass, 1 if any fail. Errors are printed per-entry with `request:` / `response:` prefixes.
