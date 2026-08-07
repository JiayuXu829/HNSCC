# Phase 1 acquisition plan

**Status:** Network execution pending explicit approval.  
**Retrieval date to record:** actual UTC timestamp at download.

## Safety envelope

Download only public clinical/structured tables, processed feature matrices, expression matrices, data dictionaries, and official split files. Do not download RADCURE imaging, HANCOCK WSI/TMA source images, or controlled-access genomic data.

## Study 1 - RADCURE + ORCESTRA

1. Download the small RADCURE clinical spreadsheet from the TCIA collection page (collection DOI `10.7937/J47W-NM11`).
2. Resolve and download the ORCESTRA processed radiomic set reported in the protocol as Zenodo DOI `10.5281/zenodo.8332910`.
3. Record the exact ORCESTRA object version and whether it contains PyRadiomics, GTV volume, random-voxel, permuted-voxel, challenge split, scanner/year variables, and any FMCIB features.
4. Do not download either the 333 GB full imaging archive or the 95 GB OPC imaging subset.

## Study 2 - HANCOCK

1. Snapshot/clone the Apache-2.0 official analysis repository.
2. Download only `StructuredData` (7 MB), `DataSplits_DataDictionaries` (<1 MB), and `TMA_CellDensityMeasurements` (<1 MB) from the official project download page.
3. Use the repository `features/` directory for provided extracted multimodal vectors.
4. Initially skip the 100 MB free-text archive; add it only if the pre-extracted text features cannot be interpreted without it.
5. Do not download TMA/WSI, tumor annotations, extracted core images, or 9 GB UNI encodings for the primary Phase 1 audit.

## Study 3 - TCGA-HNSC, GSE65858, GSE41613

1. Download open-access harmonized TCGA-HNSC expression plus clinical files from GDC; freeze the GDC release and workflow metadata.
2. Download GEO series matrices and platform annotation for GSE65858 and GSE41613.
3. Preserve source normalization metadata; do not perform cross-platform all-data ComBat.
4. External outcomes may be parsed for endpoint audit but may not drive gene/pathway selection, hyperparameters, calibration, or gate thresholds.

## Required post-download actions

- Mark source files read-only.
- Compute SHA-256 and byte size.
- Populate each `data_manifest.yaml` and `license_notes.md`.
- Extract only into `data/interim/<study>/<version>/`.
- Build patient-level ID inventories and immediately test overlap.
- Keep all population, endpoint, and feature claims marked `pending` until verified from actual fields.