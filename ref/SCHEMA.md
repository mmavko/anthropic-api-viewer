# Anthropic /v1/messages API Schema Reference

## REQUEST

**URL:** `https://api.anthropic.com/v1/messages?beta=true`  
**Method:** `POST`  
**Content-Type:** `application/json`

### Headers

**Standard:**
- `Accept`: `application/json`
- `User-Agent`: `claude-cli/X.X.X (external, cli)`
- `Content-Type`: `application/json`
- `Content-Length`: (integer)
- `Connection`: `keep-alive`
- `Host`: `api.anthropic.com`
- `Accept-Encoding`: `gzip, deflate, br, zstd`

**Anthropic-Specific:**
- `Authorization`: `Bearer sk-ant-...` (API key)
- `anthropic-version`: `2023-06-01` (API version)
- `anthropic-beta`: comma-separated feature flags (e.g., `oauth-2025-04-20,interleaved-thinking-2025-05-14,redact-thinking-2026-02-12`)
- `anthropic-dangerous-direct-browser-access`: `true|false`

**SDK/Client Metadata:**
- `X-Claude-Code-Session-Id`: UUID
- `X-Stainless-Arch`: `arm64|x86_64` (architecture)
- `X-Stainless-Lang`: `js|python` (SDK language)
- `X-Stainless-OS`: `MacOS|Linux|Windows`
- `X-Stainless-Package-Version`: semver (SDK version)
- `X-Stainless-Runtime`: `node|python`
- `X-Stainless-Runtime-Version`: version string
- `X-Stainless-Timeout`: integer (milliseconds)
- `X-Stainless-Retry-Count`: integer
- `x-client-request-id`: UUID
- `x-app`: string (client type, e.g., `cli`)

### Body Fields

```json
{
  "model": "string",                           // Required: model ID (e.g., claude-haiku-4-5-20251001)
  "max_tokens": integer,                       // Required: max output tokens
  "messages": [                                // Required: array of message objects
    {
      "role": "user|assistant",               // Required
      "content": "string|array"                // String or array of content blocks
    }
  ],
  "system": [                                  // Optional: system blocks (with caching control)
    {
      "type": "text",
      "text": "string",
      "cache_control": {                      // Optional: prompt caching config
        "type": "ephemeral",
        "ttl": "1h|5m",
        "scope": "global"
      }
    }
  ],
  "temperature": number,                       // Optional: 0.0-1.0 (default 1)
  "thinking": {                                // Optional: extended thinking config
    "type": "enabled|disabled|budgeted|adaptive",
    "budget_tokens": integer                  // If type=budgeted
  },
  "output_config": {                           // Optional: structured output config
    "format": {
      "type": "json_schema",
      "schema": object                        // JSON Schema
    }
  },
  "stream": boolean,                           // Optional: enable streaming (default false)
  "metadata": {                                // Optional: custom metadata
    "user_id": "string",                       // Internal device/session tracking
    "other_key": "any"
  }
}
```

---

## RESPONSE (Non-Streaming)

**Status:** `200 OK`  
**Content-Type:** `application/json`

### Headers

**Rate Limiting (Anthropic-Specific):**
- `anthropic-ratelimit-unified-status`: `allowed|rate_limited`
- `anthropic-ratelimit-unified-5h-status`: `allowed|rate_limited`
- `anthropic-ratelimit-unified-5h-reset`: Unix timestamp
- `anthropic-ratelimit-unified-5h-utilization`: float (0.0-1.0+)
- `anthropic-ratelimit-unified-7d-status`: `allowed|rate_limited`
- `anthropic-ratelimit-unified-7d-reset`: Unix timestamp
- `anthropic-ratelimit-unified-7d-utilization`: float
- `anthropic-ratelimit-unified-overage-status`: `allowed|rate_limited`
- `anthropic-ratelimit-unified-overage-reset`: Unix timestamp
- `anthropic-ratelimit-unified-overage-utilization`: float
- `anthropic-ratelimit-unified-representative-claim`: string (e.g., `five_hour`)
- `anthropic-ratelimit-unified-reset`: Unix timestamp

**Standard:**
- `Date`: HTTP date
- `Content-Type`: `application/json`
- `Content-Encoding`: `gzip|br`
- `Transfer-Encoding`: `chunked`
- `request-id`: `req_...` (Anthropic request ID)
- `anthropic-organization-id`: UUID
- `traceresponse`: trace ID

### Body Fields

```json
{
  "id": "string",                              // Unique message ID (msg_...)
  "type": "message",                           // Always "message"
  "role": "assistant",                         // Always "assistant"
  "model": "string",                           // Echo of request model
  "content": [                                 // Array of content blocks
    {
      "type": "text",
      "text": "string"                         // Generated text
    }
  ],
  "stop_reason": "end_turn|max_tokens|stop_sequence",
  "stop_sequence": "string|null",
  "stop_details": null,                        // Legacy; always null
  "usage": {                                   // Token counts
    "input_tokens": integer,
    "output_tokens": integer,
    "cache_creation_input_tokens": integer,   // Prompt caching write
    "cache_read_input_tokens": integer,       // Prompt caching read
    "cache_creation": {                        // Ephemeral cache writes
      "ephemeral_5m_input_tokens": integer,
      "ephemeral_1h_input_tokens": integer
    },
    "service_tier": "standard|batch",
    "inference_geo": "not_available|region"
  },
  "context_management": {
    "applied_edits": []                        // Context-management edits applied
  }
}
```

---

## RESPONSE (Streaming: text/event-stream)

**Status:** `200 OK`  
**Content-Type:** `text/event-stream; charset=utf-8`  
**Cache-Control:** `no-cache`

Events are newline-delimited JSON. Each event has a `type` field:

**Event: `message_start`** — Initial message metadata before content
```json
{
  "type": "message_start",
  "message": {
    "id": "string",
    "type": "message",
    "role": "assistant",
    "model": "string",
    "content": [],
    "stop_reason": null,
    "usage": { /* as above */ }
  }
}
```

**Event: `content_block_start`** — Begin a content block
```json
{
  "type": "content_block_start",
  "index": integer,
  "content_block": {
    "type": "text",
    "text": ""
  }
}
```

**Event: `content_block_delta`** — Text delta chunk
```json
{
  "type": "content_block_delta",
  "index": integer,
  "delta": {
    "type": "text_delta",
    "text": "string"                          // Incremental text
  }
}
```

**Event: `content_block_stop`** — End a content block
```json
{
  "type": "content_block_stop",
  "index": integer
}
```

**Event: `message_delta`** — Final stop reason & token counts
```json
{
  "type": "message_delta",
  "delta": {
    "stop_reason": "end_turn|max_tokens",
    "stop_sequence": null,
    "stop_details": null
  },
  "usage": { /* final token counts */ }
}
```

**Event: `message_stop`** — Stream complete
```json
{
  "type": "message_stop"
}
```

**Event: `ping`** — Keep-alive heartbeat (optional)
```json
{
  "type": "ping"
}
```

---

## Query Parameters

- `beta=true` — Enable beta feature flags listed in `anthropic-beta` header

---

## Key Observations

- **API Version:** Captured version is `2023-06-01` (stable for years)
- **Rate Limits:** Unified rate limiter tracks 5h, 7d, and overage windows with utilization %
- **Streaming:** Server-Sent Events format with incremental text deltas
- **Caching:** Prompt caching fully integrated into usage tracking
- **Output Formats:** Structured output via JSON Schema with `output_config.format`
- **Thinking:** Extended thinking modes (`enabled`, `disabled`, `budgeted`) with token budgets
