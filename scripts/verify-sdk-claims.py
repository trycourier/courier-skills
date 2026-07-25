#!/usr/bin/env python3
"""Verify every SDK method the skill uses actually exists in the installed package.

Checks BOTH SDKs: Node (.d.ts) and Python (resources/*.py). Pass either path, or both.

Catches the failure mode that markdown linting cannot: a well-formed file that
asserts a method exists when it doesn't, or claims one is absent when it isn't.

Usage:
    python3 scripts/verify-sdk-claims.py [path/to/node_modules/@trycourier/courier/resources]

Exits non-zero if any used method is missing from the SDK. Run in CI.
"""
import re, os, sys, glob

PATHS = sys.argv[1:] or ["node_modules/@trycourier/courier/resources"]
PATHS = [p for p in PATHS if os.path.isdir(p)]
if not PATHS:
    print("No SDK found. Pass the path to @trycourier/courier/resources and/or courier/resources.", file=sys.stderr)
    sys.exit(2)

def camel(s): return re.sub(r'[-_](.)', lambda m: m.group(1).upper(), s) if s else s

truth = {}
def add(ns, methods):
    truth.setdefault(camel(ns), set()).update(camel(m) for m in methods)

for SDK in PATHS:
    for f in glob.glob(SDK + '/**/*.d.ts', recursive=True):          # Node
        parts = os.path.relpath(f, SDK).replace('.d.ts', '').split(os.sep)
        ns = parts[-2] if len(parts) > 1 and parts[-1] in ('index', parts[-2]) else parts[-1]
        if ns in ('index', 'shared'): continue
        add(ns, set(re.findall(r'^\s{2,6}([a-zA-Z][a-zA-Z0-9]*)\s*\(', open(f).read(), re.M))
                 - {'constructor', 'if', 'for', 'return'})
    for f in glob.glob(SDK + '/**/*.py', recursive=True):             # Python
        parts = os.path.relpath(f, SDK).replace('.py', '').split(os.sep)
        ns = parts[-2] if len(parts) > 1 and parts[-1] in ('__init__', parts[-2]) else parts[-1]
        if ns.startswith('_'): continue
        add(ns, {m for m in re.findall(r'^\s{4}def ([a-z][a-z0-9_]*)\s*\(', open(f).read(), re.M)
                 if not m.startswith('_')})

bad = []
for f in sorted(glob.glob('skills/**/*.md', recursive=True)):
    for ln, line in enumerate(open(f).read().split('\n'), 1):
        low = line.lower()
        # Skip only non-Courier SDK examples. Do NOT skip markdown table rows —
        # reference tables are exactly where wrong signatures hide.
        if 'anthropic' in low or 'openai' in low or 'client.beta.messages' in low:
            continue
        for m in re.finditer(r'client\.([a-zA-Z_]+)\.([a-zA-Z_]+)(?:\.([a-zA-Z_]+))?\s*\(', line):
            ns, a, b = camel(m.group(1)), camel(m.group(2)), camel(m.group(3))
            if ns not in truth:
                bad.append((f, ln, m.group(0), 'namespace not in SDK')); continue
            if a in truth[ns]: continue
            if a in truth and (b or '') in truth.get(a, set()): continue
            bad.append((f, ln, m.group(0), f'method not in {ns}'))

# argument-shape check, scoped by namespace (a method name alone is ambiguous:
# messages.cancel takes a positional id, journeys.cancel takes an object)
OBJECT_FIRST = set()
for SDK in PATHS:
    for f in glob.glob(SDK + '/**/*.d.ts', recursive=True):
        parts = os.path.relpath(f, SDK).replace('.d.ts', '').split(os.sep)
        ns = parts[-2] if len(parts) > 1 and parts[-1] in ('index', parts[-2]) else parts[-1]
        if ns in ('index', 'shared'): continue
        for m in re.finditer(r'^\s{2,6}([a-zA-Z][a-zA-Z0-9]*)\((body|params):\s', open(f).read(), re.M):
            OBJECT_FIRST.add((camel(ns), m.group(1)))

for f in sorted(glob.glob('skills/**/*.md', recursive=True)):
    for ln, line in enumerate(open(f).read().split('\n'), 1):
        if 'anthropic' in line.lower(): continue
        for m in re.finditer(r'client\.([a-zA-Z_]+)(?:\.([a-zA-Z_]+))?\.([a-zA-Z_]+)\(([A-Za-z_][\w]*)\)', line):
            ns  = camel(m.group(2) or m.group(1))
            met = camel(m.group(3))
            if (ns, met) in OBJECT_FIRST:
                bad.append((f, ln, m.group(0), f'{ns}.{met}() takes an object, not a positional argument'))

for f, ln, call, why in bad:
    print(f"{f}:{ln}: {call} — {why}")
print(f"\n{len(truth)} namespaces checked across {len(PATHS)} SDK path(s) · {len(bad)} invalid call{'' if len(bad)==1 else 's'}")
sys.exit(1 if bad else 0)
