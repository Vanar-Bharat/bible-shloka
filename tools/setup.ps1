# Local setup on Windows (PowerShell). Run from the repository root:  powershell -ExecutionPolicy Bypass -File tools\setup.ps1
# Needs Python 3.10+ and Git on PATH. Fetches pinned upstream sources and builds source TSVs for all 66 books.
$ErrorActionPreference = 'Stop'; $env:PYTHONUTF8 = '1'
$OSHB = '3d15126fb1ef74867fc1434be1942e837932691f'   # openscriptures/morphhb (WLC + OSHB, CC BY 4.0)
$MGNT = 'aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d'   # morphgnt/sblgnt (CC BY-SA 3.0)
python -m venv .venv; & .\.venv\Scripts\python.exe -m pip -q install pyyaml
$py = '.\.venv\Scripts\python.exe'
New-Item -ItemType Directory -Force build\upstream | Out-Null
function Fetch($dir, $url, $sha) {
  if (-not (Test-Path "build\upstream\$dir")) { git init -q "build\upstream\$dir"; git -C "build\upstream\$dir" remote add origin $url }
  git -C "build\upstream\$dir" fetch -q --depth 1 origin $sha; git -C "build\upstream\$dir" checkout -q FETCH_HEAD
}
Fetch morphhb https://github.com/openscriptures/morphhb $OSHB
Fetch sblgnt https://github.com/morphgnt/sblgnt $MGNT
& $py tools\ingest.py build\upstream\morphhb\wlc build\upstream\sblgnt build\src | Select-Object -Last 1
& $py tools\naturalise.py build\src register\names.proposed.tsv
$files = Get-ChildItem mula\*\*.txt | Where-Object { $_.Name -notlike '*.deva.txt' } | ForEach-Object { $_.FullName }
& $py tools\check_mula.py @files | Where-Object { $_ -notlike 'WARN*' }
Write-Host 'Ready. Dry run:  .\.venv\Scripts\python.exe tools\run_bible.py --src build\src --maker ollama:MODEL --reviewer anthropic:MODEL --dry-run --limit 1'
