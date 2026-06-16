#!/usr/bin/env python3
"""
Extract response body from a Proxyman-exported HAR file as JSON.
For streaming (text/event-stream) responses, assembles SSE events
into the equivalent non-streaming message object.
"""

import base64
import json
import sys


def _decode_content(content):
    """Return response body text, decoding base64 if needed."""
    text = content.get("text", "")
    if content.get("encoding") == "base64":
        text = base64.b64decode(text).decode("utf-8")
    return text


def _assemble_stream(sse_text):
    """
    Assemble SSE events into a single message object matching the
    non-streaming response schema.
    """
    events = []
    for line in sse_text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data = line[len("data:"):].strip()
            if data and data != "[DONE]":
                events.append(json.loads(data))

    message = None
    content_blocks = {}  # index -> accumulated text

    for event in events:
        t = event.get("type")

        if t == "message_start":
            message = dict(event["message"])
            message["content"] = []

        elif t == "content_block_start":
            idx = event["index"]
            content_blocks[idx] = dict(event["content_block"])

        elif t == "content_block_delta":
            idx = event["index"]
            delta = event["delta"]
            if delta.get("type") == "text_delta":
                content_blocks.setdefault(idx, {"type": "text", "text": ""})
                content_blocks[idx]["text"] += delta["text"]
            elif delta.get("type") == "thinking_delta":
                content_blocks.setdefault(idx, {"type": "thinking", "thinking": ""})
                content_blocks[idx]["thinking"] += delta["thinking"]
            elif delta.get("type") == "input_json_delta":
                content_blocks.setdefault(idx, {"type": "tool_use", "input": ""})
                content_blocks[idx]["input"] = content_blocks[idx].get("input", "") + delta.get("partial_json", "")

        elif t == "content_block_stop":
            pass  # block is done; it's already accumulated

        elif t == "message_delta":
            if message is not None:
                message.update(event.get("delta", {}))
                # Merge final usage (overrides message_start usage)
                if "usage" in event:
                    message.setdefault("usage", {}).update(event["usage"])
                # context_management lives on the event, not in delta
                if "context_management" in event:
                    message["context_management"] = event["context_management"]

    if message is not None:
        # Attach assembled content blocks in index order
        message["content"] = [content_blocks[i] for i in sorted(content_blocks)]

    return message


def get_response_body(har_path):
    with open(har_path) as f:
        har = json.load(f)

    entries = har["log"]["entries"]
    results = []

    for entry in entries:
        url = entry["request"]["url"]
        if "/v1/messages" not in url:
            continue

        response = entry["response"]
        content = response.get("content", {})
        mime = content.get("mimeType", "")
        text = _decode_content(content)

        if not text:
            results.append({"url": url, "streaming": False, "body": None})
            continue

        if "text/event-stream" in mime:
            body = _assemble_stream(text)
            results.append({"url": url, "streaming": True, "body": body})
        else:
            body = json.loads(text)
            results.append({"url": url, "streaming": False, "body": body})

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.har>", file=sys.stderr)
        sys.exit(1)

    results = get_response_body(sys.argv[1])
    if not results:
        print("No /v1/messages entries found.", file=sys.stderr)
        sys.exit(1)

    for i, r in enumerate(results):
        if len(results) > 1:
            mode = "streaming" if r["streaming"] else "non-streaming"
            print(f"# Entry {i + 1} ({mode}): {r['url']}")
        print(json.dumps(r["body"], indent=2))
