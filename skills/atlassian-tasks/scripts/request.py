#!/usr/bin/env -S uv run
# /// script
# dependencies = [
# ]
# requires-python = ">=3.12"
# ///
from argparse import ArgumentParser
from json import load
from sys import stdout
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

p = ArgumentParser()
g = p.add_mutually_exclusive_group(required=True)
p.add_argument("--body-file", help="Path to a JSON body file")
p.add_argument("--method", required=True)
g.add_argument("--pat-file", help="Path to a file containing a PAT")
g.add_argument("--state-file", help="Path to a Playwright-style state JSON with cookies")
p.add_argument("--url", required=True)
p.add_argument(
    "--query", action="append", default=[],
    help="Query param as KEY=VALUE (repeatable; value is URL-encoded)"
)
args = p.parse_args()

body = None
headers = {"Accept": "application/json"}
if args.body_file:
    body = open(args.body_file, "rb").read()
    headers["Content-Type"] = "application/json"

if args.pat_file:
    headers["Authorization"] = f"Bearer {open(args.pat_file).read().strip()}"
else:
    state = load(open(args.state_file))
    headers["Cookie"] = "; ".join(f"{cookie["name"]}={cookie["value"]}" for cookie in state.get("cookies", []))

if args.query:
    parts = urlsplit(args.url)
    merged = parse_qsl(parts.query) + [tuple(q.split("=", 1)) for q in args.query]
    args.url = urlunsplit(parts._replace(query=urlencode(merged)))

req = Request(args.url, data=body, headers=headers, method=args.method.upper())
with urlopen(req) as response:
    stdout.write(response.read().decode())
