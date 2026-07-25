#!/usr/bin/env python3
"""Verify every SDK method the skill uses actually exists in the installed package.

Catches the failure mode markdown linting cannot: a well-formed file that asserts a
method exists when it doesn't, claims a real one is absent, or references a real status
as "invented". Checks BOTH SDKs (Node .d.ts and Python) and understands every
@trycourier/courier layout shipped to date:

  - v7+ "Stainless"  resources/<name>.d.ts (+ nested resources/<parent>/<sub>.d.ts)
  - v6   "Fern"      api/resources/<ns>/client/Client.d.ts
  - older            resources/<ns>.d.ts (flat)

Usage:
    python3 scripts/verify-sdk-claims.py [path/to/@trycourier/courier ...]

With no path it auto-discovers a local install. Scans every markdown file under skills/.
Exits non-zero if any used method/namespace is missing, or a real one is called absent.
Run it in CI.
"""
import re, os, sys, glob, subprocess

def discover_sdks():
    """Find installed @trycourier/courier package roots via bounded, fixed-depth globs."""
    tail = os.path.join("node_modules", "@trycourier", "courier")
    roots, home = [], os.path.expanduser("~")
    for base in (os.getcwd(), home):
        roots += [base, os.path.join(base, "*"), os.path.join(base, "*", "*")]
    found = [p for r in roots for p in glob.glob(os.path.join(r, tail)) if os.path.isdir(p)]
    return sorted(set(found), key=len)[:2]

PATHS = [p for p in sys.argv[1:] if os.path.isdir(p)] or discover_sdks()
if not PATHS:
    print("No SDK found. Install it (npm i @trycourier/courier) or pass the path to "
          "node_modules/@trycourier/courier.", file=sys.stderr)
    print("SKIP: nothing to check against.", file=sys.stderr)
    sys.exit(3)  # distinct code: skipped, not failed

def camel(s): return re.sub(r'[-_](.)', lambda m: m.group(1).upper(), s) if s else s

truth = {}
def add(ns, methods):
    truth.setdefault(camel(ns), set()).update(camel(m) for m in methods)

NOISE = {'constructor', 'if', 'for', 'return', 'while', 'switch', 'catch'}
FERN_RE = re.compile(r'^\s{2,8}(?:public\s+|protected\s+|async\s+)*([a-zA-Z][a-zA-Z0-9]*)\s*\(', re.M)
V7_RE   = re.compile(r'^\s{4}([a-zA-Z][a-zA-Z0-9]*)\(', re.M)  # Stainless: name(args): APIPromise<...>

for SDK in PATHS:
    v7 = os.path.isdir(os.path.join(SDK, 'resources')) and not os.path.isdir(os.path.join(SDK, 'api'))
    client_dts = glob.glob(SDK + '/**/client/Client.d.ts', recursive=True)  # v6 Fern
    if v7:
        for f in glob.glob(SDK + '/resources/**/*.d.ts', recursive=True):
            base = os.path.basename(f)
            if base.startswith('index.'): continue
            add(base[:-5], set(V7_RE.findall(open(f).read())) - NOISE)   # strip .d.ts
    elif client_dts:
        for f in client_dts:
            parts = os.path.relpath(f, SDK).split(os.sep)
            ns = parts[-3] if len(parts) >= 3 else parts[0]
            if ns in ('resources', 'api', 'client'): continue
            add(ns, set(FERN_RE.findall(open(f).read())) - NOISE)
    else:
        for f in glob.glob(SDK + '/**/*.d.ts', recursive=True):
            parts = os.path.relpath(f, SDK).replace('.d.ts', '').split(os.sep)
            ns = parts[-2] if len(parts) > 1 and parts[-1] in ('index', parts[-2]) else parts[-1]
            if ns in ('index', 'shared'): continue
            add(ns, set(FERN_RE.findall(open(f).read())) - NOISE)
    for f in glob.glob(SDK + '/**/*.py', recursive=True):                # Python (either layout)
        parts = os.path.relpath(f, SDK).replace('.py', '').split(os.sep)
        ns = parts[-2] if len(parts) > 1 and parts[-1] in ('__init__', parts[-2], 'client') else parts[-1]
        if ns.startswith('_'): continue
        add(ns, {m for m in re.findall(r'^\s{4}def ([a-z][a-z0-9_]*)\s*\(', open(f).read(), re.M)
                 if not m.startswith('_')})

