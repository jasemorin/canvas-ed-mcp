#!/usr/bin/env python3
"""Config tests: CANVAS_BASE_URL env override and the unit-outline domain allowlist.

Run directly: python3 test_config.py
Imports happen in a subprocess because the env var must be set before import.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SNIPPET = """
import json, sys
import canvas_ed_mcp as m
from pydantic import ValidationError

def allowed(url):
    try:
        m.FetchUnitOutlineInput(unit_outline_url=url)
        return True
    except ValidationError:
        return False

print(json.dumps({"base": m.CANVAS_BASE_URL,
                  "checks": {u: allowed(u) for u in sys.argv[1:]}}))
"""


def run(urls, env_url=None):
    env = {k: v for k, v in os.environ.items() if k != "CANVAS_BASE_URL"}
    if env_url:
        env["CANVAS_BASE_URL"] = env_url
    out = subprocess.run([sys.executable, "-c", SNIPPET, *urls],
                         capture_output=True, text=True, env=env, cwd=HERE)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def expect(env_url, expected_base, cases):
    got = run(list(cases), env_url)
    assert got["base"] == expected_base, got["base"]
    for url, want in cases.items():
        assert got["checks"][url] is want, f"{url}: expected {want} (env={env_url})"


# Default (no env var): Sydney, same behavior as before for legitimate URLs
expect(None, "https://canvas.sydney.edu.au/api/v1", {
    "https://www.sydney.edu.au/units/COMP3221/2026-S1C-ND-CC": True,
    "https://sydney.edu.au/units/COMP3221": True,
    "https://evil.com/x": False,
    "https://notsydney.edu.au/x": False,  # lookalike suffix must not pass
    "https://www.unimelb.edu.au/units/X": False,
})

# Custom instance: base URL and the allowlist both follow; only that Canvas
# host and its subdomains are allowed — not siblings, not other tenants
expect("https://canvas.unimelb.edu.au/api/v1", "https://canvas.unimelb.edu.au/api/v1", {
    "https://canvas.unimelb.edu.au/some/page": True,
    "https://sub.canvas.unimelb.edu.au/x": True,
    "https://www.unimelb.edu.au/units/X": False,
    "https://evilcanvas.unimelb.edu.au/x": False,
    "https://www.sydney.edu.au/units/X": False,
})

# Apex-domain instance must not widen the allowlist to the public suffix (edu.au)
expect("https://sydney.edu.au/api/v1", "https://sydney.edu.au/api/v1", {
    "https://www.sydney.edu.au/units/X": True,
    "https://other.edu.au/x": False,
})

# Malformed env var (no scheme -> no hostname): fail loudly at import
env = {k: v for k, v in os.environ.items() if k != "CANVAS_BASE_URL"}
env["CANVAS_BASE_URL"] = "canvas.sydney.edu.au/api/v1"
out = subprocess.run([sys.executable, "-c", SNIPPET], capture_output=True,
                     text=True, env=env, cwd=HERE)
assert out.returncode != 0 and "CANVAS_BASE_URL" in out.stderr, out.stderr

print("all config tests passed")
