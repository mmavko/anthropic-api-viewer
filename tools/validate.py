#!/usr/bin/env python3
"""
Validate Proxyman-exported HAR files against the Anthropic /v1/messages schema
documented in SCHEMA.md.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from get_request_body import get_request_body
from get_response_body import get_response_body


# ── validators ────────────────────────────────────────────────────────────────

def _err(errors, msg):
    errors.append(msg)


def validate_request_body(body, errors):
    # Required top-level fields
    for field in ("model", "max_tokens", "messages"):
        if field not in body:
            _err(errors, f"request.body: missing required field '{field}'")

    # model
    if "model" in body and not isinstance(body["model"], str):
        _err(errors, "request.body.model: must be a string")

    # max_tokens
    if "max_tokens" in body and not isinstance(body["max_tokens"], int):
        _err(errors, "request.body.max_tokens: must be an integer")

    # messages
    messages = body.get("messages")
    if isinstance(messages, list):
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                _err(errors, f"request.body.messages[{i}]: must be an object")
                continue
            if "role" not in msg:
                _err(errors, f"request.body.messages[{i}]: missing 'role'")
            elif msg["role"] not in ("user", "assistant"):
                _err(errors, f"request.body.messages[{i}].role: expected 'user'|'assistant', got {msg['role']!r}")
            if "content" not in msg:
                _err(errors, f"request.body.messages[{i}]: missing 'content'")
    elif messages is not None:
        _err(errors, "request.body.messages: must be an array")

    # system (optional)
    system = body.get("system")
    if system is not None:
        if not isinstance(system, list):
            _err(errors, "request.body.system: must be an array")
        else:
            for i, blk in enumerate(system):
                if blk.get("type") != "text":
                    _err(errors, f"request.body.system[{i}].type: expected 'text', got {blk.get('type')!r}")

    # thinking (optional)
    thinking = body.get("thinking")
    if thinking is not None:
        if thinking.get("type") not in ("enabled", "disabled", "budgeted", "adaptive"):
            _err(errors, f"request.body.thinking.type: unexpected value {thinking.get('type')!r}")

    # stream (optional)
    if "stream" in body and not isinstance(body["stream"], bool):
        _err(errors, "request.body.stream: must be a boolean")


def validate_response_body(body, errors):
    if body is None:
        _err(errors, "response.body: empty")
        return

    # Required top-level fields
    for field in ("id", "type", "role", "model", "content", "stop_reason", "usage"):
        if field not in body:
            _err(errors, f"response.body: missing required field '{field}'")

    if body.get("type") != "message":
        _err(errors, f"response.body.type: expected 'message', got {body.get('type')!r}")

    if body.get("role") != "assistant":
        _err(errors, f"response.body.role: expected 'assistant', got {body.get('role')!r}")

    # content blocks
    content = body.get("content")
    if isinstance(content, list):
        for i, blk in enumerate(content):
            if not isinstance(blk, dict):
                _err(errors, f"response.body.content[{i}]: must be an object")
                continue
            if "type" not in blk:
                _err(errors, f"response.body.content[{i}]: missing 'type'")
            elif blk["type"] == "text" and "text" not in blk:
                _err(errors, f"response.body.content[{i}]: text block missing 'text'")
            elif blk["type"] == "thinking" and "thinking" not in blk:
                _err(errors, f"response.body.content[{i}]: thinking block missing 'thinking'")
    elif content is not None:
        _err(errors, "response.body.content: must be an array")

    # stop_reason
    valid_stop = {"end_turn", "max_tokens", "stop_sequence", None}
    if body.get("stop_reason") not in valid_stop:
        _err(errors, f"response.body.stop_reason: unexpected value {body.get('stop_reason')!r}")

    # usage
    usage = body.get("usage")
    if isinstance(usage, dict):
        for field in ("input_tokens", "output_tokens"):
            if field not in usage:
                _err(errors, f"response.body.usage: missing '{field}'")
            elif not isinstance(usage[field], int):
                _err(errors, f"response.body.usage.{field}: must be an integer")
    elif usage is not None:
        _err(errors, "response.body.usage: must be an object")


# ── main ──────────────────────────────────────────────────────────────────────

def validate_file(har_path):
    path = str(har_path)
    req_entries = get_request_body(path)
    res_entries = get_response_body(path)

    if not req_entries and not res_entries:
        return [("warn", "No /v1/messages entries found")]

    results = []
    count = max(len(req_entries), len(res_entries))

    for i in range(count):
        label = f"entry {i + 1}" if count > 1 else "entry"
        req_errors, res_errors = [], []

        if i < len(req_entries):
            validate_request_body(req_entries[i]["body"], req_errors)
        if i < len(res_entries):
            validate_response_body(res_entries[i]["body"], res_errors)

        errors = [f"  request:  {e}" for e in req_errors] + \
                 [f"  response: {e}" for e in res_errors]
        results.append((label, errors))

    return results


def main(paths):
    all_ok = True

    for path in paths:
        p = Path(path)
        print(f"\n{'─' * 60}")
        print(f"  {p.name}")
        print(f"{'─' * 60}")

        try:
            results = validate_file(p)
        except Exception as exc:
            print(f"  ERROR reading file: {exc}")
            all_ok = False
            continue

        for label, errors in results:
            if errors:
                print(f"  FAIL ({label})")
                for e in errors:
                    print(e)
                all_ok = False
            else:
                print(f"  OK   ({label})")

    print()
    return 0 if all_ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: validate all .har files in data/ (sibling of tools/)
        here = Path(__file__).parent
        paths = sorted((here.parent / "data").glob("*.har"))
        if not paths:
            print("No .har files found.", file=sys.stderr)
            sys.exit(1)
    else:
        paths = [Path(a) for a in sys.argv[1:]]

    sys.exit(main(paths))
