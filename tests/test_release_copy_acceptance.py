#!/usr/bin/env python3
"""Release-only copy acceptance.

Intentionally NOT part of the green source-integrity workflow until Codex has
finished copy/design revision. Run on the integrated release candidate.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]/"docs"
html=(ROOT/"index.html").read_text(encoding="utf-8")

def fail(msg):
    raise AssertionError(msg)

# Historical evidence already demonstrates multiple route families/versions.
for phrase in ("Samma stigar", "samma stigar"):
    if phrase in html:
        fail(f"Release copy overstates course identity: {phrase!r}")

# Known typo/reference leak from the first draft.
if "GOTALENDETS" in html:
    fail("Release copy contains 'GOTALENDETS'; use a Sätila-native heading or correct Gotaledens")

# 2020 is not a measured zero year.
if re.search(r"2020[^<]{0,80}(0 deltagare|0 resultat|0 målgång)",html,re.I):
    fail("2020 may not be presented as an observed zero-result edition")

# No unsupported official D+ claim from raw GPX positive gain.
if re.search(r"\bD\+\b",html) and "rå" not in html.lower():
    fail("Unqualified D+ wording is not supported by organizer source")

# Public method should retain the core distinctions.
required=(
    "officiell timingaxel",
    "inte automatiskt uppmätt GPX-distans",
    "äldre upplagor",
)
for text in required:
    if text.lower() not in html.lower():
        fail(f"Release method copy lost required evidence qualifier: {text}")

print("RELEASE COPY ACCEPTANCE PASSED")
