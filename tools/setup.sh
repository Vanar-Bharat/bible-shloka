#!/usr/bin/env bash
# Local setup on the Spine (Ubuntu), WSL2 or macOS. Run from the repository root: bash tools/setup.sh
# Fetches the pinned upstream sources, builds source TSVs for all 66 books and the name proposals.
set -euo pipefail
OSHB=3d15126fb1ef74867fc1434be1942e837932691f      # openscriptures/morphhb (WLC + OSHB, CC BY 4.0)
MGNT=aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d      # morphgnt/sblgnt (CC BY-SA 3.0)
python3 -m venv .venv && . .venv/bin/activate && pip -q install pyyaml
mkdir -p build/upstream && cd build/upstream
fetch() { [ -d "$1" ] || { git init -q "$1"; git -C "$1" remote add origin "$2"; }
          git -C "$1" fetch -q --depth 1 origin "$3" && git -C "$1" checkout -q FETCH_HEAD; }
fetch morphhb https://github.com/openscriptures/morphhb "$OSHB"
fetch sblgnt https://github.com/morphgnt/sblgnt "$MGNT"
cd ../..
python tools/ingest.py build/upstream/morphhb/wlc build/upstream/sblgnt build/src | tail -1
python tools/naturalise.py build/src register/names.proposed.tsv
python tools/check_mula.py $(ls mula/*/*.txt | grep -v '\.deva\.') | grep -v WARN
echo "Ready. Dry run:  . .venv/bin/activate && python tools/run_bible.py --src build/src --maker anthropic:MODEL --reviewer openai:MODEL --dry-run --limit 1"
