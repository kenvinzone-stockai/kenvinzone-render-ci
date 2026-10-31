"""Colour palettes for HyperFrames videos (same presets as Preview Editor -> Tone mau)."""
from __future__ import annotations

import json
import re
from pathlib import Path

PRESETS = {
 "creator-pink-blue": {
  "--primary": "#ea4c89",
  "--primary-light": "#ff9ac2",
  "--primary-dark": "#8f1d50",
  "--accent": "#4a90e2",
  "--accent-light": "#9bd3ff",
  "--info": "#50c878",
  "--success": "#50c878",
  "--bg-dark": "#07030d"
 },
 "openclaw-neon-green": {
  "--primary": "#00e676",
  "--primary-light": "#b9f6ca",
  "--primary-dark": "#0a7442",
  "--accent": "#ffab40",
  "--accent-light": "#ffd699",
  "--info": "#69f0ae",
  "--success": "#00e676",
  "--bg-dark": "#030807"
 },
 "cyber-purple": {
  "--primary": "#8b5cf6",
  "--primary-light": "#c4b5fd",
  "--primary-dark": "#4c1d95",
  "--accent": "#22d3ee",
  "--accent-light": "#a5f3fc",
  "--info": "#38bdf8",
  "--success": "#34d399",
  "--bg-dark": "#080413"
 },
 "minimal-gold": {
  "--primary": "#f5c542",
  "--primary-light": "#ffe9a3",
  "--primary-dark": "#926b10",
  "--accent": "#ffffff",
  "--accent-light": "#f4f4f5",
  "--info": "#facc15",
  "--success": "#a3e635",
  "--bg-dark": "#090807"
 },
 "dark-terminal": {
  "--primary": "#22c55e",
  "--primary-light": "#86efac",
  "--primary-dark": "#14532d",
  "--accent": "#94a3b8",
  "--accent-light": "#cbd5e1",
  "--info": "#38bdf8",
  "--success": "#22c55e",
  "--bg-dark": "#020617"
 },
 "sunset-fire": {
  "--primary": "#ff5a36",
  "--primary-light": "#ffb59e",
  "--primary-dark": "#a62a12",
  "--accent": "#ffcf3f",
  "--accent-light": "#ffe6a3",
  "--info": "#ff8a5b",
  "--success": "#f59e0b",
  "--bg-dark": "#0d0503"
 },
 "ocean-aqua": {
  "--primary": "#06b6d4",
  "--primary-light": "#99f6ff",
  "--primary-dark": "#0e5f73",
  "--accent": "#3b82f6",
  "--accent-light": "#bfdbfe",
  "--info": "#38bdf8",
  "--success": "#22d3ee",
  "--bg-dark": "#030a0f"
 },
 "aurora-mint": {
  "--primary": "#34d399",
  "--primary-light": "#b6f7dc",
  "--primary-dark": "#0f6b4a",
  "--accent": "#a855f7",
  "--accent-light": "#ddd0fe",
  "--info": "#22d3ee",
  "--success": "#34d399",
  "--bg-dark": "#030a09"
 },
 "magenta-pop": {
  "--primary": "#ec4899",
  "--primary-light": "#ffc2e2",
  "--primary-dark": "#8a1e5a",
  "--accent": "#a855f7",
  "--accent-light": "#e9d5ff",
  "--info": "#f472b6",
  "--success": "#c084fc",
  "--bg-dark": "#0c0410"
 },
 "ice-frost": {
  "--primary": "#38bdf8",
  "--primary-light": "#e0f4ff",
  "--primary-dark": "#1b6fa8",
  "--accent": "#818cf8",
  "--accent-light": "#c7d2fe",
  "--info": "#60a5fa",
  "--success": "#22d3ee",
  "--bg-dark": "#040810"
 },
 "solar-gold": {
  "--primary": "#fbbf24",
  "--primary-light": "#fff1c2",
  "--primary-dark": "#92610a",
  "--accent": "#fb923c",
  "--accent-light": "#fed7aa",
  "--info": "#facc15",
  "--success": "#fbbf24",
  "--bg-dark": "#0c0803"
 },
 "candy-pop": {
  "--primary": "#f472b6",
  "--primary-light": "#ffd6ec",
  "--primary-dark": "#9d2168",
  "--accent": "#22d3ee",
  "--accent-light": "#a5f3fc",
  "--info": "#f9a8d4",
  "--success": "#5eead4",
  "--bg-dark": "#0c0410"
 },
 "crimson-ember": {
  "--primary": "#ef4444",
  "--primary-light": "#ffc9c9",
  "--primary-dark": "#8f1f1f",
  "--accent": "#f59e0b",
  "--accent-light": "#fde68a",
  "--info": "#fb7185",
  "--success": "#f87171",
  "--bg-dark": "#0d0404"
 }
}

ROLE_KEYS = {"primary": "--primary", "primary_light": "--primary-light", "primary_dark": "--primary-dark",
             "accent": "--accent", "accent_light": "--accent-light", "info": "--info", "success": "--success"}


def _norm(vars_: dict) -> dict:
    out = {}
    for role, key in ROLE_KEYS.items():
        v = str(vars_.get(key) or "").strip()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            out[role] = v.lower()
    if {"primary", "accent"} <= set(out):
        r, g, b = (int(out["accent"][i:i + 2], 16) for i in (1, 3, 5))
        out["on_accent"] = "#1a1205" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"
        return out
    return {}


def resolve_palette(choice: str | None, settings: dict | None) -> dict:
    """'template' (or empty) -> {} = keep the template colours.
    'preset' -> the preset chosen for this slide in Preview Editor. Any preset id -> that preset."""
    choice = (choice or "template").strip().lower()
    if choice in ("", "template", "auto", "default"):
        return {}
    if choice == "preset":
        theme = (settings or {}).get("theme") or {}
        name = str(theme.get("preset") or "")
        if name == "custom":
            return _norm(theme.get("customVariables") or theme.get("variables") or {})
        return _norm(PRESETS.get(name) or theme.get("variables") or {})
    return _norm(PRESETS.get(choice) or {})


def _rgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


def recolor_project(work: Path, palette: dict, map_file: Path) -> int:
    """Swap the template's accent colours (listed in palette-map.json) for the palette's.
    Meaning colours (green up / red down / traffic lights) are not in the map and stay."""
    if not palette or not map_file.exists():
        return 0
    mp = json.loads(map_file.read_text(encoding="utf-8"))
    hexmap = {k.lower(): palette.get(v) or palette.get(v.split("_")[0]) for k, v in mp.get("hex", {}).items()}
    rgbmap = {k.replace(" ", ""): _rgb(palette.get(v) or palette.get(v.split("_")[0])) for k, v in mp.get("rgb", {}).items()
              if palette.get(v) or palette.get(v.split("_")[0])}
    hexmap = {k: v for k, v in hexmap.items() if v}
    hex_re = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F]{1}(?:[^0-9a-fA-F]|$))")
    rgb_re = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
    n = 0
    files = [work / "index.html"] + sorted((work / "compositions").glob("*.html"))
    for f in files:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        t2 = hex_re.sub(lambda m: hexmap.get("#" + m.group(1).lower(), m.group(0)), t)
        t2 = rgb_re.sub(lambda m: (m.group(0).split("(")[0] + "(" + rgbmap[f"{m.group(1)},{m.group(2)},{m.group(3)}"])
                        if f"{m.group(1)},{m.group(2)},{m.group(3)}" in rgbmap else m.group(0), t2)
        if t2 != t:
            n += 1
            f.write_text(t2, encoding="utf-8")
    return n