ENUMS = set()
for SDK in PATHS:
    for f in glob.glob(SDK + '/**/*.d.ts', recursive=True):
        ENUMS |= set(re.findall(r"""['"]([A-Z][A-Z0-9_]{2,})['"]""", open(f).read()))
METHODS = {m for ms in truth.values() for m in ms}
NAMESPACES = set(truth)

def md_files():
    return sorted(glob.glob('skills/**/*.md', recursive=True))

bad = []
# 1. used calls that don't exist
for f in md_files():
    for ln, line in enumerate(open(f).read().split('\n'), 1):
        low = line.lower()
        if 'anthropic' in low or 'openai' in low or 'client.beta.messages' in low:
            continue
        for m in re.finditer(r'client\.([a-zA-Z_]+)\.([a-zA-Z_]+)(?:\.([a-zA-Z_]+))?\s*\(', line):
            if any(seg and len(seg) == 1 and seg.isupper() for seg in m.groups()):
                continue  # placeholder like client.X.Y()
            ns, a, b = camel(m.group(1)), camel(m.group(2)), camel(m.group(3))
            if ns not in truth:
                bad.append((f, ln, m.group(0), 'namespace not in SDK')); continue
            if a in truth[ns]: continue
            if a in truth and (b or '') in truth.get(a, set()): continue
            bad.append((f, ln, m.group(0), f'method not in {ns}'))

# 2. prose that calls a REAL method/status invented or absent
NEG = re.compile(r"(does\s*n['’o]?t exist|does not exist|no such|not a (?:real|valid)|"
                 r"is ?n['’]?t (?:a )?real|is not (?:a )?real|\binvented\b|\bhallucinated\b|"
                 r"made[- ]up|does\s*n['’]?t have)", re.I)
IDENT = re.compile(r"`([A-Za-z_][\w.]*)`|'([A-Z][A-Z0-9_]{2,})'")
for f in md_files():
    for ln, line in enumerate(open(f).read().split('\n'), 1):
        if not NEG.search(line): continue
        for m in IDENT.finditer(line):
            tok = m.group(1) or m.group(2); seg = tok.split('.')[-1]
            hit = ('a real enum value' if (tok in ENUMS or seg in ENUMS)
                   else 'a real method' if camel(seg) in METHODS
                   else 'a real namespace' if (camel(seg) in NAMESPACES or camel(tok) in NAMESPACES)
                   else None)
            if hit:
                bad.append((f, ln, tok, f'claimed absent/invented but the SDK has it as {hit}'))

# version-currency nudge (best effort; never fails the run)
def sdk_version(root):
    m = re.search(r'"version"\s*:\s*"([^"]+)"', open(os.path.join(root, "package.json")).read()) \
        if os.path.isfile(os.path.join(root, "package.json")) else None
    return m.group(1) if m else None
def npm_latest():
    try:
        return subprocess.run(["npm", "view", "@trycourier/courier", "version"],
                              capture_output=True, text=True, timeout=8).stdout.strip() or None
    except Exception:
        return None
def as_tuple(v): return tuple(int(x) for x in re.findall(r'\d+', v or "")[:3])

cur, latest = sdk_version(PATHS[0]), npm_latest()
print(f"Checked against @trycourier/courier {cur or '(unknown version)'}"
      + (f" — latest is {latest}, consider upgrading" if cur and latest and as_tuple(cur) < as_tuple(latest)
         else " (latest)" if cur and cur == latest else ""))

for f, ln, call, why in bad:
    print(f"  ✗ {f}:{ln}: {call} — {why}")
print(f"{len(truth)} namespaces checked · {len(bad)} problem{'' if len(bad)==1 else 's'}")
sys.exit(1 if bad else 0)
