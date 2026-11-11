# Sequencing & Tools

Interactive overview of sequencing platforms and the tools that process their data — raw signal to annotated MAGs — for nanopore, PacBio HiFi and short-read platforms. Live at https://kirk3gaard.github.io/sequencing-and-tools/

- `scripts/build_catalogue.py` — the curated list (edit here, then `python3 scripts/build_catalogue.py data`)
- `scripts/update_versions.py` — refreshes `data/versions.json` from GitHub release/tag feeds and bioconda (stdlib only)
- `index.html`, `assets/` — static site, no build step

Versions are refreshed weekly alongside the Techwatch tech overview. Tools flagged **artefact** handle read artefacts basecallers leave (untrimmed adapters, barcodes, chimeras, concatemers).
