# Data policy

All source and derived datasets must remain below this directory.

- `raw/`: immutable downloaded artifacts, one folder per accession/study.
- `interim/`: reversible extraction and harmonization outputs.
- `processed/`: modeling tables produced only by authoritative scripts.
- `manifests/`: tracked provenance records, file hashes, and split metadata. Never include raw identifiers in tracked sealed manifests.
- `schemas/`: data contracts.

## Explicitly prohibited downloads

- RADCURE CT/DICOM/RTSTRUCT archives (hundreds of GB).
- HANCOCK whole-slide images or raw TMA imagery.
- Any controlled-access or credentialed data not separately approved.

## Immutability

Downloaded files are read-only inputs. Corrections create a new versioned artifact and manifest record; source files are never edited in place.