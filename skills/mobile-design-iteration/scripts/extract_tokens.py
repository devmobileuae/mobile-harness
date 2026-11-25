#!/usr/bin/env python3
# WHAT: Parse Swift design tokens (a token package with UPalette/UColor/UFont/USpacing/UShadow) into tokens.json. Nothing hand-typed.
# RUN: python3 extract_tokens.py --repo <app repo> [--derived-glob '<Scheme>-*'] [--tokens-dir <dir>] [--out tokens.json]
#      (adapt the parsers if your token files are named differently)
"""Read the Ultimate token sources and emit tokens.json — the one input the Figma
builder and the parity check both read.

Nothing here is hand-typed: every colour, size and type spec is parsed out of the
Swift that ships in the app, so the Figma file cannot quietly disagree with the
build. Run:

    python3 extract_tokens.py --repo <app repo>

Sources (SPM checkout, see TOKENS_DIR below):
    UPalette.swift  raw palette          -> tokens["palette"]
    UColor.swift    semantic roles       -> tokens["roles"]   (light/dark, aliased)
    UFont.swift     UTextStyle table     -> tokens["text"]
    USpacing.swift  spacing/radius/size  -> tokens["space"], ["radius"], ["size"]
    UShadow.swift   elevation            -> tokens["shadow"]  (hand-mirrored, see note)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import argparse

_ap = argparse.ArgumentParser(description="Parse Swift design tokens into tokens.json")
_ap.add_argument("--repo", default=".", help="app repo root (default: current dir)")
_ap.add_argument("--tokens-dir", help="folder with UPalette.swift etc. (skips the search)")
_ap.add_argument("--package-path", default="Ultimate/Sources/Ultimate/Tokens",
                 help="path of the token folder inside an SPM checkout")
_ap.add_argument("--derived-glob", default="*", help="DerivedData folder glob, e.g. 'MyApp-*'")
_ap.add_argument("--out", help="output file (default: tokens.json next to this script)")
ARGS = _ap.parse_args()

ROOT = Path(ARGS.repo).expanduser().resolve()
OUT = Path(ARGS.out).expanduser().resolve() if ARGS.out else Path(__file__).resolve().parent / "tokens.json"

# The package is vendored per build directory; take whichever checkout exists.
CANDIDATES = [
    ROOT / ".build-sim2/SourcePackages/checkouts" / ARGS.package_path,
    ROOT / ".build-sim/SourcePackages/checkouts" / ARGS.package_path,
    Path.home() / "Library/Developer/Xcode/DerivedData",
]


def tokens_dir() -> Path:
    if ARGS.tokens_dir:
        return Path(ARGS.tokens_dir).expanduser().resolve()
    for c in CANDIDATES[:2]:
        if (c / "UPalette.swift").exists():
            return c
    hits = sorted(CANDIDATES[2].glob(f"{ARGS.derived_glob}/SourcePackages/checkouts/{ARGS.package_path}"))
    if hits:
        return hits[0]
    raise SystemExit("token sources not found — build the app once so SPM checks the package out, or pass --tokens-dir.")


def flatten(text: str) -> str:
    """Collapse a Swift file to one declaration per line (calls wrap across lines)."""
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.replace("public static let", "\nstatic let").replace("static let", "\nstatic let")


# --------------------------------------------------------------------------- palette

def parse_palette(src: str) -> dict:
    out = {}
    for m in re.finditer(r"static let (\w+): UInt32 = (0x[0-9A-Fa-f]{6})", src):
        out[m.group(1)] = m.group(2).lower()
    return out


# ----------------------------------------------------------------------------- roles

HEX = r"0x[0-9A-Fa-f]{6}"


def parse_side(expr: str) -> dict:
    """One side of a themed(...) pair, or a constant Color(rgb:) argument."""
    expr = expr.strip().rstrip(",)")
    if "UIColor.clear" in expr or expr == ".clear":
        return {"hex": "0x000000", "alpha": 0.0}
    m = re.search(rf"UIColor\(rgb: UPalette\.(\w+),\s*alpha: ([\d.]+)", expr)
    if m:
        return {"ref": m.group(1), "alpha": float(m.group(2))}
    m = re.search(rf"UIColor\(rgb: ({HEX}),\s*alpha: ([\d.]+)", expr)
    if m:
        return {"hex": m.group(1).lower(), "alpha": float(m.group(2))}
    m = re.search(r"UPalette\.(\w+)", expr)
    if m:
        return {"ref": m.group(1), "alpha": 1.0}
    m = re.search(rf"({HEX})", expr)
    if m:
        return {"hex": m.group(1).lower(), "alpha": 1.0}
    raise ValueError(f"unparsed colour expression: {expr!r}")


def parse_roles(src: str) -> dict:
    flat = flatten(src)
    roles = {}
    for line in flat.splitlines():
        line = line.strip()
        if not line.startswith("static let"):
            continue
        name = re.match(r"static let (\w+)", line).group(1)
        m = re.search(r"themed\(\\\.\w+,\s*light:\s*(.+?),\s*dark:\s*(.+)$", line)
        if m:
            roles[name] = {"light": parse_side(m.group(1)), "dark": parse_side(m.group(2))}
            continue
        m = re.search(r"Color\(rgb: (.+?)\)\s*$", line)
        if m:                                   # constant across themes
            side = parse_side(m.group(1))
            roles[name] = {"light": side, "dark": dict(side)}
    return roles


# ------------------------------------------------------------------------ type scale

def parse_text(src: str) -> dict:
    out = {}
    for m in re.finditer(
        r"case \.(\w+):\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*\"(\w+)\"\s*,\s*(-?[\d.]+)\s*,\s*\.(\w+)\s*\)",
        src,
    ):
        name, size, lh, weight, tracking, anchor = m.groups()
        out[name] = {"size": float(size), "lineHeightMultiplier": float(lh),
                     "weight": weight, "trackingEm": float(tracking), "dynamicTypeAnchor": anchor}
    return out


# ---------------------------------------------------------------------- numeric sets

def parse_numbers(src: str, enum_name: str) -> dict:
    m = re.search(rf"enum {enum_name} \{{(.*?)\n\}}", src, re.S)
    if not m:
        return {}
    return {k: float(v) for k, v in
            re.findall(r"static let (\w+): CGFloat = ([\d.]+)", m.group(1))}


# --------------------------------------------------------------------------- shadows

def parse_shadows(src: str) -> dict:
    """UShadow is a switch over (style, scheme) with two stacked .shadow() calls.

    Parsed rather than transcribed so a change in the package shows up here.
    `ink` is the literal in UShadowModifier; radius is SwiftUI's blur radius, which
    Figma expresses as blur = radius * 2.
    """
    ink = re.search(r"let ink = Color\(rgb: (0x[0-9A-Fa-f]{6})\)", src)
    ink_hex = (ink.group(1) if ink else "0x16171D").lower()
    out: dict = {}
    blocks = re.split(r"case \(\.", src)[1:]
    for block in blocks:
        head, _, body = block.partition("):")
        m = re.match(r"(\w+),\s*(\.light|_)\s*$", head.strip())
        if not m:
            continue
        style, scheme = m.group(1), m.group(2)
        mode = "light" if scheme == ".light" else "dark"
        layers = []
        for s in re.finditer(r"shadow\(color: (ink|black)\.opacity\(([\d.]+)\), radius: ([\d.]+)(?:, y: (-?[\d.]+))?\)", body):
            base, alpha, radius, y = s.groups()
            layers.append({"hex": ink_hex if base == "ink" else "0x000000",
                           "alpha": float(alpha), "blur": float(radius) * 2,
                           "y": float(y or 0)})
        if layers:
            out.setdefault(style, {})[mode] = layers
    return out


def main() -> int:
    d = tokens_dir()
    palette = parse_palette((d / "UPalette.swift").read_text())
    roles = parse_roles((d / "UColor.swift").read_text())
    text = parse_text((d / "UFont.swift").read_text())
    spacing_src = (d / "USpacing.swift").read_text()
    shadows = parse_shadows((d / "UShadow.swift").read_text())

    # Every alias must point at a palette entry that exists.
    missing = sorted({s["ref"] for r in roles.values() for s in r.values()
                      if "ref" in s and s["ref"] not in palette})
    if missing:
        raise SystemExit(f"roles alias unknown palette entries: {missing}")

    data = {
        "source": str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d),
        "palette": palette,
        "roles": roles,
        "text": text,
        "space": parse_numbers(spacing_src, "USpacing"),
        "radius": parse_numbers(spacing_src, "URadius"),
        "size": parse_numbers(spacing_src, "USize"),
        "shadow": shadows,
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"palette {len(palette)}  roles {len(roles)}  text {len(text)}  "
          f"space {len(data['space'])}  radius {len(data['radius'])}  size {len(data['size'])}  "
          f"shadow {len(shadows)}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
