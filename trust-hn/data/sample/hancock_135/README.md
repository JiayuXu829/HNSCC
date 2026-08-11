# HANCOCK 135-patient sample

This dataset is a reproducible simple random sample of **135**
patients from the 763-patient HANCOCK cohort available in this workspace.

- Random seed: `20260811`
- Sampling: without replacement from `clinical_data.json` patient IDs
- Patient fields/CSV columns: preserved from the HANCOCK sources
- Natural missing modalities: preserved, not imputed

## Layout

- `Hancock_Dataset/StructuredData/`: filtered structured JSON data
- `Hancock_Dataset/DataSplits_DataDictionaries/`: dictionaries and splits
- `Hancock_Dataset/TMA_CellDensityMeasurements/`: filtered raw TMA density rows
- `HANCOCK_MultimodalDataset/features/`: pre-extracted experiment features
- `metadata/patient_ids.txt`: sorted selected patient IDs
- `metadata/sample_manifest.json`: selection, coverage, hashes, and inventory
- `metadata/license_notes.md`: source citation/reuse notes

The workspace does not contain HANCOCK WSI/TMA source imagery or raw text
archives; those were not downloaded under the project data policy. All HANCOCK
data currently used by the TRUST-HN experiments, plus all other acquired
patient-level structured/TMA features, are included.
