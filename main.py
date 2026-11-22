#!/usr/bin/env python3
"""Copy the pre-rendered broadsheet to the output path (stdlib only, no network).

The image was rendered offline from the 22 November 2026 day data and is
shipped in this repository as entry.png; this program only copies it."""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
DEST = "/output/entry.png"


def main():
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    shutil.copyfile(SOURCE, DEST)
    size = os.path.getsize(DEST)
    print(f"Wrote {DEST} ({size} bytes)")


if __name__ == "__main__":
    sys.exit(main())
