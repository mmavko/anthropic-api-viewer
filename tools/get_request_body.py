#!/usr/bin/env python3
"""Extract request body from a Proxyman-exported HAR file as JSON."""

import json
import sys


def get_request_body(har_path):
    with open(har_path) as f:
        har = json.load(f)

    entries = har["log"]["entries"]
    results = []

    for entry in entries:
        url = entry["request"]["url"]
        if "/v1/messages" not in url:
            continue

        post_data = entry["request"].get("postData", {})
        text = post_data.get("text", "")
        if not text:
            continue

        body = json.loads(text)
        results.append({"url": url, "body": body})

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.har>", file=sys.stderr)
        sys.exit(1)

    results = get_request_body(sys.argv[1])
    if not results:
        print("No /v1/messages entries found.", file=sys.stderr)
        sys.exit(1)

    for i, r in enumerate(results):
        if len(results) > 1:
            print(f"# Entry {i + 1}: {r['url']}")
        print(json.dumps(r["body"], indent=2))
