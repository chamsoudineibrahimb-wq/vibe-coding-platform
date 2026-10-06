#!/usr/bin/env python3
"""Minimal Muapi.ai client (stdlib only), ported from Open-Higgsfield-AI's src/lib/muapi.js.

Commands:
  models  [--type t2i|i2i|t2v|i2v|v2v|lipsync] [--query TEXT]   list catalog models
  info    MODEL_ID                                              show a model's inputs
  upload  FILE                                                  upload a local file, print hosted URL
  run     MODEL_ID [-p key=value ...] [--json FILE] [--out DIR] [--no-wait]
  result  REQUEST_ID [--out DIR] [--no-wait]                    poll / fetch an existing job

The API key is read from MUAPI_API_KEY, then ~/.config/muapi/.env (MUAPI_API_KEY=...).
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE_URL = os.environ.get("MUAPI_BASE_URL", "https://api.muapi.ai")
CATALOG = Path(__file__).resolve().parent.parent / "references" / "models.json"
CONFIG_FILE = Path.home() / ".config" / "muapi" / ".env"
DONE = {"completed", "succeeded", "success"}
FAILED = {"failed", "error"}
VIDEO_TYPES = {"t2v", "i2v", "v2v", "lipsync"}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def get_key():
    key = os.environ.get("MUAPI_API_KEY")
    if not key and CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            if line.strip().startswith("MUAPI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        die(f"no API key: set MUAPI_API_KEY or add MUAPI_API_KEY=... to {CONFIG_FILE} "
            "(get one at https://muapi.ai)", 3)
    return key


def request(method, path, key, body=None, headers=None):
    hdrs = {"x-api-key": key, **(headers or {})}
    data = body
    if isinstance(body, dict):
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:500]}
    except urllib.error.URLError as e:
        die(f"cannot reach {BASE_URL}: {e.reason}", 4)


def load_catalog():
    return json.loads(CATALOG.read_text())


def find_model(model_id):
    for m in load_catalog():
        if m["id"] == model_id:
            return m
    return None


def parse_value(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def output_url(result):
    outputs = result.get("outputs") or []
    return (outputs[0] if outputs else None) or result.get("url") or (result.get("output") or {}).get("url")


def poll(request_id, key, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, data = request("GET", f"/api/v1/predictions/{request_id}/result", key)
        if status >= 500:
            time.sleep(3)
            continue
        if status >= 400:
            die(f"poll failed ({status}): {data.get('error')}")
        state = str(data.get("status", "")).lower()
        if state in DONE:
            return data
        if state in FAILED:
            die(f"generation failed: {data.get('error') or 'unknown error'}")
        print(f"[muapi] {request_id}: {state or 'pending'}...", file=sys.stderr)
        time.sleep(3)
    die(f"timed out after {timeout}s; resume with: muapi.py result {request_id}", 5)


def download(urls, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for url in urls:
        name = url.split("?")[0].rsplit("/", 1)[-1] or f"{uuid.uuid4().hex}.bin"
        dest = out / name
        urllib.request.urlretrieve(url, dest)
        paths.append(str(dest))
    return paths


def finish(result, args, request_id=None):
    urls = [u for u in (result.get("outputs") or []) if isinstance(u, str)] or [output_url(result)]
    urls = [u for u in urls if u]
    report = {"request_id": request_id or result.get("request_id") or result.get("id"), "status": result.get("status"), "urls": urls}
    if urls and args.out:
        report["files"] = download(urls, args.out)
    print(json.dumps(report, indent=2))


def cmd_models(args):
    q = (args.query or "").lower()
    for m in load_catalog():
        if args.type and m["type"] != args.type:
            continue
        if q and q not in m["id"].lower() and q not in m["name"].lower():
            continue
        print(f"{m['type']:8} {m['id']:45} {m['name']}")


def cmd_info(args):
    m = find_model(args.model)
    if not m:
        die(f"unknown model {args.model!r}; list them with: muapi.py models --query ...")
    print(json.dumps(m, indent=2, ensure_ascii=False))


def cmd_upload(args):
    key = get_key()
    path = Path(args.file)
    if not path.is_file():
        die(f"no such file: {path}")
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    status, data = request("POST", "/api/v1/upload_file", key, body,
                           {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if status >= 400:
        die(f"upload failed ({status}): {data.get('error')}")
    url = data.get("url") or data.get("file_url") or (data.get("data") or {}).get("url")
    if not url:
        die(f"no URL in upload response: {data}")
    print(url)


def cmd_run(args):
    key = get_key()
    model = find_model(args.model)
    endpoint = model["endpoint"] if model else args.model
    payload = json.loads(Path(args.json).read_text()) if args.json else {}
    for item in args.param or []:
        if "=" not in item:
            die(f"bad --param {item!r}, expected key=value")
        k, v = item.split("=", 1)
        payload[k] = parse_value(v)
    status, data = request("POST", f"/api/v1/{endpoint}", key, payload)
    if status >= 400:
        die(f"request failed ({status}): {data.get('error')}")
    request_id = data.get("request_id") or data.get("id")
    if not request_id:
        return finish(data, args)
    print(f"[muapi] submitted {args.model} -> request_id {request_id}", file=sys.stderr)
    if args.no_wait:
        print(json.dumps({"request_id": request_id, "status": "submitted"}))
        return
    timeout = args.timeout or (1800 if model and model["type"] in VIDEO_TYPES else 300)
    finish(poll(request_id, key, timeout), args, request_id)


def cmd_result(args):
    key = get_key()
    if args.no_wait:
        status, data = request("GET", f"/api/v1/predictions/{args.request_id}/result", key)
        print(json.dumps(data, indent=2))
        return
    finish(poll(args.request_id, key, args.timeout or 1800), args, args.request_id)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("models"); s.add_argument("--type", choices=["t2i", "i2i", "t2v", "i2v", "v2v", "lipsync"]); s.add_argument("--query"); s.set_defaults(fn=cmd_models)
    s = sub.add_parser("info"); s.add_argument("model"); s.set_defaults(fn=cmd_info)
    s = sub.add_parser("upload"); s.add_argument("file"); s.set_defaults(fn=cmd_upload)
    for name, fn in (("run", cmd_run), ("result", cmd_result)):
        s = sub.add_parser(name)
        s.add_argument("model" if name == "run" else "request_id")
        if name == "run":
            s.add_argument("-p", "--param", action="append", help="payload field key=value (JSON values allowed)")
            s.add_argument("--json", help="JSON file with the full payload")
        s.add_argument("--out", help="download outputs into this directory")
        s.add_argument("--no-wait", action="store_true", help="return immediately with the request id")
        s.add_argument("--timeout", type=int, help="polling timeout in seconds")
        s.set_defaults(fn=fn)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
