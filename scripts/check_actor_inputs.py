#!/usr/bin/env python3
"""Check that every key we send an Apify actor exists in that actor's schema.

Apify does not reject unknown input keys. It ignores them. So a renamed or
misspelled field fails silently: the run still succeeds, the setting we asked
for is not applied, and the actor's own default decides the result. That is how
`sort` survived in x-skills where the actor's field is `queryType` - every
"Top" search quietly ran as "Latest".

This reads the client with `ast` rather than calling it, so it needs no token
and costs nothing.

    python3 scripts/check_actor_inputs.py

Exit codes: 0 clean, 1 a mismatch, 2 the schemas could not be fetched (offline,
or Apify is down) - so a network blip never reads as a passing build.
"""
from __future__ import annotations

import ast
import json
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLIENT = ROOT / "lib" / "apify_client.py"

USER_AGENT = "skills-actor-check/1"
SCHEMA_URL = "https://api.apify.com/v2/acts/{actor}/builds/default"
RUNNERS = ("_run", "_run_sync", "run_actor", "_call")


def fetch_schema(actor: str) -> dict:
    request = urllib.request.Request(
        SCHEMA_URL.format(actor=actor.replace("/", "~")),
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        build = json.load(response).get("data", {})
    schema = build.get("inputSchema")
    if isinstance(schema, str):
        schema = json.loads(schema)
    if not schema:
        raise RuntimeError(f"{actor}: build has no input schema")
    return schema


def string_constants(tree: ast.AST) -> dict[str, str]:
    """Module and class level NAME = "..." assignments, for resolving actor ids."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and node.targets
            and isinstance(node.targets[0], ast.Name)
        ):
            found[node.targets[0].id] = node.value.value
    return found


def looks_like_actor(value: str) -> bool:
    """`owner~name` or `owner/name`, and not a URL that happens to contain a slash."""
    if value.startswith(("http://", "https://")) or " " in value or "{" in value:
        return False
    return value.count("~") == 1 or value.count("/") == 1


def payload_sites(tree: ast.AST, consts: dict[str, str], sole_actor: str | None):
    """(method, actor, keys) for every actor call with a literal payload."""
    sites = []
    for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for call in [n for n in ast.walk(function) if isinstance(n, ast.Call)]:
            if getattr(call.func, "attr", "") not in RUNNERS:
                continue
            actor = sole_actor
            for argument in call.args:
                if isinstance(argument, ast.Name) and argument.id in consts:
                    actor = consts[argument.id]
                elif isinstance(argument, ast.Attribute) and argument.attr in consts:
                    actor = consts[argument.attr]
                elif isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    actor = argument.value
            payload = next((a for a in call.args if isinstance(a, ast.Dict)), None)
            if not actor or payload is None:
                continue
            keys = [k.value for k in payload.keys if isinstance(k, ast.Constant)]
            if any(k is None for k in payload.keys):
                keys.append("**<computed>")          # a **spread we cannot read
            sites.append((function.name, actor, keys))
    return sites


def main() -> int:
    if not CLIENT.exists():
        print(f"no Apify client at {CLIENT.relative_to(ROOT)}, nothing to check")
        return 0

    tree = ast.parse(CLIENT.read_text())
    consts = string_constants(tree)
    actors = sorted({v for v in consts.values() if looks_like_actor(v)})
    sole = actors[0] if len(actors) == 1 else None

    sites = payload_sites(tree, consts, sole)
    if not sites:
        print("no actor calls with a literal payload found: has the client changed shape?")
        return 1

    schemas: dict[str, dict] = {}
    for _, actor, _ in sites:
        if actor in schemas:
            continue
        try:
            schemas[actor] = fetch_schema(actor)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print(f"could not fetch the schema for {actor}: {exc}")
            return 2

    problems = []
    for method, actor, keys in sites:
        schema = schemas[actor]
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for key in keys:
            if key.startswith("**<"):
                continue
            if key not in properties:
                problems.append(
                    f"{method}: sends {key!r}, which {actor} has no input for. "
                    f"Apify ignores it silently. Nearest inputs: "
                    f"{sorted(p for p in properties if key.lower()[:4] in p.lower())[:4] or sorted(properties)[:6]}"
                )
        missing = [k for k in required if k not in keys]
        if missing:
            defaults = {k: properties.get(k, {}).get("default") for k in missing}
            problems.append(
                f"{method}: omits required {missing}; the actor falls back to {defaults}, "
                f"which is its choice rather than ours"
            )

    if problems:
        print("Apify actor input mismatches:\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"OK: {len(sites)} actor calls across {len(schemas)} actors, "
        "every key is in the actor's schema and every required key is set."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
